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

也可以复制整个仓库中的多个 skill 文件夹。不要复制生成产物、缓存、私有配置或任何包含密钥的文件。

You can also copy multiple skill folders from this repository. Do not copy generated outputs, caches, private config, or files containing secrets.

## Skills / 技能列表

| Skill | 中文简介 | English summary |
| --- | --- | --- |
| [`ai-hermes-user-project-memory`](./ai-hermes-user-project-memory) | 为当前项目保存用户个人偏好和本机私有配置，支持记忆召回、学习、审计和安全边界控制。 | Stores project-local personal preferences and private runtime config, with recall, learning, auditing, and safety limits. |
| [`article-extractor`](./article-extractor) | 从文章、博客、教程 URL 中抽取干净正文，去掉导航、广告和页面噪音，并保存为本地文本。 | Extracts clean main text from article, blog, or tutorial URLs and saves readable local text. |
| [`content-research-writer`](./content-research-writer) | 辅助资料调研、提纲设计、引用整理、正文写作和逐段反馈，适合文章和长文写作。 | Helps research topics, build outlines, manage citations, draft content, and review sections iteratively. |
| [`free-media-fetcher`](./free-media-fetcher) | 通过 Pexels 和 Pixabay API 搜索并下载免费图片/视频素材，支持横屏、竖屏、质量和元数据。 | Searches and downloads free stock photos/videos from Pexels and Pixabay with orientation, quality, and metadata support. |
| [`mine-codex-workflows`](./mine-codex-workflows) | 分析本地 Codex 历史对话，发现重复工作流、常用命令模式和可沉淀为 skill 的候选项。 | Mines local Codex history for repeated workflows, command patterns, and reusable skill candidates. |
| [`rss-digest-writer`](./rss-digest-writer) | 从 RSS、Reddit、YouTube、公众号 RSS 等来源聚合热点，由 Codex 去重、筛选、摘要和归档。 | Aggregates trends from RSS, Reddit, YouTube, WeChat RSS, and web signals, then deduplicates and summarizes them. |
| [`volcengine-podcast-md-to-audio`](./volcengine-podcast-md-to-audio) | 将本地 Markdown 或文本文章通过火山引擎播客 TTS 转成双人播客 MP3，并下载服务端最终音频。 | Converts local Markdown or text articles into two-speaker podcast MP3s through Volcengine podcast TTS. |
| [`yt-dlp-smart-download`](./yt-dlp-smart-download) | 使用 `yt-dlp` 智能下载视频和字幕，在最佳质量和 MP4 兼容格式之间自动选择。 | Downloads videos and subtitles with `yt-dlp`, choosing best quality or MP4-compatible formats as needed. |

## 依赖 / Dependencies

不同 skill 的依赖不同，请优先查看对应目录中的 `README.md` 和 `SKILL.md`。

Dependencies vary by skill. Check each skill folder's `README.md` and `SKILL.md` first.

常见依赖包括：

Common dependencies include:

- Python 3
- Network access
- Optional command-line tools such as `yt-dlp`, `ffmpeg`, `curl`, `reader`, or `trafilatura`
- Optional API keys such as `PEXELS_API_KEY`, `PIXABAY_API_KEY`, or Volcengine podcast TTS credentials

## 共享注意事项 / Sharing Notes

- 不要提交 API key、token、cookie、Authorization、私钥、`.env` 文件或个人配置。
- 不要提交 `__pycache__/`、`*.pyc`、`.DS_Store`、临时 JSON、下载素材、生成音频或其他产物。
- 带脚本的 skill 应保持脚本路径相对目录可用，避免写死本机绝对路径。
- 带外部服务的 skill 应让使用者配置自己的账号和环境变量。
- Do not commit API keys, tokens, cookies, Authorization headers, private keys, `.env` files, or personal config.
- Do not commit `__pycache__/`, `*.pyc`, `.DS_Store`, temporary JSON, downloaded media, generated audio, or other outputs.
- Skills with scripts should keep paths portable and avoid hardcoded local absolute paths.
- Skills that use external services should require users to configure their own accounts and environment variables.

## License / 许可

本仓库代码和文档使用 [MIT License](./LICENSE)。

Code and documentation in this repository are released under the [MIT License](./LICENSE).

使用具体 skill 时，仍需遵守相关第三方服务、API、素材平台和依赖工具的条款。

When using a specific skill, you must still follow the terms of any related third-party services, APIs, media platforms, and dependency tools.
