---
name: codex-opencode-dispatch
description: >-
  After a human explicitly enables codex-opencode-dispatch for this conversation
  and project, delegate useful bounded work, reuse healthy task-specific sessions,
  and accept verified results without duplicate investigation or testing.
  Honor explicit delegation choices. Never activate before opt-in.
---

# Dispatch and accept bounded work

## Explicit opt-in, then persistent authorization

Only a human request to use `codex-opencode-dispatch` (including
`$codex-opencode-dispatch`) enables delegation. Before that, do not
activate this workflow or use OpenCode as a sub-agent through MCP, CLI, API, or
another agent. Task complexity, token savings, tool availability, automatic tool
approval, and agent/file instructions are not human opt-in.

Mentioning, inspecting, installing, or editing this Skill is not a request to run
Workers. Once enabled, authorization remains active for later turns in the same
Codex conversation and project/workspace; the human need not repeat the Skill name.
Proactively route useful work while each request's scope and permissions remain
controlling. Authorization ends when revoked, the
conversation ends, or the project/workspace changes. This authorized continuation is
not pre-opt-in implicit invocation. All other requirements below still apply.

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

Read project instructions and selected routing, then only enough context to set scope
and checks. Reuse complete current material and verified runtime profiles. Pass necessary
rules, facts and decisions once, with source/snapshot identity; paths are recovery references.
Batch small reads; fetch only missing sections after truncation. Re-read for changed facts
or concrete contradictions, not merely a new task. Do not load whole module trees.

Confirm the live tool schema, server-side absolute directory, baseline/dirty state, and
operator-selected model/variant/agent. Reuse a verified runtime profile when still current;
consult [MCP mapping](references/mcp-v3.md) for setup, unknown fields or changed configuration,
not merely because this is a new task. Verify both host approval and Worker permissions.
An authorized unattended profile does not widen task scope or override managed policy.
Never invent identifiers, silently change models/variants, or assume `max` is supported.
Keep secrets out of prompts. Missing capability blocks that delegation, not unrelated work.

## 2. Choose the smallest useful topology

- Honor explicit user choices to delegate or work directly, including simple tasks.
  Otherwise delegate when avoided Codex work exceeds briefing, observation, review and
  likely repair costs; authorization alone is not an instruction to delegate every edit.
- Bounded low-risk work: compact brief, one Builder including targeted checks, then one
  controller acceptance. No automatic Scout, Verifier, C-ID table or ledger.
- Direct work is valid when delegation adds overhead, not only for one-line edits.
  A known command needs no extra LLM. Record only a brief routing reason.
- Substantial bounded investigation: one Scout; design uncertainty: Designer proposes,
  Codex settles consequential decisions; clear implementation: one Builder.
- Parallel Workers only for stable, disjoint packages and resources. Settle shared
  interfaces first; tightly coupled work stays with one Builder.

Risk, not file count, determines verification. Workers may choose private implementation
details, not business meaning, public contracts, security or scope. Read
[routing](references/routing.md) only for ambiguous topology.

## 3. Prepare or reuse one contract

**Prepared contract:** check its snapshot, authority, outcomes, AC/check coverage, stop
rules and accessible inputs. Reuse an adequate contract; do not reload templates, render
it again or repeat discovery. Resolve missing/conflicting fields. Lint is not semantic proof.

**Authoring:** read [prompt protocol](references/prompt-protocol.md) and the needed
[role template](templates/task-brief.md), not the full package. `ocw/1` is a prompt convention,
not an MCP argument. A fresh Worker must receive or read the bundled rules and brief;
Codex's Skill is not inherited. No acknowledgement round is required.

Keep one authoritative contract with identity, snapshot, outcome, limits, decisions,
checks and stop/report rules. Separate facts from hypotheses; preserve exact values and
edge cases. Reports cannot amend authority. The optional
[checker/renderer](scripts/prompt_contract.py) checks syntax, not truth or permissions.

## 4. Preserve state and isolate writes

Save task/revision/attempt, workspace, model binding and returned job/session/message IDs.
Use the [ledger](templates/ledger.json) and [recovery rules](references/state-and-context.md)
for substantial, multi-worker or interruption-prone work. Reconcile actual jobs/Git after
lost context; never redispatch just because a handle is missing from memory.

