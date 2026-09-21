# AlaeddineMessadi opencode-mcp 3.0.0 adapter

Read once per changed environment. These are real tool base names; the host may prefix
its connector namespace. Live input/output schemas outrank this reference. Target version
is upstream 3.0.0. This Skill bundles the patched `3.0.0-codex.1` source; installation,
patch scope and provenance are in [README](../README.md). Do not claim another release
is compatible without checking its schema.
Source pointers: `docs/SOURCES.md` M1–M4.

## Preflight without repeated exploration

1. Inspect the connected catalog. Confirm the package identity/version from accessible
   configuration; a tool name alone cannot identify its publisher.
2. Use `opencode_setup(directory=SERVER_PATH)` if readiness is not already known.
   It has no documented `initialize` parameter: do not treat it as a create-project API.
3. Use `opencode_context(directory=SERVER_PATH)` only if paths, configuration, or agent
   capabilities are unknown. Sanitize anything persisted; never copy secrets.
4. Discover provider IDs, then call `opencode_provider_models(providerId=ID)` as needed.
   Discovery uses `providerId`; execution uses `providerID` and `modelID`. Preserve casing.
5. Record endpoint identity, directory mapping, worker agent, model source and ID pair.
   Recheck after reconnection, configuration changes, or a contradictory response.

`directory` is an absolute path on the OpenCode server, not necessarily on Codex's host.
Do not send `/Users/...` to a Linux server unless the mapping actually exists.

### Reuse a verified runtime profile

Keep endpoint/package/OpenCode versions, directory mapping, provider/model/variant, and
the effective agent permission profile in the existing task record; no separate registry
is needed. Reuse the established MCP connection and approved runtime configuration instead
of rebuilding a temporary server, client harness, or permission file for every task.
Before dispatch, confirm the connection and task directory still match; a new workspace
requires its own write/read scope. New independent tasks still get fresh sessions.

### Unattended execution, when authorized

Check two independent layers once per runtime profile:

- Codex: merge `default_tools_approval_mode = "approve"` into the existing
  `[mcp_servers.opencode]` section (or approve only required tools). A top-level
  `approval_policy = "never"` alone can reject a call requiring approval; it does not
  auto-approve MCP. Do not change the host sandbox or other servers.
- OpenCode: use a verified agent with necessary actions `allow` and out-of-scope actions
  `deny`, rather than `ask`. The optional [read-only agent](../templates/opencode-codex-reader.md)
  can be installed as `codex-reader.md` in OpenCode's `agents/` directory with authorization.
  Builders need their own explicit edit/test scope; do not turn this reader into a writer
  or allow unrestricted shell execution. Agent permissions are not an OS sandbox.

An unexpected pending request still needs inspection. Resolve it only within existing
authority; otherwise stop/report the affected work without widening permissions or looping
on requests. Unattended execution does not grant new authority or override managed policy.
Reconnection may be required before saved configuration becomes effective.
Configuration reference: https://developers.openai.com/zh-Hans/docs/extend/mcp and
https://opencode.ai/docs/permissions/ .

Rediscover only affected fields after reconnect, version/config/agent changes, model
unavailability, permission failure, or contradictory metadata. Do not re-run model probes
or enumerate all providers on every dispatch. Keep explicit generation bindings, including
an operator-selected variant, on repairs as well as initial calls.

A known installed server is not proof its tools are exposed in the current Codex
conversation. If the catalog is missing, report that connection problem; do not silently
substitute a CLI or repeatedly construct one-off clients. Never change global model defaults
or broaden a reused permission profile merely to make a task fit it.

## Model policy

The user's intended model label is DeepSeek V4.1 Flash; this is not an API identifier.
Resolve the exact provider/model pair from the user's installation. If the operator has also
selected a model `variant`/reasoning effort, resolve and record that value too. An unavailable
or mismatched binding blocks worker dispatch; never substitute a model/backend/variant silently.

The package supports `OPENCODE_DEFAULT_PROVIDER` and `OPENCODE_DEFAULT_MODEL` together.
Defaults are NOT an enforced allowlist. Choose a recorded policy:

- **Verified default:** omit per-call IDs only after confirming the defaults and agent
  behavior select the intended model. Reconfirm when environment changes.
