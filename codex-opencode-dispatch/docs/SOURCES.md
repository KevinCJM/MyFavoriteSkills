# Sources and attribution

Research checked on **2026-09-18**. Only primary project documentation/source files were
used for technical capability claims. Source branches may change. MCP compatibility was
checked against the **v3.0.0 tag**, not assumed from the current main branch. No live check
of the user's installation was performed.

This package is an original adaptation of workflow ideas. It does not vendor upstream
Skill prose or runtime scripts. The helper and templates were written for this package.
Upstream licenses remain with their respective projects; links here are attribution,
not an endorsement or a claim that this package is officially supported by them.

## Superpowers

- S1 — task orchestration / brief / ledger / repair flow:
  https://github.com/obra/superpowers/blob/main/skills/subagent-driven-development/SKILL.md
- S2 — unified task reviewer:
  https://github.com/obra/superpowers/blob/main/skills/subagent-driven-development/task-reviewer-prompt.md
- S3 — parallel task selection:
  https://github.com/obra/superpowers/blob/main/skills/dispatching-parallel-agents/SKILL.md
- S4 — worktree workflow:
  https://github.com/obra/superpowers/blob/main/skills/using-git-worktrees/SKILL.md
- S5 — evidence before completion:
  https://github.com/obra/superpowers/blob/main/skills/verification-before-completion/SKILL.md

## oubakiou/delegate-skills

- D1 — project and file-based context strategy:
  https://github.com/oubakiou/delegate-skills
- D2 — implementation role and cost gate:
  https://github.com/oubakiou/delegate-skills/blob/main/skills/delegate-implement/SKILL.md
- D3 — review role:
  https://github.com/oubakiou/delegate-skills/blob/main/skills/delegate-review/SKILL.md
- D4 — implementation architecture / protocol specification:
  https://github.com/oubakiou/delegate-skills/blob/main/docs/design/spec.md

## amElnagdy/delegate-skills

- A1 — OpenCode delegation instructions:
  https://github.com/amElnagdy/delegate-skills/blob/master/skills/opencode-delegate/SKILL.md
- A2 — test integrity and review:
  https://github.com/amElnagdy/delegate-skills/blob/master/skills/opencode-delegate/references/review-and-land.md
- A3 — actual CLI relay implementation:
  https://github.com/amElnagdy/delegate-skills/blob/master/skills/opencode-delegate/scripts/relay.mjs

## multi-agent-orchestrator-skill

- H1 — topology, shared foundations, supervision, and caveats:
  https://github.com/hyw007726/multi-agent-orchestrator-skill/blob/main/SKILL.md
- H2 — runtime structure and coordination workflow:
  https://github.com/hyw007726/multi-agent-orchestrator-skill

## delegate-to-deepseek-harness

- L1 — delegation / verification contract / stop rule:
  https://github.com/LomoMao/delegate-to-deepseek-harness/blob/master/SKILL.md
- L2 — deterministic verifier implementation examined for limitations:
  https://github.com/LomoMao/delegate-to-deepseek-harness/blob/master/scripts/verify_workspace.sh

## Actual MCP target

- M1 — generated v3.0.0 tool schemas:
  https://github.com/AlaeddineMessadi/opencode-mcp/blob/v3.0.0/docs/tools.md
- M2 — v3.0.0 environment and directory configuration:
  https://github.com/AlaeddineMessadi/opencode-mcp/blob/v3.0.0/docs/configuration.md
- M3 — v3.0.0 state, retention, cancellation, lifecycle:
  https://github.com/AlaeddineMessadi/opencode-mcp/blob/v3.0.0/docs/architecture.md
- M4 — ambiguous writes and read retry behavior in source:
  https://github.com/AlaeddineMessadi/opencode-mcp/blob/v3.0.0/src/client.ts
- M5 — v3.0.0 generated schemas showing optional `variant` on ask/reply/run/fire:
  https://raw.githubusercontent.com/AlaeddineMessadi/opencode-mcp/v3.0.0/docs/tools.md

## Git receipt hardening

- G1 — `git ls-files -v`: lowercase tags indicate assume-unchanged; `S` identifies
  skip-worktree entries. These index hints can make ordinary status/diff unsuitable as the
  sole working-tree observation, so the helper flags them for manual review:
  https://git-scm.com/docs/git-ls-files

## Official runtime documentation

- O1 — Codex skill format, discovery, references, invocation and metadata:
  https://developers.openai.com/codex/skills/
  (redirected during verification to https://learn.chatgpt.com/docs/build-skills)
- O2 — OpenCode permissions, agent overrides, external directories and tool boundaries:
  https://opencode.ai/docs/permissions/

Raw file endpoints were also read for the same paths. Upstream commit counts, stars,
model prices, release rankings and percentage savings were not used as evidence of
production maturity. The exact worker model ID must be verified on the user's server.


## v2.1 leader–worker prompt research (2026-09-18)

P1 — Orchestrator assignment requirements, complexity scaling, artifacts and tradeoffs:
https://www.anthropic.com/engineering/multi-agent-research-system

P2 — Minimal sufficient context, explicit sections, just-in-time references:
https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents

P3 — Agents-as-tools versus conversation handoffs; no SDK dependency is introduced:
https://openai.github.io/openai-agents-python/multi_agent/

P4 — MCP reusable prompt-template protocol, fixed version used for layer distinction:
https://modelcontextprotocol.io/specification/2025-06-18/server/prompts

P5 — Concrete implementation/review prompt templates and authoritative task briefs:
https://raw.githubusercontent.com/obra/superpowers/main/skills/subagent-driven-development/implementer-prompt.md
https://raw.githubusercontent.com/obra/superpowers/main/skills/subagent-driven-development/task-reviewer-prompt.md
https://raw.githubusercontent.com/obra/superpowers/main/skills/subagent-driven-development/SKILL.md

P6 — Context-efficient implementation delegation and request/response design:
https://raw.githubusercontent.com/oubakiou/delegate-skills/main/skills/delegate-implement/SKILL.md
https://raw.githubusercontent.com/oubakiou/delegate-skills/main/docs/design/spec.md

P7 — Reviewing tests before trusting gates and delta correction:
https://raw.githubusercontent.com/amElnagdy/delegate-skills/master/skills/opencode-delegate/references/review-and-land.md

P8 — Untrusted content, structured data flow, layered controls and limitations:
https://developers.openai.com/api/docs/guides/agent-builder-safety

P9 — Actual OpenCode runtime permissions, not skill-enforced scope:
https://opencode.ai/docs/permissions/

P10 — Installed-version target; schemas inspected at the v3.0.0 tag:
https://raw.githubusercontent.com/AlaeddineMessadi/opencode-mcp/v3.0.0/docs/tools.md
https://raw.githubusercontent.com/AlaeddineMessadi/opencode-mcp/v3.0.0/docs/configuration.md

P11 — Evaluating agent outcomes, traces and grading:
https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents

Additional context on isolated agent context and continuation (Claude-specific capabilities
were not copied into the OpenCode tool adapter):
https://code.claude.com/docs/en/sub-agents

Current Codex discovery/installation references were rechecked through:
https://developers.openai.com/codex/skills/
https://learn.chatgpt.com/docs/build-skills

Verification notes: source pages were inspected through web retrieval. Branch-based source
links can change; no immutable commit/hash is claimed for `main` or `master`. Bulk downloading
source copies in the local execution environment was unavailable, so no upstream byte hashes
are asserted. MCP paths are tag-qualified. No live user MCP/model invocation occurred.
