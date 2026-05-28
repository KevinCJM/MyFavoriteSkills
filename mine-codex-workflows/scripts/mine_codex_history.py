#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import fnmatch
import hashlib
import json
import os
import re
import stat
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

SCHEMA_VERSION = "1.0"
DEFAULT_MAX_FILE_BYTES = 2_000_000
DEFAULT_MAX_TOTAL_BYTES = 30_000_000
MAX_TEXT_CHARS_PER_RECORD = 80_000
MAX_COMMAND_LEN = 180
MAX_PATHS_PER_RECORD = 80

SENSITIVE_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("private_key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.I | re.S)),
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b")),
    ("openai_key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("github_token", re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b")),
    ("slack_token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b")),
    ("authorization", re.compile(r"(?i)\b(authorization\s*[:=]\s*)(bearer\s+)?[^\s'\"]+")),
    ("bearer", re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]{16,}")),
    ("cookie", re.compile(r"(?i)\b(cookie|set-cookie)\s*[:=]\s*[^\n\r;]+")),
    ("password", re.compile(r"(?i)\b(password|passwd|pwd|secret|token|api[_-]?key)\s*[:=]\s*[^\s'\"]+")),
    ("database_url", re.compile(r"\b[a-z][a-z0-9+.-]*://[^\s:@/]+:[^\s@/]+@[^\s]+", re.I)),
    ("cli_secret", re.compile(r"(?i)(--?(?:token|api-key|apikey|secret|password|passwd|pwd|cookie|authorization)\s+(?:=\s*)?)(?:'[^']*'|\"[^\"]*\"|[^\s]+)")),
    ("header_secret", re.compile(r"(?i)(-H\s+)(?:'|\")?([^'\"\n]*(?:authorization|api-key|x-api-key|cookie)[^:='\"]*[:=]\s*)[^'\"\n]+(?:'|\")?")),
    ("json_secret", re.compile(r"(?i)([\"'](?:token|api[_-]?key|authorization|secret|password|cookie)[\"']\s*:\s*[\"'])[^\"']+([\"'])")),
    ("email", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")),
    ("phone", re.compile(r"(?<!\d)(?:\+?\d[\d .-]{8,}\d)(?!\d)")),
    ("long_secret", re.compile(r"\b[A-Za-z0-9+/=_-]{40,}\b")),
]

COMMAND_RE = re.compile(
    r"(?m)(?:^|[;|&`$])\s*((?:/[^\s]+/)?(?:python|python3|pytest|bash|sh|git|curl|npm|pnpm|yarn|uv|make|codex)\b[^\n\r]*)"
)
PATH_RE = re.compile(r"(?:\.?\.?/)?(?:[\w.@+-]+/)+[\w.@+\-=,()\[\]{}\u4e00-\u9fff]+(?:\.[A-Za-z0-9_+-]+)?")

TEXT_KEYS = {
    "prompt",
    "text",
    "content",
    "input",
    "output",
    "response",
    "message",
    "messages",
    "cwd",
    "path",
    "workdir",
    "command",
    "cmd",
    "summary",
    "title",
}
ID_KEYS = ("session_id", "conversation_id", "thread_id", "id")
TIME_KEYS = ("timestamp", "created_at", "updated_at", "time", "date")

