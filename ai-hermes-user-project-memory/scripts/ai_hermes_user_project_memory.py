#!/usr/bin/env python3
"""Local AI Hermes user-project memory CLI.

Stores user/repo memories inside the current project tree. The tool is
intentionally small and policy-heavy: it never stores secrets, raw prompts, or
project shared facts.
"""

from __future__ import annotations

import argparse
import dataclasses
import fcntl
import getpass
import hashlib
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

SCHEMA_VERSION = 1
DEFAULT_MEMORY_SUBDIR = Path("docs/.ai-hermes-user-memory")
EXIT_VALIDATION = 1
EXIT_POLICY_DENIED = 2
EXIT_SECRET_BLOCKED = 3
EXIT_LOCK_TIMEOUT = 4
EXIT_IDENTITY_FAILED = 5
EXIT_CORRUPT = 6
EXIT_NOT_FOUND = 7

MEMORY_TYPES = {
    "communication_preference",
    "workflow_preference",
    "local_runtime_preference",
    "project_private_config",
    "account_alias",
    "tool_preference",
    "safety_preference",
    "automation_suppression_rule",
}
SCOPES = {"repo_user"}
PORTABILITY = {"portable", "repo_specific", "local_only"}
SENSITIVITY = {"none", "low", "personal_path", "account_alias", "secret_blocked"}
STATUSES = {"active", "disabled", "superseded", "conflict_pending", "stale"}
CONFIDENCE = {"high", "medium", "low"}
AUTO_LEARN_TYPES = {"communication_preference", "workflow_preference"}
AUTO_LEARN_FORBIDDEN_CLASSES = (
    "local_path",
    "account_alias",
    "profile_name",
    "host",
    "customer_name",
    "secret_like",
)
DEFAULT_ENABLED = {"recall": True, "learn": True, "auto_learn": True}
AGENTS_GUIDANCE_HEADER = "# AI Hermes User Project Memory"
AGENTS_GUIDANCE = """# AI Hermes User Project Memory

- The project-local `ai-hermes-user-project-memory` skill is available by default so agents know how to handle user preferences and repo-local private configuration.
- User project memory is private user context, not project implementation truth.
- Persisted recall, learning, and auto-learning are enabled by default after installation.
- Before normal user-facing work, run `tools/ai_hermes_user_project_memory.py --json recall` to dynamically resolve the current user/repo identity and load applicable project-scoped `repo_user` memories.
- Apply recalled memories only when the recall result is enabled, the current session is not suppressed, and the memory does not conflict with higher-priority instructions.
- Never hardcode user names, user hashes, git emails, account IDs, account aliases, or profile names in `AGENTS.md`; identity must be resolved by the memory tool at runtime.
- Auto-learning is only effective when learning is enabled, and disabling learning must also disable auto-learning.
- Users can ask to remember, forget, enable, disable, view, audit, or apply personal project memory through `tools/ai_hermes_user_project_memory.py`; they may also explicitly request switch changes in prompts or edit the memory config file themselves.
- When the user explicitly says "remember" or "记住", use the user memory tool for that one authorized write unless the content is forbidden.
- When a stable low-risk preference is inferred, active auto-learning is allowed only when policy permits it; otherwise generate a candidate for user approval.
- User memory may include communication preferences, workflow preferences, local runtime preferences, project-private config, account aliases without secrets, and safety preferences that only strengthen existing rules.
- User memory must be stored under `docs/.ai-hermes-user-memory/` in this project, separated by hashed user and repo identity; `users/<user_hash>/repos/<repo_hash>.json` is the only active memory file.
- Never write actual personal preferences, local absolute paths, account aliases, private profiles, git identity, or memory contents into `docs/repo_map.json`, `docs/task_routes.json`, `docs/pitfalls.json`, README, PR text, or ordinary project docs; `docs/.ai-hermes-user-memory/` is the only allowed project-internal memory data location.
- Never store secrets, tokens, cookies, Authorization plaintext, account passwords, private keys, database URLs, `.env` contents, raw conversation text, or full automation prompts in user memory.
- `docs/.ai-hermes-user-memory/` is ignored by default. Only if the user explicitly asks to save memory to the cloud/remote git repo may an agent run `tools/ai_hermes_user_project_memory.py --json git-sync-check --confirm-user-explicit`; if it passes, the agent may force-add the memory data files with `git add -f docs/.ai-hermes-user-memory/config.json docs/.ai-hermes-user-memory/users`.
- Run `git-sync-check --confirm-user-explicit` immediately before staging, committing, or pushing user memory; never sync memory when the check reports sensitive content.
- Explicit "remember"/"记住" authorizes the current memory write; it does not change general learning or auto-learning switches.
- Subagent instructions, CI prompts, batch prompts, automation templates, and handoff summaries default to no recall and no learning unless the user explicitly asks to use memory.
- System/developer instructions, this `AGENTS.md`, safety rules, sandbox/approval rules, and the current user turn always override user memory.
- The user memory tool must reject every memory home except `docs/.ai-hermes-user-memory/` in the current project.
"""

