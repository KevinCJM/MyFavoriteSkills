Protocol: ocw/1
Kind: dispatch
Task: WP-06
Revision: 1
Attempt: 1
Role: scout
Mode: full
Workspace: /srv/example-project/wt-config
Snapshot: git:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa; clean
Risk: low

## Goal
Identify where timeout_ms enters validation and which tests cover its type boundaries.

## Inputs
Read AGENTS.md and start at src/config/loader.py. The suspected bool acceptance is an
unverified hypothesis, not an approved change request. No other task dependencies.

## Scope
Write: none
Read: AGENTS.md; src/config/; tests/config/; directly related call sites in src/
Artifacts: inline-only
No tests, installs or external services. Search only enough to answer the questions.

## Decisions
Fixed: gather facts, do not change behavior or recommend a new public API as approved.
Free: select targeted searches and inspect bounded call chains.
Escalate: required paths are inaccessible or the assigned snapshot does not match.

## Acceptance
- AC-1: identify the loader-to-validator path with file/symbol evidence.
- AC-2: describe existing boundary tests and explicit coverage gaps within the search scope.

## Checks
- V-1 -> AC-1, AC-2: source inspection at the assigned snapshot; return file/symbol references,
  distinguish observed behavior from inference, and name limits of any not-found result.

## Stop
Stop when both questions are answered or blocked by a specific evidence gap.

## Return
Chinese identity/status receipt, answers by AC ID, references, unknowns and search bounds.
No repository dump or code edits.
