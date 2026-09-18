#!/usr/bin/env python3
"""Offline ocw/1 structure checks and prompt composition, NOT execution or authorization.

Python 3.10+, standard library only. Remote paths are checked syntactically: no remote
path is opened or resolved locally. Commands in prompts are never executed.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import sys
from typing import Any

MAX_BYTES = 1024 * 1024
ROOT = Path(__file__).resolve().parents[1]
IDENTITY = ('Protocol', 'Kind', 'Task', 'Revision', 'Attempt', 'Role', 'Mode',
            'Workspace', 'Snapshot', 'Risk')
ROLES = {'scout', 'designer', 'builder', 'verifier'}
ID = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.-]*\Z')
AC = re.compile(r'^-\s*(AC-[1-9]\d*):\s*(\S.*)$', re.MULTILINE)
CHECK = re.compile(r'^-\s*(V-[1-9]\d*)\s*->\s*(AC-[1-9]\d*(?:\s*,\s*AC-[1-9]\d*)*)\s*:\s*(\S.*)$', re.MULTILINE)
FAILURE = re.compile(r'^-\s*(F-[1-9]\d*)\s*->\s*(AC-[1-9]\d*(?:\s*,\s*AC-[1-9]\d*)*)\s*:\s*(\S.*)$', re.MULTILINE)
SNAPSHOT = re.compile(r'(?:git:[a-fA-F0-9]{7,64};\s*(?:clean|dirty:[A-Za-z0-9_.:-]+)|snapshot:[A-Za-z0-9][A-Za-z0-9_.:-]*|sha256:[a-fA-F0-9]{64})\Z')


@dataclass
class Contract:
    metadata: dict[str, str]
    sections: dict[str, str]
    parse_errors: list[str]


def read_text(path: Path) -> str:
    with path.open('rb') as handle:
        raw = handle.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError(f'input exceeds {MAX_BYTES} bytes')
    return raw.decode('utf-8')


def parse(text: str) -> Contract:
    metadata: dict[str, str] = {}
    parts: dict[str, list[str]] = {}
    errors: list[str] = []
    current: str | None = None
    fence: tuple[str, int] | None = None
    for line in text.splitlines():
        marker = re.match(r'^\s*(`{3,}|~{3,})(.*)$', line)
        if marker:
            run, tail = marker.groups()
            if fence is None:
                fence = (run[0], len(run))
            elif run[0] == fence[0] and len(run) >= fence[1] and not tail.strip():
                fence = None
            if current is not None:
                parts[current].append(line)
            continue
        if fence is None:
            heading = re.match(r'^##\s+(.+?)\s*$', line)
            if heading:
                current = heading.group(1)
                if current in parts:
                    errors.append(f'duplicate section: {current}')
                parts.setdefault(current, [])
                continue
            if current is None:
                match = re.match(r'^([A-Za-z][A-Za-z-]*):\s*(.*?)\s*$', line)
                if match:
                    key, value = match.groups()
                    if key in metadata:
                        errors.append(f'duplicate metadata: {key}')
                    metadata[key] = value
                    continue
        if current is not None:
            parts[current].append(line)
    if fence is not None:
        errors.append('unclosed fenced block')
    return Contract(metadata, {k: '\n'.join(v).strip() for k, v in parts.items()}, errors)


def remote_path_identity(value: str) -> str | None:
    """Syntactic absolute-path normalization; never use Path.resolve on server paths."""
    if not value or any(ord(c) < 32 for c in value):
        return None
    p: PurePosixPath | PureWindowsPath
    if value.startswith('/'):
        p = PurePosixPath(value)
    else:
        p = PureWindowsPath(value)
    if not p.is_absolute() or '..' in p.parts:
        return None
    # Preserve case: no assumptions about the remote filesystem's case sensitivity.
    return str(p)


def outside_fences(text: str) -> str:
    """Only structural prose counts as an AC/check/scope declaration, not examples in code."""
    lines: list[str] = []
    fence: tuple[str, int] | None = None
    for line in text.splitlines():
        marker = re.match(r'^\s*(`{3,}|~{3,})(.*)$', line)
        if marker:
            run, tail = marker.groups()
            if fence is None:
                fence = (run[0], len(run))
            elif run[0] == fence[0] and len(run) >= fence[1] and not tail.strip():
                fence = None
            lines.append('')
        else:
            lines.append(line if fence is None else '')
    return '\n'.join(lines)


def unresolved_placeholders(text: str) -> list[str]:
    literals = {'<...>', '{{task}}', '{{workspace}}'}
    for path in (ROOT / 'templates' / 'prompts').glob('*.md'):
        literals.update(re.findall(r'<[^<>\n]+>', path.read_text(encoding='utf-8')))
    return sorted(x for x in literals if x in text)


def validate(text: str, *, parent_text: str | None = None,
             expected_directory: str | None = None) -> dict[str, Any]:
    c = parse(text)
    m, s = c.metadata, {key: outside_fences(value) for key, value in c.sections.items()}
    errors = list(c.parse_errors)
    warnings: list[str] = []
    for key in IDENTITY:
        if not m.get(key):
            errors.append(f'missing metadata: {key}')
    if m.get('Protocol') != 'ocw/1':
        errors.append('unsupported Protocol; expected ocw/1')
    kind = m.get('Kind')
    if kind not in {'dispatch', 'rework', 'clarification'}:
        errors.append('Kind must be dispatch, rework, or clarification')
    if m.get('Role') not in ROLES:
        errors.append('Role must be scout, designer, builder, or verifier')
    if not ID.fullmatch(m.get('Task', '')):
        errors.append('Task must be a non-empty portable identifier')
    for key in ('Revision', 'Attempt'):
        if not re.fullmatch(r'[1-9]\d*', m.get(key, '')):
            errors.append(f'{key} must be a positive integer')
    if m.get('Mode') not in {'compact', 'full'}:
        errors.append('Mode must be compact or full')
    if m.get('Risk') not in {'low', 'medium', 'high'}:
        errors.append('Risk must be low, medium, or high')
    if m.get('Mode') == 'compact' and m.get('Risk') != 'low':
        errors.append('compact mode is reserved for low-risk assignments')
    directory = remote_path_identity(m.get('Workspace', ''))
    if directory is None:
        errors.append('Workspace must be an absolute server path without parent traversal')
    if expected_directory is not None:
        expected = remote_path_identity(expected_directory)
        if expected is None or expected != directory:
            errors.append('Workspace differs from the supplied expected directory')
    if not SNAPSHOT.fullmatch(m.get('Snapshot', '')):
        errors.append('Snapshot must be concrete: git:<id>; clean|dirty:<identity>, snapshot:<id>, or sha256:<digest>')
    placeholders = unresolved_placeholders(text)
    if placeholders:
        errors.append('unresolved template placeholders: ' + ', '.join(placeholders[:6]))
    if re.search(r'\b(TODO|TBD)\b', text):
        warnings.append('TODO/TBD remains; manually confirm it is not an unresolved requirement')
    if len(text.encode('utf-8')) > 16000:
        warnings.append('large brief: consider accessible references; do not discard essential constraints')

    required = {
        'dispatch': ['Goal', 'Scope', 'Acceptance', 'Checks', 'Return'],
        'rework': ['Parent', 'Failures', 'Correction', 'Preserve', 'Checks', 'Return'],
        'clarification': ['Question', 'Answer', 'Authority', 'Return'],
    }.get(kind, [])
    if kind == 'dispatch' and m.get('Mode') == 'full':
        required += ['Inputs', 'Decisions', 'Stop']
    for key in required:
        if not s.get(key):
            errors.append(f'missing/empty section: {key}')

    criteria: set[str] = set()
    if kind == 'dispatch':
        matches = AC.findall(s.get('Acceptance', ''))
        values = [a for a, _ in matches]
        criteria = set(values)
        if not criteria:
            errors.append('Acceptance requires at least one AC-n: entry')
        if len(values) != len(criteria):
            errors.append('duplicate acceptance ID')
        write = re.findall(r'^Write:\s*(\S.*)$', s.get('Scope', ''), re.MULTILINE)
        if len(write) != 1:
            errors.append('Scope requires exactly one Write: line')
        elif m.get('Role') in {'scout', 'designer', 'verifier'} and write[0].strip().lower() != 'none':
            errors.append('non-builder roles require Write: none for product files')

    parent = parse(parent_text) if parent_text is not None else None
    if kind in {'rework', 'clarification'}:
        if parent is None:
            warnings.append('parent brief not supplied: contract identity and referenced ACs require manual verification')
        else:
            parent_result = validate(parent_text or '')
            if parent_result['errors'] or parent.metadata.get('Kind') != 'dispatch':
                errors.append('parent must be a structurally valid dispatch brief')
            for key in ('Task', 'Revision', 'Role'):
                if m.get(key) != parent.metadata.get(key):
                    errors.append(f'delta {key} differs from parent; issue a new contract for changed requirements')
            if directory != remote_path_identity(parent.metadata.get('Workspace', '')):
                errors.append('delta Workspace differs from parent')
            if kind == 'rework':
                a, b = m.get('Attempt', ''), parent.metadata.get('Attempt', '')
                if a.isdigit() and b.isdigit() and int(a) <= int(b):
                    errors.append('rework Attempt must be newer than the parent dispatch attempt')
            criteria = {a for a, _ in AC.findall(outside_fences(parent.sections.get('Acceptance', '')))}

    checks = CHECK.findall(s.get('Checks', ''))
    checked: set[str] = set()
    check_ids: list[str] = []
    for cid, refs, _ in checks:
        check_ids.append(cid)
        checked.update(x.strip() for x in refs.split(','))
    if kind in {'dispatch', 'rework'}:
        if not checks:
            errors.append('Checks requires V-n -> AC-n: entries')
        if len(check_ids) != len(set(check_ids)):
            errors.append('duplicate verification ID')
        if kind == 'dispatch' or parent is not None:
            for unknown in sorted(checked - criteria):
                errors.append(f'check refers to unknown criterion {unknown}')
        if kind == 'dispatch':
            for absent in sorted(criteria - checked):
                errors.append(f'criterion has no planned evidence: {absent}')
    if kind == 'rework':
        failures = FAILURE.findall(s.get('Failures', ''))
        if not failures:
            errors.append('Failures requires F-n -> AC-n: entries')
        failure_ids = [f for f, _, _ in failures]
        if len(failure_ids) != len(set(failure_ids)):
            errors.append('duplicate finding ID')
        failing = {x.strip() for _, refs, _ in failures for x in refs.split(',')}
        if parent is not None:
            for unknown in sorted(failing - criteria):
                errors.append(f'failure refers to unknown criterion {unknown}')
        for absent in sorted(failing - checked):
            errors.append(f'failed criterion has no recheck: {absent}')
    if kind == 'clarification' and not re.search(r'\bQ-[1-9]\d*\s*:', s.get('Question', '')):
        errors.append('Question requires a Q-n: identifier')

    return {
        'status': 'failed' if errors else 'structure_pass',
        'scope': 'offline_prompt_structure_only',
        'identity': {k: m.get(k) for k in ('Task', 'Revision', 'Attempt', 'Role')},
        'chars': len(text), 'utf8_bytes': len(text.encode('utf-8')),
        'errors': errors, 'warnings': warnings,
        'not_verified': ['semantics', 'authorization', 'remote_paths', 'snapshot_existence',
                         'model_binding', 'command_execution', 'evidence_truth', 'LLM_behavior'],
    }


def compose(text: str) -> str:
    """Called after validation. Do not interpret or execute text or references."""
    if parse(text).metadata.get('Kind') != 'dispatch':
        return text.rstrip() + '\n'
    rules = read_text(ROOT / 'templates' / 'worker-rules.md').rstrip()
    return rules + '\n\n---\n\n# Task contract\n\n' + text.rstrip() + '\n'


def write_exclusive(path: Path, text: str) -> None:
    # Refuse existing targets (including symlinks); never overwrite a brief or report.
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as handle:
        handle.write(text)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest='command', required=True)
    for command in ('lint', 'render'):
        p = sub.add_parser(command)
        p.add_argument('brief', type=Path)
        p.add_argument('--parent', type=Path)
        p.add_argument('--expected-directory')
        if command == 'render':
            p.add_argument('--output', required=True, type=Path)
    args = ap.parse_args(argv)
    try:
        text = read_text(args.brief)
        parent = read_text(args.parent) if args.parent is not None else None
        result = validate(text, parent_text=parent, expected_directory=args.expected_directory)
        if not result['errors'] and args.command == 'render':
            output = compose(text)
            write_exclusive(args.output, output)
            result['rendered'] = {
                'path': str(args.output.absolute()), 'utf8_bytes': len(output.encode('utf-8')),
                'sha256': hashlib.sha256(output.encode('utf-8')).hexdigest(),
            }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2 if result['errors'] else 0
    except (OSError, ValueError) as exc:
        print(json.dumps({'status': 'error', 'error': str(exc)}, ensure_ascii=False))
        return 1


if __name__ == '__main__':
    sys.exit(main())
