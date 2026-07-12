# Preview Documentation Reconciliation

## Purpose

This document reconciles the preview documentation set after the preview CLI, appendix-table formatter, saved JSON input, end-to-end workflow documentation, and focused workflow smoke tests were implemented.

It distinguishes current implemented references from earlier planning boundaries without deleting or rewriting the historical planning record. When an older planning statement differs from the implemented workflow documented and tested later, the current implemented references listed below take precedence.

Task 028A is documentation-only. It changes no source code, tests, CLI options, formatter behavior, preview fields, JSON schema, file-output behavior, scoring, terrain processing, or user-interface behavior.

## Current Implemented Reference

The primary current implementation references are:

```text
docs/architecture/preview-artifact-workflow.md
docs/usage/preview-artifact-workflow.md
tests/test_preview_artifact_workflow_smoke.py
```

Their roles are:

- `docs/architecture/preview-artifact-workflow.md`: implemented end-to-end preview artifact workflow reference;
- `docs/usage/preview-artifact-workflow.md`: user-facing command and workflow reference;
- `tests/test_preview_artifact_workflow_smoke.py`: executable regression reference for the documented workflow.

These references describe the current synthetic and saved-preview workflow after Tasks 024B through 027B. They should be consulted before treating an earlier planning statement as the current runtime contract.

## Historical Planning Documents

The following documents record planned-state or earlier boundary reasoning:

```text
docs/architecture/preview-output-boundary-plan.md
docs/architecture/preview-appendix-table-plan.md
docs/architecture/preview-table-output-surface-plan.md
docs/architecture/preview-json-input-boundary-plan.md
```

Policy:

- retain these documents;
- preserve their original task reasoning and implementation history;
- do not treat their future-tense or pre-implementation statements as the latest runtime contract;
- use the current implemented references when later implementation and tests supersede an earlier planning statement;
- make reconciliation non-destructive by adding a short implementation-reference note rather than rewriting historical content.

Historical planning documents remain useful for understanding why each capability was separated into narrow tasks and how path, schema, validation, and artifact policies were established before implementation.

## Implemented Workflow Documents

The implemented documentation set has complementary roles:

| Document | Current role |
|---|---|
| `docs/architecture/current-candidate-preview-pipeline.md` | Candidate preview object and data-flow context through JSON-ready and plain-text preview values |
| `docs/architecture/preview-cli-output-contract.md` | Detailed CLI output schema, status-code, coordinate, and explicit file-output contract established before later table and saved-input additions |
| `docs/architecture/preview-artifact-workflow.md` | Current end-to-end source, output, saved JSON reuse, table, validation, and artifact workflow reference |
| `docs/usage/preview-artifact-workflow.md` | Current user-facing workflow command guide |

`current-candidate-preview-pipeline.md` explains the underlying candidate preview pipeline and should not be read as a complete statement of later CLI or artifact capabilities.

`preview-cli-output-contract.md` remains the detailed reference for the JSON/plain-text schema and base file/status policies. Where later table or saved-input behavior is involved, `preview-artifact-workflow.md`, the usage guide, and current regression tests provide the later implemented state.

## Test Coverage Reference

The following tests collectively fix the current preview behavior:

```text
tests/test_preview_cli.py
tests/test_preview_cli_contract.py
tests/test_preview_appendix_table.py
tests/test_preview_table_cli_output.py
tests/test_preview_json_input_table_output.py
tests/test_preview_artifact_workflow_smoke.py
```

Coverage roles:

- `test_preview_cli.py`: CLI baseline behavior, stdout, JSON, explicit files, limits, overwrite, and error paths;
- `test_preview_cli_contract.py`: JSON and plain-text schema, primitive values, status codes, file policy, and internal-coordinate exclusion;
- `test_preview_appendix_table.py`: appendix-table formatter input validation, columns, order, limits, and formatting contract;
- `test_preview_table_cli_output.py`: synthetic preview to table stdout and explicit table-file behavior;
- `test_preview_json_input_table_output.py`: saved preview JSON input, table output, source selection, validation, and output protection;
- `test_preview_artifact_workflow_smoke.py`: the documented synthetic, saved JSON reuse, row-limited table, and explicit overwrite workflows.

The smoke test is the concise executable reference for the documented artifact workflow. The focused tests remain the detailed regression evidence for individual contracts.

## How to Read the Preview Documentation Set

Recommended reading order:

1. For the current user workflow: `docs/usage/preview-artifact-workflow.md`.
2. For the current end-to-end architecture: `docs/architecture/preview-artifact-workflow.md`.
3. For JSON/plain-text CLI contract details: `docs/architecture/preview-cli-output-contract.md`.
4. For candidate preview pipeline context: `docs/architecture/current-candidate-preview-pipeline.md`.
5. For historical rationale: `preview-output-boundary-plan.md`, `preview-appendix-table-plan.md`, `preview-table-output-surface-plan.md`, and `preview-json-input-boundary-plan.md`.
6. For executable regression evidence: `tests/test_preview_artifact_workflow_smoke.py` and the related preview tests listed above.

When a historical plan uses future-tense language for behavior that was later implemented, use the current architecture, usage, and regression references to determine present behavior.

## Current Source and Output Contract

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

Current policy:

