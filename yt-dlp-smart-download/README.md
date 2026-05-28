# yt-dlp Smart Download / yt-dlp 智能下载

## English

A portable Codex skill for downloading videos and subtitles with `yt-dlp`. It chooses between best-quality and MP4-compatible formats, supports browser cookies, and includes a best-effort Douyin mobile fallback.

### Dependencies

- **Required**: Python `3.10+`.
- **Required**: `yt-dlp` command or Python package.
  - Install: `python3 -m pip install -U yt-dlp`
  - Verify: `yt-dlp --version` or `python3 -m yt_dlp --version`
- **Recommended**: `ffmpeg` for merging video/audio streams and converting subtitles.
  - macOS: `brew install ffmpeg`
  - Ubuntu/Debian: `sudo apt-get install ffmpeg`
  - Windows: install from `https://ffmpeg.org/`, or use winget/choco.
- **Optional**: `curl`; the script falls back to Python `urllib` if missing.
- **Optional**: Chrome/Safari/Firefox cookies for login-required videos via `--cookies-from-browser <browser>`.

### Install

Copy the folder to your Codex skills directory:

```bash
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R yt-dlp-smart-download "${CODEX_HOME:-$HOME/.codex}/skills/"
```

Do not copy `.idea/`, `__pycache__/`, or `*.pyc` files.

### Usage

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/yt-dlp-smart-download/scripts/smart_download.py" \
  "<video-url>" \
  --strategy quality
```

MP4-compatible mode:

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/yt-dlp-smart-download/scripts/smart_download.py" \
  "<video-url>" \
  --strategy compat
```

Use browser cookies:

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/yt-dlp-smart-download/scripts/smart_download.py" \
  "<video-url>" \
  --strategy quality \
  --cookies-from-browser chrome
```

Dry run:

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/yt-dlp-smart-download/scripts/smart_download.py" \
  "<video-url>" \
  --dry-run
```

### Output directory precedence

1. `--output-dir`
2. `YT_DLP_DOWNLOAD_DIR`
3. `OPENCLAW_DOWNLOAD_DIR` for backward compatibility
4. `./downloads`
5. `$CODEX_HOME/downloads`
6. `~/.codex/downloads`
7. `~/Downloads`
8. `$TMPDIR/yt-dlp-smart-downloads`
9. `/tmp/yt-dlp-smart-downloads`

### Notes

- The Douyin fallback is best-effort and may break if the mobile page structure changes.
- Respect copyright, website terms, and user authorization.
- Do not print or store browser cookies.

## 中文

这是一个可移植的 Codex 技能，用 `yt-dlp` 下载视频和字幕。它会在最佳质量和 MP4 兼容格式之间自动选择，支持浏览器 cookies，并包含尽力而为的抖音移动端 fallback。

### 依赖

- **必需**：Python `3.10+`。
- **必需**：`yt-dlp` 命令或 Python 包。
  - 安装：`python3 -m pip install -U yt-dlp`
  - 验证：`yt-dlp --version` 或 `python3 -m yt_dlp --version`
- **推荐**：`ffmpeg`，用于合并音视频流和转换字幕。
  - macOS：`brew install ffmpeg`
  - Ubuntu/Debian：`sudo apt-get install ffmpeg`
  - Windows：从 `https://ffmpeg.org/` 安装，或使用 winget/choco。
- **可选**：`curl`；没有时脚本会回退到 Python `urllib`。
- **可选**：Chrome/Safari/Firefox 登录态；下载需要登录的视频时使用 `--cookies-from-browser <browser>`。

### 安装

复制整个文件夹到 Codex skills 目录：

```bash
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R yt-dlp-smart-download "${CODEX_HOME:-$HOME/.codex}/skills/"
```

共享时不要包含 `.idea/`、`__pycache__/` 或 `*.pyc` 文件。

### 使用

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/yt-dlp-smart-download/scripts/smart_download.py" \
  "<视频链接>" \
  --strategy quality
```

MP4 兼容模式：

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/yt-dlp-smart-download/scripts/smart_download.py" \
  "<视频链接>" \
  --strategy compat
```

使用浏览器登录态：

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/yt-dlp-smart-download/scripts/smart_download.py" \
  "<视频链接>" \
  --strategy quality \
  --cookies-from-browser chrome
```

只探测不下载：

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/yt-dlp-smart-download/scripts/smart_download.py" \
  "<视频链接>" \
  --dry-run
```

### 输出目录优先级

1. `--output-dir`
2. `YT_DLP_DOWNLOAD_DIR`
3. `OPENCLAW_DOWNLOAD_DIR`，用于兼容旧环境
4. `./downloads`
5. `$CODEX_HOME/downloads`
6. `~/.codex/downloads`
7. `~/Downloads`
8. `$TMPDIR/yt-dlp-smart-downloads`
9. `/tmp/yt-dlp-smart-downloads`

### 注意事项

- 抖音 fallback 是尽力而为，移动端页面结构变化后可能失效。
- 请遵守版权、网站条款和用户授权边界。
- 不要打印或保存浏览器 cookies。
