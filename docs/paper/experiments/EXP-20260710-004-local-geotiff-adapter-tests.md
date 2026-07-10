# EXP-20260710-004 - Local GeoTIFF Adapter Tests

## Experiment Purpose

Verify optional GeoTIFF metadata extraction, alignment checks, index conversion, terrain-cell reads, and profile compatibility.

## Input Data

CI tests use fake raster objects only. Real GeoTIFF DEM/DSM files are not committed and are used only for optional local smoke tests.

## Method

Monkeypatched fake raster datasets exercise metadata mismatches, transform checks, row conversion, valid values, NoData, masks, non-finite values, and bounds errors. A separate optional local smoke command uses the ignored Task 018A outputs.

## Expected Result

Fake-raster tests pass without importing rasterio at package import time, and aligned local files can provide an adapter-based terrain profile when available.

## Actual Result

Fake-raster tests passed for metadata, alignment, transform, row conversion, value access, NoData, non-finite values, bounds, metadata safety, and optional import behavior. The local smoke test also produced an 11-sample profile from the ignored Task 018A DEM/DSM files.

## Metrics

Metadata fields, row/column indices, sampled DEM/DSM values, surface delta, profile sample count, and validation error categories.

## CI / Local Test Result

Local verification: 397 tests passed; compileall, Ruff, mypy, and git diff check passed. The optional local GeoTIFF smoke test passed. GitHub Actions status is recorded after push.

## Limitations

The optional smoke test checks software integration and raster alignment only. It does not establish terrain-source accuracy or field performance.

## Public Repository Sensitivity Check

Tests use fake paths and raster objects. No private absolute path or GIS data file is committed.

## Follow-up Tasks

Record QGIS visual review and compare the temporary DSM proxy with more authoritative surface-height data.
