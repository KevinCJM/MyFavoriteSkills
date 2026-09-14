from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any


SKILL_ROOT = Path(__file__).resolve().parents[1]
BUNDLED_INTERFACES_JSON = SKILL_ROOT / "references" / "tushare_interfaces_ai_optimized.json"
CONFIG_ENV = "TUSHARE_FETCHER_CONFIG"


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def user_config_path(explicit: str | Path | None = None) -> Path:
    if explicit:
        return Path(explicit).expanduser().resolve()
    env_path = os.environ.get(CONFIG_ENV)
    if env_path:
        return Path(env_path).expanduser().resolve()
    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        return (Path(xdg).expanduser() / "tushare-fetcher" / "config.json").resolve()
    return (Path.home() / ".config" / "tushare-fetcher" / "config.json").resolve()


def load_user_config(path: str | Path | None = None) -> dict[str, Any]:
    cfg_path = user_config_path(path)
    if not cfg_path.exists():
        return {}
    return json.loads(cfg_path.read_text(encoding="utf-8"))


def save_user_config(data: dict[str, Any], path: str | Path | None = None) -> Path:
    cfg_path = user_config_path(path)
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(data)
    payload.setdefault("schema_version", "1.0")
    payload["updated_at"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    atomic_write_json(cfg_path, payload, backup=False)
    return cfg_path


def load_user_points(path: str | Path | None = None) -> int | None:
    data = load_user_config(path)
    value = data.get("tushare_points")
    if value is None:
        return None
    try:
        points = int(value)
    except Exception:
        return None
    return points if points >= 0 else None


def save_user_points(points: int, path: str | Path | None = None) -> Path:
    if int(points) < 0:
        raise ValueError("points must be >= 0")
    data = load_user_config(path)
    data["tushare_points"] = int(points)
    return save_user_config(data, path)


def atomic_write_json(path: str | Path, data: Any, backup: bool = True) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if backup and path.exists():
        backup_path = path.with_suffix(path.suffix + "." + datetime.now().strftime("%Y%m%d%H%M%S") + ".bak")
        shutil.copy2(path, backup_path)
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def find_interfaces_json(explicit: str | None = None, cwd: str | Path | None = None) -> Path:
    if explicit:
        p = Path(explicit).expanduser().resolve()
        if not p.exists():
            raise FileNotFoundError(f"interfaces JSON not found: {p}")
        return p
    base = Path(cwd or os.getcwd()).resolve()
    project = base / "docs" / "tushare_interfaces_ai_optimized.json"
    if project.exists():
        return project
    if BUNDLED_INTERFACES_JSON.exists():
        return BUNDLED_INTERFACES_JSON
    raise FileNotFoundError("no tushare_interfaces_ai_optimized.json found")


def get_interface(data: dict[str, Any], api: str) -> dict[str, Any]:
    for item in data.get("interfaces", []):
        names = set(item.get("api_names") or [])
        names.add(item.get("api", ""))
        if api in names:
            return item
    raise KeyError(f"API not found in interface JSON: {api}")


def safe_relative(path: str | Path, base: str | Path) -> str:
    path = Path(path).resolve()
    base = Path(base).resolve()
    try:
        return str(path.relative_to(base))
    except ValueError:
        return str(path)



def sanitize_command(argv: list[str]) -> str:
    import shlex
    return shlex.join(argv)
