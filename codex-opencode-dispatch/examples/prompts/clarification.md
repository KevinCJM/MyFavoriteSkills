Protocol: ocw/1
Kind: clarification
Task: WP-07
Revision: 1
Attempt: 1
Role: builder
Mode: full
Workspace: /srv/example-project/wt-config
Snapshot: git:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa; clean
Risk: medium

## Question
Q-1: Does bool count as int for timeout_ms in this contract?

## Answer
No. AC-2 explicitly requires ValueError for True. Keep valid built-in positive ints unchanged.
This answer resolves wording only; it grants no additional edits or permissions.

## Authority
Original WP-07 revision 1 and its assigned scope remain unchanged. Q1–Q4 still apply;
this answer grants no contract change or unrelated repair. Resolve the specific
pending-input request using the runtime API, not a concurrent new work turn.

## Return
Continue the authorized original task after input resolution and include any further blocker.
