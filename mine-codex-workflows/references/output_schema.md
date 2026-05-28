# Mine Codex Workflows Output Schema

## JSON Fields

- `schema_version`: Stable output schema version.
- `generated_at`: UTC timestamp for the report.
- `project_root`: Redacted project-root marker, usually the basename.
- `scan_window_days`: Requested time window.
- `sources`: Local Codex sources scanned, with home paths redacted.
- `sources.anchor_count`: Number of project anchors used for current-project filtering.
- `sources.sample_anchors`: Small sample of auto-discovered and user-provided anchors.
- `limits`: Session, file-size, total-byte, and snippet limits used by the miner.
- `privacy`: Redaction and raw-content policy flags.
- `stats`: Sessions scanned, project sessions matched, candidates emitted, parse errors, unreadable files, and unknown timestamp records.
- `redaction_stats`: Counts by redaction type.
- `filter_reasons`: Counts of project-match reasons.
- `workflow_candidates`: Candidate repeated workflows.

## Candidate Fields

- `id`: Stable candidate id for this run.
- `title`: Human-readable workflow label.
- `suggested_skill_name`: Hyphen-case skill name proposal.
- `confidence`: `high`, `medium`, or `low`.
- `skill_value`: `high`, `medium`, or `low`.
- `frequency`: Distinct matched sessions.
- `distinct_days`: Distinct days represented by evidence.
- `evidence_basis`: How the candidate was formed; default rules are generic templates plus history signals.
- `evidence_counts`: Counts of sessions, commands, files, and trigger terms.
- `trigger_phrases`: Redacted terms that caused the match.
- `repeated_goal`: Summary of the repeated objective.
- `common_steps`: Reusable workflow steps inferred from the matching rule and evidence.
- `common_files`: Repo-relative files or redacted external basenames.
- `common_commands`: Redacted command templates, not raw commands.
- `risks`: Privacy, correctness, or workflow risks.
- `requires_human_review`: Always true.
- `draft_suggestion`: Present only with `--mode draft`; contains a skill proposal, not a ready-to-install skill.

## Portable Customization

- Use `--anchor VALUE` to add project-specific match anchors without editing the skill.
- Use `--workflow-rules rules.json` to replace the generic workflow rules for a project or team.
- A custom rules file can be either a list of rule objects or an object with `workflow_rules`.
- Each rule should include `id`, `terms`, and optionally `title`, `goal`, `steps`, and `risks`.

## Safety Requirements

- Raw conversation text must not appear in output by default.
- Snippets, if enabled, must be short and redacted.
- Full home paths, tokens, cookies, JWTs, database URLs, API keys, and private-key blocks must be redacted.
- Candidates are suggestions and must be reviewed before creating a skill.