SECRET_PATTERNS = [
    re.compile(r"sk-proj-[A-Za-z0-9_-]{10,}"),
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"ghp_[A-Za-z0-9_]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"glpat-[A-Za-z0-9_-]{20,}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"ASIA[0-9A-Z]{16}"),
    re.compile(r"(?i)aws(.{0,30})?(secret|secret_access_key).{0,30}[:=]\s*['\"]?[A-Za-z0-9/+=]{32,}"),
    re.compile(r"npm_[A-Za-z0-9]{20,}"),
    re.compile(r"pypi-[A-Za-z0-9_-]{20,}"),
    re.compile(r"AIza[0-9A-Za-z_-]{20,}"),
    re.compile(r"(?i)AccountKey=[A-Za-z0-9/+=]{32,}"),
    re.compile(r"(?i)sig=[A-Za-z0-9%._~+/=-]{20,}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),
    re.compile(r"(?i)Authorization\s*:\s*Bearer\s+\S+"),
    re.compile(r"(?i)\bAUTHORIZATION\s*=\s*Bearer\s+\S+"),
    re.compile(r"(?i)Cookie\s*:\s*\S+"),
    re.compile(r"(?i)\bCOOKIE\s*=\s*\S+"),
    re.compile(r"(?i)password\s*=\s*[^\s]+"),
    re.compile(r"(?i)(account[_-]?password|accountpassword)\s*[:=]\s*['\"]?[^\s'\"]{4,}"),
    re.compile(r"(?i)(client[_-]?secret|access[_-]?token|refresh[_-]?token)\s*[:=]\s*['\"]?[A-Za-z0-9_./+=-]{16,}"),
    re.compile(r"(?i)\b(postgresql|postgres|mysql|mariadb|mongodb|redis|redshift|snowflake)://[^\s'\"<>]+"),
    re.compile(r"(?i)\bjdbc:[^\s'\"<>]+"),
    re.compile(r"(?i)(database[_-]?url|db[_-]?url|dsn|connection[_-]?string)\s*[:=]\s*['\"]?[^\s'\"]{8,}"),
    re.compile(r"(?i)(api[_-]?key|secret|token|private[_-]?key)\s*[:=]\s*['\"]?[A-Za-z0-9_./+=-]{12,}"),
]
SECRET_KEY_RE = re.compile(
    r"(?ix)"
    r"^(authorization|cookie|set_cookie|password|account_password|passwd|pwd|passphrase|"
    r"token|access_token|refresh_token|id_token|auth_token|session_token|api_token|"
    r"api_key|x_api_key|secret|client_secret|secret_key|private_key|"
    r"aws_secret_access_key|secret_access_key|account_key|accountkey|"
    r"database_url|db_url|dsn|connection_string)$"
)
SECRET_KEY_COMPACT_NAMES = {
    "authorization",
    "cookie",
    "setcookie",
    "password",
    "accountpassword",
    "passwd",
    "pwd",
    "passphrase",
    "token",
    "accesstoken",
    "refreshtoken",
    "idtoken",
    "authtoken",
    "sessiontoken",
    "apitoken",
    "apikey",
    "xapikey",
    "secret",
    "clientsecret",
    "secretkey",
    "privatekey",
    "awssecretaccesskey",
    "secretaccesskey",
    "accountkey",
    "databaseurl",
    "dburl",
    "dsn",
    "connectionstring",
}
LOCAL_PATH_RE = re.compile(r"(^|[\s'\"=:\[])(/[A-Za-z0-9._~+@-][^\s'\"`<>]*|[A-Za-z]:\\[^\s'\"]+)")
SAFE_CANDIDATE_ID_RE = re.compile(r"^cand_[A-Za-z0-9_-]{8,80}$")
SAFE_MEMORY_ID_RE = re.compile(r"^[A-Za-z0-9_.:-]{1,128}$")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_utc_timestamp(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("invalid timestamp") from exc


def stable_id(prefix: str, *parts: str, length: int = 16) -> str:
    h = hashlib.sha256((prefix + ":" + "\0".join(parts)).encode("utf-8")).hexdigest()
    return h[:length]


def run_git(args: List[str], cwd: Path) -> Optional[str]:
    try:
        proc = subprocess.run(["git", *args], cwd=str(cwd), text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False)
    except OSError:
        return None
    if proc.returncode != 0:
        return None
    out = proc.stdout.strip()
    return out or None


def resolve_repo_root(repo_root: Optional[str]) -> Path:
    start = Path(repo_root or os.getcwd()).resolve()
    git_root = run_git(["rev-parse", "--show-toplevel"], start)
    return Path(git_root).resolve() if git_root else start


def is_in_git_worktree(path: Path) -> bool:
    cur = path.resolve()
    for parent in [cur, *cur.parents]:
        if (parent / ".git").exists():
            return True
    git_root = run_git(["rev-parse", "--show-toplevel"], cur if cur.exists() else cur.parent)
    return bool(git_root)


def default_memory_home(repo_root: Path) -> Path:
    return repo_root / DEFAULT_MEMORY_SUBDIR


def ensure_safe_memory_home(memory_home: Path, repo_root: Path) -> Path:
    home = memory_home.expanduser().resolve()
    repo = repo_root.resolve()
    expected = default_memory_home(repo).resolve()
    if home != expected or repo not in home.parents:
        raise PolicyDenied("memory home must be docs/.ai-hermes-user-memory in the current repo")
    if home.exists() and (home.stat().st_mode & 0o002):
        raise PolicyDenied("memory home must not be world-writable")
    home.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(home, 0o700)
    return home


def atomic_write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2, sort_keys=True)
            fh.write("\n")
            fh.flush()
            os.fsync(fh.fileno())
        os.chmod(tmp, 0o600)
        os.replace(tmp, path)
        try:
            dir_fd = os.open(str(path.parent), os.O_DIRECTORY)
            try:
                os.fsync(dir_fd)
            finally:
                os.close(dir_fd)
        except OSError:
            pass
    finally:
        if tmp.exists():
            tmp.unlink()


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing_mode = (path.stat().st_mode & 0o777) if path.exists() else 0o644
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        os.chmod(tmp, existing_mode)
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CorruptMemory(f"corrupt json: {mask_path(path)}") from exc


def validate_candidate_id(candidate_id: str) -> str:
    if not isinstance(candidate_id, str) or not SAFE_CANDIDATE_ID_RE.fullmatch(candidate_id):
        raise PolicyDenied("invalid candidate id")
    return candidate_id


def candidate_path(ctx: Context, candidate_id: str) -> Path:
    cid = validate_candidate_id(candidate_id)
    base = ctx.candidates_dir.resolve()
    path = (ctx.candidates_dir / f"{cid}.json").resolve()
    if path.parent != base:
        raise PolicyDenied("candidate path escaped memory home")
    return path


def iter_candidate_paths(ctx: Context) -> Iterable[Path]:
    if not ctx.candidates_dir.exists():
        return []
    return sorted(ctx.candidates_dir.glob("cand_*.json"))


def validate_memory_id(memory_id: str) -> str:
    if not isinstance(memory_id, str) or not SAFE_MEMORY_ID_RE.fullmatch(memory_id):
        raise PolicyDenied("invalid memory id")
    return memory_id


def mask_path(path: Path) -> str:
    s = str(path.expanduser())
    home = str(Path.home())
    if s.startswith(home):
        return "~" + s[len(home):]
    return re.sub(r"/Users/[^/]+", "/Users/<user>", s)


def mask_text(value: str) -> str:
    return LOCAL_PATH_RE.sub(lambda m: f"{m.group(1)}<LOCAL_PATH>", value)


def redact_for_human(value: Any) -> Any:
    if isinstance(value, dict):
        redacted = {}
        for key, item in value.items():
            if str(key).lower() in {"path", "file", "dir", "directory", "executable"} and isinstance(item, str) and Path(item).expanduser().is_absolute():
                redacted[key] = "<LOCAL_PATH>"
            else:
                redacted[key] = redact_for_human(item)
        return redacted
    if isinstance(value, list):
        return [redact_for_human(item) for item in value]
    if isinstance(value, str):
        return mask_text(value)
    return value


def mask_identity(identity: str) -> str:
    if "@" in identity:
        left, right = identity.split("@", 1)
        return (left[:1] + "***@" + right) if left else "***@" + right
    return identity[:1] + "***" if identity else "unknown"


