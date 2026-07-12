# Task 027A Preview Artifact Workflow Documentation

## Purpose

Task 027A documents the implemented preview artifact workflow from synthetic preview generation through explicit JSON/text/table output and saved preview JSON reuse for appendix-table output.

This is a documentation-only task. It does not change runtime behavior.

## Documents Added

- `docs/architecture/preview-artifact-workflow.md`
- `docs/usage/preview-artifact-workflow.md`
- `docs/handoff/task-027a-preview-artifact-workflow-doc.md`
- `docs/paper/experiments/EXP-20260712-033-preview-artifact-workflow-doc.md`

README receives one short Task 027A summary, and the experiment index receives one EXP-20260712-033 entry.

## Current Capabilities Documented

The documents record:

- synthetic preview generation;
- plain-text preview stdout;
- JSON stdout;
- explicit JSON and plain-text file output;
- appendix-table stdout and explicit table-file output;
- saved preview JSON input;
- saved JSON to table stdout and table file;
- row limiting for human-readable projections;
- explicit overwrite behavior.

## Source Selector Summary

```text
--synthetic
--input-json PATH
```

Exactly one source is required. Existing synthetic commands remain supported. Saved-input mode does not invoke synthetic preview generation.

## Output Selector Summary

```text
--json
--table
--output-json PATH
--output-text PATH
--output-table PATH
```

At most one output selector may be active. Synthetic mode supports every current projection. Saved-input mode supports only table stdout and explicit table-file output.

## Workflow Commands Documented

The architecture and usage documents include command-only examples for:

1. synthetic plain-text stdout;
2. synthetic JSON stdout;
3. synthetic JSON file;
4. synthetic table stdout;
5. synthetic table file;
6. saved JSON to table stdout;
7. saved JSON to table file;
8. row-limited table;
9. explicit overwrite.

No generated command output is committed.

## Status Code Summary

```text
0 = success
1 = handled preview/input/formatter error
2 = parser / argument error
3 = handled output-file error
```

Source or output conflicts remain status 2. Input read/decode/schema/formatter failures remain status 1. Output path and write failures remain status 3.

## Coordinate and Metadata Boundaries

The documented user-facing fields remain:

```text
candidate_cell_mgrs
external_coordinate_format = MGRS
source_zone
source_sensitive
source_zone_reason
```

Internal/debug coordinate keys remain excluded. The workflow adds no coordinate conversion, accuracy assessment, score change, sorting, ranking, route change, or waypoint change.

## Artifact Handling Policy

The documents require:

- explicit user-selected paths;
- no default artifact directory;
- no automatic parent-directory creation;
- opt-in overwrite with `--force`;
- temporary paths for tests and smoke checks;
- no committed generated JSON, text, table, CSV, PDF, image, or report artifacts;
- no Actions artifact upload, Git LFS, package upload, or release asset.

## Code/Test Change Check

- Source files changed: 0
- Test files changed: 0
- CLI options changed: 0
- Formatter behavior changes: 0
- JSON schema changes: 0
- File-output behavior changes: 0

## Test/CI Result

Task 027A changes documentation only. The Cloud Agent does not claim local compile, pytest, Ruff, mypy, or CLI execution. GitHub Actions is checked on the final PR head and reported in the completion report.

## Overall Status

The implemented preview artifact workflow now has one architecture reference and one concise user-facing usage guide covering source selection, output selection, reusable JSON artifacts, appendix tables, status codes, coordinate boundaries, and artifact handling.

## Limitations

Task 027A does not:

- execute the documented CLI commands;
- generate or inspect runtime artifacts;
- change source or tests;
- alter the formatter or preview schema;
- add a report or user interface;
- access real terrain or GIS data;
- convert or validate MGRS geography;
- change scoring, LOS/Fresnel, route, or waypoint behavior.

## Public Repository Sensitivity Check

Only Markdown documentation and index updates are included. No private path, credential, token, terrain raster, `METADATA_MAP` file, GIS file, QGIS project, generated preview, generated table, CSV, PDF, image, archive, or other runtime artifact is included.

## Follow-Up Tasks

1. A focused Local task may execute the documented commands as smoke checks without changing behavior.
2. A later Cloud task may reconcile historical planned-state documents with the current implementation.
3. Plain-text reconstruction from saved JSON, report formatting, UI consumption, and real-terrain integration remain separate reviewed tasks.
