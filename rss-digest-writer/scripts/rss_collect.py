#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta
from email.utils import parsedate_to_datetime
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable, Optional
from urllib.parse import urlparse


DEFAULT_USER_AGENT = "rss-digest-writer/2.0"
SKILL_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_AI_SOURCE_PACK = SKILL_ROOT / "references" / "default-ai-source-pack.json"
LEGACY_DEFAULT_AI_FEEDS_FILE = SKILL_ROOT / "references" / "default-ai-feeds.txt"


@dataclass
class FeedEntry:
    title: str
    url: str
    published_date: Optional[str]
    feed_url: str
    source_kind: str = "rss"
    source_label: str = ""
    source_domain: str = ""
    summary: str = ""
    content: str = ""
    content_chars: int = 0


@dataclass
class SourceDescriptor:
    kind: str
    label: str
    value: str
    optional: bool = False


class SimpleArticleExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.skip_depth = 0
        self.capture_tag: Optional[str] = None
        self.chunks: list[str] = []
        self.skip_tags = {"script", "style", "noscript", "svg", "form", "nav", "footer", "header", "aside"}
        self.capture_tags = {"title", "h1", "h2", "h3", "p", "li", "blockquote", "article", "main", "section"}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        if tag in self.skip_tags:
            self.skip_depth += 1
            return
        if self.skip_depth == 0 and tag in self.capture_tags:
            self.capture_tag = tag

    def handle_endtag(self, tag: str) -> None:
        if tag in self.skip_tags and self.skip_depth > 0:
            self.skip_depth -= 1
            return
        if tag == self.capture_tag:
            self.capture_tag = None

    def handle_data(self, data: str) -> None:
        if self.skip_depth > 0 or not self.capture_tag:
            return
        cleaned = clean_text(data)
        if not cleaned:
            return
        if self.capture_tag in {"title", "h1", "h2", "h3"} or len(cleaned) >= 40:
            self.chunks.append(cleaned)

    def get_text(self) -> str:
        deduped: list[str] = []
        seen: set[str] = set()
        for chunk in self.chunks:
            if chunk in seen:
                continue
            seen.add(chunk)
            deduped.append(chunk)
        return "\n\n".join(deduped)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect RSS-compatible sources for trend monitoring. Defaults can use the bundled AI source pack.")
    parser.add_argument("--feed", action="append", default=[], help="RSS or Atom feed URL. Repeat for multiple feeds.")
    parser.add_argument("--feeds-file", help="Path to a file containing one feed URL per line.")
    parser.add_argument("--use-default-ai-sources", action="store_true", help="Include the bundled AI source pack.")
    parser.add_argument(
        "--use-default-ai-feeds",
        action="store_true",
        help="Backward-compatible alias for --use-default-ai-sources.",
    )
    parser.add_argument("--source-pack", help="Path to a JSON source pack.")
    parser.add_argument("--default-feeds-file", help="Override the legacy raw feed list file.")
    parser.add_argument("--date", default="latest", help="today, yesterday, latest, or YYYY-MM-DD.")
    parser.add_argument("--date-from", help="Start date in YYYY-MM-DD format.")
    parser.add_argument("--date-to", help="End date in YYYY-MM-DD format.")
    parser.add_argument("--days-back", type=int, help="Look back this many calendar days including today.")
    parser.add_argument("--limit", type=int, default=12, help="Maximum number of items to keep.")
    parser.add_argument("--per-source-limit", type=int, default=2, help="Soft cap per source label before backfilling.")
    parser.add_argument("--fallback-recent", type=int, default=8, help="Fallback item count when target date has no hits.")
    parser.add_argument("--fetch-content", action="store_true", help="Fetch article bodies after selecting items.")
    parser.add_argument("--content-chars", type=int, default=8000, help="Maximum number of article characters to keep.")
    parser.add_argument("--crawl-timeout", type=int, default=30, help="Per-article fetch timeout in seconds.")
    parser.add_argument("--feed-timeout", type=int, default=20, help="Per-feed fetch timeout in seconds.")
    parser.add_argument("--concurrency", type=int, default=4, help="Worker count when fetching article bodies.")
    parser.add_argument("--output", help="Optional JSON output path. If omitted, JSON is written to stdout.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    return parser.parse_args()


def clean_text(text: str) -> str:
    text = unescape(text or "")
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def read_text(url: str, timeout: int, redirect_limit: int = 3) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": DEFAULT_USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            return response.read().decode(charset, errors="replace")
    except urllib.error.HTTPError as exc:
        location = exc.headers.get("Location")
        if redirect_limit > 0 and exc.code in {301, 302, 303, 307, 308} and location:
            return read_text(location, timeout, redirect_limit - 1)
        raise


def read_feed_lines(path: Path) -> list[str]:
    feeds: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            feeds.append(line)
    return feeds


def infer_source_kind(feed_url: str, item_url: str = "") -> str:
    values = f"{feed_url} {item_url}".lower()
    if "reddit.com" in values:
        return "reddit"
    if "youtube.com" in values or "youtu.be" in values:
        return "youtube"
    if "mp.weixin.qq.com" in values or "weixin.qq.com" in values:
        return "wechat_rss"
    return "rss"


def default_label_for_feed(feed_url: str) -> str:
    parsed = urlparse(feed_url)
    return parsed.netloc or feed_url


def normalize_source_descriptor(raw: dict, pack_path: Path) -> list[SourceDescriptor]:
    kind = str(raw.get("kind", "")).strip()
    label = str(raw.get("label", "")).strip()
    optional = bool(raw.get("optional", False))
    if not kind:
        return []

    if kind == "local_feeds_file":
        raw_path = str(raw.get("path", "")).strip()
        if not raw_path:
            return []
        path = Path(raw_path)
        if not path.is_absolute():
            path = (pack_path.parent / path).resolve()
        if not path.exists():
            if optional:
                return []
            raise FileNotFoundError(f"Missing source file: {path}")
        file_kind = str(raw.get("file_kind", "wechat_rss")).strip() or "wechat_rss"
        descriptors: list[SourceDescriptor] = []
        for idx, feed_url in enumerate(read_feed_lines(path), start=1):
            feed_label = f"{label} #{idx}" if label else default_label_for_feed(feed_url)
            descriptors.append(SourceDescriptor(kind=file_kind, label=feed_label, value=feed_url, optional=optional))
        return descriptors

    value = str(raw.get("url") or raw.get("feed_url") or raw.get("channel_url") or raw.get("subreddit") or "").strip()
    if not value:
        return []
    if not label:
        label = value
    return [SourceDescriptor(kind=kind, label=label, value=value, optional=optional)]


def read_source_pack(path: Path) -> list[SourceDescriptor]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    descriptors: list[SourceDescriptor] = []
    for raw in payload.get("sources", []):
        if not isinstance(raw, dict):
            continue
        descriptors.extend(normalize_source_descriptor(raw, path))
    return descriptors


def resolve_sources(
    feed_args: list[str],
    feeds_file: Optional[str],
    use_default_ai_sources: bool,
    source_pack: Optional[str],
    default_feeds_file: Optional[str],
) -> tuple[list[SourceDescriptor], list[SourceDescriptor]]:
    feed_sources: list[SourceDescriptor] = []
    deferred_sources: list[SourceDescriptor] = []

    if use_default_ai_sources:
        pack_path = Path(source_pack).expanduser() if source_pack else DEFAULT_AI_SOURCE_PACK
        for descriptor in read_source_pack(pack_path):
            if descriptor.kind in {"rss", "youtube_feed", "wechat_rss"}:
                feed_sources.append(descriptor)
            else:
                deferred_sources.append(descriptor)

    legacy_default = Path(default_feeds_file).expanduser() if default_feeds_file else LEGACY_DEFAULT_AI_FEEDS_FILE
    if not use_default_ai_sources and legacy_default.exists() and default_feeds_file:
        for feed_url in read_feed_lines(legacy_default):
            feed_sources.append(SourceDescriptor(kind="rss", label=default_label_for_feed(feed_url), value=feed_url))

    for feed_url in feed_args:
        feed_url = feed_url.strip()
        if feed_url:
            feed_sources.append(
                SourceDescriptor(
                    kind=infer_source_kind(feed_url),
                    label=default_label_for_feed(feed_url),
                    value=feed_url,
                )
            )
    if feeds_file:
        for feed_url in read_feed_lines(Path(feeds_file).expanduser()):
            feed_sources.append(
                SourceDescriptor(
                    kind=infer_source_kind(feed_url),
                    label=default_label_for_feed(feed_url),
                    value=feed_url,
                )
            )

    unique_feed_sources: list[SourceDescriptor] = []
    seen_feeds: set[str] = set()
    for descriptor in feed_sources:
        if descriptor.value in seen_feeds:
            continue
        seen_feeds.add(descriptor.value)
        unique_feed_sources.append(descriptor)

    unique_deferred: list[SourceDescriptor] = []
    seen_deferred: set[tuple[str, str]] = set()
    for descriptor in deferred_sources:
        key = (descriptor.kind, descriptor.value)
        if key in seen_deferred:
            continue
        seen_deferred.add(key)
        unique_deferred.append(descriptor)

    return unique_feed_sources, unique_deferred


def parse_date(value: str) -> Optional[str]:
    value = (value or "").strip()
    if not value:
        return None
    lowered = value.lower()
    if lowered == "today":
        return date.today().isoformat()
    if lowered == "yesterday":
        return (date.today() - timedelta(days=1)).isoformat()
    if lowered == "latest":
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date().isoformat()
    except ValueError as exc:
        raise SystemExit(f"Unsupported --date value: {value}") from exc


def parse_strict_date(value: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise SystemExit(f"Unsupported date format: {value}. Expected YYYY-MM-DD.") from exc


def parse_published_date(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    raw = raw.strip()
    if not raw:
        return None
    try:
        return parsedate_to_datetime(raw).date().isoformat()
    except (TypeError, ValueError, IndexError):
        pass
    normalized = raw.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized).date().isoformat()
    except ValueError:
        pass
    match = re.search(r"\d{4}-\d{2}-\d{2}", raw)
    if match:
        return match.group(0)
    return None


def xml_child_text(elem: ET.Element, names: Iterable[str]) -> Optional[str]:
    desired = set(names)
    for child in elem:
        local = child.tag.split("}", 1)[-1]
        if local in desired and child.text and child.text.strip():
            return child.text.strip()
    return None


def parse_feed(feed: SourceDescriptor, timeout: int) -> list[FeedEntry]:
    xml_text = read_text(feed.value, timeout)
    root = ET.fromstring(xml_text)
    entries: list[FeedEntry] = []

    if root.tag.endswith("rss") or root.tag.endswith("RDF"):
        channel = root.find("./channel")
        items = channel.findall("./item") if channel is not None else root.findall(".//item")
        for item in items:
            title = xml_child_text(item, {"title"}) or "Untitled"
            link = xml_child_text(item, {"link"})
            if not link:
                continue
            published = xml_child_text(item, {"pubDate", "published", "updated", "dc:date", "date"})
            summary = xml_child_text(item, {"description", "summary", "encoded"})
            entries.append(
                FeedEntry(
                    title=clean_text(title),
                    url=clean_text(link),
                    published_date=parse_published_date(published),
                    feed_url=feed.value,
                    source_kind=feed.kind or infer_source_kind(feed.value, link),
                    source_label=feed.label or default_label_for_feed(feed.value),
                    source_domain=urlparse(clean_text(link)).netloc,
                    summary=clean_text(summary or ""),
                )
            )
        return entries

    if root.tag.endswith("feed"):
        namespace = {"atom": root.tag.split("}")[0].strip("{")} if "}" in root.tag else {}
        atom_entries = root.findall("atom:entry", namespace) if namespace else root.findall("entry")
        for entry in atom_entries:
            title = xml_child_text(entry, {"title"}) or "Untitled"
            link = None
            for child in entry:
                local = child.tag.split("}", 1)[-1]
                if local != "link":
                    continue
                href = child.attrib.get("href")
                rel = child.attrib.get("rel", "alternate")
                if href and rel == "alternate":
                    link = href
                    break
                if href and not link:
                    link = href
            if not link:
                continue
            published = xml_child_text(entry, {"published", "updated"})
            summary = xml_child_text(entry, {"summary", "content"})
            entries.append(
                FeedEntry(
                    title=clean_text(title),
                    url=clean_text(link),
                    published_date=parse_published_date(published),
                    feed_url=feed.value,
                    source_kind=feed.kind or infer_source_kind(feed.value, link),
                    source_label=feed.label or default_label_for_feed(feed.value),
                    source_domain=urlparse(clean_text(link)).netloc,
                    summary=clean_text(summary or ""),
                )
            )
        return entries

    raise ValueError(f"Unsupported feed format for {feed.value}")


def sort_entries(entries: list[FeedEntry]) -> list[FeedEntry]:
    return sorted(entries, key=lambda item: (item.published_date or "", item.title), reverse=True)


def dedupe_entries(entries: list[FeedEntry]) -> list[FeedEntry]:
    unique: list[FeedEntry] = []
    seen_urls: set[str] = set()
    for entry in entries:
        if entry.url in seen_urls:
            continue
        seen_urls.add(entry.url)
        unique.append(entry)
    return unique


def resolve_window(args: argparse.Namespace) -> tuple[Optional[date], Optional[date], str]:
    if args.days_back is not None:
        if args.days_back <= 0:
            raise SystemExit("--days-back must be greater than 0.")
        end = date.today()
        start = end - timedelta(days=args.days_back - 1)
        return start, end, f"last_{args.days_back}_days"
    if args.date_from or args.date_to:
        if not (args.date_from and args.date_to):
            raise SystemExit("--date-from and --date-to must be used together.")
        start = parse_strict_date(args.date_from)
        end = parse_strict_date(args.date_to)
        if start > end:
            raise SystemExit("--date-from cannot be later than --date-to.")
        return start, end, f"{start.isoformat()}..{end.isoformat()}"
    target_date = parse_date(args.date)
    if target_date is None:
        return None, None, "latest"
    day = parse_strict_date(target_date)
    return day, day, target_date


def diversify_entries(entries: list[FeedEntry], limit: int, per_source_limit: int) -> list[FeedEntry]:
    if per_source_limit <= 0:
        return entries[:limit]
    selected: list[FeedEntry] = []
    selected_urls: set[str] = set()
    counts: dict[str, int] = {}
    for entry in entries:
        source_key = entry.source_label or entry.feed_url
        if counts.get(source_key, 0) >= per_source_limit:
            continue
        selected.append(entry)
        selected_urls.add(entry.url)
        counts[source_key] = counts.get(source_key, 0) + 1
        if len(selected) >= limit:
            return selected
    for entry in entries:
        if entry.url in selected_urls:
            continue
        selected.append(entry)
        selected_urls.add(entry.url)
        if len(selected) >= limit:
            break
    return selected


def select_entries(
    entries: list[FeedEntry],
    start: Optional[date],
    end: Optional[date],
    limit: int,
    fallback_recent: int,
    per_source_limit: int,
) -> tuple[list[FeedEntry], bool]:
    ordered = sort_entries(entries)
    if start is None or end is None:
        return diversify_entries(ordered, limit, per_source_limit), False
    matched = []
    for entry in ordered:
        if not entry.published_date:
            continue
        try:
            published = parse_strict_date(entry.published_date)
        except SystemExit:
            continue
        if start <= published <= end:
            matched.append(entry)
    if matched:
        return diversify_entries(matched, limit, per_source_limit), False
    return diversify_entries(ordered, fallback_recent, per_source_limit), True


def fetch_article_content(entry: FeedEntry, timeout: int, content_chars: int) -> FeedEntry:
    try:
        html = read_text(entry.url, timeout)
        parser = SimpleArticleExtractor()
        parser.feed(html)
        content = parser.get_text()[:content_chars]
    except Exception as exc:
        print(f"[warn] Failed to fetch article {entry.url}: {exc}", file=sys.stderr)
        content = ""
    if not content and entry.summary:
        content = entry.summary[:content_chars]
    entry.content = content
    entry.content_chars = len(content)
    return entry


def dump_json(payload: dict, output: Optional[str], pretty: bool) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2 if pretty else None)
    if output:
        path = Path(output).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text + ("\n" if pretty else ""), encoding="utf-8")
        return
    sys.stdout.write(text)
    if pretty:
        sys.stdout.write("\n")


