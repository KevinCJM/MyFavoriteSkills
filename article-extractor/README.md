# article-extractor

## 中文说明

- 用途：从文章、博客、教程 URL 中抽取干净正文，去掉导航、广告、订阅弹窗和页面噪音，并保存为本地文本文件。
- 适合场景：保存网页正文、提取博客内容、为后续调研准备干净资料。
- 技能类型：网页正文抽取 skill，不需要私有路径、API key 或内置脚本。
- 基础依赖：网络访问、shell、`curl`、`python3`。
- 推荐依赖：`reader` 或 `trafilatura`。
- 安装 `reader`：使用 `npm install -g @mozilla/readability-cli` 或 `npm install -g reader-cli`，以实际可用命令为准。
- 安装 `trafilatura`：使用 `python3 -m pip install trafilatura` 或 `pip3 install trafilatura`。
- Windows 建议：优先使用 WSL、Git Bash 或等价 PowerShell 命令；保持 `reader -> trafilatura -> curl fallback` 的顺序即可。
- 安装方式：把整个 `article-extractor/` 文件夹复制到目标电脑的 Codex skills 目录，例如 `$CODEX_HOME/skills/` 或 `~/.codex/skills/`。
- 使用示例：`用 $article-extractor 提取 https://example.com/article 的正文并保存为文本`。
- 限制：登录页、付费墙、强 JavaScript 渲染页面可能无法完整抽取；失败时应明确说明。

## English

- Purpose: Extract clean main text from article, blog, or tutorial URLs, removing navigation, ads, newsletter prompts, and page clutter, then save it locally.
- Best for: Saving article text, extracting blog posts, and preparing clean sources for later research.
- Skill type: Web article extraction skill. It does not require private paths, API keys, or bundled scripts.
- Baseline requirements: Network access, a shell, `curl`, and `python3`.
- Recommended tools: `reader` or `trafilatura`.
- Install `reader`: Use `npm install -g @mozilla/readability-cli` or `npm install -g reader-cli`, depending on which command works in the target environment.
- Install `trafilatura`: Use `python3 -m pip install trafilatura` or `pip3 install trafilatura`.
- Windows note: Prefer WSL, Git Bash, or equivalent PowerShell commands. Preserve the extraction order: `reader -> trafilatura -> curl fallback`.
- Installation: Copy the full `article-extractor/` folder into the target Codex skills directory, such as `$CODEX_HOME/skills/` or `~/.codex/skills/`.
- Example prompt: `Use $article-extractor to extract https://example.com/article and save the clean text`.
- Limitations: Login pages, paywalls, and heavy JavaScript-rendered pages may not extract completely. Report this clearly when it happens.
