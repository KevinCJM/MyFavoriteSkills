# MetricsFactory Job Schema

This reference defines the V1 request file for `scripts/run_metrics_job.py`.

## Commands

```bash
<python> <skill-dir>/scripts/run_metrics_job.py --project-root <project-root> --request job.json --dry-run
<python> <skill-dir>/scripts/run_metrics_job.py --project-root <project-root> --request job.json --execute
```

Risk override flags:

```bash
--allow-unknown-basis
--allow-rolling-open-close-risk
--allow-unknown-adjustment-asof
--allow-unknown-signal-timing
```

## Request

```json
{
  "schema_version": "1.0",
  "job_name": "example_period_metrics",
  "mode": "period",
  "data": {
    "format": "parquet",
    "log_return": "data/log_return.parquet",
    "close_price": "data/close_price.parquet",
    "open_price": null,
    "high_price": "data/high_price.parquet",
    "low_price": "data/low_price.parquet",
    "volume": "data/volume.parquet",
    "date_index": true,
    "date_column": null
  },
  "data_contract": {
    "price_basis": "adjusted_nav",
    "adjustment_asof": "point_in_time",
    "ohlc_basis": "same_as_close",
    "volume_basis": "real_or_not_used",
    "signal_timing": "eod_next_period"
  },
  "selection": {
    "fund_list": null,
    "periods": ["25d"],
    "roll_windows": null,
    "period_metrics": null,
    "rolling_metrics": null,
    "spec_end_date": null,
    "min_data_required": 2
  },
  "output": {
    "save_path": "outputs/metrics",
    "overwrite": false,
    "run_id": null,
    "atomic_write": true
  },
  "parallel": {
    "mode": "auto",
    "max_workers": null,
    "reserve_cores": 1,
    "min_tasks_per_worker": 4,
    "memory_headroom_gb": 2
  },
  "risk_acceptance": {
    "allow_unknown_basis": false,
    "allow_rolling_open_close_risk": false,
    "allow_unknown_adjustment_asof": false,
    "allow_unknown_signal_timing": false
  }
}
```

## Field Rules

- `schema_version` must be `"1.0"`.
- `mode` is `period`, `rolling`, or `both`.
- V1 supports only `data.format = "parquet"`.
- `data.date_index = true` means the parquet index is the date index.
- `data.date_index = false` requires `data.date_column`; the script sets that column as the index.
- Date index must parse as `pd.DatetimeIndex`, be ascending, and have no duplicates.
- All required input frames must have identical index, columns, and column order.
- `selection.period_metrics` can be `null`, a list, or a mapping keyed by period.
- `selection.rolling_metrics` must be `null` in V1. The current public rolling entrypoint does not accept a metrics subset.
- `selection.periods = null` uses the default executable period mapping; `[]` means no period calculation.
- `selection.roll_windows = null` uses all executable rolling windows; `[]` means no rolling calculation.
- `output.run_id = null` creates a deterministic child directory under `save_path` using `job_name` and the normalized request hash. This keeps dry-run and execute plan hashes stable when the request is unchanged.
- `output.run_id = "."` writes directly into `save_path` and makes overwrite checks stricter.
- `data_contract.adjustment_asof` is `point_in_time`, `full_sample`, `not_applicable`, or `unknown`.
- If `price_basis` is adjusted, use `adjustment_asof = "point_in_time"` for backtests/signals. `full_sample` is blocked because it can leak future split/dividend/distribution factors.
- `data_contract.signal_timing` is `eod_next_period`, `research_eod`, `same_day_before_close`, or `unknown`.
- Outputs dated `t` include `t` end-of-day inputs. `same_day_before_close` is blocked; use `eod_next_period` for t-close features used at t+1 or later.
- `run_metrics_job.py` executes rolling metrics through `CalRollingMetrics` keyword arguments, not the public `compute_all_rolling_metrics()` call path, so it bypasses the known open/close argument-order mismatch.

## Issue Levels

`blocker`: execution is not allowed.

`warning`: execution is allowed, but the final answer must mention the risk.

`info`: execution fact for audit only.

Common blockers:

- missing input file;
- unknown schema version;
- unsupported input format;
- invalid or duplicated date index;
- mismatched input index or columns;
- required input missing for selected mode;
- `price_basis = "unknown"` without explicit risk acceptance;
- adjusted price/NAV with `adjustment_asof = "unknown"` or `"full_sample"` without explicit risk acceptance where allowed;
- `signal_timing = "unknown"` without explicit risk acceptance;
- `signal_timing = "same_day_before_close"`;
- explicit period/window/metric not executable by current mappings;
- target output already exists while `overwrite = false`;
- runtime import failure for pandas, numpy, or MetricsFactory.
  First run `check_runtime.py`; if dependencies are missing, create a project-local runtime with `setup_runtime.py`.

Common warnings:

- unknown price basis accepted by user;
- unknown adjusted-price as-of timing accepted by user;
- unknown signal timing accepted by user;
- direct core rolling open/close risk accepted by user;
- volume metrics requested when `volume_basis` is not real;
- default period list contains unmapped periods that are skipped;
- available memory cannot be detected, so worker count is capped conservatively.

## Manifest

Successful execute writes `run_manifest.json` next to the output parquet files. It records:

- request path and normalized request fields;
- input file summaries;
- selected periods/windows and metrics;
- blockers, warnings, and risk acceptance;
- auto-parallel decisions and worker counts;
- expected and written output files;
- row count, column count, and file size for outputs;
- Python, pandas, numpy versions;
- git commit or git status summary;
- `plan_hash`, so executed manifests are tied to the planned job.

If manifest writing fails, treat the job as failed even when parquet files were produced.