DEFAULT_WORKFLOW_RULES = [
    {
        "id": "project-guidance-maintenance",
        "title": "Project agent guidance and routing maintenance",
        "terms": ["AGENTS.md", "CLAUDE.md", "README", "routing", "repo map", "task route", "pitfall", "project docs", "guardrail", "validate", "evolve"],
        "goal": "Maintain, validate, or evolve project-specific agent guidance, routing, or workflow memory.",
        "steps": [
            "Read the project's agent guidance and related routing or documentation files.",
            "Identify the narrow protocol, memory, or workflow change needed.",
            "Keep durable guidance separate from transient observations.",
            "Run the smallest available validation command.",
        ],
        "risks": ["Do not mix unverified implementation facts into durable guidance.", "Avoid editing unrelated business code during guidance-only work."],
    },
    {
        "id": "skill-authoring",
        "title": "Codex skill design and implementation",
        "terms": ["SKILL.md", "skill-creator", "skills/", "create skill", "skill draft", "创建 skill", "生成 skill", "技能"],
        "goal": "Design, implement, validate, or review reusable Codex skills.",
        "steps": [
            "Read skill creation guidance when available.",
            "Design a small single-purpose skill and resource layout.",
            "Implement SKILL.md plus deterministic scripts or references when useful.",
            "Validate the skill and test realistic usage.",
        ],
        "risks": ["Keep SKILL.md concise.", "Do not auto-write skill files from private history without confirmation."],
    },
    {
        "id": "api-debugging-and-replay",
        "title": "API debugging, payload capture, and replay workflow",
        "terms": ["API", "payload", "request", "response", "curl", "case", "CASE", "replay", "回放", "endpoint", "/api/"],
        "goal": "Capture, inspect, replay, or compare API requests and responses.",
        "steps": [
            "Identify the request source, payload, or failing endpoint.",
            "Capture or sanitize the minimal reproducible case.",
            "Run the narrow replay, smoke, or comparison command.",
            "Summarize status, timing, and output differences without exposing secrets.",
        ],
        "risks": ["Do not expose authorization headers or cookies.", "Do not infer external service behavior without direct evidence."],
    },
    {
        "id": "requirements-design-review",
        "title": "Requirements, design, and task review workflow",
        "terms": ["requirements", "design", "task", "review", "spec", "PRD", "需求澄清", "详细设计", "任务单", "评审", "原始需求"],
        "goal": "Analyze requirements, design, task, or review artifacts and produce focused implementation guidance.",
        "steps": [
            "Read the requested requirement and design artifacts.",
            "Deduplicate issues by blocking impact.",
            "Separate implementation blockers, test blockers, and deferred questions.",
            "Keep recommendations scoped to the named task.",
        ],
        "risks": ["Do not invent hidden caller behavior.", "Separate verified facts from assumptions."],
    },
    {
        "id": "deployment-audit",
        "title": "Deployment and infrastructure audit workflow",
        "terms": ["deploy", "deployment", "terraform", "helm", "docker", "kubernetes", "AWS", "GCP", "Azure", "CI", "CD", "buildspec", "ECR", "EKS"],
        "goal": "Audit or adjust deployment, infrastructure, container, or CI/CD workflows.",
        "steps": [
            "Read deployment configs and related task artifacts.",
            "Check runtime contracts and environment-specific settings.",
            "Make narrow infrastructure changes only when requested.",
            "Run syntax, unit, or targeted deployment-script validation.",
        ],
        "risks": ["Do not assume live cloud state without direct observation.", "Avoid broad infrastructure rewrites."],
    },
    {
        "id": "code-impact-analysis",
        "title": "Code impact analysis and targeted regression workflow",
        "terms": ["impact", "regression", "tests", "pytest", "datasource", "indicator", "SQL", "DataFrame", "refactor", "bug", "fix"],
        "goal": "Analyze code impact, make narrow changes, and run targeted regression checks.",
        "steps": [
            "Resolve the relevant module, files, and tests.",
            "Read nearby contracts before editing shared code.",
            "Make the smallest code change that preserves existing behavior.",
            "Run targeted tests, compile checks, or smoke commands.",
        ],
        "risks": ["Do not perform unrequested refactors.", "Treat shared contracts, data shapes, and test commands as high risk."],
    },
    {
        "id": "content-and-document-workflow",
        "title": "Content, document, and report drafting workflow",
        "terms": ["draft", "rewrite", "article", "report", "summary", "markdown", "slides", "写作", "文章", "报告", "总结"],
        "goal": "Draft, revise, or package recurring documents, reports, or content artifacts.",
        "steps": [
            "Identify the source materials and target audience.",
            "Extract the reusable outline or checklist.",
            "Draft concise output with citations or evidence when needed.",
            "Review for tone, formatting, and repeated style requirements.",
        ],
        "risks": ["Do not fabricate source-backed claims.", "Avoid storing sensitive source text inside reusable skills."],
    },
]

DEFAULT_PROJECT_ANCHORS = [
    "AGENTS.md",
    "CLAUDE.md",
    "README.md",
    "pyproject.toml",
    "package.json",
    "requirements.txt",
    "Makefile",
    "Cargo.toml",
    "go.mod",
    "pom.xml",
    "src/",
    "tests/",
    "docs/",
    "skills/",
]
WEAK_ANCHORS = ["AGENTS.md", "CLAUDE.md", "README.md", "SKILL.md", "skills/"]


@dataclass
class Record:
    session_id: str
    source: str
    timestamp: dt.datetime | None
    text: str
    match_reasons: list[str] = field(default_factory=list)


