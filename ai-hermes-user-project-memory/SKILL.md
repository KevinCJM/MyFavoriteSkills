---
name: ai-hermes-user-project-memory
description: Always available project-local skill for AI Hermes user project memory. Use when the user asks to remember, forget, enable, disable, view, audit, or apply personal preferences or repo-local private configuration; when running Python/tests/deploy commands that may use remembered local runtime preferences; and when long conversations suggest a safe preference candidate. Recall, learning, and auto-learning are enabled by default, with safety limits on what can be learned automatically.
---

# AI Hermes User Project Memory

## Default Availability

This skill is active by default as agent guidance in this project. That means agents must know the memory workflow exists and must route explicit memory requests here.

This means recall, learning, and auto-learning are enabled by default after installation. The persisted switches default to:

- `recall=true`
- `learn=true`
- `auto_learn=true`

Users may explicitly enable or disable any switch by prompt, through this CLI, or by editing the memory config file.

When this skill is used in a repo, ensure `AGENTS.md` contains the project memory protocol by running the idempotent guidance command. The inserted protocol must be generic, project-scoped, and must not hardcode any user name, user hash, git email, account ID, alias, or profile name.

## Scope

Use this skill only for private user-project memory:

- Communication preferences.
- Workflow preferences.
- Local runtime preferences such as a Python interpreter path.
- Project-private local config.
- Account aliases that do not contain secrets.
- Safety preferences that only strengthen existing rules.

The memory subject is the current project. The only active memory scope is `repo_user`, stored at `docs/.ai-hermes-user-memory/users/<user_hash>/repos/<repo_hash>.json`. Do not create, recall, or write cross-project memory.

Do not store project implementation facts here. Shared project facts belong in AI Hermes routing memory, not user memory.

## Required Tool

Use a memory CLI for all persisted memory operations:

- Prefer the current repo's project-local skill script `skills/ai-hermes-user-project-memory/scripts/ai_hermes_user_project_memory.py` when it exists.
- Otherwise use this skill's bundled `scripts/ai_hermes_user_project_memory.py`.
- Use `--repo-root <target-repo>` when operating outside the current working directory.

Common commands:

```bash
python3 skills/ai-hermes-user-project-memory/scripts/ai_hermes_user_project_memory.py --json ensure-agents-guidance
python3 skills/ai-hermes-user-project-memory/scripts/ai_hermes_user_project_memory.py --json status
python3 skills/ai-hermes-user-project-memory/scripts/ai_hermes_user_project_memory.py --json recall
python3 skills/ai-hermes-user-project-memory/scripts/ai_hermes_user_project_memory.py --json recall --scope repo_user
python3 skills/ai-hermes-user-project-memory/scripts/ai_hermes_user_project_memory.py --json learn --scope repo_user --type communication_preference --key response.language --value-json '{"language":"zh-CN"}' --source user_explicit --one-shot-authorized
python3 skills/ai-hermes-user-project-memory/scripts/ai_hermes_user_project_memory.py --json propose --candidate-json '{"proposed_memory":{"type":"workflow_preference","scope":"repo_user","key":"response.style.bullets","value":{"enabled":true}}}'
python3 skills/ai-hermes-user-project-memory/scripts/ai_hermes_user_project_memory.py --json approve --candidate-id <CANDIDATE_ID>
python3 skills/ai-hermes-user-project-memory/scripts/ai_hermes_user_project_memory.py --json forget --scope repo_user --key response.language
python3 skills/ai-hermes-user-project-memory/scripts/ai_hermes_user_project_memory.py --json disable --scope repo_user --auto-learn
python3 skills/ai-hermes-user-project-memory/scripts/ai_hermes_user_project_memory.py --json enable --scope repo_user --learn --auto-learn
python3 skills/ai-hermes-user-project-memory/scripts/ai_hermes_user_project_memory.py --json audit
```

If the project-local skill script does not exist, run the bundled script from this skill directory with the same arguments and add `--repo-root <target-repo>` when needed.

## Recall Rules

Recall is allowed only when persisted `recall=true` and the current session is not suppressed.

