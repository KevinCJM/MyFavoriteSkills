# content-research-writer

## 中文说明

- 用途：帮助用户围绕指定主题进行资料调研、提纲设计、引用整理、正文写作和逐段反馈。
- 适合场景：博客、公众号草稿、newsletter、技术文章、案例研究、教程、观点文章。
- 技能类型：研究写作协作 skill，不依赖本机脚本或私有文件。
- 依赖：AI agent 的联网搜索、网页抓取或浏览器能力；如果没有联网能力，可以基于用户提供的材料工作，并明确标记信息缺口。
- 工作目录：优先使用用户指定目录；未指定时可以用当前目录或 `./writing/<article-slug>/`。
- 安装方式：把整个 `content-research-writer/` 文件夹复制到目标电脑的 Codex skills 目录，例如 `$CODEX_HOME/skills/` 或 `~/.codex/skills/`。
- 使用示例：`用 $content-research-writer 调研 AI agent 记忆架构，并帮我写一个文章提纲`。
- 迁移注意：不要假设使用者有 Claude Code、Codex、VS Code、Notion 或固定编辑器；让 agent 根据当前环境调整。

## English

- Purpose: Help users research a specified topic, build outlines, manage citations, draft content, and review sections iteratively.
- Best for: Blog posts, newsletters, technical articles, case studies, tutorials, thought leadership, and long-form drafts.
- Skill type: Research and writing collaboration skill. It does not require local scripts or private files.
- Requirements: The agent's web search, web fetch, or browser capability. If web access is unavailable, work from user-provided materials and clearly mark research gaps.
- Working directory: Prefer the user's requested folder. If none is provided, use the current directory or `./writing/<article-slug>/`.
- Installation: Copy the full `content-research-writer/` folder into the target Codex skills directory, such as `$CODEX_HOME/skills/` or `~/.codex/skills/`.
- Example prompt: `Use $content-research-writer to research AI agent memory architecture and draft an outline`.
- Sharing note: Do not assume the user has Claude Code, Codex, VS Code, Notion, or a fixed editor. Adapt to the current environment.