@dataclass
class RuleEvidence:
    sessions: set[str] = field(default_factory=set)
    dates: set[str] = field(default_factory=set)
    terms: Counter[str] = field(default_factory=Counter)
    commands: Counter[str] = field(default_factory=Counter)
    files: Counter[str] = field(default_factory=Counter)
    snippets: list[str] = field(default_factory=list)


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_time(value: Any) -> dt.datetime | None:
    if isinstance(value, (int, float)):
        try:
            if value > 10_000_000_000:
                value = value / 1000
            return dt.datetime.fromtimestamp(value, tz=dt.timezone.utc)
        except (OverflowError, OSError, ValueError):
            return None
    if not isinstance(value, str) or not value.strip():
        return None
    raw = value.strip().replace("Z", "+00:00")
    try:
        parsed = dt.datetime.fromisoformat(raw)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc)


def walk_json(value: Any, depth: int = 0) -> Iterable[tuple[str, Any]]:
    if depth > 8:
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_str = str(key)
            yield key_str, item
            if key_str in TEXT_KEYS or isinstance(item, (Mapping, list, tuple)):
                yield from walk_json(item, depth + 1)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for item in value[:200] if isinstance(value, list) else value:
            yield from walk_json(item, depth + 1)


def collect_text(value: Any) -> str:
    parts: list[str] = []
    for key, item in walk_json(value):
        if key not in TEXT_KEYS:
            continue
        if isinstance(item, str):
            parts.append(item)
        elif isinstance(item, (int, float)) and key in {"timestamp", "time"}:
            parts.append(str(item))
    text = "\n".join(parts)
    return text[:MAX_TEXT_CHARS_PER_RECORD]


def first_field(value: Mapping[str, Any], keys: Sequence[str]) -> Any:
    for key, item in walk_json(value):
        if key in keys:
            return item
    return None


def redactor() -> tuple[callable, Counter[str]]:
    stats: Counter[str] = Counter()

    def redact(text: str) -> str:
        result = text
        for label, pattern in SENSITIVE_PATTERNS:
            def repl(match: re.Match[str], label: str = label) -> str:
                stats[label] += 1
                if label in {"authorization", "cli_secret"} and match.lastindex:
                    prefix = match.group(1) or ""
                    return f"{prefix}[REDACTED:{label}]"
                if label == "header_secret" and match.lastindex and match.lastindex >= 2:
                    return f"{match.group(1)}{match.group(2)}[REDACTED:{label}]"
                if label == "json_secret" and match.lastindex and match.lastindex >= 2:
                    return f"{match.group(1)}[REDACTED:{label}]{match.group(2)}"
                return f"[REDACTED:{label}]"
            result = pattern.sub(repl, result)
        return result

    return redact, stats


def safe_source(codex_home: Path, path: Path) -> str:
    try:
        rel = path.resolve().relative_to(codex_home.resolve())
        return f"~/.codex/{rel.as_posix()}"
    except ValueError:
        return path.name


def iter_jsonl(path: Path, max_bytes: int) -> tuple[list[Any], int]:
    if path.stat().st_size > max_bytes:
        return [], 1
    rows: list[Any] = []
    parse_errors = 0
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                parse_errors += 1
    return rows, parse_errors


def iter_json(path: Path, max_bytes: int) -> tuple[list[Any], int]:
    if path.stat().st_size > max_bytes:
        return [], 1
    try:
        data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except json.JSONDecodeError:
        return [], 1
    if isinstance(data, list):
        return data, 0
    return [data], 0


def candidate_source_files(codex_home: Path, include_archived: bool) -> list[Path]:
    roots = [codex_home / "history.jsonl", codex_home / "session_index.jsonl"]
    dirs = [codex_home / "sessions"]
    if include_archived:
        dirs.append(codex_home / "archived_sessions")
    files: list[Path] = [path for path in roots if path.is_file() and not path.is_symlink()]
    for root in dirs:
        if not root.is_dir() or root.is_symlink():
            continue
        for path in root.rglob("*"):
            if path.is_symlink() or not path.is_file():
                continue
            if path.suffix in {".jsonl", ".json"}:
                files.append(path)
    return sorted(files, key=lambda p: p.stat().st_mtime if p.exists() else 0, reverse=True)


