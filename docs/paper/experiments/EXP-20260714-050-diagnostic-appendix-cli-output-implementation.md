# EXP-20260714-050 - Diagnostic Appendix CLI Output Implementation

## Experiment Purpose

Verify the Task 034D command-line delivery of the existing 14-column diagnostic
appendix formatter through explicit stdout and UTF-8 file selectors.

## Inputs and Method

The tests use deterministic synthetic preview dictionaries and saved JSON copies of
the same contract. The CLI delegates diagnostic rendering to
`format_fresnel_diagnostics_appendix_table(preview, max_rows=...)`; it does not
recalculate terrain, Fresnel, score, rank, route, or waypoint values.

## Actual Results

- Synthetic stdout exactly matched the direct formatter result plus one trailing
  newline and created no file.
- Synthetic file output exactly matched stdout for the same source and limit.
- `--max-records 3` retained rows 1 through 3 and the exact
  `... 2 additional row(s) omitted.` sentence.
- Saved JSON legacy, eligible, and no-eligible records matched the direct formatter
  for both stdout and file output.
- Partial, mixed-null, bool, NaN, positive infinity, and negative infinity states
  returned status 1 with the `preview diagnostic table error:` prefix and created no
  artifact.
- Missing parents, directory targets, existing targets without `--force`, and forced
  replacement followed the established status-3 file policy. A forced target remained
  unchanged when formatting failed before writing.
- Every new diagnostic selector conflict with existing output selectors, and the two
  diagnostic selectors together, returned parser status 2 without stdout or output.

## Regression Result

The full local suite completed with `773 passed`. Existing plain text, JSON,
11-column table, report, preview schema, scoring, color/ranking, route/waypoint, and
map/UI behavior are covered by the unchanged regression suite and were not modified.

## Local Verification

```text
python -m compileall src                                 success
python -m pytest tests/test_diagnostic_appendix_cli_output.py  16 passed
python -m pytest                                         773 passed
python -m ruff check .                                   success
python -m mypy src                                       success
```

The manual synthetic CLI smoke with `--max-records 3 --diagnostic-table` succeeded.
Final-head CI evidence is recorded in the Draft PR completion comment after push.

## Paper Appendix Traceability

The CLI makes the reviewed 14-column diagnostic appendix reproducible from synthetic
or saved preview JSON without changing the default 11-column appendix table or report.
No generated output artifact is committed.

## Limitations

The output is an offline terrain/surface diagnostic proxy. It is not a full link
budget, field RF measurement, RSSI/SINR/packet-loss result, or prediction of
communication, reconnaissance, or flight outcomes.

## Public Repository Sensitivity Check

Only source, synthetic tests, and repository-relative documentation are included. No
GIS/DEM/DSM, `METADATA_MAP`, generated table, credential, private path, device,
autopilot, or flight-control content is committed.
