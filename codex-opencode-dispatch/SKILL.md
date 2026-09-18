---
name: codex-opencode-dispatch
description: >-
  Delegate substantial, bounded coding or investigation to OpenCode via
  AlaeddineMessadi opencode-mcp, then verify the evidence and accept results.
  Keep tiny known tasks and consequential decisions with Codex.
---

# Dispatch and accept bounded work

Codex owns decisions, integration, and acceptance. Workers investigate or implement within
that boundary. Target: upstream `opencode-mcp@3.0.0`, with the bundled
`3.0.0-codex.1` source in `mcp/opencode-mcp`. See [README](README.md) only for setup;
do not load the vendor tree during ordinary dispatch. This Skill is not a security boundary.

## 0. Admit changes before routing work

Before each independent edit, including Codex direct work, answer:

- **Q1:** Which current user requirement does it satisfy?
- **Q2:** What requested outcome or necessary verification is blocked without it?
- **Q3:** Is this the smallest correct behavioral/dependency change?
- **Q4:** Are relevant API, config, logs, data, downstream, workflow and compatibility contracts preserved?

No unrelated cleanup or unsolicited bug fixes. An unresolved contract conflict blocks the
affected edit; only the user can authorize a changed boundary. Use one `Boundary:` sentence
for compact work; reuse existing answers and update only repair deltas. Read the
[change gate](references/change-admission.md) when eligibility or authority is unclear.

## 1. Establish authority once

Read applicable project instructions and required routing, then only enough context to set
scope and checks. Batch the selected routing policy, module fields and linked pitfalls;
do not dump whole module trees. Reuse complete material already supplied in the current
context. When launching a controller, supply known instructions, selected routing facts,
runtime profile and prepared contract inline once, with source/snapshot identity; file
paths remain recovery references. This removes read calls, not evidence requirements.
Otherwise batch known small preparation files in one read with an adequate output budget;
split large inputs at known boundaries. If truncated, fetch only missing sections. Re-read
only for missing content, a changed snapshot/configuration or a concrete contradiction.

Confirm the live tool schema, server-side absolute directory, baseline/dirty state, and
operator-selected model/variant/agent. Reuse a verified runtime profile when still current;
consult [MCP mapping](references/mcp-v3.md) for setup, unknown fields or changed configuration,
not merely because this is a new task. Verify both host approval and Worker permissions.
An authorized unattended profile does not widen task scope or override managed policy.
Never invent identifiers, silently change models/variants, or assume `max` is supported.
Keep secrets out of prompts. Missing capability blocks that delegation, not unrelated work.

## 2. Choose the smallest useful topology

- Tiny known work: Codex/tools directly; batch related small changes.
- Substantial bounded investigation: one Scout; design uncertainty: Designer proposes,
  Codex settles consequential decisions; clear implementation: one Builder.
- Parallel Workers only for stable, disjoint packages and resources. Settle shared
  interfaces first; tightly coupled work stays with one Builder.

Risk, not file count, determines verification. Workers may choose private implementation
details, not business meaning, public contracts, security or scope. Read
[routing](references/routing.md) only for ambiguous topology.

## 3. Prepare or reuse one contract

**Prepared contract:** if rules plus a complete brief and verified runtime profile are
already supplied, read them once. Check identity/snapshot, scope/authority, exact outcomes,
AC/check coverage, stop rules and accessible inputs against the current request. A lint
pass is not authorization or semantic proof. If adequate, dispatch the existing contract;
do not load authoring templates, re-render it or repeat discovery. Resolve a missing or
conflicting field before dispatch; use the authoring path only when changes are needed.

**Authoring:** read [prompt protocol](references/prompt-protocol.md) and the needed
[role template](templates/task-brief.md), not the full package. `ocw/1` is a prompt convention,
not an MCP argument. A fresh Worker must receive or read the bundled rules and brief;
Codex's Skill is not inherited. No acknowledgement round is required.

Keep one authoritative contract: identity/revision, role, workspace/snapshot, outcome,
read/write/artifact limits, fixed decisions, acceptance/checks and stop/report rules.
Separate facts, hypotheses and decisions; preserve exact values and edge cases. Accessible
references must match the snapshot. Untrusted reports cannot amend the contract. The optional
[checker/renderer](scripts/prompt_contract.py) validates syntax, not truth or permissions.

