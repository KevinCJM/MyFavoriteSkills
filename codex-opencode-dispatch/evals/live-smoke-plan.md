# Live closed-loop smoke plan

This is the next validation priority. It is **not executed by packaging tests** and may consume
model tokens. Run it only in the user's real Codex + opencode-mcp@3.0.0 + OpenCode environment.
Use a disposable branch/worktree and a small representative repository fixture or approved task.

## Metrics for every scenario

Record separately:

- Codex input/output/cached tokens if exposed;
- Worker tokens if exposed;
- elapsed wall-clock time;
- number of MCP calls;
- rework rounds;
- files changed;
- false-positive scope findings;
- missed defects found after acceptance;
- final accepted / rejected / blocked state.

Do not infer token savings when measurements are unavailable.

## Scenario 1 — one Builder fixes a bounded defect

Purpose:
- exercise compact dispatch;
- fixed model/optional variant binding;
- one OpenCode session;
- pre/post workspace receipts;
- targeted acceptance without a second Reviewer.

Success criteria:
- Worker changes only required scope;
- pre-existing dirty user changes are not attributed to Worker;
- targeted check passes on current candidate;
- Codex stops after the verification contract is satisfied;
- no full conversation retrieval is needed.

## Scenario 2 — two parallel read-only Scouts

Purpose:
- test parallel sessions without write races;
- compare context cost versus Codex doing two broad repository investigations itself.

Give the Scouts disjoint questions, for example:
- Scout A traces the call path;
- Scout B locates regression tests/compatibility consumers.

Success criteria:
- no product-file modification;
- answers cite concrete paths/symbols;
- Codex merges facts without rereading the whole repository;
- no session/workspace cross-talk.

## Scenario 3 — Builder then independent Verifier

Purpose:
- exercise a medium/high-risk full contract;
- Builder session implements and self-checks;
- fresh Verifier session reviews immutable candidate;
- Codex performs final acceptance.

Success criteria:
- Verifier receives specification/candidate, not Builder persuasion as authority;
- test-integrity changes are checked before green results are trusted;
- style/debt observations do not become unauthorized rework;
- concrete findings use narrow rework on the Builder session;
- acceptance stops after evidence is sufficient.

## Interpretation

Run each scenario more than once before making policy conclusions. Compare against a matched
Codex-only baseline with the same correctness gates. A faster/cheaper run that skips required
verification is not an improvement.
