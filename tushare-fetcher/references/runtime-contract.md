# Fetch runtime contract

The generator embeds `scripts/fetch_runtime.py` into each standalone script. That file is the sole maintained execution implementation. Generated scripts need Python 3.10+, `requests`, `pandas`, and `pyarrow`. Local shared locks and hard deadlines currently support macOS/Linux.

## Requests, credentials and rate limits

- Each attempt issues exactly one HTTPS POST to the [official Tushare HTTP API](https://tushare.pro/document/1?doc_id=130), with explicit HTTP/envelope validation. No SDK-method fallback, automatic retry adapter or redirect is used. HTTP errors cannot become successful empty tables.
- `--max-requests` counts actual attempts, including retries and pagination. Exhaustion leaves the requested scope incomplete; it never silently truncates the parameter list.
- Smoke mode forces one attempt and zero retries, regardless of larger CLI values. It selects the first parameter record and labels evidence `scope=smoke`.
- Retry only connection interruptions/timeouts, HTTP 429/5xx and recognized transient service messages. Authentication, permission, points, parameters, fields, TLS, malformed responses and unknown errors stop immediately. Backoff includes jitter; rate-limit waits are at least 60 seconds and respect numeric/date `Retry-After`.
- The token comes from the requested environment variable; `config.py` requires `--allow-config-token`. It is passed in memory, never persisted using `ts.set_token`. Vendor exceptions redact it before crossing the transport boundary.
- All generated scripts on the same machine/account share SQLite reservations under the XDG cache directory (or `~/.cache/tushare-fetcher`). Only a token fingerprint is stored. Reservations use both minimum spacing and a trailing 60-second count, with 10% headroom. Concurrent lower limits apply conservatively to that shared account.
- `--rate-state` is an operational override: every cooperating job must use the same database. Independent hosts, unrelated Tushare clients and multiple tokens for one vendor account are not coordinated by this local limiter. Use an external shared quota service when those deployments are actually needed.
- CLI frequency cannot exceed the generated policy. The parser's undocumented-limit fallback is 6/minute, not evidence of entitlement or a current vendor limit. Check current interface/account conditions before production use.

## Scope, timeouts and recovery

```text
--connect-timeout 10 --read-timeout 30
--idle-timeout 180 --max-runtime 3600
--max-requests 10000 --max-retries 3
--row-cap N
--paginate --page-size N
--resume
```

Socket connection/read timeouts are separate. Idle time bounds periods without a successful response; a POSIX timer bounds the entire run including waits, slow responses and local I/O. Failed or interrupted jobs retain verified completed chunks.

The generator embeds documented input/output field names, required inputs, source catalog hash and a conservatively inferred row cap. If the cap is unknown, verify current documentation and supply `--row-cap`; an override cannot exceed an existing catalog cap. Refresh the catalog and regenerate if its cap changed.

Strategy labels (`date_loop`, `code_loop`, etc.) do not automatically enumerate a universe, trading calendar or history. Provide a finite parameter object/list with explicit date/code slices. Request coverage means those supplied slices, not proof that they describe the entire investment universe/history.

Offset pagination is opt-in and only allowed when the catalog documents both `offset` and `limit`. Full pages continue until a short page, including an empty terminal page. A repeated full page or budget exhaustion fails. APIs without documented pagination must use smaller explicit date/code slices; hitting their cap fails with a possible-truncation error. Automatic adaptive date splitting is not implemented.

Successful chunks are persisted under `.checkpoint_<api>/`. The manifest binds their hashes to the script and request plan. `--resume` verifies hashes and resumes the next unfinished record/page. Changing the script, parameters, fields, pagination, cap or output semantics rejects reuse. A completed manifest cannot be resumed over an already successful result.

## Output and evidence

- Initial empty slices require independent review and `--empty-result-reason`. Whitespace is not a reason. A terminal empty page after previous full pages is valid pagination evidence. The tool cannot itself establish an economic reason for missing data.
- Requested/default fields, consistent page columns, row widths and output hashes are checked. These checks do not establish PIT validity, source freshness, units, complete field-level numerical quality or investment validity.
- Final Parquet is produced only after all requested slices/pages finish. Each file is atomically replaced; multiple partition files are not a single filesystem transaction. Consumers must require final metadata `success=true` and `complete=true` and verify its exact output list/hashes. Failed publication may leave files that must not be treated as a completed dataset.
- `--dedupe-keys` specifies business keys. Exact repeats can be deduplicated; conflicting values fail rather than silently keeping the last variant. `--append` requires business keys and can combine with `--resume`; `--overwrite` cannot combine with either. `--limit-rows` cannot silently truncate a successful result.
- Chunks are reusable but final assembly still reads/concatenates them in memory. Streaming Parquet assembly is a future optimization for very large histories.
- Smoke requires a fresh directory and validates version-2 metadata, API, script/catalog hashes, exactly one request, zero retries, completeness of the sample, and actual Parquet hash/rows/columns/dtypes. Empty samples additionally require the recorded review reason. Output evidence is retained for solidification.
- Solidification rejects old or modified evidence, and checks destinations/catalog conflicts before copying. Standalone outputs have no dependency on the skill's helper module. Passing one smoke request does not validate all permissions, full-history completeness, batch performance or publication readiness.

## Upgrade existing scripts

Already generated standalone files keep their embedded runtime until regenerated. Recreate them using the current generator and the same intended API, parameters and output location. Their hashes change, so run a new smoke test before marking them solidified; never copy an earlier `passed` result onto updated code. Unknown caps/permissions require current documentation or user-provided facts, not guesses.
