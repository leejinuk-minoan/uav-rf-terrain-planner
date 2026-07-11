# Task 020D Local Candidate Source-zone Smoke

## Environment

- Windows local execution environment
- Repository base: PR #50 merge commit `5c1ef1e`
- rasterio used only for local runtime access
- Default boundary radius: 3 cells, approximately 270m

## Local raster files checked

- Processed DEM under `METADATA_MAP/DEM_PROCESSED/`
- Original ESA WorldCover-derived landcover under `METADATA_MAP/DSM_PROXY_FROM_ESA_WORLDCOVER/`
- MCEE WMS gap-filled landcover under `METADATA_MAP/DSM_PROXY_GAP_FILLED_FROM_MCEE_WMS_2025/`

The local files were read for smoke verification only and are not committed.

## Smoke script

`examples/local_candidate_source_zone_smoke.py` performs bounded representative search, creates small candidate grids, connects `LocalSourceZoneRasterClassifier` to Task 020C assignment, and prints aggregate counts only. It does not echo file paths or coordinates.

## CandidateCell construction

The script uses `generate_candidate_grid()` and the existing `CandidateCell` dataclass. Four anonymous representative centers are selected for ESA-derived, WMS gap-filled, DEM-only fallback, and mixed-boundary coverage. A 5x5 grid with 90m spacing and radius 2 cells is created around each center, producing 100 smoke cells in total.

Representative search is bounded by a configurable maximum of 5,000 coarse samples. It uses early source-zone collection and limited transition-line inspection rather than a nationwide pixel-by-pixel scan.

## Provider connection

Task 020C receives a provider equivalent to:

```python
classifier.sample_point(
    x_m,
    y_m,
    boundary_radius_cells=boundary_radius_cells,
).output_source_zone
```

The resulting callable is passed to `assign_source_zones_to_candidate_cells()`. No candidate score, LOS/Fresnel value, route score, or waypoint score is recalculated.

## Local smoke result

Local raster-backed candidate source-zone smoke status: **passed**.

- Candidate cells: 100
- Anonymous representative centers: 4
- Grid per center: 5x5
- Grid spacing: 90m
- Grid radius: 2 cells
- Assignment boundary radius: 3 cells
- Coordinates recorded: no

## Source-zone assignment summary

| Output source zone | Candidate count |
|---|---:|
| ESA-derived | 35 |
| WMS gap-filled | 25 |
| DEM-only fallback | 25 |
| Mixed-boundary | 15 |
| Source-sensitive total | 65 |

The dominant output zone was `esa_derived`. The counts describe this bounded smoke grid only and are not nationwide proportions.

## DEM-only fallback handling

Twenty-five candidate cells were assigned `dem_only_fallback`. The model policy is `surface_delta_proxy_m = 0` and DSM proxy equal to DEM. This is an uncovered-input fallback assumption, not evidence that real-world obstacles are absent.

## Mixed-boundary handling

Fifteen candidate cells were assigned `mixed_boundary` because more than one valid base source zone occurred in the 3-cell square neighborhood. These cells are source-sensitive interpretation metadata outputs.

## MGRS external I/O compatibility

This smoke checkpoint is aggregate-only and does not publish candidate, route, waypoint, or map coordinates. It therefore does not conflict with the MGRS external input/output boundary policy.

If future smoke outputs include user-facing coordinates, those fields should be converted to MGRS. Internal projected coordinates and raster row/col values should remain internal/debug or be omitted from user-facing summaries.

## Test result

- Provider callable invocation and expected summary counts: passed
- Aggregate-only CLI formatting: passed
- Expected raster and assignment errors return concise stderr and exit 1: passed
- Direct GIS dependency and prohibited field checks: passed
- Focused smoke-helper tests: passed
- Actual local raster-backed smoke: passed

## Overall status

**passed**.

Task 020B raster classification output was successfully connected to Task 020C candidate assignment for a bounded local smoke set.

## Limitations

- The smoke uses four automatically selected representative areas and is not an exhaustive national evaluation.
- WMS gap-filled landcover remains a styled-RGB heuristic proxy.
- DEM-only fallback and 3-cell mixed-boundary radius are model policies.
- This task assigns interpretation metadata only and does not perform scoring or field validation.

## Public repository sensitivity check

No private absolute path, coordinate, raster, `METADATA_MAP` file, CSV, image, PDF, QGIS project, or generated analysis artifact is committed. CLI output contains aggregate counts only.

## Follow-up tasks

1. Connect source-zone assignment to later raster-backed candidate output construction without changing score semantics.
2. Preserve base-zone details where future records need both base and mixed-boundary output zones.
3. Test source-zone counts across alternative boundary radii and additional bounded scenarios.
4. When future outputs include user-facing coordinates, display MGRS as the default coordinate field.
