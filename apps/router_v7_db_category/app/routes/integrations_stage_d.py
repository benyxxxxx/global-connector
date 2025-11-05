import os, re, tempfile, shutil, json, yaml
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, Header, HTTPException
from fastapi import Depends
from starlette.requests import Request

from app.integrator.patch_apply import apply_patch, BR_RE
from app.integrator.edit_spec import apply_edit_spec

router = APIRouter(
    prefix="/integrations/stage-d",
    tags=["integrations-stage-d"],
    include_in_schema=False, # hidden interface
)

MAX_PATCH_BYTES = int(os.environ.get("STAGE_D_MAX_BYTES", str(500 * 1024))) # 500KB default

def _require_admin(x_integrator_admin: Optional[str] = Header(None)):
    required = os.environ.get("PROMOTE_ADMIN_TOKEN", "").strip()
    if required and x_integrator_admin != required:
        raise HTTPException(status_code=403, detail="Forbidden")

@router.post("/submit-patch")
async def submit_patch(
    file: UploadFile = File(...),
    title: str = Form("change"),
    x_integrator_admin: None = Depends(_require_admin),
):
    if not file.filename.lower().endswith((".patch", ".diff")):
        raise HTTPException(400, "Attach a .patch or .diff file")
    data = await file.read()
    if len(data) > MAX_PATCH_BYTES:
        raise HTTPException(413, "Patch too large")
    try:
        res = apply_patch(data, title=title, dry_run=False)
        return res
    except Exception as e:
        raise HTTPException(422, f"Patch failed: {e}")

@router.post("/dry-run")
async def dry_run(
    kind: str = Form(...), # "patch" | "edits"
    file: UploadFile = File(...),
    title: str = Form("change"),
    x_integrator_admin: None = Depends(_require_admin),
):
    data = await file.read()
    if len(data) > MAX_PATCH_BYTES:
        raise HTTPException(413, "File too large")

    if kind not in ("patch", "edits"):
        raise HTTPException(400, "kind must be 'patch' or 'edits'")

    if kind == "patch":
        try:
            return apply_patch(data, title=title, dry_run=True)
        except Exception as e:
            raise HTTPException(422, f"Patch dry-run failed: {e}")

    # kind == edits
    # Parse YAML/JSON
    try:
        text = data.decode("utf-8")
        spec = yaml.safe_load(text) if file.filename.lower().endswith((".yaml", ".yml")) else json.loads(text)

        # Clone, apply to temp repo but do not commit
        from app.integrator.patch_apply import _origin_url, _run # reuse helpers safely
        repo = os.environ.get("GITHUB_REPO", "").strip()
        base = os.environ.get("GITHUB_BASE", "main").strip()
        token = os.environ.get("GITHUB_TOKEN", "").strip()
        if not repo or not token:
            raise RuntimeError("GITHUB_REPO and GITHUB_TOKEN required")

        tmp = tempfile.mkdtemp(prefix="integrator-dry-")
        try:
            _run(["git", "init"], tmp)
            _run(["git", "remote", "add", "origin", _origin_url(repo, token)], tmp)
            _run(["git", "fetch", "--depth=50", "origin", base], tmp)
            _run(["git", "checkout", "-B", "work", f"origin/{base}"], tmp)
            res = apply_edit_spec(tmp, spec, dry_run=True)
            # discard anyway
            _run(["git", "reset", "--hard"], tmp)
            return {"branch": f"stage-d/{title}", **res}
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    except Exception as e:
        raise HTTPException(422, f"Spec dry-run failed: {e}")

@router.post("/submit-edits")
async def submit_edits(
    file: UploadFile = File(None),
    spec_text: str = Form(None),
    title: str = Form("change"),
    x_integrator_admin: None = Depends(_require_admin),
):
    # accept either uploaded yaml/json or spec_text (string)
    if file is None and spec_text is None:
        raise HTTPException(400, "Provide 'file' (yaml/json) or 'spec_text'")

    if file:
        data = await file.read()
        if len(data) > MAX_PATCH_BYTES:
            raise HTTPException(413, "Spec too large")
        text = data.decode("utf-8")
        if file.filename.lower().endswith((".yaml", ".yml")):
            spec = yaml.safe_load(text)
        else:
            spec = json.loads(text)
    else: # form text (try json first, then yaml)
        try:
            spec = json.loads(spec_text)
        except Exception:
            spec = yaml.safe_load(spec_text)

    # apply edits by cloning and committing
    from app.integrator.patch_apply import _origin_url, _run, _author, _slugify
    repo = os.environ.get("GITHUB_REPO", "").strip()
    base = os.environ.get("GITHUB_BASE", "main").strip()
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if not repo or not token:
        raise HTTPException(500, "GITHUB_REPO and GITHUB_TOKEN required")

    slug = _slugify(title)
    branch = f"stage-d/{slug}"
    if not BR_RE.match(branch):
        raise HTTPException(400, "Invalid branch name")

    tmp = tempfile.mkdtemp(prefix="integrator-edits-")
    try:
        _run(["git", "init"], tmp)
        _run(["git", "remote", "add", "origin", _origin_url(repo, token)], tmp)
        _run(["git", "fetch", "--depth=50", "origin", base], tmp)
        _run(["git", "checkout", "-B", branch, f"origin/{base}"], tmp)
        res = apply_edit_spec(tmp, spec, dry_run=False)
        auth = _author()
        _run(["git", "config", "user.name", auth["name"]], tmp)
        _run(["git", "config", "user.email", auth["email"]], tmp)
        msg = f"chore(integrator): {slug} [D]\n\nApplied edit spec"
        _run(["git", "add", "-A"], tmp)
        _run(["git", "commit", "-m", msg], tmp)
        _run(["git", "push", "-u", "origin", branch], tmp)

        return {"branch": branch, "files": res["files"]}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)