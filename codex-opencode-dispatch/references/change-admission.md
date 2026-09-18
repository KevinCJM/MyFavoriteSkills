# Four-question change admission

The user's programming policy applies before deciding who does the work. It governs
Codex's own edits, Designer proposals, Builder implementation, Verifier findings, rework,
and multi-worker integration. It is not merely a style guide for workers.

**Do not edit solely to make code shorter/elegant, repay historical technical debt, or
fix an unsolicited suspected bug.** Generic quality, reuse, or autonomy guidance is
subordinate to this task-specific boundary, subject to higher-priority runtime/safety
instructions. On an instruction conflict, stop the affected work and report it; do not
claim the Skill overrides the host's instruction hierarchy.

## The four questions

| Gate | Required answer for each independent change | Failure action |
|---|---|---|
| Q1 — Is this part of the current requirement? | Link a user-authorized requirement/AC and the concrete behavior or deliverable it needs. | Not linked: omit. |
| Q2 — Would leaving it unchanged block the requirement? | Name the unmet outcome or necessary verification and a concrete reason. | No actual blocker: omit. |
| Q3 — Can the change be minimal? | Give the smallest correct intervention and its affected paths/callers; reject broader alternatives when material. | Narrow the design before proceeding. |
| Q4 — Are existing contracts preserved? | Identify relevant contracts, unchanged guarantees, and supporting source/check evidence. | Uncertain or conflicting: block the affected change. |

Use `eligible`, `omit`, or `blocked` as planning dispositions, not as safety proofs or
acceptance states. A bare yes/no is insufficient. Do not invent ACs after the fact to
justify an unrelated change. A Worker can supply factual/local-design answers, but cannot
approve its own scope expansion. Codex does not have authority to waive the user's rule.

## Granularity and timing

For full/governed tasks, record one row per independently justified behavioral change, verification addition,
configuration adjustment, or necessary implementation step. Do not create one row per
line. Homogeneous edits may share a row only when their requirement, reason, contract
assessment and path manifest are genuinely the same. A whole-feature “all four pass”
without change-level reasons is not enough.

Use the [admission template](../templates/change-admission.md) inside the authoritative
design/brief, or link one worker-visible version. Full briefs put it in `Decisions`.
Compact briefs use one concise `Boundary:` statement in `Scope`, with no C-ID table or
ledger required. Rework puts only the affected Boundary/AC delta or full-task rows
in `Correction`. Tiny direct work needs the same reasoning but not a new artifact or
Worker call. Never turn this into a compulsory extra acknowledgement exchange.

Before a substantial Builder is dispatched, Codex specifies the admitted work and known
contract boundaries. The Builder may choose the smallest private implementation inside
that boundary and refine its row before editing. Unknown method choices do not require
Codex to prewrite code; unknown scope/contract authority requires escalation. A Designer
may investigate whether a proposal passes, but cannot implement while its gate is blocked.

## Q1 and Q2: necessity, not convenience

Valid examples:
- The specified bug still violates the agreed AC unless the named branch is corrected.
- A requested new feature cannot exist without the proposed local implementation.
- The required regression/resource-release behavior cannot be verified without a focused
  test. Test additions are work too; tie them to a concrete required observation.
- This task introduced an extra side effect or unnecessary code; remove only this task's
  contribution to restore the authorized behavior/minimal patch.

Not blockers:
- “It will be easier to maintain later.”
- “This function is ugly / duplicated / old.”
- “We already touched the file, so we may as well clean it.”
- “The full suite has a failure elsewhere, so fix it too.”
- “The reviewer prefers an abstraction.”

A newly discovered necessary prerequisite must still satisfy Q1 and Q4. If it is outside
the authorized requirement/paths, report the actual obstacle and the smallest decision
needed; do not silently add it to scope. Preserve unrelated baseline failures with evidence.
A required gate that cannot pass remains blocked unless the user changes that requirement;
it does not license an unrelated repair or a false green-suite claim.

## Q3: smallest correct impact, not fewest lines

Consider behavior, callers, shared abstractions, data/resource side effects, and rollback.
Two lines in a shared helper can be broader than a contained five-line fix. Conversely,
do not add a local workaround that hides the symptom while leaving the current requirement
incorrect. Reuse an existing abstraction only if it reduces the necessary intervention
without changing unrelated consumers; do not create a general framework for future uses.

Do not format, rename, reorder imports, upgrade dependencies, alter lockfiles, move files,
regenerate unrelated output, adjust logs, or modify error messages without the same gate.
Use targeted tooling. If mandatory project tooling produces unavoidable broad changes,
report the conflict instead of silently committing its output or disabling the gate.
Incidental reformatting of a genuinely changed expression needs no separate line-by-line
ceremony, but whole-file cleanup is not part of that expression.

