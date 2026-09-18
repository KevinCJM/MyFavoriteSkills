# v2.3.0 外部审核意见复核与处理

日期：2026-09-18

## 结论

外部审核的两个 Git 回执问题属实，已做最小修复；流程简化建议属实且已收敛普通任务管理成本；
“v3.0.0 支持 variant”属实，用户此前也提出了 OpenCode Go + DeepSeek V4.1 Flash + Max。
通用模板不写死 `max`；本用户按该选择派工时明确绑定并传递 `variant: "max"`，包括返工。
真实闭环验证建议合理，打包时只增加了最小 smoke 计划，不继续扩张运行时规则。

## 1. assume-unchanged / skip-worktree 漏检

**判断：属实。**

原 `workspace_receipt.py` 主要依赖 `git status` / `git diff` 获取变化。Git 的 index hint
`assume-unchanged` 和 `skip-worktree` 可能让这些命令不再完整反映工作树内容。Git 官方
`git ls-files -v` 文档说明：小写状态表示 assume-unchanged，`S` 表示 skip-worktree。

### 修复

- snapshot 增加只读 `git ls-files -v -z` 检查。
- 遇到相关 entry，加入：
  - `assume_unchanged:<path>`
  - `skip_worktree:<path>`
- 任一此类标记导致范围结果为 `manual_review_required`，而不是假装完整审计通过。
- 快照前后也比较该 index 可见性输出，降低捕获期间 flag 改变造成的假稳定。

没有尝试开发完整文件系统审计器，符合最小改造原则。

## 2. 派工前已有本地修改被误判为 Worker 越界

**判断：属实。**

原 `scope(receipt)` 判断的是“从任务基线提交到当前候选的全部变化”。如果用户在派工前已经有
未提交修改，这些变化本来就存在，但会被当成候选变化一起检查，因此可能错误归因给 Worker。

### 修复

新增 `scope-delta`：

```text
pre-work receipt
      ↓
Worker 执行
      ↓
post-work receipt
      ↓
scope-delta(pre, post)
```

它只对 pre→post 期间新发生的文件状态变化做 allow/deny 检查；派工前已有、且 Worker 没有碰的
用户修改不会被判为越界。如果 Worker 又修改了那个原有脏文件，内容指纹变化仍会被发现。

注意：这是“时间窗口变化”判断，不是进程身份取证；如果人和多个 Agent 同时写同一工作区，
仍无法仅靠 Git 回执证明具体是谁改的，所以单工作区单写者规则继续保留。

## 3. `variant: "max"`

**判断：variant 能力缺口属实；此前对用户 Max 意图的判断遗漏了对话上下文。**

属实部分：AlaeddineMessadi `opencode-mcp@3.0.0` 生成的 tool schema 确实在
`opencode_ask`、`opencode_reply`、`opencode_run`、`opencode_fire` 暴露可选 `variant` 字段。

用户此前提出过 **OpenCode Go + DeepSeek V4.1 Flash + Max**，不应描述成“从未要求 Max”。
应区分操作者的实际选择与通用模板默认值：模板保留可选 variant，本用户按该选择试跑和返工时
显式传递 `variant: "max"`，不得静默降级或换模型。

此外，“接口接受 variant 字符串”不等于任何 provider/model 都一定支持某个值。实际模型/provider
需要验证该 variant 是否暴露/生效。

### 修复

- ledger 的 `model_binding` 增加 `variant` 与 `effective_variant_verified`。
- 项目 profile 增加 Worker variant 字段。
- MCP adapter 将 `variant?` 加入 run/fire/reply 的真实参数映射。
- 如果操作员明确选择 `max` 或其他 variant，派工和返工要一致传递并验证；否则保持 unset。
- 禁止 Codex 自己“为了更强”临时换 variant。

## 4. 四问与任务台账过重

**判断：合理，但 v2.2 已经部分做到。**

v2.2 已规定简单 one-shot 不需要 ledger，不过 compact brief 仍要求 C-ID 四问行，容易让轻量修复的
管理成本偏高。本版进一步区分：

### Compact / 低风险

只维护：

- Goal
- Scope
- 一行 `Boundary:`（用一句话覆盖四问）
- 一个或少量 Acceptance / Check
- Return

**不创建 C-ID 表，不创建 ledger。**

### Governed / Full

以下情况才使用完整 C-ID / AC / V / F 与 ledger：

- medium/high risk；
- 合同/兼容性敏感；
- 多 Worker；
- 依赖/共享接口复杂；
- 长任务、可能上下文压缩或中断；
- 返工需要精确追踪。

AC/V 保留在 compact 中，因为一个短 ID 的成本很低，却能显著减少“修的是哪条要求、验证的是哪条要求”
的歧义。没有继续把 compact 简化到完全不可追踪。

## 5. 真实闭环验证优先于继续堆规则

**判断：合理。**

本版不新增调度器、数据库或新的 Agent 层，只增加一个最小的真实环境 smoke 计划：

1. 单 Builder 修复；
2. 两个 Worker 并行只读调查；
3. Builder 完成后独立 Verifier。

记录：

- Codex token；
- Worker token；
- elapsed time；
- rework rounds；
- 漏检/误报；
- 最终是否出现验收后缺陷。

打包时这些场景**尚未在用户真实环境执行**；后续单 Builder 试跑结果见
[验证记录](VALIDATION.zh-CN.md)，不能据此把另外两个场景也算作通过。

## 保留不变的关键机制

审核员建议保留的以下机制继续保留：

- 单工作区单写者；
- 普通返工复用原 Session；
- 独立审核使用新 Session；
- timeout / unknown 不盲目重派；
- Worker 完成不等于任务完成；
- 最终验收权属于 Codex。
