from __future__ import annotations

import os
import re
import httpx
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/integrations/stage-b", tags=["integrations-stage-b"])

# --------- Config / env ---------
def _need(name: str) -> str:
    v = os.environ.get(name, "").strip()
    if not v:
        raise RuntimeError(f"Missing required env var: {name}")
    return v

def validate_env() -> Dict[str, str]:
    api = os.environ.get("GITHUB_API", "https://api.github.com").rstrip("/")
    token = _need("GITHUB_TOKEN")
    repo = _need("GITHUB_REPO")
    base = os.environ.get("GITHUB_BASE", "main")
    if repo.count("/") != 1:
        raise RuntimeError("GITHUB_REPO must look like 'owner/repo'")
    return {"GITHUB_API": api, "GITHUB_TOKEN": token, "GITHUB_REPO": repo, "GITHUB_BASE": base}

def _headers(token: str) -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

# --------- Branch validation ---------
BRANCH_RE = re.compile(r"^(?!/)(?!.*//)(?!.*\.\.)(?!.*\.$)[A-Za-z0-9._/-]{1,255}$")
STAGE_A_RE = re.compile(r"^stage-a/\d{8}-[a-z0-9-]{1,48}(-\d+)?$")

def validate_branch_name(branch: str) -> None:
    if not branch or not BRANCH_RE.match(branch):
        raise HTTPException(400, "Invalid branch name")
    if not STAGE_A_RE.match(branch):
        raise HTTPException(400, "Branch is not a Stage-A branch")

# --------- HTTP robustness ---------
async def _request_with_retries(method, url: str, *, max_retries: int = 2, backoff_start: float = 0.5, **kwargs) -> httpx.Response:
    import asyncio
    backoff = backoff_start
    last_exc: Optional[Exception] = None
    for attempt in range(max_retries + 1):
        try:
            resp: httpx.Response = await method(url, **kwargs)
            if resp.status_code == 403 and resp.headers.get("X-RateLimit-Remaining") == "0":
                raise HTTPException(429, "GitHub rate limit exceeded; wait and retry")
            if 500 <= resp.status_code < 600 and attempt < max_retries:
                await asyncio.sleep(backoff); backoff *= 2; continue
            return resp
        except httpx.RequestError as e:
            last_exc = e
            if attempt < max_retries:
                await asyncio.sleep(backoff); backoff *= 2; continue
            raise HTTPException(502, f"Network error talking to GitHub: {e!s}")
    if last_exc:
        raise HTTPException(502, f"Network error talking to GitHub: {last_exc!s}")
    raise HTTPException(502, "Unknown network error")

# --------- Helpers ---------
def _sanitize_title(s: str) -> str:
    s = re.sub(r"[\x00-\x1F\x7F\r\n\t]+", " ", (s or "")).strip()
    return (s[:120] or "Stage B Promote")

def _owner_repo(repo: str) -> tuple[str, str]:
    owner, name = repo.split("/", 1)
    return owner, name

async def _get_ref_sha(cfg: Dict[str, str], branch: str) -> Optional[str]:
    url = f"{cfg['GITHUB_API']}/repos/{cfg['GITHUB_REPO']}/git/ref/heads/{branch}"
    async with httpx.AsyncClient(timeout=20) as c:
        r = await _request_with_retries(c.get, url, headers=_headers(cfg["GITHUB_TOKEN"]))
    if r.status_code == 200:
        return r.json()["object"]["sha"]
    if r.status_code == 404:
        return None
    r.raise_for_status()

async def _find_existing_pr(cfg: Dict[str, str], branch: str) -> Optional[int]:
    owner, _ = _owner_repo(cfg["GITHUB_REPO"])
    url = f"{cfg['GITHUB_API']}/repos/{cfg['GITHUB_REPO']}/pulls"
    params = {
        "state": "all",                      # open/closed/merged
        "head": f"{owner}:{branch}",
        "base": cfg["GITHUB_BASE"],
        "per_page": 1,
    }
    async with httpx.AsyncClient(timeout=20) as c:
        r = await _request_with_retries(c.get, url, headers=_headers(cfg["GITHUB_TOKEN"]), params=params)
    if r.status_code == 200:
        items = r.json()
        if items:
            return int(items[0]["number"])
        return None
    r.raise_for_status()

async def _create_pr(cfg: Dict[str, str], branch: str, title: str) -> int:
    url = f"{cfg['GITHUB_API']}/repos/{cfg['GITHUB_REPO']}/pulls"
    body = {"title": _sanitize_title(title), "head": branch, "base": cfg["GITHUB_BASE"]}
    async with httpx.AsyncClient(timeout=30) as c:
        r = await _request_with_retries(c.post, url, headers=_headers(cfg["GITHUB_TOKEN"]), json=body)
    if r.status_code in (200, 201):
        return int(r.json()["number"])
    if r.status_code == 422 and "A pull request already exists" in r.text:
        pr_num = await _find_existing_pr(cfg, branch)
        if pr_num is not None:
            return pr_num
    r.raise_for_status()