def discover_project_anchors(project_root: Path, extra_anchors: Sequence[str]) -> list[str]:
    anchors = set(DEFAULT_PROJECT_ANCHORS)
    anchors.update(item for item in extra_anchors if item)
    try:
        for child in project_root.iterdir():
            name = child.name
            if name.startswith(".") and name not in {".github", ".gitlab"}:
                continue
            if child.is_dir():
                anchors.add(f"{name}/")
            elif child.is_file() and len(name) <= 80:
                anchors.add(name)
    except OSError:
        pass
    return sorted(anchors)


def load_workflow_rules(path: str | None) -> list[dict[str, Any]]:
    if not path:
        return DEFAULT_WORKFLOW_RULES
    raw_path = Path(path).expanduser()
    data = json.loads(raw_path.read_text(encoding="utf-8"))
    rules = data.get("workflow_rules", data) if isinstance(data, Mapping) else data
    if not isinstance(rules, list):
        raise SystemExit("workflow rules must be a list or an object with workflow_rules")
    normalized: list[dict[str, Any]] = []
    for row in rules:
        if not isinstance(row, Mapping):
            continue
        if not isinstance(row.get("id"), str) or not isinstance(row.get("terms"), list):
            continue
        normalized.append(
            {
                "id": row["id"],
                "title": str(row.get("title") or row["id"].replace("-", " ").title()),
                "terms": [str(item) for item in row.get("terms", []) if str(item).strip()],
                "goal": str(row.get("goal") or "Repeated workflow detected from local Codex history."),
                "steps": [str(item) for item in row.get("steps", [])] or ["Review the repeated evidence.", "Decide whether this should become a skill."],
                "risks": [str(item) for item in row.get("risks", [])] or ["Requires human review before skill creation."],
            }
        )
    return normalized or DEFAULT_WORKFLOW_RULES


def project_match(text: str, project_root: Path, anchors: Sequence[str], extra_anchors: Sequence[str]) -> list[str]:
    lowered = text.lower()
    reasons: list[str] = []
    root_real = str(project_root).lower()
    if root_real and root_real in lowered:
        reasons.append("project_root_absolute")
    project_name_hit = bool(re.search(rf"(?<![\w-]){re.escape(project_root.name.lower())}(?![\w-])", lowered))
    anchor_hits = [anchor for anchor in anchors if anchor.lower() in lowered]
    explicit_hits = [anchor for anchor in extra_anchors if anchor and anchor.lower() in lowered]
    weak_hits = [anchor for anchor in WEAK_ANCHORS if anchor.lower() in lowered]
    strong_hits = [anchor for anchor in anchor_hits if anchor not in WEAK_ANCHORS]
    if explicit_hits:
        reasons.append("explicit_anchor")
    if len(strong_hits) >= 2:
        reasons.append("multiple_project_anchors")
    if project_name_hit and anchor_hits:
        reasons.append("project_name_with_anchor")
    if reasons and weak_hits:
        reasons.append("weak_anchor_with_project_signal")
    return sorted(set(reasons))

def path_template(raw: str, project_root: Path, home: Path) -> str | None:
    value = raw.strip().strip("'\"`.,;:()[]{}<>")
    if not value or len(value) > 260:
        return None
    if str(project_root) in value:
        value = value.replace(str(project_root), ".")
    if str(home) in value:
        value = value.replace(str(home), "~")
    if value.startswith("./"):
        return value[2:]
    if value.startswith(".") and "/" in value:
        return value
    if value.startswith("~/") or value.startswith("/"):
        return Path(value).name or "[external-path]"
    return value if "/" in value else None


def redact_paths_for_output(text: str, project_root: Path, home: Path) -> str:
    result = text.replace(str(project_root), ".").replace(str(home), "~")
    result = re.sub(r"/Users/[^\s'\"`]+", "[REDACTED:path]", result)
    result = re.sub(r"/private/var/[^\s'\"`]+", "[REDACTED:path]", result)
    result = re.sub(r"https?://[^\s'\"`]+", "[URL]", result)
    return result


def extract_paths(text: str, project_root: Path, home: Path) -> list[str]:
    values: list[str] = []
    for match in PATH_RE.finditer(text):
        templated = path_template(match.group(0), project_root, home)
        if templated:
            values.append(templated)
        if len(values) >= MAX_PATHS_PER_RECORD:
            break
    return sorted(set(values))


