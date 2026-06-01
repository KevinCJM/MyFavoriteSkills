#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import stat
import textwrap
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


SCRIPT_TEMPLATE = r'''#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Any

API = __API_JSON__
STRATEGY = __STRATEGY_JSON__
PERMISSION_ANALYSIS = __PERMISSION_JSON__
RATE_LIMIT_POLICY = __RATE_JSON__
SKELETON_ONLY = __SKELETON_JSON__
DEFAULT_OUTPUT_DIR = __DEFAULT_OUTPUT_DIR_JSON__

# Permission warning:
# Points are only a documentation-derived threshold. Real access still depends
# on the Tushare account's actual entitlements and API responses.


def load_token(token_env_name: str, allow_config_token: bool) -> tuple[str, str]:
    token = os.environ.get(token_env_name, "")
    if token:
        return token, f"env:{token_env_name}"
    if allow_config_token:
        cfg = Path.cwd() / "config.py"
        if cfg.exists():
            spec = importlib.util.spec_from_file_location("_tushare_config", str(cfg))
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)  # type: ignore[union-attr]
                value = getattr(mod, "TUSHARE_TOKEN", "")
                if value:
                    return str(value), "config.py"
    raise RuntimeError("Tushare token is missing. Set TUSHARE_TOKEN or pass --allow-config-token.")


class RateLimiter:
    def __init__(self, requests_per_minute: float) -> None:
        self.interval = 60.0 / max(float(requests_per_minute), 0.1)
        self.last = 0.0

    def wait(self) -> None:
        delay = self.interval - (time.monotonic() - self.last)
        if delay > 0:
            time.sleep(delay)
        self.last = time.monotonic()


def read_param_records(args: argparse.Namespace) -> tuple[list[dict[str, Any]], bool]:
    if args.params_json:
        obj = json.loads(args.params_json)
        explicit = True
    elif args.params_file:
        obj = json.loads(Path(args.params_file).read_text(encoding="utf-8"))
        explicit = True
    else:
        obj = [{}]
        explicit = False
    if isinstance(obj, dict):
        records = [obj]
    elif isinstance(obj, list) and all(isinstance(x, dict) for x in obj):
        records = obj
    else:
        raise ValueError("params must be a JSON object or list of objects")
    return records, explicit


def apply_common_args(records: list[dict[str, Any]], explicit: bool, args: argparse.Namespace) -> list[dict[str, Any]]:
    common = {}
    for key in ["ts_code", "trade_date", "start_date", "end_date", "exchange"]:
        value = getattr(args, key)
        if value:
            common[key] = value
    if args.smoke and not explicit and not common and STRATEGY == "date_range":
        today = datetime.now().strftime("%Y%m%d")
        common.update({"start_date": today, "end_date": today})
    if common:
        return [{**common, **r} for r in records]
    if not explicit and STRATEGY in {"code_loop", "date_loop", "user_params", "param_grid"}:
        raise RuntimeError("This API strategy requires --params-json, --params-file, or explicit CLI params.")
    return records


def create_client(token: str):
    import tushare as ts  # type: ignore
    ts.set_token(token)
    return ts.pro_api()


def call_tushare(pro, params: dict[str, Any], fields: str | None):
    call_params = {k: v for k, v in params.items() if v is not None and v != ""}
    if fields:
        call_params["fields"] = fields
    try:
        return pro.query(API, **call_params)
    except Exception as first_error:
        method = getattr(pro, API, None)
        if callable(method):
            return method(**call_params)
        raise first_error


def write_parquet_atomic(df, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    os.close(fd)
    tmp = Path(tmp_name)
    try:
        df.to_parquet(tmp, index=False)
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()


class OutputLock:
    def __init__(self, output_dir: Path, api: str) -> None:
        self.path = output_dir / f".{api}.lock"
        self.fd = None

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.fd = os.open(str(self.path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(self.fd, str(os.getpid()).encode("utf-8"))
        return self

    def __exit__(self, exc_type, exc, tb):
        if self.fd is not None:
            os.close(self.fd)
        try:
            self.path.unlink()
        except FileNotFoundError:
            pass


def write_output(df, output_dir: Path, args: argparse.Namespace) -> list[str]:
    import pandas as pd
    output_dir.mkdir(parents=True, exist_ok=True)
    if args.limit_rows is not None:
        df = df.head(args.limit_rows)
    files: list[str] = []
    if args.partition_by:
        if args.partition_by not in df.columns:
            raise RuntimeError(f"partition column missing: {args.partition_by}")
        groups = list(df.groupby(args.partition_by, dropna=False))
        if len(groups) > args.max_output_files:
            raise RuntimeError(f"too many output files: {len(groups)} > {args.max_output_files}")
        for value, part in groups:
            safe_value = str(value).replace("/", "_").replace("\\", "_")
            path = output_dir / f"{API}_{args.partition_by}={safe_value}.parquet"
            write_single(part, path, args)
            files.append(str(path))
    else:
        path = output_dir / f"{API}.parquet"
        write_single(df, path, args)
        files.append(str(path))
    return files


def write_single(df, path: Path, args: argparse.Namespace) -> None:
    import pandas as pd
    if args.overwrite and args.append:
        raise RuntimeError("--overwrite and --append are mutually exclusive")
    if path.exists() and not args.overwrite and not args.append:
        raise RuntimeError(f"output exists; pass --overwrite or --append: {path}")
    out = df
    if args.append and path.exists():
        old = pd.read_parquet(path)
        if list(old.columns) != list(df.columns):
            raise RuntimeError("append schema mismatch")
        out = pd.concat([old, df], ignore_index=True)
    if args.dedupe_keys:
        keys = [x.strip() for x in args.dedupe_keys.split(",") if x.strip()]
        missing = [k for k in keys if k not in out.columns]
        if missing:
            raise RuntimeError(f"dedupe keys missing: {missing}")
        out = out.drop_duplicates(subset=keys, keep="last")
    write_parquet_atomic(out, path)


def write_metadata(output_dir: Path, meta: dict[str, Any]) -> str:
    path = output_dir / f"_fetch_meta_{API}_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
    path.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return str(path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=f"Fetch Tushare API {API} to Parquet")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--params-json")
    parser.add_argument("--params-file")
    parser.add_argument("--fields")
    parser.add_argument("--requests-per-minute", type=float, default=RATE_LIMIT_POLICY["requests_per_minute"])
    parser.add_argument("--max-retries", type=int, default=3)
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--limit-rows", type=int)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--append", action="store_true")
    parser.add_argument("--dedupe-keys")
    parser.add_argument("--partition-by")
    parser.add_argument("--token-env-name", default="TUSHARE_TOKEN")
    parser.add_argument("--allow-config-token", action="store_true")
    parser.add_argument("--confirm-entitlement", action="store_true")
    parser.add_argument("--max-requests", type=int)
    parser.add_argument("--max-output-files", type=int, default=100)
    parser.add_argument("--ts-code")
    parser.add_argument("--trade-date")
    parser.add_argument("--start-date")
    parser.add_argument("--end-date")
    parser.add_argument("--exchange")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if SKELETON_ONLY and not args.confirm_entitlement:
        print("This script was generated as skeleton-only. Re-run with --confirm-entitlement after confirming Tushare access.", file=sys.stderr)
        return 2
    if args.smoke:
        args.max_requests = 1 if args.max_requests is None else min(args.max_requests, 1)
        args.max_output_files = min(args.max_output_files, 1)
        args.overwrite = True
    elif args.max_requests is None:
        args.max_requests = 1000000
    output_dir = Path(args.output_dir).expanduser().resolve()
    token, token_source = load_token(args.token_env_name, args.allow_config_token)
    records, explicit = read_param_records(args)
    records = apply_common_args(records, explicit, args)
    records = records[: args.max_requests]
    import pandas as pd
    pro = create_client(token)
    limiter = RateLimiter(args.requests_per_minute)
    frames = []
    errors = []
    for params in records:
        for attempt in range(args.max_retries + 1):
            try:
                limiter.wait()
                df = call_tushare(pro, params, args.fields)
                frames.append(df)
                break
            except Exception as exc:
                if attempt >= args.max_retries:
                    errors.append({"params": params, "error": str(exc)})
                else:
                    time.sleep(min(30, 2 ** attempt))
    if errors:
        raise RuntimeError(json.dumps(errors, ensure_ascii=False))
    data = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    with OutputLock(output_dir, API):
        files = write_output(data, output_dir, args)
        meta = {
            "api": API,
            "generated_permission_analysis": PERMISSION_ANALYSIS,
            "rate_limit_policy": {**RATE_LIMIT_POLICY, "requests_per_minute_used": args.requests_per_minute},
            "strategy": STRATEGY,
            "token_source": token_source,
            "smoke": bool(args.smoke),
            "request_count": len(records),
            "row_count": int(len(data)),
            "output_files": files,
            "success": True,
        }
        meta_path = write_metadata(output_dir, meta)
    print(json.dumps({"success": True, "api": API, "row_count": int(len(data)), "output_files": files, "metadata": meta_path}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def render_script(api: str, strategy: str, permission: dict[str, Any], rate: dict[str, Any], skeleton: bool, default_output_dir: str) -> str:
    script = SCRIPT_TEMPLATE
    replacements = {
        "__API_JSON__": repr(api),
        "__STRATEGY_JSON__": repr(strategy),
        "__PERMISSION_JSON__": repr(permission),
        "__RATE_JSON__": repr(rate),
        "__SKELETON_JSON__": repr(bool(skeleton)),
        "__DEFAULT_OUTPUT_DIR_JSON__": repr(default_output_dir),
    }
    for key, value in replacements.items():
        script = script.replace(key, value)
    return script


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
    script = render_script(api, strategy, permission, rate, skeleton, default_output_dir)
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
