# Task 021G Current Candidate Preview Pipeline Documentation

## Purpose

Task 021G documents the current candidate preview pipeline implemented across Tasks 021C through 021F. It is a documentation-only task and does not change source code or tests.

## Documents Added

- `docs/architecture/current-candidate-preview-pipeline.md`
- `docs/handoff/task-021g-current-preview-pipeline-doc.md`
- `docs/paper/experiments/EXP-20260711-021-current-preview-pipeline-doc.md`

README and the experiment index receive only short links or summary entries.

## Pipeline Scope

The documented pipeline is:

```text
Synthetic scenario
→ candidate map features
→ source-zone MGRS metadata attachment
→ candidate display records
→ candidate display preview object
→ JSON-ready preview dictionary
→ plain-text preview
```

The documentation records object boundaries, schema fields, source-zone interpretation metadata, preview output forms, and work that remains outside the current implementation.

## MGRS External Coordinate Handling

The user-facing candidate coordinate is `candidate_cell_mgrs`. The external coordinate format is `MGRS`.

Task 021G documents the existing policy only. It does not implement MGRS conversion or assess the geographic accuracy of supplied or placeholder MGRS strings.

## Internal/Debug Coordinate Handling

WGS84 components, EPSG:5179 coordinates, local `x_m` and `y_m`, and raster row/column values remain internal/debug data. The current preview schema does not expose those fields in display records, JSON-ready preview records, or plain-text preview rows.

## Source-Zone Metadata Handling

The pipeline preserves the following interpretation metadata from candidate map features through display and preview stages:

- `source_zone`
- `source_sensitive`
- `source_zone_reason`

The documentation distinguishes these metadata fields from scoring inputs. Task 021G does not modify candidate scoring, LOS/Fresnel values, route scoring, or waypoint scoring.

## Paper Figure/Table Candidacy

The architecture document provides:

- a text pipeline narrative suitable for a future conceptual figure
- a Markdown schema table suitable for adaptation into a paper table
- the JSON-ready preview schema
- the plain-text preview schema

No diagram image, SVG, PNG, PDF, or rendered artifact is created in this task.

## Test/CI Result

No test code is changed. Cloud Agent does not run local commands. GitHub Actions is used as the checked repository CI result after the pull request is created.

## Overall Status

The current Task 021C through Task 021F candidate preview pipeline is documented in one architecture reference for future paper, UI, CLI, and report-boundary planning.

## Limitations

This task does not:

- change source code
- change test code
- access real DEM, DSM, or landcover data
- access `METADATA_MAP`
- implement rendering
- create a diagram image
- implement CLI or file output
- implement MGRS conversion
- assess MGRS geographic accuracy
- change scoring or LOS/Fresnel logic
- change route or waypoint scoring

## Public Repository Sensitivity Check

Only Markdown documentation and short README/index updates are included. No private absolute path, sensitive coordinate, credential, secret, local terrain data, GIS file, generated media, CSV, PDF, or QGIS project file is included.

## Follow-Up Tasks

1. Define the Cloud versus Local boundary for future CLI, report preview, and file-output work.
2. Decide which preview schema future UI consumers should adopt.
3. Produce a final paper figure or formatted paper table in a separate reviewed artifact task.
