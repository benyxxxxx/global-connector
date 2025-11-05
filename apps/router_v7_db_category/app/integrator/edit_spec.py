import os, io, json, re, yaml, shutil
from typing import Dict, Any, List
from pathlib import Path
from fnmatch import fnmatch

ALLOWED_GLOBS_DEFAULT = ["**"] # allow all by default
BLOCKED_NAMES = {".env", ".env.local", "secrets.yml", "secrets.yaml"}

def _ensure_parent(p: Path):
    p.parent.mkdir(parents=True, exist_ok=True)

def _dotset(obj: Any, path: str, value: Any):
    parts = path.split(".")
    cur = obj
    for k in parts[:-1]:
        if not isinstance(cur, dict) or k not in cur or cur[k] is None:
            cur[k] = {}
        cur = cur[k]
    cur[parts[-1]] = value

def _within_allowlist(path: str, allows: List[str]) -> bool:
    return any(fnmatch(path, gl) for gl in allows)

def _blocked(path: str) -> bool:
    name = Path(path).name
    return name in BLOCKED_NAMES

def _read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8") if p.exists() else ""

def _write_text(p: Path, content: str):
    _ensure_parent(p)
    p.write_text(content, encoding="utf-8")

def _safe_load_json(p: Path) -> Any:
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}

def _safe_dump_json(p: Path, data: Any):
    _ensure_parent(p)
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

def _safe_load_yaml(p: Path) -> Any:
    return yaml.safe_load(p.read_text(encoding="utf-8")) if p.exists() else {}

def _safe_dump_yaml(p: Path, data: Any):
    _ensure_parent(p)
    p.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")

def apply_edit_spec(repo_dir: str, spec: Dict[str, Any], *, dry_run: bool = False, allow_globs: List[str] = None) -> Dict[str, Any]:
    """Apply generic edits (idempotent where possible). Returns {'files':[...]}."""
    edits = spec.get("edits", [])
    if not isinstance(edits, list):
        raise ValueError("spec.edits must be a list")

    allows = allow_globs or ALLOWED_GLOBS_DEFAULT
    changed: List[str] = []

    def touched(p: Path):
        rel = str(p.relative_to(repo_dir))
        if rel not in changed:
            changed.append(rel)

    for op in edits:
        kind = op.get("op")
        if not kind:
            raise ValueError("edit missing 'op'")
        path = op.get("path") or op.get("to") or op.get("from")
        if not path: # for move.rename we validate separately
            pass

        # blocklist and allowlist
        if kind != "move.rename":
            if path and _blocked(path):
                raise ValueError(f"blocked path: {path}")
            if path and not _within_allowlist(path, allows):
                raise ValueError(f"path not allowed by allowlist: {path}")

        if kind == "file.create":
            p = Path(repo_dir) / op["path"]
            if p.exists(): # overwrite only if content differs
                old = _read_text(p)
                new = op.get("content", "")
                if old != new:
                    _write_text(p, new)
                    touched(p)
            else:
                _write_text(p, op.get("content", ""))
                touched(p)

        elif kind == "file.delete":
            p = Path(repo_dir) / op["path"]
            if p.exists():
                p.unlink()
                touched(p)

        elif kind == "move.rename":
            src = Path(repo_dir) / op["from"]
            dst = Path(repo_dir) / op["to"]
            if _blocked(src.name) or _blocked(dst.name):
                raise ValueError("blocked path in move.rename")
            if not _within_allowlist(str(dst.relative_to(repo_dir)), allows):
                raise ValueError("destination not allowed by allowlist")
            if src.exists():
                _ensure_parent(dst)
                shutil.move(str(src), str(dst))
                touched(src); touched(dst)

        elif kind == "text.replace":
            p = Path(repo_dir) / op["path"]
            find = op.get("find", "")
            repl = op.get("replace", "")
            count = op.get("count", 0) # 0 = replace all
            txt = _read_text(p)
            new, n = re.subn(re.escape(find), repl, txt, count=count)
            if n > 0:
                _write_text(p, new)
                touched(p)

        elif kind == "text.ensure":
            p = Path(repo_dir) / op["path"]
            after = op.get("after")
            line = op.get("line", "")
            txt = _read_text(p)
            if line in txt:
                continue
            if after and after in txt:
                idx = txt.index(after) + len(after)
                new = txt[:idx] + ("\n" if not txt[idx:idx+1] == "\n" else "") + line + "\n" + txt[idx:]
            else:
                new = (txt + ("\n" if not txt.endswith("\n") else "") + line + "\n")
            _write_text(p, new)
            touched(p)

        elif kind == "json.set":
            p = Path(repo_dir) / op["path"]
            data = _safe_load_json(p)
            for k, v in (op.get("set") or {}).items():
                _dotset(data, k, v)
            _safe_dump_json(p, data)
            touched(p)

        elif kind == "yaml.set":
            p = Path(repo_dir) / op["path"]
            data = _safe_load_yaml(p)
            for k, v in (op.get("set") or {}).items():
                _dotset(data, k, v)
            _safe_dump_yaml(p, data)
            touched(p)

        else:
            raise ValueError(f"unsupported op: {kind}")

    result = {"files": sorted(changed)}
    if dry_run: # caller must discard changes (we apply in a temp clone in the route)
        result["dry_run"] = True
    return result