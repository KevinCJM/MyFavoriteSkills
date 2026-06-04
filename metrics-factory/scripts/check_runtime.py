#!/usr/bin/env python3
"""Check whether the active Python can run MetricsFactory jobs."""

from __future__ import annotations

import argparse
import sys
import traceback
from pathlib import Path
from typing import Any

from runtime_support import (
    OPTIONAL_DEPENDENCIES,
    REQUIRED_DEPENDENCIES,
    add_project_imports,
    dependency_versions,
    find_project_root,
    json_dump,
    python_summary,
    skill_dir,
)


def add_issue(result: dict[str, Any], level: str, code: str, message: str, **details: Any) -> None:
    item = {"level": level, "code": code, "message": message}
    item.update({k: v for k, v in details.items() if v is not None})
    result["issues"][level + "s"].append(item)


def check_runtime(project_root_arg: str | None) -> dict[str, Any]:
    result: dict[str, Any] = {
        "can_run": False,
        "project_root": None,
        "skill_dir": str(skill_dir()),
        "python": python_summary(),
        "dependencies": {},
        "optional_dependencies": {},
        "metricsfactory_import": {"ok": False},
        "issues": {"blockers": [], "warnings": [], "infos": []},
    }

    version = sys.version_info
    if version < (3, 10):
        add_issue(result, "blocker", "python_too_old", "Python 3.10+ is required by the skill scripts")
    elif version[:2] not in {(3, 11), (3, 12)}:
        add_issue(result, "warning", "python_version_not_recommended", "Python 3.11 or 3.12 is recommended")

    try:
        project_root = find_project_root(explicit=project_root_arg)
        result["project_root"] = str(project_root)
    except Exception as exc:
        add_issue(result, "blocker", "project_root_not_found", str(exc))
        project_root = None

    required = dependency_versions(REQUIRED_DEPENDENCIES)
    optional = dependency_versions(OPTIONAL_DEPENDENCIES)
    result["dependencies"] = required
    result["optional_dependencies"] = optional
    for package_name, status in required.items():
        if not status["ok"]:
            add_issue(result, "blocker", "dependency_import_failed", f"could not import {package_name}", error=status.get("error"))
    for package_name, status in optional.items():
        if not status["ok"]:
            add_issue(result, "warning", "optional_dependency_missing", f"optional dependency not available: {package_name}", error=status.get("error"))

    if project_root is not None:
        try:
            add_project_imports(project_root)
            from MetricsFactory.metrics_cal_config import create_period_metrics_map, create_rolling_metrics_map
            from MetricsFactory.metrics_factory import compute_metrics_for_period_initialize

            result["metricsfactory_import"] = {
                "ok": True,
                "period_window_count": len(create_period_metrics_map()),
                "rolling_window_count": len(create_rolling_metrics_map()),
                "period_entrypoint": getattr(compute_metrics_for_period_initialize, "__name__", "unknown"),
            }
        except Exception as exc:
            result["metricsfactory_import"] = {
                "ok": False,
                "error": str(exc),
                "traceback": traceback.format_exc(limit=4),
            }
            add_issue(result, "blocker", "metricsfactory_import_failed", "could not import MetricsFactory runtime", error=str(exc))

    project_hint = result["project_root"] or "<project-root>"
    result["suggested_setup_command"] = (
        f"python {skill_dir() / 'scripts' / 'setup_runtime.py'} --project-root {project_hint}"
    )
    result["suggested_run_command"] = (
        f"python {skill_dir() / 'scripts' / 'run_metrics_job.py'} --project-root {project_hint} --request job.json --dry-run"
    )
    result["can_run"] = len(result["issues"]["blockers"]) == 0
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Check MetricsFactory runtime environment.")
    parser.add_argument("--project-root", default=None, help="Path to the MetricsFactory source directory")
    args = parser.parse_args()

    result = check_runtime(args.project_root)
    print(json_dump(result))
    return 0 if result["can_run"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
