---
name: free-media-fetcher
description: Search and download free stock photos and videos from Pixabay and Pexels using local PIXABAY_API_KEY and PEXELS_API_KEY environment variables. Use when the user asks to get, fetch, download, source, collect, or test free/open stock images or videos from pixabay.com or pexels.com, including requests for 16:9 horizontal media, 9:16 vertical media, resolution, size, orientation, width, height, quality, attribution, or metadata.
---

# Free Media Fetcher

## Quick Start

Use `scripts/fetch_media.py` to search Pixabay/Pexels and optionally download media. The script only uses Python standard library modules and reads API keys from environment variables:

- `PEXELS_API_KEY` for Pexels photos/videos
- `PIXABAY_API_KEY` for Pixabay photos/videos

Run commands from the skill folder when possible:

```bash
python3 scripts/fetch_media.py "forest" --type all --count 3 --dry-run
```

```bash
python3 scripts/fetch_media.py "forest" --type all --count 3 --output-dir media
```

If the current working directory is not the skill folder, locate the script portably:

```bash
FREE_MEDIA_FETCHER_SCRIPT="${FREE_MEDIA_FETCHER_SCRIPT:-${CODEX_HOME:-$HOME/.codex}/skills/free-media-fetcher/scripts/fetch_media.py}"
python3 "$FREE_MEDIA_FETCHER_SCRIPT" "forest" --type all --count 3 --dry-run
```

## Installation And Setup

1. Install Python 3 if missing.
2. Register a free Pexels API key at `https://www.pexels.com/api/`.
3. Register a free Pixabay API key at `https://pixabay.com/api/docs/` or from your Pixabay account page.
4. Export the keys in the current shell or shell profile.
5. Run a dry-run before downloading.

macOS/Linux `zsh` or `bash`:

```bash
export PEXELS_API_KEY="your_pexels_key"
export PIXABAY_API_KEY="your_pixabay_key"
python3 scripts/fetch_media.py "city skyline" --type photo --count 3 --dry-run
```

Windows PowerShell:

```powershell
$env:PEXELS_API_KEY="your_pexels_key"
$env:PIXABAY_API_KEY="your_pixabay_key"
python scripts/fetch_media.py "city skyline" --type photo --count 3 --dry-run
```

Security rules:

- Never write API keys into `SKILL.md`, `README.md`, Git history, screenshots, or shared logs.
- Never print full API keys; only show masked status such as whether a key exists.
- Do not commit `.env`, downloaded media folders, or private manifests unless the user explicitly wants sample artifacts.

## Default Aspect Ratio Policy

Default behavior is horizontal, 16:9-oriented media:

- Default `--orientation` is `horizontal`.
- Default minimum size becomes `--min-width 1920 --min-height 1080`.
- Default Pexels photo asset preference becomes `--image-size landscape`.
- Results are ranked toward the closest `16:9` aspect ratio.

If the user explicitly asks for vertical, portrait, Shorts, TikTok, Reels, phone, or 9:16 media, use vertical mode:

```bash
python3 scripts/fetch_media.py "city night" --type video --orientation vertical --count 3 --output-dir city-night-vertical
```

Vertical mode means:

- `--orientation vertical`
- default minimum size `--min-width 1080 --min-height 1920`
- default Pexels photo asset preference `--image-size portrait`
- results ranked toward the closest `9:16` aspect ratio

Use `--aspect-ratio any` or `--orientation any` only when the user explicitly does not care about layout.

## API Key Behavior

- Prefer `--provider auto`: try Pexels first, then fall back to Pixabay when Pexels quota/rate limits are hit or when Pexels has too few results.
- If `PEXELS_API_KEY` is missing and provider is `auto` or `pexels`, stop and ask the human to configure it.
- If Pixabay is needed and `PIXABAY_API_KEY` is missing, stop and ask the human to configure it.
- Prefer dry-run first when the user wants to inspect options; download when they ask to fetch/save assets.

## Resolution And Size Controls

- Use `--orientation horizontal|vertical|landscape|portrait|square|any` for aspect direction.
- Use `--aspect-ratio auto|16:9|9:16|any` to control aspect ranking.
- Use `--aspect-tolerance 0.18` to control how strict the aspect match metadata is.
- Use `--min-width 1920 --min-height 1080` for horizontal HD assets.
- Use `--min-width 1080 --min-height 1920` for vertical HD assets.
- Use `--image-size preview|medium|large|original|landscape|portrait` for returned image asset size.
- Use `--video-quality tiny|small|medium|large|best` for Pixabay video size preference.
- Use `--pexels-video-quality sd|hd|uhd|any` for Pexels video quality preference.
- Use `--pexels-size small|medium|large|any` for Pexels photo search size filtering.

Example: get horizontal 16:9 HD-ish videos:

```bash
python3 scripts/fetch_media.py "city night" --type video --count 3 --video-quality best --pexels-video-quality hd --output-dir city-night-media
```

Example: get vertical 9:16 videos:

```bash
python3 scripts/fetch_media.py "city night" --type video --orientation vertical --count 3 --pexels-video-quality hd --output-dir city-night-vertical
```

## Workflow

1. Confirm required local API keys exist with masked output if needed; never print full keys.
2. Use Pexels first via `--provider auto`; only use Pixabay first when the user explicitly asks for Pixabay.
3. Default to horizontal 16:9 unless the user explicitly asks for vertical/portrait/9:16.
4. Run dry-run for broad searches or quality-sensitive requests.
5. Choose provider/type/count and resolution flags from the user's request.
6. Download into a clear folder under the current project unless the user specifies another path.
7. Return concise results: downloaded paths, provider page URLs, `manifest.json`, and any notable gaps.

## Purpose-Based Selection

When the user gives a clear purpose, do not use the first result blindly.

1. Search/download 3 candidates for the requested media type, e.g. `--count 3`.
2. Inspect the candidates:
   - For images, use the local image viewer tool when available or generate contact sheets/thumbnails.
   - For videos, extract representative frames with `ffmpeg` or `ffprobe` when available; inspect thumbnails, duration, aspect ratio, and composition.
3. Pick the best candidate for the stated use case: subject fit, composition, orientation, resolution, lack of distracting watermarks/text, and compatibility with the target layout.
4. Keep `manifest.json`; if discarding candidates, say which file was selected and why.

## Attribution And Licensing Notes

- Treat returned `page_url`, `author`, and `manifest.json` as important attribution/traceability metadata.
- Do not claim assets are copyright-free; say they are sourced through Pixabay/Pexels free stock APIs and advise checking the provider license/page for final use.
- Keep `manifest.json` with delivered assets so later workflows can cite source pages.