async def _get_pr(cfg: Dict[str, str], pr_number: int) -> Dict[str, Any]:
    url = f"{cfg['GITHUB_API']}/repos/{cfg['GITHUB_REPO']}/pulls/{pr_number}"
    async with httpx.AsyncClient(timeout=20) as c:
        r = await _request_with_retries(c.get, url, headers=_headers(cfg["GITHUB_TOKEN"]))
    r.raise_for_status()
    return r.json()

async def _merge_pr(cfg: Dict[str, str], pr_number: int) -> str:
    """
    Squash-merge PR. If already merged, return merge commit SHA.
    If blocked/conflicting, raise HTTPException(409) with a helpful message.
    """
    import asyncio
    # Wait until GitHub computes mergeability (mergeable_state != "unknown")
    pr = await _get_pr(cfg, pr_number)
    for _ in range(10):
        state = pr.get("mergeable_state")
        if state and state != "unknown":
            break
        await asyncio.sleep(1.0)
        pr = await _get_pr(cfg, pr_number)

    if pr.get("merged"):
        sha = pr.get("merge_commit_sha")
        if sha:
            return sha

    state = pr.get("mergeable_state")  # clean / unstable / blocked / dirty / behind / ...
    if state not in ("clean", "unstable"):
        raise HTTPException(409, f"PR cannot be auto-merged (state={state}). Review: {pr['html_url']}")

    url = f"{cfg['GITHUB_API']}/repos/{cfg['GITHUB_REPO']}/pulls/{pr_number}/merge"
    body = {"merge_method": "squash"}
    async with httpx.AsyncClient(timeout=60) as c:
        r = await _request_with_retries(c.put, url, headers=_headers(cfg["GITHUB_TOKEN"]), json=body, max_retries=2)
    if r.status_code == 200:
        return r.json().get("sha")
    if r.status_code in (405, 409):
        raise HTTPException(409, f"PR cannot be auto-merged (state={state}). Review: {pr['html_url']}")
    r.raise_for_status()

async def _tag_exists(cfg: Dict[str, str], tag: str) -> bool:
    url = f"{cfg['GITHUB_API']}/repos/{cfg['GITHUB_REPO']}/git/ref/tags/{tag}"
    async with httpx.AsyncClient(timeout=20) as c:
        r = await _request_with_retries(c.get, url, headers=_headers(cfg["GITHUB_TOKEN"]))
    if r.status_code == 200:
        return True
    if r.status_code == 404:
        return False
    r.raise_for_status()

async def _create_lightweight_tag(cfg: Dict[str, str], tag: str, sha: str) -> None:
    url = f"{cfg['GITHUB_API']}/repos/{cfg['GITHUB_REPO']}/git/refs"
    body = {"ref": f"refs/tags/{tag}", "sha": sha}
    async with httpx.AsyncClient(timeout=30) as c:
        r = await _request_with_retries(c.post, url, headers=_headers(cfg["GITHUB_TOKEN"]), json=body)
    if r.status_code not in (200, 201):
        r.raise_for_status()

def _release_tag_for_branch(branch: str) -> str:
    # stage-a/20250915-foo -> release/stage-a-20250915-foo
    return f"release/{branch.replace('/', '-')}"

# --------- Request model ---------
class PromoteRequest(BaseModel):
    branch: str
    title: Optional[str] = None
    tag: Optional[str] = None  # optional; if provided we tag this; else default release/<slug>

# --------- Routes ---------
@router.post("/promote")
async def promote(req: PromoteRequest):
    # 1) env
    try:
        cfg = validate_env()
    except RuntimeError as e:
        raise HTTPException(500, f"Integrator misconfigured: {e}")

    # 2) validate branch input
    validate_branch_name(req.branch)

    # 3) resolve branch head sha (existence check)
    sha = await _get_ref_sha(cfg, req.branch)
    if not sha:
        raise HTTPException(404, f"Branch '{req.branch}' not found")

    # 4) idempotent PR: reuse or create against base
    pr_num = await _find_existing_pr(cfg, req.branch)
    if pr_num is None:
        pr_num = await _create_pr(cfg, req.branch, req.title or f"Promote {req.branch} → {cfg['GITHUB_BASE']}")
    pr = await _get_pr(cfg, pr_num)
    pr_url = pr["html_url"]

    # 5) accept (merge) PR → get MERGE COMMIT SHA
    merge_sha = await _merge_pr(cfg, pr_num)

    # 6) tag on the merge commit (release/**). Use provided tag or default from branch.
    tag = (req.tag or _release_tag_for_branch(req.branch)).strip("/")
    if not re.match(r"^[A-Za-z0-9._/-]{3,}$", tag) or ".." in tag or "//" in tag or tag.endswith("."):
        raise HTTPException(400, "Invalid tag name")
    if not await _tag_exists(cfg, tag):
        await _create_lightweight_tag(cfg, tag, merge_sha)

    return {"ok": True, "pr_number": pr_num, "pr_url": pr_url, "sha": merge_sha, "tag": tag}
