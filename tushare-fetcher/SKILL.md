---
name: tushare-fetcher
description: Generate, smoke-test, and solidify Tushare data-fetch scripts that respect user points, inferred permission/rate limits, and save results as Parquet. Use when the user asks to create Tushare acquisition scripts, fetch Tushare APIs within allowed frequency, run smoke tests, promote verified scripts into this skill, or update `tushare_interfaces_ai_optimized.json` with solidified script metadata.
---

# Tushare Fetcher

Use this skill to generate repeatable Tushare Pro data-fetch scripts from the machine-readable interface catalog in `references/tushare_interfaces_ai_optimized.json`. Prefer a project-local `docs/tushare_interfaces_ai_optimized.json` when it exists; otherwise use the bundled reference.

Resolve all bundled paths relative to the directory containing this `SKILL.md`. Do not hardcode a user home directory, plugin cache path, or project path. In shell examples below, set `SKILL_DIR` to the absolute path of this skill directory at runtime.

## Workflow

1. Identify the target API and the user's Tushare points.
   - If the user did not provide points, run `scripts/configure_points.py --show`.
   - If no saved points exist, ask the user for their current Tushare points before generation.
   - After the user answers, save it with `scripts/configure_points.py --points N`.
2. Load interface facts from JSON. Do not parse Markdown when JSON exists. Verify current permission, frequency, row-cap and pagination facts before production use; the bundled catalog is a dated snapshot.
3. Run `scripts/generate_fetch_script.py` to create a standalone fetch script.
4. Run `scripts/smoke_test_fetch_script.py` before any solidification.
5. After a passed smoke test, run `scripts/solidify_fetch_script.py` to copy the script into `scripts/solidified/` and update the selected interface JSON.

## Safety Rules

- Points are not entitlement. If the docs imply separate permission, generate only a skeleton unless the user explicitly confirms entitlement.
- Never assume the user's points. Points differ by user and must come from the current request or the user-local config file.
- Store user points only in the user-local config file resolved by `scripts/configure_points.py`; never write personal points into bundled skill references.
- Refuse executable generation when points are below the explicit threshold, the API is missing, the JSON is invalid, or full-history strategy is ambiguous.
- Default token source is environment variable `TUSHARE_TOKEN`. Reading project `config.py` requires `--allow-config-token`.
- Never print or write token values.
- Smoke tests must use `--smoke`, exactly one actual request attempt with zero retries, and a fresh temporary output directory unless the user provides a fresh directory. Empty results require an independently verified reason.
- Do not solidify without passed version-2 smoke evidence and matching script, catalog and output hashes. Regenerated scripts need new smoke evidence; one sample does not validate the full history.

## Runtime and batch requests

Generated standalone scripts use Python 3.10+, `requests`, `pandas`, and `pyarrow`; hard deadlines and shared output locks currently require macOS/Linux. They use the official HTTP API without persisting the token.

Before a batch download or recovery, read [runtime-contract.md](references/runtime-contract.md) for limits, paging, checkpoints, output/evidence rules, and upgrades of existing scripts.

- Supply finite date/code parameter slices. Strategy labels do not automatically enumerate a full history.
- Unknown row caps require current documentation and an explicit `--row-cap`. Reaching a cap fails unless documented offset pagination can finish it.
- All local jobs for the same account must share the default quota DB or the same `--rate-state`; independent hosts/other clients are outside this limiter.
- Use `--resume` for a failed run with the same script and request plan. Do not relabel partial output as success.

## Generate

If points were not given in the current request, first check saved config:

```bash
python3 "$SKILL_DIR/scripts/configure_points.py" --show
```

If the command reports `missing`, ask the user for their current Tushare points, then save:

```bash
python3 "$SKILL_DIR/scripts/configure_points.py" --points 10000
```

Example:

```bash
python3 "$SKILL_DIR/scripts/generate_fetch_script.py" \
  --api stock_basic \
  --points 10000 \
  --output-script ./stock_basic_fetch.py
```

Useful options:

```text
--interfaces-json PATH
--strategy single_call|date_loop|code_loop|date_range|param_grid|user_params
--default-output-dir PATH
--skeleton-only
--confirm-entitlement
--user-config PATH
--save-points
```

The generated script saves Parquet under `./data/tushare/{api}` unless `--output-dir` is provided at run time.

## Smoke Test

Example:

```bash
python3 "$SKILL_DIR/scripts/smoke_test_fetch_script.py" \
  --script ./stock_basic_fetch.py \
  --api stock_basic \
  --result-json ./stock_basic_smoke.json
```

If token is unavailable, run `--help` and compile checks only; do not pretend smoke passed.

## Solidify

Example:

```bash
python3 "$SKILL_DIR/scripts/solidify_fetch_script.py" \
  --api stock_basic \
  --script ./stock_basic_fetch.py \
  --smoke-result ./stock_basic_smoke.json \
  --target skill
```

Default JSON update target is the JSON used by the smoke/generation workflow. If a project JSON exists, updating only the skill-bundled JSON will not affect that project until the project JSON is updated or removed.

## JSON Notes

The bundled JSON is required:

```text
references/tushare_interfaces_ai_optimized.json
```

Solidification writes `interfaces[].solidified_script` with script path/hash, runtime contract version, interface JSON hash, smoke scope/command, Parquet output contract, and rate-limit policy. The generated script is standalone (`runtime_dependency` is empty).

## Validation

When modifying this skill:

```bash
# Set SKILL_DIR to this skill folder and SKILL_CREATOR_DIR to the skill-creator skill folder.
python3 -m py_compile "$SKILL_DIR"/scripts/*.py
python3 "$SKILL_CREATOR_DIR/scripts/quick_validate.py" "$SKILL_DIR"
python3 "$SKILL_DIR/scripts/generate_fetch_script.py" --help
python3 -m pytest "$SKILL_DIR/tests" -q
```

For requested improvement planning, see the source-backed [optimization review](references/optimization-review.md); proposed capabilities there are not implemented features.