- **Explicit binding:** pass the same resolved `providerID`/`modelID` on EVERY generation
  call, including a new task, repair, Scout, and Reviewer. If a variant is explicitly selected,
  pass the same `variant` on those calls as well. This is safer when defaults/agent overrides
  are opaque. It is not task-dependent model selection.

`opencode-mcp@3.0.0` exposes an optional `variant` field on `ask`, `reply`, `run`, and
`fire`. This proves transport support, not that a particular model accepts a named variant.
Do **not** assume `max` merely because the field exists. If `max` (or another value) is an
operator requirement, verify the installed provider/model exposes or correctly honors it,
then record/pass it consistently. Otherwise leave variant unset.

Where effective model/variant metadata is exposed, compare it with the binding. If it is not
exposed, record the corresponding value as unverified; do not advertise a hard lock. Hard
restrictions require runtime/provider controls. Also inspect agent overrides and auxiliary
model configuration: locking the principal worker does not prove no helper/title model
can ever be used internally. This Skill does not configure those controls.

## Operations

| Purpose | Tool and important fields |
|---|---|
| Short bounded execution | `opencode_run(prompt, directory, sessionId?, providerID?, modelID?, variant?, agent?, maxDurationSeconds?)` |
| Durable background execution | `opencode_fire(prompt, directory, sessionId?, providerID?, modelID?, variant?, agent?)` |
| Compact observation | `opencode_check(jobId, detailed=false, directory)` |
| Bounded wait | `opencode_wait(jobId, timeoutSeconds, directory)` |
| Recover one job | `opencode_job_get(jobId)` |
| Find saved jobs | `opencode_job_list` with only fields advertised in the live schema |
| Required input | `opencode_job_input(jobId, responses?)`; inspect its nested schema |
| Request stop | `opencode_job_cancel(jobId)` |
| Review navigation | `opencode_review_changes(sessionId, directory, messageID?)` |
| Short follow-up | `opencode_reply(sessionId, prompt, directory, providerID?, modelID?, variant?, agent?)` |

Do not invent `mode=readonly`, `worktree=true`, `task_id`, `max_workers`, or `model=`
parameters for these tools. Workspace management and our acceptance states are separate.
`messageID` in review is not `messageId` in async outputs/observation.

`run`/`fire` yield correlated job/session/message identifiers and structured state.
For repeated Builder cycles prefer `run`/`fire` with a healthy compatible session: each
new turn has a new job/message ID. Apply the [context rules](state-and-context.md) before
continuation or handoff. The original completed job must not be polled for its repair.
`reply` can continue the session, but its generic result is not the same durable-job
contract. Recover using the actual returned message/schema rather than inventing handles.

## Observation and recovery

Treat `isError`, structured state, and correlated messages together. Runtime states:
`accepted`, `running`, `input_required`, `completed`, `failed`, `cancelled`, `unknown`.
Runtime `accepted` means accepted for execution, NOT our final acceptance.

- `run.maxDurationSeconds` limits observation, not remote execution; its documented
  default is 600 seconds. `wait.timeoutSeconds` is also observational (default 120).
- Set `run.maxDurationSeconds` explicitly when observing immediately; use `fire` when
  returning handles before observation or doing independent work. A running `run` result
  continues via `wait`, never a new submit. Keep observations below the host deadline and
  at most 55 seconds for minute-level interactive updates. Prefer wait over check-then-wait.
  Do not assume a ten-minute MCP call survives every client/proxy.
- `unknown` or a lost submit response: recover jobs/session messages and inspect the
  workspace before another submit. There is no application exactly-once guarantee.
- Default local job retention is 24 hours from creation. Keep your own durable IDs and
  ledger. An expired handle neither proves cancellation nor destroys the remote session.
- No automatic task-status wake-up is promised here. Use compact checks/bounded waits;
  `pollIntervalMs` is the server's internal observation interval, not a cue to make the
  Codex model issue calls every two seconds.
- Job cancellation ultimately aborts a session. Never overlap task turns in one session.
  A cancellation acknowledgement is not proof that remote tools or child processes have
  stopped. Confirm quiescence before replacement, cleanup, or handing writing ownership elsewhere.
