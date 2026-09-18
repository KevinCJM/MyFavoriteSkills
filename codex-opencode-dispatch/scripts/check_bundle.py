#!/usr/bin/env python3
"""Offline structure checks only; this does not evaluate an LLM or MCP connection."""
from __future__ import annotations
import ast
import json
import importlib.util
import os
from pathlib import Path
import re
import sys


def skill_files(root: Path):
    """Check Skill-owned files; the vendored MCP has its own build and test suite."""
    for directory, dirs, names in os.walk(root):
        current = Path(directory)
        dirs[:] = [name for name in dirs
                   if name not in {'.git', 'node_modules', '__pycache__'}
                   and current / name != root / 'mcp' / 'opencode-mcp']
        for name in names:
            yield current / name


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    errors = []
    core = (root / 'SKILL.md').read_text(encoding='utf-8')
    if not core.startswith('---\n') or core.count('\n---\n') < 1:
        errors.append('SKILL.md: missing frontmatter')
    if 'name: codex-opencode-dispatch\n' not in core.split('---', 2)[1]:
        errors.append('SKILL.md: wrong name')
    if len(core.split()) > 1500:
        errors.append('SKILL.md: core exceeds the 1500-word maintenance budget')
    links = 0
    owned_files = list(skill_files(root))
    markdown_files = [path for path in owned_files if path.suffix == '.md']
    for path in markdown_files:
        text = path.read_text(encoding='utf-8')
        opened = None
        for number, line in enumerate(text.splitlines(), 1):
            match = re.match(r'^\s*(`{3,}|~{3,})', line)
            if match:
                marker = match.group(1)[0]
                if opened is None:
                    opened = marker
                elif opened == marker:
                    opened = None
        if opened is not None:
            errors.append(f'{path.relative_to(root)}: unmatched fence')
        for target in re.findall(r'\[[^\]\n]+\]\(([^)\n]+)\)', text):
            target = target.split('#', 1)[0]
            if not target or '://' in target or target.startswith('mailto:'):
                continue
            links += 1
            destination = (path.parent / target).resolve()
            if not destination.is_relative_to(root) or not destination.exists():
                errors.append(f'{path.relative_to(root)}: broken local link {target}')
    python_files = [path for path in owned_files if path.suffix == '.py']
    for path in python_files:
        try:
            ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
        except SyntaxError as exc:
            errors.append(f'{path.relative_to(root)}: {exc}')
    for path in (path for path in owned_files if path.suffix == '.json'):
        try:
            json.loads(path.read_text(encoding='utf-8'))
        except ValueError as exc:
            errors.append(f'{path.relative_to(root)}: {exc}')
    cases = json.loads((root / 'evals/scenarios.json').read_text())['cases']
    if len({c['id'] for c in cases}) != len(cases):
        errors.append('behavior cases: duplicate IDs')
    for case in cases:
        if not all(case.get(k) for k in ('id', 'prompt', 'expected_route', 'must', 'must_not', 'reference')):
            errors.append(f"behavior case {case.get('id')}: missing rubric")
        if not (root / case['reference']).exists():
            errors.append(f"behavior case {case['id']}: missing reference")
    for old in ('opencode_loop', 'opencode_submit', 'opencode_audit', 'OPENCODE_MCP_PIN_MODEL'):
        for path in [root / 'SKILL.md', *list((root / 'references').glob('*.md'))]:
            if old in path.read_text():
                errors.append(f'{path.relative_to(root)}: foreign MCP capability {old}')
    # These are offline example/shape checks, not live-worker evaluations.
    expected_templates = ['compact-brief.md', 'scout-brief.md', 'designer-brief.md',
                          'builder-brief.md', 'verifier-brief.md', 'rework-brief.md',
                          'clarification.md', 'dispatch-envelope.md']
    for name in expected_templates:
        if not (root / 'templates/prompts' / name).is_file():
            errors.append(f'missing prompt template {name}')
    spec = importlib.util.spec_from_file_location('bundle_prompt_contract', root / 'scripts/prompt_contract.py')
    pc = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = pc
    spec.loader.exec_module(pc)
    example_count = 0
    parent_brief = (root / 'examples/prompts/builder.md').read_text(encoding='utf-8')
    for example in sorted((root / 'examples/prompts').glob('*.md')):
        if example.name == 'README.md':
            continue
        parent = parent_brief if example.name in ('rework.md', 'clarification.md') else None
        result = pc.validate(example.read_text(encoding='utf-8'), parent_text=parent)
        example_count += 1
        errors.extend(f'{example.relative_to(root)}: {msg}' for msg in result['errors'])
    for template in (root / 'templates/prompts').glob('*brief.md'):
        if not pc.validate(template.read_text(encoding='utf-8'))['errors']:
            errors.append(f'{template.name}: unresolved template unexpectedly looks sendable')
    metadata = (root / 'agents/openai.yaml').read_text()
    if '$codex-opencode-dispatch' not in metadata or 'allow_implicit_invocation: true' not in metadata:
        errors.append('agents/openai.yaml: missing invocation metadata')
    result = {'status': 'failed' if errors else 'passed', 'checks': 'offline_structure_only',
              'vendor_checks': 'Run npm test, npm run test:codex-stdio and npm run docs:check in mcp/opencode-mcp',
              'core_words': len(core.split()), 'core_lines': len(core.splitlines()),
              'core_utf8_bytes': len(core.encode()), 'markdown_files': len(markdown_files),
              'local_links_checked': links, 'python_files_parsed': len(python_files),
              'prompt_examples_linted': example_count,
              'behavior_cases_prepared_not_executed': len(cases), 'errors': errors}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == '__main__':
    raise SystemExit(main())
