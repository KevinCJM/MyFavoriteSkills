#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

from tushare_runtime import SKILL_ROOT, find_interfaces_json, sanitize_command, sha256_file


def parse_args():
    p = argparse.ArgumentParser(description='Smoke-test one bounded Tushare request')
    for flag in ('script', 'api'):
        p.add_argument('--' + flag, required=True)
    for flag in ('interfaces-json', 'params-json', 'params-file', 'output-dir', 'result-json', 'empty-result-reason'):
        p.add_argument('--' + flag)
    p.add_argument('--timeout', type=int, default=120)
    p.add_argument('--row-cap', type=int)
    p.add_argument('--keep-output', action='store_true', help='Retained for compatibility; evidence is always retained')
    p.add_argument('--token-env-name', default='TUSHARE_TOKEN')
    p.add_argument('--allow-config-token', action='store_true')
    p.add_argument('--confirm-entitlement', action='store_true')
    return p.parse_args()


def portable_path(path, cwd):
    p = Path(path).expanduser().resolve()
    for prefix, base in (('$SKILL_DIR/', SKILL_ROOT), ('./', cwd)):
        try:
            return prefix + str(p.relative_to(base))
        except ValueError:
            pass
    return str(p)  # Resolvable local evidence; solidification publishes only portable metadata.


def redact_text(text):
    for key, value in os.environ.items():
        if 'TOKEN' in key.upper() and value:
            text = text.replace(value, '<redacted-token>')
    text = re.sub(r'(?i)(token[\x27\"]?\s*[:=]\s*[\x27\"]?)[A-Za-z0-9._\\-]{16,}', r'\1<redacted-token>', text)
    return text


def validate_outputs(meta, output_dir, api, script_hash, catalog_hash):
    import pandas as pd
    if (meta.get('contract_version') != 2 or meta.get('api') != api
            or meta.get('success') is not True or meta.get('complete') is not True
            or meta.get('scope') != 'smoke' or meta.get('request_count') != 1
            or meta.get('retry_count') != 0 or meta.get('requested_record_count') != 1
            or meta.get('script_sha256') != script_hash
            or meta.get('interfaces_json_sha256') != catalog_hash):
        raise ValueError('smoke metadata contract or provenance mismatch')
    outputs = meta.get('outputs')
    if not isinstance(outputs, list) or len(outputs) != 1:
        raise ValueError('smoke must produce exactly one verified Parquet file')
    row_count = 0
    for entry in outputs:
        path = Path(entry['path']).resolve()
        if path.parent != output_dir.resolve() or path.suffix != '.parquet':
            raise ValueError('output path escapes the smoke directory')
        if sha256_file(path) != entry['sha256']:
            raise ValueError('Parquet hash mismatch')
        df = pd.read_parquet(path)
        if (list(df.columns) != entry['columns'] or len(df) != entry['row_count']
                or [str(x) for x in df.dtypes] != entry['dtypes'] or not len(df.columns)):
            raise ValueError('Parquet row count/schema mismatch')
        row_count += len(df)
    if row_count != meta.get('row_count') or row_count != meta.get('source_row_count'):
        raise ValueError('metadata row count mismatch')
    if row_count == 0 and not str(meta.get('empty_result_reason') or '').strip():
        raise ValueError('empty smoke result requires independent review')
    return row_count


def main():
    args = parse_args()
    script = Path(args.script).expanduser().resolve()
    interfaces = find_interfaces_json(args.interfaces_json)
    if args.timeout <= 0:
        raise ValueError('timeout must be positive')
    script_hash, catalog_hash = sha256_file(script), sha256_file(interfaces)
    output_dir = (Path(args.output_dir).expanduser().resolve() if args.output_dir
                  else Path(tempfile.mkdtemp(prefix=f'tushare-smoke-{args.api}-')))
    output_dir.mkdir(parents=True, exist_ok=True)
    if any(output_dir.iterdir()):
        raise ValueError('smoke output directory must be empty; previous artifacts are not evidence')
    cmd = [sys.executable, str(script), '--smoke', '--output-dir', str(output_dir),
           '--max-requests', '1', '--max-retries', '0', '--max-runtime', str(args.timeout),
           '--token-env-name', args.token_env_name]
    for name in ('params_json', 'params_file', 'empty_result_reason', 'row_cap'):
        if getattr(args, name) is not None:
            cmd.extend(['--' + name.replace('_', '-'), str(getattr(args, name))])
    for name in ('allow_config_token', 'confirm_entitlement'):
        if getattr(args, name):
            cmd.append('--' + name.replace('_', '-'))
    started = datetime.now().isoformat(timespec='seconds')
    status, error, stdout, stderr = 'failed', '', '', ''
    meta, row_count = {}, 0
    try:
        proc = subprocess.run(cmd, text=True, capture_output=True, timeout=args.timeout + 5)
        stdout, stderr = proc.stdout[-4000:], proc.stderr[-4000:]
        if proc.returncode != 0:
            raise ValueError(f'script exited {proc.returncode}: {stderr or stdout}')
        if sha256_file(script) != script_hash or sha256_file(interfaces) != catalog_hash:
            raise ValueError('script/catalog changed during smoke')
        summary = json.loads(proc.stdout.strip().splitlines()[-1])
        meta_path = Path(summary['metadata']).resolve()
        if meta_path.parent != output_dir:
            raise ValueError('metadata path escapes the smoke directory')
        meta = json.loads(meta_path.read_text())
        row_count = validate_outputs(meta, output_dir, args.api, script_hash, catalog_hash)
        status = 'passed'
    except Exception as exc:
        error = str(exc)
    portable = sanitize_command(cmd).replace(str(script), '<script>').replace(str(output_dir), '<output_dir>').replace(sys.executable, 'python3')
    if args.params_file:
        portable = portable.replace(args.params_file, '<params_file>')
    result = {
        'status': status, 'validation_version': 2, 'api': args.api,
        'script_path': portable_path(script, Path.cwd()), 'script_sha256': script_hash,
        'interfaces_json_path': portable_path(interfaces, Path.cwd()), 'interfaces_json_sha256': catalog_hash,
        'command_sanitized': redact_text(portable), 'started_at': started,
        'ended_at': datetime.now().isoformat(timespec='seconds'), 'output_dir': str(output_dir),
        'runtime_rate_limit_policy': meta.get('rate_limit_policy', {}),
        'request_count': meta.get('request_count'), 'retry_count': meta.get('retry_count'),
        'complete': meta.get('complete', False), 'scope': meta.get('scope'),
        'row_count': row_count, 'empty_result_reason': meta.get('empty_result_reason'),
        'outputs': meta.get('outputs', []), 'stdout_tail': redact_text(stdout),
        'stderr_tail': redact_text(stderr), 'error': redact_text(error),
    }
    if args.result_json:
        Path(args.result_json).expanduser().resolve().write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if status == 'passed' else 2


if __name__ == '__main__':
    raise SystemExit(main())
