Protocol: ocw/1
Kind: dispatch
Task: WP-07
Revision: 1
Attempt: 1
Role: builder
Mode: full
Workspace: /srv/example-project/wt-config
Snapshot: git:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa; clean
Risk: medium

## Goal
Reject invalid timeout_ms configuration while preserving the public loader API.

## Inputs
Read AGENTS.md, src/config/loader.py::load_config, src/config/timeout.py::parse_timeout,
and tests/config/test_timeout.py. These are example paths, not verified user repository facts.
Approved behavior: timeout_ms must be a built-in int, not bool, and greater than zero.
Hypothesis: missing type validation causes True to be accepted; verify rather than assume.
Dependencies: none. Baseline is the assigned clean fixture snapshot.

## Scope
Write: src/config/timeout.py; tests/config/test_timeout.py
Read: AGENTS.md; src/config/; tests/config/
Artifacts: inline-only; test caches/temp files only in the configured fixture scratch area.
Protected: public load_config signature, lockfiles, fixtures outside owned scope and user data.
Resources: fixture-local tests only; no production service, package install or network.

## Decisions
Fixed: valid built-in positive ints retain their value; bool/float/string/zero/negative
values raise ValueError. Do not change the config-loader API or exception type.
Free: reuse existing validators or add a private helper inside the assigned module.
Escalate: an API/schema/behavior change or new dependency is required.
Existing-test edits authorized: add parameterized negative cases, not remove/weaken existing cases.
In this fixture the approved contract already requires the rejection; baseline acceptance
of bool is an implementation violation, not permission to change an undocumented API.

| Change | Q1: current requirement | Q2: blocker if unchanged | Q3: smallest correct change | Q4: preserved contracts / evidence | Disposition |
|---|---|---|---|---|---|
| C-1: local timeout validation | AC-1, AC-2 | invalid values continue to violate the assigned rule | change the local validation branch; do not rewrite the loader | preserve positive-int values, ValueError, loader signature, defaults, logs and unrelated flows; verify relevant callers with V-2 | eligible |
| C-2: focused negative-case tests | AC-2 verification | no regression check for the listed rejected types | extend the existing test file only | no removal/weakening, new test framework or config changes; inspect diff and execute V-1 | eligible |
| C-3: rename adjacent loader variables | no current requirement | none | leave unchanged | not assessed because already out of scope | omit |

These are fixture design assumptions to verify before editing; any contradicting source
or contract uncertainty blocks that edit. No whole-file formatting or unrelated fixes.

## Acceptance
- AC-1: valid built-in positive int timeout_ms values are unchanged.
- AC-2: True, 1.0, "1", 0 and -1 are rejected with ValueError.
- AC-3: load_config public signature and unrelated config behavior remain unchanged.

## Checks
- V-1 -> AC-1, AC-2: run python -m pytest tests/config/test_timeout.py from the assigned
  workspace with the fixture's existing isolated test environment; record collection and exit.
- V-2 -> AC-3: inspect loader signature and diff; run the existing config regression command
  declared by fixture AGENTS.md. If absent or unavailable, report not_checked with the reason.

## Stop
Stop once these changes/checks and one self-review are done. Report baseline/rule conflicts,
missing verification or forbidden-scope needs. No recursive delegation, commits or model changes.

## Return
Chinese receipt: identity, candidate, status, AC coverage, actual commands/results/evidence,
changed paths and every blocker. Full logs remain in permitted test artifacts; no diary.
