# Codex OpenCode Dispatch

让 **Codex 负责判断与验收，OpenCode Worker 负责边界清楚的调查和实现**。

这是一个可跨项目复用的 Codex Skill，目标是减少主控重复劳动，同时保留工程质量检查。包内同时附带可构建的 MCP 源码；Skill 规则本身不是服务、模型代理或安全沙箱，也不保证每个任务都能节省 token。

- Skill 版本：`2.4.0`；本文更新于 2026-09-21。
- 内置底座：[AlaeddineMessadi/opencode-mcp](https://github.com/AlaeddineMessadi/opencode-mcp) `v3.0.0` 的修改版 `3.0.0-codex.1`，源码在 [mcp/opencode-mcp](mcp/opencode-mcp/)。
- 正常运行入口：[SKILL.md](SKILL.md)。README 面向使用者，不需要每次派工都加载。

## 适合做什么

**仅限人类明确要求使用 `codex-opencode-dispatch` 时启用。** 普通任务默认禁止使用本 Skill，也禁止绕过 Skill 通过 MCP、CLI、API 或其他智能体调用 OpenCode 作为子智能体；任务复杂、节省 token 或工具自动批准都不是授权。

仅讨论、检查、安装或修改本 Skill 不等于授权启动 Worker。**一旦人类明确启用，授权会在当前 Codex 对话和同一项目/工作区内持续有效**；后续开发、调研和测试无需重复写 `$codex-opencode-dispatch`，Codex 应按需主动派工。用户撤回、对话结束或切换项目/工作区后失效。

`allow_implicit_invocation` 仍为 `false`：它阻止首次授权前自动启用，不阻止已经明确授权后的连续工作。每个新请求仍受自身范围、权限、数据共享、模型和验收要求约束。

明确授权后，适合委派：

- 调查范围明确、工作量较大的代码问题，返回可定位的证据。
- 按已确定的需求修改代码、补充测试，再由 Codex 独立验收。
- 将相互独立的问题交给多个 Worker 分析，由 Codex 汇总。
- 让实现者和审核者使用不同会话，避免把“Worker 已完成”当成“已经验收”。

授权后，只要派工能减少有意义的代码阅读、修改、测试或重复准备，就优先交给 Worker。只有已定位的一行修改、单条已知命令、Worker 不可用/不兼容或派工开销明显更高时才直接完成，并简要记录原因。业务语义、公共接口、安全边界、发布和合并等关键决定仍由 Codex 在用户授权范围内负责。

## 工作方式

1. **确定边界。** 读取项目规则，确认目标、代码快照、允许修改的范围和验收要求。
2. **派一次清楚的任务。** 把必要上下文、固定决定、检查项和停止条件交给 Worker；不发送整段聊天历史。
3. **保留任务身份。** 记录 job/session/message ID，等待已有任务，不因超时盲目重派。
4. **独立验收。** Codex 核对实际代码、关键失败路径、测试断言及原始需求覆盖。
5. **窄范围返工或交付。** 返工只补具体差异；权限不足、范围冲突或证据不足时报告阻塞。

每个独立修改先回答四个问题：属于当前需求吗？不改会阻塞什么？是不是最小正确修改？是否保留已有契约？小任务用一行 `Boundary:` 即可，不强制建立完整台账。

Codex 维护 `项目/工作区 + 工作流 + 模型/variant + 角色` 的 session 映射。相同工作流的连续任务和返工显式传入已有 `sessionId`，每轮使用新的 job/message ID；同一对话里的无关工作流新建 session，但不丢失授权。并行 Worker 与独立 Verifier 必须使用不同 session，同一 session 不并发两个回合。

Scout、Designer、Builder、Verifier 是任务角色，不是自动安装好的 OpenCode agent。`ocw/1` 是放在 MCP `prompt` 字符串中的任务约定，不是新的 MCP 参数。

## 安装

### 1. 准备运行环境

需要 Codex、Node.js 22+ 和 npm、可用的 OpenCode，以及你自己的模型访问权限。OpenCode 的安装和模型登录按 [OpenCode 官方文档](https://opencode.ai/docs/) 完成；本次本地构建验证使用 Node.js 24.18.0，上游 SDK/模拟服务契约为 OpenCode 1.18.31，不代表所有其他版本均已验证。

下载本 Skill 已包含修改后的 MCP 源码，不需要再复制本机的 `node_modules` 补丁。不过**仍需首次安装依赖、构建、连接 OpenCode 并注册 MCP**，不会因复制文件自动登录账号或修改全局配置。

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

### 3. 构建包内 MCP

在安装后的 Skill 目录中执行：

```bash
cd mcp/opencode-mcp
npm ci --ignore-scripts --no-audit --no-fund
npm run build
```

`npm ci` 使用随包锁文件安装依赖；显式构建生成 `dist/index.js`。保留开发依赖直到编译和测试完成。不要改用 `npx -y opencode-mcp`：它运行 npm 上游包，不包含这里的补丁。

需要网络下载依赖；本包不是完整离线运行包。源码和锁文件纳入版本控制，`node_modules/`、`dist/`、账号凭据和运行日志不发布。依赖下载一直不返回时，可用 `npm ci --ignore-scripts --no-audit --no-fund --fetch-retries=0 --fetch-timeout=30000` 重试并查看 npm 错误，不要为了安装成功盲目升级依赖。

### 4. 连接 OpenCode，再注册到 Codex

如果已有可用的本机 OpenCode 服务，复用它；不要重复启动或停止别的任务占用的服务。没有时在授权的项目目录启动：

```bash
opencode serve --hostname 127.0.0.1 --port 4096
```

在另一终端注册 MCP。**仅用于尚未配置 `opencode` 的首次安装**；替换下面两个绝对路径。已有配置时只更新原条目的 `command`、`args` 和所需环境变量，保留其他字段，不新增重复连接：

```bash
codex mcp add opencode \
  --env OPENCODE_BASE_URL=http://127.0.0.1:4096 \
  --env OPENCODE_AUTO_SERVE=false \
  --env OPENCODE_TOOL_PROFILE=essential \
  -- /absolute/path/to/node /absolute/path/to/codex-opencode-dispatch/mcp/opencode-mcp/dist/index.js
```

桌面应用的 PATH 不一定等于终端 PATH，尤其使用 nvm 时，建议 `command` 写 Node 可执行文件的绝对路径。`OPENCODE_AUTO_SERVE=false` 表示 MCP 连接现有服务，不代管它的生命周期。

重连或重启 Codex 后，确认当前会话能看到 MCP 工具、初始化版本为 `3.0.0-codex.1`；必要时用 `opencode_setup` 检查服务和目录。`codex mcp list` 只能证明配置存在，不能代替实际连接验证。服务器上的项目路径必须真实存在；MCP 不会自动上传本机文件到远端。注册方式见 [Codex MCP 官方说明](https://developers.openai.com/codex/mcp/)。

客户端确认能把 `structuredContent` 交给主控后，再在该 MCP 的环境中设置 `OPENCODE_COMPACT_RESULTS=true` 并重连。默认关闭是为了兼容只读取普通文本的客户端。不要把未确认支持结构化结果的客户端直接切到紧凑模式。

安装与运行分开：本仓库不自动执行全局注册、不改审批策略、不启动真实 Worker。上面的命令由使用者明确执行。

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

## 内置 MCP 详解

### 来源和分发方式

本目录是 **vendored fork（随 Skill 分发的源码快照及修改）**，不是 GitHub 的独立 Fork 仓库，也不是 submodule；普通 clone 或下载 ZIP 即可取得源码，不需要 `--recurse-submodules`。

- 上游：[AlaeddineMessadi/opencode-mcp](https://github.com/AlaeddineMessadi/opencode-mcp)，标签 `v3.0.0`。
- 固定源提交：[`6f1f62fd6c151377e09f4fe95bed58eb48c6196b`](https://github.com/AlaeddineMessadi/opencode-mcp/commit/6f1f62fd6c151377e09f4fe95bed58eb48c6196b)。
- 包内版本：`3.0.0-codex.1`；包名保留 `opencode-mcp`，标记 `private: true` 防止误发 npm。
- 保留上游 [MIT LICENSE](mcp/opencode-mcp/LICENSE)、作者信息、源码、锁文件、文档与原有测试；来源和补丁摘要见 [mcp/UPSTREAM.json](mcp/UPSTREAM.json)。

GitHub Fork 不能作为一个仓库直接“挂在文件夹下”；这里选择源码快照，满足“下载 Skill 同时拿到可修改的 MCP”的目标。上游文档中的 npm 安装示例属于原版；本包安装以本 README 为准。原有全局 npm 安装不会因此自动更新。

### 各组件负责什么

调用链是：**Codex 按 Skill 分工 → stdio MCP → OpenCode HTTP 服务 → 已配置模型/工具 → MCP 返回结果 → Codex 验收**。

- **Skill** 决定什么时候委派、任务边界、模型绑定、如何等待和验收；它不启动常驻 Worker，也不强制执行权限隔离。
- **MCP** 把工具调用转换为 OpenCode API 请求，提供会话、任务状态、权限/问题交互和结果回收；不是模型提供商或通用调度集群。
- **OpenCode** 管理实际会话和工具执行，通过用户自己的 provider/订阅调用模型。多个 Worker 是不同会话，不需要安装多个 MCP；共享服务不等于工作区隔离。
- **Codex** 决定是否接受结果；`completed` 只说明任务执行结束，不代表代码合格或已发布。

工具的准确参数见 [适配说明](references/mcp-v3.md) 与 [包内工具目录](mcp/opencode-mcp/docs/tools.md)。常用 `run` 边执行边有界观察、`fire` 后台提交、`wait/check` 观察已有任务、`job_get` 恢复结果；始终保存 job/session/message ID。超时先恢复状态，不盲目重派；同一会话不并发两个回合。

### 补丁一：去掉返回中的 reasoning 消息片段

此前仅修改了本机已编译 JavaScript，本次迁入 TypeScript 源码，重新构建后仍生效：

- `src/helpers.ts` 在消息输出边界移除 `parts[].type === "reasoning"`，文本摘要也使用该过滤结果。
- `src/tools/workflow.ts`、`src/tools/message.ts` 覆盖问答、回复、会话/消息查询、命令/终端执行结果和 provider 测试返回；`src/resources.ts` 覆盖 session message 资源。
- `src/jobs.ts` 覆盖任务观察结果，以及可识别、关联正确的旧终态缓存的公开返回；不重写旧缓存文件或 OpenCode 原始会话。

保留最终答案、工具输出、错误、权限/问题请求、任务身份、消息元数据和 token 数值；不递归删除业务 JSON 中恰好名为 `reasoning` 的字段，也不改变模型的思考程度。

**它是减少主控输入噪声的输出过滤，不是全面脱敏器。** 原始事件、工具输出内部的任意内容和服务端历史不在全面清洗承诺内。源码发送给模型之前仍需确认授权、筛选凭据；此补丁不减少 Worker 已经产生的 reasoning 用量。

### 补丁二：可选紧凑结果，减少报告重复

仅当 MCP 环境设置 `OPENCODE_COMPACT_RESULTS=true` 时启用，逻辑在 `src/mcp-server.ts`：

- 普通 `opencode_run/fire/wait/check` 调用的完整报告放在 `structuredContent.text`；普通 `content` 文本只给简短回执，非文本附件保留。
- 仅删除关联身份匹配、且已完整出现在报告中的消息 text part。未合并文本、工具结果、错误、结构化业务数据不截断。
- 保留状态、ID、待处理输入、错误与元数据，新增 `responseMode: "compact"` 和 `fullResultTool: "opencode_job_get"`。
- `opencode_job_get` 保留完整恢复格式（reasoning 消息过滤仍生效）；不要每次正常结束后再额外拉取同一份报告。
- 默认模式保留原版返回结构；原生 MCP Tasks 结果不做紧凑化，协议级 `input_required` 也不被改写。

这不是上游 3.0.0 自带的开关。返回字节减少不等于 Codex 必然按同样比例省 token；客户端是否把结构化结果送入模型、是否重复包装内容也会影响结果。文本客户端保持默认模式。

### 配置、权限与数据边界

- `OPENCODE_BASE_URL` 选择 OpenCode 服务；默认本机 `http://127.0.0.1:4096`。未经独立的认证和网络保护，不把无认证服务公开到公网。
- `OPENCODE_TOOL_PROFILE=essential` 当前提供 25 个常用工具，减少目录负担；它不是权限白名单，普通委派仍可能执行编辑或命令。
- `OPENCODE_DEFAULT_PROVIDER` 与 `OPENCODE_DEFAULT_MODEL` 必须成对设置，且只是默认值，不是硬锁。模型/variant 以实际账号发现结果和用户选择为准，包内不附订阅或密钥。
- `OPENCODE_TASK_STORE` 可指定任务记录目录，默认规则见 [上游配置文档](mcp/opencode-mcp/docs/configuration.md)。记录可能含代码和结果，保存在私有目录，不能提交仓库；默认句柄 24 小时后过期，过期不代表远端会话被取消。
- 自动审批仍有 Codex 宿主与 OpenCode 工具权限两层，按前文分别设置；内置补丁不自动批准权限、不放宽沙箱、不修改全局设置。

### 验证和升级

从 `mcp/opencode-mcp` 运行以下命令：

```bash
npm test
npm run test:codex-stdio
npm run docs:check
```

2026-09-18 在 Node.js 24.18.0 下验证：上游基线 **503 通过、3 跳过**；包内修改版 **539 通过、3 跳过**，新增 36 项覆盖过滤、业务数据保留、错误/权限/状态保留、旧缓存和紧凑模式。3 项跳过沿用上游，没有为本次修改新增跳过。

两次真实 MCP stdio 进程测试分别覆盖默认/紧凑模式，使用本机合成 HTTP 服务完成 `run → wait → job_get`；工具文档与目录校验也通过。这里“真实 stdio”不等于真实模型：**本次没有调用模型、连接 AWS，或做新的 token 节省对照实验**。

上游升级时不要直接覆盖本目录：先选择具体 tag/commit，在临时目录检查与现有基线的差异；逐项迁移这两组补丁，保留原有回归，再跑上述命令及 Skill 检查。确认后更新 `UPSTREAM.json`、包内版本、README 与分发清单；依赖变化要由锁文件明确记录。无需另建自动升级框架。

切换运行版本前先等待已有任务结束，保存旧配置和构建；只修改原 MCP 条目指向新 `dist/index.js` 并重连。若新连接异常，恢复旧命令和环境后重连，不删除旧任务记录，也不盲目重发任务。本次源码分发不替你执行这一步。

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

Skill 离线工具与规则连接测试 **108 项通过**；另外准备的 **92 个行为场景并未全部执行**，二者不能混为一谈。可自行复验：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_bundle.py
```

`check_bundle.py` 只扫描 Skill 自有文件，不递归读取内置 MCP/其安装依赖；它仍检查 Skill 文档指向 MCP 的本地链接。MCP 源码必须单独运行上一节的构建、回归和 stdio 检查，不能用 Skill 结构检查替代。

2026-09-18 做过真实单 Builder 试跑，以及“Codex 直接审查”和“Codex 经 MCP 委派后验收”的只读对照。最近一次委派流程相对前一轮，总调用 **24 → 10**，准备文件读取 **10 → 0**；但未缓存输入加输出 token **增加约 4.6%**，含缓存累计 token 仅减少约 5.7%。

与同轮直接 Codex 审查相比，委派方案仍更慢且耗用更多 Codex token，验收也有漏项。因此目前能确认的是调用减少，**不能宣称质量完全等价或稳定节省 token**。

这些是特定环境的单任务样本，使用了本机 MCP 补丁；各轮输入包装也有变化。统计不包含外围准备和主控额外复核，Worker 用量另计，不等于费用或订阅额度。私有项目源码、原始审查报告和会话日志不随本包发布。历史记录见 [验证说明](docs/VALIDATION.zh-CN.md)；其中早期“未执行”描述只代表当时阶段，最新状态以本节为准。

## 目录导航

- [SKILL.md](SKILL.md)：主控实际执行规则，按需引导加载细节。
- [references](references/)：MCP、任务协议、权限、工作区、状态恢复和验收说明。
- [templates](templates/)：通用 Worker 规则、角色任务、返工、台账和只读 agent 模板。
- [examples/prompts](examples/prompts/README.md)：已填写的虚构示例，不可当作真实项目证据。
- [scripts](scripts/) 与 [tests](tests/)：可选离线工具及其单元测试。
- [mcp/opencode-mcp](mcp/opencode-mcp/)：固定版本的 MCP 源码、锁文件、补丁测试与原有上游文档；[UPSTREAM.json](mcp/UPSTREAM.json) 记录来源。
- [evals](evals/README.md)：待执行的行为评测与真实闭环方案。
- [docs](docs/)：历史研究、来源和阶段验证记录，不是每次派工的必读材料。
- [MANIFEST.json](MANIFEST.json)：分发文件的大小和 SHA-256 清单，不包含清单自身。

开始时先读 [SKILL.md](SKILL.md)，需要配置再读 [MCP 适配说明](references/mcp-v3.md)，需要写任务再读 [模板入口](templates/task-brief.md)。不要一次加载整个包。
