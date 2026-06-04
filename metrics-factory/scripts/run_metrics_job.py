#!/usr/bin/env python3
"""AI-safe dry-run and execution wrapper for MetricsFactory jobs."""

from __future__ import annotations

import argparse
import contextlib
import copy
import hashlib
import json
import math
import os
import platform
import re
import shutil
import subprocess
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

from runtime_support import (
    add_project_imports,
    find_project_root as find_metrics_project_root,
    skill_dir,
    venv_python_path,
)


SCHEMA_VERSION = "1.0"
SUPPORTED_FORMAT = "parquet"
WORK_UNIT_THRESHOLD = 200_000
ROLL_WORK_UNIT_THRESHOLD = 500_000
CONSERVATIVE_WORKER_CAP = 4

PERIOD_KEYS = ["log_return", "close_price", "high_price", "low_price", "volume"]
ROLLING_KEYS = ["open_price", "close_price", "high_price", "low_price", "volume"]
VALID_MODES = {"period", "rolling", "both"}
VALID_PARALLEL_MODES = {"auto", "on", "off"}
VOLUME_METRIC_NAMES = {
    "VolAvg",
    "VolSlope",
    "VolVolatility",
    "VolMA",
    "VolMADiff",
    "OBV",
    "MAOBV",
    "MAOBVDiff",
    "PVT",
    "MAPVT",
    "MAPVTDiff",
    "VR",
}
VOLUME_METRIC_PREFIXES = ("MAVR-", "MAVRDiff-")


