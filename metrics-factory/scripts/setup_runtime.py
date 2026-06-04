#!/usr/bin/env python3
"""Create a project-local Python environment for MetricsFactory."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import traceback
from pathlib import Path
from typing import Any

from runtime_support import PIP_REQUIREMENTS, find_project_root, json_dump, script_dir, venv_python_path


def add_issue(result: dict[str, Any], level: str, code: str, message: str, **details: Any) -> None:
    item = {"level": level, "code": code, "message": message}
    item.update({k: v for k, v in details.items() if v is not None})
    result["issues"][level + "s"].append(item)


def sanitize(text: str) -> str:
    # Avoid reflecting private package index credentials into JSON output.
    return re.sub(r"([A-Za-z][A-Za-z0-9+.-]*://)([^\s/@]+@)", r"\1<redacted>@", text)


def run_command(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, check=False)


def setup_runtime(args: argparse.Namespace) -> dict[str, Any]:
    result: dict[str, Any] = {
        "ok": False,
        "project_root": None,
        "venv_dir": None,
        "venv_python": None,
        "requirements": list(PIP_REQUIREMENTS),
        "steps": [],
        "check_runtime": None,
        "issues": {"blockers": [], "warnings": [], "infos": []},
    }

    try:
        project_root = find_project_root(explicit=args.project_root)
        result["project_root"] = str(project_root)
    except Exception as exc:
        add_issue(result, "blocker", "project_root_not_found", str(exc))
        return result

    venv_dir = Path(args.venv).expanduser()
    if not venv_dir.is_absolute():
        venv_dir = project_root / venv_dir
    venv_dir = venv_dir.resolve()
    venv_python = venv_python_path(venv_dir)
    result["venv_dir"] = str(venv_dir)
    result["venv_python"] = str(venv_python)

    base_python = args.python or os.environ.get("METRICS_FACTORY_PYTHON") or sys.executable
    create_cmd = [base_python, "-m", "venv", str(venv_dir)]
    created = run_command(create_cmd, project_root)
    result["steps"].append({"name": "create_venv", "returncode": created.returncode})
    if created.returncode != 0:
        add_issue(
            result,
            "blocker",
            "venv_create_failed",
            "could not create project-local venv",
            stderr=sanitize(created.stderr[-3000:]),
        )
        return result

    if not venv_python.exists():
        add_issue(result, "blocker", "venv_python_missing", "venv python was not created", path=str(venv_python))
        return result

    if not args.no_install:
        install_cmd = [str(venv_python), "-m", "pip", "install", "--disable-pip-version-check", "--no-input"]
        if args.index_url:
            install_cmd.extend(["--index-url", args.index_url])
        for extra in args.extra_index_url:
            install_cmd.extend(["--extra-index-url", extra])
        install_cmd.extend(PIP_REQUIREMENTS)
        installed = run_command(install_cmd, project_root)
        result["steps"].append({"name": "install_dependencies", "returncode": installed.returncode})
        if installed.returncode != 0:
            add_issue(
                result,
                "blocker",
                "dependency_install_failed",
                "pip install failed inside project-local venv",
                stderr=sanitize(installed.stderr[-3000:]),
            )
            return result

    check_cmd = [str(venv_python), str(script_dir() / "check_runtime.py"), "--project-root", str(project_root)]
    checked = run_command(check_cmd, project_root)
    result["steps"].append({"name": "check_runtime", "returncode": checked.returncode})
    try:
        result["check_runtime"] = json.loads(checked.stdout)
    except Exception:
        result["check_runtime"] = {"parse_error": True, "stdout": checked.stdout[-3000:], "stderr": sanitize(checked.stderr[-3000:])}
    if checked.returncode != 0:
        add_issue(result, "blocker", "runtime_check_failed", "created venv did not pass runtime check")
        return result

    result["ok"] = len(result["issues"]["blockers"]) == 0
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a project-local MetricsFactory runtime venv.")
    parser.add_argument("--project-root", default=None, help="Path to the MetricsFactory source directory")
    parser.add_argument("--venv", default=".metricsfactory-venv", help="Venv directory, relative to project root unless absolute")
    parser.add_argument("--python", default=None, help="Base Python used to create the venv")
    parser.add_argument("--index-url", default=None, help="Optional pip index URL")
    parser.add_argument("--extra-index-url", action="append", default=[], help="Optional extra pip index URL")
    parser.add_argument("--no-install", action="store_true", help="Create venv but skip dependency installation")
    args = parser.parse_args()

    try:
        result = setup_runtime(args)
    except Exception:
        result = {
            "ok": False,
            "issues": {
                "blockers": [
                    {
                        "level": "blocker",
                        "code": "setup_runtime_failed",
                        "message": "setup_runtime crashed",
                        "traceback": traceback.format_exc(limit=6),
                    }
                ],
                "warnings": [],
                "infos": [],
            },
        }
    print(json_dump(result))
    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
