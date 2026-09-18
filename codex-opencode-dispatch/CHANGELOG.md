# Changelog

## Explicit human invocation — 2026-09-18

- Disable implicit invocation; require a human to explicitly request `codex-opencode-dispatch` for the task before delegating to OpenCode, including direct MCP/CLI/API or indirect delegation.
- Distinguish Skill discussion/maintenance from Worker authorization, and keep authorization within the named task and its in-scope follow-ups.
- Align offline metadata checks and add invocation-gate evaluation scenarios. No live Worker run or MCP runtime/approval change is included.

## MCP source bundle — 2026-09-18

- Vendored upstream v3.0.0 at commit `6f1f62fd6c151377e09f4fe95bed58eb48c6196b` under `mcp/opencode-mcp`, with MIT license and `mcp/UPSTREAM.json` provenance. No nested Git repository or submodule is required.
- Ported the previously local compiled-output patches to maintained TypeScript: message reasoning filtering and opt-in compact ordinary run/fire/wait/check results. Bundled MCP version is `3.0.0-codex.1`; Skill version and `ocw/1` protocol remain unchanged.
- Added 36 MCP regressions and two fixture-backed stdio modes. Baseline: 503 passed / 3 skipped; patched: 539 passed / 3 skipped. No new model run or token-saving benchmark was performed.
- Documented explicit source build, Codex registration, compatibility limits and update/rollback procedures. Existing global MCP/configuration is not modified by this package.
- Scoped Skill structure checks to owned files, with one new regression: 105 offline Skill tests passed. Vendor build, tests and tool-documentation checks run separately.

## 2.3.0 — 2026-09-18

- Hardened Git evidence: detect `assume-unchanged` / `skip-worktree` entries and require manual review instead of treating hidden changes as complete evidence.
- Added pre/post `scope-delta` receipts so pre-existing user changes are not misattributed to a Worker; preserved single-writer requirements because the delta is a time-window check, not actor attribution.
- Added optional worker `variant` binding for opencode-mcp@3.0.0, with explicit verification state; did not hard-code `max` without an operator-selected policy and verified provider/model support.
- Simplified compact work: one `Boundary:` sentence covers the four-question gate; no C-ID table or ledger is required for ordinary low-risk one-shot work. Full C-ID/AC/V/F traceability remains for governed, parallel, contract-sensitive, high-risk, and rework-heavy tasks.
- Added an explicit three-scenario live smoke plan (single Builder, parallel read-only Scouts, Builder + independent Verifier) and made real end-to-end validation the next priority rather than adding more orchestration rules.
- Preserved core controls: one writer per workspace, same-session rework, fresh-session independent review, no blind redispatch after timeout/unknown submission, and Codex final acceptance.
- Offline suite: 104 tests passed. No claim of live Codex/OpenCode/DeepSeek behavior or measured token savings.

## 2.2.0 — 2026-09-18

- Integrated the user's four-question change-admission policy across direct Codex work,
  Designer/Builder/Verifier roles, narrow rework, multi-worker coordination and integration.
- Required change-level necessity, smallest-correct-impact and existing-contract evidence;
  prohibited elegance-only changes, historical-debt cleanup and unsolicited suspected fixes.
- Restricted local autonomy and mandatory review findings; file access is not blanket
  authorization and Codex cannot waive the user's scope/contract boundary.
- Distinguished introduced defects, necessary current blockers, unrelated baseline findings
  and serious hazards without authorizing extra repairs or hiding risks.
- Added a concise admission table, optional manually merged resident-rule snippet, examples,
  policy-wiring regression checks and explicitly unexecuted Agent-behavior cases.
- Preserved MCP target, model policy, ocw/1 syntax, ledger schema and all three existing
  runtime/helper scripts byte-for-byte; no new infrastructure or false semantic checker.
- No live user-environment installation, enforcement guarantee or token-saving claim.

## 2.1.0 — 2026-09-18

- Added original ocw/1 prompt-content protocol: layered worker rules, compact/full role
  contracts, explicit authority/facts/hypotheses, criterion-to-check mapping and stop rules.
- Added Scout, Designer, Builder, Verifier, rework, clarification and file-dispatch templates.
- Added role/contract/attempt/candidate correlation and explicit contract-amendment behavior.
- Added offline prompt lint/render with no MCP calls, no command execution, no overwrite.
- Added resolved fictional examples and behavioral-evaluation scenarios; retained v2 Git
  receipt helper, permission boundaries, evidence integrity, state recovery and integration.
- Rechecked v3.0.0 MCP prompt transport: no invented API fields or automatic read-only role.
- Kept the core Skill below its 1500-word maintenance budget; detailed material loads on demand.
- No user environment installation, live model validation or token-saving percentage claimed.




## 2.0.0 — 2026-09-18

### Policy
- Separate decision ownership from implementation labor; allow bounded local worker design.
- Route direct, single, parallel, and phased work; batch homogeneous micro-edits.
- Keep the fixed worker model across all roles; no implicit model/CLI fallback.
- Combine requirement coverage and quality review in one pass by default.
- Add test-integrity checks, snapshot-bound evidence, delta review and a strict stop rule.
- Keep task execution, Codex acceptance and target integration as separate states.
- Recover from a durable ledger without duplicate execution; disallow recursive delegation.

### MCP 3.0.0 corrections
- Treat run/wait deadlines as observation limits, not execution cancellation.
- Prefer durable run/fire with the same session for substantive rework and new turn IDs.
- Handle unknown submission, expired job handles and session-wide cancellation carefully.
- Do not assume wake-up notifications or checkpoint recovery.
- Use exact field casing; do not infer read-only capability from opencode_ask.
- Treat model defaults as defaults, not a hard lock; support explicit fixed ID pairs.
- Document the essential catalog and externally managed versus MCP-owned server lifecycle.

### Workspaces and evidence
- Preserve uncommitted user changes; do not assume worktrees include them.
- Freeze shared foundations and isolate mutable test resources, not only source files.
- Review actual committed/staged/unstaged/new files instead of trusting a session summary.
- Provide an optional read-only Git scope/identity helper, unit tests and behavioral eval cases.

### Packaging
- Compact the core; use on-demand references and separate maintainer research.
- Add migration instructions and prevent accidental duplicate old-skill installation.
- No new MCP, daemon, automatic updater, blanket permissions, or model routing runtime.
