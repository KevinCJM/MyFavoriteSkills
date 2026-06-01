#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from tushare_runtime import SKILL_ROOT, atomic_write_json, find_interfaces_json, get_interface, load_json, safe_relative, sha256_file


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Solidify a smoke-tested Tushare fetch script")
    parser.add_argument("--api", required=True)
    parser.add_argument("--script", required=True)
    parser.add_argument("--smoke-result", required=True)
    parser.add_argument("--interfaces-json")
    parser.add_argument("--target", choices=["skill", "project"], default="skill")
    parser.add_argument("--target-script-path")
    parser.add_argument("--overwrite-solidified", action="store_true")
    parser.add_argument("--update-both-json", action="store_true")
    return parser.parse_args()


def load_smoke(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).expanduser().resolve().read_text(encoding="utf-8"))
    if data.get("status") != "passed":
        raise RuntimeError("smoke result did not pass")
    return data


def target_script_path(args: argparse.Namespace) -> Path:
    if args.target_script_path:
        return Path(args.target_script_path).expanduser().resolve()
    if args.target == "skill":
        return SKILL_ROOT / "scripts" / "solidified" / f"{args.api}.py"
    raise RuntimeError("--target-script-path is required when --target project")


def ensure_under(path: Path, base: Path, label: str) -> None:
    try:
        path.resolve().relative_to(base.resolve())
    except ValueError:
        raise RuntimeError(f"{label} must be under {base} for portable metadata: {path}")


def update_interface_json(path: Path, api: str, patch: dict[str, Any], overwrite: bool) -> None:
    data = load_json(path)
    item = get_interface(data, api)
    if item.get("solidified_script") and not overwrite:
        raise RuntimeError("solidified_script already exists; pass --overwrite-solidified to replace it")
    item["solidified_script"] = patch
    atomic_write_json(path, data, backup=True)


def resolve_smoke_interfaces_path(value: str | None) -> Path | None:
    if not value:
        return None
    if value.startswith("$SKILL_DIR/"):
        return (SKILL_ROOT / value[len("$SKILL_DIR/") :]).resolve()
    if value.startswith("./"):
        return (Path.cwd() / value[2:]).resolve()
    p = Path(value).expanduser()
    if p.exists():
        return p.resolve()
    return None


def main() -> int:
    args = parse_args()
    script = Path(args.script).expanduser().resolve()
    smoke = load_smoke(args.smoke_result)
    if smoke.get("api") != args.api:
        raise RuntimeError(f"smoke API mismatch: {smoke.get('api')} != {args.api}")
    current_script_hash = sha256_file(script)
    if smoke.get("script_sha256") != current_script_hash:
        raise RuntimeError("script hash does not match smoke result")
    smoke_interfaces = resolve_smoke_interfaces_path(smoke.get("interfaces_json_path"))
    interfaces = find_interfaces_json(args.interfaces_json or (str(smoke_interfaces) if smoke_interfaces else None))
    if sha256_file(interfaces) != smoke.get("interfaces_json_sha256"):
        raise RuntimeError("interfaces JSON hash does not match smoke result")
    destination = target_script_path(args)
    if args.target == "project":
        ensure_under(destination, Path.cwd(), "project solidified script")
    else:
        ensure_under(destination, SKILL_ROOT, "skill solidified script")
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and not args.overwrite_solidified:
        raise RuntimeError(f"target script already exists: {destination}")
    shutil.copy2(script, destination)
    relative_base = SKILL_ROOT if args.target == "skill" else Path.cwd()
    runtime_rate = smoke.get("runtime_rate_limit_policy") or {}
    patch = {
        "status": "solidified",
        "script_path": safe_relative(destination, relative_base),
        "script_sha256": current_script_hash,
        "runtime_dependency": "scripts/tushare_runtime.py" if args.target == "skill" else "",
        "interfaces_json_sha256": sha256_file(interfaces),
        "smoke_tested_at": smoke.get("ended_at") or datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "smoke_command": smoke.get("command_sanitized", ""),
        "output_format": "parquet",
        "default_output_dir": f"./data/tushare/{args.api}",
        "rate_limit_policy": {
            "requests_per_minute": runtime_rate.get("requests_per_minute_used") or runtime_rate.get("requests_per_minute"),
            "source": runtime_rate.get("source", "generated_script"),
            "source_text": runtime_rate.get("source_text", ""),
        },
        "notes": [
            "Solidified only after a passed smoke test whose script and interface JSON hashes matched.",
        ],
    }
    update_targets = [interfaces]
    project_json = Path.cwd() / "docs" / "tushare_interfaces_ai_optimized.json"
    skill_json = SKILL_ROOT / "references" / "tushare_interfaces_ai_optimized.json"
    if not args.update_both_json and interfaces.resolve() == skill_json.resolve() and project_json.exists():
        print(
            "warning: project-local docs/tushare_interfaces_ai_optimized.json exists; this run updates only the skill-bundled JSON.",
            file=sys.stderr,
        )
    if args.update_both_json:
        if not project_json.exists() or not skill_json.exists():
            raise RuntimeError("--update-both-json requires both project and skill interface JSON files")
        if sha256_file(project_json) != sha256_file(skill_json):
            raise RuntimeError("--update-both-json requires project and skill JSON to match before update")
        update_targets = [project_json.resolve(), skill_json.resolve()]
    for target_json in dict.fromkeys(update_targets):
        update_interface_json(target_json, args.api, patch, args.overwrite_solidified)
    result = {
        "status": "solidified",
        "api": args.api,
        "script_path": str(destination),
        "interfaces_json": str(interfaces),
        "script_sha256": current_script_hash,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
