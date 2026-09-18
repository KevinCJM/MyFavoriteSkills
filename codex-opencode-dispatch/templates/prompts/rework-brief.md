Protocol: ocw/1
Kind: rework
Task: <task-id>
Revision: <positive-integer>
Attempt: <positive-integer>
Role: builder
Mode: full
Workspace: <absolute-OpenCode-server-path>
Snapshot: <concrete-base-and-dirty-state-or-snapshot-id>
Risk: medium

## Parent
<authoritative brief location and revision; same Task/Role/Workspace, current candidate>
Previous attempt: <prior attempt>. Previous turn is confirmed terminal before submitting.

## Failures
- F-1 -> AC-1: <observed discrepancy, exact evidence/location, expected behavior>

## Correction
Fix only <narrow issue>. Do not restart the entire task. A report-only issue requires no
code edits. For a governed parent, reference its C-ID/F-ID; for a compact parent, reference
the affected AC/F-ID and its Boundary. Reconfirm only the correction delta: current
requirement, still-blocked outcome, smallest correct repair, and preserved contracts/evidence.
Reuse unchanged original answers; add only this delta. Reviewer preference is not
permission to beautify, repay old debt, or fix unrelated bugs. If the original authority
is insufficient, return a blocker; do not expand it or silently revise an exception/API.

## Preserve
<exact numerical/API/security invariants and already-accepted behavior>
No other contract fields or scope are changed. Do not weaken checks or remove the failure.

## Checks
- V-1 -> AC-1: <affected targeted command/inspection and expected corrected observation>

## Return
Identity/revision/new attempt/candidate; resolved and unresolved F IDs; changed delta;
actual checks/evidence; blockers. No repeated history. Original acceptance remains binding.
