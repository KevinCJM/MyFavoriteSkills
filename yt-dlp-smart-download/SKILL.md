---
name: yt-dlp-smart-download
description: 使用 yt-dlp 智能下载视频与字幕。当用户用自然语言表达“下载视频/下载这个视频/把这个视频下到本地/下载 MP4”等意图时触发；自动探测可用格式并在质量优先或兼容优先之间选择。Use when asked to download a video URL locally with yt-dlp, choose quality or MP4-compatible formats, download subtitles, or use browser cookies when needed.
---

# yt-dlp 智能下载 / Smart Video Download

默认直接下载，不做多轮确认；如果没有链接，只追问一次“请发我视频链接”。

## 依赖 / Dependencies

- **Required / 必需**：Python `3.10+`。
- **Required / 必需**：`yt-dlp` 命令或 Python 包。
  - Install: `python3 -m pip install -U yt-dlp`
  - Verify: `yt-dlp --version` or `python3 -m yt_dlp --version`
- **Recommended / 推荐**：`ffmpeg`，用于合并音视频、转字幕、处理高质量格式。
  - macOS: `brew install ffmpeg`
  - Ubuntu/Debian: `sudo apt-get install ffmpeg`
  - Windows: install from `https://ffmpeg.org/` or use a package manager such as winget/choco.
- **Optional / 可选**：`curl`，抖音 fallback 和直链下载会优先使用；没有时脚本会回退到 Python `urllib`。
- **Optional / 可选**：Chrome/Safari/Firefox 浏览器登录态；需要会员、私密、年龄限制或登录内容时使用 `--cookies-from-browser <browser>`。

If dependencies are missing, report the install command and do not pretend the download ran.

## 自然语言触发

将以下表达视为触发信号（不限于这些）：

- 下载视频
- 下载这个视频
- 把这个视频下载下来
- 帮我下这个链接
- 下载 MP4
- 把字幕也下载
- download this video
- save this video locally
- download video with subtitles

触发规则：

- 用户表达“下载视频到本地”的意图时，优先使用本技能，不改走网页自动化。
- 若消息内有视频链接，直接执行下载。
- 若消息内没有链接，但同一会话最近用户消息包含可用视频链接，可沿用该链接并执行。
- 若上下文中也找不到链接，先追问一次“请发我视频链接”。

## 工作流

1. 识别用户意图与链接。
2. 选择策略：
   - `quality`：用户强调“最佳画质 / 原画 / 最高质量 / best quality”。
   - `compat`：用户强调“兼容 / 手机 / MP4 / 剪辑软件可用 / mobile / compatible”。
   - 未明确时默认 `quality`。
3. 调用脚本完成探测与下载。
4. 若抖音链接遇到 `Fresh cookies are needed`、JSON 解析失败、或 `yt-dlp` 无法读取详情页，脚本会尝试抖音移动端分享页 `_ROUTER_DATA` fallback，提取 `play_addr` 直链并保存 MP4。
5. 返回结果：输出目录、策略、格式表达式、字幕语言、执行方法与状态。

## 可移植脚本定位

Use the bundled script from the active skill folder. Prefer `YT_DLP_SKILL_SCRIPT` when set.

```bash
PYTHON_BIN="${PYTHON_BIN:-python3}"
SKILL_SCRIPT="${YT_DLP_SKILL_SCRIPT:-}"
if [ -z "$SKILL_SCRIPT" ]; then
  for candidate in \
    "${CODEX_HOME:-$HOME/.codex}/skills/yt-dlp-smart-download/scripts/smart_download.py" \
    "$HOME/.codex/skills/yt-dlp-smart-download/scripts/smart_download.py" \
    "${OPENCLAW_SKILLS_DIR:-$HOME/.openclaw/skills}/yt-dlp-smart-download/scripts/smart_download.py" \
    "skills/yt-dlp-smart-download/scripts/smart_download.py"
  do
    if [ -f "$candidate" ]; then
      SKILL_SCRIPT="$candidate"
      break
    fi
  done
fi
[ -n "$SKILL_SCRIPT" ] || { echo "未找到 smart_download.py / smart_download.py not found"; exit 1; }
```

## 执行命令

质量优先：

```bash
"$PYTHON_BIN" "$SKILL_SCRIPT" "<视频链接>" --strategy quality
```

兼容 MP4 优先：

```bash
"$PYTHON_BIN" "$SKILL_SCRIPT" "<视频链接>" --strategy compat
```

需要浏览器登录态：

```bash
"$PYTHON_BIN" "$SKILL_SCRIPT" "<视频链接>" \
  --strategy quality \
  --cookies-from-browser chrome
```

先探测不下载：

```bash
"$PYTHON_BIN" "$SKILL_SCRIPT" "<视频链接>" --strategy quality --dry-run
```

## 参数约定

- 默认输出目录回退顺序：
  1. `--output-dir`
  2. `YT_DLP_DOWNLOAD_DIR`
  3. `OPENCLAW_DOWNLOAD_DIR`（兼容旧环境）
  4. `./downloads`
  5. `$CODEX_HOME/downloads`
  6. `~/.codex/downloads`
  7. `~/Downloads`
  8. `$TMPDIR/yt-dlp-smart-downloads`
  9. `/tmp/yt-dlp-smart-downloads`
- 默认下载字幕：`--write-subs`，并启用自动字幕回退。
- 默认字幕语言：`zh-Hans,zh-Hant,zh-CN,zh-TW,zh,en,en-US,en-GB`。
- 默认转换字幕为 `srt`。
- 默认 `--no-playlist` 防止误下载整播放列表；只有用户明确要求时才加 `--allow-playlist`。
- `--cookies-from-browser <browser>` 会原样传给 `yt-dlp`，例如 `chrome`、`safari`、`firefox`。
- 抖音 fallback 默认启用；如需排查 `yt-dlp` 原始错误，可加 `--no-douyin-fallback`。

## 输出要求

执行完成后，始终反馈：

- `strategy`：`quality` 或 `compat`
- `format_expression`
- `method`：例如 `yt-dlp` 或 `douyin_mobile_ssr_fallback`
- 字幕设置：语言、是否自动字幕、是否转 `srt`
- 下载目录、输出文件或输出模板与结果状态

默认下载目录应以脚本输出中的 `output_dir` 字段为准。

## 异常处理

- 若缺少 `yt-dlp`：提示安装命令，不继续伪执行。
- 若缺少 `ffmpeg` 且合并/字幕转换失败：提示安装 `ffmpeg`，并说明视频站点或格式可能需要它。
- 若抖音下载失败且错误类似 `Fresh cookies are needed`：不要停在 cookies 报错，脚本会尝试移动端 SSR fallback；最终 `method` 以实际成功路径为准。
- 若移动端 fallback 成功但无字幕字段：明确说明“该视频未提供可下载字幕”，视频下载仍视为完成。
- 若所有路径均失败：原样返回错误，并附带可复现命令。
- 若无字幕：明确说明“该视频未提供可下载字幕”，但视频下载流程仍完成。

## 共享与安全

- Do not include `.idea/`, `__pycache__/`, or `*.pyc` when sharing this skill.
- Respect copyright, website terms, and user authorization. Only download content the user has rights or permission to download.
- Browser cookies may grant account access; use `--cookies-from-browser` only when needed and never print cookie values.
