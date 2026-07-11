# Task 020B Local Source-zone Raster Classifier

## Environment

- Windows local execution environment
- Python 3.11-compatible package implementation
- rasterio used only as an optional local runtime import
- Repository base: PR #48 merge commit `7a28205`

## Local raster files checked

- Processed DEM under `METADATA_MAP/DEM_PROCESSED/`
- Original ESA WorldCover-derived landcover under `METADATA_MAP/DSM_PROXY_FROM_ESA_WORLDCOVER/`
- MCEE WMS gap-filled landcover under `METADATA_MAP/DSM_PROXY_GAP_FILLED_FROM_MCEE_WMS_2025/`
- Gap-filled surface-delta and temporary DSM proxy for fallback consistency checking

The required rasters matched `EPSG:5179`, dimensions, transform, bounds, and 90m grid alignment. No local raster is committed.

## Classifier implementation

`source_zone_raster.py` adds `SourceZoneRasterError`, sample and summary dataclasses, pure scalar and neighborhood helpers, and `LocalSourceZoneRasterClassifier`. The classifier imports rasterio lazily and validates CRS, transform, bounds, width, and height before reading points.

## Source-zone decision rules

| DEM | Original landcover | Gap-filled landcover | Base zone |
|---|---:|---:|---|
| Invalid or NoData | any | any | explicit `SourceZoneRasterError` |
| Valid | non-zero | any | `ESA_DERIVED` |
| Valid | zero | non-zero | `WMS_GAP_FILLED` |
| Valid | zero | zero | `DEM_ONLY_FALLBACK` |

Landcover NaN and infinite values raise an explicit error. Zero codes are read as policy inputs even though zero is also landcover NoData metadata.

## Boundary neighborhood rule

- Default radius: 3 cells, approximately 270m at 90m resolution
- Neighborhood: 8-connected square window
- Radius zero: output equals base zone
- Raster edges: clipped to valid raster bounds
- Invalid DEM neighbors: excluded
- Two or more valid base-zone types: `MIXED_BOUNDARY`

Each sample retains both `base_source_zone` and boundary-aware `output_source_zone`.

## Local smoke sample result

| Sample | Expected type | Base zone | Output zone | Source-sensitive | Result |
|---|---|---|---|---|---|
| A | ESA-derived interior | `esa_derived` | `esa_derived` | no | passed |
| B | WMS-filled interior | `wms_gap_filled` | `wms_gap_filled` | yes | passed |
| C | DEM-only fallback interior | `dem_only_fallback` | `dem_only_fallback` | yes | passed |
| D | Mixed boundary | `wms_gap_filled` | `mixed_boundary` | yes | passed |

Samples were selected automatically from eligible local raster cells. Coordinates are intentionally not recorded.

## DEM-only fallback handling

For Sample C, optional consistency rasters confirmed `surface_delta_proxy_m = 0` and `temporary_dsm_proxy_m = DEM_msl`. This is a model fallback assumption for uncovered input cells, not evidence that real-world surface obstacles are absent.

## Mixed-boundary handling

Sample D retained its WMS base zone and returned `mixed_boundary` because another valid base-zone type was present in the 3-cell neighborhood. The output is source-sensitive and can be passed directly to Task 020A records.

## Integration with Task 020A output scaffold

The classifier reuses `TerrainSourceZone`, `summarize_source_zones`, and `is_source_sensitive_zone`. Its output is the enum already accepted by candidate, route, waypoint, scenario, and map-ready records. Full candidate-grid scoring integration is deferred.

## Test result

- Scalar decision and finite-value rules: passed
- ESA/WMS/fallback neighborhood behavior: passed
- Invalid DEM neighbor exclusion and radius-zero behavior: passed
- Task 020A summary reuse and raster alignment validation: passed
- Prohibited operational field check: passed
- Local four-type raster smoke: passed
- Smoke CLI expected-error handling: exit 1 with concise stderr and no traceback

## Overall status

**passed**.

The classifier maps aligned local raster cells to the Task 020A source-zone scaffold and preserves base/output distinction at mixed boundaries.

## Limitations

- rasterio is required for local runtime sampling but remains outside package dependencies.
- WMS gap-filled classes remain a styled-RGB heuristic proxy.
- Boundary radius 3 is a model policy and should be included in sensitivity analysis.
- The classifier provides source metadata only and does not complete candidate-grid scoring integration.
- Source-zone labels do not establish terrain or obstacle-height accuracy.

## Public repository sensitivity check

No private absolute path, sample coordinate, raster, `METADATA_MAP` file, CSV, image, PDF, QGIS project, or temporary analysis artifact is committed.

## Follow-up tasks

1. Connect classifier output to future raster-backed candidate-grid construction.
2. Propagate base and output zones together where schemas permit both.
3. Compare candidate results across boundary radii and source-zone strata.
4. Replace styled WMS classification if authoritative source class data becomes available.
