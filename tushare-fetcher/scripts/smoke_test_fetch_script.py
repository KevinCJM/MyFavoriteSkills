#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

from tushare_runtime import SKILL_ROOT, find_interfaces_json, sanitize_command, sha256_file


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Smoke-test a generated Tushare fetch script")
    parser.add_argument("--script", required=True)
    parser.add_argument("--api", required=True)
    parser.add_argument("--interfaces-json")
    parser.add_argument("--params-json")
    parser.add_argument("--params-file")
    parser.add_argument("--output-dir")
    parser.add_argument("--result-json")
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--keep-output", action="store_true")
    parser.add_argument("--token-env-name", default="TUSHARE_TOKEN")
    parser.add_argument("--allow-config-token", action="store_true")
    parser.add_argument("--confirm-entitlement", action="store_true")
    return parser.parse_args()


def count_rows(parquet_files: list[Path]) -> int:
    if not parquet_files:
        return 0
    import pandas as pd
    total = 0
    for path in parquet_files:
        total += len(pd.read_parquet(path))
    return int(total)


def portable_command(cmd: list[str], script: Path, output_dir: Path, params_file: str | None) -> str:
    text = sanitize_command(cmd)
    text = text.replace(sys.executable, "python3")
    text = text.replace(str(script), "<script>")
    text = text.replace(str(output_dir), "<output_dir>")
    if params_file:
        text = text.replace(str(Path(params_file).expanduser().resolve()), "<params_file>")
    return text


def portable_path(path: str | Path, cwd: Path) -> str:
    p = Path(path).expanduser().resolve()
    for prefix, base in (("./", cwd), ("$SKILL_DIR/", SKILL_ROOT)):
        try:
            return prefix + str(p.relative_to(base))
        except ValueError:
            pass
    return f"<external:{p.name}>"


def redact_text(text: str) -> str:
    for key, value in os.environ.items():
        if "TOKEN" in key.upper() and value:
            text = text.replace(value, "<redacted-token>")
    text = text.replace(str(Path.cwd().resolve()), ".")
    text = text.replace(str(SKILL_ROOT.resolve()), "$SKILL_DIR")
    text = re.sub(r"/private/var/folders/[^\s'\"]+", "<temp-path>", text)
    text = re.sub(r"/var/folders/[^\s'\"]+", "<temp-path>", text)
    text = re.sub(r"(?i)(token['\"]?\s*[:=]\s*['\"]?)[A-Za-z0-9._\\-]{16,}", r"\1<redacted-token>", text)
    text = re.sub(r"\b[a-f0-9]{32,}\b", "<redacted-hex>", text)
    return text


def main() -> int:
    args = parse_args()
    script = Path(args.script).expanduser().resolve()
    interfaces = find_interfaces_json(args.interfaces_json)
    temp_dir = None
    if args.output_dir:
        output_dir = Path(args.output_dir).expanduser().resolve()
    else:
        temp_dir = Path(tempfile.mkdtemp(prefix=f"tushare-smoke-{args.api}-"))
        output_dir = temp_dir
    cmd = [
        sys.executable,
        str(script),
        "--smoke",
        "--output-dir",
        str(output_dir),
        "--max-requests",
        "1",
        "--overwrite",
        "--token-env-name",
        args.token_env_name,
    ]
    if args.params_json:
        cmd.extend(["--params-json", args.params_json])
    if args.params_file:
        cmd.extend(["--params-file", str(Path(args.params_file).expanduser().resolve())])
    if args.allow_config_token:
        cmd.append("--allow-config-token")
    if args.confirm_entitlement:
        cmd.append("--confirm-entitlement")
    started = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    status = "failed"
    error = ""
    stdout = ""
    stderr = ""
    parquet_files: list[Path] = []
    metadata_files: list[Path] = []
    runtime_rate_limit_policy: dict[str, Any] = {}
    row_count = 0
    try:
        proc = subprocess.run(cmd, cwd=str(Path.cwd()), text=True, capture_output=True, timeout=args.timeout)
        stdout = proc.stdout[-4000:]
        stderr = proc.stderr[-4000:]
        if proc.returncode != 0:
            error = f"script exited {proc.returncode}: {stderr or stdout}"
        else:
            parquet_files = sorted(output_dir.glob("*.parquet"))
            metadata_files = sorted(output_dir.glob("_fetch_meta_*.json"))
            if not parquet_files:
                error = "no parquet files were produced"
            elif not metadata_files:
                error = "no metadata file was produced"
            else:
                row_count = count_rows(parquet_files)
                try:
                    meta = json.loads(metadata_files[-1].read_text(encoding="utf-8"))
                    runtime_rate_limit_policy = meta.get("rate_limit_policy") or {}
                except Exception:
                    runtime_rate_limit_policy = {}
                status = "passed"
    except Exception as exc:
        error = str(exc)
    ended = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    result: dict[str, Any] = {
        "status": status,
        "api": args.api,
        "script_path": portable_path(script, Path.cwd()),
        "script_sha256": sha256_file(script) if script.exists() else "",
        "interfaces_json_path": portable_path(interfaces, Path.cwd()),
        "interfaces_json_sha256": sha256_file(interfaces),
        "command_sanitized": portable_command(cmd, script, output_dir, args.params_file),
        "started_at": started,
        "ended_at": ended,
        "output_dir": portable_path(output_dir, Path.cwd()),
        "output_files": [portable_path(p, Path.cwd()) for p in output_dir.iterdir()] if output_dir.exists() else [],
        "parquet_files": [portable_path(p, Path.cwd()) for p in parquet_files],
        "metadata_files": [portable_path(p, Path.cwd()) for p in metadata_files],
        "runtime_rate_limit_policy": runtime_rate_limit_policy,
        "row_count": row_count,
        "stdout_tail": redact_text(stdout),
        "stderr_tail": redact_text(stderr),
        "error": redact_text(error),
    }
    if args.result_json:
        Path(args.result_json).expanduser().resolve().write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if temp_dir and not args.keep_output and status != "passed":
        shutil.rmtree(temp_dir, ignore_errors=True)
    return 0 if status == "passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
