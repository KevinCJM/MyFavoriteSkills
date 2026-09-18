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

`direct`: a trivial known edit, one lookup, or a known build/test command. Running a
command does not itself require another LLM. Codex may launch the authorized command
with logs redirected and inspect its summary rather than paying a Worker to press Enter.

`single`: give one Builder a complete coherent unit, including related code discovery,
implementation, necessary targeted tests, and fixes of task-related failures. Avoid a Scout → designer → coder →
tester pipeline for a routine task when a Builder can do all four.

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

Delegate only when expected avoided Codex work exceeds brief + observation + review +
likely correction/integration work. This is a planning heuristic, not measured accounting.

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
broad package. Repeated unexplained stalls, two failed repairs of the same issue, an
expanding diff, or missing verifiability trigger Codex diagnosis. Split/rebrief/take over;
do not lower requirements, recursively spawn helpers, or switch the model.

## Measuring improvement

Track per comparable task: measured Codex input/output/cached tokens when available,
worker tokens separately, model/effort, elapsed time, correction rounds, and post-acceptance
defects. Use `null` for missing measurements. File byte counts and tool-output sizes are
context proxies, not token counts or dollar savings. Compare matched workloads with the
same quality gates; do not optimize a percentage by skipping difficult tests.