def command_template(command: str, project_root: Path, home: Path, redact_fn: callable) -> str:
    value = redact_fn(command.strip())
    value = redact_paths_for_output(value, project_root, home)
    value = re.sub(r"https?://[^\s]+", "[URL]", value)
    value = re.sub(r"\s+", " ", value)
    if len(value) > MAX_COMMAND_LEN:
        value = value[: MAX_COMMAND_LEN - 3] + "..."
    return value


def extract_commands(text: str, project_root: Path, home: Path, redact_fn: callable) -> list[str]:
    commands = [command_template(m.group(1), project_root, home, redact_fn) for m in COMMAND_RE.finditer(text)]
    return sorted(set(commands))[:30]


def session_hash(source: str, text: str) -> str:
    return hashlib.sha1(f"{source}\n{text[:1000]}".encode("utf-8", errors="ignore")).hexdigest()[:16]


def load_records(args: argparse.Namespace) -> tuple[list[Record], dict[str, Any]]:
    codex_home = Path(args.codex_home).expanduser().resolve()
    project_root = Path(args.project_root).expanduser().resolve()
    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=args.days)
    files = candidate_source_files(codex_home, args.include_archived)
    anchors = discover_project_anchors(project_root, args.anchor)
    parse_errors = 0
    unreadable = 0
    oversized = 0
    total_bytes = 0
    records: list[Record] = []
    seen_record_keys: set[str] = set()
    seen_sessions_considered: set[str] = set()
    matched_sessions: set[str] = set()
    unknown_timestamp_records = 0
    stop_scanning = False

    for path in files:
        try:
            size = path.stat().st_size
        except OSError:
            unreadable += 1
            continue
        if total_bytes + size > args.max_total_bytes:
            break
        total_bytes += size
        try:
            rows, errors = iter_jsonl(path, args.max_file_bytes) if path.suffix == ".jsonl" else iter_json(path, args.max_file_bytes)
        except OSError:
            unreadable += 1
            continue
        if errors and not rows:
            oversized += 1 if size > args.max_file_bytes else 0
        parse_errors += errors
        if stop_scanning:
            break
        for row in rows:
            if not isinstance(row, Mapping):
                continue
            raw_session = first_field(row, ID_KEYS)
            text = collect_text(row)
            if not text:
                continue
            sid = str(raw_session) if raw_session else session_hash(safe_source(codex_home, path), text)
            seen_sessions_considered.add(sid)
            timestamp = parse_time(first_field(row, TIME_KEYS))
            if timestamp is None:
                unknown_timestamp_records += 1
            if timestamp and timestamp < cutoff:
                continue
            reasons = project_match(text, project_root, anchors, args.anchor)
            if not reasons:
                continue
            if sid not in matched_sessions and len(matched_sessions) >= args.max_sessions:
                stop_scanning = True
                break
            matched_sessions.add(sid)
            dedupe_key = f"{sid}:{safe_source(codex_home, path)}:{hashlib.sha1(text[:2000].encode()).hexdigest()[:12]}"
            if dedupe_key in seen_record_keys:
                continue
            seen_record_keys.add(dedupe_key)
            records.append(Record(sid, safe_source(codex_home, path), timestamp, text, reasons))

    metadata = {
        "codex_home": "~/.codex" if codex_home == Path.home() / ".codex" else codex_home.name,
        "sources": [safe_source(codex_home, path) for path in files[:20]],
        "source_file_count": len(files),
        "sessions_considered": len(seen_sessions_considered),
        "project_sessions_matched": len(matched_sessions),
        "unknown_timestamp_records": unknown_timestamp_records,
        "parse_errors": parse_errors,
        "unreadable_files": unreadable,
        "oversized_files": oversized,
        "total_bytes_considered": total_bytes,
        "sqlite_scanned": False,
        "anchor_count": len(anchors),
        "sample_anchors": anchors[:20],
    }
    return records, metadata


def term_matches(term: str, lowered_text: str) -> bool:
    lowered_term = term.lower()
    if re.fullmatch(r"[a-z0-9_-]{1,4}", lowered_term):
        return bool(re.search(rf"(?<![a-z0-9_-]){re.escape(lowered_term)}(?![a-z0-9_-])", lowered_text))
    return lowered_term in lowered_text


