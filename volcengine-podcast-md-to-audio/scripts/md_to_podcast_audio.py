#!/usr/bin/env python3
"""Convert a Markdown article to a downloaded Volcengine podcast audio file.

This client uses the Volcengine openspeech podcasttts WebSocket API, waits for
PodcastEnd.meta_info.audio_url, then downloads that complete audio URL. It does
not concatenate streamed audio chunks locally.
"""

from __future__ import annotations

import argparse
import asyncio
import gzip
import inspect
import json
import os
import struct
import sys
import uuid
from json import JSONDecodeError
from pathlib import Path
from typing import Any

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None

try:
    import websockets
except ImportError:  # pragma: no cover
    websockets = None


DEFAULT_WS_URL = "wss://openspeech.bytedance.com/api/v3/sami/podcasttts"
DEFAULT_RESOURCE_ID = "volc.service_type.10050"
DEFAULT_APP_KEY = "aGjiRDfUWi"

EVENT_START_CONNECTION = 1
EVENT_FINISH_CONNECTION = 2
EVENT_CONNECTION_STARTED = 50
EVENT_CONNECTION_FINISHED = 52
EVENT_START_SESSION = 100
EVENT_FINISH_SESSION = 102
EVENT_SESSION_STARTED = 150
EVENT_SESSION_FINISHED = 152
EVENT_USAGE = 154
EVENT_ROUND_START = 360
EVENT_ROUND_RESPONSE = 361
EVENT_ROUND_END = 362
EVENT_PODCAST_END = 363


def env_first(*names: str) -> str | None:
    for name in names:
        value = os.getenv(name)
        if value:
            return value
    return None


def websocket_connect(ws_url: str, headers: dict[str, str]):
    if websockets is None:
        raise SystemExit("Missing dependency: websockets. Install with: python3 -m pip install -r scripts/requirements.txt")
    params = inspect.signature(websockets.connect).parameters
    header_arg = "additional_headers" if "additional_headers" in params else "extra_headers"
    return websockets.connect(ws_url, **{header_arg: headers}, max_size=None)


def u32(value: int) -> bytes:
    return struct.pack(">I", value)


def read_u32(data: bytes, offset: int) -> tuple[int, int]:
    if offset + 4 > len(data):
        raise ValueError("frame ended while reading uint32")
    return struct.unpack(">I", data[offset : offset + 4])[0], offset + 4


def make_header(message_type: int = 0x1, flags: int = 0x4, serialization: int = 0x1, compression: int = 0x0) -> bytes:
    # v1, 4-byte header
    return bytes([0x11, ((message_type & 0xF) << 4) | (flags & 0xF), ((serialization & 0xF) << 4) | (compression & 0xF), 0x00])


def json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def pack_connection_event(event: int, payload: dict[str, Any] | None = None) -> bytes:
    body = json_bytes(payload or {})
    return make_header() + u32(event) + u32(len(body)) + body


def pack_session_event(event: int, session_id: str, payload: dict[str, Any] | None = None) -> bytes:
    sid = session_id.encode("utf-8")
    body = json_bytes(payload or {})
    return make_header() + u32(event) + u32(len(sid)) + sid + u32(len(body)) + body


def parse_payload(payload: bytes, serialization: int, compression: int) -> Any:
    if compression == 0x1:
        payload = gzip.decompress(payload)
    if serialization == 0x1:
        if not payload:
            return {}
        try:
            return json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, JSONDecodeError):
            return payload
    return payload


def parse_frame(frame: bytes) -> dict[str, Any]:
    if len(frame) < 4:
        raise ValueError("frame too short")
    header_size = (frame[0] & 0x0F) * 4
    message_type = frame[1] >> 4
    flags = frame[1] & 0x0F
    serialization = frame[2] >> 4
    compression = frame[2] & 0x0F
    offset = header_size

    if message_type == 0xF:
        error_code, offset = read_u32(frame, offset)
        if offset + 4 <= len(frame):
            payload_len, offset = read_u32(frame, offset)
            payload_bytes = frame[offset : offset + payload_len]
        else:
            payload_bytes = frame[offset:]
        payload = parse_payload(payload_bytes, serialization, compression)
        return {
            "message_type": message_type,
            "event": None,
            "error_code": error_code,
            "payload": payload,
            "session_id": None,
        }

    event = None
    if flags & 0x4:
        event, offset = read_u32(frame, offset)

    session_id = None
    payload = b""
    if offset < len(frame):
        first_len, offset = read_u32(frame, offset)
        # Event frames normally carry id_len + id + payload_len + payload.
        # FinishConnection style frames may carry payload_len + payload only.
        if offset + first_len + 4 <= len(frame):
            possible_id = frame[offset : offset + first_len]
            try:
                session_id = possible_id.decode("utf-8")
                offset += first_len
                payload_len, offset = read_u32(frame, offset)
                payload = frame[offset : offset + payload_len]
            except UnicodeDecodeError:
                payload = possible_id
        elif offset + first_len <= len(frame):
            payload = frame[offset : offset + first_len]

    return {
        "message_type": message_type,
        "event": event,
        "error_code": None,
        "payload": payload if event == EVENT_ROUND_RESPONSE else parse_payload(payload, serialization, compression),
        "session_id": session_id,
    }


