---
name: rss-digest-writer
description: 从 Reddit、YouTube、WeChat RSS 和通用 RSS 聚合 AI 相关热门信息，并由 Codex 自己完成筛选、摘要和记录归档。不需要配置任何外部 LLM API。当用户要求“找 AI 热门信息”“追踪 Reddit/YouTube/公众号/RSS 更新”“整理近两天 AI 圈热点”时触发。
allowed-tools: Bash,Write,WebSearch,WebFetch
---

# AI Trend Recorder

这是一个纯 Codex 技能。

核心原则：

共享与移植约束：

- 技能必须随目录整体分发，至少包含 `SKILL.md`、`scripts/rss_collect.py` 和 `references/`。
- 不要依赖作者本机路径；从技能目录读取 `references/default-ai-source-pack.json` 和 `references/local-wechat-rss-feeds.txt`。
- 默认只依赖 Python 标准库、网络访问、Codex 网页检索/抓取能力。
- `local-wechat-rss-feeds.txt` 是用户私有占位文件；共享前不得写入个人公众号 RSS、token 或内网地址。
- Reddit、YouTube、公众号 RSS 都可能受网络环境影响；失败时降级为网页搜索、公开页面抓取或标记为弱信号。

- 不要要求用户配置 OpenAI、DeepSeek、Firecrawl 之类的 API。
- 辅助脚本只负责拉取 RSS 兼容源并输出结构化 JSON。
- Reddit、YouTube 这类非稳定 feed 源，优先用现成 MCP；没有 MCP 时改用网页能力补抓。
- 热门度判断、去重、筛选、总结和记录整理必须由 Codex 在当前会话里完成。
- 不要扩展到发布、飞书、图片和公众号后台链路，除非用户另提要求。

## 触发信号

以下表达都应优先使用本技能：

- 找 AI 相关热门信息
- 看近两天 AI 圈发生了什么
- 追踪 Reddit / YouTube / 公众号 / RSS 更新
- 做 AI 热点监测笔记
- 根据这些 RSS 和社媒来源做总结记录
- 看看最近有哪些 AI 热门帖子 / 视频 / 文章

如果用户只给了单篇文章链接，而不是监测需求，不用本技能。

## 默认来源

本技能不再只依赖单一 RSS feed 列表，而是用一个默认 source pack：

- [default-ai-source-pack.json](references/default-ai-source-pack.json)

它包含四类来源：

1. `RSS 聚合`
   - AI 厂商博客
   - 研究博客
   - arXiv 论文 feed
2. `YouTube`
   - AI 频道页面或上传 feed
3. `Reddit`
   - AI 相关 subreddit
4. `WeChat RSS`
   - 用户本地提供的公众号 RSS 列表

本地公众号 RSS 文件路径固定为：

- [local-wechat-rss-feeds.txt](references/local-wechat-rss-feeds.txt)

默认行为：

1. 使用 source pack 中的 RSS 兼容源跑辅助脚本。
2. 自动尝试合并本地 `WeChat RSS` 文件中的 feed。
3. 把 `Reddit` 和 `YouTube` 作为延迟源保留下来，由 Codex 后续用 MCP 或网页能力补抓。
4. 如果用户没有指定时间范围，默认查近 `2` 个自然日。

注意：

- 这里的“热门”是编辑性判断，不是平台真实流量榜。
- Reddit 在部分网络环境下对 RSS 抓取不稳定，所以不要把 Reddit 绑定死在 feed 流程里。
- WeChat 默认不内置公共 RSS 地址，避免依赖不稳定的第三方公开转换服务。

## 工作流

1. 判断是不是“AI 热门信息 / 多源监测”请求。
2. 若是，默认启用 source pack，并合并用户额外提供的 feeds。
3. 若用户未指定时间范围，默认使用近 `2` 天窗口。
4. 先用辅助脚本拉取 RSS 兼容源：
   - 通用 RSS
   - 可直接解析的 YouTube upload feeds
   - 本地 WeChat RSS
   - 默认每个来源只先保留少量候选，避免单一高频源挤满结果
