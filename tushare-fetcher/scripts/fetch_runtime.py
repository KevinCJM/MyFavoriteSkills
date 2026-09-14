#!/usr/bin/env python3
"""Single runtime source embedded into generated, standalone fetch scripts."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
import random
import signal
import sqlite3
import sys
import tempfile
import time
from contextlib import contextmanager
from email.utils import parsedate_to_datetime
from pathlib import Path

CONTRACT = {}
CONTRACT_VERSION = 2


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def json_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=path.parent, prefix=path.name + '.')
    try:
        with os.fdopen(fd, 'w') as f:
            json.dump(value, f, ensure_ascii=False, indent=2)
            f.write('\n')
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def write_parquet(df, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=path.parent, prefix=path.name + '.')
    os.close(fd)
    try:
        df.to_parquet(name, index=False)
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


@contextmanager
def output_lock(directory):
    # Kernel releases this lock on exit/crash; never unlink another process's lock.
    import fcntl
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / '.fetch.lock').open('a') as f:
        try:
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError('another fetch owns this output directory') from None
        try:
            yield
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


@contextmanager
def run_deadline(seconds):
    # Unlike a socket read timeout, this also bounds slow trickle responses and I/O.
    if not hasattr(signal, 'setitimer'):
        raise RuntimeError('hard run deadlines currently require macOS/Linux')
    def expired(*_):
        raise TimeoutError('maximum run time exceeded; resume the checkpoint')
    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def load_token(env_name, allow_config):
    token = os.environ.get(env_name, '')
    if token:
        return token, 'env:' + env_name
    if allow_config:
        path = Path.cwd() / 'config.py'
        if path.exists():
            spec = importlib.util.spec_from_file_location('_fetch_config', path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            token = getattr(module, 'TUSHARE_TOKEN', '')
            if token:
                return str(token), 'config.py'
    raise RuntimeError('Tushare token missing; configure the requested environment variable')


class SharedRateLimiter:
    """One account budget across processes/scripts using the same local state DB."""
    def __init__(self, token, rpm, state_path=None):
        root = Path(os.environ.get('XDG_CACHE_HOME', str(Path.home() / '.cache')))
        self.path = Path(state_path or root / 'tushare-fetcher' / 'rate.sqlite3')
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.scope = hashlib.sha256(token.encode()).hexdigest()
        self.rpm = float(rpm) * 0.9  # reserve 10% headroom
        with sqlite3.connect(self.path, timeout=5) as db:
            db.execute('CREATE TABLE IF NOT EXISTS quota (scope TEXT PRIMARY KEY, calls TEXT NOT NULL)')
        os.chmod(self.path, 0o600)

    def reserve(self, now=None):
        now = time.time() if now is None else now
        with sqlite3.connect(self.path, timeout=5) as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT calls FROM quota WHERE scope=?', (self.scope,)).fetchone()
            calls = json.loads(row[0]) if row else []
            calls = [c for c in calls if now - c[0] < max(60, 60 / c[1])]
            rpm = min([self.rpm] + [c[1] for c in calls])
            recent = [c for c in calls if now - c[0] < 60]
            delay = max(0, calls[-1][0] + 60 / rpm - now) if calls else 0
            if len(recent) >= max(1, int(rpm)):
                delay = max(delay, recent[0][0] + 60 - now)
            if delay <= 0:
                calls.append([now, self.rpm])
                db.execute('INSERT OR REPLACE INTO quota VALUES (?,?)', (self.scope, json.dumps(calls)))
            return delay

    def wait(self):
        while True:
            delay = self.reserve()
            if delay <= 0:
                return
            time.sleep(delay)


class APIError(RuntimeError):
    def __init__(self, message, retryable=False, retry_after=0):
        super().__init__(message)
        self.retryable = retryable
        self.retry_after = retry_after


def retry_classification(message):
    text = str(message).lower()
    if any(s in text for s in ('权限', '积分', 'token', 'permission', 'unauthorized', '参数', '字段', 'parameter', 'field')):
        return False
    return any(s in text for s in ('每分钟', '频率', '频次', 'too many requests', 'rate limit', '系统内部错误', '暂时不可用', 'temporarily unavailable', 'server error'))


class TushareClient:
    """Official HTTP contract, explicit status handling, one POST per attempt."""
    def __init__(self, token, connect_timeout, read_timeout):
        import requests
        self.session = requests.Session()
        self.token = token
        self.timeout = (connect_timeout, read_timeout)

    def query(self, api, params, fields):
        import pandas as pd
        import requests
        try:
            response = self.session.post(
                'https://api.tushare.pro',
                json={'api_name': api, 'token': self.token, 'params': params, 'fields': fields or ''},
                timeout=self.timeout, allow_redirects=False,
            )
        except requests.exceptions.SSLError:
            raise APIError('TLS verification failed') from None
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            raise APIError('temporary network/connection timeout', retryable=True) from None
        status = response.status_code
        if status != 200:
            wait = 0
            try:
                wait = max(0, float(response.headers.get('Retry-After', 0)))
            except ValueError:
                try:
                    wait = max(0, parsedate_to_datetime(response.headers['Retry-After']).timestamp() - time.time())
                except (KeyError, TypeError, ValueError, OverflowError):
                    pass
            if not math.isfinite(wait):
                wait = 60
            raise APIError(f'HTTP {status}', status == 429 or 500 <= status <= 599, max(wait, 60 if status == 429 else 0))
        try:
            payload = response.json()
        except ValueError:
            raise APIError('invalid JSON response') from None
        if not isinstance(payload, dict) or 'code' not in payload:
            raise APIError('invalid API response envelope')
        if payload['code'] != 0:
            message = str(payload.get('msg', 'unknown API error')).replace(self.token, '<redacted-token>')
            retry = retry_classification(message)
            limited = any(s in message.lower() for s in ('每分钟', '频率', '频次', 'rate limit', 'too many'))
            raise APIError(message, retry, 60 if limited else 0)
        data = payload.get('data')
        if not isinstance(data, dict) or not isinstance(data.get('fields'), list) or not isinstance(data.get('items'), list):
            raise APIError('invalid data schema')
        fields = data['fields']
        if not fields or any(not isinstance(x, str) for x in fields) or len(set(fields)) != len(fields):
            raise APIError('invalid response fields')
        if any(not isinstance(row, list) or len(row) != len(fields) for row in data['items']):
            raise APIError('response row width mismatch')
        return pd.DataFrame(data['items'], columns=fields)

    def close(self):
        self.session.close()


class RequestRunner:
    def __init__(self, client, limiter, args):
        self.client, self.limiter, self.args = client, limiter, args
        self.request_count = 0
        self.retry_count = 0
        self.last_progress = time.monotonic()

    def check_idle(self):
        if time.monotonic() - self.last_progress >= self.args.idle_timeout:
            raise TimeoutError('idle timeout exceeded; checkpoint retained')

    def fetch(self, params):
        for attempt in range(self.args.max_retries + 1):
            self.check_idle()
            if self.request_count >= self.args.max_requests:
                raise RuntimeError('request budget exhausted; requested scope incomplete')
            self.limiter.wait()
            self.check_idle()
            self.request_count += 1
            try:
                df = self.client.query(CONTRACT['api'], params, self.args.fields)
                self.last_progress = time.monotonic()
                return df
            except APIError as exc:
                if not exc.retryable or attempt >= self.args.max_retries or self.request_count >= self.args.max_requests:
                    raise
                self.retry_count += 1
                time.sleep(max(exc.retry_after, min(30, 2 ** attempt) + random.uniform(0, 0.5)))
        raise AssertionError('unreachable')


def parse_args(argv=None):
    p = argparse.ArgumentParser(description='Fetch a documented Tushare API to Parquet')
    p.add_argument('--output-dir', default=CONTRACT.get('default_output_dir', './data/tushare'))
    p.add_argument('--params-json')
    p.add_argument('--params-file')
    p.add_argument('--fields')
    p.add_argument('--requests-per-minute', type=float, default=CONTRACT.get('rate', {}).get('requests_per_minute', 6))
    p.add_argument('--rate-state', help='Shared local SQLite quota path; all jobs must use the same path')
    p.add_argument('--max-retries', type=int, default=3)
    p.add_argument('--max-requests', type=int, default=10000)
    p.add_argument('--connect-timeout', type=float, default=10)
    p.add_argument('--read-timeout', type=float, default=30)
    p.add_argument('--idle-timeout', type=float, default=180)
    p.add_argument('--max-runtime', type=float, default=3600)
    p.add_argument('--row-cap', type=int, default=CONTRACT.get('row_cap'))
    p.add_argument('--paginate', action='store_true')
    p.add_argument('--page-size', type=int)
    p.add_argument('--resume', action='store_true')
    p.add_argument('--empty-result-reason', help='Independent review explaining why an empty slice is valid')
    p.add_argument('--smoke', action='store_true')
    p.add_argument('--overwrite', action='store_true')
    p.add_argument('--append', action='store_true')
    p.add_argument('--dedupe-keys')
    p.add_argument('--partition-by')
    p.add_argument('--max-output-files', type=int, default=100)
    p.add_argument('--limit-rows', type=int, help='Only accepted if it does not truncate the requested result')
    p.add_argument('--token-env-name', default='TUSHARE_TOKEN')
    p.add_argument('--allow-config-token', action='store_true')
    p.add_argument('--confirm-entitlement', action='store_true')
    for name in ('ts-code', 'trade-date', 'start-date', 'end-date', 'exchange'):
        p.add_argument('--' + name)
    return p.parse_args(argv)


def prepare(args):
    if not CONTRACT:
        raise ValueError('generate a configured script with generate_fetch_script.py first')
    if CONTRACT['skeleton'] and not args.confirm_entitlement:
        raise ValueError('skeleton requires confirmed entitlement and an explicit bounded request plan')
    for name in ('requests_per_minute', 'connect_timeout', 'read_timeout', 'idle_timeout', 'max_runtime', 'max_requests', 'max_output_files'):
        value = getattr(args, name)
        if not math.isfinite(value) or value <= 0:
            raise ValueError(name + ' must be finite and positive')
    if args.max_retries < 0:
        raise ValueError('max_retries must be nonnegative')
    if args.requests_per_minute > CONTRACT['rate']['requests_per_minute']:
        raise ValueError('requested frequency exceeds generated policy; verify docs and regenerate')
    if args.row_cap is None or args.row_cap <= 0:
        raise ValueError('row cap unknown; verify current docs and pass --row-cap')
    if CONTRACT.get('row_cap') and args.row_cap > CONTRACT['row_cap']:
        raise ValueError('row cap exceeds catalog; refresh the catalog before regenerating')
    if args.overwrite and (args.append or args.resume):
        raise ValueError('overwrite cannot be combined with append/resume')
    if args.append and not args.dedupe_keys:
        raise ValueError('append requires explicit business keys for idempotence')
    if args.params_json and args.params_file:
        raise ValueError('choose one parameter input')
    explicit = bool(args.params_json or args.params_file)
    records = json.loads(args.params_json or Path(args.params_file).read_text()) if explicit else [{}]
    if isinstance(records, dict):
        records = [records]
    if not isinstance(records, list) or not records or any(not isinstance(x, dict) for x in records):
        raise ValueError('params must be a nonempty object or list of objects')
    common = {k: getattr(args, k) for k in ('ts_code', 'trade_date', 'start_date', 'end_date', 'exchange') if getattr(args, k)}
    if not explicit and not common and CONTRACT['strategy'] != 'single_call':
        raise ValueError('provide explicit bounded params; strategy labels do not expand dates or codes')
    records = [{**common, **r} for r in records]
    allowed = set(CONTRACT.get('input_fields', []))
    for r in records:
        if set(r) - allowed:
            raise ValueError('unknown parameters: ' + ','.join(sorted(set(r) - allowed)))
        if any(k in r for k in ('offset', 'limit')):
            raise ValueError('pagination params are managed by --paginate/--page-size')
        if any(r.get(k) in (None, '') for k in CONTRACT.get('required_fields', [])):
            raise ValueError('missing required parameter')
        if r.get('start_date') and r.get('end_date') and r['start_date'] > r['end_date']:
            raise ValueError('start_date is after end_date')
    if args.fields:
        unknown = set(args.fields.split(',')) - set(CONTRACT.get('output_fields', []))
        if unknown:
            raise ValueError('unknown output fields: ' + ','.join(sorted(unknown)))
    if args.paginate and not {'offset', 'limit'} <= allowed:
        raise ValueError('catalog does not document offset/limit pagination; split params instead')
    if args.page_size is not None and not args.paginate:
        raise ValueError('page-size requires paginate')
    if args.paginate:
        args.page_size = args.page_size or args.row_cap
        if not 0 < args.page_size <= args.row_cap:
            raise ValueError('page size must be within the row cap')
    if args.smoke:
        if args.resume or args.append:
            raise ValueError('smoke must use fresh output')
        records = records[:1]
        args.max_requests, args.max_retries = 1, 0
        args.max_output_files = 1
    return records


def artifact(path, df):
    return {'path': str(path.resolve()), 'sha256': digest(path), 'row_count': len(df), 'columns': list(df.columns), 'dtypes': [str(x) for x in df.dtypes]}


def validate_frame(df, expected_columns, args):
    required = args.fields.split(',') if args.fields else CONTRACT.get('default_fields', [])
    if not set(required) <= set(df.columns) or df.columns.duplicated().any():
        raise ValueError('response missing expected fields or has duplicate columns')
    if expected_columns is not None and list(df.columns) != expected_columns:
        raise ValueError('schema changed between slices/pages')


def fetch_scope(args, records, runner, output):
    import pandas as pd
    checkpoint_dir = output / ('.checkpoint_' + CONTRACT['api'])
    manifest_path = checkpoint_dir / 'manifest.json'
    plan = {'script': digest(__file__), 'records': records, 'fields': args.fields, 'row_cap': args.row_cap,
            'paginate': args.paginate, 'page_size': args.page_size, 'smoke': args.smoke,
            'empty_reason': args.empty_result_reason, 'dedupe_keys': args.dedupe_keys,
            'partition_by': args.partition_by, 'limit_rows': args.limit_rows, 'append': args.append}
    fingerprint = json_hash(plan)
    if args.resume:
        state = json.loads(manifest_path.read_text())
        if state['fingerprint'] != fingerprint:
            raise ValueError('checkpoint request plan or script changed')
        if state.get('complete'):
            raise ValueError('checkpoint already complete; verify existing metadata or start an explicit new run')
    else:
        if manifest_path.exists() and not (args.overwrite or args.append):
            raise ValueError('checkpoint exists; use resume or explicit overwrite')
        state = {'fingerprint': fingerprint, 'chunks': [], 'record': 0, 'offset': 0, 'complete': False}
        atomic_json(manifest_path, state)
    frames = []
    columns = None
    for entry in state['chunks']:
        path = checkpoint_dir / entry['file']
        if path.parent.resolve() != checkpoint_dir.resolve() or digest(path) != entry['sha256']:
            raise ValueError('checkpoint chunk integrity failure')
        df = pd.read_parquet(path)
        validate_frame(df, columns, args)
        columns = list(df.columns)
        frames.append(df)
    while state['record'] < len(records):
        params = dict(records[state['record']])
        if args.paginate:
            params.update(offset=state['offset'], limit=args.page_size)
        df = runner.fetch(params)
        validate_frame(df, columns, args)
        columns = list(df.columns)
        cap = args.page_size if args.paginate else args.row_cap
        if len(df) > cap:
            raise ValueError('response exceeds documented/requested row cap')
        if len(df) == cap and not args.paginate:
            raise ValueError('possible truncation: narrow params or use documented pagination')
        if df.empty and state['offset'] == 0 and not str(args.empty_result_reason or '').strip():
            raise ValueError('empty slice needs independent review; pass empty-result-reason after verification')
        page_hash = hashlib.sha256(df.to_json(orient='split', index=False).encode()).hexdigest()
        if args.paginate and state['offset'] and len(df) == cap and any(e['record'] == state['record'] and e['page_hash'] == page_hash for e in state['chunks']):
            raise ValueError('pagination repeated a full page; offset may be ignored')
        name = f"{fingerprint[:16]}_{state['record']}_{state['offset']}.parquet"
        path = checkpoint_dir / name
        write_parquet(df, path)
        state['chunks'].append({'file': name, 'sha256': digest(path), 'record': state['record'], 'page_hash': page_hash})
        frames.append(df)
        if args.paginate and len(df) == cap:
            state['offset'] += len(df)
        else:
            state['record'] += 1
            state['offset'] = 0
        atomic_json(manifest_path, state)
    data = pd.concat(frames, ignore_index=True)
    return data, state, manifest_path


def publish(data, output, args):
    import pandas as pd
    if args.limit_rows is not None and args.limit_rows < len(data):
        raise ValueError('limit-rows would truncate the requested result')
    keys = args.dedupe_keys.split(',') if args.dedupe_keys else []
    if keys:
        if not set(keys) <= set(data.columns):
            raise ValueError('business keys missing')
        duplicate = data.duplicated(keys, keep=False)
        if duplicate.any() and data[duplicate].drop_duplicates().duplicated(keys).any():
            raise ValueError('conflicting values for business keys; review source variants')
        data = data.drop_duplicates(keys).sort_values(keys, kind='stable')
    if args.partition_by:
        if args.partition_by not in data.columns:
            raise ValueError('partition column missing')
        groups = list(data.groupby(args.partition_by, dropna=False))
    else:
        groups = [(None, data)]
    if not groups or len(groups) > args.max_output_files:
        raise ValueError('invalid number of output files')
    pending = []
    for value, frame in groups:
        suffix = '' if value is None else '_' + json_hash(str(value))[:16]
        path = output / (CONTRACT['api'] + suffix + '.parquet')
        if path.exists() and args.append:
            old = pd.read_parquet(path)
            if list(old.columns) != list(frame.columns):
                raise ValueError('append schema mismatch')
            frame = pd.concat([old, frame], ignore_index=True)
            duplicate = frame.duplicated(keys, keep=False)
            if duplicate.any() and frame[duplicate].drop_duplicates().duplicated(keys).any():
                raise ValueError('append conflicts with existing business keys')
            frame = frame.drop_duplicates(keys).sort_values(keys, kind='stable')
        elif path.exists() and not (args.overwrite or args.resume):
            raise ValueError('output exists; choose overwrite, append, or resume')
        pending.append((path, frame))
    outputs = []
    for path, frame in pending:
        write_parquet(frame, path)
        outputs.append(artifact(path, frame))
    return outputs


def run(args, client_factory=TushareClient, limiter_factory=SharedRateLimiter):
    records = prepare(args)
    token, source = load_token(args.token_env_name, args.allow_config_token)
    output = Path(args.output_dir).expanduser().resolve()
    with run_deadline(args.max_runtime), output_lock(output):
        if args.resume:
            existing = json.loads((output / ('.checkpoint_' + CONTRACT['api']) / 'manifest.json').read_text())
            if existing.get('complete'):
                raise ValueError('checkpoint already complete; existing result retained')
        meta_path = output / ('_fetch_meta_' + CONTRACT['api'] + '.json')
        if meta_path.exists() and not (args.overwrite or args.resume or args.append):
            raise ValueError('output metadata already exists')
        meta = {'contract_version': CONTRACT_VERSION, 'api': CONTRACT['api'], 'success': False,
                'complete': False, 'scope': 'smoke' if args.smoke else 'requested_params',
                'script_sha256': digest(__file__), 'interfaces_json_sha256': CONTRACT['interfaces_json_sha256'],
                'requested_record_count': len(records), 'request_count': 0, 'retry_count': 0,
                'token_source': source, 'started_at': time.time(), 'empty_result_reason': args.empty_result_reason,
                'rate_limit_policy': {**CONTRACT['rate'], 'requests_per_minute_used': args.requests_per_minute,
                                      'safety_factor': 0.9, 'scope': 'local_account_shared'}}
        atomic_json(meta_path, meta)
        client = client_factory(token, args.connect_timeout, args.read_timeout)
        runner = RequestRunner(client, limiter_factory(token, args.requests_per_minute, args.rate_state), args)
        try:
            data, state, manifest = fetch_scope(args, records, runner, output)
            outputs = publish(data, output, args)
            meta.update(success=True, complete=True, row_count=sum(e['row_count'] for e in outputs),
                        source_row_count=len(data), outputs=outputs)
            state['complete'] = True
            atomic_json(manifest, state)
        except Exception as exc:
            meta.update(success=False, complete=False)
            meta['error'] = str(exc).replace(token, '<redacted-token>')
            raise RuntimeError(meta['error']) from None
        finally:
            meta.update(request_count=runner.request_count, retry_count=runner.retry_count, ended_at=time.time())
            atomic_json(meta_path, meta)
            client.close()
        return {'success': True, 'api': CONTRACT['api'], 'row_count': meta['row_count'], 'metadata': str(meta_path)}


def main():
    try:
        result = run(parse_args())
    except Exception as exc:
        # Transport strips credentials before exceptions cross the runtime boundary.
        print(json.dumps({'success': False, 'error': str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
