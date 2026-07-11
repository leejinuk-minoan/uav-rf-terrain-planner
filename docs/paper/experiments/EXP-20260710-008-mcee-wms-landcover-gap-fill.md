# EXP-20260710-008 - MCEE WMS Landcover Gap Fill

## Experiment Purpose

Evaluate whether a public, georeferenced landcover WMS can fill the rectangular and cross-shaped proxy coverage gaps identified in Task 018D without changing existing non-zero landcover cells or breaking DEM grid alignment.

## Input Data

- Local processed DEM mosaic and DEM source tiles under ignored `METADATA_MAP/`
- Existing ESA WorldCover-derived landcover, surface-delta, and temporary DSM proxy mosaics
- Public MCEE WMS layer `EGIS:lv3_2025y`

No raster, rendered image, PDF, QGIS project, or local manifest is committed.

## Method

The WMS was requested in `EPSG:3857` for 39 unique candidate tiles. Each rendered RGB response was georeferenced from its requested bounding box and reprojected with nearest-neighbor resampling to the corresponding `EPSG:5179`, 90m DEM grid. White WMS background pixels were treated as NoData. A heuristic RGB classifier mapped the styled image to coarse proxy classes, which were normalized to the existing ESA WorldCover code scheme. Only cells with existing landcover code `0`, valid DEM, and a non-zero WMS proxy class were updated. Surface delta and temporary DSM were recalculated only for those cells.

## Expected Result

- Remove the central rectangular/cross-shaped landcover gap.
- Preserve every existing non-zero landcover cell.
- Preserve DEM CRS, dimensions, transform, and bounds.
- Maintain `temporary DSM MSL = DEM MSL + surface delta proxy` at every changed cell.
- Avoid treating WMS background as built-up landcover.

## Actual Result

The central cross-shaped gap was filled in the inspected landcover, surface-delta, and DSM proxy layers. A total of 1,231,394 pixels were updated. No existing non-zero landcover pixel changed. The corrected rasters remained aligned with the DEM, and the maximum absolute DSM formula error at changed pixels was `0.0 m`.

QGIS confirmed loading and spatial alignment without systematic offset. Mixed-source visual boundaries remain between ESA WorldCover 2021 coverage and MCEE WMS 2025 gap-fill areas. Overall status: **partial**.

## Metrics

- Candidate WMS tiles: 39 unique tiles
- Corrected pixels: 1,231,394
- Valid-DEM landcover zero pixels before: 1,993,186
- Valid-DEM landcover zero pixels after: 761,792
- Existing non-zero landcover pixels changed: 0
- CRS: `EPSG:5179`
- Dimensions: `4057 x 5865`
- DEM transform and bounds match: passed
- Maximum absolute DSM formula error: `0.0 m`
- Systematic QGIS offset observed: no
- Overall QGIS overlay status: partial

## CI / Local Test Result

The WMS download, reprojection, raster checks, and QGIS rendering were local-only. Repository compile, test, lint, type-check, diff, sensitivity, and prohibited-file checks are reported in the PR verification record.

## Interpretation

Georeferenced WMS reprojection is more reproducible and spatially defensible than manually georeferencing the downloaded map-layout PDFs. The result repairs the major coverage gap for simulation use, but it does not create an authoritative nationwide landcover raster. Styled RGB classification and mixed-source boundaries remain important limitations.

## Limitations

- The WMS is a styled map image rather than source class values.
- RGB-to-class conversion is heuristic.
- ESA WorldCover 2021 and MCEE WMS 2025 differ in acquisition time, classification system, and likely source resolution.
- Remaining zero cells include outer coverage, water-adjacent, and unclassified WMS areas that were not exhaustively categorized.
- The temporary DSM is not measured building or canopy height.

## Figure/Table Candidacy

A sanitized before/after coverage figure and a pixel-accounting table may be candidates after separate approval. Local verification PNG files are not committed.

## Public Repository Sensitivity Check

Only repository-relative paths and aggregate metrics are recorded. No private absolute path, raster, image, PDF, QGIS project, or sensitive coordinate is included.

## Follow-up Tasks

Quantify mixed-source boundary effects, obtain authoritative source class data where possible, and manage any reproducible processing script under a separate Task.
