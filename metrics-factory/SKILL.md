---
name: metrics-factory
description: "Use when working with MetricsFactory financial metric calculators in any local repository: portable runtime checks, project-local environment setup, AI-safe metric jobs, period metrics, rolling technical indicators, supported periods/windows, adjusted NAV contracts, parquet input validation, auto parallel planning, dry-run manifests, or metric catalog extraction."
---

# MetricsFactory

## Decision Tree

- Runtime or portability question: run `python <skill-dir>/scripts/check_runtime.py --project-root <project-root>`.
- Missing dependencies or native wheel mismatch: run `python <skill-dir>/scripts/setup_runtime.py --project-root <project-root>` after user accepts creating a project-local venv.
- Metric support question: read `references/metric-index.json` first. It is the machine-readable index of executable metrics, windows, dependencies, and risk tags. Regenerate it with `python <skill-dir>/scripts/export_metric_catalog.py --project-root <project-root> --format index --output <skill-dir>/references/metric-index.json` when checking a different MetricsFactory source tree.
- Human metric explanation: read `references/metric-definitions.md` after `metric-index.json`.
- AI-run calculation job: run `--dry-run` before `--execute` with `scripts/run_metrics_job.py`.
- Metric explanation or metric changes: verify the actual `cal_*` implementation and dispatch in `period_metrics_cal.py` or `rolling_metrics_cal.py`; do not rely only on config prose.

`<skill-dir>` is this skill directory. `<project-root>` is the local MetricsFactory source directory containing `metrics_factory.py` and `metrics_cal_config.py`.

## Portable Runtime

- Do not assume `.venv`, Homebrew, Conda, or any user-specific Python path exists.
- Preferred interpreter order: `METRICS_FACTORY_PYTHON`, active venv Python, `<project-root>/.metricsfactory-venv`, `<project-root>/.venv`, then `python3` if it passes `check_runtime.py`.
- Automatic installation is allowed only into a project-local venv, normally `<project-root>/.metricsfactory-venv`.
- Never install dependencies into system Python or global user site-packages unless the user explicitly requests that.
- Runtime scripts support `--project-root`; use it whenever the skill is installed globally.
- See `references/environment.md` for dependency ranges and setup rules.

## Core Commands

```bash
python <skill-dir>/scripts/check_runtime.py --project-root <project-root>
python <skill-dir>/scripts/setup_runtime.py --project-root <project-root>
<python> <skill-dir>/scripts/run_metrics_job.py --project-root <project-root> --request job.json --dry-run
<python> <skill-dir>/scripts/run_metrics_job.py --project-root <project-root> --request job.json --execute
```

Use the Python that passed `check_runtime.py`. If `setup_runtime.py` created a venv, use `<project-root>/.metricsfactory-venv/bin/python` on macOS/Linux or `<project-root>/.metricsfactory-venv/Scripts/python.exe` on Windows.

Use risk override flags only when the user explicitly accepts the related risk:

- `--allow-unknown-basis`: price basis is unknown.
- `--allow-unknown-adjustment-asof`: adjusted price/NAV as-of timing is unknown.
- `--allow-unknown-signal-timing`: downstream feature timing is unknown.
- `--allow-rolling-open-close-risk`: legacy flag for direct core rolling calls; normal `run_metrics_job.py` rolling execution bypasses the core open/close mismatch.

V1 request and error details live in `references/job-schema.md`.

## Source Of Truth

- Real behavior lives in `metrics_factory.py`, `period_metrics_cal.py`, and `rolling_metrics_cal.py`.
- `metrics_cal_config.py` owns metric names, Chinese labels, formulas, and supported window mappings, but formula text is not enough to prove implementation behavior.
- `log_return_relative_metrics_dict` and `long_short_metrics` are not wired into current public entrypoints.
- The scripts register a `MetricsFactory` package alias for the chosen project root, so the source directory does not have to be named `MetricsFactory`.

## Hard Input Contract

- Inputs are wide `pandas.DataFrame` objects: ascending date index, product codes as columns, numeric values.
- All required input frames must have exactly the same index, columns, and order. The core code uses `.values` and will not align by labels.
- Period jobs need `log_return_df`, `close_price_df`, `high_price_df`, `low_price_df`, `volume_df`.
- Rolling jobs need `open_price_df`, `close_price_df`, `high_price_df`, `low_price_df`, `volume_df`.
- `fund_list` is direct column selection; missing product codes should be treated as blockers.
- `spec_end_date` must be a trading day in the input index.

## Adjusted NAV Contract

- Strongly prefer adjusted NAV or adjusted close for `close_price_df`.
- Build `log_return_df` from the same adjusted close/NAV series.
- Keep `open/high/low/close` on the same adjustment basis.
- For backtests or model signals, adjusted prices/NAV must be point-in-time: adjustment factors must be known as of each output date.
- Treat full-sample adjusted prices as unsafe for signals unless the user accepts future adjustment-factor leakage.
- Do not mix unadjusted price, unit NAV, and accumulated NAV.
- If NAV products lack OHLC, adjusted NAV can temporarily fill OHLC, but AR/BR/DKX/CCI style indicators become weaker.
- Do not interpret `Vol*`, `OBV`, `PVT`, `VR`, or related volume metrics unless volume is real.

