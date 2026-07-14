# Task 034D Diagnostic Appendix CLI Output Implementation

## Purpose

Implement the approved opt-in diagnostic appendix table CLI delivery surfaces without
changing the formatter, report composition, preview schema, scoring, routing, or UI.

## Start Gate

Verified before branch creation:

```text
PR #93: closed / merged to main
PR #93 merge commit: 4997c3e7ca3b0d130f6b885ef473824cef3e08ad
Issue #92: closed / completed
Issue #94: open
base origin/main SHA: 4997c3e7ca3b0d130f6b885ef473824cef3e08ad
open PRs: none
```

The four Task 034C architecture, handoff, decision, and EXP documents were verified
on `origin/main` before implementation.

## Branch and Scope

```text
branch: agent/task-034d-diagnostic-appendix-cli-output
base: origin/main at 4997c3e7ca3b0d130f6b885ef473824cef3e08ad
Issue: #94
```

Changed runtime source:

```text
src/uav_rf_terrain/preview_cli.py
```

Changed and added tests:

```text
tests/test_diagnostic_appendix_cli_output.py
```

## Implemented CLI Contract

Exact opt-in output selectors:

```text
--diagnostic-table
--output-diagnostic-table PATH
```

Both selectors support exactly one source:

```text
--synthetic
--input-json PATH
```

The complete output selector set remains mutually exclusive. Saved JSON accepts
default-table, report, or diagnostic-table stdout/file output, but continues to
reject bare input and JSON/plain-text echo modes.

The CLI calls `format_fresnel_diagnostics_appendix_table(...)` once only when a
diagnostic selector is active and passes `args.max_records` as `max_rows`. The
formatter result is completed before any diagnostic file write.

## Output and Error Behavior

- `--diagnostic-table` prints the existing 14-column formatter output with exactly
  one trailing newline and creates no file.
- `--output-diagnostic-table PATH` reuses `_write_text_output(...)`, writes UTF-8
  with exactly one trailing newline, and prints `preview saved: <PATH>` on success.
- Identical source and limit produce identical stdout and file content.
- Diagnostic formatter failures return status 1, write no stdout, preserve an
  existing forced target, and use `preview diagnostic table error:` on stderr.
- Parser and selector errors remain status 2; path/write errors remain status 3.
- Missing parent directories, directory targets, and existing files without
  `--force` use the existing output-file policy.

## Local Verification

Actually executed:

```text
python -m compileall src                                 success
python -m pytest tests/test_diagnostic_appendix_cli_output.py  16 passed
python -m pytest                                         773 passed
python -m ruff check .                                   success
python -m mypy src                                       success
python -m uav_rf_terrain.preview_cli --synthetic --max-records 3 --diagnostic-table  success
```

The manual smoke printed the approved 14-column header, the first three candidate
rows, and the exact `... 2 additional row(s) omitted.` sentence.

Final-head GitHub Actions evidence is recorded in the Draft PR completion comment
after the final branch push, avoiding an evidence-only commit cycle.

## Regression and Boundaries

Focused tests cover synthetic stdout/file equality, UTF-8/newline behavior,
`--max-records`, legacy/eligible/no-eligible saved JSON, partial/mixed/bool/non-finite
diagnostic failures, all new-selector conflicts, saved-input restrictions, file path
policy, force overwrite, and formatter-failure target preservation.

The implementation does not modify:

```text
preview_appendix_table.py
preview_report.py
preview JSON
plain-text preview
report behavior
scoring, color/ranking, route/waypoint, map/UI
.github/workflows, pyproject.toml, dependencies
```

No GIS/DEM/DSM or `METADATA_MAP` data, generated diagnostic table, credential,
private path, external-device, autopilot, or flight-control content is added.

## Limitations and Next Work

The diagnostic table remains an offline terrain/surface support proxy. It is not a
full link budget, measured RF validation, or communication, reconnaissance, or flight
outcome prediction. Report composition remains a separate reviewed task.