def safe_name(job_name: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", job_name).strip("_") or "metrics_job"
    return safe


def default_run_id(job_name: str, request: dict[str, Any]) -> str:
    clone = copy.deepcopy(request)
    clone.setdefault("output", {})["run_id"] = None
    return f"{safe_name(job_name)}_{stable_hash(clone)[:12]}"


def iso_now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def issue(level: str, code: str, message: str, **details: Any) -> dict[str, Any]:
    item = {"level": level, "code": code, "message": message}
    item.update({k: v for k, v in details.items() if v is not None})
    return item


def add_issue(plan: dict[str, Any], level: str, code: str, message: str, **details: Any) -> None:
    plan["issues"][level + "s"].append(issue(level, code, message, **details))


def resolve_path(raw_path: Any, cwd: Path) -> Path | None:
    if raw_path is None:
        return None
    path = Path(str(raw_path)).expanduser()
    if not path.is_absolute():
        path = cwd / path
    return path.resolve()


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("request JSON must be an object")
    return data


def stable_hash(obj: Any) -> str:
    payload = json.dumps(obj, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def plan_hash(plan: dict[str, Any]) -> str:
    clone = copy.deepcopy(plan)
    clone.pop("plan_hash", None)
    clone.pop("started_at", None)
    clone.pop("finished_at", None)
    clone.pop("output_stats", None)
    return stable_hash(clone)


def get_git_summary(project_root: Path) -> dict[str, Any]:
    try:
        head = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=project_root,
            text=True,
            capture_output=True,
            check=True,
        ).stdout.strip()
        status = subprocess.run(
            ["git", "status", "--short", "--", "."],
            cwd=project_root,
            text=True,
            capture_output=True,
            check=True,
        ).stdout.splitlines()
        return {"head": head, "status_short": status[:100], "status_count": len(status)}
    except Exception:
        return {"head": "not_a_git_repo", "status_short": [], "status_count": 0}


def get_available_memory() -> tuple[int | None, str | None]:
    try:
        import psutil  # type: ignore

        return int(psutil.virtual_memory().available), None
    except Exception as exc:
        return None, str(exc)


def load_runtime(project_root: Path) -> dict[str, Any]:
    add_project_imports(project_root)
    import numpy as np  # type: ignore
    import pandas as pd  # type: ignore
    from MetricsFactory.metrics_cal_config import create_period_metrics_map, create_rolling_metrics_map, period_list
    from MetricsFactory.metrics_factory import (
        compute_all_rolling_metrics,
        compute_metrics_for_period_initialize,
        get_start_date,
    )

    return {
        "np": np,
        "pd": pd,
        "period_list": period_list,
        "create_period_metrics_map": create_period_metrics_map,
        "create_rolling_metrics_map": create_rolling_metrics_map,
        "compute_metrics_for_period_initialize": compute_metrics_for_period_initialize,
        "compute_all_rolling_metrics": compute_all_rolling_metrics,
        "get_start_date": get_start_date,
    }


def runtime_import_hint(project_root: Path, exc: Exception) -> str:
    run_script = skill_dir() / "scripts" / "run_metrics_job.py"
    check_script = skill_dir() / "scripts" / "check_runtime.py"
    setup_script = skill_dir() / "scripts" / "setup_runtime.py"
    managed_venv_python = venv_python_path(project_root / ".metricsfactory-venv")
    project_venv_python = venv_python_path(project_root / ".venv")
    parts = [
        f"current executable: {sys.executable}",
        f"current machine: {platform.machine()}",
        f"check runtime: python {check_script} --project-root {project_root}",
    ]
    if managed_venv_python.exists():
        parts.append(f"retry with: {managed_venv_python} {run_script} --project-root {project_root} --request job.json --dry-run")
    elif project_venv_python.exists():
        parts.append(f"retry with: {project_venv_python} {run_script} --project-root {project_root} --request job.json --dry-run")
    else:
        parts.append(f"create project-local runtime: python {setup_script} --project-root {project_root}")
    error_text = str(exc)
    if "incompatible architecture" in error_text or "mach-o" in error_text:
        parts.append("likely Python/native-wheel CPU architecture mismatch")
    return "; ".join(parts)


def version_summary(runtime: dict[str, Any] | None) -> dict[str, str]:
    result = {
        "python": sys.version.split()[0],
        "executable": sys.executable,
        "machine": platform.machine(),
        "platform": platform.platform(),
        "pandas": "unavailable",
        "numpy": "unavailable",
    }
    if runtime:
        result["pandas"] = getattr(runtime["pd"], "__version__", "unknown")
        result["numpy"] = getattr(runtime["np"], "__version__", "unknown")
    return result


def normalize_request(request: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    normalized = copy.deepcopy(request)
    normalized.setdefault("job_name", "metrics_job")
    normalized.setdefault("mode", "period")
    normalized.setdefault("data", {})
    normalized.setdefault("data_contract", {})
    normalized.setdefault("selection", {})
    normalized.setdefault("output", {})
    normalized.setdefault("parallel", {})
    normalized.setdefault("risk_acceptance", {})

    data = normalized["data"]
    data.setdefault("format", SUPPORTED_FORMAT)
    data.setdefault("date_index", True)
    data.setdefault("date_column", None)

    contract = normalized["data_contract"]
    contract.setdefault("price_basis", "unknown")
    contract.setdefault("ohlc_basis", "unknown")
    contract.setdefault("volume_basis", "unknown")

    selection = normalized["selection"]
    selection.setdefault("fund_list", None)
    selection.setdefault("periods", None)
    selection.setdefault("roll_windows", None)
    selection.setdefault("period_metrics", None)
    selection.setdefault("rolling_metrics", None)
    selection.setdefault("spec_end_date", None)
    selection.setdefault("min_data_required", 2)

    output = normalized["output"]
    output.setdefault("save_path", "outputs/metrics")
    output.setdefault("overwrite", False)
    output.setdefault("run_id", None)
    output.setdefault("atomic_write", True)

    parallel = normalized["parallel"]
    parallel.setdefault("mode", "auto")
    parallel.setdefault("max_workers", None)
    parallel.setdefault("reserve_cores", 1)
    parallel.setdefault("min_tasks_per_worker", 4)
    parallel.setdefault("memory_headroom_gb", 2)

    risk = normalized["risk_acceptance"]
    risk.setdefault("allow_unknown_basis", False)
    risk.setdefault("allow_rolling_open_close_risk", False)
    if args.allow_unknown_basis:
        risk["allow_unknown_basis"] = True
    if args.allow_rolling_open_close_risk:
        risk["allow_rolling_open_close_risk"] = True
    return normalized


def required_data_keys(mode: str) -> list[str]:
    if mode == "period":
        return PERIOD_KEYS
    if mode == "rolling":
        return ROLLING_KEYS
    return sorted(set(PERIOD_KEYS + ROLLING_KEYS))


def read_frame(
    pd: Any,
    path: Path,
    date_index: bool,
    date_column: str | None,
) -> tuple[Any | None, dict[str, Any], str | None]:
    try:
        frame = pd.read_parquet(path)
        if not date_index:
            if not date_column:
                return None, {}, "date_column is required when date_index=false"
            if date_column not in frame.columns:
                return None, {}, f"date_column {date_column!r} not found"
            frame = frame.set_index(date_column)
        frame.index = pd.to_datetime(frame.index)
        if frame.index.has_duplicates:
            return None, {}, "date index has duplicates"
        if not frame.index.is_monotonic_increasing:
            return None, {}, "date index is not ascending"
        for column in frame.columns:
            frame[column] = pd.to_numeric(frame[column], errors="raise")
        summary = {
            "path": str(path),
            "shape": [int(frame.shape[0]), int(frame.shape[1])],
            "date_start": str(frame.index.min().date()) if len(frame.index) else None,
            "date_end": str(frame.index.max().date()) if len(frame.index) else None,
            "product_count": int(frame.shape[1]),
            "columns_sample": [str(c) for c in list(frame.columns)[:20]],
            "columns_hash": stable_hash([str(c) for c in frame.columns]),
        }
        return frame, summary, None
    except Exception as exc:
        return None, {}, str(exc)


def validate_same_axes(plan: dict[str, Any], frames: dict[str, Any]) -> None:
    if not frames:
        return
    first_key = next(iter(frames))
    first = frames[first_key]
    for key, frame in frames.items():
        if key == first_key:
            continue
        if not frame.index.equals(first.index):
            add_issue(plan, "blocker", "input_index_mismatch", f"{key} index differs from {first_key}")
        if list(frame.columns) != list(first.columns):
            add_issue(plan, "blocker", "input_columns_mismatch", f"{key} columns differ from {first_key}")


def normalize_roll_window(value: Any) -> int | None:
    try:
        if isinstance(value, str) and not value.strip().isdigit():
            return None
        return int(value)
    except Exception:
        return None


def select_metrics(
    selector: Any,
    key: str | int,
    default_metrics: list[str],
    issue_prefix: str,
    plan: dict[str, Any],
) -> list[str] | None:
    if selector is None:
        return None
    if isinstance(selector, list):
        metrics = [str(item) for item in selector]
    elif isinstance(selector, dict):
        raw = selector.get(str(key), selector.get(key, None))
        if raw is None:
            return None
        if not isinstance(raw, list):
            add_issue(plan, "blocker", f"{issue_prefix}_metrics_invalid", f"metrics for {key} must be a list")
            return []
        metrics = [str(item) for item in raw]
    else:
        add_issue(plan, "blocker", f"{issue_prefix}_metrics_invalid", "metrics must be null, list, or mapping")
        return []
    unsupported = sorted(set(metrics) - set(default_metrics))
    if unsupported:
        add_issue(
            plan,
            "blocker",
            f"{issue_prefix}_metrics_not_executable",
            f"metrics are not executable for {key}: {', '.join(unsupported)}",
        )
    return metrics


def has_volume_metric(metrics: list[str]) -> bool:
    return any(metric in VOLUME_METRIC_NAMES or metric.startswith(VOLUME_METRIC_PREFIXES) for metric in metrics)


def valid_end_dates_count(pd: Any, index: Any, period: str, spec_end_date: str | None, get_start_date: Any) -> int:
    trading_days = pd.to_datetime(index)
    if spec_end_date:
        days_iter = [pd.to_datetime(spec_end_date)]
    else:
        days_iter = list(trading_days)
    count = 0
    first_day = trading_days.min()
    last_day = trading_days.max()
    for end_date in days_iter:
        match = re.match(r"^(\d+).*d$", str(period))
        if match:
            days = int(match.group(1))
            end_idx = trading_days.searchsorted(end_date)
            if end_idx < days:
                continue
        else:
            start_date = get_start_date(end_date, period)
            if start_date < first_day or start_date > last_day:
                continue
        count += 1
    return count


def estimate_resampled_bytes(frames: dict[str, Any]) -> int:
    total = 0
    for frame in frames.values():
        if len(frame.index) == 0:
            continue
        daily_rows = (frame.index.max() - frame.index.min()).days + 1
        total += int(daily_rows) * int(frame.shape[1]) * int(frame.values.dtype.itemsize)
    return total


def memory_worker_cap(available_bytes: int | None, estimated_bytes: int, headroom_gb: float) -> tuple[int | None, str]:
    if available_bytes is None:
        return None, "memory_unknown"
    headroom = int(headroom_gb * 1024**3)
    usable = max(0, available_bytes - headroom)
    base_need = max(estimated_bytes * 2, 1)
    if usable < base_need:
        return 1, "available_memory_below_base_estimate"
    per_worker = max(int(estimated_bytes * 0.25), 256 * 1024**2)
    return max(1, int((usable - base_need) // per_worker) + 1), "memory_estimated"


def decide_period_parallel(
    period: str,
    valid_end_dates: int,
    product_count: int,
    metric_count: int,
    spec_end_date: str | None,
    parallel: dict[str, Any],
    estimated_bytes: int,
    available_memory: int | None,
    plan: dict[str, Any],
) -> dict[str, Any]:
    cpu_count = os.cpu_count() or 1
    reserve_cores = int(parallel.get("reserve_cores", 1) or 0)
    min_tasks_per_worker = max(1, int(parallel.get("min_tasks_per_worker", 4) or 4))
    max_workers = parallel.get("max_workers")
    max_workers = int(max_workers) if max_workers is not None else None
    headroom_gb = float(parallel.get("memory_headroom_gb", 2) or 0)
    mode = str(parallel.get("mode", "auto"))

    cpu_cap = max(1, cpu_count - reserve_cores)
    task_cap = max(1, math.floor(valid_end_dates / min_tasks_per_worker))
    user_cap = max_workers if max_workers is not None else cpu_cap
    mem_cap, mem_reason = memory_worker_cap(available_memory, estimated_bytes, headroom_gb)
    if mem_cap is None:
        add_issue(
            plan,
            "warning",
            "memory_unknown_use_conservative_worker_cap",
            "available memory could not be detected; worker count is capped conservatively",
        )
        mem_cap = min(cpu_cap, task_cap, CONSERVATIVE_WORKER_CAP)

    workers = max(1, min(cpu_cap, task_cap, user_cap, mem_cap))
    work_units = int(valid_end_dates) * int(product_count) * int(metric_count)

    reason = []
    if mode == "off":
        multi_process = False
        workers = 1
        reason.append("parallel.mode=off")
    elif spec_end_date is not None:
        multi_process = False
        workers = 1
        reason.append("spec_end_date creates a single-end-date job")
    elif workers < 2:
        multi_process = False
        reason.append("workers<2")
    elif mode == "on":
        multi_process = True
        reason.append("parallel.mode=on")
    elif valid_end_dates < 8:
        multi_process = False
        workers = 1
        reason.append("valid_end_dates<8")
    elif work_units < WORK_UNIT_THRESHOLD:
        multi_process = False
        workers = 1
        reason.append(f"work_units<{WORK_UNIT_THRESHOLD}")
    else:
        multi_process = True
        reason.append("auto thresholds exceeded")

    if multi_process:
        add_issue(
            plan,
            "warning",
            "shared_memory_names_fixed",
            "period multi-process uses fixed shared-memory names; avoid concurrent jobs in the same OS namespace",
            period=period,
        )

    return {
        "kind": "period",
        "period": period,
        "multi_process": bool(multi_process),
        "workers": int(workers),
        "valid_end_dates": int(valid_end_dates),
        "product_count": int(product_count),
        "metric_count": int(metric_count),
        "estimated_work_units": int(work_units),
        "cpu_count": int(cpu_count),
        "cpu_cap": int(cpu_cap),
        "task_cap": int(task_cap),
        "memory_cap": int(mem_cap),
        "memory_reason": mem_reason,
        "reason": "; ".join(reason),
    }


def output_files_for(
    final_dir: Path,
    periods: list[str],
    include_rolling: bool,
) -> list[dict[str, Any]]:
    outputs: list[dict[str, Any]] = []
    for period in periods:
        outputs.append({"kind": "period", "key": period, "filename": f"{period}.parquet", "path": str(final_dir / f"{period}.parquet")})
    if include_rolling:
        outputs.append({"kind": "rolling", "key": "rolling", "filename": "rolling_metrics.parquet", "path": str(final_dir / "rolling_metrics.parquet")})
    outputs.append({"kind": "manifest", "key": "manifest", "filename": "run_manifest.json", "path": str(final_dir / "run_manifest.json")})
    return outputs


def build_plan(request_path: Path, args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, Any]]:
    cwd = Path.cwd().resolve()
    project_root = find_metrics_project_root(start=cwd, explicit=args.project_root)
    raw_request = load_json(request_path)
    request = normalize_request(raw_request, args)

    plan: dict[str, Any] = {
        "schema_version": request.get("schema_version"),
        "job_name": request.get("job_name"),
        "mode": request.get("mode"),
        "request_path": {"raw": str(request_path), "absolute": str(request_path.resolve())},
        "cwd": str(cwd),
        "project_root": str(project_root),
        "issues": {"blockers": [], "warnings": [], "infos": []},
        "risk_acceptance": request["risk_acceptance"],
        "data_contract": request["data_contract"],
        "input_summary": {},
        "selection_summary": {},
        "parallel_decisions": [],
        "outputs": [],
        "environment": {},
        "git": get_git_summary(project_root),
    }
    context: dict[str, Any] = {"request": request, "frames": {}, "runtime": None, "project_root": project_root}

    if "schema_version" not in request:
        add_issue(plan, "blocker", "schema_version_missing", "schema_version is required")
    elif request.get("schema_version") != SCHEMA_VERSION:
        add_issue(plan, "blocker", "schema_version_unknown", f"unsupported schema_version: {request.get('schema_version')}")

    mode = str(request.get("mode"))
    if mode not in VALID_MODES:
        add_issue(plan, "blocker", "mode_invalid", f"mode must be one of {sorted(VALID_MODES)}")

    data = request["data"]
    if data.get("format") != SUPPORTED_FORMAT:
        add_issue(plan, "blocker", "format_unsupported", "V1 supports only parquet input")

    parallel = request["parallel"]
    if parallel.get("mode") not in VALID_PARALLEL_MODES:
        add_issue(plan, "blocker", "parallel_mode_invalid", f"parallel.mode must be one of {sorted(VALID_PARALLEL_MODES)}")

    try:
        runtime = load_runtime(project_root)
        context["runtime"] = runtime
        plan["environment"] = version_summary(runtime)
    except Exception as exc:
        plan["environment"] = version_summary(None)
        add_issue(
            plan,
            "blocker",
            "runtime_import_failed",
            "could not import pandas, numpy, or MetricsFactory runtime",
            error=str(exc),
            hint=runtime_import_hint(project_root, exc),
            traceback=traceback.format_exc(limit=3),
        )
        runtime = None

    if mode in VALID_MODES:
        keys = required_data_keys(mode)
    else:
        keys = []

    resolved_inputs: dict[str, Any] = {}
    for key in keys:
        raw_path = data.get(key)
        path = resolve_path(raw_path, cwd)
        resolved_inputs[key] = {"raw": raw_path, "absolute": str(path) if path else None}
        if path is None:
            add_issue(plan, "blocker", "input_missing", f"required input {key} is missing", input=key)
        elif not path.exists():
            add_issue(plan, "blocker", "input_file_missing", f"input file does not exist: {path}", input=key)

    plan["resolved_inputs"] = resolved_inputs

    if runtime and data.get("format") == SUPPORTED_FORMAT:
        pd = runtime["pd"]
        for key, path_info in resolved_inputs.items():
            path_value = path_info.get("absolute")
            if not path_value:
                continue
            path = Path(path_value)
            if not path.exists():
                continue
            frame, summary, error = read_frame(pd, path, bool(data.get("date_index", True)), data.get("date_column"))
            if error:
                add_issue(plan, "blocker", "input_frame_invalid", f"{key}: {error}", input=key)
                continue
            context["frames"][key] = frame
            plan["input_summary"][key] = summary

    validate_same_axes(plan, context["frames"])

    base_frame = next(iter(context["frames"].values()), None)
    fund_list = request["selection"].get("fund_list")
    if fund_list is not None and not isinstance(fund_list, list):
        add_issue(plan, "blocker", "fund_list_invalid", "fund_list must be null or a list")
        fund_list = None
    if fund_list and base_frame is not None:
        missing = sorted(set(fund_list) - set(base_frame.columns))
        if missing:
            add_issue(plan, "blocker", "fund_list_missing_columns", f"fund_list contains missing products: {', '.join(missing)}")

    product_count = len(fund_list) if fund_list else (int(base_frame.shape[1]) if base_frame is not None else 0)
    trading_day_count = int(base_frame.shape[0]) if base_frame is not None else 0
    date_start = str(base_frame.index.min().date()) if base_frame is not None and len(base_frame.index) else None
    date_end = str(base_frame.index.max().date()) if base_frame is not None and len(base_frame.index) else None
    plan["input_summary"]["combined"] = {
        "product_count": product_count,
        "trading_day_count": trading_day_count,
        "date_start": date_start,
        "date_end": date_end,
    }

    spec_end_date = request["selection"].get("spec_end_date")
    if spec_end_date and base_frame is not None and runtime:
        pd = runtime["pd"]
        parsed = pd.to_datetime(spec_end_date)
        if parsed not in base_frame.index:
            add_issue(plan, "blocker", "spec_end_date_not_trading_day", f"spec_end_date is not in the input index: {spec_end_date}")
        request["selection"]["spec_end_date"] = str(parsed.date())

    price_basis = str(request["data_contract"].get("price_basis", "unknown")).lower()
    if price_basis == "unknown":
        if request["risk_acceptance"].get("allow_unknown_basis"):
            add_issue(plan, "warning", "unknown_price_basis_accepted", "price_basis=unknown was accepted by risk override")
        else:
            add_issue(plan, "blocker", "unknown_price_basis", "price_basis=unknown requires explicit risk acceptance")

    available_memory, mem_error = get_available_memory()
    if mem_error:
        add_issue(plan, "warning", "available_memory_unknown", "could not read available memory", error=mem_error)
    estimated_bytes = estimate_resampled_bytes(context["frames"]) if context["frames"] else 0
    plan["resource_summary"] = {
        "estimated_array_bytes": estimated_bytes,
        "available_memory_bytes": available_memory,
    }

    periods_executed: list[str] = []
    rolling_windows_executed: list[int] = []
    period_metrics_by_period: dict[str, list[str]] = {}
    rolling_metrics_by_window: dict[str, list[str]] = {}
    skipped: list[dict[str, str]] = []

    if runtime:
        period_map = runtime["create_period_metrics_map"]()
        rolling_map = runtime["create_rolling_metrics_map"]()
        context["period_map"] = period_map
        context["rolling_map"] = rolling_map

        if mode in {"period", "both"}:
            requested_periods = request["selection"].get("periods")
            if requested_periods is None:
                default_periods = list(runtime["period_list"])
                for period in default_periods:
                    if period in period_map:
                        periods_executed.append(period)
                    else:
                        skipped.append({"kind": "period", "key": str(period), "reason": "default_period_without_metric_mapping"})
                        add_issue(plan, "warning", "default_period_skipped", f"default period has no metric mapping and will be skipped: {period}")
            elif isinstance(requested_periods, list):
                for period in requested_periods:
                    period = str(period)
                    if period not in period_map:
                        add_issue(plan, "blocker", "period_not_executable", f"period is not executable by current mapping: {period}")
                    else:
                        periods_executed.append(period)
            else:
                add_issue(plan, "blocker", "periods_invalid", "selection.periods must be null or a list")

            for period in periods_executed:
                default_metrics = list(period_map[period])
                selected_metrics = select_metrics(
                    request["selection"].get("period_metrics"),
                    period,
                    default_metrics,
                    "period",
                    plan,
                )
                metrics_for_period = selected_metrics if selected_metrics is not None else default_metrics
                if not metrics_for_period:
                    add_issue(plan, "blocker", "period_metric_empty", f"no metrics selected for period {period}")
                period_metrics_by_period[period] = metrics_for_period
                valid_count = valid_end_dates_count(runtime["pd"], base_frame.index, period, request["selection"].get("spec_end_date"), runtime["get_start_date"]) if base_frame is not None else 0
                if valid_count == 0:
                    add_issue(plan, "blocker", "period_no_valid_end_dates", f"period has no valid end dates: {period}")
                decision = decide_period_parallel(
                    period,
                    valid_count,
                    product_count,
                    len(metrics_for_period),
                    request["selection"].get("spec_end_date"),
                    parallel,
                    estimated_bytes,
                    available_memory,
                    plan,
                )
                plan["parallel_decisions"].append(decision)

        if mode in {"rolling", "both"}:
            requested_windows = request["selection"].get("roll_windows")
            if requested_windows is None:
                rolling_windows_executed = sorted(int(k) for k in rolling_map.keys())
            elif isinstance(requested_windows, list):
                for value in requested_windows:
                    window = normalize_roll_window(value)
                    if window is None or window not in rolling_map:
                        add_issue(plan, "blocker", "rolling_window_not_executable", f"rolling window is not executable: {value}")
                    else:
                        rolling_windows_executed.append(window)
            else:
                add_issue(plan, "blocker", "roll_windows_invalid", "selection.roll_windows must be null or a list")

            rolling_selector = request["selection"].get("rolling_metrics")
            if rolling_selector is not None:
                add_issue(
                    plan,
                    "blocker",
                    "rolling_metric_selection_not_supported",
                    "current compute_all_rolling_metrics entrypoint does not accept a rolling metrics list; leave rolling_metrics null in V1",
                )
            if rolling_windows_executed:
                if not request["risk_acceptance"].get("allow_rolling_open_close_risk"):
                    add_issue(
                        plan,
                        "blocker",
                        "rolling_open_close_risk_not_accepted",
                        "rolling execution is blocked until open/close risk is fixed or explicitly accepted",
                    )
                else:
                    add_issue(plan, "warning", "rolling_open_close_risk_accepted", "rolling open/close risk was explicitly accepted")
            for window in rolling_windows_executed:
                default_metrics = list(rolling_map[window])
                rolling_metrics_by_window[str(window)] = default_metrics
                work_units = int(product_count) * int(trading_day_count) * int(len(default_metrics))
                plan["parallel_decisions"].append(
                    {
                        "kind": "rolling",
                        "window": window,
                        "parallel": False,
                        "workers": 1,
                        "product_count": product_count,
                        "trading_day_count": trading_day_count,
                        "metric_count": len(default_metrics),
                        "estimated_work_units": work_units,
                        "reason": "V1 rolling entrypoint ignores num_workers",
                        "future_parallel_candidate": work_units >= ROLL_WORK_UNIT_THRESHOLD and len(rolling_windows_executed) >= 3,
                    }
                )

        if request["data_contract"].get("volume_basis") not in {"real", "real_or_not_used"}:
            volume_requested = any(has_volume_metric(metrics) for metrics in period_metrics_by_period.values()) or any(
                has_volume_metric(metrics) for metrics in rolling_metrics_by_window.values()
            )
            if volume_requested:
                add_issue(plan, "warning", "volume_basis_not_real", "volume metrics are selected but volume_basis is not real")

    output = request["output"]
    save_path = resolve_path(output.get("save_path"), cwd)
    if save_path is None:
        add_issue(plan, "blocker", "save_path_missing", "output.save_path is required")
        save_path = cwd / "outputs" / "metrics"
    run_id = output.get("run_id")
    if run_id is None:
        run_id = default_run_id(str(request["job_name"]), request)
    final_dir = save_path if run_id == "." else save_path / str(run_id)
    plan["output"] = {
        "save_path": str(save_path),
        "run_id": run_id,
        "final_dir": str(final_dir),
        "overwrite": bool(output.get("overwrite", False)),
        "atomic_write": bool(output.get("atomic_write", True)),
    }

    if run_id != "." and final_dir.exists() and not output.get("overwrite", False):
        add_issue(plan, "blocker", "output_dir_exists", f"run output directory exists and overwrite=false: {final_dir}")

    parent_to_create = final_dir if run_id != "." else save_path
    existing_parent = parent_to_create
    while not existing_parent.exists() and existing_parent.parent != existing_parent:
        existing_parent = existing_parent.parent
    if existing_parent.exists() and not os.access(existing_parent, os.W_OK):
        add_issue(plan, "blocker", "save_path_not_writable", f"output path is not writable: {existing_parent}")

    include_rolling = mode in {"rolling", "both"} and bool(rolling_windows_executed)
    if not periods_executed and not include_rolling and runtime:
        add_issue(plan, "blocker", "no_calculation_selected", "no period or rolling calculation is selected")
    plan["outputs"] = output_files_for(final_dir, periods_executed, include_rolling)
    if not output.get("overwrite", False):
        for out in plan["outputs"]:
            if out["kind"] == "manifest":
                continue
            if Path(out["path"]).exists():
                add_issue(plan, "blocker", "output_exists", f"target output exists and overwrite=false: {out['path']}")

    plan["selection_summary"] = {
        "fund_list": fund_list,
        "product_count": product_count,
        "periods_executed": periods_executed,
        "roll_windows_executed": rolling_windows_executed,
        "period_metrics_by_period": period_metrics_by_period,
        "rolling_metrics_by_window": rolling_metrics_by_window,
        "skipped": skipped,
        "spec_end_date": request["selection"].get("spec_end_date"),
        "min_data_required": request["selection"].get("min_data_required"),
    }
    context["period_metrics_by_period"] = period_metrics_by_period
    context["rolling_windows_executed"] = rolling_windows_executed

    plan["can_execute"] = len(plan["issues"]["blockers"]) == 0
    plan["plan_hash"] = plan_hash(plan)
    return plan, context


def output_stats(pd: Any, path: Path) -> dict[str, Any]:
    stat = {"path": str(path), "exists": path.exists()}
    if not path.exists():
        return stat
    stat["file_size_bytes"] = path.stat().st_size
    if path.suffix == ".parquet":
        frame = pd.read_parquet(path)
        stat["rows"] = int(frame.shape[0])
        stat["columns"] = int(frame.shape[1])
    return stat


def prepare_execution_dir(plan: dict[str, Any]) -> tuple[Path, Path | None]:
    final_dir = Path(plan["output"]["final_dir"])
    overwrite = bool(plan["output"]["overwrite"])
    atomic = bool(plan["output"]["atomic_write"])
    run_id = plan["output"]["run_id"]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if run_id == ".":
        final_dir.mkdir(parents=True, exist_ok=True)
        if atomic:
            temp_dir = final_dir / ".tmp" / f"run_{timestamp}"
            temp_dir.mkdir(parents=True, exist_ok=False)
            return temp_dir, final_dir
        return final_dir, None

    if final_dir.exists() and overwrite:
        backup = final_dir.parent / f".backup_{final_dir.name}_{timestamp}"
        shutil.move(str(final_dir), str(backup))
    if atomic:
        final_dir.parent.mkdir(parents=True, exist_ok=True)
        temp_dir = final_dir.parent / f".tmp_{final_dir.name}_{timestamp}"
        temp_dir.mkdir(parents=True, exist_ok=False)
        return temp_dir, final_dir
    final_dir.mkdir(parents=True, exist_ok=True)
    return final_dir, None


def commit_execution_dir(temp_dir: Path, final_dir: Path | None, plan: dict[str, Any]) -> None:
    if final_dir is None:
        return
    if plan["output"]["run_id"] == ".":
        backup_dir = final_dir / f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        for item in temp_dir.iterdir():
            target = final_dir / item.name
            if target.exists():
                backup_dir.mkdir(parents=True, exist_ok=True)
                shutil.move(str(target), str(backup_dir / item.name))
            shutil.move(str(item), str(target))
        try:
            temp_dir.rmdir()
        except OSError:
            pass
    else:
        shutil.move(str(temp_dir), str(final_dir))


def execute_plan(plan: dict[str, Any], context: dict[str, Any]) -> int:
    if plan["issues"]["blockers"]:
        print(json.dumps(plan, ensure_ascii=False, indent=2, default=str))
        return 2

    runtime = context["runtime"]
    if runtime is None:
        print(json.dumps(plan, ensure_ascii=False, indent=2, default=str))
        return 2

    started_at = iso_now()
    exec_dir, final_dir = prepare_execution_dir(plan)
    failed_dir: Path | None = None
    try:
        request = context["request"]
        frames = context["frames"]
        fund_list = request["selection"].get("fund_list")
        spec_end_date = request["selection"].get("spec_end_date")
        min_data_required = int(request["selection"].get("min_data_required", 2) or 2)

        with contextlib.redirect_stdout(sys.stderr):
            for decision in plan["parallel_decisions"]:
                if decision["kind"] != "period":
                    continue
                period = decision["period"]
                metrics = context["period_metrics_by_period"].get(period)
                runtime["compute_metrics_for_period_initialize"](
                    log_return_df=frames["log_return"],
                    close_price_df=frames["close_price"],
                    high_price_df=frames["high_price"],
                    low_price_df=frames["low_price"],
                    volume_df=frames["volume"],
                    save_path=str(exec_dir),
                    p_list=[period],
                    metrics_list=metrics,
                    fund_list=fund_list,
                    spec_end_date=spec_end_date,
                    num_workers=decision["workers"],
                    multi_process=decision["multi_process"],
                    min_data_required=min_data_required,
                )

            if plan["mode"] in {"rolling", "both"} and context["rolling_windows_executed"]:
                runtime["compute_all_rolling_metrics"](
                    open_price_df=frames["open_price"],
                    close_price_df=frames["close_price"],
                    high_price_df=frames["high_price"],
                    low_price_df=frames["low_price"],
                    volume_df=frames["volume"],
                    save_path=str(exec_dir),
                    fund_list=fund_list,
                    roll_list=context["rolling_windows_executed"],
                )

        manifest = copy.deepcopy(plan)
        manifest["started_at"] = started_at
        manifest["finished_at"] = iso_now()
        manifest["execution_dir"] = str(exec_dir)
        manifest["final_dir"] = str(final_dir or exec_dir)
        manifest["output_stats"] = []
        for out in plan["outputs"]:
            path = exec_dir / out["filename"]
            if out["kind"] == "manifest":
                continue
            stat = output_stats(runtime["pd"], path)
            stat["temp_path"] = stat.pop("path")
            stat["path"] = str(Path(plan["output"]["final_dir"]) / out["filename"])
            stat.update({"kind": out["kind"], "key": out["key"], "filename": out["filename"]})
            manifest["output_stats"].append(stat)
        manifest["plan_hash"] = plan["plan_hash"]
        manifest_path = exec_dir / "run_manifest.json"
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

        commit_execution_dir(exec_dir, final_dir, plan)
        final_manifest = Path(plan["output"]["final_dir"]) / "run_manifest.json"
        if not final_manifest.exists():
            raise RuntimeError(f"manifest was not written to final location: {final_manifest}")
        print(json.dumps(manifest, ensure_ascii=False, indent=2, default=str))
        return 0
    except Exception:
        if final_dir is not None and exec_dir.exists():
            failed_dir = exec_dir.parent / f"failed_{exec_dir.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.move(str(exec_dir), str(failed_dir))
        error_plan = copy.deepcopy(plan)
        error_plan["started_at"] = started_at
        error_plan["finished_at"] = iso_now()
        error_plan["failed_temp_dir"] = str(failed_dir) if failed_dir else str(exec_dir)
        add_issue(error_plan, "blocker", "execution_failed", "execution failed", traceback=traceback.format_exc())
        print(json.dumps(error_plan, ensure_ascii=False, indent=2, default=str))
        return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Dry-run or execute a MetricsFactory JSON job request.")
    parser.add_argument("--project-root", default=None, help="Path to the MetricsFactory source directory")
    parser.add_argument("--request", required=True, type=Path, help="Path to V1 job JSON request")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true", help="Validate and print the execution plan")
    mode.add_argument("--execute", action="store_true", help="Execute the planned job")
    parser.add_argument("--allow-unknown-basis", action="store_true", help="Accept price_basis=unknown risk")
    parser.add_argument("--allow-rolling-open-close-risk", action="store_true", help="Accept current rolling open/close mismatch risk")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    request_path = resolve_path(args.request, Path.cwd())
    if request_path is None or not request_path.exists():
        print(json.dumps({"error": f"request file does not exist: {args.request}"}, ensure_ascii=False), file=sys.stderr)
        return 2
    try:
        plan, context = build_plan(request_path, args)
    except Exception:
        print(json.dumps({"error": "failed to build plan", "traceback": traceback.format_exc()}, ensure_ascii=False), file=sys.stderr)
        return 2
    if args.dry_run:
        print(json.dumps(plan, ensure_ascii=False, indent=2, default=str))
        return 0 if plan["can_execute"] else 2
    return execute_plan(plan, context)


if __name__ == "__main__":
    raise SystemExit(main())
