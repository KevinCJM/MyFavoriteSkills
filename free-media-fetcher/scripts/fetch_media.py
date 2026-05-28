#!/usr/bin/env python3
"""Search and download free stock images/videos from Pixabay and Pexels."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

USER_AGENT = "Codex-Free-Media-Fetcher/1.0"


class ApiError(RuntimeError):
    def __init__(self, provider: str, status: int, message: str):
        self.provider = provider
        self.status = status
        super().__init__(f"{provider} HTTP {status}: {message}")


class MissingKeyError(RuntimeError):
    pass


def request_json(url: str, headers: dict[str, str] | None = None, provider: str = "api") -> dict[str, Any]:
    req = Request(url, headers={"User-Agent": USER_AGENT, **(headers or {})})
    try:
        with urlopen(req, timeout=30) as resp:
            body = resp.read()
    except HTTPError as exc:
        msg = exc.read().decode("utf-8", errors="replace")[:500]
        raise ApiError(provider, exc.code, msg) from exc
    except URLError as exc:
        raise RuntimeError(f"{provider} network error: {exc}") from exc
    return json.loads(body.decode("utf-8"))


def download(url: str, path: Path) -> int:
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=120) as resp:
        data = resp.read()
    path.write_bytes(data)
    return len(data)


def slugify(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9._-]+", "-", value.strip()).strip("-")
    return value[:80] or "media"


def ext_from_url(url: str, fallback: str) -> str:
    clean = url.split("?", 1)[0]
    suffix = Path(clean).suffix.lower()
    if suffix in {".jpg", ".jpeg", ".png", ".webp", ".mp4", ".mov"}:
        return suffix
    return fallback


def provider_orientation(provider: str, orientation: str) -> str:
    if provider == "pexels":
        return {"horizontal": "landscape", "vertical": "portrait"}.get(orientation, orientation)
    if provider == "pixabay":
        return {"landscape": "horizontal", "portrait": "vertical", "square": "all"}.get(orientation, orientation)
    return orientation


def target_aspect_ratio(args: argparse.Namespace) -> float | None:
    ratio = getattr(args, "aspect_ratio", "auto")
    if ratio == "16:9":
        return 16 / 9
    if ratio == "9:16":
        return 9 / 16
    if ratio == "any":
        return None
    if args.orientation in {"vertical", "portrait"}:
        return 9 / 16
    if args.orientation in {"horizontal", "landscape"}:
        return 16 / 9
    return None


def aspect_error(width: Any, height: Any, target: float | None) -> float | None:
    if not target or not width or not height:
        return None
    try:
        actual = float(width) / float(height)
    except (TypeError, ValueError, ZeroDivisionError):
        return None
    return abs(actual - target) / target


def rank_by_aspect(items: list[dict[str, Any]], args: argparse.Namespace) -> list[dict[str, Any]]:
    target = target_aspect_ratio(args)
    if not target:
        return items[: args.count]
    tolerance = max(0.0, float(getattr(args, "aspect_tolerance", 0.18)))
    for item in items:
        error = aspect_error(item.get("width"), item.get("height"), target)
        item["target_aspect_ratio"] = "9:16" if target < 1 else "16:9"
        item["aspect_error"] = error
        item["aspect_match"] = error is not None and error <= tolerance
    return sorted(
        items,
        key=lambda item: (
            item.get("aspect_error") is None,
            item.get("aspect_error") if item.get("aspect_error") is not None else 999,
            -((item.get("width") or 0) * (item.get("height") or 0)),
        ),
    )[: args.count]


def normalize_defaults(args: argparse.Namespace) -> argparse.Namespace:
    if args.orientation in {"vertical", "portrait"}:
        args.orientation = "vertical"
        if args.min_width is None:
            args.min_width = 1080
        if args.min_height is None:
            args.min_height = 1920
        if args.image_size is None:
            args.image_size = "portrait"
    elif args.orientation in {"horizontal", "landscape"}:
        args.orientation = "horizontal"
        if args.min_width is None:
            args.min_width = 1920
        if args.min_height is None:
            args.min_height = 1080
        if args.image_size is None:
            args.image_size = "landscape"
    else:
        if args.min_width is None:
            args.min_width = 0
        if args.min_height is None:
            args.min_height = 0
        if args.image_size is None:
            args.image_size = "large"
    return args


def pick_pixabay_photo(hit: dict[str, Any], size: str) -> str | None:
    fields = {
        "preview": ["previewURL"],
        "medium": ["webformatURL"],
        "large": ["largeImageURL", "webformatURL"],
        "original": ["imageURL", "fullHDURL", "largeImageURL", "webformatURL"],
    }
    for field in fields.get(size, fields["large"]):
        if hit.get(field):
            return hit[field]
    return None


def pick_pixabay_video(hit: dict[str, Any], quality: str) -> str | None:
    videos = hit.get("videos") or {}
    order = {
        "tiny": ["tiny", "small", "medium", "large"],
        "small": ["small", "medium", "tiny", "large"],
        "medium": ["medium", "large", "small", "tiny"],
        "large": ["large", "medium", "small", "tiny"],
        "best": ["large", "medium", "small", "tiny"],
    }.get(quality, ["large", "medium", "small", "tiny"])
    for key in order:
        item = videos.get(key) or {}
        if item.get("url"):
            return item["url"]
    return None


def pixabay_video_dimensions(hit: dict[str, Any], quality: str) -> tuple[Any, Any]:
    videos = hit.get("videos") or {}
    order = {
        "tiny": ["tiny", "small", "medium", "large"],
        "small": ["small", "medium", "tiny", "large"],
        "medium": ["medium", "large", "small", "tiny"],
        "large": ["large", "medium", "small", "tiny"],
        "best": ["large", "medium", "small", "tiny"],
    }.get(quality, ["large", "medium", "small", "tiny"])
    for key in order:
        item = videos.get(key) or {}
        if item.get("url"):
            return item.get("width"), item.get("height")
    return None, None


def pick_pexels_photo(photo: dict[str, Any], size: str) -> str | None:
    src = photo.get("src") or {}
    order = {
        "preview": ["tiny", "small"],
        "medium": ["medium", "large"],
        "large": ["large2x", "large", "original"],
        "original": ["original", "large2x", "large"],
        "landscape": ["landscape", "large2x", "large"],
        "portrait": ["portrait", "large2x", "large"],
    }.get(size, ["large2x", "large", "original"])
    for key in order:
        if src.get(key):
            return src[key]
    return None


def pick_pexels_video(video: dict[str, Any], quality: str, min_width: int, min_height: int) -> str | None:
    files = [f for f in video.get("video_files") or [] if f.get("link")]
    if min_width:
        files = [f for f in files if (f.get("width") or 0) >= min_width]
    if min_height:
        files = [f for f in files if (f.get("height") or 0) >= min_height]
    if not files:
        files = [f for f in video.get("video_files") or [] if f.get("link")]
    if quality in {"sd", "hd", "uhd"}:
        preferred = [f for f in files if f.get("quality") == quality]
        if preferred:
            files = preferred
    files.sort(key=lambda f: ((f.get("width") or 0) * (f.get("height") or 0), f.get("fps") or 0), reverse=True)
    return files[0]["link"] if files else None


def pixabay_items(args: argparse.Namespace, media_type: str) -> list[dict[str, Any]]:
    key = os.environ.get("PIXABAY_API_KEY")
    if not key:
        raise MissingKeyError(
            "PIXABAY_API_KEY is not set. Ask the user to register a free Pixabay API key at pixabay.com "
            "and export it as PIXABAY_API_KEY."
        )
    endpoint = "https://pixabay.com/api/videos/" if media_type == "video" else "https://pixabay.com/api/"
    params: dict[str, Any] = {
        "key": key,
        "q": args.query,
        "per_page": max(3, min(args.count * 2, 200)),
        "safesearch": "true",
    }
    if media_type == "photo":
        params["image_type"] = "photo"
        if args.min_width:
            params["min_width"] = args.min_width
        if args.min_height:
            params["min_height"] = args.min_height
    if args.orientation != "any":
        pixabay_orientation = provider_orientation("pixabay", args.orientation)
        if pixabay_orientation in {"horizontal", "vertical", "all"}:
            params["orientation"] = pixabay_orientation
    data = request_json(endpoint + "?" + urlencode(params), provider="pixabay")
    results = []
    for hit in data.get("hits", []):
        url = pick_pixabay_video(hit, args.video_quality) if media_type == "video" else pick_pixabay_photo(hit, args.image_size)
        if not url:
            continue
        video_width, video_height = pixabay_video_dimensions(hit, args.video_quality) if media_type == "video" else (None, None)
        width = hit.get("imageWidth") if media_type == "photo" else video_width
        height = hit.get("imageHeight") if media_type == "photo" else video_height
        if args.min_width and width and width < args.min_width:
            continue
        if args.min_height and height and height < args.min_height:
            continue
        results.append({
            "provider": "pixabay",
            "type": media_type,
            "id": hit.get("id"),
            "page_url": hit.get("pageURL"),
            "download_url": url,
            "author": hit.get("user"),
            "width": width,
            "height": height,
            "tags": hit.get("tags"),
        })
    return rank_by_aspect(results, args)


def pexels_items(args: argparse.Namespace, media_type: str) -> list[dict[str, Any]]:
    key = os.environ.get("PEXELS_API_KEY")
    if not key:
        raise MissingKeyError(
            "PEXELS_API_KEY is not set. Ask the user to register a free Pexels API key at pexels.com/api "
            "and export it as PEXELS_API_KEY."
        )
    endpoint = "https://api.pexels.com/videos/search" if media_type == "video" else "https://api.pexels.com/v1/search"
    params: dict[str, Any] = {"query": args.query, "per_page": min(args.count * 2, 80)}
    if args.orientation != "any":
        params["orientation"] = provider_orientation("pexels", args.orientation)
    if media_type == "photo" and args.pexels_size != "any":
        params["size"] = args.pexels_size
    data = request_json(endpoint + "?" + urlencode(params), {"Authorization": key}, provider="pexels")
    rows = data.get("videos" if media_type == "video" else "photos", [])
    results = []
    for row in rows:
        url = pick_pexels_video(row, args.pexels_video_quality, args.min_width, args.min_height) if media_type == "video" else pick_pexels_photo(row, args.image_size)
        if not url:
            continue
        user = row.get("user") or {}
        results.append({
            "provider": "pexels",
            "type": media_type,
            "id": row.get("id"),
            "page_url": row.get("url"),
            "download_url": url,
            "author": row.get("photographer") or user.get("name"),
            "width": row.get("width"),
            "height": row.get("height"),
        })
    return rank_by_aspect(results, args)


def collect(args: argparse.Namespace) -> list[dict[str, Any]]:
    types = ["photo", "video"] if args.type == "all" else [args.type]
    out: list[dict[str, Any]] = []
    if args.provider == "auto":
        for media_type in types:
            try:
                pexels = pexels_items(args, media_type)
                out.extend(pexels)
                if len(pexels) >= args.count:
                    continue
                # Fill sparse Pexels results from Pixabay while keeping Pexels first.
                fallback_args = argparse.Namespace(**vars(args))
                fallback_args.count = args.count - len(pexels)
                out.extend(pixabay_items(fallback_args, media_type))
            except ApiError as exc:
                if exc.provider == "pexels" and (exc.status in {403, 429} or "quota" in str(exc).lower()):
                    print(f"warning: Pexels quota/limit issue, falling back to Pixabay for {media_type}", file=sys.stderr)
                    out.extend(pixabay_items(args, media_type))
                else:
                    raise
        return out

    providers = ["pexels", "pixabay"] if args.provider == "both" else [args.provider]
    for provider in providers:
        for media_type in types:
            if provider == "pixabay":
                out.extend(pixabay_items(args, media_type))
            else:
                out.extend(pexels_items(args, media_type))
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Search/download free media from Pixabay and Pexels.")
    parser.add_argument("query", help="Search query, e.g. 'forest', 'city night', 'technology'.")
    parser.add_argument("--provider", choices=["auto", "pexels", "pixabay", "both"], default="auto")
    parser.add_argument("--type", choices=["photo", "video", "all"], default="all")
    parser.add_argument("--count", type=int, default=3, help="Items per provider/type.")
    parser.add_argument("--output-dir", default="free-media-downloads")
    parser.add_argument("--orientation", choices=["any", "horizontal", "vertical", "landscape", "portrait", "square"], default="horizontal", help="Default is horizontal/16:9. Use vertical or portrait for 9:16.")
    parser.add_argument("--min-width", type=int, default=None)
    parser.add_argument("--min-height", type=int, default=None)
    parser.add_argument("--aspect-ratio", choices=["auto", "16:9", "9:16", "any"], default="auto", help="Default auto maps horizontal to 16:9 and vertical to 9:16.")
    parser.add_argument("--aspect-tolerance", type=float, default=0.18, help="Relative tolerance for ranking aspect-ratio matches.")
    parser.add_argument("--image-size", choices=["preview", "medium", "large", "original", "landscape", "portrait"], default=None)
    parser.add_argument("--video-quality", choices=["tiny", "small", "medium", "large", "best"], default="large", help="Pixabay video size preference.")
    parser.add_argument("--pexels-size", choices=["any", "small", "medium", "large"], default="any", help="Pexels photo search size filter.")
    parser.add_argument("--pexels-video-quality", choices=["any", "sd", "hd", "uhd"], default="hd")
    parser.add_argument("--dry-run", action="store_true", help="Print metadata but do not download files.")
    args = normalize_defaults(parser.parse_args())

    items = collect(args)
    outdir = Path(args.output_dir)
    if not args.dry_run:
        outdir.mkdir(parents=True, exist_ok=True)

    manifest = []
    for index, item in enumerate(items, 1):
        fallback = ".mp4" if item["type"] == "video" else ".jpg"
        ext = ext_from_url(item["download_url"], fallback)
        filename = f"{index:02d}-{item['provider']}-{item['type']}-{slugify(str(item.get('id') or args.query))}{ext}"
        record = {**item, "filename": filename}
        if args.dry_run:
            print(json.dumps(record, ensure_ascii=False))
        else:
            size = download(item["download_url"], outdir / filename)
            record["bytes"] = size
            print(f"downloaded {filename} ({size} bytes)")
            time.sleep(0.2)
        manifest.append(record)

    if not args.dry_run:
        (outdir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"manifest: {outdir / 'manifest.json'}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