- An external `opencode serve` can outlive the MCP connection. A server child owned by
  `OPENCODE_AUTO_SERVE=true` is shut down with that MCP process. Neither arrangement
  supplies automatic model-execution checkpoint/restart.

### Follow the same job until it stops

Use the existing `wait`/`check`/job tools; no separate monitor or new submission is needed.
Retain `jobId`, `sessionId`, `messageId` and directory throughout observation. A wait
returning `running` means another observation of that job, not another implementation turn.

| Observed state | Controller action |
| --- | --- |
| `accepted` / `running` | Continue bounded waits on the same job. Give concise progress updates; do not cancel, resubmit or declare completion because an observation window ended. |
| `input_required` | Inspect the actual question/permission and resolve only within existing authority; otherwise request the missing user input. Do not silently wait forever or retry through another job. |
| `unknown`, disconnect or missing handle | Reconcile saved identity with session messages, server/tool liveness and workspace state. Do not assume the writer stopped. |
| `completed` | Retrieve the correlated result and verify it; completion is not acceptance. |
| `failed` / `cancelled` | Inspect the cause and partial changes; confirm no active writer, then apply the retry rules below. A user cancellation is not permission to restart. |

Keep each wait within host/update deadlines; a sequence of waits can cover a task lasting
many minutes. No fresh output during a wait is not a stall.

### Choose a progress checkpoint, not a kill timer

Before dispatch, choose the next diagnostic checkpoint from the expected phase or known
tool/test duration. Without useful timing evidence, start with five minutes; this is an
adjustable diagnostic default, not a measured optimum or execution deadline. Keep the next
check and last meaningful progress in the existing receipt; no extra ledger is required.

At that point, inspect only the active tool/test, recent relevant events or a bounded log
tail. Inspect earlier for explicit errors, pending input or resource trouble. Prefer evidence
already returned by waits; do not fetch transcripts or query every process on each timeout.
Record the active phase, evidence and next check. A new completed step, tool transition or
test milestone is progress; repeated status/heartbeat timestamps or a live PID alone are not.
Do not keep postponing diagnosis on those signals alone.

For a healthy quiet test, continue the same job and set the next check using its expected
duration. With uncertain progress, perform a bounded targeted diagnosis; insufficient
telemetry is not proof of failure. If observation cannot be restored, report the blocker and
retain ownership rather than inventing progress or starting a second writer. A diagnosed
stall follows the cancellation rules below; elapsed time alone never authorizes cancellation.

Do not end the user turn with a required job still running unless the user explicitly asks
to pause, stop or leave it in the background, or observation is genuinely blocked. In that
case report the last known state, handles and remaining work without claiming completion
or promising an automatic wake-up. Preserve the single-writer boundary when state is unknown.

### Cancel only for a concrete reason

Valid grounds are a user stop/revocation or incompatible redirection, an observed
scope/permission/safety/data-loss violation, a diagnosed blocked operation that cannot
continue without stopping, or an explicit hard user/resource limit. A wait timeout, slow
execution, quiet logs, a context-review threshold or an ordinary review finding is not enough.
Queue ordinary findings until handoff; let safe edits/tests finish before session rotation.

Before cancellation, record one short reason with the user instruction or observed evidence
and the next action in the existing receipt/ledger. Use the real cancellation tool, then
verify session/tool/process quiescence and reconcile partial changes. If stop cannot be
confirmed, keep ownership unresolved and do not start another writer. No new logging service
or permission question is required for an already-authorized stop.

### Classify failures before retrying

An observation timeout/disconnect is not a failed execution. Recover the same job first;
an unknown submission outcome must be reconciled before any new submit. Retrying a read-only
status query is not resubmitting work. Do not count healthy waits as retries.

- **Transient infrastructure failure:** after confirming the old turn and its tools have
  stopped (or submission never occurred), reconcile partial effects before resubmitting.
  Retry only when safe to resume without duplicating effects. Default to at most two
  automatic infrastructure resubmissions across the task, in addition to its initial submit;
  honor a stricter user budget. Respect any server retry-after and increase delays between
  retries, keeping individual waits within host/update deadlines.
- **Deterministic input/configuration error:** correct the diagnosed cause within authority
  before continuing; no unchanged retry. Permission denials follow the separate stop rule.
  Code/test defects use the implementation-repair process, not an infrastructure retry.
