# MyFavoriteSkills

个人常用 Codex skills 集合。每个 skill 都放在独立目录中，包含 `SKILL.md`，部分技能还带有脚本、引用资料、agent 元数据和独立说明文档。

Personal collection of reusable Codex skills. Each skill lives in its own folder with a `SKILL.md`; some skills also include scripts, references, agent metadata, and a dedicated README.

## 安装 / Install

复制需要的 skill 文件夹到 Codex skills 目录：

Copy the skill folder you need into your Codex skills directory:

```bash
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R <skill-folder> "${CODEX_HOME:-$HOME/.codex}/skills/"
```

也可以复制多个 skill 文件夹。不要复制生成产物、缓存、私有配置或任何包含密钥的文件。

You can also copy multiple skill folders. Do not copy generated outputs, caches, private config, or files containing secrets.

## 推荐组合 / Recommended Bundles

AI Hermes 路由闭环建议同时安装这三个 skill：

For the complete AI Hermes routing loop, install these three skills together:

```bash
cp -R ai-hermes-routing-init ai-hermes-self-evolve ai-hermes-user-project-memory "${CODEX_HOME:-$HOME/.codex}/skills/"
```

- `ai-hermes-routing-init`：初始化项目路由文件、项目内置 AI Hermes 脚本和基础自审核流程。
- `ai-hermes-self-evolve`：在代码、测试、配置、工具或路由事实变化后维护路由记忆。
- `ai-hermes-user-project-memory`：保存项目级个人偏好和本机私有配置，并提供安全召回、学习和审计。
- `ai-hermes-routing-init`: initializes routing files, project-local AI Hermes scripts, and bootstrap self-audits.
- `ai-hermes-self-evolve`: maintains routing memory after code, tests, configs, tools, or routing facts change.
- `ai-hermes-user-project-memory`: stores project-scoped personal preferences and private local config with safe recall, learning, and auditing.

`ai-hermes-routing-init` 会在缺少 `AGENTS.md` 时创建路由协议，或在普通 `AGENTS.md` 缺少路由层说明时追加带 `AI-HERMES-ROUTING-PROTOCOL` 标记的协议块；`ai-hermes-self-evolve` 在路由层未初始化时会返回 `routing_not_initialized` 并提示先初始化。

`ai-hermes-routing-init` creates routing guidance when `AGENTS.md` is missing, or appends an `AI-HERMES-ROUTING-PROTOCOL` marker block when a plain `AGENTS.md` lacks routing-layer instructions; `ai-hermes-self-evolve` returns `routing_not_initialized` and points users to initialization when the routing layer is absent.

## Skills / 技能列表

| Skill | 中文简介 | English summary |
| --- | --- | --- |
| [`ai-hermes-routing-init`](./ai-hermes-routing-init) | 创建初始 AI Hermes 路由文件、项目内置脚本和 AGENTS 路由协议，支持幂等追加和修复 marker 协议块。 | Creates initial AI Hermes routing files, project-local scripts, and AGENTS routing guidance, with idempotent marker insertion and repair. |
| [`ai-hermes-self-evolve`](./ai-hermes-self-evolve) | 维护 AI Hermes 路由记忆，检查覆盖、验证路由文件；未初始化时提示先运行 routing-init。 | Maintains AI Hermes routing memory, checks coverage, validates routing files, and points uninitialized repos to routing-init first. |
| [`ai-hermes-user-project-memory`](./ai-hermes-user-project-memory) | 为当前项目保存用户个人偏好和本机私有配置，支持记忆召回、学习、审计和安全边界控制。 | Stores project-local personal preferences and private runtime config, with recall, learning, auditing, and safety limits. |
| [`article-extractor`](./article-extractor) | 从文章、博客、教程 URL 中抽取干净正文，去掉导航、广告和页面噪音，并保存为本地文本。 | Extracts clean main text from article, blog, or tutorial URLs and saves readable local text. |
| [`content-research-writer`](./content-research-writer) | 辅助资料调研、提纲设计、引用整理、正文写作和逐段反馈，适合文章和长文写作。 | Helps research topics, build outlines, manage citations, draft content, and review sections iteratively. |
| [`free-media-fetcher`](./free-media-fetcher) | 通过 Pexels 和 Pixabay API 搜索并下载免费图片/视频素材，支持横屏、竖屏、质量和元数据。 | Searches and downloads free stock photos/videos from Pexels and Pixabay with orientation, quality, and metadata support. |
| [`metrics-factory`](./metrics-factory) | 面向 AI 智能体的金融产品指标计算技能，封装 MetricsFactory 区间/滚动指标、可移植运行时、PIT 复权数据契约和滚动入口防护。 | Agent-facing financial metric calculation skill for MetricsFactory, with period/rolling metrics, portable runtime setup, PIT adjusted data contracts, and guarded rolling jobs. |
| [`mine-codex-workflows`](./mine-codex-workflows) | 分析本地 Codex 历史对话，发现重复工作流、常用命令模式和可沉淀为 skill 的候选项。 | Mines local Codex history for repeated workflows, command patterns, and reusable skill candidates. |
| [`rss-digest-writer`](./rss-digest-writer) | 从 RSS、Reddit、YouTube、公众号 RSS 等来源聚合热点，由 Codex 去重、筛选、摘要和归档。 | Aggregates trends from RSS, Reddit, YouTube, WeChat RSS, and web signals, then deduplicates and summarizes them. |
| [`tushare-fetcher`](./tushare-fetcher) | 根据 Tushare 积分和接口 JSON 生成限频数据获取脚本，支持 Parquet 输出、冒烟测试和脚本固化。 | Generates rate-limited Tushare Parquet fetch scripts from interface JSON and user points, with smoke tests and solidification. |
| [`volcengine-podcast-md-to-audio`](./volcengine-podcast-md-to-audio) | 将本地 Markdown 或文本文章通过火山引擎播客 TTS 转成双人播客 MP3，并下载服务端最终音频。 | Converts local Markdown or text articles into two-speaker podcast MP3s through Volcengine podcast TTS. |
| [`yt-dlp-smart-download`](./yt-dlp-smart-download) | 使用 `yt-dlp` 智能下载视频和字幕，在最佳质量和 MP4 兼容格式之间自动选择。 | Downloads videos and subtitles with `yt-dlp`, choosing best quality or MP4-compatible formats as needed. |

