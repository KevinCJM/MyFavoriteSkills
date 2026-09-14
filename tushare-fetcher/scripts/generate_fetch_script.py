#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import stat
from pathlib import Path
from typing import Any

from tushare_runtime import find_interfaces_json, get_interface, load_json, load_user_points, save_user_points, sha256_file, user_config_path


SEPARATE_PERMISSION_PATTERNS = [
    r"本接口需单独开权限",
    r"跟积分没关系",
    r"单独开权限",
    r"开通正式权限",
    r"正式权限",
    r"申请权限",
]

KNOWN_STRATEGIES = {
    "stock_basic": "single_call",
    "trade_cal": "date_range",
    "daily_basic": "date_loop",
}

AMBIGUOUS_STRATEGY_APIS = {"daily", "weekly", "monthly"}


def classify_permission(item: dict[str, Any], points: int, confirm_entitlement: bool) -> dict[str, Any]:
    limits = "；".join(item.get("limits") or [])
    thresholds = [int(x) for x in item.get("point_thresholds") or []]
    separate = any(re.search(p, limits) for p in SEPARATE_PERMISSION_PATTERNS)
    if thresholds:
        min_point = min(thresholds)
        max_point = max(thresholds)
        points_met: bool | str = min_point <= points
    else:
        min_point = None
        max_point = None
        points_met = "unknown"
    if separate:
        entitlement = "confirmed" if confirm_entitlement else "separate_permission_required"
        risk = "medium" if confirm_entitlement else "high"
    elif points_met is True:
        entitlement = "unconfirmed"
        risk = "low"
    elif points_met is False:
        entitlement = "unconfirmed"
        risk = "high"
    else:
        entitlement = "unknown"
        risk = "medium"
    return {
        "points_threshold_met": points_met,
        "min_points": min_point,
        "max_points": max_point,
        "entitlement_status": entitlement,
        "permission_risk": risk,
        "separate_permission_detected": separate,
        "source_text": item.get("limits") or [],
    }


def infer_rate_limit(item: dict[str, Any], points: int) -> dict[str, Any]:
    texts = item.get("limits") or []
    candidates: list[dict[str, Any]] = []
    for text in texts:
        compact = re.sub(r"\s+", "", text)
        for m in re.finditer(r"(\d{2,6})积分[^，。；]*?每分钟[^，。；]*?(\d{1,5})次", compact):
            candidates.append({"threshold": int(m.group(1)), "rpm": int(m.group(2)), "source_text": text})
        for m in re.finditer(r"每分钟[^，。；]*?(\d{1,5})次", compact):
            if not any(c.get("source_text") == text and c.get("rpm") == int(m.group(1)) for c in candidates):
                candidates.append({"threshold": None, "rpm": int(m.group(1)), "source_text": text})
    eligible = [c for c in candidates if c["threshold"] is None or c["threshold"] <= points]
    if eligible:
        chosen = max(eligible, key=lambda c: c["rpm"] if c["threshold"] is not None else min(c["rpm"], 30))
        return {"requests_per_minute": int(chosen["rpm"]), "source": "docs_text", "source_text": chosen["source_text"], "candidates": candidates}
    return {"requests_per_minute": 6, "source": "fallback_default", "source_text": "", "candidates": candidates}


def infer_strategy(api: str, item: dict[str, Any], override: str | None) -> str:
    if override:
        return override
    if api in AMBIGUOUS_STRATEGY_APIS:
        return "user_params"
    if api in KNOWN_STRATEGIES:
        return KNOWN_STRATEGIES[api]
    names = {p.get("name", "") for p in item.get("input_params", [])}
    if {"start_date", "end_date"} & names:
        return "date_range"
    if "trade_date" in names or "ann_date" in names or "cal_date" in names:
        return "date_loop"
    if "ts_code" in names:
        return "user_params"
    return "single_call"


def decide_generation(permission: dict[str, Any], strategy: str, skeleton_only: bool) -> tuple[str, list[str]]:
    reasons: list[str] = []
    if skeleton_only:
        return "skeleton_only", ["requested skeleton-only generation"]
    if permission["points_threshold_met"] is False:
        return "refuse", ["user points are below the lowest explicit threshold"]
    if permission["entitlement_status"] == "separate_permission_required":
        return "skeleton_only", ["separate permission detected and entitlement not confirmed"]
    if strategy == "user_params":
        return "skeleton_only", ["strategy requires explicit params, params file, or an explicit --strategy choice"]
    return "executable", reasons


