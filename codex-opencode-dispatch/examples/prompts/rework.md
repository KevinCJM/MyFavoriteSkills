Protocol: ocw/1
Kind: rework
Task: WP-07
Revision: 1
Attempt: 2
Role: builder
Mode: full
Workspace: /srv/example-project/wt-config
Snapshot: git:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa; dirty:sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
Risk: medium

## Parent
WP-07 revision 1 at /srv/example-project/artifacts/WP-07/brief-r1.md.
The previous attempt has stopped. The candidate is now the assigned dirty snapshot.

## Failures
- F-1 -> AC-2: the observed targeted test accepts True. The original contract requires
  ValueError for bool. Evidence: fixture check V-1, case test_bool_rejected, recorded exit 1.

## Correction
Fix only the bool rejection and its direct negative-case coverage in the original owned paths.
Do not restart the implementation or change the public exception type.
Admission delta C-1/C-2 for F-1: Q1 original AC-2; Q2 True still violates the current
requirement; Q3 fix local bool rejection plus the focused assertion only; Q4 retain the
original ValueError, positive-int behavior and loader/config/log/data/workflow contracts,
checked against the parent brief and targeted diff. Reuse other unchanged gate answers.
Disposition: eligible only if those preservation checks hold; otherwise report blocked.
A preference for refactoring the full config module is not part of this correction.

## Preserve
Original revision 1 remains authoritative: built-in positive ints are unchanged, bool/float/
string/zero/negative values raise ValueError, and the public loader signature is unchanged.

## Checks
- V-1 -> AC-1, AC-2: rerun the targeted timeout tests in the assigned fixture environment;
  retain actual collection/exit/output and candidate identity. No weaker assertion or skip.

## Return
New attempt/candidate, F-1 resolution, changed delta, actual checks and any remaining blocker.
Do not repeat the entire first report or claim acceptance.
