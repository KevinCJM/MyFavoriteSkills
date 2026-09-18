# Codex OpenCode Dispatch

让 **Codex 负责判断与验收，OpenCode Worker 负责边界清楚的调查和实现**。

这是一个可跨项目复用的 Codex Skill，目标是减少主控重复劳动，同时保留工程质量检查。它不是 MCP 服务、模型代理或安全沙箱，也不保证每个任务都能节省 token。

- Skill 版本：`2.3.0`，包含后续流程优化；本文更新于 2026-09-18。
- 适配底座：[AlaeddineMessadi/opencode-mcp](https://github.com/AlaeddineMessadi/opencode-mcp) `3.0.0`。
- 正常运行入口：[SKILL.md](SKILL.md)。README 面向使用者，不需要每次派工都加载。

## 适合做什么

- 调查范围明确、工作量较大的代码问题，返回可定位的证据。
- 按已确定的需求修改代码、补充测试，再由 Codex 独立验收。
- 将相互独立的问题交给多个 Worker 分析，由 Codex 汇总。
- 让实现者和审核者使用不同会话，避免把“Worker 已完成”当成“已经验收”。

很小且答案已明确的修改，直接由 Codex 完成通常更合适。业务语义、公共接口、安全边界、发布和合并等关键决定仍由 Codex 在用户授权范围内负责。

## 工作方式

1. **确定边界。** 读取项目规则，确认目标、代码快照、允许修改的范围和验收要求。
2. **派一次清楚的任务。** 把必要上下文、固定决定、检查项和停止条件交给 Worker；不发送整段聊天历史。
3. **保留任务身份。** 记录 job/session/message ID，等待已有任务，不因超时盲目重派。
4. **独立验收。** Codex 核对实际代码、关键失败路径、测试断言及原始需求覆盖。
5. **窄范围返工或交付。** 返工只补具体差异；权限不足、范围冲突或证据不足时报告阻塞。

每个独立修改先回答四个问题：属于当前需求吗？不改会阻塞什么？是不是最小正确修改？是否保留已有契约？小任务用一行 `Boundary:` 即可，不强制建立完整台账。

Scout、Designer、Builder、Verifier 是任务角色，不是自动安装好的 OpenCode agent。`ocw/1` 是放在 MCP `prompt` 字符串中的任务约定，不是新的 MCP 参数。

## 安装

### 1. 准备运行环境

需要能正常使用 Skills 的 Codex、已连接的 `opencode-mcp@3.0.0`、可用的 OpenCode，以及你自己的模型访问权限。安装 Skill **不会**自动安装 MCP、登录模型账号或修改全局配置。

先按 [MCP 上游说明](https://github.com/AlaeddineMessadi/opencode-mcp) 安装并连接服务，再确认当前 Codex 会话确实能看到它的工具。服务器上的项目目录必须真实存在；本机文件不会由 MCP 自动上传到另一台机器。

可选辅助脚本需要 Python 3.10+；Git 回执工具另外需要 Git，均不需要额外 pip 依赖。

### 2. 复制 Skill

克隆本仓库后，在仓库根目录执行以下首次安装命令。目标已存在时停止，不覆盖旧版本：

```bash
mkdir -p "$HOME/.agents/skills"
skill_target="$HOME/.agents/skills/codex-opencode-dispatch"
if [ -e "$skill_target" ] || [ -L "$skill_target" ]; then
  echo "目标已存在，请先将旧版移到 skills 扫描目录之外，再安装。"
else
  cp -R ./codex-opencode-dispatch "$skill_target"
fi
```

仅用于一个项目时，可改放项目的 `.agents/skills/`。全局和项目级选一种，避免同名副本同时生效；如果现有 Codex 安装使用其他受支持的 Skill 目录，沿用该目录即可。更新未被识别时重启 Codex。参见 [Codex Skills 官方说明](https://developers.openai.com/zh-Hans/docs/build-skills)。

升级时先备份旧目录，再替换完整 Skill。已有 Worker 不会自动收到新规则；先确认旧轮次停止，再更新任务契约。

## 开始使用

### 只读调查

```text
$codex-opencode-dispatch
请分析本项目某个模块的错误处理和测试缺口。
将边界清楚的调查交给一个只读 Worker，不改代码、不连接外部环境；
你负责核对关键证据，并区分确认的问题和仍需验证的推测。
```

### 实现与验收

```text
$codex-opencode-dispatch
按已确认的需求修复这个问题，保留现有 API 和兼容行为。
将明确的实现工作交给 Worker，限制修改范围并运行相关测试；
完成后由你检查 diff 和测试断言，未经授权不要提交、推送或部署。
```

### 多个 Worker

可以让两个只读 Worker 分别调查不同模块，也可以让 Builder 完成后交给新会话的 Verifier 审核。只读 Worker 可共用一个稳定快照；并行写入必须使用互相隔离的工作区，并隔离或串行使用端口、数据库等共享资源。

一个会话同一时间只运行一轮，一个工作区同一时间只允许一个写者。Worktree 不包含原工作区的未提交修改，也不隔离凭据；不能把这两点当作已经自动解决。

## 模型与审批配置

### 固定 Worker 模型

由用户选择模型，再从实际 OpenCode 环境核实 `providerID`、`modelID` 和可选 `variant`。本机试跑使用过 OpenCode Go / DeepSeek V4.1 Flash / Max，但不能据此假设其他账号也有相同 ID 或支持 `max`。

记录已验证的绑定，并在初次派工和返工中保持一致。模型不可用时不自动换模型。运行配置未变时复用已有记录，不必每个任务重新枚举所有 provider。详细字段见 [MCP 适配说明](references/mcp-v3.md)。

### 希望不用每次人工审批

需要分别配置两层，且只针对已经授权的工作：

- **Codex 宿主层：** 为对应 MCP 服务或指定工具设置自动批准；只设置顶层 `approval_policy = "never"` 不代表 MCP 会自动获批，也可能直接拒绝调用。
- **OpenCode Worker 层：** 必要操作设为 `allow`，越界操作设为 `deny`，避免常规路径依赖 `ask`。只读调查可参考 [codex-reader 模板](templates/opencode-codex-reader.md)；实现任务需要单独确认编辑和测试权限。

模板需要授权后安装并核实有效配置，不会因复制 Skill 自动生效。`read/grep/glob` 权限也不是按文件白名单隔离的操作系统沙箱；处理私有代码时优先提供不含凭据的筛选快照。详细配置和权限止损见 [MCP 适配说明](references/mcp-v3.md)，宿主设置以 [Codex 配置参考](https://developers.openai.com/zh-Hans/docs/config-file/config-reference) 为准。

自动批准不扩大任务授权，也不能覆盖受管策略。遇到明确拒绝就停止相关操作，不通过其他工具绕过。

## 怎样减少额外开销

- 先判断是否值得派工；优先一个边界清楚的 Worker，不为小任务搭多层审核链。
- 当前上下文已有完整且有效的规则、任务说明和配置时直接复用，不重复读文件、重建提示词。
- 必须读取的准备材料成批读取；发生截断时只补缺失部分。
- 明确设置观察时限，优先有界等待，不做 `check → wait → check` 的重复查询；等待超时不等于任务失败。
- 回报只保留结论、验收覆盖、路径与检查证据，正常流程不拉取整份会话。
- Codex 验收时按文件合并相邻证据范围，但不能省略关键失败路径或必要测试。

一次性提供材料只是调用方的准备方式，不是 MCP 自动去重；这些内容仍计入模型输入。工具目录的 `essential` profile 可以减少工具定义，但不是权限控制。

### Skill 与本机 MCP 补丁的区别

本包只包含 Skill，不包含修改后的 MCP 程序，也不会修改 `node_modules`。

此前本机 MCP 另加过 reasoning 返回过滤和可选 `OPENCODE_COMPACT_RESULTS=true` 补丁。后者让 `run/fire/wait/check` 的完整报告放在 `structuredContent.text`，普通文本块只保留回执；这**不是上游 3.0.0 自带能力**。未安装相应补丁时使用上游返回格式，不要期待设置同名变量就自动生效。只支持文本结果的客户端也不应开启此补丁模式。

## 可选工具

以下命令在本 Skill 目录中运行；示例路径需替换为真实且已授权的路径。

```bash
# 检查任务契约，再生成包含 Worker 规则的提示词。
python3 scripts/prompt_contract.py lint /absolute/artifacts/task.md
python3 scripts/prompt_contract.py render /absolute/artifacts/task.md \
  --output /absolute/artifacts/worker-prompt.md

# 同一基线、同一工作区，分别在派工前后生成回执。
# 输出目录须已存在且位于被检查仓库之外。
python3 scripts/workspace_receipt.py snapshot \
  --repo /absolute/worktree --base "$BASE_SHA" \
  --output /absolute/artifacts/pre-work.json
# Worker 停止写入后，再以相同参数生成 post-work.json。
python3 scripts/workspace_receipt.py scope-delta \
  --before /absolute/artifacts/pre-work.json \
  --after /absolute/artifacts/post-work.json \
  --allow src/ --allow tests/
```

`prompt_contract.py` 不强制检查四问是否填写或是否真实成立；结构通过不代表授权、语义正确或行为通过。它不执行提示词里的命令，也不负责 MCP 派工。

`workspace_receipt.py` 用来识别工作区与范围变化，不运行测试、不证明修改者身份；忽略文件、外部状态及 submodule 内部不在完整审计范围。隐藏 Git index 标记等情况需要人工或额外证据核查。具体契约见 [工作区规则](references/workspaces.md) 和 [验收规则](references/verification.md)。

## 验证与效果边界

已有离线工具与规则连接测试 **104 项通过**；另外准备的 **84 个行为场景并未全部执行**，二者不能混为一谈。可自行复验：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_bundle.py
```

2026-09-18 做过真实单 Builder 试跑，以及“Codex 直接审查”和“Codex 经 MCP 委派后验收”的只读对照。最近一次委派流程相对前一轮，总调用 **24 → 10**，准备文件读取 **10 → 0**；但未缓存输入加输出 token **增加约 4.6%**，含缓存累计 token 仅减少约 5.7%。

与同轮直接 Codex 审查相比，委派方案仍更慢且耗用更多 Codex token，验收也有漏项。因此目前能确认的是调用减少，**不能宣称质量完全等价或稳定节省 token**。

这些是特定环境的单任务样本，使用了本机 MCP 补丁；各轮输入包装也有变化。统计不包含外围准备和主控额外复核，Worker 用量另计，不等于费用或订阅额度。私有项目源码、原始审查报告和会话日志不随本包发布。历史记录见 [验证说明](docs/VALIDATION.zh-CN.md)；其中早期“未执行”描述只代表当时阶段，最新状态以本节为准。

## 目录导航

- [SKILL.md](SKILL.md)：主控实际执行规则，按需引导加载细节。
- [references](references/)：MCP、任务协议、权限、工作区、状态恢复和验收说明。
- [templates](templates/)：通用 Worker 规则、角色任务、返工、台账和只读 agent 模板。
- [examples/prompts](examples/prompts/README.md)：已填写的虚构示例，不可当作真实项目证据。
- [scripts](scripts/) 与 [tests](tests/)：可选离线工具及其单元测试。
- [evals](evals/README.md)：待执行的行为评测与真实闭环方案。
- [docs](docs/)：历史研究、来源和阶段验证记录，不是每次派工的必读材料。
- [MANIFEST.json](MANIFEST.json)：分发文件的大小和 SHA-256 清单，不包含清单自身。

开始时先读 [SKILL.md](SKILL.md)，需要配置再读 [MCP 适配说明](references/mcp-v3.md)，需要写任务再读 [模板入口](templates/task-brief.md)。不要一次加载整个包。
