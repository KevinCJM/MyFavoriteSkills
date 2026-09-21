# Evidence-based acceptance with a stopping rule

## Define correctness before implementation

Give each requirement an ID and an observable check or review question. Record numerical
conventions, backwards compatibility, permitted test changes, allowed files, and prohibited
behavior. Verification commands come from the repository, not invented framework guesses.
Require the relevant behavioral test, not merely a build or lint pass.

## Review change necessity and contracts first

Use the [four-question gate](change-admission.md). For governed/full work use the brief's
C-ID answers; for compact work use its Boundary statement and AC. Map every independent
actual change to a genuine current requirement and blocker, smallest correct intervention,
and relevant contract assessment. Allowed paths alone are insufficient.
Unjustified edits block acceptance even if tests pass. Remove only this task's extra work,
not pre-existing user modifications. Final integration is subject to the same gate.

## Review the measuring standard first

Inspect edits to existing assertions, snapshots, golden data, tolerances, skips/xfails,
fixtures, test discovery, coverage thresholds, CI commands, and dependencies. Authorized
behavior changes may require legitimate test updates; each must match the new requirement.
An unexplained relaxed assertion or deleted test blocks acceptance. Pre-existing skips
are baseline facts, not newly introduced defects, but may leave relevant evidence missing.

For a bug regression, prefer a non-destructive red/green demonstration against baseline
and candidate snapshots when practical. Never roll back the user's active work to create
that demonstration. Performance tasks require the same representative workload/environment,
correctness comparison, and agreed timing/memory method; no fabricated benchmark gain.

## Scope and immutable identity

Record the task's actual base, not `HEAD~1`. Account for every deliverable:

- changes committed after base;
- staged and unstaged changes;
- new untracked files, including tests;
- both sides of renames/moves, deletions, executable modes, symlinks and binaries;
- submodule Git links AND internal uncommitted changes when relevant;
- generated output and build/configuration changes.

Git status alone misses already-committed work. Plain `git diff` misses staged/new files.
A session diff may help navigation but does not prove full coverage. Use safe Git tooling
or the optional [workspace receipt helper](../scripts/workspace_receipt.py). For a dirty
pre-existing workspace, capture a receipt before dispatch and use `scope-delta` against the
post-work receipt; do not judge Worker scope from the base-wide receipt alone. The helper
flags submodules/conflicts and Git assume-unchanged/skip-worktree hints; those hints require
manual inspection because ordinary status/diff may hide content changes. It is intentionally
not a universal repository auditor or actor-attribution mechanism.

Freeze mutation while testing/reviewing a snapshot. Record base/HEAD plus dirty-content
fingerprint when not fully committed. Record the exact check command, cwd, exit status,
relevant output/artifact, execution provenance, and environment/fixtures/lockfile identity.
If source or the measuring standard changes afterward, invalidate affected receipts.
Ignored files, external services/data, time and nondeterminism may affect checks even when
a Git fingerprint is unchanged. Explicitly record relevant dependencies; do not call a
repository hash a proof of whole-system identity.

## Evidence provenance

1. A result from Codex's authorized shell/CI runner, observed at the exact candidate state,
   can satisfy a check without Codex itself doing the implementation.
2. A trusted harness tool-execution record can be reused if it identifies that state,
   command, exit status and output, and the trust assumptions are acceptable.
3. A Builder-authored Markdown/JSON/log file is a claim until corroborated. Its presence
   or a self-computed hash is not a trusted execution attestation.

Missing or untrusted evidence → run the check through a trusted path. Matching trusted
CI evidence need not be rerun merely to change the speaker. Label worker-reported evidence
as such; never turn it into “I verified” without observing a sufficient basis.
Reuse the observed command result, not just a completion summary. Track relevant source,
test and environment dependencies so an unrelated edit does not invalidate every check.
An affected dependency invalidates its checks; unknown impact requires investigation or
rerunning the necessary checks. User/project-required final runs remain mandatory.

## Review depth

