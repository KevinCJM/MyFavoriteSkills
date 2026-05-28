#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen


DEFAULT_SUB_LANGS = "zh-Hans,zh-Hant,zh-CN,zh-TW,zh,en,en-US,en-GB"
DEFAULT_OUTPUT_SUBDIR = "downloads"
DOUYIN_MOBILE_UA = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
)
DOUYIN_REFERER = "https://www.iesdouyin.com/"


@dataclass
class ProbeInfo:
    title: str
    extractor: str
    has_mp4_video_only: bool
    has_m4a_audio_only: bool
    has_mp4_muxed: bool
    subtitle_langs: list[str]
    auto_subtitle_langs: list[str]


@dataclass
class DouyinFallbackInfo:
    title: str
    video_id: str
    media_url: str
    width: int | None
    height: int | None
    duration: float | None
    subtitle_langs: list[str]
    source_url: str


def run_cmd(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, capture_output=True, check=check)


def dedupe_paths(paths: list[Path]) -> list[Path]:
    unique: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        expanded = path.expanduser()
        key = str(expanded)
        if key in seen:
            continue
        seen.add(key)
        unique.append(expanded)
    return unique


def resolve_output_dir(explicit_output_dir: str | None) -> Path:
    if explicit_output_dir:
        target = Path(explicit_output_dir).expanduser()
        target.mkdir(parents=True, exist_ok=True)
        if not os.access(target, os.W_OK):
            raise RuntimeError(f"输出目录不可写: {target}")
        return target.resolve()

    candidates: list[Path] = []
    for env_name in ("YT_DLP_DOWNLOAD_DIR", "OPENCLAW_DOWNLOAD_DIR"):
        env_output_dir = os.getenv(env_name)
        if env_output_dir:
            candidates.append(Path(env_output_dir))
    candidates.append(Path.cwd() / DEFAULT_OUTPUT_SUBDIR)
    codex_home = os.getenv("CODEX_HOME")
    if codex_home:
        candidates.append(Path(codex_home) / DEFAULT_OUTPUT_SUBDIR)
    candidates.append(Path.home() / ".codex" / DEFAULT_OUTPUT_SUBDIR)
    candidates.append(Path.home() / "Downloads")
    candidates.append(Path.home() / ".openclaw" / DEFAULT_OUTPUT_SUBDIR)

    tmpdir = os.getenv("TMPDIR")
    if tmpdir:
        candidates.append(Path(tmpdir) / "yt-dlp-smart-downloads")
        candidates.append(Path(tmpdir) / "openclaw" / DEFAULT_OUTPUT_SUBDIR)
    candidates.append(Path("/tmp/yt-dlp-smart-downloads"))
    candidates.append(Path("/tmp/openclaw/downloads"))

    for candidate in dedupe_paths(candidates):
        try:
            candidate.mkdir(parents=True, exist_ok=True)
        except OSError:
            continue
        if os.access(candidate, os.W_OK):
            return candidate.resolve()

    raise RuntimeError(
        "无法确定可写下载目录。请通过 --output-dir、YT_DLP_DOWNLOAD_DIR 或 OPENCLAW_DOWNLOAD_DIR 指定目录。"
    )


def resolve_yt_dlp_cmd() -> list[str]:
    ytdlp_bin = shutil.which("yt-dlp")
    if ytdlp_bin:
        try:
            run_cmd([ytdlp_bin, "--version"])
            return [ytdlp_bin]
        except Exception:
            pass
    try:
        run_cmd([sys.executable, "-m", "yt_dlp", "--version"])
        return [sys.executable, "-m", "yt_dlp"]
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(
            f"未找到 yt-dlp。请先安装：{sys.executable} -m pip install -U yt-dlp"
        ) from exc


def append_common_yt_dlp_options(cmd: list[str], args: argparse.Namespace) -> None:
    if args.cookies_from_browser:
        cmd.extend(["--cookies-from-browser", args.cookies_from_browser])


