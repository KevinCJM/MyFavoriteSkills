Protocol: ocw/1
Kind: dispatch
Task: <task-id>
Revision: <positive-integer>
Attempt: <positive-integer>
Role: scout
Mode: full
Workspace: <absolute-OpenCode-server-path>
Snapshot: <concrete-base-and-dirty-state-or-snapshot-id>
Risk: low

## Goal
Answer <bounded question>; collect facts needed for <Codex decision>.

## Inputs
Read first: <project rules + likely paths/symbols>
Known facts: <sources, or none>
Unconfirmed hypothesis: <optional diagnostic lead; do not assume true>

## Scope
Write: none
Read: <permitted repository areas and bounded expansion for related call sites>
Artifacts: <report-only path, or inline-only>
Do not run mutation-capable tests/setup, alter product files, or use external services.

## Decisions
Fixed: this is investigation, not implementation or final architecture choice.
Free: choose efficient searches and inspect related permitted evidence.
Escalate: missing access or contradictory authoritative requirements. No code edits, even
for an obvious nearby bug. Distinguish current blockers, unrelated baseline observations
and unverified suspicions; do not start an unsolicited technical-debt inventory.

## Acceptance
- AC-1: <question requiring concrete file/symbol evidence>
- AC-2: <impact/test-coverage question; allow explicit not-found with search scope>

## Checks
- V-1 -> AC-1, AC-2: cite source paths/symbols and snapshot; separate facts, inference,
  and unknowns. Trace only the necessary edges; do not claim an exhaustive absence from
  a narrow search.

## Stop
Stop when each question has supported findings or an explicit bounded evidence gap.
No whole-repository survey or design document unless it answers the assigned question.

## Return
Identity/candidate/status, answers by AC ID with references, search limits, uncertainties,
and the smallest follow-up Codex must decide. Report in <language>. No source dumps.
