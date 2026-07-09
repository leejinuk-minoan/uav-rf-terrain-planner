# Paper Log Structure

Task 014 introduces a sharded paper log structure for future records. The goal is to keep each new decision, research note, experiment record, and PR review small enough for focused review while preserving the legacy long logs as historical archives.

## Scope

- This structure applies to new paper-support records created after Task 014.
- Existing long logs remain in place and are not deleted, shortened, or migrated.
- The sharded files provide the working record for new decisions and evidence.
- GPT Master owns the final paper structure, contribution boundary, and interpretation.

## Directories

| Directory | Purpose |
|---|---|
| `docs/paper/decisions/` | Individual decision records |
| `docs/paper/research-notes/` | Individual research notes and reasoning records |
| `docs/paper/experiments/` | Individual experiment and verification records |
| `docs/paper/pr-reviews/` | Individual PR review records |
| `docs/paper/templates/` | Reusable templates for new records |

## Legacy Logs

The following files remain historical archive and legacy index documents:

- `docs/paper/decision-log.md`
- `docs/paper/research-log.md`
- `docs/paper/experiment-log.md`
- `docs/paper/pr-review-log.md`

Do not delete, shorten, or rewrite previous entries in these files as part of the sharding transition. If a future task needs to reference old material, link to the legacy file and create any new interpretation in the appropriate sharded directory.

## Naming

Use stable, sortable file names:

- Decisions: `DEC-YYYYMMDD-NNN-short-title.md`
- Research notes: `RN-YYYYMMDD-NNN-short-title.md`
- Experiments: `EXP-YYYYMMDD-NNN-short-title.md`
- PR reviews: `PR-XXX-short-title.md`

Use lowercase ASCII words in the short title when practical. Keep the title descriptive, but avoid embedding sensitive coordinates, unit names, account identifiers, or private paths in file names.

## Templates

Use the matching template from `docs/paper/templates/` when creating a new sharded record:

- `decision-template.md`
- `research-note-template.md`
- `experiment-template.md`
- `pr-review-template.md`

The template headings should remain stable so GPT Master can compare records across tasks.

## Public Repository Sensitivity

Every new record must include a public repository sensitivity check. Do not add:

- Secret keys, tokens, credentials, or account identifiers
- Private local paths outside the repository
- Sensitive coordinates or unit-specific operational details
- Non-public datasets or restricted source details
- Claims that exceed documented simulation or offline verification

If a detail is needed for private review, keep it outside this public repository and record only a sanitized summary.

## Paper and Product Boundaries

Paper records should distinguish method, implementation evidence, experiment evidence, limitations, and future work. Product or deployment roadmap items may be referenced only when they clarify scope; they should not be presented as paper contributions unless GPT Master explicitly approves that boundary.

## Agent Responsibilities

- GPT Master decides the record category, paper boundary, and final interpretation.
- Cloud Execution Agent may draft sharded records for GitHub-based tasks.
- Codex may edit long documents only when a local or direct patch is specifically needed.
- Claude Code may add records for local execution, UI checks, dependency issues, and environment findings.
