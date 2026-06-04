#!/usr/bin/env python3
"""Export MetricsFactory metric catalog without importing numpy/pandas."""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
from typing import Any

from runtime_support import find_project_root


PERIOD_INPUT_DEPENDENCIES = {
    "volume": {"VolAvg", "VolSlope", "VolVolatility"},
    "high_price": {"MaxHigh", "HLDiff", "AvgHigh"},
    "low_price": {"MinLow", "HLDiff", "AvgLow"},
    "close_price": {
        "MaxDrawDown",
        "MaxDrawDownDays",
        "ReturnDrawDownRatio",
        "DrawDownSlope",
        "UlcerIndex",
        "MartinRatio",
        "NewHighRatio",
        "NetEquitySlope",
        "EquitySmoothness",
    },
}
ROLLING_INPUT_DEPENDENCIES = {
    "volume": {
        "VolMA",
        "VolMADiff",
        "OBV",
        "MAOBV",
        "MAOBVDiff",
        "PVT",
        "MAPVT",
        "MAPVTDiff",
        "VR",
        "MAVR-3",
        "MAVRDiff-3",
        "MAVR-6",
        "MAVRDiff-6",
        "MAVR-12",
        "MAVRDiff-12",
    },
    "open_price": {
        "AR",
        "BRARDiff",
        "ARDiff-40",
        "ARDiff-180",
        "DKX",
        "DKXDiff",
        "MADKX-5",
        "MADKXDiff-5",
        "MADKX-10",
        "MADKXDiff-10",
        "MADKX-15",
        "MADKXDiff-15",
    },
    "high_price": {
        "L",
        "H",
        "RSV",
        "KDJ-K-3",
        "KDJ-D-3",
        "KDJ-J-3",
        "KDJ-KD-3",
        "KDJ-KJ-3",
        "KDJ-DJ-3",
        "CCI",
        "CR",
        "MACR-10-5",
        "MACRDiff-10-5",
        "MACR-20-9",
        "MACRDiff-20-9",
        "MACR-40-17",
        "MACRDiff-40-17",
        "MACR-62-28",
        "MACRDiff-62-28",
        "AR",
        "BR",
        "BRARDiff",
        "ARDiff-40",
        "ARDiff-180",
        "BRDiff-400",
        "BRDiff-40",
        "TR",
        "PDI",
        "MDI",
        "PDIMDIDiff",
        "ADX-6",
        "ADXR-6-6",
        "ADXRDiff-6-6",
        "ADXR-6-14",
        "ADXRDiff-6-14",
        "DKX",
        "DKXDiff",
        "MADKX-5",
        "MADKXDiff-5",
        "MADKX-10",
        "MADKXDiff-10",
        "MADKX-15",
        "MADKXDiff-15",
    },
    "low_price": {
        "L",
        "H",
        "RSV",
        "KDJ-K-3",
        "KDJ-D-3",
        "KDJ-J-3",
        "KDJ-KD-3",
        "KDJ-KJ-3",
        "KDJ-DJ-3",
        "CCI",
        "CR",
        "MACR-10-5",
        "MACRDiff-10-5",
        "MACR-20-9",
        "MACRDiff-20-9",
        "MACR-40-17",
        "MACRDiff-40-17",
        "MACR-62-28",
        "MACRDiff-62-28",
        "AR",
        "BR",
        "BRARDiff",
        "ARDiff-40",
        "ARDiff-180",
        "BRDiff-400",
        "BRDiff-40",
        "TR",
        "PDI",
        "MDI",
        "PDIMDIDiff",
        "ADX-6",
        "ADXR-6-6",
        "ADXRDiff-6-6",
        "ADXR-6-14",
        "ADXRDiff-6-14",
        "DKX",
        "DKXDiff",
        "MADKX-5",
        "MADKXDiff-5",
        "MADKX-10",
        "MADKXDiff-10",
        "MADKX-15",
        "MADKXDiff-15",
    },
}
METRIC_TEXT_OVERRIDES = {
    "BollUpDo-2": ("布林带宽度", "BollUpDo = BollUp - BollDo，2 倍标准差上下轨之间的距离"),
    "BollUpDo-3": ("布林带宽度", "BollUpDo = BollUp - BollDo，3 倍标准差上下轨之间的距离"),
    "H": ("过去N天的最高价 (KDJ相关指标)", "H = Max(N天最高价)"),
    "KDJ-KJ-3": ("KDJ 指标的 K 值与 J 值之差", "KDJ-KJ = K - J"),
    "KDJ-DJ-3": ("KDJ 指标的 D 值与 J 值之差", "KDJ-DJ = D - J"),
    "TRIX": ("TRIX 指标 (三重指数平滑移动平均)", "TRIX = 三重 EMA 的单期变化率 * 100"),
    "MATRIX-3": ("TRIX 的移动平均", "MATRIX = TRIX 的 3 日移动平均"),
    "MATRIXDiff-3": ("TRIX 移动平均与当前 TRIX 的差值", "MATRIXDiff = MATRIX - TRIX"),
    "MATRIX-5": ("TRIX 的移动平均", "MATRIX = TRIX 的 5 日移动平均"),
    "MATRIXDiff-5": ("TRIX 移动平均与当前 TRIX 的差值", "MATRIXDiff = MATRIX - TRIX"),
    "CR": ("CR 指标 (现价能量强度指标)", "CR = N日 sum(max(0, H - 昨日中间价)) / sum(max(0, 昨日中间价 - L)) * 100"),
    "VR": ("VR 指标 (成交量变异率)", "VR = (上涨日成交量 + 0.5 * 平盘日成交量) / (下跌日成交量 + 0.5 * 平盘日成交量) * 100"),
    "AR": ("AR（人气指标）", "AR = N日 sum(H - O) / sum(O - L) * 100"),
    "BR": ("BR（买气指标）", "BR = N日 sum(max(0, H - 昨收)) / sum(max(0, 昨收 - L)) * 100"),
    "ARDiff-180": ("AR 与 180 之差", "ARDiff-180 = AR - 180"),
    "MABIAS-10": ("乖离率的移动均值", "MABIAS-10 = BIAS 的 10 日移动均值"),
    "MADKX-5": ("DKX 指标的移动平均", "MADKX-5 = DKX 的 5 日移动平均"),
    "MADKX-10": ("DKX 指标的移动平均", "MADKX-10 = DKX 的 10 日移动平均"),
    "MADKX-15": ("DKX 指标的移动平均", "MADKX-15 = DKX 的 15 日移动平均"),
}
PERIOD_DEPENDENCY_OVERRIDES = {
    "VolAvg": ["volume"],
    "VolSlope": ["volume"],
    "VolVolatility": ["volume"],
    "MaxHigh": ["high_price"],
    "MinLow": ["low_price"],
    "HLDiff": ["high_price", "low_price"],
    "AvgHigh": ["high_price"],
    "AvgLow": ["low_price"],
    "MaxDrawDown": ["close_price"],
    "MaxDrawDownDays": ["close_price"],
    "DrawDownSlope": ["close_price"],
    "UlcerIndex": ["close_price"],
    "NewHighRatio": ["close_price"],
    "NetEquitySlope": ["close_price"],
    "EquitySmoothness": ["close_price"],
}
ROLLING_DEPENDENCY_OVERRIDES = {
    "VolMA": ["volume"],
    "VolMADiff": ["volume"],
    "L": ["low_price"],
    "H": ["high_price"],
    "AR": ["open_price", "high_price", "low_price"],
    "ARDiff-40": ["open_price", "high_price", "low_price"],
    "ARDiff-180": ["open_price", "high_price", "low_price"],
    "CR": ["high_price", "low_price"],
    "MACR-10-5": ["high_price", "low_price"],
    "MACRDiff-10-5": ["high_price", "low_price"],
    "MACR-20-9": ["high_price", "low_price"],
    "MACRDiff-20-9": ["high_price", "low_price"],
    "MACR-40-17": ["high_price", "low_price"],
    "MACRDiff-40-17": ["high_price", "low_price"],
    "MACR-62-28": ["high_price", "low_price"],
    "MACRDiff-62-28": ["high_price", "low_price"],
}
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