Before normal user-facing work, run `skills/ai-hermes-user-project-memory/scripts/ai_hermes_user_project_memory.py --json recall` to dynamically resolve the current user/repo identity and load applicable project-scoped `repo_user` memories. Do not hardcode identity in `AGENTS.md` or prompts; let the tool look it up from git config or its safe fallback.

Recall should be silent. Mention it only when it changes an important action, such as choosing a Python interpreter, or when a remembered path is missing.

Never let memory override:

- System instructions.
- Developer instructions.
- Project `AGENTS.md`.
- Sandbox or approval rules.
- Current user instructions in this turn.

## Learning Rules

Direct writes require one of these:

- User explicitly says `remember` / `记住`, then use `--source user_explicit --one-shot-authorized` for that memory.
- Learning is enabled, and the user approves a candidate or requests a manual import.
- Learning and auto learn are both enabled, there is no active memory with the same key, and the memory is low-sensitive communication or workflow preference.
- If an inferred preference conflicts with an existing active memory, propose a candidate instead of writing active memory.

Do not auto-write:

- Local paths.
- Account aliases.
- Browser profiles.
- Hosts.
- Customer names.
- Private config.
- One-off task parameters.
- Any secret-like value.

## Suppression Rules

Default to no recall and no learning for:

- Subagent instructions.
- CI or batch prompts.
- Automation templates.
- Another agent's handoff summary.
- User phrases such as `本轮不记`, `不要学习`, `只是这次`.

Only override suppression if the user explicitly asks to use personal memory for this turn.

## Python Runtime Preference

Before running Python, tests, or scripts, if recall is enabled, check for:

- `type=local_runtime_preference`
- `key=python.interpreter.default`
- `scope=repo_user`

Apply priority:

1. System/developer instruction.
2. Current user instruction.
3. `$PYTHON`.
4. Valid remembered `python.interpreter.default`.
5. `python3`.

Validate remembered paths before use with `test -x` and `<path> --version`. If invalid, fall back and briefly tell the user the memory may be stale.

## Privacy Rules

Never store or output unnecessarily:

- API keys.
- Tokens.
- Cookies.
- Authorization plaintext.
- Passwords.
- Account passwords or credential pairs.
- Private keys.
- Database URLs or DSNs.
- `.env` contents.
- Raw conversation text.
- Full automation prompts.
- Plain git email/name as file names.

Human-facing output should mask local paths and identity unless the full path is needed for command execution.

## Git Cloud Sync

Default behavior: `docs/.ai-hermes-user-memory/` stays ignored by git and should not be committed.

If and only if the user explicitly asks to save project memory to a cloud/remote git repository:

- First run `python3 skills/ai-hermes-user-project-memory/scripts/ai_hermes_user_project_memory.py --json git-sync-check --confirm-user-explicit`.
- The check must run immediately before `git add`, commit, or push.
- The check must scan the entire `docs/.ai-hermes-user-memory/` tree and fail on tokens, passwords, Authorization plaintext, cookies, private keys, database URLs, `.env` content, corrupt memory files, or legacy `profile.json`.
- If the check passes, the agent may use `git add -f docs/.ai-hermes-user-memory/config.json docs/.ai-hermes-user-memory/users` because the directory is ignored by default.
- If the check fails, do not stage, commit, push, paste, or summarize the sensitive value; report only that sensitive memory content must be removed.
- Do not sync memory from non-git projects.

## Project Boundary

The memory files must live exactly under this project's `docs/.ai-hermes-user-memory/` directory. The CLI must reject every custom memory home, even if it is inside the current project.

This project may contain:

- The memory CLI.
- This skill.
- Policy JSON.
- Tests.
- Routing coverage facts for the capability itself.
- User memory data under `docs/.ai-hermes-user-memory/`, which stays ignored by git unless the user explicitly requests cloud sync and `git-sync-check` passes.

The active memory data file is `docs/.ai-hermes-user-memory/users/<user_hash>/repos/<repo_hash>.json`.

Do not write actual personal preferences, local paths, account aliases, or profile names into `AGENTS.md`, `docs/repo_map.json`, `docs/task_routes.json`, `docs/pitfalls.json`, README, PR text, or routing facts. Use `docs/.ai-hermes-user-memory/` for actual memory data only.
