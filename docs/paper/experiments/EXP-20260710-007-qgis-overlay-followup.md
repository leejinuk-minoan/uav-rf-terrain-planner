# EXP-20260710-007 - QGIS Overlay Follow-up Verification

## Experiment Purpose

Complete the QGIS comparisons left open by EXP-20260710-006 using distinct symbology, transparency, layer toggling, and representative multi-zoom inspection.

## Input Data

Four ignored local rasters under `METADATA_MAP/`: processed DEM, temporary DSM proxy, surface-delta proxy, and aligned landcover. No raster is committed.

## Method

QGIS 3.40.14 LTR loaded all four rasters under `EPSG:5179`. Pseudocolor renderers and opacity were applied, and each layer was rendered separately and together at a nationwide overview plus coastal/island, inland high-relief, and rectangular-boundary extents. Sixteen evidence PNGs were generated under ignored `.tmp/task-018d/` and visually compared.

## Expected Result

All layers should remain spatially colocated across zoom levels. Layer isolation should distinguish grid displacement from NoData, source coverage, or proxy-processing artifacts.

## Actual Result

QGIS overlay status: **partial**.

All four layers loaded and rendered. Coastline, island, relief, drainage, landcover, and surface-delta patterns were colocated in valid covered areas, with no visible systematic grid offset. At the boundary extent, DEM and DSM remained continuous while landcover and surface delta showed prominent rectangular and cross-shaped missing-coverage strips. The observed blocks are therefore localized to proxy source coverage rather than DEM/DSM grid displacement. Remaining zero or flat-cell semantics were not fully classified.

## Metrics

- Raster layers loaded: 4 of 4
- Project and layer CRS: `EPSG:5179`
- Representative zoom extents: 3
- Render configurations: 16
- Systematic spatial offset observed: no
- Proxy layers with rectangular coverage gaps: 2 of 2 inspected derived inputs (`landcover`, `surface delta`)
- Local screenshots generated: yes
- Screenshot files committed: no

## CI / Local Test Result

Repository compile, test, lint, type-check, and diff checks are recorded in the Task 018D PR after execution. QGIS visual verification is local-only and is not part of GitHub Actions.

## Interpretation

The follow-up supports the raster grid-alignment assumption in the inspected valid areas. It does not support a complete nationwide proxy-coverage claim. The landcover and surface-delta coverage gaps should be quantified and repaired or explicitly masked before further terrain-loader or paper-result use.

## Limitations

This is a visual verification of selected extents, not an exhaustive pixel-level audit. The DSM is a heuristic landcover proxy rather than authoritative measured surface height, and the review does not validate field outcomes.

## Figure/Table Candidacy

The local comparison renders are verification evidence only and are not committed. A sanitized boundary comparison could become a limitations figure after the coverage issue is resolved and separately approved.

## Public Repository Sensitivity Check

No screenshot, image, QGIS project, private absolute path, sensitive coordinate, or raster file is included.

## Follow-up Tasks

Quantify missing landcover coverage by source tile, rebuild or mask affected proxy outputs, and repeat the same boundary comparison before claiming nationwide DSM-proxy completeness.
