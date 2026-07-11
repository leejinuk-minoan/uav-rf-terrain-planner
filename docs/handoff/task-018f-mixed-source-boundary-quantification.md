# Task 018F Mixed-source Boundary Quantification

## Environment

- Windows local execution environment
- Python raster analysis with rasterio, NumPy, and SciPy
- Repository base: PR #46 merge commit `551d36f`
- Analysis intermediates stored only under ignored `.tmp/task-018f/`

## Local raster files checked

- `METADATA_MAP/DEM_PROCESSED/south_korea_dem_90m_epsg5179_alltiles.tif`
- Original ESA WorldCover-derived landcover, surface-delta, and temporary DSM proxy mosaics under `METADATA_MAP/DSM_PROXY_FROM_ESA_WORLDCOVER/`
- MCEE WMS gap-filled landcover, surface-delta, and temporary DSM proxy mosaics under `METADATA_MAP/DSM_PROXY_GAP_FILLED_FROM_MCEE_WMS_2025/`
- Local gap-fill manifest under the same ignored output directory

All seven rasters matched the DEM CRS, dimensions, transform, and bounds: `EPSG:5179`, `4057 x 5865`, and 90m square pixels.

## Boundary definition

- `valid DEM`: finite DEM pixels that are not NoData
- `original ESA`: valid DEM pixels where original landcover is non-zero
- `gap filled`: valid DEM pixels where original landcover is zero and gap-filled landcover is non-zero
- `remaining zero`: valid DEM pixels where gap-filled landcover remains zero; modeled as an `unclassified / no-surface-obstacle fallback`
- `ESA-neighbor zone`: original ESA pixels within an 8-connected square buffer outside the gap-filled mask
- `WMS-filled boundary zone`: gap-filled pixels within the same buffer distance inside the mask

Buffers of 1, 3, and 5 cells were evaluated, corresponding to approximately 90m, 270m, and 450m. The 270m result is used as the primary comparison, while 90m and 450m show sensitivity to boundary width.

## Pixel accounting

| Metric | Count | Valid DEM ratio |
|---|---:|---:|
| Valid DEM | 17,391,989 | 100.000% |
| Original ESA non-zero | 15,398,803 | 88.539% |
| Gap-filled | 1,231,394 | 7.080% |
| Remaining zero | 761,792 | 4.380% |
| Existing non-zero changed | 0 | 0.000% |

The gap-filled count exactly matched the changed-pixel count.

## Boundary buffer metrics

| Buffer | ESA-neighbor pixels | WMS-filled boundary pixels | Combined pixels | Combined area | Share of all gap-filled pixels in WMS boundary zone |
|---|---:|---:|---:|---:|---:|
| 1 cell / 90m | 9,360 | 110,129 | 119,489 | 967.861 km2 | 8.943% |
| 3 cells / 270m | 28,430 | 420,752 | 449,182 | 3,638.374 km2 | 34.169% |
| 5 cells / 450m | 47,587 | 702,030 | 749,617 | 6,071.898 km2 | 57.011% |

The WMS-filled side contains many small class patches and internal edges, so increasing the buffer includes a substantial fraction of all gap-filled pixels.

## Landcover class distribution comparison

Primary 3-cell / 270m comparison:

| Class | ESA-neighbor | WMS-filled boundary | Absolute ratio difference |
|---|---:|---:|---:|
| Tree cover (10) | 74.340% | 27.236% | 47.104 percentage points |
| Grassland (30) | 5.603% | 22.285% | 16.682 percentage points |
| Cropland (40) | 9.314% | 17.924% | 8.610 percentage points |
| Built-up (50) | 5.434% | 20.007% | 14.573 percentage points |
| Bare/sparse vegetation (60) | 0.528% | 7.561% | 7.033 percentage points |
| Permanent water (80) | 4.777% | 4.403% | 0.374 percentage points |
| Herbaceous wetland (90) | 0.004% | 0.584% | 0.580 percentage points |

Total variation distance was `0.523` at 90m, `0.475` at 270m, and `0.451` at 450m. The persistent difference across all widths shows a material source-dependent class discontinuity rather than a narrow one-pixel seam.

## Surface-delta proxy comparison

| Buffer | ESA mean | WMS mean | Mean difference, WMS - ESA | ESA median | WMS median | Median difference |
|---|---:|---:|---:|---:|---:|---:|
| 90m | 9.438m | 5.242m | -4.196m | 14.0m | 1.0m | -13.0m |
| 270m | 9.453m | 5.729m | -3.724m | 14.0m | 1.0m | -13.0m |
| 450m | 9.478m | 5.932m | -3.547m | 14.0m | 1.0m | -13.0m |

