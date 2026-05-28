# Mine Codex Workflows / Codex 历史工作流挖掘技能

## English

`mine-codex-workflows` is a portable Codex skill that analyzes local Codex conversation history for the current project and proposes repeated workflows that may be worth turning into reusable skills.

### What it does

- Scans local Codex history from `${CODEX_HOME:-$HOME/.codex}`.
- Filters history to the current project with project-root and anchor matching.
- Redacts secrets, tokens, cookies, private keys, emails, phone numbers, URLs, and sensitive command arguments.
- Reports repeated workflow candidates, common files, common command templates, risks, and human-review-required skill draft suggestions.
- Does not upload data, call external services, write files, or output raw conversations by default.

### Install

Copy this folder into your Codex skills directory:

```bash
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R mine-codex-workflows "${CODEX_HOME:-$HOME/.codex}/skills/"
```

Restart Codex if your environment requires skill discovery on startup.

### Basic usage

From any project root:

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/mine-codex-workflows/scripts/mine_codex_history.py" \
  --project-root . \
  --days 60 \
  --min-count 2 \
  --max-sessions 500 \
  --format json
```

### Draft mode

Use draft mode when you want skill proposal fields in the output:

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/mine-codex-workflows/scripts/mine_codex_history.py" \
  --project-root . \
  --days 60 \
  --min-count 2 \
  --mode draft \
  --format json
```

Draft suggestions are not ready-to-install skills. Review them before creating or editing any files.

### Project customization

Add project-specific anchors without editing the skill:

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/mine-codex-workflows/scripts/mine_codex_history.py" \
  --project-root . \
  --anchor my-project-name \
  --anchor important-config.yaml
```

Use custom workflow rules:

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/mine-codex-workflows/scripts/mine_codex_history.py" \
  --project-root . \
  --workflow-rules path/to/rules.json
```

A rules file can be a list of rules or an object with `workflow_rules`:

```json
{
  "workflow_rules": [
    {
      "id": "notebook-maintenance",
      "title": "Notebook maintenance workflow",
      "terms": ["notebook", "ipynb"],
      "goal": "Maintain recurring notebook workflows.",
      "steps": ["Find repeated notebook tasks", "Summarize reusable steps"],
      "risks": ["Do not include sensitive notebook outputs in skills"]
    }
  ]
}
```

### Validate

```bash
python3 -m py_compile "${CODEX_HOME:-$HOME/.codex}/skills/mine-codex-workflows/scripts/mine_codex_history.py"
python3 "${CODEX_HOME:-$HOME/.codex}/skills/mine-codex-workflows/scripts/mine_codex_history.py" --project-root . --days 7 --max-sessions 20 --format json
```

## 中文

`mine-codex-workflows` 是一个可移植的 Codex 技能，用于扫描当前项目相关的本地 Codex 历史对话，找出反复出现、值得沉淀为技能的工作流。

### 功能

- 从 `${CODEX_HOME:-$HOME/.codex}` 读取本地 Codex 历史。
- 根据当前项目路径和项目锚点过滤历史记录。
- 自动脱敏密钥、token、cookie、私钥、邮箱、手机号、URL 和敏感命令参数。
- 输出重复工作流候选、常见文件、常见命令模板、风险，以及需要人工审核的技能草案建议。
- 默认不上传数据、不调用外部服务、不写文件、不输出原始对话。

### 安装

把整个文件夹复制到 Codex skills 目录：

```bash
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R mine-codex-workflows "${CODEX_HOME:-$HOME/.codex}/skills/"
```

如果你的 Codex 环境需要启动时发现技能，请重启 Codex。

### 基础用法

在任意项目根目录运行：

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/mine-codex-workflows/scripts/mine_codex_history.py" \
  --project-root . \
  --days 60 \
  --min-count 2 \
  --max-sessions 500 \
  --format json
```

### 草案模式

如果希望输出技能草案建议字段，使用 draft 模式：

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/mine-codex-workflows/scripts/mine_codex_history.py" \
  --project-root . \
  --days 60 \
  --min-count 2 \
  --mode draft \
  --format json
```

草案建议不是可直接安装的最终技能，创建或修改技能文件前需要人工审核。

### 项目定制

不用修改技能源码，也可以增加项目专属锚点：

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/mine-codex-workflows/scripts/mine_codex_history.py" \
  --project-root . \
  --anchor my-project-name \
  --anchor important-config.yaml
```

也可以使用自定义工作流规则：

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/mine-codex-workflows/scripts/mine_codex_history.py" \
  --project-root . \
  --workflow-rules path/to/rules.json
```

规则文件可以是规则列表，也可以是包含 `workflow_rules` 的对象。

### 验证

```bash
python3 -m py_compile "${CODEX_HOME:-$HOME/.codex}/skills/mine-codex-workflows/scripts/mine_codex_history.py"
python3 "${CODEX_HOME:-$HOME/.codex}/skills/mine-codex-workflows/scripts/mine_codex_history.py" --project-root . --days 7 --max-sessions 20 --format json
```

### 安全说明

- 这个技能只做本地只读分析。
- 默认不输出原始对话。
- 默认不保存报告。
- 如果启用 `--write-report`，请确认输出路径是私有位置。
- 所有候选都只是建议，不应未经审核就写成正式技能。
