# Context, records, and recovery

## Keep storage small and explicit

Simple one-shot work: inline brief and receipt are enough. Heavy, multi-worker, or
interruption-prone work: create one task-run directory and a controller-owned ledger.
Do not make a generic task database or background supervisor for this Skill.

Prefer an existing approved ignored artifact area. Controller records can be outside the
repository. Worker-visible briefs must be in an accessible permitted path on the server;
place a scoped copy inside its workspace when external reads are forbidden. Never assume
Codex-local `/tmp` is OpenCode-local `/tmp`.

Suggested logical files (not automatic MCP endpoints):

```
run-<unique-id>/
  ledger.json             # Codex alone writes
  tasks/<task-id>/brief.md
  tasks/<task-id>/report.md
  tasks/<task-id>/review.md
  tasks/<task-id>/checks/  # bounded stdout/stderr and metadata
```

Use [ledger template](../templates/ledger.json). Resolve template fields; this file is a
recovery record, not a scheduler or authorization service.

## Store facts, not transcripts

Record repository/server identities, task and attempt IDs, canonical worker directory,
base revision, contract revision, model/variant binding, file/resource ownership, dependencies,
returned session/job/message IDs, final snapshot, and acceptance evidence pointers.
Record concise decisions, open blockers, integration target/state, and deferred nonblocking
observations. Do not store secrets or full chat histories.

Context package: objective + constraints + read-first file paths + relevant interfaces.
Unfamiliar projects benefit from a cached [project profile](../templates/project-profile.md).
Invalidate relevant profile entries after branch/configuration/lockfile/toolchain changes;
do not repeat whole-repo exploration merely because a new Worker starts.

Large report → read header/status/findings first, then selected evidence. A file index does
not save the tokens already spent printing the file; avoid printing it before indexing.
Never trim away failures, limitations, numerical constraints, or exact acceptance values.

## Two state dimensions

Execution mirrors the MCP: `accepted/running/input_required/completed/failed/cancelled/unknown`.
Acceptance is Codex-owned: `not_reviewed/rework_required/blocked/accepted/rejected`.
Integration is separate: `not_integrated/integrated/not_applicable`.

A Builder may return `ready_for_review`, `needs_context`, or `blocked` in its own report;
these are not new MCP statuses. Keep task identity separate from job and session identity.

## Transition discipline

Before submit, record an attempt as `submission_pending` with task ID, directory and
contract revision. After the call, save exact returned handles. No result after submit
means outcome unknown, not safe-to-retry. Use the pending record to reconcile.

For a repair, wait until the previous turn is terminal; reuse the session but record a
NEW job/message ID and retain previous evidence. New independent tasks and Reviewer
roles use fresh sessions. A session accidentally working in another directory must not
be silently continued.

Before replacing a stuck Worker: inspect pending input, server/job liveness, tool/test
progress and resources; classify the blocker. Request stop only when needed and confirm
no active writer remains. Then record the replacement attempt and its accessible context.
Elapsed waiting alone is not proof the model is stuck.

## Recovery after context compaction or reconnect

1. Read the run's ledger and unaccepted tasks, not other runs' logs.
2. Reconcile job state and actual Git/snapshot identity. File records can be stale.
3. If completed, retrieve the correlated result and verify evidence. Do not reimplement.
4. If running, resume observation. If input-required, resolve only the specific request.
5. If the job handle expired, use saved session/message/workspace identity and the actual
   catalog for recovery. Do not resubmit because the local record is gone.
6. If ownership/liveness cannot be established, mark blocked and preserve artifacts.

Accepted tasks are not dispatched again unless their contract/evidence became invalid.
Changes to shared interfaces invalidate downstream assumptions; reopen only affected
packages, document the reason, and stop conflicting writers before updating snapshots.

A Markdown/JSON ownership record coordinates cooperating agents; it is not an atomic
cross-process lock. Other humans/Codex sessions must honor the same reservation mechanism
or use separate workspaces. This Skill cannot enforce a global lease by writing a file.


## Prompt identity additions (v2.1)

Store `prompt_protocol: ocw/1`, brief revision/reference and optional content hash per task;
record each attempt separately from its runtime handles. Rework preserves the contract
revision; a changed definition requires the user's explicit authorization and a higher
revision. Link the authoritative full-work C-ID/Q1–Q4 table, or the compact Boundary/AC, from the
existing brief reference; do not copy a second set of requirement definitions into the
ledger. After correction,
new evidence belongs to the new candidate and attempt, not silently to the old receipt.

Do not duplicate the same numerical/interface specification across ledger prose, dispatch,
and report templates. The ledger points to the authoritative brief. A copied server-side
brief must be kept aligned with that revision. Worker reports never update controller-owned
authority or ledger state automatically; validate identity and interpret evidence first.