def probe_url(yt_dlp_cmd: list[str], args: argparse.Namespace) -> ProbeInfo:
    cmd = [*yt_dlp_cmd, "-J", "--skip-download"]
    append_common_yt_dlp_options(cmd, args)
    if not args.allow_playlist:
        cmd.append("--no-playlist")
    cmd.append(args.url)
    result = run_cmd(cmd)

    data = json.loads(result.stdout)
    if isinstance(data, dict) and data.get("_type") == "playlist":
        entries = data.get("entries") or []
        first = next((e for e in entries if isinstance(e, dict)), None)
        if first is None:
            raise RuntimeError("播放列表为空，无法选择下载格式")
        data = first

    if not isinstance(data, dict):
        raise RuntimeError("yt-dlp 探测结果异常")

    formats = data.get("formats") or []
    has_mp4_video_only = False
    has_m4a_audio_only = False
    has_mp4_muxed = False

    for fmt in formats:
        if not isinstance(fmt, dict):
            continue
        ext = str(fmt.get("ext") or "")
        vcodec = str(fmt.get("vcodec") or "none")
        acodec = str(fmt.get("acodec") or "none")
        if ext == "mp4" and vcodec != "none" and acodec == "none":
            has_mp4_video_only = True
        if ext == "m4a" and vcodec == "none" and acodec != "none":
            has_m4a_audio_only = True
        if ext == "mp4" and vcodec != "none" and acodec != "none":
            has_mp4_muxed = True

    subtitles = data.get("subtitles") or {}
    auto_subtitles = data.get("automatic_captions") or {}

    return ProbeInfo(
        title=str(data.get("title") or ""),
        extractor=str(data.get("extractor_key") or data.get("extractor") or ""),
        has_mp4_video_only=has_mp4_video_only,
        has_m4a_audio_only=has_m4a_audio_only,
        has_mp4_muxed=has_mp4_muxed,
        subtitle_langs=sorted(subtitles.keys()) if isinstance(subtitles, dict) else [],
        auto_subtitle_langs=sorted(auto_subtitles.keys()) if isinstance(auto_subtitles, dict) else [],
    )


def choose_format(strategy: str, probe: ProbeInfo) -> tuple[str, str]:
    if strategy == "compat":
        if probe.has_mp4_video_only and probe.has_m4a_audio_only:
            return (
                "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/bv*+ba/b",
                "vcodec:h264,acodec:m4a,res,fps,br,size",
            )
        if probe.has_mp4_muxed:
            return ("b[ext=mp4]/bv*+ba/b", "vcodec:h264,acodec:m4a,res,fps,br,size")
        return ("bv*+ba/b", "res,fps,hdr:12,vcodec,acodec,size,br")

    # quality
    return ("bv*+ba/b", "res,fps,hdr:12,vcodec,acodec,size,br")


def build_download_cmd(
    yt_dlp_cmd: list[str], args: argparse.Namespace, fmt: str, sort_expr: str, out_dir: Path
) -> list[str]:
    cmd = [
        *yt_dlp_cmd,
        "-f",
        fmt,
        "-S",
        sort_expr,
        "--write-subs",
        "--sub-langs",
        args.sub_langs,
        "--convert-subs",
        args.convert_subs,
        "-o",
        str(out_dir / "%(title).120B [%(id)s].%(ext)s"),
    ]

    append_common_yt_dlp_options(cmd, args)
    if args.write_auto_subs:
        cmd.append("--write-auto-subs")
    if not args.allow_playlist:
        cmd.append("--no-playlist")

    cmd.append(args.url)
    return cmd


def is_douyin_url(url: str) -> bool:
    return any(host in url for host in ("douyin.com", "iesdouyin.com"))


def extract_douyin_video_id(url: str) -> str | None:
    match = re.search(r"/(?:video|share/video)/(\d+)", url)
    return match.group(1) if match else None


def fetch_text(url: str, user_agent: str) -> str:
    curl_bin = shutil.which("curl")
    if curl_bin:
        result = run_cmd(
            [
                curl_bin,
                "-L",
                "-s",
                "--max-time",
                "45",
                "-A",
                user_agent,
                url,
            ]
        )
        return result.stdout

    request = Request(url, headers={"User-Agent": user_agent})
    try:
        with urlopen(request, timeout=45) as response:  # noqa: S310
            return response.read().decode("utf-8", errors="replace")
    except URLError as exc:
        raise RuntimeError(f"下载页面失败: {exc}") from exc


def find_douyin_item(data: Any) -> dict[str, Any] | None:
    if isinstance(data, dict):
        item_list = data.get("item_list")
        if isinstance(item_list, list):
            for item in item_list:
                if isinstance(item, dict) and item.get("aweme_id") and isinstance(item.get("video"), dict):
                    return item
        for value in data.values():
            found = find_douyin_item(value)
            if found:
                return found
    elif isinstance(data, list):
        for value in data:
            found = find_douyin_item(value)
            if found:
                return found
    return None


def extract_url_list(value: Any) -> list[str]:
    if not isinstance(value, dict):
        return []
    urls = value.get("url_list")
    return [url for url in urls if isinstance(url, str) and url.startswith("http")] if isinstance(urls, list) else []


def collect_douyin_subtitle_langs(item: dict[str, Any]) -> list[str]:
    langs: set[str] = set()

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            lang = value.get("language") or value.get("language_code") or value.get("sub_lang") or value.get("Format")
            if isinstance(lang, str) and lang:
                if any(key in value for key in ("Url", "url", "caption_url", "url_list")):
                    langs.add(lang)
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(item)
    return sorted(langs)


