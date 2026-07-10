# EXP-20260710-005 - Local DEM/DSM Smoke and QGIS Overlay Check

## Experiment Purpose

Verify that the local Task 018A DEM and temporary DSM proxy can pass through the Task 017B GeoTIFF adapter and Task 017A profile extraction path, and record QGIS overlay status.

## Input Data

Local ignored DEM, temporary DSM proxy, surface-delta proxy, and aligned landcover rasters under `METADATA_MAP/`. No raster input is committed.

## Method

Metadata and raster transforms were inspected with rasterio. Three 900m segments were sampled through `LocalGeoTiffTerrainDataAdapter` and `extract_terrain_profile_from_adapter`. One intentional out-of-bounds case was executed. QGIS availability and GUI verification capability were checked separately.

## Expected Result

Aligned rasters should report compatible metadata, valid segments should return terrain profiles, invalid bounds should fail explicitly, and QGIS visual status should be reported without inference.

## Actual Result

All four rasters matched in CRS, square-pixel resolution, dimensions, bounds, and transform. Three valid segments passed with 11 samples each. The bounds case was rejected explicitly. QGIS visual overlay was not run because reliable GUI control and screenshot capture were unavailable.

## Metrics

- CRS: `EPSG:5179`
- Resolution: 90m
- Dimensions: `4057 x 5865`
- Valid segments: 3 of 3
- Samples per segment: 11
- Highest selected-segment DEM: 836.90m MSL
- Highest selected-segment DSM: 850.90m MSL
- Highest selected-segment surface delta: 14.0m
- Bounds rejection: passed
- QGIS visual status: not run

## CI / Local Test Result

Local project verification and GitHub Actions status are recorded in the Task 018B PR after documentation checks complete.

## Interpretation

The selected local rasters are structurally compatible with the adapter and profile workflow. The results demonstrate software-path execution on selected inputs only.

## Limitations

The selected segments are not a representative accuracy sample. The temporary DSM is heuristic. Coastline, NoData boundaries, tile seams, suspicious flat areas, and landcover spatial consistency remain visually unverified.

## Figure/Table Candidacy

The segment summary table is a candidate verification table. No QGIS screenshot is available from this run.

## Public Repository Sensitivity Check

The record uses repository-relative paths and generalized locations only. No local absolute path or GIS data file is included.

## Follow-up Tasks

Complete manual QGIS overlay review and add a separate visual verification record without committing large raster inputs.