## 使用方式 / Usage

在 Codex 中直接通过技能名触发，例如：

Trigger a skill in Codex by mentioning its name, for example:

```text
$ai-hermes-routing-init 初始化这个仓库的路由文件
$ai-hermes-self-evolve 检查这次提交是否需要更新路由记忆
$ai-hermes-user-project-memory 记住这个项目默认用指定 Python 解释器
$metrics-factory 计算多个金融产品在多个区间的指标
```

具体参数、脚本路径和安全规则以每个 skill 目录中的 `README.md` 和 `SKILL.md` 为准。

For exact arguments, script paths, and safety rules, see each skill folder's `README.md` and `SKILL.md`.

## 依赖 / Dependencies

不同 skill 的依赖不同，请优先查看对应目录中的 `README.md` 和 `SKILL.md`。

Dependencies vary by skill. Check each skill folder's `README.md` and `SKILL.md` first.

常见依赖包括：

Common dependencies include:

- Python 3
- Git and GitHub CLI for publishing workflows
- Python scientific stack for metric calculation skills, such as `numpy`, `pandas`, `scipy`, `numba`, and `pyarrow`
- Network access for skills that fetch remote content or call APIs
- Optional command-line tools such as `yt-dlp`, `ffmpeg`, `curl`, `reader`, or `trafilatura`
- Optional API keys or account settings such as `PEXELS_API_KEY`, `PIXABAY_API_KEY`, Tushare token/points config, or Volcengine podcast TTS credentials

## 共享注意事项 / Sharing Notes

- 不要提交 API key、token、cookie、Authorization、私钥、`.env` 文件或个人配置。
- 不要提交 `__pycache__/`、`*.pyc`、`.DS_Store`、临时 JSON、下载素材、生成音频或其他产物。
- 带脚本的 skill 应保持脚本路径相对目录可用，避免写死本机绝对路径。
- 带外部服务的 skill 应让使用者配置自己的账号和环境变量。
- AI Hermes user memory 数据默认应保留在项目本地并被 git 忽略，除非用户明确要求同步且安全检查通过。
- Do not commit API keys, tokens, cookies, Authorization headers, private keys, `.env` files, or personal config.
- Do not commit `__pycache__/`, `*.pyc`, `.DS_Store`, temporary JSON, downloaded media, generated audio, or other outputs.
- Skills with scripts should keep paths portable and avoid hardcoded local absolute paths.
- Skills that use external services should require users to configure their own accounts and environment variables.
- AI Hermes user memory data should stay project-local and git-ignored by default unless the user explicitly requests sync and the safety check passes.

## License / 许可

本仓库代码和文档使用 [MIT License](./LICENSE)。

Code and documentation in this repository are released under the [MIT License](./LICENSE).

使用具体 skill 时，仍需遵守相关第三方服务、API、素材平台和依赖工具的条款。

When using a specific skill, you must still follow the terms of any related third-party services, APIs, media platforms, and dependency tools.
