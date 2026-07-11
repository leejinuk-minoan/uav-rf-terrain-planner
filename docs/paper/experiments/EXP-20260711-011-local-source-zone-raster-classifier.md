# EXP-20260711-011 - Local Source-zone Raster Classifier

## Experiment Purpose

Verify that aligned local DEM and landcover rasters produce Task 020A-compatible ESA-derived, WMS gap-filled, DEM-only fallback, and mixed-boundary metadata.

## Input Data

Local processed DEM, original ESA WorldCover-derived landcover, and MCEE WMS gap-filled landcover under ignored `METADATA_MAP/`. Gap-filled surface-delta and temporary DSM proxy rasters were checked for fallback consistency. No local data file is committed.

## Method

The classifier validated raster CRS, transform, bounds, width, and height. A pure scalar rule classified each valid center cell. A clipped 8-connected square neighborhood with default radius 3 cells identified multiple valid base zones. Invalid DEM neighbors were excluded. Four representative cells were selected automatically without recording coordinates.

## Expected Result

- ESA interior remains `esa_derived`.
- WMS interior remains `wms_gap_filled`.
- Remaining-zero valid DEM becomes `dem_only_fallback`.
- A center near more than one valid base zone becomes `mixed_boundary`.
- DEM-only fallback uses surface-delta zero and temporary DSM equal to DEM.
- Output remains compatible with Task 020A records.

## Actual Result

All four representative samples matched their expected base and output zones. The mixed sample retained a WMS base zone and returned `mixed_boundary`. The fallback sample had zero surface delta and temporary DSM equal to DEM. Required rasters were aligned under `EPSG:5179` at 90m resolution.

## Metrics

- Representative samples: 4
- Expected classifications matched: 4 of 4
- ESA sample source-sensitive: no
- WMS, fallback, and mixed samples source-sensitive: yes
- Default boundary radius: 3 cells, approximately 270m
- DEM-only fallback surface delta: `0m`
- DEM-only fallback DSM minus DEM: `0m`
- Raster alignment checks: passed
- Expected CLI error handling: concise stderr, exit 1, no traceback

## CI / Local Test Result

Local raster smoke passed. Pure helper, neighborhood, alignment, summary, field-boundary, compile, unit-test, lint, and type-check results are recorded in the Task 020B PR. Actual local rasters are not used by CI.

## Interpretation

Task 020A source-zone metadata can now be derived from aligned local raster values. Keeping base and output zones separate preserves the center-cell source while allowing a mixed-boundary flag to inform later analysis.

## Limitations

The WMS source remains a styled-RGB heuristic proxy. DEM-only fallback is a model assumption rather than obstacle-absence evidence. The 3-cell square neighborhood is policy-driven, and full raster-backed candidate scoring is outside this task.

## Figure/Table Candidacy

The four anonymized sample outcomes and decision-rule table are paper-table candidates. No raster screenshot or map is committed.

## Public Repository Sensitivity Check

Only aggregate and anonymized results are included. No private path, coordinate, raster, CSV, image, PDF, QGIS project, or temporary analysis file is committed.

## Follow-up Tasks

Integrate output zones with raster-backed candidate construction, preserve base-zone metadata where schemas allow, and test score sensitivity across neighborhood radii and source zones.
