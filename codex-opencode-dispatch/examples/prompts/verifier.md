Protocol: ocw/1
Kind: dispatch
Task: VR-07
Revision: 1
Attempt: 1
Role: verifier
Mode: full
Workspace: /srv/example-project/wt-config
Snapshot: git:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa; clean
Risk: high

## Goal
Independently assess WP-07 implementation against its approved contract.

## Inputs
Authoritative spec: /srv/example-project/artifacts/WP-07/brief-r1.md.
Candidate is the assigned fixture snapshot; baseline and complete diff manifest are in
/srv/example-project/artifacts/WP-07/review-package.md. Builder report is unverified claims.
No independently attested test result is currently supplied.

## Scope
Write: none
Read: approved brief, complete diff, changed tests and relevant loader/validator code.
Artifacts: inline-only
Do not run tests, edit product files, install dependencies or change Git state.

## Decisions
Fixed: separate spec coverage from quality; Codex makes final acceptance within the
user's boundary. Audit actual C-1/C-2 edits against Q1–Q4 and verify C-3 was omitted;
an allowed path and green test report do not justify unsolicited changes. Never require
historical debt, elegance-only refactoring, or unrelated baseline fixes as current rework.
Free: inspect nearby call sites for a named exception/type/compatibility risk.
Escalate: missing evidence or a mismatch between the packaged candidate and workspace.

## Acceptance
- AC-1: cover original WP-07 criteria with code evidence and explicit test-evidence gaps.
- AC-2: identify concrete test-integrity, bool/int, exception or compatibility defects.

## Checks
- V-1 -> AC-1, AC-2: inspect measuring-standard changes first and then risk-bearing code.
  Cite locations and consequences; do not claim passing tests without execution evidence.

## Stop
End once named coverage/risk questions are answered or explicit gaps remain.

## Return
Identity/candidate, spec verdict, quality verdict, located findings, unverified checks,
and smallest correction. No issue quota, fake approval, or praise-only confirmation.
