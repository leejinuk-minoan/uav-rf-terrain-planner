# Preview Artifact Workflow Usage

## Overview

The preview CLI can generate a synthetic candidate preview, print it in several review formats, save selected artifacts, and reuse a saved preview JSON file to produce an appendix table.

Two source selectors are available:

```text
--synthetic
--input-json PATH
```

Exactly one source is required. Synthetic mode supports all current output projections. Saved JSON mode supports table and report stdout/file output.

## Quick Commands

```text
python -m uav_rf_terrain.preview_cli --synthetic
python -m uav_rf_terrain.preview_cli --synthetic --json
python -m uav_rf_terrain.preview_cli --synthetic --output-json <PREVIEW_JSON>
python -m uav_rf_terrain.preview_cli --synthetic --table
python -m uav_rf_terrain.preview_cli --synthetic --output-table <TABLE_MD>
python -m uav_rf_terrain.preview_cli --input-json <PREVIEW_JSON> --table
python -m uav_rf_terrain.preview_cli --input-json <PREVIEW_JSON> --output-table <TABLE_MD>
python -m uav_rf_terrain.preview_cli --synthetic --report
python -m uav_rf_terrain.preview_cli --synthetic --output-report <REPORT_MD>
python -m uav_rf_terrain.preview_cli --input-json <PREVIEW_JSON> --report
python -m uav_rf_terrain.preview_cli --input-json <PREVIEW_JSON> --output-report <REPORT_MD>
```

Use actual user-selected paths in place of `<PREVIEW_JSON>` and `<TABLE_MD>`. The CLI does not create missing parent directories.

## Generate Preview JSON

Print the complete preview dictionary to stdout:

```text
python -m uav_rf_terrain.preview_cli --synthetic --json
```

Save the complete preview dictionary as UTF-8 JSON:

```text
python -m uav_rf_terrain.preview_cli --synthetic --output-json <PREVIEW_JSON>
```

JSON modes retain all preview records even when `--max-records` is present. The row limit applies to human-readable text and appendix-table projections, not to JSON.

## Generate Table Directly from Synthetic Preview

Print an appendix table:

```text
python -m uav_rf_terrain.preview_cli --synthetic --table
```

Save an appendix table:

```text
python -m uav_rf_terrain.preview_cli --synthetic --output-table <TABLE_MD>
```

The table preserves preview record order, adds a display-only row number, and displays existing MGRS and source-zone metadata. It does not sort, rank, or recalculate scores.

## Reuse Saved Preview JSON

Print a table from a saved preview JSON file:

```text
python -m uav_rf_terrain.preview_cli --input-json <PREVIEW_JSON> --table
```

Save the resulting table:

```text
python -m uav_rf_terrain.preview_cli --input-json <PREVIEW_JSON> --output-table <TABLE_MD>
```

Saved JSON must be UTF-8, contain a JSON object at the top level, and follow the current preview contract. The selected input file is read but not rewritten.

Saved JSON mode does not support default plain text, JSON stdout, JSON file output, or plain-text file output.

## Row Limits

Limit the number of visible table rows:

```text
python -m uav_rf_terrain.preview_cli --input-json <PREVIEW_JSON> --table --max-records 3
```

The same modifier works with synthetic table output and plain-text preview output:

```text
python -m uav_rf_terrain.preview_cli --synthetic --table --max-records 3
python -m uav_rf_terrain.preview_cli --synthetic --max-records 3
```

`--max-records` must be a positive integer. Limited table and plain-text output includes an omitted-record line when additional records exist.

## Overwrite Policy

The CLI writes only to an explicit path and does not create missing parent directories.

An existing output file is preserved by default. To replace it, add `--force`:

```text
python -m uav_rf_terrain.preview_cli --input-json <PREVIEW_JSON> --output-table <TABLE_MD> --force
```

The same overwrite policy applies to synthetic JSON, text, and table file outputs.

## Common Error Categories

```text
0 = success
1 = handled preview/input/formatter error
2 = parser / argument error
3 = handled output-file error
```

Typical status-1 cases:

- selected input is missing, is a directory, cannot be read as UTF-8 JSON, or is not a JSON object;
- saved preview fields do not satisfy the formatter contract;
- MGRS or internal-coordinate validation fails;
- synthetic preview or appendix-table formatting fails through a handled path.

Typical status-2 cases:

- neither source or both sources are selected;
- more than one output selector is active;
- saved JSON is used without a supported table or report selector;
- `--max-records` is not a positive integer.

Typical status-3 cases:

- the output parent directory does not exist;
- the selected output path is a directory;
- the output file already exists and `--force` is absent;
- another handled output write problem occurs.

Handled errors are written concisely to stderr without a traceback.

## What This Workflow Does Not Do

This workflow does not:

- discover input or output paths automatically;
- create missing directories;
- reconstruct plain-text preview output from saved JSON;
- copy or re-emit saved JSON;
- render an interactive table, card, popup, map, or HTML page;
- generate HTML, PDF, image, or interactive report rendering;
- access real DEM, DSM, landcover, or `METADATA_MAP`;
- add GIS processing;
- convert MGRS coordinates or assess supplied MGRS accuracy;
- expose internal/debug coordinates;
- sort, rank, or recalculate candidate scores;
- change route or waypoint calculations;
- produce vehicle-control or autopilot output.

Generated runtime JSON, text, table, and report files should remain outside the repository. Use temporary or explicitly disposable paths for smoke checks.

Reports use `format_preview_report(...)`, include the appendix table by default, and reject `--max-records` with status 2. Report files use explicit UTF-8 paths, create no parent directory, protect existing files unless `--force` is supplied, and print `preview saved: <PATH>` on success.
