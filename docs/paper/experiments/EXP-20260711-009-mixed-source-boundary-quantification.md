# EXP-20260711-009 - Mixed-source Boundary Quantification

## Experiment Purpose

Quantify the preprocessing discontinuity between existing ESA WorldCover-derived terrain proxy coverage and the MCEE WMS-derived gap-filled area identified in Tasks 018D and 018E.

## Input Data

Seven aligned local rasters under ignored `METADATA_MAP/`: DEM; original landcover, surface delta, and temporary DSM proxy; and gap-filled landcover, surface delta, and temporary DSM proxy. The local gap-fill manifest was checked for context. No data file is committed.

## Method

A valid DEM mask excluded NoData and non-finite values. Original ESA pixels had non-zero original landcover. Gap-filled pixels had zero original landcover and non-zero corrected landcover. Remaining-zero pixels retained zero corrected landcover. For 1-, 3-, and 5-cell square buffers, the experiment compared original ESA pixels immediately outside the gap-filled mask with WMS-filled pixels immediately inside it. Class distributions were compared using total variation distance. Surface-delta and temporary DSM statistics included count, range, mean, median, standard deviation, and p05/p25/p50/p75/p95.

## Expected Result

The analysis should preserve all existing non-zero landcover values, quantify the fraction and boundary scale of WMS-filled pixels, and disclose any class or surface-height discontinuity without assuming that either source is ground truth.

## Actual Result

All rasters matched `EPSG:5179`, `4057 x 5865`, 90m resolution, transform, and bounds. Gap-filled pixels represented 7.080% of valid DEM pixels, while 4.380% remained zero. Existing non-zero changes were zero.

Boundary class TVD remained high across buffer widths: `0.523` at 90m, `0.475` at 270m, and `0.451` at 450m. At the primary 270m width, tree cover was 74.340% in ESA-neighbor pixels and 27.236% in WMS-filled boundary pixels. WMS-filled surface delta was `3.724m` lower in mean and `13m` lower in median. Overall status: **partial**.

## Metrics

- Valid DEM pixels: 17,391,989
- Original ESA non-zero pixels: 15,398,803
- Gap-filled pixels: 1,231,394, or 7.080%
- Remaining-zero pixels: 761,792, or 4.380%
- Existing non-zero landcover changed: 0
- Combined boundary pixels at 90/270/450m: 119,489 / 449,182 / 749,617
- Combined boundary area at 90/270/450m: 967.861 / 3,638.374 / 6,071.898 km2
- Class TVD at 90/270/450m: 0.523 / 0.475 / 0.451
- Surface-delta mean difference at 90/270/450m: -4.196 / -3.724 / -3.547m
- Surface-delta median difference at all widths: -13m
- Temporary DSM mean difference at 90/270/450m: -158.996 / -134.854 / -108.821m

## CI / Local Test Result

Local raster quantification completed. Repository compile, unit tests, lint, type checking, diff checks, and prohibited-file/path/wording checks are recorded in the Task 018F PR. Local raster inputs and temporary analysis outputs are not part of CI.

## Interpretation

The gap fill preserved existing classified pixels but introduced a material mixed-source distribution boundary. The surface-delta difference is the most direct proxy impact; temporary DSM differences also reflect terrain elevation and geographic placement. Candidate-scoring experiments should identify source zones and treat boundary-intersecting results as source-sensitive.

## Limitations

The WMS classification is a heuristic interpretation of styled RGB imagery. Neither source is treated as ground truth. Source date and classification differences, unequal boundary-zone sample sizes, fragmented gap geometry, and DEM confounding limit causal interpretation of the DSM statistics.

## Figure/Table Candidacy

The pixel-accounting table, class-ratio comparison, buffer-width TVD table, and surface-delta summary are paper-table candidates. A boundary-zone map would require separate sanitization and approval; no image is committed in this task.

## Public Repository Sensitivity Check

Only aggregate metrics and repository-relative input descriptions are included. No raster, CSV, image, PDF, QGIS project, temporary script, private path, or coordinate is committed.

## Follow-up Tasks

Stratify future candidate-score experiments by source zone, quantify score sensitivity near mixed-source boundaries, classify remaining-zero causes, and replace the styled WMS proxy if authoritative source class data becomes available.