def normalize_remote(url: str) -> str:
    value = url.strip()
    value = re.sub(r"^[a-z]+://[^/@]+:[^/@]+@", "https://", value, flags=re.I)
    value = re.sub(r"^[a-z]+://[^/@]+@", "https://", value, flags=re.I)
    m = re.match(r"git@([^:]+):(.+)$", value)
    if m:
        value = f"https://{m.group(1)}/{m.group(2)}"
    value = re.sub(r"\.git$", "", value)
    value = re.sub(r"^(https?://)([^/]+)", lambda m: m.group(1) + m.group(2).lower(), value)
    return value


def mask_repo_label(normalized: str) -> str:
    if normalized.startswith("http"):
        parts = normalized.split("/")
        if len(parts) >= 5:
            return f"{parts[2]}/***/{parts[-1]}"
    return "local-repo-" + stable_id("repo-label", normalized, length=8)


class MemoryErrorBase(Exception):
    code = EXIT_VALIDATION


class PolicyDenied(MemoryErrorBase):
    code = EXIT_POLICY_DENIED


class SecretBlocked(MemoryErrorBase):
    code = EXIT_SECRET_BLOCKED


class LockTimeout(MemoryErrorBase):
    code = EXIT_LOCK_TIMEOUT


class IdentityFailed(MemoryErrorBase):
    code = EXIT_IDENTITY_FAILED


class CorruptMemory(MemoryErrorBase):
    code = EXIT_CORRUPT


class NotFound(MemoryErrorBase):
    code = EXIT_NOT_FOUND


@dataclasses.dataclass
class Context:
    repo_root: Path
    memory_home: Path
    config: Dict[str, Any]
    user_hash: str
    repo_hash: str
    identity_source: str
    identity_confidence: str
    masked_identity: str
    repo_identity_source: str
    masked_repo_label: str

    @property
    def user_dir(self) -> Path:
        return self.memory_home / "users" / self.user_hash

    @property
    def repo_path(self) -> Path:
        return self.user_dir / "repos" / f"{self.repo_hash}.json"

    @property
    def candidates_dir(self) -> Path:
        return self.user_dir / "candidates"

    @property
    def audit_path(self) -> Path:
        return self.user_dir / "audit.log.jsonl"

    @property
    def locks_dir(self) -> Path:
        return self.memory_home / "locks"


class FileLock:
    def __init__(self, path: Path, timeout: float = 5.0):
        self.path = path
        self.timeout = timeout
        self.fh = None

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.fh = open(self.path, "a+", encoding="utf-8")
        os.chmod(self.path, 0o600)
        deadline = time.time() + self.timeout
        while True:
            try:
                fcntl.flock(self.fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                return self
            except BlockingIOError:
                if time.time() >= deadline:
                    raise LockTimeout(f"lock timeout: {mask_path(self.path)}")
                time.sleep(0.05)

    def __exit__(self, exc_type, exc, tb):
        if self.fh:
            fcntl.flock(self.fh.fileno(), fcntl.LOCK_UN)
            self.fh.close()


def scan_secret(value: Any) -> None:
    def normalize_secret_key(key: Any) -> str:
        raw = str(key).strip()
        snake = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", raw)
        return snake.lower().replace("-", "_")

    def has_sensitive_key_payload(obj: Any) -> bool:
        if isinstance(obj, dict):
            for key, item in obj.items():
                normalized = normalize_secret_key(key)
                compact = re.sub(r"[^a-z0-9]", "", str(key).lower())
                if (SECRET_KEY_RE.fullmatch(normalized) or compact in SECRET_KEY_COMPACT_NAMES) and item not in (None, "", [], {}):
                    return True
                if has_sensitive_key_payload(item):
                    return True
        if isinstance(obj, list):
            return any(has_sensitive_key_payload(item) for item in obj)
        return False

    if has_sensitive_key_payload(value):
        raise SecretBlocked("secret-like content blocked")
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.startswith(("{", "[")):
            try:
                parsed = json.loads(stripped)
            except json.JSONDecodeError:
                pass
            else:
                if not isinstance(parsed, str):
                    scan_secret(parsed)
    text = json.dumps(value, ensure_ascii=False) if not isinstance(value, str) else value
    for pat in SECRET_PATTERNS:
        if pat.search(text):
            raise SecretBlocked("secret-like content blocked")


def rel_to_memory_home(ctx: Context, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ctx.memory_home))
    except ValueError:
        return mask_path(path)


def iter_memory_files(ctx: Context) -> List[Path]:
    if not ctx.memory_home.exists():
        return []
    return sorted(path for path in ctx.memory_home.rglob("*") if path.is_file())


def scan_memory_home_tree(ctx: Context) -> List[Dict[str, Any]]:
    issues: List[Dict[str, Any]] = []
    for path in iter_memory_files(ctx):
        rel = rel_to_memory_home(ctx, path)
        if path.name == "profile.json":
            issues.append({"severity": "high", "code": "profile_json_forbidden", "path": rel})
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            issues.append({"severity": "high", "code": "non_text_memory_file", "path": rel})
            continue
        try:
            scan_secret(text)
        except SecretBlocked:
            issues.append({"severity": "high", "code": "secret_like_memory_file", "path": rel})
            continue
        if path.suffix == ".json":
            try:
                parsed = json.loads(text or "{}")
            except json.JSONDecodeError:
                issues.append({"severity": "high", "code": "corrupt_memory_file", "path": rel})
                continue
            try:
                scan_secret(parsed)
            except SecretBlocked:
                issues.append({"severity": "high", "code": "secret_like_memory_file", "path": rel})
        elif path.suffix == ".jsonl":
            for lineno, line in enumerate(text.splitlines(), start=1):
                if not line.strip():
                    continue
                try:
                    parsed = json.loads(line)
                except json.JSONDecodeError:
                    issues.append({"severity": "high", "code": "corrupt_memory_file", "path": rel, "line": lineno})
                    break
                try:
                    scan_secret(parsed)
                except SecretBlocked:
                    issues.append({"severity": "high", "code": "secret_like_memory_file", "path": rel, "line": lineno})
                    break
    return issues


def classify_value(value: Any) -> Tuple[str, str]:
    text = json.dumps(value, ensure_ascii=False)
    if contains_absolute_path(value):
        return "local_only", "personal_path"
    if LOCAL_PATH_RE.search(text):
        return "local_only", "personal_path"
    return "portable", "low"


