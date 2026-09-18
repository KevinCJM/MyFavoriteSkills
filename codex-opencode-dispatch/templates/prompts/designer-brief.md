Protocol: ocw/1
Kind: dispatch
Task: <task-id>
Revision: <positive-integer>
Attempt: <positive-integer>
Role: designer
Mode: full
Workspace: <absolute-OpenCode-server-path>
Snapshot: <concrete-base-and-dirty-state-or-snapshot-id>
Risk: medium

## Goal
Propose <bounded internal design> for Codex to decide; do not implement it.

## Inputs
Read first: <approved requirements/project rules/current interfaces>
Facts and assumptions: <separate, with references>
Dependencies: <fixed external contracts and versions>

## Scope
Write: none
Read: <relevant permitted files>
Artifacts: <proposal-only path, or inline-only>
Do not modify code/schema/configuration, install dependencies or change public semantics.

## Decisions
Fixed: <public API/business behavior, constraints and compatibility>
Free: propose only necessary local implementation within the requested outcome; no broad redesign.
Codex decision required: <in-scope tradeoffs; identify user decision needed for any contract delta>
For EACH independent proposed change, supply a C-ID and answer Q1 current requirement/AC,
Q2 blocker if unchanged, Q3 smallest correct intervention, Q4 relevant contracts and
preservation evidence/unknowns; conclude eligible, omit, or blocked. No beauty/debt/extra
bug-fix rationale. Use the admission table from the supplied design convention; do not
restate answers already available at an authoritative worker-visible path.

## Acceptance
- AC-1: proposal satisfies <binding outcome> and reuses justified existing mechanisms.
- AC-2: each change answers Q1–Q4 with bounded impact, evidence, disposition and feasible checks.

## Checks
- V-1 -> AC-1, AC-2: map proposal to concrete code locations/contracts; explain tradeoffs
  only where real alternatives exist. Distinguish inspected facts from proposed behavior.

## Stop
Once a decision-ready bounded proposal exists, report it. Do not write a comprehensive
system redesign or perform implementation “to validate” without authorization.

## Return
Identity/status, proposed design, evidence, meaningful alternatives/tradeoffs, test plan,
and explicit decisions for Codex. Report in <language>; no invented benchmarks or approval.
