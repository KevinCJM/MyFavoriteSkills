#!/usr/bin/env python3
"""Shared runtime helpers for portable MetricsFactory skill scripts."""

from __future__ import annotations

import json
import os
import platform
import sys
import types
from pathlib import Path
from typing import Any


PROJECT_MARKERS = (
    "metrics_factory.py",
    "metrics_cal_config.py",
    "period_metrics_cal.py",
    "rolling_metrics_cal.py",
)

REQUIRED_DEPENDENCIES = (
    ("numpy", "numpy"),
    ("pandas", "pandas"),
    ("scipy", "scipy"),
    ("numba", "numba"),
    ("pyarrow", "pyarrow"),
    ("tqdm", "tqdm"),
    ("dateutil", "python-dateutil"),
)

OPTIONAL_DEPENDENCIES = (
    ("psutil", "psutil"),
)

PIP_REQUIREMENTS = (
    "numpy>=1.26,<2.1",
    "pandas>=2.2,<3.1",
    "scipy>=1.11",
    "numba>=0.60",
    "pyarrow>=15",
    "python-dateutil>=2.8",
    "tqdm>=4.60",
    "psutil>=5.9",
)


def script_dir() -> Path:
    return Path(__file__).resolve().parent


def skill_dir() -> Path:
    return script_dir().parent


def is_project_root(path: Path) -> bool:
    return all((path / marker).exists() for marker in PROJECT_MARKERS)


def find_project_root(start: Path | None = None, explicit: str | Path | None = None) -> Path:
    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(explicit).expanduser())
    env_root = os.environ.get("METRICS_FACTORY_PROJECT_ROOT")
    if env_root:
        candidates.append(Path(env_root).expanduser())
    if start is not None:
        start = start.resolve()
        candidates.extend([start, *start.parents])
    current = Path.cwd().resolve()
    candidates.extend([current, *current.parents])
    here = script_dir()
    candidates.extend([here, *here.parents])

    seen: set[Path] = set()
    for candidate in candidates:
        candidate = candidate.resolve()
        if candidate in seen:
            continue
        seen.add(candidate)
        if is_project_root(candidate):
            return candidate
    raise FileNotFoundError(
        "Could not locate MetricsFactory project root. Pass --project-root or set METRICS_FACTORY_PROJECT_ROOT."
    )


def add_project_imports(project_root: Path) -> None:
    project_root = project_root.resolve()
    parent = str(project_root.parent)
    if parent not in sys.path:
        sys.path.insert(0, parent)

    module = sys.modules.get("MetricsFactory")
    if module is None or not hasattr(module, "__path__"):
        module = types.ModuleType("MetricsFactory")
        module.__package__ = "MetricsFactory"
        module.__path__ = [str(project_root)]  # type: ignore[attr-defined]
        module.__file__ = str(project_root / "__init__.py")
        sys.modules["MetricsFactory"] = module
        return

    paths = list(getattr(module, "__path__", []))
    root_text = str(project_root)
    if root_text not in paths:
        paths.insert(0, root_text)
        module.__path__ = paths  # type: ignore[attr-defined]


def venv_python_path(venv_dir: Path) -> Path:
    if platform.system().lower().startswith("win"):
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def dependency_versions(module_names: tuple[tuple[str, str], ...]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for import_name, package_name in module_names:
        try:
            module = __import__(import_name)
            result[package_name] = {
                "import": import_name,
                "ok": True,
                "version": getattr(module, "__version__", "unknown"),
            }
        except Exception as exc:
            result[package_name] = {
                "import": import_name,
                "ok": False,
                "version": None,
                "error": str(exc),
            }
    return result


def python_summary() -> dict[str, str]:
    return {
        "executable": sys.executable,
        "version": sys.version.split()[0],
        "machine": platform.machine(),
        "platform": platform.platform(),
    }


def json_dump(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2, default=str)