def has_auto_learn_forbidden_value(value: Any) -> bool:
    if contains_absolute_path(value):
        return True
    if isinstance(value, dict):
        for key, item in value.items():
            lowered = str(key).lower()
            if any(token in lowered for token in ("host", "profile", "customer", "client", "account_alias")):
                return True
            if has_auto_learn_forbidden_value(item):
                return True
    if isinstance(value, list):
        return any(has_auto_learn_forbidden_value(item) for item in value)
    if isinstance(value, str):
        lowered = value.lower()
        if any(marker in lowered for marker in ("profile", "customer", "client")):
            return True
        if re.search(r"\b[a-z0-9-]+(\.[a-z0-9-]+)+\b", lowered):
            return True
    return False


def contains_absolute_path(value: Any) -> bool:
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key).lower() in {"path", "file", "dir", "directory", "executable"} and isinstance(item, str):
                if Path(item).expanduser().is_absolute():
                    return True
            if contains_absolute_path(item):
                return True
    if isinstance(value, list):
        return any(contains_absolute_path(item) for item in value)
    if isinstance(value, str):
        return bool(LOCAL_PATH_RE.search(value) or Path(value).expanduser().is_absolute())
    return False


def normalize_enabled_flags(flags: Optional[Dict[str, Any]]) -> Dict[str, bool]:
    out = dict(DEFAULT_ENABLED)
    if isinstance(flags, dict):
        for key in DEFAULT_ENABLED:
            if key in flags:
                out[key] = bool(flags[key])
    if not out["learn"]:
        out["auto_learn"] = False
    return out


def default_enabled_for(ctx: Context) -> Dict[str, bool]:
    return normalize_enabled_flags(ctx.config.get("default_enabled"))


def init_config(memory_home: Path) -> Dict[str, Any]:
    cfg_path = memory_home / "config.json"
    cfg = read_json(cfg_path, None)
    if cfg is None:
        cfg = {
            "schema_version": SCHEMA_VERSION,
            "identity_salt": secrets.token_hex(16),
            "default_enabled": dict(DEFAULT_ENABLED),
            "repo_overrides": {},
            "created_at": utc_now(),
            "updated_at": utc_now(),
        }
        atomic_write_json(cfg_path, cfg)
    else:
        default_enabled = cfg.get("default_enabled")
        normalized_enabled = normalize_enabled_flags(default_enabled)
        changed = False
        if default_enabled != normalized_enabled:
            cfg["default_enabled"] = normalized_enabled
            changed = True
        if changed:
            cfg["updated_at"] = utc_now()
            atomic_write_json(cfg_path, cfg)
    os.chmod(cfg_path, 0o600)
    return cfg


def resolve_identity(repo_root: Path, salt: str) -> Tuple[str, str, str, str]:
    sources = [
        ("git_config_user_email", run_git(["config", "user.email"], repo_root)),
        ("git_config_user_name", run_git(["config", "user.name"], repo_root)),
        ("git_user_config_email", run_git(["config", "--global", "user.email"], repo_root)),
        ("git_user_config_name", run_git(["config", "--global", "user.name"], repo_root)),
    ]
    for source, ident in sources:
        if ident:
            normalized = ident.strip().lower()
            return stable_id("ai-hermes-user-v1", salt, normalized), source, "high", mask_identity(normalized)
    fallback = f"{getpass.getuser()}:{repo_root}"
    return stable_id("ai-hermes-user-v1", salt, fallback), "system_user_repo_hash_fallback", "low", "low-confidence-local-user"


def resolve_repo(repo_root: Path) -> Tuple[str, str, str]:
    remote = run_git(["config", "--get", "remote.origin.url"], repo_root)
    if remote:
        normalized = normalize_remote(remote)
        return stable_id("ai-hermes-repo-v1", normalized), "remote_origin_url", mask_repo_label(normalized)
    git_root = run_git(["rev-parse", "--show-toplevel"], repo_root)
    if git_root:
        normalized = str(Path(git_root).resolve())
        return stable_id("ai-hermes-repo-v1", normalized), "local_path", mask_repo_label(normalized)
    normalized = str(repo_root.resolve())
    return stable_id("ai-hermes-repo-v1", normalized), "cwd", mask_repo_label(normalized)


def build_context(args: argparse.Namespace) -> Context:
    repo_root = resolve_repo_root(getattr(args, "repo_root", None))
    configured_home = getattr(args, "memory_home", None) or os.environ.get("AI_HERMES_MEMORY_HOME")
    if configured_home:
        configured_path = Path(configured_home).expanduser()
        memory_home_input = configured_path if configured_path.is_absolute() else repo_root / configured_path
    else:
        memory_home_input = default_memory_home(repo_root)
    memory_home = ensure_safe_memory_home(memory_home_input, repo_root)
    cfg = init_config(memory_home)
    user_hash, identity_source, confidence, masked = resolve_identity(repo_root, cfg["identity_salt"])
    repo_hash, repo_source, repo_label = resolve_repo(repo_root)
    return Context(repo_root, memory_home, cfg, user_hash, repo_hash, identity_source, confidence, masked, repo_source, repo_label)


def resolve_agents_path(ctx: Context, agents_path: Optional[str]) -> Path:
    raw = Path(agents_path or "AGENTS.md").expanduser()
    path = raw if raw.is_absolute() else ctx.repo_root / raw
    resolved = path.resolve()
    if resolved == ctx.repo_root or ctx.repo_root not in resolved.parents:
        raise PolicyDenied("AGENTS guidance path must stay inside current repo")
    return resolved


def find_agents_section(lines: List[str]) -> Tuple[Optional[int], Optional[int]]:
    start = None
    for idx, line in enumerate(lines):
        if line.strip() == AGENTS_GUIDANCE_HEADER:
            start = idx
            break
    if start is None:
        return None, None
    for idx in range(start + 1, len(lines)):
        stripped = lines[idx].lstrip()
        if stripped.startswith("# ") and stripped.strip() != AGENTS_GUIDANCE_HEADER:
            return start, idx
    return start, len(lines)


def upsert_agents_guidance(text: str) -> Tuple[str, str]:
    guidance_lines = AGENTS_GUIDANCE.strip("\n").splitlines()
    lines = text.splitlines()
    start, end = find_agents_section(lines)
    if start is not None and end is not None:
        updated = lines[:start] + guidance_lines
        if lines[end:]:
            updated += [""] + lines[end:]
        action = "updated"
    else:
        insert_at = len(lines)
        for idx, line in enumerate(lines):
            if line.strip() == "# Output Discipline":
                insert_at = idx
                break
        prefix = lines[:insert_at]
        suffix = lines[insert_at:]
        if prefix and prefix[-1] != "":
            prefix.append("")
        updated = prefix + guidance_lines
        if suffix:
            updated += [""] + suffix
        action = "created"
    rendered = "\n".join(updated).rstrip() + "\n"
    if rendered == (text.rstrip() + "\n" if text else ""):
        action = "unchanged"
    return rendered, action