- exactly one source selector is required;
- at most one output selector may be active;
- `--max-records` and `--force` are modifiers rather than output selectors;
- synthetic input supports all current projections;
- saved preview JSON supports table stdout and explicit table-file output only;
- synthetic input with no output selector retains plain-text stdout as the default;
- saved input without a table selector is an argument error.

Source/output compatibility:

| Source | Default text stdout | JSON stdout | JSON file | Text file | Table stdout | Table file |
|---|---:|---:|---:|---:|---:|---:|
| `--synthetic` | Yes | Yes | Yes | Yes | Yes | Yes |
| `--input-json PATH` | No | No | No | No | Yes | Yes |

## Current Artifact Workflow Contract

The current implemented workflow supports:

- synthetic plain-text stdout;
- synthetic JSON stdout;
- synthetic JSON file output;
- synthetic table stdout;
- synthetic table file output;
- saved preview JSON to table stdout;
- saved preview JSON to table file;
- row-limited plain-text and table projections;
- explicit overwrite with `--force` for selected output files.

JSON projections preserve the complete preview record set. `--max-records` limits human-readable plain-text and appendix-table rows and does not truncate JSON stdout or JSON file output.

Saved JSON reuse reads one explicit UTF-8 JSON object and passes it to the existing appendix-table formatter. It does not invoke synthetic preview generation, reconstruct the plain-text preview, or copy the selected JSON input.

## Current Validation and Status-Code Contract

```text
0 = success
1 = handled preview/input/formatter error
2 = parser / argument error
3 = handled output-file error
```

Current classification:

- input read, UTF-8 decode, JSON decode, top-level-object, schema, and formatter failures return status 1;
- missing or conflicting source selectors, conflicting output selectors, unsupported saved-input output combinations, and invalid positive limits return status 2;
- output parent, directory-target, protected-existing-file, and handled output-write failures return status 3;
- successful stdout and explicit file workflows return status 0.

Handled errors use concise stderr without a traceback. Input and formatter validation occur before table-file writing, so invalid input does not produce a partial table or replace an existing selected output.

## Coordinate and Metadata Boundary

User-facing coordinate and interpretation fields remain:

```text
candidate_cell_mgrs
external_coordinate_format = MGRS
source_zone
source_sensitive
source_zone_reason
```

`candidate_cell_mgrs` is the candidate coordinate shown in user-facing preview and table output. The workflow does not perform coordinate conversion or assess the geographic correctness of supplied or synthetic placeholder MGRS text.

Source-zone fields remain interpretation metadata. They do not change scores, record order, row numbering, colors, LOS/Fresnel values, route values, or waypoint values.

Internal/debug coordinate fields remain excluded:

```text
x_m
y_m
row
col
epsg5179_x_m
epsg5179_y_m
wgs84_lat
wgs84_lon
local_x_m
local_y_m
raster_row
raster_col
```

The appendix-table formatter rejects these keys at the preview top level or within a record.

## Artifact Handling Boundary

The current artifact policy is:

- input and output paths are explicitly selected by the user;
- there is no default artifact directory;
- parent directories are not created automatically;
- existing output files are preserved unless `--force` is supplied;
- explicit text outputs use UTF-8 and one trailing newline;
- generated runtime preview JSON, plain-text, table, CSV, PDF, image, and report artifacts remain outside the repository;
- tests use `tmp_path` or another managed temporary directory;
- no GitHub Actions artifact upload is part of this workflow;
- no Git LFS, package upload, or release asset is part of this workflow;
- no generated sample preview or table artifact is stored under `docs/`.

## Reconciliation Actions

Task 028A performs the following documentation actions:

1. Add `docs/architecture/preview-documentation-reconciliation.md`.
2. Add a short current implementation note to `docs/architecture/preview-output-boundary-plan.md`.
3. Add the same non-destructive note to `docs/architecture/preview-appendix-table-plan.md`.
4. Add the same non-destructive note to `docs/architecture/preview-table-output-surface-plan.md`.
5. Add the same non-destructive note to `docs/architecture/preview-json-input-boundary-plan.md`.
6. Point each note to the current architecture, usage, and smoke-test references.
7. Add a concise README Task 028A summary.
8. Add a Task 028A handoff and EXP-20260712-035 record.
9. Add EXP-20260712-035 to the experiment index.

The historical bodies are retained. No historical planning document is deleted or broadly rewritten.

## Non-Goals

Task 028A does not:

- change source code or tests;
- add or change CLI options;
- change formatter behavior;
- change the preview JSON schema or preview fields;
- change file-output behavior;
- delete or broadly rewrite historical planning documents;
- generate sample preview, table, report, or media artifacts;
- implement report generation, interactive presentation, or HTML output;
- access real DEM, DSM, landcover, or `METADATA_MAP` content;
- add GIS dependencies;
- convert or validate MGRS geography;
- change candidate scoring, LOS/Fresnel calculations, route scoring, or waypoint scoring;
- add external device-control behavior.

## Follow-Up Tasks

1. Future preview work should cite the current implementation references before relying on historical planning statements.
2. A later task may add a concise preview documentation index if the preview document family grows further.
3. Plain-text reconstruction from saved JSON, report formatting, interactive consumption, and real-terrain integration remain separate reviewed tasks.
