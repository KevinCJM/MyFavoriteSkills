# AI Hermes User Project Memory / AI Hermes 用户项目记忆

## 中文说明

### 这个技能做什么

- `ai-hermes-user-project-memory` 用来保存某个用户在某个项目里的个人长期偏好和本机私有配置, 如果是git项目则通过git账号区分不同的用户。
- 适合保存：
  - 沟通偏好，例如默认中文、简洁回答、使用 bullet。
  - 工作流偏好，例如先测试再总结、提交前先自查。
  - 本机运行偏好，例如某项目默认 Python 解释器。
  - 项目私有配置，例如本机 profile 名称或非敏感账号别名。
  - 只会增强安全性的个人偏好。
- 不适合保存：
  - 项目实现事实。
  - 共享架构事实。
  - 一次性任务参数。
  - secrets、token、cookie、Authorization 明文、账号密码、私钥、数据库连接串、`.env` 内容。
  - 原始对话全文或完整自动化 prompt。

### 它和 AGENTS.md 有什么不同

- `AGENTS.md` 是项目共享协议：
  - 会进入仓库。
  - 对所有智能体和所有协作者生效。
  - 记录项目级规则、路由协议、验证要求、输出纪律。
- 用户项目记忆是个人私有上下文：
  - 只能保存在当前项目的 `docs/.ai-hermes-user-memory/`。
  - 按 git 用户和 repo 隔离。
  - 用来记录“这个用户在这个项目里怎么希望智能体工作”以及“这个用户独有的本机配置”。
- 优先级不同：
  - system/developer 指令优先。
  - 当前用户本轮明确要求优先。
  - 项目 `AGENTS.md` 优先。
  - 用户记忆只能在不冲突时辅助智能体工作。
- 边界不同：
  - 项目共享事实应该进 `AGENTS.md` 或 AI Hermes 路由 JSON。
  - 个人偏好、本机路径、账号别名、profile 名称只能写进 `docs/.ai-hermes-user-memory/`，不应该写进 `AGENTS.md` 或路由 JSON。

### AGENTS.md 自动说明

- 使用这个技能时，应先运行 `ensure-agents-guidance`，把通用记忆协议自动写入或更新到当前项目的 `AGENTS.md`。
- 这段说明只写协议，不写真实个人记忆：
  - 不写死用户名。
  - 不写死用户 hash。
  - 不写死 git email。
  - 不写死账号 ID、账号别名或 profile 名称。
- 当 `recall` 开启且当前会话没有被抑制时，`AGENTS.md` 会要求智能体先运行 `skills/ai-hermes-user-project-memory/scripts/ai_hermes_user_project_memory.py --json recall`，只召回当前项目的 `repo_user` 记忆。
- 用户和 repo 身份由工具在运行时根据 git 配置或安全 fallback 动态查找，并使用 hash 做隔离。
- 召回结果只在不冲突时应用；system/developer 指令、当前用户本轮要求和 `AGENTS.md` 始终优先。

### 默认开关

- 安装或首次使用后，默认三项都开启：
  - `recall=true`
  - `learn=true`
  - `auto_learn=true`
- 如果需要关闭或重新开启任一项，可以直接在提示词中声明，也可以运行 CLI 命令，也可以手动改配置文件。
- 即使自动学习开启，仍然不能自动写入本机路径、账号别名、profile、host、客户名、私有配置或 secret-like 内容。

### recall、learn、auto_learn 是什么

- `recall` 是“召回/读取记忆”：
  - 开启后，智能体可以读取当前用户在当前项目里保存的 `repo_user` 记忆。
  - 典型用途是应用已有偏好，例如回答风格、默认工具、项目本机 Python 解释器。
  - 召回只读已有记忆，不代表会写入新记忆。
- `learn` 是“允许学习/写入记忆”：
  - 开启后，智能体可以在策略允许时写入、更新、批准候选记忆。
  - 关闭后，普通学习和候选批准会被拒绝；只有用户明确“记住”并使用一次性授权时，才允许写入当前这一条。
  - 关闭 `learn` 会同时压制 `auto_learn`。
