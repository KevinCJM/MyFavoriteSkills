---
name: volcengine-podcast-md-to-audio
description: Convert local Markdown or text articles into downloaded Volcengine/ByteDance podcast audio through the openspeech podcasttts WebSocket API. Use when the user wants an article turned into a two-speaker podcast MP3 and wants the final server-generated PodcastEnd audio_url downloaded instead of local audio chunk stitching.
---

# Volcengine Podcast MD To Audio

Use this skill to turn a local Markdown or text article into a complete podcast audio file through Volcengine podcast TTS.

This skill uses `input_info.return_audio_url=true`, waits for `PodcastEnd.meta_info.audio_url`, then downloads that final audio URL.

## Non-Negotiable Rule

- Default mode is `server-generate then direct-download final podcast`.
- Do not assemble, concatenate, stitch, or merge `PodcastRoundResponse` audio chunks locally.
- If the user asks what happens, say: `wait for Volcengine to return the final podcast audio_url, then download the completed mp3`.
- Only touch round audio chunks if the user explicitly asks for streaming audio inspection or local stream stitching.

## Requirements

- Python 3.10+ recommended.
- Python packages: `requests` and `websockets`.
- A local `.md` or `.txt` article path.
- Volcengine Speech credentials:
  - `VOLCENGINE_PODCAST_APP_ID` or `--app-id`
  - `VOLCENGINE_PODCAST_ACCESS_KEY` or `--access-key`

Credential priority:

1. CLI flags: `--app-id`, `--access-key`
2. Podcast-only env vars: `VOLCENGINE_PODCAST_APP_ID`, `VOLCENGINE_PODCAST_ACCESS_KEY`
3. Legacy env vars: `VOLCENGINE_SPEECH_APP_ID`, `VOLCENGINE_SPEECH_ACCESS_KEY`

Prefer podcast-only env vars so other Volcengine tools can use separate credentials.

## Portable Setup

After loading this skill, resolve paths relative to the directory that contains this `SKILL.md`.

Install dependencies:

```bash
cd /path/to/volcengine-podcast-md-to-audio
python3 -m pip install -r scripts/requirements.txt
```

Run the bundled script:

```bash
cd /path/to/volcengine-podcast-md-to-audio
python3 scripts/md_to_podcast_audio.py \
  --input-md /absolute/path/article.md \
  --output /absolute/path/article_podcast.mp3
```

For permanent shell config, add user-owned credentials to `~/.zshrc` or the active shell profile:

```bash
export VOLCENGINE_PODCAST_APP_ID="your-app-id"
export VOLCENGINE_PODCAST_ACCESS_KEY="your-access-token"
```

Do not commit or share real credentials.

## Service Defaults

The script includes known service defaults and lets users override them for migration or service changes:

- WebSocket URL: `VOLCENGINE_PODCAST_WS_URL` or `--ws-url`
- Resource ID: `VOLCENGINE_PODCAST_RESOURCE_ID` or `--resource-id`
- App key: `VOLCENGINE_PODCAST_APP_KEY` or `--app-key`

Default endpoint and IDs:

- `wss://openspeech.bytedance.com/api/v3/sami/podcasttts`
- `volc.service_type.10050`
- `aGjiRDfUWi`

## Workflow

1. Read the article file as UTF-8.
2. Use `action=0` with `input_text` for article-to-podcast generation.
3. Set `input_info.return_audio_url=true`.
4. Set `input_info.input_text_max_length` to `12000` unless the user requests another value.
5. Request `audio_config.format=mp3`, `sample_rate=24000`, `speech_rate=0`.
6. Wait for server-side generation to finish and for `PodcastEnd` event `363`.
7. Extract `meta_info.audio_url` and download that completed podcast to the requested output path.
8. Save a sidecar metadata JSON beside the audio.

## Useful Flags

- `--speaker male_id --speaker female_id` to select exactly two speakers.
- `--speech-rate 0` where valid range is `-50` to `100`.
- `--use-head-music` and `--use-tail-music`.
- `--max-input-length 12000`.
- `--download-timeout 120`.
- `--use-env-proxy` for final audio download proxies.
- `--save-request-json /path/request.json` for debugging.

## Long-Running Execution

- Start the command with a long wait interval, ideally `yield_time_ms=300000`.
- If the process is still running, poll at most once every 5 minutes.
- Keep `max_output_tokens` small during polling because the script is quiet until final success or error.
- In progress updates, describe the job as `waiting for final podcast generation` or `waiting for audio_url`.

## Script Behavior

The script:

- installs nothing automatically;
- supports both newer `websockets` `additional_headers` and older `extra_headers` APIs;
- sends StartConnection, StartSession, FinishSession, and FinishConnection binary frames;
- ignores audio chunk payloads except for progress events;
- fails clearly if `PodcastEnd` does not contain `meta_info.audio_url`;
- downloads the returned URL directly as the final audio file;
- writes `<output>.metadata.json` containing `session_id`, `audio_url`, `rounds`, usage events, and response metadata.

## Sharing Checklist

When sharing this skill, include only:

- `SKILL.md`
- `agents/openai.yaml`
- `scripts/md_to_podcast_audio.py`
- `scripts/requirements.txt`

Exclude `__pycache__`, generated audio, metadata JSON, saved request JSON, and any file containing real credentials.

## When Not To Use

- If the user wants a single-speaker local TTS output, use a local TTS skill instead.
- If the user wants exact narration with no model rewriting, first convert the article into two-speaker `nlp_texts` and extend the script to use `action=3`.
- If the article is longer than the service limit, ask whether to trim, summarize locally first, or split into multiple podcast jobs.
