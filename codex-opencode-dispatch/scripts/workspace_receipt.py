#!/usr/bin/env python3
"""Read-only Git scope/identity receipts. No tests, acceptance, or remote operations.

Python 3.10+. All Git paths are parsed as NUL-delimited data. Changed file contents
are streamed into hashes, never included in the receipt. This is not a sandbox,
an execution attestation, or an audit of ignored files, submodules, and services.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import subprocess
import sys
from typing import Any, Sequence


class ReceiptError(RuntimeError):
    """Unsafe, unsupported, or incomplete receipt operation."""


def git(repo: Path, *args: str) -> bytes:
    env = dict(os.environ, GIT_OPTIONAL_LOCKS="0", GIT_TERMINAL_PROMPT="0")
    command = ["git", "-c", "core.fsmonitor=false", "-c", "core.untrackedCache=false",
               "-C", os.fspath(repo), *args]
    try:
        result = subprocess.run(command, capture_output=True, check=False,
                                timeout=60, env=env)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ReceiptError(f"Git inspection failed: {type(exc).__name__}") from exc
    if result.returncode != 0:
        message = result.stderr.decode("utf-8", "replace").strip()[:800]
        raise ReceiptError(f"Git inspection failed ({result.returncode}): {message}")
    return result.stdout


def names(raw: bytes) -> set[str]:
    return {os.fsdecode(item) for item in raw.split(b"\0") if item}


def digest_object(obj: Any) -> str:
    data = json.dumps(obj, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
    return hashlib.sha256(data.encode("ascii")).hexdigest()


def inspect_file(root: Path, relative: str, flags: set[str]) -> dict[str, Any]:
    logical = PurePosixPath(relative)
    if logical.is_absolute() or ".." in logical.parts:
        raise ReceiptError("Git returned a non-relative path")
    path = root.joinpath(*logical.parts)
    # Never follow a replaced parent directory to inspect outside the checkout.
    if not path.parent.resolve().is_relative_to(root):
        flags.add("path_parent_escapes_workspace")
        return {"kind": "outside_parent_not_read"}
    try:
        info = path.lstat()
    except FileNotFoundError:
        return {"kind": "missing"}
    if stat.S_ISLNK(info.st_mode):
        target = os.fsencode(os.readlink(path))
        return {"kind": "symlink", "sha256": hashlib.sha256(target).hexdigest()}
    if not stat.S_ISREG(info.st_mode):
        flags.add("directory_or_special_file_not_inspected")
        return {"kind": "directory" if stat.S_ISDIR(info.st_mode) else "special"}
    hasher = hashlib.sha256()
    try:
        # O_NOFOLLOW is available on macOS/Linux; also verify the opened inode.
        fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        with os.fdopen(fd, "rb") as stream:
            opened = os.fstat(stream.fileno())
            if not stat.S_ISREG(opened.st_mode) or (opened.st_ino, opened.st_dev) != (info.st_ino, info.st_dev):
                raise ReceiptError("File changed during snapshot; stop writers and retry")
            while block := stream.read(1024 * 1024):
                hasher.update(block)
            after = os.fstat(stream.fileno())
        end = path.lstat()
    except OSError as exc:
        raise ReceiptError(f"Cannot inspect {relative!r}: {type(exc).__name__}") from exc
    before_key = (info.st_ino, info.st_dev, info.st_size, info.st_mtime_ns, info.st_mode)
    if before_key != (after.st_ino, after.st_dev, after.st_size, after.st_mtime_ns, after.st_mode) or before_key != (end.st_ino, end.st_dev, end.st_size, end.st_mtime_ns, end.st_mode):
        raise ReceiptError("File changed during snapshot; stop writers and retry")
    return {"kind": "file", "bytes": info.st_size, "executable": bool(info.st_mode & 0o111),
            "sha256": hasher.hexdigest()}


def snapshot(repo: Path, base: str) -> dict[str, Any]:
    if base.startswith("-") or any(c in base for c in "\0\r\n"):
        raise ReceiptError("Unsafe base revision")
    root = Path(os.fsdecode(git(repo, "rev-parse", "--show-toplevel")).rstrip("\r\n")).resolve()
    base_sha = git(root, "rev-parse", "--verify", f"{base}^{{commit}}").decode().strip()
    head = git(root, "rev-parse", "--verify", "HEAD").decode().strip()
    git(root, "merge-base", "--is-ancestor", base_sha, head)
    status_start = git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    index_start = git(root, "ls-files", "--stage", "-z")
    visibility_start = git(root, "ls-files", "-v", "-z")
    diff_options = ("--no-ext-diff", "--no-textconv", "--name-only", "--no-renames", "-z")
    working = names(git(root, "diff", *diff_options, base_sha, "--"))
    staged = names(git(root, "diff", "--cached", *diff_options, base_sha, "--"))
    untracked = names(git(root, "ls-files", "--others", "--exclude-standard", "-z"))
    all_paths = sorted(working | staged | untracked)
    flags: set[str] = set()
    # `git status`/`git diff` may intentionally ignore paths marked assume-unchanged
    # or skip-worktree. Detect those index hints explicitly and require manual review
    # rather than pretending this helper observed every working-tree mutation.
    for record in visibility_start.split(b"\0"):
        if not record:
            continue
        if len(record) < 3 or record[1:2] != b" ":
            raise ReceiptError("Unexpected git ls-files -v record")
        tag = chr(record[0])
        path = os.fsdecode(record[2:])
        if tag in {"S", "s"}:
            flags.add(f"skip_worktree:{path}")
        if tag.isalpha() and tag.islower():
            flags.add(f"assume_unchanged:{path}")
    index_entries: dict[str, list[dict[str, str]]] = {}
    gitlinks: list[str] = []
    for record in index_start.split(b"\0"):
        if not record:
            continue
        metadata, encoded_path = record.split(b"\t", 1)
        mode, oid, stage = metadata.decode("ascii").split()
        path = os.fsdecode(encoded_path)
        if stage != "0":
            flags.add("unmerged_index")
        if mode == "160000":
            gitlinks.append(path)
            flags.add("submodules_not_recursively_inspected")
        if path in working or path in staged or path in untracked:
            index_entries.setdefault(path, []).append({"mode": mode, "oid": oid, "stage": stage})
    files = [{"path": p, "working": inspect_file(root, p, flags),
              "index": index_entries.get(p, []), "untracked": p in untracked} for p in all_paths]
    # These checks detect common concurrent mutations; they are not an atomic FS snapshot.
    if (status_start != git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all")
            or index_start != git(root, "ls-files", "--stage", "-z")
            or visibility_start != git(root, "ls-files", "-v", "-z")
            or head != git(root, "rev-parse", "--verify", "HEAD").decode().strip()):
        raise ReceiptError("Workspace changed during snapshot; stop writers and retry")
    body = {"root": str(root), "base": base_sha, "head": head,
            "index_sha256": hashlib.sha256(index_start).hexdigest(), "files": files,
            "changed_paths": all_paths, "gitlink_paths": sorted(gitlinks),
            "manual_review_flags": sorted(flags)}
    return {"schema_version": 1, "purpose": "workspace_scope_and_identity_only",
            **body, "fingerprint": digest_object(body),
            "limitations": ["not_atomic_stop_writers_before_capture", "no_test_execution_or_attestation",
                            "ignored_files_and_external_state_not_covered", "not_a_security_boundary"]}


def load_receipt(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ReceiptError("Cannot read a valid receipt") from exc
    required = ("root", "base", "head", "index_sha256", "files", "changed_paths", "fingerprint", "manual_review_flags", "gitlink_paths")
    if not isinstance(data, dict) or data.get("schema_version") != 1 or any(k not in data for k in required):
        raise ReceiptError("Unsupported receipt schema")
    if not isinstance(data["files"], list) or not isinstance(data["changed_paths"], list):
        raise ReceiptError("Invalid receipt inventory")
    if any(not isinstance(data[k], list) or any(not isinstance(p, str) for p in data[k])
           for k in ("changed_paths", "manual_review_flags", "gitlink_paths")):
        raise ReceiptError("Invalid receipt metadata")
    if any(not isinstance(f, dict) or not isinstance(f.get("path"), str) for f in data["files"]):
        raise ReceiptError("Invalid receipt file entry")
    if sorted(f["path"] for f in data["files"]) != sorted(data["changed_paths"]):
        raise ReceiptError("Receipt path inventory mismatch")
    body = {k: data[k] for k in ("root", "base", "head", "index_sha256", "files",
                               "changed_paths", "gitlink_paths", "manual_review_flags")}
    if digest_object(body) != data["fingerprint"]:
        raise ReceiptError("Receipt integrity mismatch (not an authenticity check)")
    return data


def normalize_rule(rule: str) -> tuple[str, bool]:
    if rule.endswith("/**"):
        rule = rule[:-2]
    if not rule or rule.startswith("/") or any(c in rule for c in "*?[]\0\r\n\\"):
        raise ReceiptError("Scope rule must be an exact relative file or a directory ending in / (or /**)")
    if any(part in ("", ".", "..") for part in rule.rstrip("/").split("/")):
        raise ReceiptError("Invalid scope rule")
    return rule, rule.endswith("/")


def matches(path: str, rules: Sequence[tuple[str, bool]]) -> bool:
    return any(path.startswith(rule) if prefix else path == rule for rule, prefix in rules)


def scope(receipt: dict[str, Any], allowed: Sequence[str], denied: Sequence[str]) -> dict[str, Any]:
    if not allowed:
        raise ReceiptError("At least one explicit allowed path is required")
    allow = [normalize_rule(r) for r in allowed]
    deny = [normalize_rule(r) for r in denied]
    unexpected = [p for p in receipt["changed_paths"] if not matches(p, allow) or matches(p, deny)]
    flags = receipt["manual_review_flags"]
    status = "scope_violation" if unexpected else "manual_review_required" if flags else "scope_only_pass"
    return {"status": status, "unexpected_paths": unexpected, "manual_review_flags": flags,
            "fingerprint": receipt["fingerprint"], "acceptance": "not_evaluated"}


def delta(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    if (before["root"], before["base"]) != (after["root"], after["base"]):
        raise ReceiptError("Delta requires the same repository root and task base")
    left = {f["path"]: f for f in before["files"]}
    right = {f["path"]: f for f in after["files"]}
    return {"same_snapshot": before["fingerprint"] == after["fingerprint"],
            "changed_since_review": [p for p in sorted(left.keys() | right.keys()) if left.get(p) != right.get(p)],
            "head_changed": before["head"] != after["head"], "acceptance": "not_evaluated"}



def scope_delta(before: dict[str, Any], after: dict[str, Any],
                allowed: Sequence[str], denied: Sequence[str]) -> dict[str, Any]:
    """Check only changes made after a pre-work receipt, not pre-existing dirty state.

    This attributes a time-window delta, not an actor: concurrent human/other-agent edits
    during the same window are included and must be coordinated separately.
    """
    if not allowed:
        raise ReceiptError("At least one explicit allowed path is required")
    change = delta(before, after)
    allow = [normalize_rule(r) for r in allowed]
    deny = [normalize_rule(r) for r in denied]
    changed = change["changed_since_review"]
    unexpected = [p for p in changed if not matches(p, allow) or matches(p, deny)]
    flags = sorted(set(before["manual_review_flags"]) | set(after["manual_review_flags"]))
    status = "scope_violation" if unexpected else "manual_review_required" if flags else "scope_only_pass"
    return {
        "status": status,
        "changed_since_before": changed,
        "unexpected_paths": unexpected,
        "manual_review_flags": flags,
        "before_fingerprint": before["fingerprint"],
        "after_fingerprint": after["fingerprint"],
        "head_changed": change["head_changed"],
        "same_snapshot": change["same_snapshot"],
        "acceptance": "not_evaluated",
    }

def write_new(path: Path, receipt: dict[str, Any]) -> None:
    destination = path.expanduser().resolve()
    if destination.is_relative_to(Path(receipt["root"])):
        raise ReceiptError("Write receipts outside the inspected repository to avoid changing its snapshot")
    # No overwrite, chmod escalation, parent creation, or project writes.
    with destination.open("x", encoding="utf-8") as stream:
        json.dump(receipt, stream, indent=2, ensure_ascii=True)
        stream.write("\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest="command", required=True)
    snap = subs.add_parser("snapshot")
    snap.add_argument("--repo", type=Path, required=True)
    snap.add_argument("--base", required=True)
    snap.add_argument("--output", type=Path)
    check = subs.add_parser("scope")
    check.add_argument("--receipt", type=Path, required=True)
    check.add_argument("--allow", action="append", required=True)
    check.add_argument("--deny", action="append", default=[])
    diff = subs.add_parser("delta")
    diff.add_argument("--before", type=Path, required=True)
    diff.add_argument("--after", type=Path, required=True)
    scoped_diff = subs.add_parser("scope-delta")
    scoped_diff.add_argument("--before", type=Path, required=True)
    scoped_diff.add_argument("--after", type=Path, required=True)
    scoped_diff.add_argument("--allow", action="append", required=True)
    scoped_diff.add_argument("--deny", action="append", default=[])
    args = parser.parse_args()
    try:
        code = 0
        if args.command == "snapshot":
            result = snapshot(args.repo, args.base)
            if args.output:
                write_new(args.output, result)
                result = {"receipt": str(args.output.resolve()), "fingerprint": result["fingerprint"],
                          "changed_file_count": len(result["changed_paths"]),
                          "manual_review_flags": result["manual_review_flags"], "acceptance": "not_evaluated"}
        elif args.command == "scope":
            result = scope(load_receipt(args.receipt), args.allow, args.deny)
            code = 0 if result["status"] == "scope_only_pass" else 2
        elif args.command == "scope-delta":
            result = scope_delta(load_receipt(args.before), load_receipt(args.after),
                                 args.allow, args.deny)
            code = 0 if result["status"] == "scope_only_pass" else 2
        else:
            result = delta(load_receipt(args.before), load_receipt(args.after))
        print(json.dumps(result, ensure_ascii=True))
        return code
    except (ReceiptError, OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"error": str(exc), "acceptance": "not_evaluated"}, ensure_ascii=True), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
