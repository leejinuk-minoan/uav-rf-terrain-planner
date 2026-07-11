# EXP-20260711-020 - Synthetic Candidate Display Preview Smoke

## Experiment Purpose

Record the Task 021F in-memory connection from the synthetic scenario through map candidate metadata, display records, and candidate preview outputs.

## Input Data

Synthetic in-memory scenario records and synthetic placeholder MGRS metadata only.

No real raster, `METADATA_MAP` content, GIS file, map screenshot, CSV file, image, PDF, or QGIS project file is used.

## Method

Build the synthetic scenario, create candidate map features, generate deterministic placeholder MGRS strings, construct source-zone metadata, rebuild the map output package with attached metadata, create candidate display records, and create preview object, JSON-ready dictionary, and plain-text output.

## Expected Result

- Candidate feature, display record, and preview record counts match.
- Candidate preview coordinates use `candidate_cell_mgrs`.
- External coordinate format is `MGRS`.
- Placeholder MGRS strings appear in dictionary and text output.
- Source-zone metadata and source-sensitive counts are preserved.
- Internal/debug coordinate keys are absent from preview dictionaries and text.
- Preview text supports positive record limits and omitted-count reporting.
- No file is written.

## Actual Result

Implemented on the Task 021F branch. The synthetic smoke helper, placeholder MGRS builder, source-zone metadata builder, preview output connection, synthetic tests, handoff document, README summary, and experiment index update were added. PR and CI status are finalized after pull request creation.

## Metrics

- New smoke modules: 1
- New smoke result dataclasses: 1
- New public smoke helpers: 4
- New test files: 1
- New handoff documents: 1
- Local terrain data files added: 0
- GIS files added: 0

## CI / Local Test Result

Local commands were not run by the Cloud Agent. GitHub Actions CI will be checked after the pull request is created and this record will be updated to the checked result.

## Interpretation

The smoke demonstrates that the existing synthetic candidate pipeline can reach a serialization-ready and human-readable preview boundary while preserving MGRS user-facing coordinates and source-zone interpretation metadata.

## Limitations

The placeholder MGRS strings are not converted coordinates and are not assessed for geographic accuracy. This task does not implement file output, a command-line interface, rendering, real terrain data access, scoring changes, LOS/Fresnel recalculation, route scoring changes, or waypoint scoring changes.

## Figure/Table Candidacy

A paper schema table or pipeline diagram can show the sequence from synthetic scenario records to map features, attached source-zone metadata, display records, and preview output.

## Public Repository Sensitivity Check

Only source code, synthetic tests, and documentation are included. No local path, sensitive coordinate, credential, secret, local dataset, or generated media file is included.

## Follow-up Tasks

1. Prepare a concise current-preview-pipeline diagram or schema table.
2. Keep file output and rendering separate from this smoke path.
3. Preserve MGRS as the external candidate coordinate format.