- `auto_learn` 是“允许自动学习低风险偏好”：
  - 开启后，智能体可以把高置信、稳定、低敏的沟通偏好或工作流偏好自动写入记忆。
  - 它依赖 `learn=true`；如果 `learn=false`，`auto_learn` 实际无效。
  - 它不能自动写入本机路径、账号别名、profile、host、客户名、私有配置、secret-like 内容，也不能覆盖已有 active memory。

### 提示词触发方式

- 明确记忆：
  - “记住：以后本项目回答直接简要，用 bullet。”
  - “remember this preference for this repo.”
- 忘记或删除：
  - “忘记本项目的 Python 解释器记忆。”
  - “forget my repo memory for response.language.”
- 开关控制：
  - “关闭本项目自动学习。”
  - “开启个人项目记忆召回。”
  - “本轮不记，不要学习。”
- 查看和审计：
  - “查看当前用户项目记忆状态。”
  - “审计用户记忆是否有敏感信息。”
- 应用记忆：
  - “使用我的本项目记忆运行测试。”
  - “按我的偏好继续。”

### 自动触发机制

- 使用该技能时，先确保 `AGENTS.md` 已包含用户记忆协议：`python3 skills/ai-hermes-user-project-memory/scripts/ai_hermes_user_project_memory.py --json ensure-agents-guidance`。
- 普通用户面对话开始执行前，如果召回开启且没有被抑制，应运行 `python3 skills/ai-hermes-user-project-memory/scripts/ai_hermes_user_project_memory.py --json recall`，让工具动态查找当前用户和 repo 身份，并只读取当前项目的 `repo_user` 记忆。
- 当智能体准备运行 Python、测试、部署或本地脚本时，应先召回相关本机运行偏好。
- 当长对话或多轮密集协作中出现稳定、低风险、可复用的偏好时，可以自动学习。
- 自动学习只允许低敏的沟通偏好和工作流偏好。
- 如果推断到的偏好与已有 active memory 冲突，应生成候选并等待用户确认，而不是直接覆盖。
- 以下上下文默认抑制召回和学习，除非用户明确要求使用记忆：
  - subagent 指令。
  - CI prompt。
  - 批处理 prompt。
  - 自动化模板。
  - 其他模型或智能体的 handoff summary。
  - 用户明确说“本轮不记”“不要学习”“只是这次”。

### 常用命令

优先在项目根目录使用项目内技能脚本：

```bash
python3 skills/ai-hermes-user-project-memory/scripts/ai_hermes_user_project_memory.py --json ensure-agents-guidance
python3 skills/ai-hermes-user-project-memory/scripts/ai_hermes_user_project_memory.py --json status
```

如果当前项目没有项目内技能脚本，但已经安装了本地 Codex 技能，可以使用 bundled script：

```bash
python3 ~/.codex/skills/ai-hermes-user-project-memory/scripts/ai_hermes_user_project_memory.py \
  --repo-root <repo> \
  --json status
```

- 这里的 `~/.codex/skills/ai-hermes-user-project-memory/` 只提供可复用的技能说明、脚本和策略文件。
- 即使使用全局 Codex 技能里的 bundled script，真实用户记忆仍然固定写入目标项目的 `<repo>/docs/.ai-hermes-user-memory/`，不会写入 `~/.codex/`。

召回当前用户在当前项目里的记忆：

```bash
python3 skills/ai-hermes-user-project-memory/scripts/ai_hermes_user_project_memory.py --json recall
python3 skills/ai-hermes-user-project-memory/scripts/ai_hermes_user_project_memory.py --json recall --scope repo_user
```

记住一条明确偏好：

```bash
python3 skills/ai-hermes-user-project-memory/scripts/ai_hermes_user_project_memory.py --json learn \
  --scope repo_user \
  --type communication_preference \
  --key response.style \
  --value-json '{"format":"bullets","tone":"direct"}' \
  --source user_explicit \
  --one-shot-authorized
```

关闭当前 repo 的自动学习：