def build_contract(api, strategy, permission, rate, skeleton, default_output_dir, item, interfaces_sha):
    limits = "；".join(item.get("limits") or [])
    caps = [int(m.group(1)) for m in re.finditer(
        r"(?:最多|最大|限量)[^\d，。；]{0,12}(\d+)(?:行|条|[，。；]|$)", limits)]
    inputs = item.get("input_params") or []
    outputs = item.get("output_params") or []
    return {
        "api": api, "strategy": strategy, "permission": permission, "rate": rate,
        "skeleton": skeleton, "default_output_dir": default_output_dir,
        "interfaces_json_sha256": interfaces_sha,
        "row_cap": min(caps) if caps else None,
        "input_fields": [p["name"] for p in inputs],
        "required_fields": [p["name"] for p in inputs if str(p.get("required", "")).upper() == "Y"],
        "output_fields": [p["name"] for p in outputs],
        "default_fields": [p["name"] for p in outputs if str(p.get("default_display", "")).upper() == "Y"],
    }


def render_script(api, strategy, permission, rate, skeleton, default_output_dir, *, item, interfaces_sha):
    contract = build_contract(api, strategy, permission, rate, skeleton, default_output_dir, item, interfaces_sha)
    source = Path(__file__).with_name("fetch_runtime.py").read_text(encoding="utf-8")
    return source.replace("CONTRACT = {}", "CONTRACT = " + repr(contract), 1)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a Tushare Parquet fetch script")
    parser.add_argument("--api", required=True)
    parser.add_argument("--points", type=int, help="User Tushare points. If omitted, read from user config.")
    parser.add_argument("--user-config", help="Optional user config path for saved Tushare points")
    parser.add_argument("--save-points", action="store_true", help="Persist --points to user config after validation")
    parser.add_argument("--interfaces-json")
    parser.add_argument("--output-script", required=True)
    parser.add_argument("--strategy", choices=["single_call", "date_loop", "code_loop", "date_range", "param_grid", "user_params"])
    parser.add_argument("--default-output-dir")
    parser.add_argument("--skeleton-only", action="store_true")
    parser.add_argument("--confirm-entitlement", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    points = args.points if args.points is not None else load_user_points(args.user_config)
    if points is None:
        print(json.dumps({
            "status": "needs_points",
            "message": "Tushare points are required. Ask the user for their current points, then save them with configure_points.py --points N.",
            "config_path": str(user_config_path(args.user_config)),
        }, ensure_ascii=False, indent=2))
        return 3
    if points < 0:
        raise ValueError("--points must be >= 0")
    if args.points is not None and args.save_points:
        save_user_points(args.points, args.user_config)
    interfaces_path = find_interfaces_json(args.interfaces_json)
    data = load_json(interfaces_path)
    item = get_interface(data, args.api)
    api = item.get("api") or args.api
    permission = classify_permission(item, points, args.confirm_entitlement)
    rate = infer_rate_limit(item, points)
    strategy = infer_strategy(api, item, args.strategy)
    mode, reasons = decide_generation(permission, strategy, args.skeleton_only)
    if mode == "refuse":
        print(json.dumps({"status": "refused", "api": api, "reasons": reasons, "permission": permission}, ensure_ascii=False, indent=2))
        return 2
    skeleton = mode == "skeleton_only"
    default_output_dir = args.default_output_dir or f"./data/tushare/{api}"
    script = render_script(api, strategy, permission, rate, skeleton, default_output_dir, item=item, interfaces_sha=sha256_file(interfaces_path))
    out = Path(args.output_script).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(script, encoding="utf-8")
    out.chmod(out.stat().st_mode | stat.S_IXUSR)
    report = {
        "status": "generated",
        "api": api,
        "mode": mode,
        "reasons": reasons,
        "script_path": str(out),
        "script_sha256": sha256_file(out),
        "interfaces_json_path": str(interfaces_path),
        "interfaces_json_sha256": sha256_file(interfaces_path),
        "points": points,
        "points_source": "argument" if args.points is not None else "user_config",
        "user_config_path": str(user_config_path(args.user_config)),
        "permission": permission,
        "rate_limit_policy": rate,
        "strategy": strategy,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
