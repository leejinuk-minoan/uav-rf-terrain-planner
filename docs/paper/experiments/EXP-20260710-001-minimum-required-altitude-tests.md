# EXP-20260710-001 - Minimum Required Altitude Tests

## Date

2026-07-10

## Related Task / Issue / PR

- Task: 015 - Minimum Required Altitude Model Scaffold
- Issue: none
- PR: #35

## Experiment Purpose

Validate the Task 015 minimum required altitude scaffold with synthetic terrain/profile unit tests.

## Input Data

Synthetic DEM/DSM profile data only.

## Scenario / Configuration

Manual synthetic profiles cover flat terrain, middle ridge limiting samples, frequency sensitivity, clearance-ratio sensitivity, highest DEM AGL conversion, target DEM AGL conversion, and invalid input handling.

## Method

Run pure Python unit tests for `compute_minimum_required_altitude` and `summarize_minimum_altitude_result`. The tests compare expected geometry behavior, limiting sample selection, AGL conversion, and boundary wording.

## Expected Result

The model returns a minimum required MSL, AGL conversions, a limiting sample index, per-sample requirements, and explicit offline-proxy boundary wording.

## Actual Result

Local verification passed. The Task 015 unit tests and full existing test suite passed in the Codex local environment.

## Metrics

- `minimum_required_msl_m`
- `minimum_required_agl_over_highest_dem_m`
- `minimum_required_agl_over_target_dem_m`
- `limiting_sample_index`
- invalid input exception coverage
- summary boundary wording coverage

## CI / Local Test Result

- `python -m compileall src tests examples`: passed
- `python -m pytest`: passed, 348 tests
- `python -m ruff check .`: passed
- `python -m mypy src`: passed

## Interpretation

If tests pass, Task 015 provides a synthetic-profile scaffold for altitude requirement analysis. The result remains a planning proxy and should not be interpreted as field validation.

## Limitations

Real DEM/DSM loading, heavy GIS dependencies, map rendering, field link validation, and operational approval assessment are not included.

## Paper Figure / Table Candidate

- Table: minimum altitude output fields
- Figure: limiting DSM/Fresnel sample along a synthetic terrain profile

## Public Repository Sensitivity Check

Synthetic data only. No sensitive coordinates, operational details, account information, tokens, keys, private paths, or restricted datasets are included.

## Follow-up Tasks

- Add CI result after PR checks complete.
- Add more synthetic profile variants if GPT Master requests paper figures or tables.
