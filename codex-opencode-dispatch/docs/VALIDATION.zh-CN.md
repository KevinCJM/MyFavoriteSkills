# v2.3.0 验证记录

## 已实际执行

本版在 v2.2.0 的 97 项回归基础上，加入 Git 隐藏索引标记、派工前后范围差分、`variant`
绑定与 compact 流程简化的覆盖。完整离线测试结果为 **104 项通过**：

- **45** 项提示词契约、模板与渲染测试；
- **41** 项 Git 工作区回执测试；
- **18** 项四问准入、MCP/variant 与流程连接检查。

新增的关键回归覆盖：

- `assume-unchanged` 内容改变时不能误报完整快照通过；
- `skip-worktree` 条目必须触发人工核查；
- 派工前已有越界本地修改、Worker 未触碰时不应误判；
- Worker 在派工期间又修改原有脏文件时仍应被差分发现；
- `scope-delta` CLI 的前后回执行为；
- MCP v3.0.0 支持可选 `variant`，但 Skill 不擅自硬编码 `max`；
- compact 任务不需要 C-ID 表或 ledger，而仍保留最小 Boundary / Acceptance / Check。

运行命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -v
PYTHONDONTWRITEBYTECODE=1 python scripts/check_bundle.py
```

实际单元测试输出：[unit-tests.log](unit-tests.log)。包结构结果：[bundle-check.json](bundle-check.json)。
结构检查包括 Skill 元数据、1500-word 核心预算、Markdown 本地链接与围栏、Python 语法、JSON、
角色示例 lint，以及行为案例引用。结构通过不代表真实 Agent 已遵循规则。

## 两个 Git 回执缺陷的验证边界

### 隐藏 index hint

`workspace_receipt.py` 现在读取 `git ls-files -v -z`。发现 `assume-unchanged` 或
`skip-worktree` 时只将结果升级为 `manual_review_required`；它**没有**尝试变成完整文件系统审计器。
这是有意的最小修复。

### 派工前已有修改

推荐流程：

```text
pre-work receipt -> Worker -> post-work receipt -> scope-delta(pre, post)
```

`scope-delta` 判断的是 pre→post 时间窗口内的新文件状态变化，不是进程身份取证。如果用户、另一个
Agent 或后台工具同时写同一目录，无法仅靠回执证明具体作者，因此“单工作区单写者”规则仍然必要。

## Variant 的验证边界

本版记录：

- provider；
- model；
- optional variant；
- `effective_variant_verified`。

`opencode-mcp@3.0.0` 接口存在 `variant` 参数，不等于任何 provider/model 都保证支持或实际应用
`max`。因此没有把 `max` 写死。若操作员明确绑定某 variant，应在真实 OpenCode/provider 环境核对
其可用性和实际生效，再把 `effective_variant_verified` 设为 true。

## 打包时尚未执行

- 未连接用户真实 Codex、`opencode-mcp@3.0.0`、OpenCode、DeepSeek 环境；
- **84 个行为案例仍未执行**；
- [live-smoke-plan.md](../evals/live-smoke-plan.md) 中三个闭环场景仍未执行；
- 未测真实 Codex/Worker token、耗时、首次验收率、返工率、漏检率或成本；
- 没有把 104 项脚本测试当成 104 次 LLM 行为通过；
- 提示词约束仍不是运行时硬权限。

下一阶段优先执行三个真实闭环，而不是继续增加治理规则：

1. 单 Builder 修复；
2. 两个并行只读 Scout；
3. Builder 完成后用新 Session 独立 Verifier。

需要记录真实 token、MCP 调用数、返工次数、误报/漏检与最终缺陷，再决定是否继续调整策略。

## 本版没有声称的事情

- 用户此前提出过 `variant=max`；本版离线测试没有声称它已在目标模型上实测；
- 没有声称 `scope-delta` 能进行作者归因；
- 没有声称 `assume-unchanged` / `skip-worktree` 下仍可自动完整审核；
- 没有声称结构测试证明实际 token 一定下降或质量一定提升。

外部审核意见的逐项处理见 [AUDIT_RESPONSE.zh-CN.md](AUDIT_RESPONSE.zh-CN.md)。

## 2026-09-18 本机追加试跑

- 单 Builder → Codex 验收已通过，使用已安装 MCP 3.0.0 的真实 stdio 调用和 OpenCode 1.18.31。
- 固定 OpenCode Go / DeepSeek V4.1 Flash / Max；两轮响应元数据均匹配，未修改全局模型配置。
- 首轮因临时读取权限路径不匹配而阻塞；修正配置后复用同一 Session 完成，未盲目重派。
- Codex 独立重跑样例测试 3/3、额外验收 5/5；scope-delta 仅包含两个授权文件，原有用户修改未变。
- 104 项离线测试重新通过。两个并行 Scout、独立 Verifier 和 84 个行为案例仍未执行。
- 未取得 Codex token 或同质量对照，不能宣称节省比例。现场发现 MCP 格式化返回包含 reasoning 文本；试跑当时仅调用器过滤，未修改 MCP 包。

## 2026-09-18 返回过滤与运行说明修订

- MCP 3.0.0 本地补丁已过滤消息正文和结构化结果中的 reasoning transport parts，兼顾旧任务缓存与消息资源；保留最终报告、错误、任务关联字段及数值用量。不递归删改合法业务 JSON，也不改 OpenCode 原始会话。
- 23 项针对性 Node 测试通过：真实 MCP 模块与工具处理器搭配模拟 OpenCode 响应，覆盖 run/wait/check、消息接口、缓存、错误、待授权、超时和结构化答案；不是新的模型实跑。
- 真实 stdio 协议复核通过：25 个工具可发现，run → wait → job_get 的完整返回均无合成 reasoning 标记；后端为本机模拟服务，模型调用数为 0，临时进程已退出。Skill 原有 104 项测试、包结构检查和 Skill 校验重新通过。
- Worker 规则明确：权限拒绝立即停止该操作，只报告一个具体错误；不得尝试等价路径或其他工具绕过。待授权请求仍走授权输入流程。
- MCP 参考补充配置复用与失效条件，沿用既有任务记录，不增加调度器或配置注册表。
- 本次不执行新的付费 Worker 任务；节省效果留给后续实际工作量、同等质量的对照任务验证。
