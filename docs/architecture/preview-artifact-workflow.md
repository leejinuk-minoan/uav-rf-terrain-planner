# Preview Artifact Workflow

## Purpose

This document records the current preview artifact workflow implemented through Tasks 022B through 026B. It explains how the CLI selects a source, produces plain-text, JSON, or appendix-table projections, persists explicitly selected artifacts, and reuses a saved preview JSON file for table output.

Task 027A is documentation-only. It does not change source code, tests, CLI options, formatter behavior, preview fields, JSON schema, file-output behavior, scoring, terrain processing, or user-interface behavior.

## Current Capabilities

The current workflow supports:

- synthetic preview generation through the existing in-memory preview path;
- plain-text preview stdout;
- JSON stdout;
- explicit UTF-8 JSON file output;
- explicit UTF-8 plain-text preview file output;
- appendix-table stdout;
- explicit UTF-8 appendix-table file output;
- saved preview JSON input;
- saved preview JSON to appendix-table stdout;
- saved preview JSON to an explicit appendix-table file;
- positive row limits for plain-text and table projections;
- opt-in overwrite through `--force` for explicit output files.

The JSON projection contains the complete reviewed preview dictionary. `--max-records` limits human-readable plain-text and appendix-table rows; it does not truncate JSON stdout or JSON file output.

## Supported Source Selectors

```text
--synthetic
--input-json PATH
```

Source policy:

- exactly one source selector is required;
- `--synthetic` and `--input-json PATH` cannot be used together;
- missing or conflicting source selectors are parser/argument errors;
- existing synthetic commands remain supported;
- saved-input mode does not invoke the synthetic preview helper;
- source validation occurs before input reading or output generation.

`--synthetic` builds the existing in-memory preview result. `--input-json PATH` reads one explicitly selected UTF-8 JSON file, requires an object at the top level, and passes the decoded mapping to the existing appendix-table formatter.

## Supported Output Selectors

```text
--json
--table
--report
--output-json PATH
--output-text PATH
--output-table PATH
--output-report PATH
```

Output policy:

- at most one output selector may be active;
- output-selector conflicts are parser/argument errors;
- `--max-records` and `--force` are modifiers, not output selectors;
- the synthetic source supports all current projections;
- the saved JSON source supports `--table`, `--output-table PATH`, `--report`, and `--output-report PATH`;
- synthetic source with no output selector retains the default plain-text stdout behavior;
- saved JSON without a supported table or report selector is not supported.

Source/output compatibility:

| Source | Default text stdout | JSON stdout | JSON file | Text file | Table stdout | Table file | Report stdout | Report file |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `--synthetic` | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| `--input-json PATH` | No | No | No | No | Yes | Yes | Yes | Yes |

## End-to-End Workflows

### 1. Synthetic preview plain stdout

```text
python -m uav_rf_terrain.preview_cli --synthetic
```

Builds the synthetic preview and prints the existing human-readable preview.

### 2. Synthetic preview JSON stdout

```text
python -m uav_rf_terrain.preview_cli --synthetic --json
```

Builds the synthetic preview and prints the complete JSON-ready preview dictionary.

### 3. Synthetic preview JSON file

```text
python -m uav_rf_terrain.preview_cli --synthetic --output-json <PREVIEW_JSON>
```

Writes the complete preview dictionary as UTF-8 indented JSON to one explicit path.

### 4. Synthetic preview table stdout

```text
python -m uav_rf_terrain.preview_cli --synthetic --table
```

Builds the synthetic preview, validates the preview dictionary, and prints the appendix-table projection.

### 5. Synthetic preview table file

```text
python -m uav_rf_terrain.preview_cli --synthetic --output-table <TABLE_MD>
```

Writes the appendix-table projection to one explicit UTF-8 text path.

### 6. Saved JSON to table stdout

```text
python -m uav_rf_terrain.preview_cli --input-json <PREVIEW_JSON> --table
```

Reads the selected preview JSON, validates it through the existing formatter, and prints the table.

### 7. Saved JSON to table file

```text
python -m uav_rf_terrain.preview_cli --input-json <PREVIEW_JSON> --output-table <TABLE_MD>
```

Reads and validates the selected preview JSON, then writes the table to the selected output path.

### 8. Row-limited table

```text
python -m uav_rf_terrain.preview_cli --input-json <PREVIEW_JSON> --table --max-records 3
```

Passes `3` to the appendix-table formatter as `max_rows`. The first three records remain in input order and the formatter adds its omitted-row line.

### 9. Explicit overwrite

```text
python -m uav_rf_terrain.preview_cli --input-json <PREVIEW_JSON> --output-table <TABLE_MD> --force
```

Allows replacement of the explicitly selected existing table file after input and formatter validation complete successfully.

These commands document the current CLI workflow. Task 027A does not execute them or commit their runtime outputs.

## Synthetic Preview Workflows

The synthetic source follows this path:

```text
--synthetic
→ build_synthetic_candidate_preview_smoke(...)
→ preview_dict and preview_text
→ one selected projection
```

Available projections:

- default plain-text stdout;
- JSON stdout;
- explicit JSON file;
- explicit plain-text file;
- appendix-table stdout;
- explicit appendix-table file.

