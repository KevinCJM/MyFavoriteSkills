# rss-digest-writer

## 中文说明

- 用途：从 RSS、Reddit、YouTube、公众号 RSS 等来源聚合 AI 相关热点，由 Codex 完成筛选、去重、摘要和记录。
- 适合场景：找近两天 AI 热点、追踪 AI 圈更新、整理 Reddit/YouTube/RSS/公众号来源。
- 技能类型：热点发现与摘要编排 skill，不是通用新闻爬虫，也不是文章写作 skill。
- 依赖：`python3`、网络访问、Codex 的网页搜索/抓取能力。
- 可选依赖：Reddit MCP、YouTube 相关 MCP 或浏览器能力；没有时会降级为网页搜索或公开页面抓取。
- 必须一起复制的文件：`SKILL.md`、`scripts/rss_collect.py`、`references/default-ai-source-pack.json`、`references/default-ai-feeds.txt`、`references/local-wechat-rss-feeds.txt`。
- 公众号 RSS：`references/local-wechat-rss-feeds.txt` 默认只是占位文件，使用者需要自己添加 feed；共享前不要写入私人 feed、token 或内网地址。
- 安装方式：把整个 `rss-digest-writer/` 文件夹复制到目标电脑的 Codex skills 目录，例如 `$CODEX_HOME/skills/` 或 `~/.codex/skills/`。
- 使用示例：`用 $rss-digest-writer 整理近两天 AI 圈热点`。
- 迁移注意：不要提交 `__pycache__/`、`*.pyc`、临时输出 JSON、个人 RSS 列表或私有来源。

## English

- Purpose: Aggregate AI-related trends from RSS, Reddit, YouTube, WeChat RSS, and similar sources, then let Codex deduplicate, rank, summarize, and archive the findings.
- Best for: Finding recent AI trends, monitoring AI updates, and summarizing Reddit/YouTube/RSS/WeChat RSS signals.
- Skill type: Trend discovery and digest orchestration. It is not a general news crawler or a long-form writing skill.
- Requirements: `python3`, network access, and Codex web search/fetch capability.
- Optional integrations: Reddit MCP, YouTube-related MCP, or browser tools. If unavailable, the skill should fall back to web search or public pages.
- Files to copy together: `SKILL.md`, `scripts/rss_collect.py`, `references/default-ai-source-pack.json`, `references/default-ai-feeds.txt`, and `references/local-wechat-rss-feeds.txt`.
- WeChat RSS: `references/local-wechat-rss-feeds.txt` is a placeholder by default. Users should add their own feeds and must not share private feeds, tokens, or internal URLs.
- Installation: Copy the full `rss-digest-writer/` folder into the target Codex skills directory, such as `$CODEX_HOME/skills/` or `~/.codex/skills/`.
- Example prompt: `Use $rss-digest-writer to summarize AI trends from the last two days`.
- Sharing note: Do not include `__pycache__/`, `*.pyc`, temporary JSON outputs, personal RSS lists, or private sources.
