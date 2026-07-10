# EXP-20260710-003 - Terrain Profile Adapter Tests

## Experiment Purpose

Verify adapter-based profile extraction against the existing synthetic direct path.

## Input Data

Synthetic in-memory terrain only.

## Method

Compare sample structures and test default/explicit spacing, metadata grid conversion, bounds errors, and metadata validation calls.

## Expected Result

The adapter path matches direct extraction and rejects invalid inputs with `TerrainProfileError`.

## Actual Result

The direct and adapter extraction paths matched for all compared sample fields. Default and explicit spacing, metadata conversion, bounds errors, and validation invocation behaved as expected.

## Metrics

Sample count, grid indices, distances, DEM MSL, DSM MSL, and surface delta are compared.

## CI / Local Test Result

Local verification: `376 passed`; compileall, Ruff, mypy, and `git diff --check` passed. GitHub Actions status is recorded in the PR after push.

## Limitations

No real DEM/DSM file, GeoTIFF loader, map rendering, network request, or field validation is included.

## Public Repository Sensitivity Check

The test inputs are synthetic and contain no private paths, sensitive coordinates, or large GIS files.

## Follow-up Tasks

Add a separately scoped local GeoTIFF adapter and local-only smoke test after review.
