Protocol: ocw/1
Kind: dispatch
Task: WP-08
Revision: 1
Attempt: 1
Role: builder
Mode: compact
Workspace: /srv/example-project/wt-config
Snapshot: git:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa; clean
Risk: low

## Goal
Update the three documented timeout examples to the approved spelling timeout_ms.

## Scope
Write: docs/config.md
Read: AGENTS.md; docs/config.md
Artifacts: inline-only
Preserve all example values and other text. Local edit method is free; changing the API is not.
Boundary: this correction is explicitly requested; leaving it unchanged keeps the three
examples wrong; edit only those keys; runtime/API/config/default/log/data/dependency/workflow
contracts remain unchanged. Do not polish neighboring prose.

## Acceptance
- AC-1: all three named example keys read timeout_ms, with values unchanged.

## Checks
- V-1 -> AC-1: inspect the diff against the assigned snapshot; count the three example keys
  and confirm their original values remain unchanged. No execution or test suite is required.

## Return
Identity/candidate/status, changed path and focused diff evidence; include blockers.
Apply ocw/1 worker rules. Do not expand scope or return a development diary.