def strip_markdown_for_input(text: str) -> str:
    # Keep Markdown mostly intact; only remove local image references that waste context.
    lines: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("![") and "](" in stripped:
            continue
        lines.append(line)
    return "\n".join(lines).strip()


def build_payload(args: argparse.Namespace, article_text: str) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "input_id": args.input_id,
        "action": 0,
        "input_text": article_text,
        "use_head_music": args.use_head_music,
        "use_tail_music": args.use_tail_music,
        "aigc_watermark": args.aigc_watermark,
        "input_info": {
            "return_audio_url": True,
            "input_text_max_length": args.max_input_length,
        },
        "audio_config": {
            "format": args.format,
            "sample_rate": args.sample_rate,
            "speech_rate": args.speech_rate,
        },
    }
    if args.max_char_length_per_round:
        payload["input_info"]["max_char_length_per_round"] = args.max_char_length_per_round
    if args.speaker:
        if len(args.speaker) != 2:
            raise SystemExit("--speaker must be passed exactly twice because podcast synthesis requires two speakers")
        payload["speaker_info"] = {
            "random_order": args.random_order,
            "speakers": args.speaker,
        }
    return payload


async def call_podcast_api(args: argparse.Namespace, payload: dict[str, Any]) -> dict[str, Any]:
    request_id = args.request_id or str(uuid.uuid4())
    session_id = args.session_id or str(uuid.uuid4())
    headers = {
        "X-Api-App-Id": args.app_id,
        "X-Api-Access-Key": args.access_key,
        "X-Api-Resource-Id": args.resource_id,
        "X-Api-App-Key": args.app_key,
        "X-Api-Request-Id": request_id,
    }

    audio_url = None
    rounds: list[dict[str, Any]] = []
    usage: list[dict[str, Any]] = []
    podcast_end_payload: dict[str, Any] | None = None

    async with websocket_connect(args.ws_url, headers) as ws:
        response_headers = dict(getattr(ws, "response_headers", {}) or {})
        if not response_headers:
            response = getattr(ws, "response", None)
            response_headers = dict(getattr(response, "headers", {}) or {})
        if not args.no_start_connection:
            await ws.send(pack_connection_event(EVENT_START_CONNECTION, {}))
            while True:
                event = parse_frame(await ws.recv())
                if event["message_type"] == 0xF:
                    raise RuntimeError(f"connection error {event['error_code']}: {event['payload']}")
                if event["event"] == EVENT_CONNECTION_STARTED:
                    break
                # Some deployments may skip ConnectionStarted; continue until observed.

        await ws.send(pack_session_event(EVENT_START_SESSION, session_id, payload))

        while True:
            event = parse_frame(await ws.recv())
            event_code = event["event"]
            data = event["payload"]
            if event["message_type"] == 0xF:
                raise RuntimeError(f"service error {event['error_code']}: {data}")
            if event_code == EVENT_SESSION_STARTED:
                continue
            if event_code == EVENT_USAGE:
                usage.append(data)
                continue
            if event_code == EVENT_ROUND_START:
                if isinstance(data, dict):
                    rounds.append({"start": data})
                continue
            if event_code == EVENT_ROUND_RESPONSE:
                # Audio bytes are intentionally ignored. This skill downloads final audio_url.
                continue
            if event_code == EVENT_ROUND_END:
                if isinstance(data, dict):
                    if rounds and "end" not in rounds[-1]:
                        rounds[-1]["end"] = data
                    else:
                        rounds.append({"end": data})
                continue
            if event_code == EVENT_PODCAST_END:
                podcast_end_payload = data if isinstance(data, dict) else {}
                meta = podcast_end_payload.get("meta_info") or {}
                audio_url = meta.get("audio_url")
                break
            if event_code == EVENT_SESSION_FINISHED:
                break

        try:
            await ws.send(pack_session_event(EVENT_FINISH_SESSION, session_id, {}))
        except Exception:
            pass
        try:
            await ws.send(pack_connection_event(EVENT_FINISH_CONNECTION, {}))
        except Exception:
            pass

    return {
        "request_id": request_id,
        "session_id": session_id,
        "response_headers": response_headers,
        "audio_url": audio_url,
        "rounds": rounds,
        "usage": usage,
        "podcast_end": podcast_end_payload,
    }