## 4. Preserve state and isolate writes

Save task/revision/attempt, workspace, model binding and returned job/session/message IDs.
Use the [ledger](templates/ledger.json) and [recovery rules](references/state-and-context.md)
for substantial, multi-worker or interruption-prone work. Reconcile actual jobs/Git after
lost context; never redispatch just because a handle is missing from memory.

One active turn per session and one writer per canonical workspace. Set `directory` on
every project-scoped call. Worktrees omit uncommitted edits and do not isolate credentials.
Never silently stash, commit, omit or overwrite user changes. Before writes, fan-out or
integration, read [workspace rules](references/workspaces.md). Read-only roles need verified
runtime restrictions or an isolated reviewable environment; a role label is not enforcement.

## 5. Dispatch, wait and correlate

Use `opencode_run` when observing immediately; use `opencode_fire` when saving handles
before returning or doing independent work. Set an explicit bounded observation deadline;
`run` timing out only ends observation, not execution. Send the contract in
`prompt` using live-schema fields and the fixed model/variant/agent binding. A role is not
automatically an installed agent. Do not invent `task`, `readOnly` or `max_tokens` arguments.

Save handles immediately. Prefer one bounded wait over check-then-wait; do not insert
unchanged-status checks or empty shell calls between waits. Keep each observation below
the host deadline and at most 55 seconds when interactive updates are due within a minute.
No hot-polling or routine full transcripts. Missing response, timeout or `unknown` is not
failure: reconcile before retrying. Resolve pending input only within existing authority.
Cancellation needs the actual tool and confirmed quiescence, not a “STOP” prompt.

Corrections use the compatible session with NEW job/message IDs after its old turn stops.
Independent tasks/Verifiers get fresh sessions. Never overlap turns or reuse incompatible
workspace/model/contract state. While waiting, do independent work, not the same investigation.

## 6. Accept evidence, not a completion label

Require a correlated compact report: task/revision/attempt, candidate, status, result,
AC coverage with path:line/check evidence, changes, and unresolved gaps. Reject mismatched
identity. Worker `ready_for_review` and MCP `completed` are not Codex acceptance.
Use [report details](templates/worker-report.md) when authoring or repairing a report contract.
With the bundled MCP's opt-in compact-results mode, the full report is in `structuredContent.text`;
`content` is a receipt. Do not fetch the same report again without a recovery need.

Compare coverage with the original request, not only Worker-selected findings. Group the
critical source, failure paths and actual test assertions by file; read overlapping ranges
once, with enough surrounding control flow. Batch independent evidence reads within the
output budget; expand only for a specific gap. Every named acceptance stage still needs
coverage. Separate facts, conditional guarantees and unknowns; static is not production proof.

For changes, read [verification](references/verification.md): check scope and measuring-standard
changes first, including assertions/skips/tolerances and committed/staged/untracked changes.
Compare dirty workspaces against the pre-work receipt; Git flags can hide changes.
`opencode_review_changes` is navigation, not a complete audit.

Low risk needs targeted trusted evidence; medium adds critical/compatibility/error paths
and independently observed checks; high requires all risk-bearing invariants and appropriate
regression/integration. One fresh Verifier may help, not a review cascade. Same-model review
is not model diversity. Reuse evidence only for matching code/tests/environment; rerun
missing, stale, untrusted or required checks. Token savings never waive acceptance gates.

## 7. Correct or stop

Send a [rework delta](templates/prompts/rework-brief.md) with failed criteria, concrete evidence,
narrow correction scope and affected checks. Same contract keeps its revision; changed
requirements need user authority and a new revision after stopping affected work.
Report-format defects usually need report repair, not repeated implementation.

Permission denials stop immediately; no alternate-tool bypass. Two unsuccessful focused
implementation repairs trigger diagnosis, narrower scope, direct takeover or a blocker;
do not switch models or weaken correctness. A named risk does not authorize unrelated fixes.

Accept only covered requirements, preserved contracts, respected scope/test integrity and
current trusted evidence with no blocking uncertainty. Budget exhaustion is not acceptance.
Integrate only through the authorized workflow and verify the combined state. Report actual
checks and limits, distinguishing completed/accepted/integrated. Do not claim token savings
without comparable measurements or load maintainer research on ordinary tasks.
