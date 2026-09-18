# Worker report — ocw/1

## Receipt (inline; normally about 12 lines, never hide blockers)
- Task / Revision / Attempt / Role: <exact submitted identity>
- Candidate / Workspace: <concrete observed snapshot, not a moving HEAD alias>
- Status: ready_for_review | needs_context | blocked | partial
- Result: <one-line outcome>
- Changed paths: <complete small list or accessible manifest>
- Checks: <actually passed / failed / not-run, with evidence reference>
- Blockers/concerns: <all blocking gaps; explicit none otherwise>
- Detailed report: <permitted shared path, or inline-only>

## Acceptance coverage
| AC ID | supported / unsupported / not_checked | Evidence type and location | Remaining gap |
|---|---|---|---|

Evidence types include source inspection, proposal analysis, observed execution, or
worker-reported execution. A structured assertion is not automatically an attestation.
Scouts/Designers report evidence/proposals, not invented implementation or tests.
Separate verified facts, conditional inference (state its assumptions), and unverified
behavior in each material conclusion. A static source check is not runtime evidence;
absence in a search is not proof of impossibility. Include uncovered requirements, not
only findings that appear supported. Prefer one concise conclusion plus path:line evidence.

## Verification detail
| Check ID | Actual command/method + cwd | Candidate/environment | Exit/result | Runner/log source |
|---|---|---|---|---|

Record checks never run, failed setup, no-tests-collected, baseline failures with evidence,
and nondeterminism. Do not substitute an intended command for an observed execution.
The same exit code can have different semantics; interpret actual output for the check.

## Scope and measuring standard
For full/governed work map edits to admitted C-IDs/ACs; for compact work map edits to the
Boundary/AC, including edits inside allowed files.
List new/deviating Q1–Q4 facts, rejected/unimplemented changes, and any unresolved contract
concern; reference unchanged original answers instead of duplicating the entire table.
List unexpected files, dependency/lockfile/config/log changes, test/fixture/tolerance/skip
changes, new files, renames, binary/submodule changes as relevant. Preserve user work.
Unrelated baseline findings belong in a separate observation, not an added implementation
scope or a new mandatory acceptance item. Do not create repository TODO/debt markers.

## Corrections / decisions
For rework map F IDs to fixes/evidence; do not repeat the old narrative. For escalation,
state the smallest required Codex decision with facts, options and consequences. Never
supply private reasoning traces. No worker may mark leader acceptance or integration.