Delegate the investigation before doing the same broad source reads yourself. Read only
enough up front to define scope and checks; while it runs, wait or handle independent work.
After handoff, compare coverage against the original request, then inspect risk-bearing
source, failure paths and actual assertions. Do not only confirm the Worker's selected
findings: look for missing requirements and overbroad claims. An identified risk may justify
deeper reading; token savings never waive necessary verification.

Group evidence locations by file and merge overlapping read ranges before fetching. Batch
independent reads within the response budget; retrieve only missing ranges after truncation.
This is a read strategy, not a cap: inspect surrounding branches and uncovered acceptance
stages even if the Worker did not flag them. Do not reread a complete unchanged result.

**Low:** examine scope and relevant diff, test-integrity changes, and targeted evidence.
No independent Reviewer by default. One-line financial/API/security changes are not Low.

**Medium:** above plus critical control flow, compatibility and error paths. Codex must
independently observe the required checks, through its own run or trusted execution records.
Use a Reviewer only when the avoided wide reading exceeds coordination overhead.

**High:** Codex directly checks all risk-bearing logic and requirement invariants. Use
appropriate property/oracle/edge/regression/integration tests and one fresh Reviewer when
it adds coverage. Same-model independent context is supplementary, not mathematical proof.
User-required full regression remains mandatory regardless of the Skill's defaults.

## One review, two verdicts

A Reviewer checks specification coverage and code quality in one scoped pass. Findings
must give a location, requirement or risk, observed behavior, consequence, and evidence.
Mandatory corrections must concern a current unmet requirement, this task's introduced
defect/unauthorized extra edit, relevant contract violation, or necessary verification gap.
Historical debt, stylistic preference and unrelated baseline bugs are not current rework
orders. Report a serious unrelated hazard separately and pause hazardous execution as
needed, without granting repair authority. A numeric severity label alone is not evidence.

Do not prime the Reviewer with “the Builder passed; approve it.” Inspect implementation
against requirements first; Builder rationale may then help explain, not excuse, changes.
Read outside the diff only for a named call-path, compatibility or semantic risk. Broaden
inspection only to resolve a concrete relevant risk; discovering one does not authorize
scope expansion, contract changes, or open-ended cleanup.

## Repair and re-review

Collect concrete current-task defects into one correction request. Specify affected
requirement IDs, checks and the correction's Q1–Q4 delta. A review cannot redefine the
user's requirement or make a new contract change mandatory. Resume a healthy compatible
Builder session; use context handoff only after confirmed release of the old writer.
Count unsuccessful controller-requested implementation repair rounds across the whole
task, including different defects and sessions. After two, diagnose the combined cause
and record a narrower package, changed brief or takeover decision before further repair.
Initial implementation, local pre-handoff fixes and report-only corrections do not count.
Preserve user delegation choices. Do not reset the counter by renaming the task or session,
blindly continue the same loop, or accept defects because the checkpoint was reached.
Do not interrupt safe active edits for each newly noticed issue; send consolidated findings
after handoff unless an actual scope, safety or data-loss risk requires stopping sooner.

Review new changes against the last reviewed snapshot; also revisit impacted invariants
and tests. Do not rerun an entire suite twice on identical trusted inputs by habit. A
cross-cutting fix can legitimately invalidate broad evidence; record why.

## Acceptance stop condition

All of these must hold: requirement coverage established; actual changes pass Q1–Q4 and
relevant contracts are preserved (or follow an explicit user-authorized revised boundary);
allowed scope respected; tests not improperly weakened; current trustworthy evidence
available; no unresolved
blocking finding or correctness uncertainty; integration checks passed when applicable.

Then stop. Do not add nice-to-have refactoring, reread unrelated code, or initiate another
review wave without a new concrete risk. Nonblocking observations may be recorded outside
this task. A failed/missing required check, unverified critical claim, exhausted budget,
or disconnected server yields `blocked`/`rework_required`, never unconditional acceptance.

A known baseline failure can be reported separately only with evidence that it predates
and is unaffected by this task. Do not label all failures “pre-existing” or claim the full
suite is green. User authorization is needed to waive an explicitly required gate.