def empty_memory(ctx: Context, scope: str) -> Dict[str, Any]:
    now = utc_now()
    base = {
        "schema_version": SCHEMA_VERSION,
        "user_hash": ctx.user_hash,
        "scope": scope,
        "enabled": default_enabled_for(ctx),
        "metadata": {
            "created_at": now,
            "updated_at": now,
            "identity_source": ctx.identity_source,
            "identity_confidence": ctx.identity_confidence,
        },
        "memories": [],
    }
    if scope == "repo_user":
        base["repo_hash"] = ctx.repo_hash
        base["metadata"]["repo_identity_source"] = ctx.repo_identity_source
    return base


def memory_path(ctx: Context, scope: str) -> Path:
    if scope == "repo_user":
        return ctx.repo_path
    raise ValueError("invalid or unsupported scope")


def load_memory(ctx: Context, scope: str) -> Dict[str, Any]:
    path = memory_path(ctx, scope)
    mem = read_json(path, None)
    return mem if mem is not None else empty_memory(ctx, scope)


def save_memory(ctx: Context, scope: str, mem: Dict[str, Any]) -> None:
    mem.setdefault("metadata", {})["updated_at"] = utc_now()
    atomic_write_json(memory_path(ctx, scope), mem)


def audit(ctx: Context, event: Dict[str, Any]) -> None:
    scan_secret(event)
    ctx.user_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    line = json.dumps({"timestamp": utc_now(), **event}, ensure_ascii=False, sort_keys=True)
    with FileLock(ctx.locks_dir / f"{ctx.user_hash}.audit.lock"):
        with open(ctx.audit_path, "a", encoding="utf-8") as fh:
            os.chmod(ctx.audit_path, 0o600)
            fh.write(line + "\n")
            fh.flush()
            os.fsync(fh.fileno())


def enabled_for(ctx: Context, scope: str) -> Dict[str, bool]:
    mem = load_memory(ctx, scope)
    return normalize_enabled_flags(mem.get("enabled") or ctx.config.get("default_enabled"))


def cmd_status(ctx: Context, args: argparse.Namespace) -> Dict[str, Any]:
    enabled = enabled_for(ctx, "repo_user")
    return {
        "memory_model": "project_scoped_user_memory",
        "user_hash": ctx.user_hash,
        "repo_hash": ctx.repo_hash,
        "identity_source": ctx.identity_source,
        "identity_confidence": ctx.identity_confidence,
        "repo_identity_source": ctx.repo_identity_source,
        "memory_home": mask_path(ctx.memory_home),
        "project_enabled": enabled,
        "repo_enabled": enabled,
        "supported_scopes": sorted(SCOPES),
        "warnings": [] if ctx.identity_confidence == "high" else ["low identity confidence; auto learn writes are blocked"],
    }


def cmd_identity(ctx: Context, args: argparse.Namespace) -> Dict[str, Any]:
    return {
        "user_hash": ctx.user_hash,
        "repo_hash": ctx.repo_hash,
        "identity_source": ctx.identity_source,
        "identity_confidence": ctx.identity_confidence,
        "masked_identity": ctx.masked_identity,
        "repo_identity_source": ctx.repo_identity_source,
        "masked_repo_label": ctx.masked_repo_label,
    }


def cmd_enable_disable(ctx: Context, args: argparse.Namespace, enabled_value: bool) -> Dict[str, Any]:
    scope = args.scope

    def apply_switches(flags: Dict[str, bool]) -> Dict[str, bool]:
        planned = dict(flags)
        for attr, key in [(args.recall, "recall"), (args.learn, "learn"), (args.auto_learn, "auto_learn")]:
            if attr:
                if key == "auto_learn" and enabled_value and ctx.identity_confidence != "high":
                    raise PolicyDenied("auto learn requires high-confidence identity")
                planned[key] = enabled_value
                if key == "auto_learn" and enabled_value:
                    planned["learn"] = True
                if key == "learn" and not enabled_value:
                    planned["auto_learn"] = False
        if not any([args.recall, args.learn, args.auto_learn]):
            if enabled_value:
                planned["recall"] = True
            else:
                planned.update({"recall": False, "learn": False, "auto_learn": False})
        return planned

    if args.dry_run:
        current = enabled_for(ctx, scope)
        planned = apply_switches(current)
        return {"dry_run": True, "scope": scope, "current": current, "planned": planned}
    with FileLock(ctx.locks_dir / f"{ctx.user_hash}.{ctx.repo_hash}.lock"):
        mem = load_memory(ctx, scope)
        flags = mem.setdefault("enabled", default_enabled_for(ctx))
        flags.update(apply_switches(flags))
        save_memory(ctx, scope, mem)
    audit(ctx, {"event": "enable" if enabled_value else "disable", "scope": scope, "flags": mem["enabled"]})
    return {"scope": scope, "enabled": mem["enabled"]}


def validate_memory_item(ctx: Context, item: Dict[str, Any], source: str, one_shot: bool, allow_inferred_active: bool = False) -> Dict[str, Any]:
    scan_secret(item)
    typ = item.get("type")
    scope = item.get("scope")
    key = item.get("key")
    if typ not in MEMORY_TYPES:
        raise ValueError("invalid memory type")
    if scope not in SCOPES:
        raise ValueError("invalid or unsupported scope")
    if not key:
        raise ValueError("memory key is required")
    portability, sensitivity = classify_value(item.get("value"))
    if typ == "local_runtime_preference":
        portability = "local_only"
        sensitivity = "personal_path"
    if typ == "project_private_config":
        portability = "local_only" if portability == "local_only" else item.get("portability", "repo_specific")
        sensitivity = "personal_path" if sensitivity == "personal_path" else item.get("sensitivity", "low")
    if typ == "account_alias":
        sensitivity = "account_alias"
    if source == "inferred" and not allow_inferred_active:
        raise PolicyDenied("inferred memories must be proposed unless auto learn allows them")
    if source == "inferred" and typ not in AUTO_LEARN_TYPES:
        raise PolicyDenied("auto learn cannot write this memory type")
    if source == "inferred" and (sensitivity not in {"none", "low"} or portability == "local_only"):
        raise PolicyDenied("auto learn cannot write sensitive or local-only values")
    if source == "inferred" and has_auto_learn_forbidden_value(item.get("value")):
        raise PolicyDenied("auto learn cannot write host, profile, customer, account alias, or local path values")
    now = utc_now()
    mem_id = validate_memory_id(item.get("id") or stable_id("ai-hermes-memory-id", scope, key, json.dumps(item.get("value"), sort_keys=True), length=20))
    out = {
        "id": mem_id,
        "type": typ,
        "key": key,
        "scope": scope,
        "value": item.get("value", {}),
        "rule": item.get("rule") or "Apply this user memory only when it does not conflict with higher-priority instructions.",
        "portability": "local_only" if portability == "local_only" else item.get("portability") or portability,
        "sensitivity": "personal_path" if sensitivity == "personal_path" else item.get("sensitivity") or sensitivity,
        "commit_to_git": False,
        "apply_mode": item.get("apply_mode", "suggest_or_apply"),
        "confidence": item.get("confidence", "high" if source == "user_explicit" else "medium"),
        "evidence": item.get("evidence", {"source": source, "summary": item.get("evidence_summary", "User memory entry."), "count": 1}),
        "validation": item.get("validation", {"kind": "none", "last_checked_at": None, "last_status": "unchecked"}),
        "status": item.get("status", "active"),
        "created_at": item.get("created_at", now),
        "updated_at": now,
        "expires_at": item.get("expires_at"),
        "supersedes": item.get("supersedes", []),
        "superseded_by": item.get("superseded_by"),
        "conflict_group": item.get("conflict_group"),
    }
    if out["portability"] not in PORTABILITY or out["sensitivity"] not in SENSITIVITY or out["status"] not in STATUSES or out["confidence"] not in CONFIDENCE:
        raise ValueError("invalid memory item enum value")
    return out


