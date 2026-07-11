# EXP-20260711-018 - Candidate Display Formatter Scaffold

## Experiment Purpose

Record the Task 021D conversion from candidate map features with attached MGRS metadata into display-ready records.

## Input Data

Synthetic in-memory `CandidateCellMapFeature` records and dummy MGRS metadata only.

No local terrain datasets or generated media files are used.

## Method

The formatter reads attached candidate metadata, preserves `candidate_cell_mgrs`, color, score, reason, and source-zone fields, and returns primitive display dictionaries without internal geometry coordinates.

## Expected Result

- Display records use `candidate_cell_mgrs`.
- External coordinate format is `MGRS`.
- Color class and source zone are returned as text values.
- Internal coordinate keys are absent.
- Summary counts cover colors and source-sensitive records.
- Existing map output constructors remain unchanged.

## Actual Result

Implemented in PR #56. Candidate display records, bundle helpers, by-candidate-id mapping, summaries, synthetic tests, handoff documentation, README summary, and experiment documentation were added.

## Metrics

- New formatter modules: 1
- New display record types: 2
- New formatter helpers: 3
- New test files: 1
- New handoff documents: 1
- Local terrain data files added: 0
- GIS files added: 0

## CI / Local Test Result

Local commands were not run by the Cloud Agent. GitHub Actions CI completed successfully for PR #56 before this record update. The final documentation head is rechecked before completion reporting.

## Interpretation

The formatter creates a user-facing display-data boundary while preserving MGRS coordinate policy and excluding internal geometry values.

## Limitations

This task does not implement rendering, MGRS conversion, coordinate-accuracy assessment, scoring changes, LOS/Fresnel recalculation, route scoring changes, or waypoint scoring changes.

## Figure/Table Candidacy

A paper-ready schema table can compare candidate map feature inputs with the user-facing display record fields.

## Public Repository Sensitivity Check

Only source and documentation changes are included. No local datasets or generated media files are included.

## Follow-up Tasks

1. Add a plain-text or JSON preview scaffold.
2. Keep rendering separate from formatter output.
3. Preserve MGRS as the external candidate coordinate format.
