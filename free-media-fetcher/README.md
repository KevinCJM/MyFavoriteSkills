# free-media-fetcher

## 中文说明

- 用途：通过 Pexels 和 Pixabay 免费素材 API 搜索并下载图片/视频。
- 默认比例：默认获取横屏 `16:9` 倾向素材，适合网站、YouTube、Remotion 横版视频、文章封面。
- 竖屏模式：当用户明确说竖屏、portrait、9:16、Shorts、TikTok、Reels、手机视频时，使用竖屏 `9:16` 倾向素材。
- 主要产物：下载的媒体文件和 `manifest.json`，其中包含 provider、作者、来源页、尺寸和下载 URL 等元数据。
- 依赖：`python3`、网络访问、`PEXELS_API_KEY` 或 `PIXABAY_API_KEY`，推荐两个都配置。
- 可选依赖：`ffmpeg` / `ffprobe`，仅用于视频缩略图、抽帧和检查，不是下载必需项。

## 安装步骤

1. 安装 Python 3。
2. 申请 Pexels API key：https://www.pexels.com/api/
3. 申请 Pixabay API key：https://pixabay.com/api/docs/
4. 设置环境变量。
5. 运行 dry-run 验证。

macOS / Linux:

```bash
export PEXELS_API_KEY="your_pexels_key"
export PIXABAY_API_KEY="your_pixabay_key"
python3 scripts/fetch_media.py "forest" --type all --count 3 --dry-run
```

Windows PowerShell:

```powershell
$env:PEXELS_API_KEY="your_pexels_key"
$env:PIXABAY_API_KEY="your_pixabay_key"
python scripts/fetch_media.py "forest" --type all --count 3 --dry-run
```

## 使用示例

默认横屏 16:9：

```bash
python3 scripts/fetch_media.py "city skyline" --type photo --count 3 --output-dir media
```

竖屏 9:16：

```bash
python3 scripts/fetch_media.py "city skyline" --type video --orientation vertical --count 3 --output-dir media-vertical
```

指定高质量横屏视频：

```bash
python3 scripts/fetch_media.py "nature sunrise" --type video --video-quality best --pexels-video-quality hd --count 3 --output-dir sunrise-video
```

## 共享注意事项

- 不要提交 API key、`.env`、下载素材目录、私有 `manifest.json`。
- 不要提交 `__pycache__/`、`*.pyc`、`.DS_Store`。
- 可以共享整个 skill 文件夹：`SKILL.md`、`README.md`、`scripts/fetch_media.py`、`agents/openai.yaml`。
- 不要声称素材“无版权”；应说明素材来自 Pexels/Pixabay 免费素材 API，最终使用前应检查 provider 页面授权。

## English

- Purpose: Search and download free stock photos/videos from the Pexels and Pixabay APIs.
- Default aspect: horizontal `16:9`-oriented media for websites, YouTube, Remotion landscape videos, and article covers.
- Vertical mode: when the user explicitly asks for vertical, portrait, 9:16, Shorts, TikTok, Reels, or phone video, use `9:16`-oriented media.
- Outputs: downloaded media files plus `manifest.json` with provider, author, source page, dimensions, and download URL metadata.
- Requirements: `python3`, network access, `PEXELS_API_KEY` or `PIXABAY_API_KEY`; configuring both is recommended.
- Optional tools: `ffmpeg` / `ffprobe` for thumbnails, frame extraction, and video inspection. They are not required for downloading.

## Setup

1. Install Python 3.
2. Get a Pexels API key: https://www.pexels.com/api/
3. Get a Pixabay API key: https://pixabay.com/api/docs/
4. Export the API keys as environment variables.
5. Run a dry-run test.

macOS / Linux:

```bash
export PEXELS_API_KEY="your_pexels_key"
export PIXABAY_API_KEY="your_pixabay_key"
python3 scripts/fetch_media.py "forest" --type all --count 3 --dry-run
```

Windows PowerShell:

```powershell
$env:PEXELS_API_KEY="your_pexels_key"
$env:PIXABAY_API_KEY="your_pixabay_key"
python scripts/fetch_media.py "forest" --type all --count 3 --dry-run
```

## Examples

Default horizontal 16:9:

```bash
python3 scripts/fetch_media.py "city skyline" --type photo --count 3 --output-dir media
```

Vertical 9:16:

```bash
python3 scripts/fetch_media.py "city skyline" --type video --orientation vertical --count 3 --output-dir media-vertical
```

High-quality horizontal video:

```bash
python3 scripts/fetch_media.py "nature sunrise" --type video --video-quality best --pexels-video-quality hd --count 3 --output-dir sunrise-video
```

## Sharing Notes

- Do not commit API keys, `.env`, downloaded media folders, or private `manifest.json` files.
- Do not commit `__pycache__/`, `*.pyc`, or `.DS_Store`.
- Share the full skill folder: `SKILL.md`, `README.md`, `scripts/fetch_media.py`, and `agents/openai.yaml`.
- Do not claim assets are copyright-free. Say they are sourced through Pexels/Pixabay free stock APIs and check the provider license/page before final use.
