"""Offline contract tests: all transport calls use test doubles."""
import importlib.util
import json
import multiprocessing
import signal
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pandas as pd
import pytest
import requests

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
import fetch_runtime as runtime
import generate_fetch_script as generator
import smoke_test_fetch_script as smoke
import solidify_fetch_script as solidify


@pytest.fixture(autouse=True)
def forbid_network(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError('live network is forbidden in tests')
    monkeypatch.setattr(requests.sessions.Session, 'request', forbidden)


@pytest.fixture
def generated(tmp_path, monkeypatch):
    item = {
        'limits': ['限量：单次最大3行'],
        'input_params': [{'name': n, 'required': 'N'} for n in ['ts_code', 'start_date', 'end_date', 'offset', 'limit']],
        'output_params': [{'name': n, 'default_display': 'Y'} for n in ['ts_code', 'value']],
    }
    catalog = tmp_path / 'interfaces.json'
    catalog.write_text(json.dumps({'interfaces': [{'api': 'demo', **item}]}))
    source = generator.render_script('demo', 'code_loop', {}, {'requests_per_minute': 100}, False,
                                     str(tmp_path / 'out'), item=item, interfaces_sha=runtime.digest(catalog))
    path = tmp_path / 'fetch.py'
    path.write_text(source)
    spec = importlib.util.spec_from_file_location('generated_fetch', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setenv('FETCH_TEST_TOKEN', 'test-credential-no-network')
    return module, path, catalog


class NoWait:
    def __init__(self, *args):
        self.calls = 0
    def wait(self):
        self.calls += 1


class FakeClient:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.calls = []
    def query(self, api, params, fields):
        self.calls.append(dict(params))
        value = next(self.responses)
        if isinstance(value, BaseException):
            raise value
        return value
    def close(self):
        pass


def frame(rows=1, start=0):
    return pd.DataFrame({'ts_code': [str(x) for x in range(start, start + rows)], 'value': list(range(start, start + rows))})


def args_for(module, *extra):
    return module.parse_args(['--params-json', '{"ts_code":"A"}', '--token-env-name', 'FETCH_TEST_TOKEN', *extra])


def run_fake(module, args, responses):
    client = FakeClient(responses)
    result = module.run(args, lambda *_: client, NoWait)
    return result, client


def metadata(args):
    return json.loads((Path(args.output_dir) / '_fetch_meta_demo.json').read_text())


@pytest.mark.parametrize('message', ['没有权限', '积分不足', 'invalid token', 'invalid parameter', 'unknown field'])
def test_permanent_errors_are_not_retryable(message):
    assert not runtime.retry_classification(message)


@pytest.mark.parametrize('status,retryable', [(401, False), (403, False), (400, False), (302, False), (429, True), (503, True)])
def test_http_errors_do_not_become_empty_results(monkeypatch, status, retryable):
    client = runtime.TushareClient('test-credential', 2, 7)
    post = Mock(return_value=SimpleNamespace(status_code=status, headers={}))
    monkeypatch.setattr(client.session, 'post', post)
    with pytest.raises(runtime.APIError) as e:
        client.query('demo', {}, '')
    assert e.value.retryable is retryable
    assert post.call_count == 1
    assert post.call_args.kwargs['timeout'] == (2, 7)
    assert post.call_args.kwargs['allow_redirects'] is False


def test_credentials_redacted_from_vendor_error(monkeypatch):
    token = 'test-sensitive-credential'
    client = runtime.TushareClient(token, 2, 7)
    response = SimpleNamespace(status_code=200, json=lambda: {'code': 2002, 'msg': 'bad token ' + token})
    monkeypatch.setattr(client.session, 'post', lambda *a, **k: response)
    with pytest.raises(runtime.APIError) as error:
        client.query('demo', {}, '')
    assert token not in str(error.value)
    assert error.value.retryable is False


def test_smoke_counts_one_attempt_even_on_transient_failure(generated):
    module, _, _ = generated
    args = args_for(module, '--smoke', '--max-retries', '99', '--max-requests', '99')
    client = FakeClient([module.APIError('temporary', retryable=True)])
    with pytest.raises(RuntimeError, match='temporary'):
        module.run(args, lambda *_: client, NoWait)
    assert len(client.calls) == 1
    assert metadata(args)['request_count'] == 1
    assert metadata(args)['success'] is False
    assert args.max_retries == 0


def test_permission_error_stops_without_retries(generated):
    module, _, _ = generated
    args = args_for(module)
    client = FakeClient([module.APIError('permission denied')])
    with pytest.raises(RuntimeError, match='permission denied'):
        module.run(args, lambda *_: client, NoWait)
    assert len(client.calls) == 1


def test_retry_consumes_actual_request_budget(generated, monkeypatch):
    module, _, _ = generated
    monkeypatch.setattr(module.time, 'sleep', lambda _: None)
    args = args_for(module, '--max-requests', '2')
    client = FakeClient([module.APIError('temporary', True), module.APIError('temporary', True), frame()])
    with pytest.raises(RuntimeError):
        module.run(args, lambda *_: client, NoWait)
    assert len(client.calls) == 2
    assert metadata(args)['request_count'] == 2


def test_successful_smoke_has_verified_output_and_provenance(generated):
    module, path, catalog = generated
    args = args_for(module, '--smoke')
    result, client = run_fake(module, args, [frame(2)])
    meta = metadata(args)
    assert len(client.calls) == 1
    assert smoke.validate_outputs(meta, Path(args.output_dir), 'demo', runtime.digest(path), runtime.digest(catalog)) == 2
    assert result['success']


@pytest.mark.parametrize('bad', ['api', 'count', 'complete', 'catalog', 'file', 'rows', 'dtype'])
def test_smoke_rejects_false_or_corrupt_evidence(generated, bad):
    module, path, catalog = generated
    args = args_for(module, '--smoke')
    run_fake(module, args, [frame()])
    meta = metadata(args)
    if bad == 'api': meta['api'] = 'wrong'
    if bad == 'count': meta['request_count'] = 2
    if bad == 'complete': meta['complete'] = False
    if bad == 'catalog': meta['interfaces_json_sha256'] = 'wrong'
    if bad == 'rows': meta['row_count'] = 2
    if bad == 'dtype': meta['outputs'][0]['dtypes'] = ['object', 'float64']
    if bad == 'file': Path(meta['outputs'][0]['path']).write_text('corrupt')
    with pytest.raises(ValueError):
        smoke.validate_outputs(meta, Path(args.output_dir), 'demo', runtime.digest(path), runtime.digest(catalog))


def test_empty_result_requires_explicit_review(generated):
    module, _, _ = generated
    args = args_for(module, '--smoke')
    with pytest.raises(RuntimeError, match='empty slice'):
        run_fake(module, args, [frame(0)])
    assert not metadata(args)['success']


def test_reviewed_empty_smoke_is_distinct(generated):
    module, path, catalog = generated
    args = args_for(module, '--smoke', '--empty-result-reason', 'Verified non-trading date from calendar')
    run_fake(module, args, [frame(0)])
    assert smoke.validate_outputs(metadata(args), Path(args.output_dir), 'demo', runtime.digest(path), runtime.digest(catalog)) == 0


def test_row_cap_fails_closed(generated):
    module, _, _ = generated
    args = args_for(module)
    with pytest.raises(RuntimeError, match='possible truncation'):
        run_fake(module, args, [frame(3)])
    assert not (Path(args.output_dir) / 'demo.parquet').exists()


def test_pagination_resume_skips_verified_chunks(generated):
    module, _, _ = generated
    args = args_for(module, '--paginate', '--page-size', '2', '--max-requests', '1')
    with pytest.raises(RuntimeError, match='budget exhausted'):
        run_fake(module, args, [frame(2)])
    resumed = args_for(module, '--paginate', '--page-size', '2', '--resume')
    result, client = run_fake(module, resumed, [frame(1, 2)])
    assert client.calls == [{'ts_code': 'A', 'offset': 2, 'limit': 2}]
    assert result['row_count'] == 3
    assert list(pd.read_parquet(Path(args.output_dir) / 'demo.parquet')['value']) == [0, 1, 2]


@pytest.mark.parametrize('corrupt', [False, True])
def test_resume_rejects_changed_plan_or_chunk(generated, corrupt):
    module, _, _ = generated
    args = args_for(module, '--paginate', '--page-size', '2', '--max-requests', '1')
    with pytest.raises(RuntimeError):
        run_fake(module, args, [frame(2)])
    if corrupt:
        next((Path(args.output_dir) / '.checkpoint_demo').glob('*.parquet')).write_text('bad')
    resumed = args_for(module, '--paginate', '--page-size', '2', '--resume', *([] if corrupt else ['--fields', 'value']))
    client = FakeClient([])
    with pytest.raises(RuntimeError, match='integrity|changed'):
        module.run(resumed, lambda *_: client, NoWait)
    assert not client.calls


def test_repeated_page_cannot_loop_forever(generated):
    module, _, _ = generated
    args = args_for(module, '--paginate', '--page-size', '2')
    with pytest.raises(RuntimeError, match='repeated a full page'):
        run_fake(module, args, [frame(2), frame(2)])
    assert not metadata(args)['success']


def test_schema_drift_is_not_merged(generated):
    module, _, _ = generated
    args = args_for(module, '--paginate', '--page-size', '2')
    bad = frame().rename(columns={'value': 'other'})
    with pytest.raises(RuntimeError, match='missing expected fields'):
        run_fake(module, args, [frame(2), bad])


@pytest.mark.parametrize('extra', [
    ['--requests-per-minute', 'nan'], ['--max-requests', '0'], ['--max-retries', '-1'],
    ['--requests-per-minute', '101'], ['--row-cap', '4'], ['--append'],
    ['--fields', 'unknown'], ['--page-size', '2'], ['--row-cap', '0'],
])
def test_invalid_settings_fail_before_network(generated, extra):
    module, _, _ = generated
    with pytest.raises(ValueError):
        module.prepare(args_for(module, *extra))


def reserve_worker(path, now, queue):
    queue.put(runtime.SharedRateLimiter('test-account', 60, path).reserve(now))


def test_quota_is_shared_across_processes(tmp_path):
    path = str(tmp_path / 'quota.sqlite3')
    runtime.SharedRateLimiter('test-account', 60, path)
    ctx = multiprocessing.get_context('spawn')
    queue = ctx.Queue()
    workers = [ctx.Process(target=reserve_worker, args=(path, 1000, queue)) for _ in range(3)]
    for p in workers: p.start()
    delays = [queue.get(timeout=10) for _ in workers]
    for p in workers:
        p.join(10)
        assert p.exitcode == 0
    assert delays.count(0) == 1
    assert sum(d > 0 for d in delays) == 2


def test_quota_obeys_interval_window_and_lower_concurrent_cap(tmp_path):
    path = tmp_path / 'quota.sqlite3'
    fast = runtime.SharedRateLimiter('account', 1000, path)
    slow = runtime.SharedRateLimiter('account', 2, path)
    assert fast.reserve(1000) == 0
    assert slow.reserve(1001) > 0
    assert slow.reserve(1061) == 0
    assert fast.reserve(1062) > 0


def test_lock_does_not_remove_owner_on_collision(tmp_path):
    with runtime.output_lock(tmp_path):
        with pytest.raises(RuntimeError):
            with runtime.output_lock(tmp_path):
                pass
        with pytest.raises(RuntimeError):
            with runtime.output_lock(tmp_path):
                pass
    with runtime.output_lock(tmp_path):
        pass


def test_hard_deadline_interrupts_blocked_work():
    with pytest.raises(TimeoutError):
        with runtime.run_deadline(0.02):
            signal.pause()


def test_legacy_smoke_cannot_solidify(tmp_path):
    path = tmp_path / 'smoke.json'
    path.write_text(json.dumps({'status': 'passed'}))
    with pytest.raises(RuntimeError):
        solidify.load_smoke(path)


def test_conflicting_duplicates_cannot_overwrite_data(generated):
    module, _, _ = generated
    args = args_for(module, '--dedupe-keys', 'ts_code')
    df = pd.DataFrame({'ts_code': ['A', 'A'], 'value': [1, 2]})
    with pytest.raises(RuntimeError, match='conflicting values'):
        run_fake(module, args, [df])


def test_idempotent_append_can_resume(generated):
    module, _, _ = generated
    first = args_for(module, '--dedupe-keys', 'ts_code')
    run_fake(module, first, [frame(1)])
    failed = args_for(module, '--append', '--dedupe-keys', 'ts_code', '--paginate', '--page-size', '2', '--max-requests', '1')
    with pytest.raises(RuntimeError, match='budget exhausted'):
        run_fake(module, failed, [frame(2)])
    resumed = args_for(module, '--append', '--resume', '--dedupe-keys', 'ts_code', '--paginate', '--page-size', '2')
    result, _ = run_fake(module, resumed, [frame(1, 2)])
    assert result['row_count'] == 3


def test_resume_completed_run_preserves_success_metadata(generated):
    module, _, _ = generated
    args = args_for(module)
    run_fake(module, args, [frame()])
    meta = metadata(args)
    with pytest.raises(ValueError, match='already complete'):
        run_fake(module, args_for(module, '--resume'), [])
    assert metadata(args) == meta


def test_limit_rows_cannot_silently_truncate(generated):
    module, _, _ = generated
    args = args_for(module, '--limit-rows', '1')
    with pytest.raises(RuntimeError, match='truncate'):
        run_fake(module, args, [frame(2)])


def test_idle_timeout_stops_before_call(generated, monkeypatch):
    module, _, _ = generated
    args = args_for(module, '--idle-timeout', '1')
    runner = module.RequestRunner(FakeClient([frame()]), NoWait(), args)
    runner.last_progress -= 2
    with pytest.raises(TimeoutError, match='idle timeout'):
        runner.fetch({})
    assert runner.request_count == 0


def test_documented_cap_and_permission_gate():
    item = {'limits': ['权限：需单独开权限', '限量：单次最大5000，支持分页提取数据'], 'point_thresholds': []}
    p = generator.classify_permission(item, 10000, False)
    assert generator.decide_generation(p, 'single_call', False)[0] == 'skeleton_only'
    contract = generator.build_contract('demo', 'single_call', p, {}, True, '.', item, 'sha')
    assert contract['row_cap'] == 5000
    p = generator.classify_permission({'point_thresholds': [2000]}, 100, False)
    assert generator.decide_generation(p, 'single_call', False)[0] == 'refuse'


def test_cli_generate_smoke_solidify_and_stale_artifact_guard(tmp_path):
    import os
    import subprocess
    stage = tmp_path / 'project'
    (stage / 'docs').mkdir(parents=True)
    catalog = stage / 'docs' / 'tushare_interfaces_ai_optimized.json'
    catalog.write_text(json.dumps({'interfaces': [{
        'api': 'demo', 'point_thresholds': [2000], 'limits': ['单次最大10行'],
        'input_params': [{'name': 'ts_code', 'required': 'N'}],
        'output_params': [{'name': 'ts_code', 'default_display': 'Y'}],
    }]}))
    # Child processes use this fake HTTP module; no Tushare token/network is used.
    fake = tmp_path / 'fake_transport'
    fake.mkdir()
    (fake / 'requests.py').write_text('''
class Response:
    status_code = 200
    def json(self):
        return {'code': 0, 'data': {'fields': ['ts_code'], 'items': [['A']]}}
class Session:
    def post(self, *args, **kwargs):
        assert kwargs['allow_redirects'] is False
        assert len(kwargs['timeout']) == 2
        return Response()
    def close(self): pass
class exceptions:
    SSLError = type('SSLError', (Exception,), {})
    Timeout = type('Timeout', (Exception,), {})
    ConnectionError = type('ConnectionError', (Exception,), {})
''')
    env = dict(os.environ, PYTHONPATH=str(fake), XDG_CACHE_HOME=str(tmp_path / 'cache'),
               TUSHARE_TOKEN='fake-offline-token', PYTHONDONTWRITEBYTECODE='1')
    output_script = stage / 'fetch.py'
    def cli(name, *args, success=True):
        result = subprocess.run([sys.executable, str(SCRIPTS / name), *map(str, args)],
                                cwd=stage, env=env, text=True, capture_output=True, timeout=15)
        assert (result.returncode == 0) is success, result.stderr + result.stdout
        return result
    cli('generate_fetch_script.py', '--api', 'demo', '--points', '10000', '--strategy', 'single_call', '--output-script', output_script)
    evidence = stage / 'smoke.json'
    cli('smoke_test_fetch_script.py', '--script', output_script, '--api', 'demo', '--result-json', evidence, '--output-dir', stage / 'smoke-output')
    result = json.loads(evidence.read_text())
    assert result['request_count'] == 1 and result['retry_count'] == 0 and result['status'] == 'passed'
    destination = stage / 'reusable.py'
    # A failed preflight must not install a script.
    cli('solidify_fetch_script.py', '--api', 'demo', '--script', output_script, '--smoke-result', evidence,
        '--target', 'project', '--target-script-path', destination, '--update-both-json', success=False)
    assert not destination.exists()
    cli('solidify_fetch_script.py', '--api', 'demo', '--script', output_script, '--smoke-result', evidence,
        '--target', 'project', '--target-script-path', destination)
    assert destination.read_bytes() == output_script.read_bytes()
    saved = json.loads(catalog.read_text())['interfaces'][0]['solidified_script']
    assert saved['runtime_contract_version'] == 2 and saved['runtime_dependency'] == ''
    Path(result['outputs'][0]['path']).write_text('changed')
    with pytest.raises(RuntimeError, match='changed after validation'):
        solidify.load_smoke(evidence)


def test_smoke_cli_rejects_stale_output_directory(tmp_path):
    import subprocess
    output = tmp_path / 'output'
    output.mkdir()
    (output / 'stale.parquet').write_text('old')
    result = subprocess.run([sys.executable, str(SCRIPTS / 'smoke_test_fetch_script.py'),
                             '--script', str(SCRIPTS / 'fetch_runtime.py'), '--api', 'demo',
                             '--output-dir', str(output)], text=True, capture_output=True)
    assert result.returncode != 0
    assert 'must be empty' in result.stderr


def test_retry_after_date_is_respected(monkeypatch):
    from datetime import datetime, timezone
    from email.utils import format_datetime
    now = runtime.time.time()
    response = SimpleNamespace(status_code=429, headers={'Retry-After': format_datetime(datetime.fromtimestamp(now + 180, timezone.utc))})
    client = runtime.TushareClient('fake', 2, 7)
    monkeypatch.setattr(client.session, 'post', lambda *a, **k: response)
    with pytest.raises(runtime.APIError) as error:
        client.query('demo', {}, '')
    assert error.value.retry_after >= 178


def test_whitespace_does_not_approve_empty_result(generated):
    module, _, _ = generated
    with pytest.raises(RuntimeError, match='empty slice'):
        run_fake(module, args_for(module, '--empty-result-reason', '   '), [frame(0)])