## Feature Timing Contract

- Outputs dated `t` include `t` end-of-day data: period jobs include `t` log return/close/high/low/volume, and rolling jobs include row `t` in rolling windows.
- This is not a future-row leak for end-of-day research or `t+1`/next-period signals.
- It is a lookahead risk for same-day pre-close or same-day open signals. Shift metric features by at least one trading row before same-day trading use.
- In job JSON, set `data_contract.signal_timing` to `eod_next_period` or `research_eod`. `same_day_before_close` is blocked by the runner.

## Period Calculation Contract

- `compute_metrics_for_period_initialize(...)` writes one `{period}.parquet` per period and returns no result DataFrame.
- Direct core calls require `save_path` to already exist. The AI job runner creates and manages its output directory.
- Default traversal uses `period_list`, but only periods present in `create_period_metrics_map()` are computed.
- Default `period_list` includes unmapped `3y`, `5y`, `mtd`, `qtd`, `ytd`, `max`; they are skipped by current code.
- Configured `30d`, `35d`, `70d` are not in default `period_list`; pass them explicitly.
- `Nd` periods use trading-day offsets. `Nm/Ny/mtd/qtd/ytd` use natural-date boundaries via `get_start_date()`.
- Period multi-process is real: it parallelizes end-date tasks inside one period with `multiprocessing.Pool` and shared memory.

## Rolling Calculation Contract

- Direct `compute_all_rolling_metrics(...)` writes `rolling_metrics.parquet` and returns no result DataFrame.
- Direct core calls require `save_path` to already exist. The AI job runner creates and manages its output directory.
- `run_metrics_job.py` does not call the buggy public rolling entrypoint for execution; it calls `CalRollingMetrics` with keyword arguments so close/open are bound correctly.
- Supported rolling windows are from `create_rolling_metrics_map().keys()`: `0, 3, 4, 5, 6, 7, 8, 9, 10, 12, 14, 15, 19, 20, 22, 25, 26, 30, 35, 60, 99`.
- Window `0` is for non-window metrics such as `OBV`, `PVT`, and `TR`.
- Rolling `num_workers` is currently ignored; do not claim rolling jobs are parallelized.
- V1 job requests must leave `selection.rolling_metrics` as `null`; the public rolling entrypoint does not accept a metrics subset.
- Rolling windows are merged with inner joins across windows, so the final row set can shrink.

## Known Blocking Risks

- Direct core rolling open/close mismatch: `compute_all_rolling_metrics()` passes `open_price_array, close_price_array` into `CalRollingMetrics`, while the constructor signature expects `close_price_array, open_price_array`.
- `run_metrics_job.py` bypasses that mismatch by using keyword arguments. If calling core code directly, fix or test with a small fixture where open and close intentionally differ. Check at least `CloseMA`, `EMA`, `KDJ`, `VR`, `OBV`, `AR`, `BR`, and `DKX`.
- Unknown `signal_timing` and unsafe same-day pre-close usage are blocked by `run_metrics_job.py` unless explicitly accepted where applicable.
- Full-sample adjusted prices are blocked for adjusted price/NAV jobs because they can leak future split/dividend/distribution factors.
- Runtime import can fail even if `py_compile` passes when the active Python and local NumPy/Pandas wheels use different CPU architectures. Run `check_runtime.py` before diagnosing business logic.

## Dry Run And Manifest

`run_metrics_job.py --dry-run` must be used before execute when an AI agent is preparing a job. It reports:

- input paths, shape, date range, product count, and exact index/column alignment;
- adjusted NAV/price basis declaration;
- executable periods/windows and skipped periods/windows;
- blockers, warnings, and `can_execute`;
- expected output files;
- auto-parallel decisions and worker counts.

`--execute` writes `run_manifest.json` with job inputs, risk acceptance, output files, row/column counts, environment details, git status, blockers/warnings, and parallel decisions. Missing manifest means the execution is not audit-complete.

## Validation

After skill edits:

```bash
python ${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-creator/scripts/quick_validate.py <skill-dir>
python -m py_compile <skill-dir>/scripts/*.py
python <skill-dir>/scripts/check_runtime.py --project-root <project-root>
python <skill-dir>/scripts/export_metric_catalog.py --project-root <project-root> --format json
python <skill-dir>/scripts/export_metric_catalog.py --project-root <project-root> --format index
```

Before runtime calculation, also run a dry-run request with a Python that passed `check_runtime.py`.

## References

- `references/environment.md`: portable Python, dependency, and auto-install rules.
- `references/job-schema.md`: V1 JSON request schema, risk levels, output and manifest rules.
- `references/metric-index.json`: AI-first machine-readable metric index; use this to choose executable metrics and windows.
- `references/metric-definitions.md`: human-readable metric meaning and calculation notes.
- `references/metric-catalog.md`: current metric catalog snapshot; regenerate for the target repository before final claims.
- `scripts/check_runtime.py`: runtime compatibility check.
- `scripts/setup_runtime.py`: project-local venv creation and dependency installation.
- `scripts/export_metric_catalog.py`: static catalog extraction without importing NumPy/Pandas.
- `scripts/run_metrics_job.py`: AI-safe dry-run and execution wrapper.
