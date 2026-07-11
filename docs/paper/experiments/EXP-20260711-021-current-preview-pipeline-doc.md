# EXP-20260711-021 - Current Candidate Preview Pipeline Documentation

## Experiment Purpose

Record the documentation-only consolidation of the current candidate preview pipeline implemented across Tasks 021C through 021F.

## Input Data

Existing repository source files, handoff documents, experiment records, and README content only.

No real raster, `METADATA_MAP` content, GIS file, map screenshot, CSV file, image, PDF, or QGIS project file is used.

## Method

Review the current candidate map feature, optional source-zone MGRS metadata, display record, preview object, JSON-ready dictionary, plain-text preview, and synthetic smoke contracts. Consolidate those contracts into one architecture document containing a pipeline narrative, Markdown schema table, coordinate boundaries, source-zone interpretation boundary, preview schemas, limitations, and figure/table candidacy.

## Expected Result

- One architecture document describes the complete Task 021C through Task 021F pipeline.
- The documented pipeline uses `candidate_cell_mgrs` as the user-facing candidate coordinate.
- The documented external coordinate format is `MGRS`.
- Internal/debug coordinate fields remain outside display and preview outputs.
- Source-zone interpretation metadata is described separately from scoring behavior.
- JSON-ready and plain-text preview schemas are recorded.
- No source or test code is changed.
- No image or rendered diagram is generated.

## Actual Result

Implemented in PR #59. The architecture document, handoff record, experiment record, README summary, and experiment index entry were added without source or test code changes.

## Metrics

- Architecture documents added: 1
- Handoff documents added: 1
- Experiment records added: 1
- Markdown schema tables added: 1
- Source files changed: 0
- Test files changed: 0
- Diagram image files added: 0
- Local terrain data files added: 0
- GIS files added: 0

## CI / Local Test Result

Local commands were not run by the Cloud Agent. GitHub Actions CI completed successfully for PR #59 on the checked documentation head. The final documentation-status commit is rechecked before completion reporting.

## Interpretation

The current candidate preview pipeline now has a single architecture reference describing how synthetic scenario records progress through candidate map metadata, display records, and in-memory preview outputs while preserving the MGRS external coordinate policy.

## Limitations

This documentation task does not execute code, implement CLI or file output, render maps, tables, popups, HTML, or application UI, convert MGRS coordinates, assess MGRS geographic accuracy, modify scoring, recalculate LOS/Fresnel values, or change route and waypoint scoring.

## Figure/Table Candidacy

The architecture pipeline narrative is a candidate for a future conceptual figure. The Markdown schema table is a candidate for adaptation into a paper table comparing stages, object contracts, coordinate boundaries, internal-field exposure, and implementation status.

No figure image is generated in this task.

## Public Repository Sensitivity Check

Only repository documentation is included. No private path, sensitive coordinate, credential, secret, local dataset, GIS file, generated media, CSV, PDF, or QGIS project file is included.

## Follow-Up Tasks

1. Define the Cloud and Local implementation boundary for future CLI, report preview, and file-output work.
2. Review whether the architecture schema should become a final paper table.
3. Preserve MGRS as the external candidate coordinate format.