def parse_douyin_router_data(page: str) -> dict[str, Any]:
    match = re.search(r"<script>window\._ROUTER_DATA\s*=\s*(.*?)</script>", page, re.S)
    if not match:
        raise RuntimeError("抖音移动端页面未找到 _ROUTER_DATA")
    return json.loads(html.unescape(match.group(1)))


def extract_douyin_mobile_info(url: str) -> DouyinFallbackInfo:
    candidate_urls = [url]
    video_id = extract_douyin_video_id(url)
    if video_id:
        candidate_urls.append(f"https://www.iesdouyin.com/share/video/{video_id}/")

    errors: list[str] = []
    for candidate_url in dedupe_paths_as_strings(candidate_urls):
        try:
            page = fetch_text(candidate_url, DOUYIN_MOBILE_UA)
            data = parse_douyin_router_data(page)
            item = find_douyin_item(data)
            if not item:
                raise RuntimeError("抖音移动端 SSR 数据未包含视频 item")

            video = item["video"]
            media_urls = extract_url_list(video.get("play_addr"))
            if not media_urls:
                raise RuntimeError("抖音移动端 SSR 数据未包含 play_addr")

            duration_ms = video.get("duration")
            duration = duration_ms / 1000 if isinstance(duration_ms, (int, float)) else None
            return DouyinFallbackInfo(
                title=str(item.get("desc") or item.get("aweme_id") or "douyin-video").strip(),
                video_id=str(item.get("aweme_id") or video_id or "unknown"),
                media_url=media_urls[0],
                width=video.get("width") if isinstance(video.get("width"), int) else None,
                height=video.get("height") if isinstance(video.get("height"), int) else None,
                duration=duration,
                subtitle_langs=collect_douyin_subtitle_langs(item),
                source_url=candidate_url,
            )
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{candidate_url}: {exc}")

    raise RuntimeError("抖音移动端 fallback 失败: " + " | ".join(errors))


def dedupe_paths_as_strings(values: list[str]) -> list[str]:
    unique: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        unique.append(value)
    return unique


def sanitize_filename(name: str, fallback: str) -> str:
    clean = re.sub(r"[\0/\\:*?\"<>|]+", "-", name).strip(" .")
    clean = re.sub(r"\s+", " ", clean)
    return (clean or fallback)[:120]


def download_file(url: str, output_path: Path, user_agent: str, referer: str) -> int:
    curl_bin = shutil.which("curl")
    if curl_bin:
        cmd = [
            curl_bin,
            "-L",
            "--fail",
            "--retry",
            "3",
            "--retry-delay",
            "1",
            "-A",
            user_agent,
            "-H",
            f"referer: {referer}",
            "-o",
            str(output_path),
            url,
        ]
        return subprocess.run(cmd, text=True).returncode

    request = Request(url, headers={"User-Agent": user_agent, "Referer": referer})
    try:
        with urlopen(request, timeout=120) as response, output_path.open("wb") as output:  # noqa: S310
            shutil.copyfileobj(response, output)
        return 0
    except URLError as exc:
        print(json.dumps({"status": "failed", "error": f"下载媒体失败: {exc}"}, ensure_ascii=False), file=sys.stderr)
        return 1