def write_memory(ctx: Context, item: Dict[str, Any], source: str, one_shot: bool) -> Dict[str, Any]:
    scope = item["scope"]
    learn_flags = enabled_for(ctx, scope)
    allow_inferred = (
        source == "inferred"
        and learn_flags.get("learn")
        and learn_flags.get("auto_learn")
        and ctx.identity_confidence == "high"
        and item.get("type") in AUTO_LEARN_TYPES
    )
    if (
        not learn_flags.get("learn")
        and not (source == "user_explicit" and one_shot)
        and not allow_inferred
    ):
        raise PolicyDenied("learn is disabled; use user_explicit with one-shot authorization or enable learning")
    item = validate_memory_item(ctx, item, source, one_shot, allow_inferred_active=allow_inferred)
    lock_name = f"{ctx.user_hash}.{ctx.repo_hash}.lock"
    with FileLock(ctx.locks_dir / lock_name):
        mem = load_memory(ctx, scope)
        for existing in mem.get("memories", []):
            if existing.get("status") == "active" and existing.get("key") == item["key"] and existing.get("scope") == scope:
                if source == "inferred":
                    raise PolicyDenied("inferred memory conflicts with an active memory; propose a candidate for approval")
                existing["status"] = "superseded"
                existing["superseded_by"] = item["id"]
                item["supersedes"].append(existing["id"])
        mem.setdefault("memories", []).append(item)
        save_memory(ctx, scope, mem)
    audit(ctx, {"event": "learn", "scope": scope, "memory_id": item["id"], "type": item["type"], "key": item["key"], "source": source})
    return {"written": True, "memory_id": item["id"], "scope": scope, "key": item["key"]}


def cmd_learn(ctx: Context, args: argparse.Namespace) -> Dict[str, Any]:
    if args.source == "approved_candidate":
        raise PolicyDenied("approved_candidate writes must use approve --candidate-id")
    value = json.loads(args.value_json)
    evidence_summary = args.evidence_summary
    if evidence_summary is None and args.source == "user_explicit":
        evidence_summary = "User explicitly provided this memory."
    item = {
        "type": args.type,
        "key": args.key,
        "scope": args.scope,
        "value": value,
        "rule": args.rule,
        "evidence_summary": evidence_summary,
    }
    if args.dry_run:
        flags = enabled_for(ctx, args.scope)
        allow_inferred = args.source == "inferred" and flags.get("learn") and flags.get("auto_learn") and ctx.identity_confidence == "high" and args.type in AUTO_LEARN_TYPES
        return {"dry_run": True, "planned": validate_memory_item(ctx, item, args.source, args.one_shot_authorized, allow_inferred_active=allow_inferred)}
    result = write_memory(ctx, item, args.source, args.one_shot_authorized)
    if args.source == "user_explicit" and args.one_shot_authorized and args.scope == "repo_user":
        # Keep the just-written repo memory recallable even if defaults were customized.
        scope = args.scope
        with FileLock(ctx.locks_dir / f"{ctx.user_hash}.{ctx.repo_hash}.lock"):
            mem = load_memory(ctx, scope)
            mem.setdefault("enabled", default_enabled_for(ctx))["recall"] = True
            save_memory(ctx, scope, mem)
    return result


def cmd_recall(ctx: Context, args: argparse.Namespace) -> Dict[str, Any]:
    scopes = [args.scope] if args.scope else ["repo_user"]
    memories = []
    enabled_scopes = []
    for scope in scopes:
        mem = load_memory(ctx, scope)
        if not mem.get("enabled", {}).get("recall"):
            continue
        enabled_scopes.append(scope)
        for item in mem.get("memories", []):
            if item.get("status") != "active":
                continue
            if args.type and item.get("type") != args.type:
                continue
            if args.key and item.get("key") != args.key:
                continue
            memories.append({k: item.get(k) for k in ["id", "key", "type", "scope", "value", "apply_mode", "status", "rule", "portability", "sensitivity"]})
    return {
        "memory_model": "project_scoped_user_memory",
        "enabled": bool(enabled_scopes),
        "enabled_scopes": enabled_scopes,
        "user_hash": ctx.user_hash,
        "repo_hash": ctx.repo_hash,
        "applicable_memories": memories,
        "warnings": [],
    }


def load_candidate_arg(args: argparse.Namespace) -> Dict[str, Any]:
    if args.candidate_json:
        return json.loads(args.candidate_json)
    if args.candidate_file:
        return json.loads(Path(args.candidate_file).read_text(encoding="utf-8"))
    raise ValueError("candidate json or file is required")


def candidate_is_expired(candidate: Dict[str, Any]) -> bool:
    expires_at = parse_utc_timestamp(candidate.get("expires_at"))
    return bool(expires_at and expires_at <= datetime.now(timezone.utc))


def cleanup_candidates(
    ctx: Context,
    *,
    scope: Optional[str] = None,
    key: Optional[str] = None,
    memory_id: Optional[str] = None,
    repo_only: bool = False,
) -> List[str]:
    deleted = []
    for path in iter_candidate_paths(ctx):
        cand = read_json(path, None)
        if not cand:
            continue
        proposed = cand.get("proposed_memory", {})
        if cand.get("user_hash") != ctx.user_hash:
            continue
        if repo_only and cand.get("repo_hash") != ctx.repo_hash:
            continue
        if scope and proposed.get("scope") != scope:
            continue
        if key and proposed.get("key") != key:
            continue
        if memory_id and proposed.get("id") != memory_id:
            continue
        path.unlink(missing_ok=True)
        deleted.append(cand.get("candidate_id", path.stem))
    return deleted


