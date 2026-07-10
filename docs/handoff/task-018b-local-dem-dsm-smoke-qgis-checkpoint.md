# Task 018B Local DEM/DSM Smoke and QGIS Checkpoint

## Environment

- Windows local execution environment
- Python and rasterio available
- QGIS 3.40.14 installation detected
- Repository base: Task 018B-Cloud merge commit `2f127c6`

## Local files checked

Required and optional files were present under repository-relative `METADATA_MAP/` paths:

- DEM processed mosaic
- Temporary DSM proxy mosaic
- Surface-delta proxy mosaic
- Aligned landcover mosaic

No local raster file is included in this change.

## Metadata validation result

All four rasters reported `EPSG:5179`, 90m square pixels, size `4057 x 5865`, and bounds `(838710, 1555740, 1203840, 2083590)`.

- DEM NoData: `-9999`
- Temporary DSM proxy NoData: `-9999`
- Surface-delta proxy NoData: `-9999`
- Landcover NoData: `0`
- Status: passed

## DEM/DSM pair result

DEM and temporary DSM proxy matched in CRS, resolution, width, height, bounds, transform, and NoData convention. Both use the documented MSL height convention. Status: passed.

## Smoke test commands

The repository smoke example was run with repository-relative DEM/DSM arguments on three short 900m east-west segments. Public reporting uses generalized coordinate labels rather than private paths or operational locations.

## Smoke test results

| Label | Generalized location | Spacing | Samples | Max DEM MSL | Max DSM MSL | Max delta | Status |
|---|---|---:|---:|---:|---:|---:|---|
| Segment A | x about 1,028km, y about 2,075km | 90m | 11 | 836.90m | 850.90m | 14.0m | passed |
| Segment B | x about 1,005km, y about 2,030km | 90m | 11 | 317.73m | 328.03m | 14.0m | passed |
| Segment C | x about 983km, y about 2,052km | 90m | 11 | 381.35m | 381.85m | 0.5m | passed |

The highest values observed across these selected segments were DEM 836.90m MSL, DSM 850.90m MSL, and surface delta 14.0m. These selected software-path samples do not establish nationwide terrain accuracy.

## NoData or bounds case result

An intentional start point outside the western metadata bound was rejected with `TerrainProfileError`: `ix is outside the terrain metadata bounds.` Bounds handling status: passed.

The CLI example currently exposes the traceback for this profile-level bounds error because it formats `TerrainDataError` only. A concise CLI error message is a follow-up usability item; the underlying bounds rejection is explicit.

## QGIS overlay result

Status: not run.

QGIS 3.40.14 was detected, but reliable GUI control and screenshot capture were unavailable in this execution context. No visual claim is made. Numerical checks confirmed identical CRS, dimensions, bounds, and transforms for DEM, DSM proxy, surface delta, and landcover, but coastline, tile seams, zero-elevation areas, and landcover visual consistency still need manual QGIS review.

## Limitations

- The temporary DSM is derived from landcover-class height assumptions and is not measured building or vegetation height.
- Smoke tests cover three selected segments and one bounds case only.
- Numerical raster alignment is not a substitute for QGIS visual overlay review.
- No terrain-source accuracy or field outcome was validated.

## Public repository sensitivity check

Only repository-relative paths and generalized test locations are recorded. No private absolute path, credential, sensitive coordinate, or GIS raster is committed.

## Follow-up tasks

1. Perform manual QGIS overlay review of coastline, NoData boundaries, tile seams, and landcover alignment.
2. Improve the smoke example to format `TerrainProfileError` without a traceback.
3. Compare the temporary DSM proxy with authoritative building-height and vegetation-height data when available.