5. 读取脚本输出中的 `deferred_sources`。
6. 对 `deferred_sources`：
   - 若当前环境已有对应 MCP，优先用 MCP
   - 否则改用网页搜索和定点打开补抓
7. 合并全部候选内容后，由 Codex 自己完成：
   - 去重与降噪
   - 热门度判断
   - 相关性判断
   - 摘要提炼
   - 主题归类
   - 结构化记录整理
8. 如果用户要文件，就落成 Markdown 或 JSON；否则直接在回复里给结果。

## 来源策略

### RSS / WeChat RSS

这部分走辅助脚本。

适合：

- 博客
- 研究 feed
- arXiv
- 用户自己通过 `we-mp-rss` 或类似工具转出来的公众号 RSS

### Reddit

优先顺序：

1. 如果当前环境有 Reddit MCP，优先用它。
2. 否则用网页搜索和公开页面补抓。

默认关注的 subreddit 见 source pack。优先看：

- `r/OpenAI`
- `r/LocalLLaMA`
- `r/MachineLearning`
- `r/singularity`

如果网页抓取结果很多，优先看：

- 最近 `2` 天
- 讨论密度高的帖子
- 明显对应产品发布、模型更新、重要论文和工具链变化的帖子

### YouTube

优先顺序：

1. 如果 source pack 里给了可用的 upload feed，先交给脚本。
2. 如果没有可用 feed，改用网页能力查看默认频道近两天视频。

重点看：

- 官方 AI 机构频道
- 高信号 AI 研究/工程频道
- 与模型发布、基准、工程实践、论文解读直接相关的视频

## 热门度判断

当用户要求“热门信息”时，Codex 按下面的优先级综合判断：

1. 最近 `2` 天或用户指定区间内的新内容优先。
2. 多来源同时覆盖的主题优先。
3. Reddit 讨论热、YouTube 快速跟进、博客同时发文的主题优先。
4. 大模型发布、重要论文、重大产品发布、基础设施变化优先。
5. 技术细节密度高、后续影响大的内容优先。
6. 纯营销、轻量活动、招聘和无实质信息的内容降权。

不要把“热门”理解为精确流量指标；这是跨来源聚合后的编辑性判断。

## 时间范围规则

- 用户未指定区间且请求 AI 热点：默认 `近 2 天`
- 用户指定 `今天/昨天/某日`：按指定日期
- 用户指定 `从 A 到 B`：按明确区间
- 用户只说“最新”：抓最新若干条

优先用脚本参数表达范围：

- `--days-back 2`
- `--date YYYY-MM-DD`
- `--date-from YYYY-MM-DD --date-to YYYY-MM-DD`

## 关键约束

- 不要向用户索要任何 LLM API key。
- 不要把脚本输出直接当成最终内容交付。
- 默认保留来源链接，便于用户追溯。
- 当 feed 很多时，先把 RSS 兼容候选控制在 8 到 15 条。
- 默认按来源做软限额，避免 arXiv 之类的高频源独占候选。
- Reddit 和 YouTube 只补抓最关键的一小批，不要无上限展开。
- 不要写成日报、专栏、文章或综述体；默认输出为摘要列表、主题要点和记录条目。
- 如果用户要“热门信息”，结果中先给热点条目，再给主题归纳。

## 辅助脚本

先定位脚本：

```bash
PYTHON_BIN="${PYTHON_BIN:-python3}"
RSS_COLLECT_SCRIPT="${RSS_COLLECT_SCRIPT:-}"
if [ -z "$RSS_COLLECT_SCRIPT" ]; then
  for candidate in \
    "${CODEX_HOME:-$HOME/.codex}/skills/rss-digest-writer/scripts/rss_collect.py" \
    "$HOME/.codex/skills/rss-digest-writer/scripts/rss_collect.py"
  do
    if [ -f "$candidate" ]; then
      RSS_COLLECT_SCRIPT="$candidate"
      break
    fi
  done
fi
[ -n "$RSS_COLLECT_SCRIPT" ] || { echo "未找到 rss_collect.py"; exit 1; }
```