```bash
python3 skills/ai-hermes-user-project-memory/scripts/ai_hermes_user_project_memory.py --json disable --scope repo_user --auto-learn
```

关闭当前 repo 的学习；这也会关闭自动学习：

```bash
python3 skills/ai-hermes-user-project-memory/scripts/ai_hermes_user_project_memory.py --json disable --scope repo_user --learn
```

重新开启学习和自动学习：

```bash
python3 skills/ai-hermes-user-project-memory/scripts/ai_hermes_user_project_memory.py --json enable --scope repo_user --learn --auto-learn
```

关闭当前 repo 的全部记忆开关：

```bash
python3 skills/ai-hermes-user-project-memory/scripts/ai_hermes_user_project_memory.py --json disable --scope repo_user
```

删除某条记忆：

```bash
python3 skills/ai-hermes-user-project-memory/scripts/ai_hermes_user_project_memory.py --json forget --scope repo_user --key response.style
```

审计记忆文件：

```bash
python3 skills/ai-hermes-user-project-memory/scripts/ai_hermes_user_project_memory.py --json audit
```

显式检查是否允许把用户记忆保存到云端 git 仓库：

```bash
python3 skills/ai-hermes-user-project-memory/scripts/ai_hermes_user_project_memory.py --json git-sync-check --confirm-user-explicit
```

### 保存到云端 git 仓库

- 默认不提交真实用户记忆，`docs/.ai-hermes-user-memory/` 仍应被 `.gitignore` 忽略。
- 只有用户明确要求“保存记忆到云端仓库 / 提交用户记忆到 git”时，智能体才可以考虑同步。
- 同步前必须确认当前项目是 git 项目。
- 同步前必须立刻运行：

```bash
python3 skills/ai-hermes-user-project-memory/scripts/ai_hermes_user_project_memory.py --json git-sync-check --confirm-user-explicit
```

- 该检查会扫描整个 `docs/.ai-hermes-user-memory/`，发现 token、账号密码、Authorization 明文、cookie、私钥、数据库连接串、`.env` 内容、损坏文件或旧 `profile.json` 就会失败。
- 只有检查通过后，才允许使用：

```bash
git add -f docs/.ai-hermes-user-memory/config.json docs/.ai-hermes-user-memory/users
```

- 如果检查失败，不要 stage、commit、push，也不要把敏感值展示给用户；只说明需要先删除敏感记忆。

### 敏感信息防线

- 学习、导入、审计和 git 同步检查都必须拒绝 secret-like 内容。
- 禁止保存 token、cookie、Authorization 明文、账号密码、私钥、数据库连接串、`.env` 内容和完整自动化 prompt。
- 检查失败时，只报告“存在敏感记忆内容需要删除”，不要复述、摘录或总结敏感值。
- 如果确实需要记录账号相关信息，只能保存不含凭据的别名或选择器，并且不能自动学习。

### 用户记忆保存在哪里

- 默认 memory home：
  - `<repo>/docs/.ai-hermes-user-memory`
- 项目记忆开关配置：
  - `<repo>/docs/.ai-hermes-user-memory/config.json`
- 当前项目内某个用户的项目记忆：
  - `<repo>/docs/.ai-hermes-user-memory/users/<user_hash>/repos/<repo_hash>.json`
- 候选记忆：
  - `<repo>/docs/.ai-hermes-user-memory/users/<user_hash>/candidates/`
- 审计日志：
  - `<repo>/docs/.ai-hermes-user-memory/users/<user_hash>/audit.log.jsonl`
- 锁文件：
  - `<repo>/docs/.ai-hermes-user-memory/locks/`
- 这些文件必须固定在当前项目下，不允许保存到 `~/.codex/` 或其他项目内自定义目录。
- 全局 Codex 技能目录只保存技能代码和说明，不保存任何项目用户记忆数据。
- `docs/.ai-hermes-user-memory/` 应加入 `.gitignore`，默认不提交真实用户记忆。
- 如果用户明确要求保存到云端 git 仓库，必须先运行 `git-sync-check --confirm-user-explicit`，通过后才可 `git add -f docs/.ai-hermes-user-memory/config.json docs/.ai-hermes-user-memory/users`。