The synthetic preview uses deterministic placeholder MGRS text for schema and workflow testing. This workflow does not perform MGRS conversion or assess the geographic accuracy of those values.

## Saved JSON Reuse Workflows

The saved-input source follows this path:

```text
--input-json PATH
→ explicit path check
→ UTF-8 read
→ JSON decode
→ top-level object check
→ existing appendix-table formatter validation
→ table or report stdout, or explicit table/report file
```

Saved input supports table and report projections. It does not reconstruct the existing human-readable preview text, re-emit JSON, copy the selected JSON file, discover inputs automatically, or invoke the synthetic helper.

Handled input failures include a missing or directory path, unreadable input, invalid UTF-8, invalid JSON, non-object top level, preview schema violations, invalid MGRS contract, internal/debug coordinate keys, record-count mismatch, and invalid documented field types.

## Table Output Workflows

Both sources use the same existing formatter:

```text
format_preview_appendix_table(preview, max_rows=None)
```

The formatter:

- validates required top-level and record fields;
- validates `external_coordinate_format = MGRS`;
- preserves input record order;
- derives display-only one-based `row_no`;
- displays existing values without score recalculation;
- includes source-zone interpretation metadata;
- rejects internal/debug coordinate keys;
- supports an optional positive row limit;
- returns one deterministic Markdown/plain-text table string;
- does not mutate the input mapping;
- does not read or write files.

The CLI reuses the existing text-output helper for table files and the existing `--force` overwrite policy.

## Status Code Summary

```text
0 = success
1 = handled preview/input/formatter error
2 = parser / argument error
3 = handled output-file error
```

| Situation | Status |
|---|---:|
| Selected stdout or explicit output completes | 0 |
| Synthetic preview generation fails in a handled path | 1 |
| Saved input read, UTF-8 decode, JSON decode, top-level-object, schema, or formatter validation fails | 1 |
| Source selector is missing or conflicting | 2 |
| Output selectors conflict | 2 |
| Saved-input output combination is unsupported | 2 |
| Output parent is missing, target is a directory, protected file exists, or output write fails | 3 |

Handled errors use concise stderr without a traceback. Input or formatter failures occur before table-file writing, so no partial table is printed and an existing output file is not replaced.

## Coordinate and Metadata Boundaries

User-facing coordinate and metadata fields remain:

```text
candidate_cell_mgrs
external_coordinate_format = MGRS
source_zone
source_sensitive
source_zone_reason
```

`candidate_cell_mgrs` is the only candidate coordinate column in the appendix table. Source-zone fields remain interpretation metadata and do not alter scores, record order, row numbering, colors, LOS/Fresnel values, route values, or waypoint values.

The workflow does not perform MGRS conversion or geographic-accuracy assessment.

Internal/debug coordinates remain excluded:

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

The formatter rejects these keys at the preview top level or within a record.

## Artifact Handling Policy

- Input and output paths are explicitly selected by the user.
- There is no default artifact directory.
- Parent directories are not created automatically.
- A missing output parent or directory target is an output-file error.
- Existing output files are preserved unless `--force` is supplied.
- Explicit text outputs use UTF-8 and one trailing newline.
- Generated preview JSON, plain-text, table, CSV, PDF, image, or report artifacts are runtime outputs and are not committed.
- Tests and smoke checks may use `tmp_path` or another managed temporary directory only.
- No GitHub Actions artifact upload is part of this workflow.
- No Git LFS, package upload, or release-asset upload is part of this workflow.
- No sample preview JSON, text, or generated table file is stored under `docs/`.

## Non-Goals

Task 027A includes:

- no source code changes;
- no test changes;
- no CLI option changes;
- no formatter behavior changes;
- no JSON schema or preview field changes;
- no file-output behavior changes;
- no generated sample JSON, table, or text files;
- no additional report generator beyond the implemented pure preview report formatter and CLI projection;
- no UI table, card, popup, map, or HTML rendering;
- no real DEM, DSM, or landcover access;
- no `METADATA_MAP` access;
- no GIS dependencies;
- no MGRS conversion;
- no MGRS geographic-accuracy assessment;
- no scoring, LOS/Fresnel, route, or waypoint changes;
- no vehicle-control or autopilot output.

## Current Limitations

- The synthetic source uses placeholder MGRS values.
- Saved input must follow the current reviewed preview JSON contract.
- Saved input supports table and report stdout/file projections.
- The workflow does not reconstruct plain-text preview output from saved JSON.
- The workflow does not re-emit or copy saved JSON.
- Input and output paths are explicit; there is no path discovery.
- Parent directories are not created automatically.
- The table formatter preserves record order and does not sort, rank, or rescore.
- The workflow does not connect to real-terrain candidate generation.
- The workflow provides developer and documentation artifacts rather than an interactive application surface.

## Follow-Up Tasks

1. A focused Local task may run the documented commands as smoke checks without changing the CLI contract.
2. A later documentation task may reconcile older planned-state architecture documents with the current implemented workflow.
3. A separate formatter task may define plain-text preview reconstruction from reviewed saved JSON.
4. Separate report and UI tasks may consume reviewed preview JSON or table strings.
5. Real-terrain integration remains a separate reviewed task.