At the primary 270m buffer, ESA-neighbor surface delta had min/max `0/14m`, standard deviation `6.296m`, and p05/p25/p50/p75/p95 of `0/0.5/14/14/14m`. WMS-filled boundary values had min/max `0/14m`, standard deviation `5.800m`, and quantiles `0/0.5/1/14/14m`.

The lower WMS median follows its higher grassland, cropland, built-up, and bare/sparse shares and much lower tree-cover share. It should not be interpreted as measured obstacle-height accuracy.

## Temporary DSM proxy comparison

| Buffer | ESA mean | WMS mean | Mean difference, WMS - ESA | ESA median | WMS median | Median difference |
|---|---:|---:|---:|---:|---:|---:|
| 90m | 365.570m | 206.574m | -158.996m | 292.897m | 109.010m | -183.887m |
| 270m | 363.586m | 228.732m | -134.854m | 288.234m | 136.554m | -151.679m |
| 450m | 362.816m | 253.995m | -108.821m | 289.367m | 167.261m | -122.106m |

At 270m, ESA-neighbor DSM p05/p25/p50/p75/p95 were `4.396/147.569/288.234/555.238/898.107m`; WMS-filled boundary values were `6.425/55.102/136.554/317.149/782.127m`.

DSM differences are strongly confounded by underlying DEM elevation and the geographic placement of the gap-filled strips. Surface-delta differences are therefore the more direct mixed-source diagnostic.

## Existing non-zero preservation check

Existing non-zero landcover pixels changed: **0**. The 1,231,394 changed pixels were all original-zero, valid-DEM pixels that received a non-zero WMS-derived proxy class. Status: **passed**.

## Remaining zero-pixel interpretation

After gap fill, 761,792 valid-DEM pixels remained zero, or 4.380% of valid DEM coverage. These pixels use the following model fallback policy:

- landcover class: `unclassified / no-surface-obstacle fallback`
- `surface_delta_proxy_m = 0`
- `temporary_dsm_proxy_m = DEM_msl`

Candidate scoring and route evaluation therefore treat remaining-zero cells as `DSM proxy = DEM`. This is an obstacle-free fallback assumption for uncovered input cells, not evidence that real-world obstacles are absent. The policy is user-defined and is not based on measured obstacle-height verification.

## Interpretation for candidate scoring

- The 7.080% gap-filled share is large enough to affect nationwide aggregate analysis.
- Class TVD of `0.451-0.523` indicates substantial source-dependent class composition near the boundary.
- WMS-filled boundary surface delta was lower by `3.547-4.196m` in mean and `13m` in median, which can reduce DSM obstacle proxy values relative to neighboring ESA-derived cells.
- Candidate scores or route comparisons that cross or lie near mixed-source boundaries should be flagged as source-sensitive.
- Candidate scoring and route evaluation use the surface-delta zero fallback for remaining-zero valid DEM cells; results involving those cells should be flagged as fallback-dependent.
- Paper experiments should stratify ESA-only, WMS-filled, and boundary-intersecting cases or run a sensitivity analysis rather than pool them without qualification.
- These metrics quantify preprocessing discontinuity only; they do not validate field outcomes.

## Overall status

**partial**.

The mixed-source effect was quantified successfully and raster preservation checks passed. The measured class and surface-delta discontinuities remain large enough to require explicit interpretation limits and follow-up sensitivity analysis.

## Limitations

- MCEE WMS input is a styled RGB map image classified through a heuristic proxy, not an authoritative source class raster.
- ESA WorldCover 2021 and MCEE WMS 2025 differ in source date, classification, and likely effective resolution.
- The paired boundary zones contain unequal pixel counts because of mask geometry and fragmented WMS class patches.
- The square 8-connected buffer is a raster proximity definition, not a physical feature boundary.
- DSM distribution differences include DEM elevation and geographic-placement effects.
- No measured obstacle height or field data was used.
- The remaining-zero obstacle-free fallback is a modeling policy, not a data-derived statement about actual obstacle presence.

## Public repository sensitivity check

Only repository-relative input descriptions and aggregate statistics are recorded. No private absolute path, coordinate, raster, CSV, image, PDF, QGIS project, or temporary analysis script is committed.

## Follow-up tasks

1. Add source-zone flags to future candidate and route experiment datasets.
2. Run candidate-score sensitivity analysis with ESA-only, WMS-filled, and boundary-intersecting strata.
3. Replace styled WMS RGB classification if authoritative source class data becomes available.
4. Run sensitivity analysis comparing the remaining-zero surface-delta zero fallback with alternative conservative fallback values.