def cmd_propose(ctx: Context, args: argparse.Namespace) -> Dict[str, Any]:
    cand = load_candidate_arg(args)
    scan_secret(cand)
    raw_proposed = cand.get("proposed_memory") or cand
    scope = raw_proposed.get("scope", "repo_user")
    cid = validate_candidate_id(cand.get("candidate_id") or "cand_" + stable_id("candidate", ctx.user_hash, ctx.repo_hash, json.dumps(raw_proposed, sort_keys=True), length=16))
    proposed = validate_memory_item(ctx, raw_proposed, "approved_candidate", True)
    expires = (datetime.now(timezone.utc) + timedelta(days=7)).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    payload = {
        "schema_version": SCHEMA_VERSION,
        "candidate_id": cid,
        "user_hash": ctx.user_hash,
        "repo_hash": ctx.repo_hash,
        "proposed_memory": proposed,
        "status": "pending",
        "created_at": utc_now(),
        "expires_at": cand.get("expires_at", expires),
    }
    if args.dry_run:
        return {"dry_run": True, "candidate": payload}
    path = candidate_path(ctx, cid)
    ctx.candidates_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    atomic_write_json(path, payload)
    audit(ctx, {"event": "propose", "candidate_id": cid, "scope": scope})
    return {"candidate_id": cid, "status": "pending"}


def cmd_approve(ctx: Context, args: argparse.Namespace) -> Dict[str, Any]:
    path = candidate_path(ctx, args.candidate_id)
    cand = read_json(path, None)
    if cand is None:
        raise NotFound("candidate not found")
    if cand.get("user_hash") != ctx.user_hash or cand.get("repo_hash") != ctx.repo_hash:
        raise PolicyDenied("candidate does not belong to the current user and repo")
    if cand.get("status") != "pending":
        raise PolicyDenied("candidate is not pending")
    if candidate_is_expired(cand):
        path.unlink(missing_ok=True)
        raise PolicyDenied("candidate expired")
    item = cand["proposed_memory"]
    item.setdefault("evidence", {"source": "approved_candidate", "summary": "Approved candidate.", "count": 1})
    item["evidence"]["source"] = "approved_candidate"
    if args.dry_run:
        return {"dry_run": True, "candidate_id": args.candidate_id, "planned": validate_memory_item(ctx, item, "approved_candidate", True)}
    result = write_memory(ctx, item, "approved_candidate", True)
    path.unlink(missing_ok=True)
    audit(ctx, {"event": "approve", "candidate_id": args.candidate_id, "memory_id": result["memory_id"]})
    return result


def cmd_forget(ctx: Context, args: argparse.Namespace) -> Dict[str, Any]:
    if args.all_current_user and not (args.confirm_current_user_hash == ctx.user_hash and args.confirm_delete_all):
        raise PolicyDenied("deleting current user memory requires confirmation")
    if args.all_current_repo and not (args.confirm_current_repo_hash == ctx.repo_hash and args.confirm_delete_all):
        raise PolicyDenied("deleting current repo memory requires confirmation")
    if args.dry_run:
        return {"dry_run": True, "scope": args.scope or "repo_user", "id": args.id, "key": args.key, "all_current_repo": args.all_current_repo, "all_current_user": args.all_current_user}
    deleted = []
    if args.all_current_user:
        shutil.rmtree(ctx.user_dir, ignore_errors=True)
        return {"deleted": ["current_user"]}
    if args.all_current_repo:
        ctx.repo_path.unlink(missing_ok=True)
        deleted_candidates = cleanup_candidates(ctx, repo_only=True)
        audit(ctx, {"event": "forget", "scope": "repo_user", "deleted": ["current_repo"], "deleted_candidates": deleted_candidates})
        return {"deleted": ["current_repo"], "deleted_candidates": deleted_candidates}
    scope = args.scope or "repo_user"
    if not args.id and not args.key:
        raise ValueError("forget requires --id, --key, --all-current-repo, or --all-current-user")
    deleted_candidates = cleanup_candidates(ctx, scope=scope, key=args.key, memory_id=args.id)
    with FileLock(ctx.locks_dir / f"{ctx.user_hash}.{ctx.repo_hash}.lock"):
        mem = load_memory(ctx, scope)
        kept = []
        for item in mem.get("memories", []):
            match = (args.id and item.get("id") == args.id) or (args.key and item.get("key") == args.key)
            if match:
                deleted.append(item.get("id"))
            else:
                kept.append(item)
        if not deleted and not deleted_candidates:
            raise NotFound("memory not found")
        if deleted:
            mem["memories"] = kept
            save_memory(ctx, scope, mem)
    audit(ctx, {"event": "forget", "scope": scope, "deleted": deleted, "deleted_candidates": deleted_candidates})
    return {"deleted": deleted, "deleted_candidates": deleted_candidates}


def cmd_audit(ctx: Context, args: argparse.Namespace) -> Dict[str, Any]:
    issues = []
    if ctx.memory_home != default_memory_home(ctx.repo_root).resolve():
        issues.append({"severity": "high", "code": "memory_home_not_default"})
    issues.extend(scan_memory_home_tree(ctx))
    for scope in ["repo_user"]:
        mem = load_memory(ctx, scope)
        active = {}
        for item in mem.get("memories", []):
            try:
                scan_secret(item)
            except SecretBlocked:
                issues.append({"severity": "high", "code": "secret_like_memory", "id": item.get("id")})
            if item.get("status") == "active":
                k = item.get("key")
                if k in active:
                    issues.append({"severity": "medium", "code": "multiple_active", "key": k})
                active[k] = item.get("id")
            if LOCAL_PATH_RE.search(json.dumps(item.get("value"), ensure_ascii=False)) and not (item.get("portability") == "local_only" and item.get("sensitivity") == "personal_path"):
                issues.append({"severity": "medium", "code": "local_path_not_classified", "id": item.get("id")})
    for path in iter_candidate_paths(ctx):
        cand = read_json(path, None)
        if not cand:
            continue
        try:
            scan_secret(cand)
        except SecretBlocked:
            issues.append({"severity": "high", "code": "secret_like_candidate", "candidate_id": cand.get("candidate_id", path.stem)})
        if candidate_is_expired(cand):
            issues.append({"severity": "medium", "code": "expired_candidate", "candidate_id": cand.get("candidate_id", path.stem)})
    return {"issues": issues, "recommendation": "keep" if not issues else "needs_user_confirmation"}


