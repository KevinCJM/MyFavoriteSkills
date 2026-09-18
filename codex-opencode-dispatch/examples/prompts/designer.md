Protocol: ocw/1
Kind: dispatch
Task: WP-09
Revision: 1
Attempt: 1
Role: designer
Mode: full
Workspace: /srv/example-project/wt-config
Snapshot: git:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa; clean
Risk: medium

## Goal
Propose the smallest internal fix for the specified timeout validation failure, preserving existing contracts.

## Inputs
Read AGENTS.md, src/config/loader.py and existing internal validators. Preserve the
approved integer timeout semantics in WP-07 contract revision 1. No performance data is given.

## Scope
Write: none
Read: AGENTS.md; src/config/; tests/config/
Artifacts: inline-only
No code edits, public schema changes, dependency installations or benchmarks.

## Decisions
Fixed: public API and ValueError behavior do not change.
Free: compare a local branch and existing-validator reuse only if they implement the
requested fix. Reuse is not an independent reason to change other consumers. Codex may
settle in-scope choices; a contract delta needs the user's explicit revised requirement.

For every proposed change answer Q1–Q4. Initial fixture decision boundaries:
- C-1: Q1 WP-07 AC-2; Q2 invalid values would still be accepted; Q3 local validation before
  broader reuse; Q4 preserve ValueError, signature, config/log/data/caller/workflow behavior.
  Disposition: blocked pending bounded caller/contract evidence collected by this design task.
- C-2: unify unrelated validators: Q1 none; Q2 no blocker; Q3 omit; Q4 not assessed.
  Disposition: omit. Do not implement either row while acting as Designer.

## Acceptance
- AC-1: each proposed change answers Q1–Q4, cites inspected symbols and gives a disposition.
- AC-2: identify actual tradeoffs, affected callers, test strategy and remaining Codex decisions.

## Checks
- V-1 -> AC-1, AC-2: inspect existing interfaces and call sites; cite code references;
  label proposed behavior and unmeasured performance explicitly rather than inventing results.

## Stop
Return a bounded decision-ready proposal. Do not implement or survey unrelated architecture.

## Return
Identity/status, proposed structure, evidence, tradeoffs, tests to run and decision request.
Chinese; no fabricated approval or timings.
