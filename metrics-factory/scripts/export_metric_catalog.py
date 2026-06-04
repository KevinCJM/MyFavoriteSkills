#!/usr/bin/env python3
"""Export MetricsFactory metric catalog without importing numpy/pandas."""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
from typing import Any

from runtime_support import find_project_root


CONFIG_NAMES = {
    "period_list",
    "log_return_metrics_dict",
    "log_return_relative_metrics_dict",
    "rolling_metrics",
    "long_short_metrics",
}


def suspicious_metric_keys(metrics: dict[str, Any]) -> list[str]:
    result: list[str] = []
    for key in metrics:
        stripped = key.strip()
        has_cjk = any("\u4e00" <= char <= "\u9fff" for char in key)
        if key != stripped or has_cjk:
            result.append(key)
    return result


def load_config(config_path: Path) -> dict[str, Any]:
    tree = ast.parse(config_path.read_text(encoding="utf-8"))
    values: dict[str, Any] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id in CONFIG_NAMES:
                values[target.id] = ast.literal_eval(node.value)
    missing = CONFIG_NAMES - values.keys()
    if missing:
        raise ValueError(f"Missing config objects: {', '.join(sorted(missing))}")
    return values


def invert_metric_windows(metrics: dict[str, list[Any]]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for metric, spec in metrics.items():
        for window in spec[2]:
            result.setdefault(str(window), []).append(metric)
    return result


def build_catalog(project_root: Path) -> dict[str, Any]:
    values = load_config(project_root / "metrics_cal_config.py")
    period_metrics = values["log_return_metrics_dict"]
    rolling_metrics = values["rolling_metrics"]
    relative_metrics = values["log_return_relative_metrics_dict"]
    long_short_metrics = values["long_short_metrics"]
    return {
        "project_root": str(project_root),
        "period_list": values["period_list"],
        "period_metric_count": len(period_metrics),
        "period_metrics": list(period_metrics.keys()),
        "period_metrics_by_period": invert_metric_windows(period_metrics),
        "rolling_metric_count": len(rolling_metrics),
        "rolling_metrics": list(rolling_metrics.keys()),
        "rolling_metrics_by_window": invert_metric_windows(rolling_metrics),
        "relative_metric_count": len(relative_metrics),
        "relative_metrics": list(relative_metrics.keys()),
        "relative_metrics_suspicious_keys": suspicious_metric_keys(relative_metrics),
        "long_short_metric_count": len(long_short_metrics),
        "long_short_metrics": list(long_short_metrics.keys()),
        "long_short_metrics_suspicious_keys": suspicious_metric_keys(long_short_metrics),
        "not_wired_by_public_entrypoints": [
            "log_return_relative_metrics_dict",
            "long_short_metrics",
        ],
    }


def format_markdown(catalog: dict[str, Any]) -> str:
    period_keys = sorted(catalog["period_metrics_by_period"].keys())
    rolling_keys = sorted(catalog["rolling_metrics_by_window"].keys(), key=lambda x: int(x))
    lines = [
        "# MetricsFactory Metric Catalog",
        "",
        f"- Period metrics: {catalog['period_metric_count']}",
        f"- Rolling metrics: {catalog['rolling_metric_count']}",
        f"- Relative-history config entries not wired: {catalog['relative_metric_count']}",
        f"- Long/short config entries not wired: {catalog['long_short_metric_count']}",
        "",
        "## Default Period List",
        "",
        "`" + ", ".join(catalog["period_list"]) + "`",
        "",
        "## Configured Period Metric Windows",
        "",
    ]
    for key in period_keys:
        lines.append(f"- `{key}`: {len(catalog['period_metrics_by_period'][key])} metrics")
    lines.extend(["", "## Rolling Windows", ""])
    for key in rolling_keys:
        lines.append(f"- `{key}`: {len(catalog['rolling_metrics_by_window'][key])} metrics")
    lines.extend(
        [
            "",
            "## Period Metrics",
            "",
            "`" + ", ".join(catalog["period_metrics"]) + "`",
            "",
            "## Rolling Metrics",
            "",
            "`" + ", ".join(catalog["rolling_metrics"]) + "`",
            "",
            "## Not Wired By Public Entrypoints",
            "",
            "`" + ", ".join(catalog["not_wired_by_public_entrypoints"]) + "`",
            "",
            "Suspicious not-wired config keys are likely prose/comment string concatenation, not supported metrics:",
            "",
            "`" + ", ".join(catalog["relative_metrics_suspicious_keys"] + catalog["long_short_metrics_suspicious_keys"]) + "`",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=None)
    parser.add_argument("--format", choices=["json", "markdown"], default="json")
    args = parser.parse_args()

    project_root = find_project_root(start=Path.cwd().resolve(), explicit=args.project_root)
    catalog = build_catalog(project_root)
    if args.format == "markdown":
        print(format_markdown(catalog))
    else:
        print(json.dumps(catalog, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