def cmd_ensure_agents_guidance(ctx: Context, args: argparse.Namespace) -> Dict[str, Any]:
    path = resolve_agents_path(ctx, args.agents_path)
    original = path.read_text(encoding="utf-8") if path.exists() else ""
    updated, action = upsert_agents_guidance(original)
    changed = updated != original
    if changed and not args.dry_run:
        atomic_write_text(path, updated)
    return {
        "path": str(path.relative_to(ctx.repo_root)),
        "changed": changed,
        "action": "dry_run" if args.dry_run else action,
        "identity_resolution": "dynamic_runtime_lookup",
        "hardcoded_identity_in_agents": False,
    }


def cmd_validate(ctx: Context, args: argparse.Namespace) -> Dict[str, Any]:
    audit_result = cmd_audit(ctx, args)
    high_issues = [issue for issue in audit_result["issues"] if issue.get("severity") == "high"]
    if high_issues:
        raise PolicyDenied(f"high severity memory audit issues: {json.dumps(high_issues, ensure_ascii=False, sort_keys=True)}")
    for path in [ctx.memory_home / "config.json", ctx.repo_path]:
        if path.exists():
            read_json(path, {})
            mode = path.stat().st_mode & 0o777
            if mode & 0o077:
                raise PolicyDenied(f"insecure file mode: {mask_path(path)}")
    return {"valid": True, "issues": audit_result["issues"]}


def cmd_git_sync_check(ctx: Context, args: argparse.Namespace) -> Dict[str, Any]:
    if not args.confirm_user_explicit:
        raise PolicyDenied("git memory sync requires explicit user instruction and --confirm-user-explicit")
    if not is_in_git_worktree(ctx.repo_root):
        raise PolicyDenied("git memory sync requires a git worktree")
    validation = cmd_validate(ctx, args)
    files = [rel_to_memory_home(ctx, path) for path in iter_memory_files(ctx)]
    return {
        "git_sync_allowed": True,
        "memory_home": str(DEFAULT_MEMORY_SUBDIR),
        "checked_files": files,
        "checked_file_count": len(files),
        "issues": validation["issues"],
        "required_before_stage_commit_push": "rerun git-sync-check --confirm-user-explicit",
        "force_add_command": f"git add -f {DEFAULT_MEMORY_SUBDIR.as_posix()}/config.json {DEFAULT_MEMORY_SUBDIR.as_posix()}/users",
        "privacy_note": "Only sync after explicit user instruction; never sync if sensitive content is detected.",
    }


def emit(result: Dict[str, Any], json_mode: bool) -> None:
    if json_mode:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    else:
        print(json.dumps(redact_for_human(result), ensure_ascii=False, indent=2, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="AI Hermes local user-project memory")
    p.add_argument("--repo-root")
    p.add_argument("--memory-home")
    p.add_argument("--json", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("status")
    sub.add_parser("identity")
    for name in ["enable", "disable"]:
        sp = sub.add_parser(name)
        sp.add_argument("--scope", choices=sorted(SCOPES), default="repo_user")
        sp.add_argument("--recall", action="store_true")
        sp.add_argument("--learn", action="store_true")
        sp.add_argument("--auto-learn", action="store_true", dest="auto_learn")
    sp = sub.add_parser("recall")
    sp.add_argument("--scope", choices=sorted(SCOPES))
    sp.add_argument("--type", choices=sorted(MEMORY_TYPES))
    sp.add_argument("--key")
    sp = sub.add_parser("learn")
    sp.add_argument("--scope", choices=sorted(SCOPES), default="repo_user")
    sp.add_argument("--type", choices=sorted(MEMORY_TYPES), required=True)
    sp.add_argument("--key", required=True)
    sp.add_argument("--value-json", required=True)
    sp.add_argument("--source", choices=["user_explicit", "manual_import", "inferred"], required=True)
    sp.add_argument("--one-shot-authorized", action="store_true")
    sp.add_argument("--rule")
    sp.add_argument("--evidence-summary")
    sp = sub.add_parser("propose")
    sp.add_argument("--candidate-json")
    sp.add_argument("--candidate-file")
    sp = sub.add_parser("approve")
    sp.add_argument("--candidate-id", required=True)
    sp = sub.add_parser("forget")
    sp.add_argument("--id")
    sp.add_argument("--key")
    sp.add_argument("--scope", choices=sorted(SCOPES))
    sp.add_argument("--all-current-repo", action="store_true")
    sp.add_argument("--all-current-user", action="store_true")
    sp.add_argument("--confirm-current-repo-hash")
    sp.add_argument("--confirm-current-user-hash")
    sp.add_argument("--confirm-delete-all", action="store_true")
    sub.add_parser("audit")
    sp = sub.add_parser("ensure-agents-guidance")
    sp.add_argument("--agents-path", default="AGENTS.md")
    sub.add_parser("validate")
    sp = sub.add_parser("git-sync-check")
    sp.add_argument("--confirm-user-explicit", action="store_true")
    return p


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        ctx = build_context(args)
        if args.command == "status":
            result = cmd_status(ctx, args)
        elif args.command == "identity":
            result = cmd_identity(ctx, args)
        elif args.command == "enable":
            result = cmd_enable_disable(ctx, args, True)
        elif args.command == "disable":
            result = cmd_enable_disable(ctx, args, False)
        elif args.command == "recall":
            result = cmd_recall(ctx, args)
        elif args.command == "learn":
            result = cmd_learn(ctx, args)
        elif args.command == "propose":
            result = cmd_propose(ctx, args)
        elif args.command == "approve":
            result = cmd_approve(ctx, args)
        elif args.command == "forget":
            result = cmd_forget(ctx, args)
        elif args.command == "audit":
            result = cmd_audit(ctx, args)
        elif args.command == "ensure-agents-guidance":
            result = cmd_ensure_agents_guidance(ctx, args)
        elif args.command == "validate":
            result = cmd_validate(ctx, args)
        elif args.command == "git-sync-check":
            result = cmd_git_sync_check(ctx, args)
        else:
            raise ValueError("unknown command")
        emit(result, args.json)
        return 0
    except MemoryErrorBase as exc:
        if args.json:
            print(json.dumps({"error": exc.__class__.__name__, "message": str(exc)}, ensure_ascii=False, sort_keys=True), file=sys.stderr)
        else:
            print(f"{exc.__class__.__name__}: {exc}", file=sys.stderr)
        return exc.code
    except Exception as exc:
        if args.json:
            print(json.dumps({"error": "validation_error", "message": str(exc)}, ensure_ascii=False, sort_keys=True), file=sys.stderr)
        else:
            print(f"validation_error: {exc}", file=sys.stderr)
        return EXIT_VALIDATION


if __name__ == "__main__":
    raise SystemExit(main())
