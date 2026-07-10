# Task 018B - Local DEM/DSM Smoke Test and QGIS Overlay Verification Protocol

## 1. Task purpose

This protocol prepares the next local verification step after Task 017B. It defines the smoke-test and QGIS overlay checks that a Local Execution Agent should perform with user-prepared DEM/DSM files.

This Cloud task does not open local terrain files, run raster tooling, run QGIS, or validate local data. It only prepares documentation for the local step.

## 2. Current prerequisite status

- Task 017B has been merged into `main` through PR #41.
- `LocalGeoTiffTerrainDataAdapter` is available in `src/uav_rf_terrain/geotiff_terrain_data.py`.
- `examples/local_geotiff_adapter_smoke.py` is available.
- The DEM checkpoint records a processed EPSG:5179 90m DEM output under `METADATA_MAP/DEM_PROCESSED/`.
- The ESA WorldCover checkpoint records a temporary DSM proxy, surface-delta proxy, and aligned landcover raster under `METADATA_MAP/DSM_PROXY_FROM_ESA_WORLDCOVER/`.

## 3. Local input files expected

Required local files:

```text
METADATA_MAP/DEM_PROCESSED/south_korea_dem_90m_epsg5179_alltiles.tif
METADATA_MAP/DSM_PROXY_FROM_ESA_WORLDCOVER/south_korea_temporary_dsm_proxy_90m_epsg5179.tif
```

Optional local files:

```text
METADATA_MAP/DSM_PROXY_FROM_ESA_WORLDCOVER/south_korea_landcover_90m_epsg5179.tif
METADATA_MAP/DSM_PROXY_FROM_ESA_WORLDCOVER/south_korea_surface_delta_proxy_90m_epsg5179.tif
```

These files are local working files only and must not be committed.

## 4. Smoke test protocol

### 4.1 Metadata validation

Record for DEM and DSM:

- CRS.
- Pixel resolution.
- Width and height.
- Bounds.
- NoData value.
- Vertical datum or height convention, if documented.
- Pass/fail status.

### 4.2 DEM/DSM pair check

Confirm whether DEM and DSM have matching or documented-compatible:

- CRS.
- Resolution.
- Bounds.
- Width and height.
- NoData convention.
- Vertical datum or height convention.

If this check fails, stop the smoke test and record the mismatch.

### 4.3 Profile extraction samples

Run `examples/local_geotiff_adapter_smoke.py` on several short coordinate segments inside valid raster areas.

For each sample, record:

- Sanitized sample label.
- Generalized start/end coordinates suitable for public documentation.
- Sample spacing.
- Profile sample count.
- Maximum DEM MSL.
- Maximum DSM MSL.
- Maximum surface delta.
- Pass/fail status.
- Error category, if failed.

### 4.4 NoData handling check

Run at least one intentional edge or missing-data case if a safe NoData area is known.

Record whether the case fails cleanly and whether the error category is NoData, mask, non-finite value, or bounds.

### 4.5 Profile summary

Summarize:

- Profile sample count per segment.
- Highest DEM MSL observed in smoke-test segments.
- Highest DSM MSL observed in smoke-test segments.
- Highest surface delta observed in smoke-test segments.
- Any suspicious zero-elevation or flat areas requiring follow-up.

## 5. QGIS overlay verification protocol

Load the available local raster layers:

1. DEM.
2. DSM proxy.
3. Surface delta proxy, if present.
4. Aligned landcover raster, if present.

Check and record:

- Loaded layers report CRS `EPSG:5179`.
- DEM and DSM proxy extents align.
- Raster grids appear aligned at multiple zoom levels.
- Coastline or NoData boundaries appear consistent across layers.
- Tile seam artifacts are absent or documented.
- Suspicious zero-elevation areas are absent or documented.
- Landcover appears spatially aligned with the DSM proxy, if loaded.
- Visual check status is one of: `passed`, `failed`, or `needs manual follow-up`.

If QGIS cannot be run, record `not run` and explain the environment limitation.

## 6. Reporting template

The Local Execution Agent should write:

```text
docs/handoff/task-018b-local-dem-dsm-smoke-qgis-checkpoint.md
docs/paper/experiments/EXP-20260710-005-local-dem-dsm-smoke-qgis.md
```

Checkpoint headings:

```markdown
# Task 018B Local DEM/DSM Smoke and QGIS Checkpoint

## Environment
## Local files checked
## Metadata validation result
## DEM/DSM pair result
## Smoke test commands
## Smoke test results
## NoData or bounds case result
## QGIS overlay result
## Limitations
## Public repository sensitivity check
## Follow-up tasks
```

Experiment headings:

```markdown
# EXP-20260710-005 - Local DEM/DSM Smoke and QGIS Overlay Check

## Experiment Purpose
## Input Data
## Method
## Expected Result
## Actual Result
## Metrics
## CI / Local Test Result
## Interpretation
## Limitations
## Figure/Table Candidacy
## Public Repository Sensitivity Check
## Follow-up Tasks
```

## 7. Limitations

- ESA WorldCover DSM is a temporary proxy derived from landcover classes and heuristic surface-height assumptions.
- The DSM proxy is not an authoritative building-height or vegetation-height dataset.
- QGIS overlay review is a visual alignment check only.
- Smoke-test success confirms only that the adapter path runs on selected local files.
- This protocol is not an operational validation and does not provide field-outcome assurance.

## 8. Public repository sensitivity check

Do not record:

- Private absolute paths.
- Sensitive coordinates.
- Credentials, tokens, or secrets.
- Local account identifiers.
- GIS raster files.
- `METADATA_MAP` data files.

Use repository-relative paths and sanitized sample labels in public reports.

## 9. Follow-up tasks

- Local Execution Agent performs the smoke test and QGIS overlay review.
- Local Execution Agent records the checkpoint and experiment record.
- GPT Master reviews whether the temporary DSM proxy is sufficient for the next integration step.
- If needed, prepare a later task for more authoritative surface-height data.
- Keep real terrain files outside Git unless a separate data-policy review approves a small redistributable processed fixture.
