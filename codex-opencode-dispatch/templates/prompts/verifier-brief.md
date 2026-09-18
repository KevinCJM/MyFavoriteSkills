Protocol: ocw/1
Kind: dispatch
Task: <task-id>
Revision: <positive-integer>
Attempt: <positive-integer>
Role: verifier
Mode: full
Workspace: <absolute-OpenCode-server-path>
Snapshot: <concrete-base-and-dirty-state-or-snapshot-id>
Risk: high

## Goal
Independently review <task> at the exact assigned candidate. Do not implement fixes.

## Inputs
Authoritative specification: <brief path/revision and required ACs>
Review baseline/candidate: <exact identities, including dirty snapshot when relevant>
Diff/manifest: <complete accessible evidence, not only unstaged git diff>
Builder report: <path; unverified claims, inspect after reading specification>
Trusted check evidence: <runner references, or missing>

## Scope
Write: none
Read: diff and necessary related code; expand only for a named semantic risk.
Artifacts: <review-only permitted path, or inline-only>
No product edits, recursive review delegation, branch changes or unsolicited full suites.

## Decisions
Fixed: acceptance is Codex's decision; judge both spec coverage and code quality.
Free: choose focused inspection for a named current-task risk; report unverifiable coverage.
For full/governed tasks inspect the C-ID Q1–Q4 answers; for compact tasks inspect the
Boundary/AC against the actual diff, including edits within allowed files. Missing
justification, unnecessary changes, or contract drift blocks acceptance.
Do not mandate style-only refactoring, historical debt cleanup, or unrelated baseline bug
fixes. Report serious unrelated hazards separately and pause hazardous work when needed;
a reviewer finding cannot authorize a new requirement or contract change.
Escalate: an unsafe/wrong requirement, missing candidate, insufficient evidence, or required
checks outside the approved permission/resource scope. A bad brief is not self-validating.

## Acceptance
- AC-1: map original task requirements to supported/unsupported/not_checked evidence.
- AC-2: identify concrete correctness/regression/test-integrity defects with locations and
  consequences; distinguish unrelated baseline observations from current blockers. No issue quota.

## Checks
- V-1 -> AC-1, AC-2: inspect existing test/fixture/tolerance/skip/config changes first,
  then risk-bearing hunks and necessary callers; compare exact candidate to baseline.
- V-2 -> AC-1: inspect check provenance and snapshot; request a narrow missing check rather
  than treating self-report as proof or repeating all observed tests automatically.

## Stop
Stop when the defined coverage/risk questions are answered or explicit gaps remain.
Do not repeatedly search for hypothetical issues after the verification contract is met.

## Return
Identity/candidate; spec verdict; quality verdict; findings with requirement/path/location,
consequence, evidence and smallest correction; unverified areas; executed checks if any.
Report in <language>. No statement that the task is accepted or merged.
