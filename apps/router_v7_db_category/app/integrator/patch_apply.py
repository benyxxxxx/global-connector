import os, re, tempfile, shutil, subprocess, json
from typing import List, Dict

BR_RE = re.compile(r"^stage-d/[a-z0-9._/-]{1,60}$")

def _slugify(s: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9._/-]+", "-", s.strip())
    s = s.strip("-").lower()
    return s or "change"

def _run(cmd: List[str], cwd: str):
    p = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"cmd failed: {' '.join(cmd)}\n{p.stderr or p.stdout}")
    return p.stdout

def _origin_url(repo: str, token: str) -> str:
    # repo = "owner/name"
    token = token.strip()
    if not token:
        raise RuntimeError("GITHUB_TOKEN is required")
    return f"https://x-access-token:{token}@github.com/{repo}.git"

def _author() -> Dict[str, str]:
    return {
        "name": os.environ.get("GIT_COMMIT_AUTHOR_NAME", "Integrator Bot"),
        "email": os.environ.get("GIT_COMMIT_AUTHOR_EMAIL", "integrator@noreply.local"),
    }

def apply_patch(patch_bytes: bytes, *, title: str, dry_run: bool = False) -> Dict:
    """
    Clone -> create stage-d/<slug> -> git apply --3way -> (optionally commit&push) -> summary
    Env required: GITHUB_TOKEN, GITHUB_REPO, GITHUB_BASE
    """
    repo = os.environ.get("GITHUB_REPO", "").strip() # e.g. "owner/repo"
    base = os.environ.get("GITHUB_BASE", "main").strip()
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if not repo:
        raise RuntimeError("GITHUB_REPO is required")

    slug = _slugify(title)
    branch = f"stage-d/{slug}"
    if not BR_RE.match(branch):
        raise RuntimeError("Invalid branch name after slugify")

    odir = tempfile.mkdtemp(prefix="integrator-")
    try:
        # clone base branch shallow
        _run(["git", "init"], odir)
        _run(["git", "remote", "add", "origin", _origin_url(repo, token)], odir)
        _run(["git", "fetch", "--depth=50", "origin", base], odir)
        _run(["git", "checkout", "-B", branch, f"origin/{base}"], odir)

        # write patch file
        pfile = os.path.join(odir, "changes.patch")
        with open(pfile, "wb") as f:
            f.write(patch_bytes)

        # apply (do a dry-run check first for better error)
        _run(["git", "apply", "--3way", "--check", pfile], odir)

        if dry_run:
            # show planned changes without committing
            _run(["git", "apply", "--3way", pfile], odir)
            changed = _run(["git", "status", "--porcelain"], odir).strip().splitlines()
            files = sorted({ln.split()[-1] for ln in changed}) if changed and changed[0] else []
            # cleanup: discard changes
            _run(["git", "reset", "--hard"], odir)
            return {"branch": branch, "dry_run": True, "files": files}

        # apply + commit + push
        _run(["git", "apply", "--3way", "--index", pfile], odir)
        auth = _author()
        _run(["git", "config", "user.name", auth["name"]], odir)
        _run(["git", "config", "user.email", auth["email"]], odir)
        msg = f"chore(integrator): {slug} [D]\n\nApplied patch via Stage D"
        _run(["git", "commit", "-m", msg], odir)
        _run(["git", "push", "-u", "origin", branch], odir)

        # summary vs base
        diff = _run(["git", "diff", "--name-status", f"origin/{base}...{branch}"], odir).strip().splitlines()
        files = [ln.split("\t")[-1] for ln in diff] if diff and diff[0] else []
        return {"branch": branch, "files": files}

    finally:
        shutil.rmtree(odir, ignore_errors=True)