def download_audio(url: str, output: Path, timeout: int, use_env_proxy: bool = False) -> None:
    if requests is None:
        raise SystemExit("Missing dependency: requests. Install with: python3 -m pip install -r scripts/requirements.txt")
    output.parent.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.trust_env = use_env_proxy
    with session.get(url, stream=True, timeout=timeout) as response:
        response.raise_for_status()
        tmp = output.with_suffix(output.suffix + ".part")
        with tmp.open("wb") as fh:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    fh.write(chunk)
        tmp.replace(output)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert Markdown to Volcengine podcast audio by downloading PodcastEnd audio_url.")
    parser.add_argument("--input-md", required=True, help="Local Markdown or text file path.")
    parser.add_argument("--output", help="Output audio path. Defaults to <input>_podcast.mp3.")
    parser.add_argument(
        "--app-id",
        default=env_first("VOLCENGINE_PODCAST_APP_ID", "VOLCENGINE_SPEECH_APP_ID"),
        help="Volcengine podcast APP ID. Priority: CLI, VOLCENGINE_PODCAST_APP_ID, VOLCENGINE_SPEECH_APP_ID.",
    )
    parser.add_argument(
        "--access-key",
        default=env_first("VOLCENGINE_PODCAST_ACCESS_KEY", "VOLCENGINE_SPEECH_ACCESS_KEY"),
        help="Volcengine podcast Access Token. Priority: CLI, VOLCENGINE_PODCAST_ACCESS_KEY, VOLCENGINE_SPEECH_ACCESS_KEY.",
    )
    parser.add_argument(
        "--ws-url",
        default=env_first("VOLCENGINE_PODCAST_WS_URL") or DEFAULT_WS_URL,
        help="Podcast WebSocket URL. Defaults to VOLCENGINE_PODCAST_WS_URL or the public openspeech endpoint.",
    )
    parser.add_argument(
        "--resource-id",
        default=env_first("VOLCENGINE_PODCAST_RESOURCE_ID") or DEFAULT_RESOURCE_ID,
        help="X-Api-Resource-Id. Defaults to VOLCENGINE_PODCAST_RESOURCE_ID or the known podcasttts resource id.",
    )
    parser.add_argument(
        "--app-key",
        default=env_first("VOLCENGINE_PODCAST_APP_KEY") or DEFAULT_APP_KEY,
        help="X-Api-App-Key. Defaults to VOLCENGINE_PODCAST_APP_KEY or the known podcasttts app key.",
    )
    parser.add_argument("--input-id", default=None, help="Business input_id. Defaults to md filename stem plus random suffix.")
    parser.add_argument("--request-id", default=None, help="Optional X-Api-Request-Id UUID.")
    parser.add_argument("--session-id", default=None, help="Optional StartSession session_id. Also acts as retry task id.")
    parser.add_argument("--format", default="mp3", choices=["mp3", "ogg_opus", "pcm", "aac"])
    parser.add_argument("--sample-rate", type=int, default=24000, choices=[16000, 24000, 48000])
    parser.add_argument("--speech-rate", type=int, default=0)
    parser.add_argument("--max-input-length", type=int, default=12000)
    parser.add_argument("--max-char-length-per-round", type=int, default=None)
    parser.add_argument("--speaker", action="append", help="Speaker id. Pass exactly twice to set a speaker pair.")
    parser.add_argument("--random-order", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--use-head-music", action="store_true")
    parser.add_argument("--use-tail-music", action="store_true")
    parser.add_argument("--aigc-watermark", action="store_true")
    parser.add_argument("--use-env-proxy", action="store_true", help="Let the final audio download inherit HTTP(S)/ALL_PROXY environment variables.")
    parser.add_argument("--download-timeout", type=int, default=120, help="Final audio download timeout in seconds.")
    parser.add_argument("--no-start-connection", action="store_true", help="Skip StartConnection frame if a deployment expects StartSession immediately.")
    parser.add_argument("--save-request-json", help="Write the request payload JSON for debugging.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    if not args.app_id:
        raise SystemExit("Missing --app-id, VOLCENGINE_PODCAST_APP_ID, or VOLCENGINE_SPEECH_APP_ID")
    if not args.access_key:
        raise SystemExit("Missing --access-key, VOLCENGINE_PODCAST_ACCESS_KEY, or VOLCENGINE_SPEECH_ACCESS_KEY")
    input_path = Path(args.input_md).expanduser().resolve()
    if not input_path.is_file():
        raise SystemExit(f"Input file not found: {input_path}")
    if args.input_id is None:
        args.input_id = f"{input_path.stem}_{uuid.uuid4().hex[:8]}"
    output = Path(args.output).expanduser().resolve() if args.output else input_path.with_name(f"{input_path.stem}_podcast.mp3")

    article_text = strip_markdown_for_input(input_path.read_text(encoding="utf-8"))
    if not article_text:
        raise SystemExit("Input article is empty after basic cleanup")
    payload = build_payload(args, article_text)
    if args.save_request_json:
        Path(args.save_request_json).expanduser().resolve().write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    result = asyncio.run(call_podcast_api(args, payload))
    audio_url = result.get("audio_url")
    if not audio_url:
        metadata_path = output.with_suffix(output.suffix + ".metadata.json")
        metadata_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        raise SystemExit(f"PodcastEnd did not return meta_info.audio_url. Metadata saved: {metadata_path}")

    result["output"] = str(output)
    metadata_path = output.with_suffix(output.suffix + ".metadata.json")
    metadata_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    download_audio(audio_url, output, timeout=args.download_timeout, use_env_proxy=args.use_env_proxy)
    print(json.dumps({"status": "succeeded", "output": str(output), "metadata": str(metadata_path), "session_id": result["session_id"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