def metric_text(metric: str, spec: list[Any]) -> tuple[str, str]:
    if metric in METRIC_TEXT_OVERRIDES:
        return METRIC_TEXT_OVERRIDES[metric]
    return str(spec[0]), str(spec[1])


def period_dependencies(metric: str) -> list[str]:
    if metric in PERIOD_DEPENDENCY_OVERRIDES:
        return PERIOD_DEPENDENCY_OVERRIDES[metric]
    deps = {"log_return"}
    for dependency, metrics in PERIOD_INPUT_DEPENDENCIES.items():
        if metric in metrics:
            deps.add(dependency)
    return sorted(deps)


def rolling_dependencies(metric: str) -> list[str]:
    if metric in ROLLING_DEPENDENCY_OVERRIDES:
        return ROLLING_DEPENDENCY_OVERRIDES[metric]
    deps = {"close_price"}
    for dependency, metrics in ROLLING_INPUT_DEPENDENCIES.items():
        if metric in metrics:
            deps.add(dependency)
    return sorted(deps)


def risk_tags(metric: str, dependencies: list[str]) -> list[str]:
    tags: list[str] = []
    if "volume" in dependencies:
        tags.append("requires_real_volume")
    if any(dependency in dependencies for dependency in ("open_price", "high_price", "low_price")):
        tags.append("requires_consistent_ohlc_basis")
    if "close_price" in dependencies or "log_return" in dependencies:
        tags.append("prefer_point_in_time_adjusted_nav_or_price")
    if metric in {"OBV", "PVT"}:
        tags.append("stateful_from_series_start")
    return tags