## Q4: relevant contract inventory

| Area | Preserve or explicitly surface |
|---|---|
| API / CLI | signatures, parameter rules, return shape, status/error types, CLI flags and exit behavior |
| Configuration | names, defaults, units, precedence, discovery paths, environment-variable behavior |
| Logs / observability | levels, fields, format, conditions, ordering/frequency when consumed, downstream parsers |
| Data | schema, types, ordering, null/NaN, units, rounding/tolerances, serialization and persistence |
| Dependencies | caller assumptions, exports, lockfiles, generated interfaces, side effects, resource lifecycle |
| User workflow / compatibility | operation sequence, defaults, old consumers/data/configs, migrations and recovery |

Inspect only relevant surfaces, not the entire system for every edit. `Not affected`
requires a bounded reason, such as isolated code path/caller evidence; green tests alone
are not proof. Record remaining uncertainty honestly and resolve it before the affected
edit, or report a blocker. A prompt, report, or Git fingerprint is not a compatibility proof.

**Existing contracts must not change.** Only the user can explicitly revise the current
requirement and authorize the specific contract delta. Record that decision/source in a
new brief revision before resuming affected work; preserve every other contract. A generic
“make it work”, task-plan approval, write permission, Codex decision, or review request is
not a blanket exception. Do not repeatedly ask about a delta the user has already clearly
authorized; record the existing instruction accurately instead.

A documented requested repair that restores an existing contract is not automatically a
contract change. Establish the expected behavior from the actual requirement/spec/tests/
consumers; do not relabel an inconvenient existing behavior as a bug by intuition.

## Baseline findings, introduced defects, and reporting

| Observation | Required handling |
|---|---|
| Requested bug with evidence | Implement only the admitted fix and checks. |
| Defect/extra work introduced by this task | Correct or remove this task's contribution, preserving user work. |
| Existing issue proven to block the current requirement | Stop the affected path; determine whether an in-scope contract-preserving fix exists, otherwise report for user decision. |
| Existing unrelated issue or debt | Do not fix; mention only concrete material observations, separately from current acceptance. |
| Suspected unrelated bug | Label unverified; do not investigate broadly or modify automatically. |
| Serious unrelated security/data-loss hazard | Report facts and, where needed, pause hazardous execution; do not silently repair it or accept unsafe output. |

Do not create debt markers, comments, tickets, or persistent TODOs without authorization;
recording an observation is not permission to edit the repository. Do not remove user
changes or run destructive Git cleanup to make the final diff look minimal.

## Review and rework gate

For each changed behavior/hunk group, map it to an eligible C-ID/AC for governed work or
to the compact task's Boundary/AC. A path allowlist is only a boundary, not a justification
for every edit inside it. Check contract impact,
then test integrity and correctness. Passing tests do not excuse unauthorized changes.

A mandatory rework finding must identify at least one of:
- a current requirement not met;
- a defect or unauthorized extra change introduced by this task;
- a violation of an existing contract relevant to this candidate;
- a missing/invalid necessary verification of the current task.

No elegance-only, historical-debt, or unrelated-baseline-bug finding may mandate rework.
A severity label is not evidence. If a baseline contract problem is unrelated to the task,
report it separately rather than turning it into an implementation order. Stop hazardous
execution when necessary; do not hide a real risk for the sake of a green verdict.

For a correction, keep the same contract, state the failure and smallest correction, and
update only the affected Boundary/AC delta or full-task C rows. A requirement/contract change needs the user's explicit
revision first. Reviewer wording cannot silently expand Worker authority. Removing this
task's own extra edits must be safe and must not revert the user's baseline contributions.

## Multi-worker and acceptance

Maintain one authoritative overall boundary. Governed packages link C-IDs to that boundary;
compact packages link their Boundary/AC. Workers cannot each add a small “cleanup” and
collectively create a broad refactor.
Shared files/interfaces have one owner. Integration/conflict resolution is itself subject
to all four questions; combined compatibility must be checked after combining candidates.

Accept only if actual modifications are justified, required evidence is current, relevant
contracts are preserved (or a specific user-authorized revision is fulfilled), and no
current blocking defect/uncertainty remains. Then stop. Historical polish is not another
acceptance phase, and budget exhaustion cannot waive a gate.

## Automation boundary

`prompt_contract.py` still checks **ocw/1 structure**, not whether Q1–Q4 are true or even
fully answered; the format remains compatible. `workspace_receipt.py` checks path/snapshot
facts, not change necessity. Neither can return semantic admission or contract approval.
These rules guide Codex/Workers and require evidence-based review; they are not an MCP
interceptor, runtime permission system, or guaranteed model-behavior enforcement.
