# Task 018D-Local QGIS Overlay Follow-up Verification

## Environment

- Windows local execution environment
- QGIS 3.40.14 LTR
- Repository base: PR #45 merge commit `27b8ea2`
- Local evidence directory: ignored `.tmp/task-018d/`

## Local raster files checked

The following ignored local rasters under `METADATA_MAP/` were loaded without committing them:

- Processed DEM mosaic
- Temporary DSM proxy mosaic
- Surface-delta proxy mosaic
- Aligned landcover mosaic

All four layers loaded in QGIS with known `EPSG:5179` CRS. Distinct pseudocolor renderers and opacity were applied so the layers could be toggled and compared. Status: passed.

## Follow-up method

QGIS map rendering was exercised with one nationwide overview and three representative zoom extents: a coastal/island area, an inland high-relief area, and an area crossing conspicuous rectangular source boundaries. Each extent was rendered with DEM, DSM, surface delta, and landcover visibility isolated, followed by a combined overlay. This produced 16 local PNG evidence files in the ignored temporary directory. No image or QGIS project is committed.

## Results

| Check | Result | Observation |
|---|---|---|
| Layer loading and CRS | passed | Four of four layers rendered under `EPSG:5179`. |
| Distinct symbology, opacity, and toggling | passed | DEM, DSM, surface delta, and landcover were distinguishable in isolated and combined renders. |
| Nationwide footprint | passed | The four rasters occupy the expected common South Korea processing extent. |
| Coastal and island alignment | passed | Coastline and island features were colocated where proxy coverage was valid. |
| Inland high-relief alignment | passed | Relief, drainage patterns, landcover, and derived surface delta showed no visible spatial offset. |
| Multi-zoom grid alignment | passed | No half-cell or systematic layer displacement was visible in the three inspected extents. |
| Rectangular boundary classification | partial | DEM and DSM remain continuous across the inspected boundary, while landcover and surface-delta overlays contain rectangular and cross-shaped missing-coverage strips. These are proxy source-sheet coverage gaps, not a DEM/DSM grid displacement. |
| Suspicious zero or flat areas | partial | The visual review separates proxy coverage gaps from terrain relief, but it does not establish whether every zero or flat source cell is valid terrain, water, or missing source data. |
| Landcover-to-DSM relationship | partial | Covered areas align visually and the surface-delta pattern follows landcover classes, but the landcover coverage gaps prevent a nationwide passed verdict. |

## Overall status

QGIS overlay status: **partial**.

The follow-up closes the prior uncertainty about layer toggling, symbology, representative zoom checks, and systematic grid displacement. It also localizes the prominent rectangular artifacts to missing coverage in the landcover and surface-delta proxy layers. The proxy mosaic must be repaired or explicitly masked before it is treated as complete nationwide DSM-support coverage.

## Limitations and next action

- The temporary DSM is a landcover-derived heuristic proxy, not measured building height or canopy height.
- This visual review does not establish source accuracy, communication availability, flight feasibility, or field outcomes.
- Quantify missing proxy coverage by source tile, repair or mask the gaps, rebuild the affected derived rasters, and repeat the same boundary renders.
- Retain the local screenshots only as uncommitted verification evidence unless a separately sanitized figure is approved.

## Public repository sensitivity check

No private absolute path, sensitive coordinate, screenshot, QGIS project, or GIS raster is committed. Only repository-relative dataset descriptions are recorded.
