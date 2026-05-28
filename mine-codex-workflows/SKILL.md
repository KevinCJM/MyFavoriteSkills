---
name: mine-codex-workflows
description: Analyze local Codex conversation history for the current project to find repeated workflows, repeated goals, recurring command patterns, and reusable skill candidates. Use when asked to scan Codex history, mine prior conversations, identify repeated project workflows, propose skill candidates, or draft skill designs from repeated Codex work.
---

# Mine Codex Workflows

## Safety Gate

- Treat this skill as privacy-sensitive because it reads local Codex history.
- Proceed only when the user explicitly asks to scan or analyze conversation history.
- Default to current-project filtering, redacted summaries, no snippets, no network, and no file writes.
- Do not output raw conversations, secrets, full external paths, or full commands with sensitive arguments.
- Do not create skills, edit agent guidance, or edit project docs unless the user explicitly asks after reviewing candidates.

## Locate The Script

Use the bundled script from the active skill folder. For a global install, this is usually under `${CODEX_HOME:-$HOME/.codex}/skills`; for a project-local copy, it may be under `skills/` in the current repo.

```bash
SKILL_DIR="${CODEX_HOME:-$HOME/.codex}/skills/mine-codex-workflows"
if [ ! -f "$SKILL_DIR/scripts/mine_codex_history.py" ]; then
  SKILL_DIR="skills/mine-codex-workflows"
fi
```

Use any available Python 3 interpreter. Prefer the project's Python when one is already specified by the repo; otherwise use `python3`.

## Modes

- **Analysis**: Run the bundled miner and summarize repeated workflow candidates.
- **Skills draft**: First run analysis, then draft human-reviewed skill proposals from high or medium candidates. Drafts are suggestions only; do not write files unless the user explicitly requests implementation.

## Default Command

```bash
SKILL_DIR="${CODEX_HOME:-$HOME/.codex}/skills/mine-codex-workflows"
if [ ! -f "$SKILL_DIR/scripts/mine_codex_history.py" ]; then
  SKILL_DIR="skills/mine-codex-workflows"
fi
python3 "$SKILL_DIR/scripts/mine_codex_history.py" \
  --project-root . \
  --days 60 \
  --min-count 2 \
  --max-sessions 500 \
  --format json
```

Use `--include-archived` only when the user wants broader historical coverage. Use `--allow-snippets` only when the user explicitly accepts redacted snippets.

For project-specific matching, repeat `--anchor` with extra project terms or pass `--workflow-rules path/to/rules.json` to replace the generic workflow rules.

For analysis plus skill proposals, add draft mode after the first safe analysis pass:

```bash
python3 "$SKILL_DIR/scripts/mine_codex_history.py" \
  --project-root . \
  --days 60 \
  --min-count 2 \
  --mode draft \
  --format json
```

Draft mode emits human-review-required suggestions; it still does not create or edit skill files.

## Workflow

1. Run the miner in `analysis` mode with a narrow time window first.
2. Read the JSON output; if schema details are needed, read `references/output_schema.md`.
3. Report scan scope, matched sessions, privacy settings, and top workflow candidates.
4. For each candidate, explain why it is or is not worth turning into a skill.
5. In skills draft mode, produce bullet-form proposals with:
   - skill name
   - trigger phrases
   - inputs and outputs
   - core workflow
   - bundled scripts or references needed
   - validation plan
   - risks and human-review notes
6. Ask for confirmation before creating or editing any skill files.

## Interpretation Rules

- Treat candidates as evidence-backed suggestions, not truth.
- Prefer workflows repeated across multiple sessions or days with stable commands and file sets.
- Prefer small, single-purpose skills over broad umbrella skills.
- If a candidate overlaps an existing skill, recommend updating the existing skill instead of creating a duplicate.
- If the miner reports parse errors or unreadable files, mention coverage limits.
- If generic candidates are too broad, rerun with project-specific `--anchor` or `--workflow-rules` rather than editing this skill.

## Portable Validation

```bash
python3 "$SKILL_DIR/scripts/mine_codex_history.py" --project-root . --days 7 --max-sessions 20 --format json
python3 -m py_compile "$SKILL_DIR/scripts/mine_codex_history.py"
```

For this repository's project-local copy, also run the repo's own tests if present:

```bash
python3 -m pytest tests/tools/test_mine_codex_workflows.py
```
