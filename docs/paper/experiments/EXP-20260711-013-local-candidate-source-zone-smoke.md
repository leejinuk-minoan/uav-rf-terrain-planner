# EXP-20260711-013 - Local Candidate Source-zone Smoke

## Experiment Purpose

Verify that Task 020B local raster classification can supply Task 020C candidate-grid source-zone assignment without committing terrain data or recalculating candidate scores.

## Input Data

Local processed DEM, original ESA WorldCover-derived landcover, and MCEE WMS gap-filled landcover under ignored `METADATA_MAP/`. No local data file is committed.

## Method

A bounded coarse search identified four anonymous representative centers for ESA-derived, WMS gap-filled, DEM-only fallback, and mixed-boundary behavior. The existing candidate-grid generator created a 5x5 grid around each center at 90m spacing. A provider returned `LocalSourceZoneRasterClassifier.sample_point(...).output_source_zone` with a 3-cell neighborhood. Task 020C assigned and summarized the resulting metadata.

## Expected Result

- The local classifier provider is called for every candidate cell.
- All four output source-zone types appear in the bounded smoke assignment.
- DEM-only fallback and mixed-boundary cells are source-sensitive.
- Output contains aggregate counts without coordinates or paths.
- Existing scoring, LOS/Fresnel, route, and waypoint computations are not invoked.

## Actual Result

The assignment completed for 100 candidate cells. All four source-zone types were present: 35 ESA-derived, 25 WMS gap-filled, 25 DEM-only fallback, and 15 mixed-boundary. Sixty-five cells were source-sensitive. CLI output contained aggregate fields only.

## Metrics

- Representative centers: 4
- Candidate grids: 4
- Candidate cells per grid: 25
- Total candidate cells: 100
- ESA-derived: 35
- WMS gap-filled: 25
- DEM-only fallback: 25
- Mixed-boundary: 15
- Source-sensitive: 65
- Dominant zone: `esa_derived`
- Boundary radius: 3 cells
- Result status: passed

## CI / Local Test Result

Local raster-backed smoke passed. Synthetic provider, summary, aggregate formatting, concise error handling, compile, unit-test, lint, type-check, and repository-boundary results are reported in the Task 020D PR. Local rasters are not used in CI.

## Interpretation

The source-zone metadata layers now connect from actual local raster values through candidate-grid records. The smoke confirms metadata plumbing only; the resulting counts do not measure candidate quality or nationwide source-zone proportions.

## Limitations

Representative search is bounded rather than exhaustive. WMS classes remain a styled-RGB heuristic proxy. DEM-only fallback and mixed-boundary radius are model assumptions. No scoring or field outcome is evaluated.

## Figure/Table Candidacy

The aggregate four-zone count table is a paper-table candidate. No coordinate map or raster screenshot is committed.

## Public Repository Sensitivity Check

Only anonymized aggregate results are recorded. No private path, coordinate, raster, CSV, image, PDF, QGIS project, or generated local artifact is included.

## Follow-up Tasks

Apply source-zone metadata to future raster-backed candidate output construction, retain source-sensitive flags in analyses, and test alternative neighborhood radii.
