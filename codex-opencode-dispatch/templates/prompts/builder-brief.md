Protocol: ocw/1
Kind: dispatch
Task: <task-id>
Revision: <positive-integer>
Attempt: <positive-integer>
Role: builder
Mode: full
Workspace: <absolute-OpenCode-server-path>
Snapshot: <concrete-base-and-dirty-state-or-snapshot-id>
Risk: medium

## Goal
<cohesive implementation outcome; why it matters in one sentence>

## Inputs
Rules: <applicable AGENTS.md and approved specifications, accessible paths>
Facts: <verified behavior + file/symbol or evidence>
Hypotheses: <label explicitly, or none>
Dependencies: <accepted task/artifact version + interface, or none>
Baseline: <clean or exact user/dirty changes that must be preserved>

## Scope
Write: <owned product paths>
Read: <relevant permitted paths, with room for bounded call-site investigation>
Artifacts: <report/log/cache/scratch paths permitted, or inline-only>
Protected: <public contracts, dependency lockfiles, tests/config, secrets, other owners>
Resources: <assigned test DB/ports, or no external resources>

## Decisions
Fixed: <exact public behavior, units, null rules, compatibility and edge cases>
Free: <necessary private choices only within eligible change rows; no adjacent cleanup>
Escalate: <specific unresolved or forbidden changes requiring Codex>
Existing-test edits authorized: <none, or exact approved measuring-standard change>
Change admission: <worker-visible authoritative table or per-change C-ID rows answering
Q1 requirement/AC; Q2 concrete blocker; Q3 smallest correct change; Q4 relevant API/config/
log/data/dependency/workflow/compatibility evidence; eligible/omit/blocked disposition>.
No independent change may proceed on a bare yes/no or missing contract assessment.
If contract preservation is uncertain, stop that edit; only an explicit user-authorized
revised requirement can permit a specific contract delta. Codex cannot waive this rule.

## Acceptance
- AC-1: <observable primary behavior>
- AC-2: <important negative/edge/compatibility behavior>

## Checks
- V-1 -> AC-1, AC-2: <command, cwd, setup and relevant expected observation>
- V-2 -> AC-2: <named inspection or additional focused test>
Keep failed/not-run evidence; do not weaken tests. Discover unknown native commands only
inside scope, and report the gap if no feasible check exists.

## Stop
Finish after bounded implementation, listed checks and self-review. On scope/meaning change,
baseline conflict, unavailable verification, or repeated non-progress, stop affected work
and return evidence plus the smallest decision needed. Do not commit/push/delegate.

## Return
Concise identity/candidate/status receipt and AC map; changed paths; actual commands, cwd,
exit/results and evidence; changed tests/dependencies; actual C-ID coverage and deviations; risks/blockers. Full report path:
<approved path, or inline-only>. Report in <language>. Never omit blockers for brevity.
