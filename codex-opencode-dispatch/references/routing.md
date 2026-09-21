# Routing, cost, and delegated judgment

## Ownership is not the same as doing all the work

Apply the [four-question gate](change-admission.md) before choosing a route, including
direct edits. Codex owns requirement interpretation within the user's authority, not an
exception to it. A Builder may choose necessary private implementation details inside an
admitted change. It may not beautify neighbors, repay historical debt, or fix unrequested
bugs. Requiring Codex to prewrite every algorithm and line still defeats delegation.

A Scout gathers evidence; a Designer may propose bounded options. Codex resolves local
choices inside existing authority. Altering public behavior, security, business definitions,
persistence, compatibility, or scope beyond it requires an explicit user-authorized revised
requirement. A desirable architecture is not a reason to change the current one.
Do not escalate every local variable or private-method choice.

## Four independent assessments

**Judgment:** What unresolved decision could change the definition of correct?
**Execution:** How much expensive reading, editing, experimentation, or debugging remains?
**Risk:** What would a subtle defect affect, and how can we detect it?
**Coupling:** Can packages advance using stable interfaces and independently verifiable output?

Do not score every task with a long essay. Record one routing reason for a substantial
task. A single-line financial sign error can be high risk; a 100-file mechanical rename
can be low judgment. Long duration is not itself high semantic risk.

## Topology

After explicit opt-in, route proactively instead of waiting for the human to repeat the
Skill name. Honor explicit user choices to delegate or work directly. Otherwise compare
avoided Codex work with briefing, observation, review and likely repairs before dispatch.

`direct`: work whose execution and necessary checks cost less than delegation, or an
unavailable/incompatible Worker. This is not restricted to one-line edits. Record the
reason briefly. Running a known command does not itself require another LLM. An explicit
user instruction to delegate simple work still controls; optimize that dispatch instead.

`single`: give one Builder a complete coherent unit, including related code discovery,
implementation, necessary targeted tests, and fixes of task-related failures. Avoid a Scout → designer → coder →
tester pipeline for a routine task when a Builder can do all four.
For bounded low-risk work use the compact brief and one controller acceptance; no default
ledger, independent Reviewer or repeated environment discovery. Contract-sensitive work
still needs risk-appropriate review even when its diff is small.

`parallel`: independent components with frozen contracts, separate directories/resources,
and small integration cost. Parallelism is a latency choice, not guaranteed token saving.

`phased`: settle and implement shared foundations first; verify an accessible exact
revision; fan out only afterward. A dedicated Builder can implement the foundation under
Codex's design—Codex need not type it all. If committing the baseline is not authorized,
use a verified transferable snapshot or remain serial rather than silently committing.

## Worker roles

- Scout: answer named questions, return path/symbol evidence, uncertainties, and stop.
- Builder: own one implementation package; fix its ordinary failures before handoff.
- Reviewer: inspect an immutable implementation snapshot; return concrete findings and
  coverage/quality verdicts. Never quietly repair code during review.

These are role contracts, not three different model tiers. Use the fixed worker model.
A fresh Reviewer context reduces self-review coupling; it does not eliminate the fixed
model's shared blind spots. Codex must still examine high-risk reasoning directly.

## Cost guard

Delegate when expected avoided Codex work exceeds brief + observation + review + likely
correction/integration work. Opt-in permits useful delegation; it does not make uncertain
benefit a reason to delegate. Respect the user's chosen priority: Codex usage, combined
usage or elapsed time. These objectives can conflict and none waives correctness.

Good: one Builder fixes the explicitly requested validation cases and necessary checks.
Bad: Codex reads all those files, writes the exact patch, dispatches it, then rereads all.
Good: a Scout locates an unfamiliar call chain and returns exact entry/exit paths.
Bad: delegate one grep that Codex can run and interpret immediately.
Good: batch only admitted homogeneous edits with one manifest and completion checklist.
Bad: one worker for every one-line change, each repeating project setup.

## Bounds, not blind caps

Default one writer; two independent writers when it helps. Higher concurrency requires
known model/API capacity, memory/test-resource budget, and clear ownership. A failed
resource check serializes work; it does not authorize disabling gates.

Begin with one compact brief and at most one independent Reviewer for a high-risk or
broad package. Repeated unexplained stalls, an expanding diff or missing verifiability
trigger diagnosis. After two unsuccessful controller-requested implementation repairs
across the whole task, diagnose and record a narrower package, revised brief or takeover
decision before another repair. Different findings, job IDs and sessions do not reset the
counter. Initial implementation, local fixes before handoff and report-only repairs are
excluded. Consolidate known findings rather than repeatedly interrupting safe active work.
Keep the user's delegation/model choices, scope and correctness; do not recursively spawn
helpers. A checkpoint is not permission to accept unfinished work.

## Measuring improvement

Use the existing receipt/ledger, not a new monitor. Record the user's priority, elapsed
time, task-wide repair/infrastructure retry counts and next decision. Follow the
[progress checkpoint and retry rules](mcp-v3.md#choose-a-progress-checkpoint-not-a-kill-timer):
inspect actual progress when due, using existing evidence first. Waiting time alone does
not prove a stall; never cancel a healthy test solely because time elapsed.

When usage is exposed, record Codex and Worker separately: input, output, reasoning and
cache, using task-level deltas or correlated messages rather than lifetime session totals.
Normalize provider fields without double-counting cache already included in input or
reasoning already included in output. Different tokenizers are not directly equivalent.
Missing usage/limits remain `null`; no extra polling solely to fill a metric. Compact tasks
need only an inline receipt. Counts are not subscription charges; byte counts are proxies.
Compare matched workloads and quality gates, including post-acceptance defects. Static
policy checks cannot establish latency, quality or token improvements.
