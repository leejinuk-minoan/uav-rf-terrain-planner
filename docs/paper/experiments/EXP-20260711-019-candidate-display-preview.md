# EXP-20260711-019 - Candidate Display Preview Scaffold

## Experiment Purpose

Record the Task 021E conversion from `CandidateDisplayBundle` values into a preview object, JSON-ready dictionary, and plain-text preview string.

## Input Data

Synthetic in-memory `CandidateDisplayBundle` values and dummy MGRS metadata only.

No local terrain datasets, `METADATA_MAP` content, GIS files, map screenshots, CSV files, images, PDFs, or QGIS project files are used.

## Method

The preview layer copies primitive dictionaries from `CandidateDisplayRecord.to_display_dict()`, preserves the Task 021D summary, converts record tuples to lists for JSON-ready output, and formats readable text rows from each display label, overall score, and source-zone value.

## Expected Result

- Preview records preserve `candidate_cell_mgrs`.
- External coordinate format is `MGRS`.
- User coordinate field is `candidate_cell_mgrs`.
- Preview dictionaries are JSON serializable.
- Internal coordinate keys are absent from dictionaries and text.
- Plain-text output supports optional positive record limits and omitted-count reporting.
- No file is written.

## Actual Result

Implemented in PR #57. The preview object, JSON-ready helper, plain-text formatter, truncation behavior, synthetic tests, handoff documentation, README summary, and experiment index update were added.

## Metrics

- New preview modules: 1
- New preview dataclasses: 1
- New preview helpers: 3
- New test files: 1
- New handoff documents: 1
- Local terrain data files added: 0
- GIS files added: 0

## CI / Local Test Result

Local commands were not run by the Cloud Agent. GitHub Actions CI completed successfully for PR #57 on the checked head commit.

## Interpretation

The preview scaffold creates a serialization and human-review boundary above Task 021D without introducing file output, command-line behavior, rendering, coordinate conversion, or scoring changes.

## Limitations

This task does not implement file output, a command-line interface, rendering, MGRS conversion, coordinate-accuracy assessment, scoring changes, LOS/Fresnel recalculation, route scoring changes, or waypoint scoring changes.

## Figure/Table Candidacy

A schema table can compare the Task 021D display record, the JSON-ready preview dictionary, and the plain-text preview row.

## Public Repository Sensitivity Check

Only source code, synthetic tests, and documentation are included. No local datasets or generated media files are included.

## Follow-up Tasks

1. Add an end-to-end synthetic preview smoke in a separate task.
2. Keep file output and command-line integration separate.
3. Preserve MGRS as the external candidate coordinate format.