def run_douyin_mobile_fallback(args: argparse.Namespace, output_dir: Path, reason: str) -> int:
    info = extract_douyin_mobile_info(args.url)
    fmt = "douyin-mobile-ssr:play_addr"
    output_file = output_dir / f"{sanitize_filename(info.title, 'douyin-video')} [{info.video_id}].mp4"

    plan: dict[str, Any] = {
        "status": "planned",
        "method": "douyin_mobile_ssr_fallback",
        "fallback_reason": reason,
        "url": args.url,
        "source_url": info.source_url,
        "title": info.title,
        "id": info.video_id,
        "strategy": args.strategy,
        "format_expression": fmt,
        "sort_expression": "mobile SSR play_addr",
        "subtitle_langs_requested": args.sub_langs,
        "available_subtitle_langs": info.subtitle_langs,
        "available_auto_subtitle_langs": [],
        "write_auto_subs": args.write_auto_subs,
        "convert_subs": args.convert_subs,
        "width": info.width,
        "height": info.height,
        "duration": info.duration,
        "output_dir": str(output_dir),
        "output_file": str(output_file),
        "command": shlex.join(
            [
                "curl",
                "-L",
                "--fail",
                "-A",
                DOUYIN_MOBILE_UA,
                "-H",
                f"referer: {DOUYIN_REFERER}",
                "-o",
                str(output_file),
                info.media_url,
            ]
        ),
    }
    if not info.subtitle_langs:
        plan["subtitle_note"] = "该视频未在移动端 SSR 数据中提供可下载字幕"

    print(json.dumps(plan, ensure_ascii=False, indent=2))
    if args.dry_run:
        return 0

    returncode = download_file(info.media_url, output_file, DOUYIN_MOBILE_UA, DOUYIN_REFERER)
    if returncode != 0:
        print(
            json.dumps(
                {
                    "status": "failed",
                    "returncode": returncode,
                    "method": "douyin_mobile_ssr_fallback",
                    "output_file": str(output_file),
                },
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return returncode

    print(
        json.dumps(
            {
                "status": "ok",
                "method": "douyin_mobile_ssr_fallback",
                "strategy": args.strategy,
                "format_expression": fmt,
                "output_dir": str(output_dir),
                "output_file": str(output_file),
                "subtitle_note": plan.get("subtitle_note"),
            },
            ensure_ascii=False,
        )
    )
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="yt-dlp 智能下载（视频+字幕）")
    parser.add_argument("url", help="视频链接")
    parser.add_argument("--strategy", choices=["quality", "compat"], default="quality")
    parser.add_argument(
        "--output-dir",
        default=None,
        help=(
            "输出目录（默认按 YT_DLP_DOWNLOAD_DIR -> OPENCLAW_DOWNLOAD_DIR -> "
            "./downloads -> $CODEX_HOME/downloads -> ~/.codex/downloads -> "
            "~/Downloads -> /tmp/yt-dlp-smart-downloads 回退）"
        ),
    )
    parser.add_argument("--sub-langs", default=DEFAULT_SUB_LANGS, help="字幕语言列表")
    parser.add_argument("--convert-subs", default="srt", help="字幕转换格式")
    parser.add_argument("--no-auto-subs", action="store_true", help="禁用自动字幕回退")
    parser.add_argument("--allow-playlist", action="store_true", help="允许下载播放列表")
    parser.add_argument(
        "--cookies-from-browser",
        default=None,
        help="传给 yt-dlp 的浏览器 cookies 来源，例如 chrome、safari、firefox",
    )
    parser.add_argument(
        "--no-douyin-fallback",
        action="store_true",
        help="禁用抖音移动端 SSR fallback",
    )
    parser.add_argument("--dry-run", action="store_true", help="仅探测并输出计划，不下载")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.write_auto_subs = not args.no_auto_subs

    try:
        output_dir = resolve_output_dir(args.output_dir)
        args.output_dir = str(output_dir)
        yt_dlp_cmd = resolve_yt_dlp_cmd()
        try:
            probe = probe_url(yt_dlp_cmd, args)
        except subprocess.CalledProcessError as exc:
            detail = exc.stderr.strip() if exc.stderr else str(exc)
            if is_douyin_url(args.url) and not args.no_douyin_fallback:
                return run_douyin_mobile_fallback(args, output_dir, detail)
            raise

        fmt, sort_expr = choose_format(args.strategy, probe)
        cmd = build_download_cmd(yt_dlp_cmd, args, fmt, sort_expr, output_dir)

        plan: dict[str, Any] = {
            "status": "planned",
            "method": "yt-dlp",
            "url": args.url,
            "title": probe.title,
            "extractor": probe.extractor,
            "strategy": args.strategy,
            "format_expression": fmt,
            "sort_expression": sort_expr,
            "subtitle_langs_requested": args.sub_langs,
            "available_subtitle_langs": probe.subtitle_langs,
            "available_auto_subtitle_langs": probe.auto_subtitle_langs,
            "write_auto_subs": args.write_auto_subs,
            "convert_subs": args.convert_subs,
            "output_dir": str(output_dir),
            "output_template": str(output_dir / "%(title).120B [%(id)s].%(ext)s"),
            "command": shlex.join(cmd),
        }

        print(json.dumps(plan, ensure_ascii=False, indent=2))

        if args.dry_run:
            return 0

        proc = subprocess.run(cmd, text=True)
        if proc.returncode != 0:
            if is_douyin_url(args.url) and not args.no_douyin_fallback:
                return run_douyin_mobile_fallback(args, output_dir, f"yt-dlp exited {proc.returncode}")
            print(
                json.dumps(
                    {
                        "status": "failed",
                        "returncode": proc.returncode,
                        "command": shlex.join(cmd),
                    },
                    ensure_ascii=False,
                ),
                file=sys.stderr,
            )
            return proc.returncode

        print(
            json.dumps(
                {
                    "status": "ok",
                    "method": "yt-dlp",
                    "strategy": args.strategy,
                    "format_expression": fmt,
                    "output_dir": str(output_dir),
                },
                ensure_ascii=False,
            )
        )
        return 0
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr.strip() if exc.stderr else str(exc)
        print(json.dumps({"status": "failed", "error": detail}, ensure_ascii=False), file=sys.stderr)
        return exc.returncode or 1
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"status": "failed", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
