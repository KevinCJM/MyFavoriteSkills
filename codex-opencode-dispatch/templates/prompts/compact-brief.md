Protocol: ocw/1
Kind: dispatch
Task: <task-id>
Revision: <positive-integer>
Attempt: <positive-integer>
Role: builder
Mode: compact
Workspace: <absolute-OpenCode-server-path>
Snapshot: <concrete-base-and-dirty-state-or-snapshot-id>
Risk: low

## Goal
<one bounded outcome>

## Scope
Write: <specific product paths, or none>
Read: <necessary rules/files/symbols>
Artifacts: <permitted paths, or inline-only>
Preserve: <unchanged behavior and user modifications>
Free: necessary local implementation only; no cleanup or unsolicited fixes.
Boundary: <one concise sentence covering the four-question gate: current requirement; what
remains unsatisfied if unchanged; smallest correct intervention; relevant contracts preserved
or the specific unresolved contract risk>. No C-ID table or ledger is required for this
compact task. If the boundary cannot be stated confidently, stop or use the full form.

## Acceptance
- AC-1: <observable result, including exact edge behavior>

## Checks
- V-1 -> AC-1: <existing command + cwd + expected evidence, or named inspection>

## Return
Report Task/Revision/Attempt, candidate, ready_for_review|needs_context|blocked|partial,
AC-1 coverage, changed paths, actual check result/evidence, and all blockers. No diary.
Report in <language>. Apply the supplied ocw/1 worker rules; do not change acceptance.