def descriptor_payload(descriptor: SourceDescriptor) -> dict[str, object]:
    return {
        "kind": descriptor.kind,
        "label": descriptor.label,
        "value": descriptor.value,
        "optional": descriptor.optional,
    }


def main() -> int:
    args = parse_args()
    use_default_ai_sources = bool(args.use_default_ai_sources or args.use_default_ai_feeds)
    feed_sources, deferred_sources = resolve_sources(
        args.feed,
        args.feeds_file,
        use_default_ai_sources,
        args.source_pack,
        args.default_feeds_file,
    )

    if not feed_sources and not deferred_sources:
        raise SystemExit("No sources resolved. Use --feed, --feeds-file, or --use-default-ai-sources.")

    all_entries: list[FeedEntry] = []
    feed_errors: list[dict[str, str]] = []
    for source in feed_sources:
        try:
            entries = parse_feed(source, args.feed_timeout)
            print(f"[info] {source.value} -> {len(entries)} entries", file=sys.stderr)
            all_entries.extend(entries)
        except Exception as exc:
            feed_errors.append({"feed_url": source.value, "label": source.label, "error": str(exc)})
            print(f"[warn] Failed to parse feed {source.value}: {exc}", file=sys.stderr)

    all_entries = dedupe_entries(all_entries)
    range_start, range_end, resolved_window = resolve_window(args)
    selected_entries, used_fallback = select_entries(
        all_entries,
        range_start,
        range_end,
        args.limit,
        args.fallback_recent,
        args.per_source_limit,
    )

    if args.fetch_content and selected_entries:
        fetched_entries: list[FeedEntry] = []
        with ThreadPoolExecutor(max_workers=max(1, args.concurrency)) as executor:
            futures = {
                executor.submit(fetch_article_content, entry, args.crawl_timeout, args.content_chars): entry
                for entry in selected_entries
            }
            for future in as_completed(futures):
                fetched_entries.append(future.result())
        selected_entries = sort_entries(fetched_entries)

    if not selected_entries and not deferred_sources:
        raise SystemExit("No articles found across all RSS-compatible sources.")

    payload = {
        "collected_at": datetime.now().isoformat(timespec="seconds"),
        "requested_date": args.date,
        "requested_window": {
            "date": args.date,
            "date_from": args.date_from,
            "date_to": args.date_to,
            "days_back": args.days_back,
        },
        "resolved_date": args.date,
        "resolved_window": resolved_window,
        "used_fallback": used_fallback,
        "fetch_content": bool(args.fetch_content),
        "feed_count": len(feed_sources),
        "deferred_source_count": len(deferred_sources),
        "requested_feeds": [descriptor.value for descriptor in feed_sources],
        "feed_sources": [descriptor_payload(descriptor) for descriptor in feed_sources],
        "deferred_sources": [descriptor_payload(descriptor) for descriptor in deferred_sources],
        "selected_count": len(selected_entries),
        "feed_errors": feed_errors,
        "items": [asdict(entry) for entry in selected_entries],
    }
    dump_json(payload, args.output, args.pretty or bool(args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
