# Task 028A Preview Documentation Reconciliation

## Purpose

Task 028A reconciles the preview documentation set so current implemented workflow references are clearly separated from earlier planning boundaries.

This is a documentation-only task. It does not change runtime behavior.

## Documents Added

- `docs/architecture/preview-documentation-reconciliation.md`
- `docs/handoff/task-028a-preview-documentation-reconciliation.md`
- `docs/paper/experiments/EXP-20260712-035-preview-documentation-reconciliation.md`

README receives one short Task 028A summary, and the experiment index receives one EXP-20260712-035 entry.

## Documents Updated

The following historical planning documents receive one short current implementation note near the Purpose section:

- `docs/architecture/preview-output-boundary-plan.md`
- `docs/architecture/preview-appendix-table-plan.md`
- `docs/architecture/preview-table-output-surface-plan.md`
- `docs/architecture/preview-json-input-boundary-plan.md`

Their historical bodies remain intact.

## Current Implemented Reference

The primary current references are:

```text
docs/architecture/preview-artifact-workflow.md
docs/usage/preview-artifact-workflow.md
tests/test_preview_artifact_workflow_smoke.py
```

The architecture document records the implemented end-to-end workflow, the usage document records the user-facing commands, and the smoke test provides concise executable regression coverage.

## Historical Planning Documents Marked

The four planning documents listed above are preserved as task reasoning and implementation-history records. Their notes explain that later implementation references take precedence when a historical future-tense statement differs from the current workflow.

No historical document is deleted or broadly rewritten.

## Test Coverage Reference

The reconciliation guide identifies the following current regression references:

```text
tests/test_preview_cli.py
tests/test_preview_cli_contract.py
tests/test_preview_appendix_table.py
tests/test_preview_table_cli_output.py
tests/test_preview_json_input_table_output.py
tests/test_preview_artifact_workflow_smoke.py
```

Together they cover CLI baseline behavior, JSON/plain-text contracts, appendix-table formatting, synthetic table output, saved JSON reuse, and the documented end-to-end artifact workflow.

## Current Contract Summary

Current source selectors:

```text
--synthetic
--input-json PATH
```

Current output selectors:

```text
--json
--table
--output-json PATH
--output-text PATH
--output-table PATH
```

Exactly one source is required. At most one output selector may be active. Synthetic input supports all current projections, while saved preview JSON supports table stdout and explicit table-file output only.

The current artifact workflow includes synthetic plain text, JSON stdout/file, table stdout/file, saved JSON reuse to table stdout/file, row limits, and explicit overwrite through `--force`.

Status meanings remain:

```text
0 = success
1 = handled preview/input/formatter error
2 = parser / argument error
3 = handled output-file error
```

User-facing fields remain `candidate_cell_mgrs`, `external_coordinate_format = MGRS`, `source_zone`, `source_sensitive`, and `source_zone_reason`. Internal/debug coordinate fields remain excluded.

## Reconciliation Actions

- Added one architecture reconciliation guide.
- Marked four earlier planning documents with a short current implementation note.
- Defined the reading order for current workflow, architecture, detailed contracts, historical rationale, and tests.
- Documented the current source/output, artifact, validation, coordinate, metadata, and artifact-handling boundaries.
- Added README, handoff, experiment, and experiment-index references.

## Code/Test Change Check

- Source files changed: 0
- Test files changed: 0
- CLI options changed: 0
- Formatter behavior changes: 0
- JSON schema changes: 0
- Preview field changes: 0
- File-output behavior changes: 0
- Historical planning documents deleted: 0
- Historical planning documents broadly rewritten: 0

## Test/CI Result

Task 028A changes documentation only. The Cloud Agent does not claim local compile, pytest, Ruff, mypy, or CLI execution. GitHub Actions is checked on the final PR head and reported in the completion report.

## Overall Status

The preview documentation set now has an explicit hierarchy:

1. current user workflow;
2. current end-to-end architecture;
3. detailed CLI and pipeline context;
4. historical planning rationale;
5. executable regression references.

## Limitations

Task 028A does not execute the CLI, read or write preview JSON, generate tables, inspect runtime artifacts, connect real terrain data, convert coordinates, alter scoring, or add a report or interactive surface.

The historical planning documents retain statements that describe the state at the time they were written. The new notes direct readers to later implementation references rather than rewriting those historical statements.

## Public Repository Sensitivity Check

Only repository Markdown documentation and index updates are included. No private path, credential, terrain raster, `METADATA_MAP` content, GIS file, QGIS project, generated JSON/text/table artifact, CSV, PDF, image, archive, or other runtime artifact is included.

## Follow-Up Tasks

1. Future preview tasks should cite the current implementation references and use historical planning documents only for rationale.
2. A later task may add a compact preview documentation index if additional document families are introduced.
3. Plain-text reconstruction from saved JSON, report formatting, interactive consumption, and real-terrain integration remain separate reviewed tasks.