def build_candidates(records: Sequence[Record], args: argparse.Namespace, redact_fn: callable) -> list[dict[str, Any]]:
    project_root = Path(args.project_root).expanduser().resolve()
    home = Path.home().resolve()
    evidence_by_rule: dict[str, RuleEvidence] = defaultdict(RuleEvidence)
    workflow_rules = load_workflow_rules(args.workflow_rules)
    rules_by_id = {rule["id"]: rule for rule in workflow_rules}

    for record in records:
        redacted_text = redact_fn(record.text)
        commands = extract_commands(redacted_text, project_root, home, redact_fn)
        paths = extract_paths(redacted_text, project_root, home)
        record_date = record.timestamp.date().isoformat() if record.timestamp else "unknown"
        lowered = redacted_text.lower()
        matched_any = False
        for rule in workflow_rules:
            hits = [term for term in rule["terms"] if term_matches(term, lowered)]
            if not hits:
                continue
            matched_any = True
            ev = evidence_by_rule[rule["id"]]
            ev.sessions.add(record.session_id)
            ev.dates.add(record_date)
            ev.terms.update(hits)
            ev.commands.update(commands)
            ev.files.update(paths)
            if args.allow_snippets and len(ev.snippets) < 3:
                snippet = redact_paths_for_output(redacted_text[:240], project_root, home).replace("\n", " ")
                ev.snippets.append(snippet)
        if not matched_any and (commands or len(paths) >= 3):
            ev = evidence_by_rule["unknown-repeat-workflow"]
            ev.sessions.add(record.session_id)
            ev.dates.add(record_date)
            ev.commands.update(commands)
            ev.files.update(paths)

    candidates: list[dict[str, Any]] = []
    for rule_id, ev in evidence_by_rule.items():
        frequency = len(ev.sessions)
        if frequency < args.min_count:
            continue
        if rule_id in rules_by_id:
            rule = rules_by_id[rule_id]
            title = str(rule["title"])
            goal = str(rule["goal"])
            steps = list(rule["steps"])
            risks = list(rule["risks"])
            terms = [item for item, _ in ev.terms.most_common(8)]
        else:
            title = "Unknown repeated project workflow"
            goal = "Repeated project work with similar commands or file groups that needs human classification."
            steps = ["Review repeated command and file evidence.", "Decide whether this is a stable workflow.", "Create or update a small skill only after human review."]
            risks = ["This candidate is weakly classified.", "Do not create a skill without reviewing evidence." ]
            terms = []
        command_stability = 1 if ev.commands else 0
        file_stability = 1 if ev.files else 0
        score = frequency + len(ev.dates) + command_stability + file_stability
        confidence = "high" if frequency >= 3 and score >= 6 else "medium" if frequency >= args.min_count else "low"
        skill_value = confidence
        candidate: dict[str, Any] = {
            "id": f"candidate-{len(candidates)+1:03d}",
            "title": title,
            "suggested_skill_name": rule_id if rule_id != "unknown-repeat-workflow" else "review-repeated-workflow",
            "confidence": confidence,
            "skill_value": skill_value,
            "frequency": frequency,
            "distinct_days": len([d for d in ev.dates if d != "unknown"]),
            "evidence_counts": {
                "sessions": frequency,
                "commands": sum(ev.commands.values()),
                "files": sum(ev.files.values()),
                "trigger_terms": sum(ev.terms.values()),
            },
            "trigger_phrases": terms,
            "repeated_goal": goal,
            "common_steps": steps,
            "common_files": [item for item, _ in ev.files.most_common(12)],
            "common_commands": [item for item, _ in ev.commands.most_common(8)],
            "risks": risks,
            "requires_human_review": True,
            "evidence_basis": "rule_template_plus_history_signals",
        }
        if args.allow_snippets:
            candidate["redacted_snippets"] = ev.snippets
        if args.mode == "draft":
            candidate["draft_suggestion"] = {
                "skill_name": candidate["suggested_skill_name"],
                "description": f"Use when asked to perform or analyze this repeated workflow: {goal}",
                "inputs": ["User goal", "Project root", "Relevant files or task artifacts"],
                "outputs": ["Concise result", "Validation status", "Risks or next steps"],
                "workflow": steps,
                "validation": ["Run the smallest commands seen in common_commands when applicable.", "Ask for confirmation before writing files."],
                "evidence_basis": "Template guidance combined with repeated trigger terms, files, and command evidence.",
                "evidence_summary": {
                    "trigger_phrases": candidate["trigger_phrases"],
                    "common_files": candidate["common_files"][:8],
                    "common_commands": candidate["common_commands"][:5],
                },
                "notes": ["Draft suggestion only; review existing skills before implementation.", "Keep any final SKILL.md concise and single-purpose."],
            }
        candidates.append(candidate)

    return sorted(candidates, key=lambda c: (-int(c["frequency"]), str(c["title"])))