### 手动修改配置

- 可以编辑 `config.json` 里的 `default_enabled`：

```json
{
  "default_enabled": {
    "recall": true,
    "learn": true,
    "auto_learn": true
  }
}
```

- 如果设置 `"learn": false`，工具会把 `"auto_learn"` 视为 `false`。
- 不要手动把真实 secret、token、cookie、密码或 `.env` 内容写进任何记忆文件。

## English

### What This Skill Does

- `ai-hermes-user-project-memory` stores long-term private preferences and local configuration for one git user in one project.
- Good fit:
  - Communication preferences, such as default language, concise answers, or bullet format.
  - Workflow preferences, such as testing before summarizing or checking memory before running scripts.
  - Local runtime preferences, such as a project-specific Python interpreter.
  - Project-private local configuration, such as non-secret account aliases or profile names.
  - Personal safety preferences that only strengthen existing rules.
- Not a good fit:
  - Project implementation facts.
  - Shared architecture facts.
  - One-off task parameters.
  - Secrets, tokens, cookies, Authorization plaintext, account passwords, private keys, database connection strings, or `.env` contents.
  - Raw conversation logs or full automation prompts.

### How It Differs From AGENTS.md

- `AGENTS.md` is shared project protocol:
  - It is committed to the repository.
  - It applies to every agent and collaborator.
  - It stores project-level rules, routing protocol, verification requirements, and output discipline.
- User project memory is project-local private user context:
  - It must be stored in the current project under `docs/.ai-hermes-user-memory/`.
  - The project is the memory subject; memories are then isolated by git user and repo hash.
  - It stores only how this user wants agents to work in this project and what local configuration belongs to this user in this project.
  - It does not provide cross-project memory.
- Priority:
  - System/developer instructions win.
  - Current user instructions win.
  - Project `AGENTS.md` wins.
  - User memory can help only when it does not conflict with higher-priority instructions.
- Boundary:
  - Shared project facts belong in `AGENTS.md` or AI Hermes routing JSON.
  - Personal preferences, local paths, account aliases, and profile names should only be written to `docs/.ai-hermes-user-memory/`, not to `AGENTS.md` or routing JSON.

### Automatic AGENTS.md Guidance

- When this skill is used, agents should first run `ensure-agents-guidance` to insert or update the generic memory protocol in the current project's `AGENTS.md`.
- The inserted guidance is protocol only; it must not store real personal memory:
  - No hardcoded user name.
  - No hardcoded user hash.
  - No hardcoded git email.
  - No hardcoded account ID, account alias, or profile name.
- When `recall` is enabled and the current session is not suppressed, `AGENTS.md` requires agents to run `skills/ai-hermes-user-project-memory/scripts/ai_hermes_user_project_memory.py --json recall` before normal user-facing work and load only current-project `repo_user` memories.
- User and repo identity are resolved dynamically by the tool at runtime from git configuration or a safe fallback, then isolated by hashes.
- Recalled memories apply only when they do not conflict with higher-priority instructions; system/developer instructions, the current user turn, and `AGENTS.md` always win.

### Default Switches

- After installation or first use, all three switches are enabled by default:
  - `recall=true`
  - `learn=true`
  - `auto_learn=true`
- Users can explicitly enable or disable any switch in a prompt, through CLI commands, or by editing the config file.
- Even when auto-learning is enabled, it must not auto-write local paths, account aliases, profiles, hosts, customer names, private config, or secret-like values.

### What recall, learn, and auto_learn Mean

- `recall` means “read existing memory”:
  - When enabled, agents can read stored `repo_user` memories for the current user in the current project.
  - Common uses include applying existing response style, preferred tools, or a project-local Python interpreter.
  - Recall is read-only; it does not mean new memories will be written.
- `learn` means “allow memory writes”:
  - When enabled, agents can write, update, or approve candidate memories when policy allows it.
  - When disabled, normal learning and candidate approval are denied; only an explicit user “remember” request with one-shot authorization may write that single memory.
  - Disabling `learn` also suppresses `auto_learn`.