def build_metric_index(project_root: Path) -> dict[str, Any]:
    values = load_config(project_root / "metrics_cal_config.py")
    period_metrics = values["log_return_metrics_dict"]
    rolling_metrics = values["rolling_metrics"]
    period_windows = invert_metric_windows(period_metrics)
    rolling_windows = invert_metric_windows(rolling_metrics)
    default_period_set = set(str(period) for period in values["period_list"])

    metrics: list[dict[str, Any]] = []
    for metric, spec in period_metrics.items():
        label, calculation = metric_text(metric, spec)
        windows = [str(window) for window in spec[2]]
        executable_windows = [window for window in windows if metric in period_windows.get(window, [])]
        default_windows = [window for window in executable_windows if window in default_period_set]
        dependencies = period_dependencies(metric)
        metrics.append(
            {
                "name": metric,
                "kind": "period",
                "is_executable": True,
                "label_zh": label,
                "calculation": calculation,
                "output_column_pattern": f"{metric}:<period>",
                "windows": executable_windows,
                "default_windows": default_windows,
                "requires_explicit_windows": [window for window in executable_windows if window not in default_period_set],
                "input_dependencies": dependencies,
                "risk_tags": risk_tags(metric, dependencies),
            }
        )
    for metric, spec in rolling_metrics.items():
        label, calculation = metric_text(metric, spec)
        windows = [str(window) for window in spec[2]]
        executable_windows = [window for window in windows if metric in rolling_windows.get(window, [])]
        dependencies = rolling_dependencies(metric)
        metrics.append(
            {
                "name": metric,
                "kind": "rolling",
                "is_executable": True,
                "label_zh": label,
                "calculation": calculation,
                "output_column_pattern": f"{metric}:<rolling_window>",
                "windows": executable_windows,
                "default_windows": executable_windows,
                "requires_explicit_windows": [],
                "input_dependencies": dependencies,
                "risk_tags": risk_tags(metric, dependencies),
            }
        )

    not_executable = []
    for config_name in ("log_return_relative_metrics_dict", "long_short_metrics"):
        for metric, spec in values[config_name].items():
            label, calculation = metric_text(metric, spec)
            not_executable.append(
                {
                    "name": metric,
                    "source_config": config_name,
                    "is_executable": False,
                    "label_zh": label,
                    "calculation": calculation,
                    "reason": "not wired by current public entrypoints",
                }
            )

    return {
        "schema_version": "1.0",
        "source": "metrics_cal_config.py",
        "portability": "no local absolute paths",
        "counts": {
            "executable_period_metrics": len(period_metrics),
            "executable_rolling_metrics": len(rolling_metrics),
            "not_executable_config_entries": len(not_executable),
        },
        "period_windows": list(period_windows.keys()),
        "default_period_list": values["period_list"],
        "rolling_windows": sorted(rolling_windows.keys(), key=lambda value: int(value)),
        "metrics": metrics,
        "not_executable_config_entries": not_executable,
        "selection_rules": {
            "period_output_column": "指标名:区间",
            "rolling_output_column": "指标名:滚动天数",
            "period_30d_35d_70d": "executable but not in default period_list; pass explicitly",
            "default_unmapped_periods": ["3y", "5y", "mtd", "qtd", "ytd", "max"],
            "rolling_metric_subset": "not supported by V1 job schema; leave selection.rolling_metrics null",
            "same_day_signal": "outputs dated t include t end-of-day inputs; shift features before same-day pre-close use",
        },
    }


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
    parser.add_argument("--format", choices=["json", "markdown", "index"], default="json")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    project_root = find_project_root(start=Path.cwd().resolve(), explicit=args.project_root)
    if args.format == "index":
        content = json.dumps(build_metric_index(project_root), ensure_ascii=False, indent=2)
    else:
        catalog = build_catalog(project_root)
        if args.format == "markdown":
            content = format_markdown(catalog)
        else:
            content = json.dumps(catalog, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(content + "\n", encoding="utf-8")
    else:
        print(content)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