def render_md(report: Mapping[str, Any]) -> str:
    lines = ["# Codex Workflow Candidates", ""]
    stats = report.get("stats", {})
    lines.append(f"- Sessions scanned: {stats.get('sessions_scanned', 0)}")
    lines.append(f"- Project sessions matched: {stats.get('project_sessions_matched', 0)}")
    lines.append(f"- Candidates: {stats.get('candidates_emitted', 0)}")
    lines.append("- Raw conversations included: false")
    lines.append("")
    for candidate in report.get("workflow_candidates", []):
        lines.append(f"## {candidate.get('title')}")
        lines.append(f"- Suggested skill: `{candidate.get('suggested_skill_name')}`")
        lines.append(f"- Confidence: {candidate.get('confidence')}")
        lines.append(f"- Frequency: {candidate.get('frequency')}")
        lines.append(f"- Goal: {candidate.get('repeated_goal')}")
        for step in candidate.get("common_steps", [])[:5]:
            lines.append(f"- Step: {step}")
        for risk in candidate.get("risks", [])[:4]:
            lines.append(f"- Risk: {risk}")
        lines.append("")
    return "\n".join(lines)


def write_report(path: Path, content: str, force: bool) -> None:
    if path.exists() and not force:
        raise SystemExit(f"refusing to overwrite existing report: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    project_root = Path(args.project_root).expanduser().resolve()
    redact_fn, redaction_stats = redactor()
    records, metadata = load_records(args)
    candidates = build_candidates(records, args, redact_fn)
    filter_counts = Counter(reason for record in records for reason in record.match_reasons)
    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": utc_now(),
        "project_root": project_root.name,
        "scan_window_days": args.days,
        "sources": {
            "codex_home": metadata["codex_home"],
            "source_file_count": metadata["source_file_count"],
            "sample_sources": metadata["sources"],
            "sqlite_scanned": metadata["sqlite_scanned"],
            "archived_included": args.include_archived,
            "anchor_count": metadata["anchor_count"],
            "sample_anchors": metadata["sample_anchors"],
        },
        "limits": {
            "max_sessions": args.max_sessions,
            "max_file_bytes": args.max_file_bytes,
            "max_total_bytes": args.max_total_bytes,
            "allow_snippets": args.allow_snippets,
        },
        "privacy": {
            "redaction_applied": True,
            "raw_conversations_included": False,
            "external_paths_redacted": True,
            "network_used": False,
            "requires_human_review": True,
        },
        "stats": {
            "source_files_scanned": metadata["source_file_count"],
            "sessions_scanned": metadata["sessions_considered"],
            "project_sessions_matched": metadata["project_sessions_matched"],
            "records_matched": len(records),
            "unknown_timestamp_records": metadata["unknown_timestamp_records"],
            "candidates_emitted": len(candidates),
            "parse_errors": metadata["parse_errors"],
            "unreadable_files": metadata["unreadable_files"],
            "oversized_files": metadata["oversized_files"],
        },
        "redaction_stats": dict(redaction_stats),
        "filter_reasons": dict(filter_counts),
        "workflow_candidates": candidates,
    }
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Mine local Codex history for repeated project workflows.")
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--codex-home", default=os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    parser.add_argument("--days", type=int, default=60)
    parser.add_argument("--min-count", type=int, default=2)
    parser.add_argument("--format", choices=("json", "md"), default="json")
    parser.add_argument("--mode", choices=("analysis", "draft"), default="analysis")
    parser.add_argument("--include-archived", action="store_true")
    parser.add_argument("--max-sessions", type=int, default=500)
    parser.add_argument("--max-file-bytes", type=int, default=DEFAULT_MAX_FILE_BYTES)
    parser.add_argument("--max-total-bytes", type=int, default=DEFAULT_MAX_TOTAL_BYTES)
    parser.add_argument("--allow-snippets", action="store_true")
    parser.add_argument("--write-report")
    parser.add_argument("--workflow-rules", help="Optional JSON file containing portable workflow_rules overrides.")
    parser.add_argument("--anchor", action="append", default=[], help="Extra project-specific anchor; can be repeated.")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args)
    output = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) if args.format == "json" else render_md(report)
    if args.write_report:
        write_report(Path(args.write_report), output, args.force)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
