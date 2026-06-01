# Volcengine Podcast MD to Audio / 火山引擎播客语音合成

## English

A portable Codex skill for converting local Markdown or text articles into a downloaded two-speaker podcast audio file through Volcengine/ByteDance `podcasttts`.

The workflow is server-side generation first: the script requests `input_info.return_audio_url=true`, waits for `PodcastEnd.meta_info.audio_url`, and downloads the completed podcast file. It does not concatenate streamed round audio chunks locally.

### Requirements

- **Required**: Python `3.10+` recommended.
- **Required**: Python packages from `scripts/requirements.txt`.
- **Required**: Network access to Volcengine openspeech WebSocket and the returned audio URL.
- **Required**: Volcengine Speech credentials with access to podcast TTS.
- **Input**: A local `.md` or `.txt` article.

Install Python dependencies:

```bash
python3 -m pip install -r scripts/requirements.txt
```

### Install

Copy the folder to your Codex skills directory:

```bash
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R volcengine-podcast-md-to-audio "${CODEX_HOME:-$HOME/.codex}/skills/"
```

Do not copy `__pycache__/`, `*.pyc`, generated audio, metadata JSON, saved request JSON, or files containing real credentials.

### Credentials

Use podcast-specific environment variables:

```bash
export VOLCENGINE_PODCAST_APP_ID="your-app-id"
export VOLCENGINE_PODCAST_ACCESS_KEY="your-access-token"
```

For persistent shell config on macOS/Linux:

```bash
printf '\nexport VOLCENGINE_PODCAST_APP_ID="your-app-id"\nexport VOLCENGINE_PODCAST_ACCESS_KEY="your-access-token"\n' >> ~/.zshrc
source ~/.zshrc
```

Credential priority:

1. CLI flags: `--app-id`, `--access-key`
2. `VOLCENGINE_PODCAST_APP_ID`, `VOLCENGINE_PODCAST_ACCESS_KEY`
3. Legacy compatibility: `VOLCENGINE_SPEECH_APP_ID`, `VOLCENGINE_SPEECH_ACCESS_KEY`

### Usage

```bash
python3 scripts/md_to_podcast_audio.py \
  --input-md /absolute/path/article.md \
  --output /absolute/path/article_podcast.mp3
```

Choose two speakers:

```bash
python3 scripts/md_to_podcast_audio.py \
  --input-md /absolute/path/article.md \
  --output /absolute/path/article_podcast.mp3 \
  --speaker male_id \
  --speaker female_id
```

Enable intro and outro music:

```bash
python3 scripts/md_to_podcast_audio.py \
  --input-md /absolute/path/article.md \
  --output /absolute/path/article_podcast.mp3 \
  --use-head-music \
  --use-tail-music
```

Override service defaults when Volcengine changes endpoint metadata:

```bash
python3 scripts/md_to_podcast_audio.py \
  --input-md /absolute/path/article.md \
  --output /absolute/path/article_podcast.mp3 \
  --ws-url "wss://openspeech.bytedance.com/api/v3/sami/podcasttts" \
  --resource-id "volc.service_type.10050" \
  --app-key "your-app-key"
```

### Outputs

- Final podcast audio file at `--output`.
- Sidecar metadata JSON at `<output>.metadata.json`.
- Metadata includes `session_id`, `audio_url`, round progress, usage events, and response metadata.

### Notes

- Keep generated work quiet while waiting; podcast generation can be long-running.
- If `PodcastEnd.meta_info.audio_url` is missing, the script fails clearly and writes metadata for debugging.
- Do not fall back to local chunk stitching unless the user explicitly asks for streaming audio inspection or local stream stitching.
- Do not commit Volcengine credentials, `.env` files, generated audio, or metadata containing private URLs.

## 中文

这是一个可移植的 Codex 技能，用于把本地 Markdown 或文本文章通过火山引擎/字节 `podcasttts` 转成双人播客音频，并下载最终音频文件。

该技能采用服务端生成流程：脚本请求 `input_info.return_audio_url=true`，等待 `PodcastEnd.meta_info.audio_url`，然后下载完整播客文件。它不会在本地拼接 streamed round audio chunks。

### 依赖

- **必需**：推荐 Python `3.10+`。
- **必需**：`scripts/requirements.txt` 中的 Python 包。
- **必需**：可以访问火山引擎 openspeech WebSocket 和返回的音频 URL。
- **必需**：拥有 podcast TTS 权限的火山引擎语音凭证。
- **输入**：本地 `.md` 或 `.txt` 文章。

安装依赖：

```bash
python3 -m pip install -r scripts/requirements.txt
```

### 安装

复制整个文件夹到 Codex skills 目录：

```bash
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R volcengine-podcast-md-to-audio "${CODEX_HOME:-$HOME/.codex}/skills/"
```

共享时不要包含 `__pycache__/`、`*.pyc`、生成的音频、metadata JSON、保存的 request JSON，或任何包含真实凭证的文件。

### 凭证

优先使用 podcast 专用环境变量：

```bash
export VOLCENGINE_PODCAST_APP_ID="your-app-id"
export VOLCENGINE_PODCAST_ACCESS_KEY="your-access-token"
```

macOS/Linux 持久化到 shell 配置：

```bash
printf '\nexport VOLCENGINE_PODCAST_APP_ID="your-app-id"\nexport VOLCENGINE_PODCAST_ACCESS_KEY="your-access-token"\n' >> ~/.zshrc
source ~/.zshrc
```

凭证优先级：

1. CLI 参数：`--app-id`、`--access-key`
2. `VOLCENGINE_PODCAST_APP_ID`、`VOLCENGINE_PODCAST_ACCESS_KEY`
3. 旧变量兼容：`VOLCENGINE_SPEECH_APP_ID`、`VOLCENGINE_SPEECH_ACCESS_KEY`

### 使用

```bash
python3 scripts/md_to_podcast_audio.py \
  --input-md /absolute/path/article.md \
  --output /absolute/path/article_podcast.mp3
```

指定两个说话人：

```bash
python3 scripts/md_to_podcast_audio.py \
  --input-md /absolute/path/article.md \
  --output /absolute/path/article_podcast.mp3 \
  --speaker male_id \
  --speaker female_id
```

开启片头和片尾音乐：

```bash
python3 scripts/md_to_podcast_audio.py \
  --input-md /absolute/path/article.md \
  --output /absolute/path/article_podcast.mp3 \
  --use-head-music \
  --use-tail-music
```

当火山服务参数变化时覆盖默认值：

```bash
python3 scripts/md_to_podcast_audio.py \
  --input-md /absolute/path/article.md \
  --output /absolute/path/article_podcast.mp3 \
  --ws-url "wss://openspeech.bytedance.com/api/v3/sami/podcasttts" \
  --resource-id "volc.service_type.10050" \
  --app-key "your-app-key"
```

### 输出

- `--output` 指定的最终播客音频文件。
- `<output>.metadata.json` 旁路元数据。
- 元数据包含 `session_id`、`audio_url`、round 进度、usage events 和响应元信息。

### 注意事项

- 生成过程可能较长，等待时应保持输出简洁。
- 如果 `PodcastEnd.meta_info.audio_url` 缺失，脚本会明确失败并写出 metadata 供排查。
- 除非用户明确要求检查流式音频或本地拼接，否则不要 fallback 到本地 chunk stitching。
- 不要提交火山引擎凭证、`.env` 文件、生成音频，或包含私有 URL 的 metadata。