默认多源抓法：

```bash
"$PYTHON_BIN" "$RSS_COLLECT_SCRIPT" \
  --use-default-ai-sources \
  --days-back 2 \
  --limit 15 \
  --fetch-content \
  --content-chars 8000 \
  --output ./tmp/ai-trend-sources.json
```

默认来源 + 用户自带 feeds：

```bash
"$PYTHON_BIN" "$RSS_COLLECT_SCRIPT" \
  --use-default-ai-sources \
  --feeds-file ./feeds.txt \
  --days-back 2 \
  --limit 15 \
  --fetch-content \
  --output ./tmp/ai-trend-sources.json
```

用户指定区间：

```bash
"$PYTHON_BIN" "$RSS_COLLECT_SCRIPT" \
  --use-default-ai-sources \
  --date-from 2026-03-17 \
  --date-to 2026-03-19 \
  --limit 15 \
  --fetch-content \
  --output ./tmp/ai-trend-sources.json
```

兼容旧调用时，也允许：

```bash
"$PYTHON_BIN" "$RSS_COLLECT_SCRIPT" --use-default-ai-feeds ...
```

它现在会被视为 `--use-default-ai-sources` 的别名。

## 脚本输出

脚本会输出一个 JSON 对象，核心字段有：

- `collected_at`
- `requested_window`
- `resolved_window`
- `used_fallback`
- `selected_count`
- `requested_feeds`
- `deferred_sources`
- `items`

`items` 里每条内容至少有：

- `title`
- `url`
- `published_date`
- `feed_url`
- `source_kind`
- `source_label`
- `source_domain`
- `summary`
- `content`（仅当用了 `--fetch-content`）

`deferred_sources` 里是脚本没直接抓、需要 Codex 后续处理的来源，例如：

- Reddit subreddit
- YouTube channel page

## Codex 在脚本之后要做什么

拿到 `ai-trend-sources.json` 后，不要再跑额外 LLM 脚本。直接在会话里完成下面几步：

1. 读 JSON，先处理 `items`。
2. 再看 `deferred_sources`，补抓最关键的 Reddit / YouTube 来源。
3. 对相近标题、同一事件、多源重复内容做聚合。
4. 先筛出“热点条目”，再归纳主题和共同线索。
5. 按用户要求输出摘要记录，而不是文章。
6. 文末附上来源链接，除非用户明确不要。

## 输出要求

给用户的结果至少包含：

- 摘要记录内容或文件路径
- 热点条目列表
- 实际采用的来源数和文章数
- 来源类型分布
- 主题要点或分类结果
- 关键来源列表
- 如果存在明显抓取缺口，明确说明哪些来源只拿到了弱信号

推荐的默认记录结构：

1. `热点概览`：这个窗口里最值得关注的 AI 主题。
2. `热点条目`：按重要性列出 5 到 10 条。
3. `主题归纳`：把相近事件合并说明。
4. `观察记录`：值得继续跟踪的变化、发布、研究方向。
5. `来源`：按 Reddit / YouTube / WeChat RSS / RSS 分类列出。

## 异常处理

- feed 解析失败：跳过失败 feed，继续处理其他 feed。
- 目标日期或区间没有文章：自动回退到最近文章，并明确告诉用户。
- 部分正文抓取失败：保留元数据，继续处理其他内容。
- Reddit 或 YouTube 页面受限：保留该来源为弱信号，并明确说明抓取方式受限。
- 全部 RSS 兼容源都抓不到，但存在 `deferred_sources`：不要停止，改走 MCP 或网页补抓。