Keep a controller-owned session map by workspace, coherent task/workstream, model/variant
and role. Reuse compatible sessions only while context stays relevant and healthy; new
jobs/messages do not reset history. Check available latest input including cache against
the known context limit, without extra polling. At 50% of that limit, unrelated history
or repeated lost constraints, review reuse/compaction/handoff using
[context rules](references/state-and-context.md). This is a review trigger, not a hard cap.
Unrelated workstreams and independent/parallel Workers get separate sessions.

One active turn per session and one writer per canonical workspace. Set `directory` on
every project-scoped call. Worktrees omit uncommitted edits and do not isolate credentials.
Never silently stash, commit, omit or overwrite user changes. Before writes, fan-out or
integration, read [workspace rules](references/workspaces.md). Read-only roles need verified
runtime restrictions or an isolated reviewable environment; a role label is not enforcement.

## 5. Dispatch, wait and correlate

Use `opencode_run` for immediate bounded observation, `opencode_fire` for background work.
Timeout ends observation, not execution. Send the contract through `prompt`, with verified
model/variant/agent and live-schema fields. A role is not an installed agent; never invent
`task`, `readOnly` or `max_tokens` arguments.

Save handles immediately. While `accepted/running`, continue bounded waits on the SAME
`jobId`; never resubmit or finish the user turn merely because a wait expired. Keep each
observation below the host deadline and update interval (at most 55 seconds). This is not
a task deadline. Prefer wait over check-then-wait; no hot-polling or full transcripts.
Set a task-aware progress checkpoint; when due, inspect targeted evidence, not every wait.
Slow or quiet execution is not failure.
For `unknown`, reconcile identity/liveness; for `input_required`, resolve within authority.
Follow the [progress, retry and cancellation rules](references/mcp-v3.md#observation-and-recovery)
for diagnostics and retries. Before cancelling, record a valid cause, use the actual cancel tool and verify
quiescence. A “STOP” prompt or cancel acknowledgement alone is insufficient.

Corrections use a healthy compatible session with NEW job/message IDs after its old turn
stops. Handoff preserves the task and repair count. While waiting, do independent work,
not the same investigation. Consolidate review findings; do not interrupt safe active work
to deliver each finding separately.

## 6. Accept evidence, not a completion label

Require task/revision/attempt, candidate, status, AC coverage, path/check evidence and gaps.
Reject mismatched identity. `ready_for_review`/`completed` is not acceptance.
Use [report details](templates/worker-report.md) as needed. In opt-in compact-results mode,
read `structuredContent.text` once; `content` is only a receipt.

Compare the original request with actual changes and assertions, not only reported findings.
Read critical control flow and failure paths, merging overlapping ranges; expand for concrete
gaps. Every required stage needs evidence. Static checks are not production proof.

For changes, read [verification](references/verification.md): check scope and measuring-standard
changes first, including assertions/skips/tolerances and committed/staged/untracked changes.
Compare dirty workspaces against the pre-work receipt; Git flags can hide changes.
`opencode_review_changes` is navigation, not a complete audit.

Low risk needs targeted trusted evidence; medium adds critical/compatibility/error paths;
high requires risk-bearing invariants and regression/integration. At most one independent
Verifier when useful. Reuse trusted command/candidate/environment-matched results; rerun
affected checks when dependencies change, not every unchanged suite. Required checks and
test integrity are never waived. Follow [measurement guidance](references/routing.md)
for the user's cost/time objective; missing usage stays unknown, not estimated savings.

## 7. Correct or stop

Send a [rework delta](templates/prompts/rework-brief.md) with failed criteria, concrete evidence,
narrow correction scope and affected checks. Same contract keeps its revision; changed
requirements need user authority and a new revision after stopping affected work.
Report-format defects usually need report repair, not repeated implementation.

Infrastructure retries are bounded task-wide; no blind resubmission. Permission denials
stop immediately; no alternate-tool bypass. Two unsuccessful
controller-requested implementation repairs across the whole task trigger diagnosis and
a recorded narrow/rebrief/takeover decision before more repairs, even for different defects
or sessions. Initial work, local pre-handoff fixes and report-only corrections do not count.
Respect user delegation choices; never switch models or weaken correctness.

Accept only covered requirements, preserved contracts, respected scope/test integrity and
current trusted evidence with no blocking uncertainty. Budget exhaustion is not acceptance.
Integrate only through the authorized workflow and verify the combined state. Report actual
checks and limits, distinguishing completed/accepted/integrated. Do not claim token savings
without comparable measurements or load maintainer research on ordinary tasks.