- **Budget exhausted or cause unresolved:** stop automatic resubmission, preserve results and
  diagnose. Proceed only after an evidenced recovery change within authority or necessary
  user input; record why another attempt is justified. New IDs or labels do not reset the
  task counter. A progress checkpoint does not replenish it.

Record count/cause, any recovery change and next action in the existing receipt; retain them
through session changes and compaction. This budget bounds controller resubmissions, not
hidden retries inside providers/tools; do not claim to control those through this Skill.

### Permission denial is an infrastructure stop

For an explicit denial, use the Worker rule: one sanitized error, no equivalent-path or
alternate-tool retries. Inspect the effective rule and the exact tool-request path before
fixing configuration; do not assume absolute and workspace-relative patterns match equally.
Keep any authorized fix confined to the intended scope, and do not bypass a rejection from
the operator or approval system. If additional authority is needed, ask for it.

Confirm the old turn is quiescent and the configuration/input actually changed before
continuing the same compatible session with a small correction and new job/message IDs.
Otherwise report the blocker; repeatedly re-submitting the same task will not repair
permissions. Infrastructure retries do not consume or justify the two implementation-repair
attempts. A genuine `input_required` permission request instead follows the existing
authorized pending-input flow; it is not automatically a hard denial.

## Lower catalog overhead

`OPENCODE_TOOL_PROFILE=essential` advertises the smaller workflow catalog. It is a useful
operator setting for this Skill, not a security mechanism. Do not change the user's
config automatically. Full profile remains valid; discover only the tools you need.

The bundled `mcp/opencode-mcp` build (`3.0.0-codex.1`) optionally supports
`OPENCODE_COMPACT_RESULTS=true` in the MCP server environment. This is NOT an upstream
3.0.0 capability. For `run/fire/wait/check`, read the complete report from
`structuredContent.text`; the text content block is only a receipt. IDs, state, pending
inputs, errors and message metadata remain available. Only transport text already present
in the report is omitted from result parts; structured business data is retained.
`opencode_job_get` remains the full-result recovery path, not a routine extra call.
Leave the setting off for text-only clients; the default response contract is unchanged.
Native MCP Tasks results are not compacted; the opt-in covers ordinary tool calls only.
The bundle also filters transport `reasoning` parts from message/job responses and session
message resources. It does not scrub arbitrary business JSON, tool output, events, or
OpenCode history. Existing globally installed npm packages do not gain these patches until
the operator explicitly switches the MCP command to the bundled build.
Keep compact Markdown reports and path:line evidence; do not replace full conclusions
with arbitrary output truncation. Load only matching routing fields, not entire module trees.

`opencode_ask` is a model-generation tool, not a read-only filesystem operation. A Scout
requires a verified restricted OpenCode agent or an isolated reviewable workspace.
`opencode_conversation` is for targeted recovery/diagnostics, not routine handoff.
`format` JSON-schema output may require OpenCode StructuredOutput permission; compact
Markdown is the default to avoid an unnecessary permission/dependency surface.


## Prompt-contract transport (v2.1)

`ocw/1` metadata and sections belong INSIDE the `prompt` string of `opencode_run/fire`.
They do not add `task`, `context`, `prompt_file`, `readOnly`, `scope`, `budget`, `max_tokens`,
or `idempotency_key` parameters. In the v3.0.0 published `opencode_fire` input schema,
`system` is not a field; do not forward `opencode_ask`'s optional override there.

Keep roles (`scout/designer/builder/verifier`) distinct from actual OpenCode agent names.
Select only an installed agent with verified permissions, or omit the agent field while
retaining the task role policy and an appropriate execution boundary. Do not assume “plan”
means all required forms of runtime read-only isolation.

A short clarification for a pending question belongs in the matching pending-input API.
A rework delta is a new correlated run/fire turn after the previous one stops. A contract
revision change requires reconciliation, not an untracked mid-write steering message.

A full contract can be inline, or a prompt can instruct OpenCode to read a copied file.
The MCP does not upload Codex-local files automatically. The offline renderer produces
text only, and cannot enforce model binding, scopes, prompt permissions or deadline caps.
