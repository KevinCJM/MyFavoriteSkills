# Choose a brief, not all briefs

When authoring or changing a brief, use [prompt protocol](../references/prompt-protocol.md)
and the needed template. Skip this index when dispatching an adequate prepared contract:

| Assignment | Template |
|---|---|
| Small bounded low-risk task worth delegating | [Compact](prompts/compact-brief.md) |
| Bounded repository investigation | [Scout](prompts/scout-brief.md) |
| Design proposal within an explicit decision boundary | [Designer](prompts/designer-brief.md) |
| Implementation and tests | [Builder](prompts/builder-brief.md) |
| Independent review | [Verifier](prompts/verifier-brief.md) |
| Same-contract correction | [Rework](prompts/rework-brief.md) |
| Answer a pending question | [Clarification](prompts/clarification.md) |
| File-based transport to a fresh worker | [Dispatch envelope](prompts/dispatch-envelope.md) |

Templates contain placeholders and are deliberately not sendable unchanged. Resolve them,
remove irrelevant instructions, and keep exact acceptance values in one authoritative brief.
For every proposed edit/design change use the [admission table](change-admission.md) or its
compact equivalent in the authoritative brief. Existing answers may be referenced, not
copied repeatedly; rework supplies only changed answers. Read-only work must not become
implementation. The common [worker rules](worker-rules.md) must reach a fresh worker too. Existing local
project rules still apply. Do not send this index or the full Skill package to every worker.