- `auto_learn` means “allow automatic learning of low-risk preferences”:
  - When enabled, agents can automatically store high-confidence, stable, low-sensitive communication or workflow preferences.
  - It depends on `learn=true`; if `learn=false`, `auto_learn` is effectively off.
  - It must not auto-write local paths, account aliases, profiles, hosts, customer names, private config, secret-like values, or overwrite an existing active memory.

### Prompt Triggers

- Remember:
  - “Remember: answer directly and use bullets in this project.”
  - “记住：以后本项目回答直接简要，用 bullet。”
- Forget:
  - “Forget my repo memory for response.language.”
  - “忘记本项目的 Python 解释器记忆。”
- Switches:
  - “Disable auto-learning for this repo.”
  - “开启个人项目记忆召回。”
  - “Do not learn from this turn.”
- View and audit:
  - “Show current user project memory status.”
  - “Audit user memory for sensitive content.”
- Apply:
  - “Use my project memory before running tests.”
  - “Continue with my preferences.”

### Automatic Triggers

- When using this skill, first ensure `AGENTS.md` contains the user memory protocol: `python3 skills/ai-hermes-user-project-memory/scripts/ai_hermes_user_project_memory.py --json ensure-agents-guidance`.
- Before normal user-facing work, if recall is enabled and not suppressed, run `python3 skills/ai-hermes-user-project-memory/scripts/ai_hermes_user_project_memory.py --json recall` so the tool dynamically resolves the current user and repo identity and reads only current-project `repo_user` memories.
- Before running Python, tests, deployment commands, or local scripts, agents should recall relevant local runtime preferences.
- In long or dense collaborations, stable low-risk reusable preferences may be learned automatically.
- Auto-learning is limited to low-sensitive communication and workflow preferences.
- If an inferred preference conflicts with an existing active memory, create a candidate and wait for user approval instead of overwriting it.
- Recall and learning are suppressed by default in these contexts unless the user explicitly asks to use memory:
  - Subagent instructions.
  - CI prompts.
  - Batch prompts.
  - Automation templates.
  - Handoff summaries from another model or agent.
  - User phrases such as “do not learn from this turn” or “just this time.”

### Common Commands

Prefer the project-local skill script from the project root:

```bash
python3 skills/ai-hermes-user-project-memory/scripts/ai_hermes_user_project_memory.py --json ensure-agents-guidance
python3 skills/ai-hermes-user-project-memory/scripts/ai_hermes_user_project_memory.py --json status
```

If the current project does not have the project-local skill script but this local Codex skill is installed, use the bundled script:

```bash
python3 ~/.codex/skills/ai-hermes-user-project-memory/scripts/ai_hermes_user_project_memory.py \
  --repo-root <repo> \
  --json status
```

- `~/.codex/skills/ai-hermes-user-project-memory/` contains only reusable skill instructions, scripts, and policy files.
- Even when the bundled script is used, real user memory is still written only to the target project's `<repo>/docs/.ai-hermes-user-memory/`, not to `~/.codex/`.

Recall current user memory for the current project:

```bash
python3 skills/ai-hermes-user-project-memory/scripts/ai_hermes_user_project_memory.py --json recall
python3 skills/ai-hermes-user-project-memory/scripts/ai_hermes_user_project_memory.py --json recall --scope repo_user
```

Remember an explicit preference:

```bash
python3 skills/ai-hermes-user-project-memory/scripts/ai_hermes_user_project_memory.py --json learn \
  --scope repo_user \
  --type communication_preference \
  --key response.style \
  --value-json '{"format":"bullets","tone":"direct"}' \
  --source user_explicit \
  --one-shot-authorized
```

Disable auto-learning for this repo:

```bash
python3 skills/ai-hermes-user-project-memory/scripts/ai_hermes_user_project_memory.py --json disable --scope repo_user --auto-learn
```

Disable learning for this repo, which also disables auto-learning:

```bash
python3 skills/ai-hermes-user-project-memory/scripts/ai_hermes_user_project_memory.py --json disable --scope repo_user --learn
```

Re-enable learning and auto-learning:

```bash
python3 skills/ai-hermes-user-project-memory/scripts/ai_hermes_user_project_memory.py --json enable --scope repo_user --learn --auto-learn
```

Disable all memory switches for this repo:

```bash
python3 skills/ai-hermes-user-project-memory/scripts/ai_hermes_user_project_memory.py --json disable --scope repo_user
```

Forget a memory:

```bash
python3 skills/ai-hermes-user-project-memory/scripts/ai_hermes_user_project_memory.py --json forget --scope repo_user --key response.style
```

Audit memory files:

```bash
python3 skills/ai-hermes-user-project-memory/scripts/ai_hermes_user_project_memory.py --json audit
```

Explicitly check whether user memory can be saved to a cloud git repository:

```bash
python3 skills/ai-hermes-user-project-memory/scripts/ai_hermes_user_project_memory.py --json git-sync-check --confirm-user-explicit
```

### Saving To A Cloud Git Repository

- By default, real user memory is not committed; `docs/.ai-hermes-user-memory/` should remain ignored by `.gitignore`.
- Agents may consider syncing only when the user explicitly asks to save memory to a cloud/remote git repository.
- The project must be a git worktree.
- Immediately before syncing, run:

```bash
python3 skills/ai-hermes-user-project-memory/scripts/ai_hermes_user_project_memory.py --json git-sync-check --confirm-user-explicit
```

- The check scans the entire `docs/.ai-hermes-user-memory/` tree and fails on tokens, account passwords, Authorization plaintext, cookies, private keys, database URLs, `.env` content, corrupt files, or legacy `profile.json`.
- Only after the check passes, use:

```bash
git add -f docs/.ai-hermes-user-memory/config.json docs/.ai-hermes-user-memory/users
```

- If the check fails, do not stage, commit, push, paste, or summarize the sensitive value; only report that sensitive memory content must be removed first.

### Sensitive-Information Guardrails

- Learning, import, audit, and git-sync checks must reject secret-like content.
- Do not store tokens, cookies, Authorization plaintext, account passwords, private keys, database connection strings, `.env` contents, or full automation prompts.
- When a check fails, report only that sensitive memory content must be removed; do not repeat, excerpt, or summarize the sensitive value.
- If account-related information must be remembered, store only non-secret aliases or selectors, and do not auto-learn them.

### Where User Memory Is Stored

- Default memory home:
  - `<repo>/docs/.ai-hermes-user-memory`
- Project memory switch config:
  - `<repo>/docs/.ai-hermes-user-memory/config.json`
- Project memory for one user in the current repo:
  - `<repo>/docs/.ai-hermes-user-memory/users/<user_hash>/repos/<repo_hash>.json`
- Candidate memories:
  - `<repo>/docs/.ai-hermes-user-memory/users/<user_hash>/candidates/`
- Audit log:
  - `<repo>/docs/.ai-hermes-user-memory/users/<user_hash>/audit.log.jsonl`
- Lock files:
  - `<repo>/docs/.ai-hermes-user-memory/locks/`
- These files must stay at that exact project path and must not be stored in `~/.codex/` or a custom in-project directory.
- The global Codex skill directory stores only skill code and documentation, never project user memory data.
- `docs/.ai-hermes-user-memory/` should be listed in `.gitignore`; real user memory is not committed by default.
- If the user explicitly asks to save memory to a cloud git repository, run `git-sync-check --confirm-user-explicit` first; only after it passes may agents use `git add -f docs/.ai-hermes-user-memory/config.json docs/.ai-hermes-user-memory/users`.

### Manual Config Edits

- You can edit `default_enabled` in `config.json`:

```json
{
  "default_enabled": {
    "recall": true,
    "learn": true,
    "auto_learn": true
  }
}
```

- If `"learn": false`, the tool treats `"auto_learn"` as `false`.
- Do not manually write real secrets, tokens, cookies, passwords, or `.env` contents into any memory file.
