# Task 022A Preview Output Boundary and Local Implementation Plan

## Purpose

Task 022A defines the boundary between the current MGRS-based candidate preview pipeline and later CLI, report, and file-output implementation work. It is a documentation and planning task only.

## Documents Added

- `docs/architecture/preview-output-boundary-plan.md`
- `docs/prompts/local-task-022b-preview-cli-scaffold.md`
- `docs/handoff/task-022a-preview-output-boundary-plan.md`
- `docs/paper/experiments/EXP-20260711-022-preview-output-boundary-plan.md`

README and the experiment index receive only short summary entries.

## Boundary Decision

The recommended implementation order is:

```text
1. CLI stdout preview scaffold
2. optional JSON stdout scaffold
3. optional JSON file output scaffold
4. optional plain-text file output scaffold
5. later UI/report formatting
```

Task 022B should implement only a minimal synthetic stdout CLI and, if small and non-breaking, optional JSON stdout. Persistent file output is deferred to Task 022C or later.

## Cloud vs Local Split

Cloud Execution Agent scope:

- output contract design
- boundary documentation
- Local prompt preparation
- review criteria and repository-safety checks
- PR and GitHub Actions review

Local Execution Agent scope:

- actual Python CLI/helper implementation
- parser or module entrypoint choice
- stdout and return-code behavior
- JSON serialization behavior
- focused tests
- compileall, pytest, ruff, and mypy execution
- manual local command smoke

## Recommended Task 022B Scope

Task 022B should:

1. Invoke `build_synthetic_candidate_preview_smoke(...)`.
2. Print the existing plain-text preview to stdout by default.
3. Support an optional positive maximum-record limit.
4. Optionally print the existing JSON-ready preview dictionary to stdout.
5. Add focused CLI/helper tests.
6. Avoid file writing, report generation, UI rendering, real terrain access, coordinate conversion, and scoring changes.

Suggested files are `src/uav_rf_terrain/preview_cli.py` and `tests/test_preview_cli.py`, but the Local Agent may adjust them after reviewing the package layout.

## MGRS External Coordinate Handling

The user-facing candidate coordinate remains `candidate_cell_mgrs`, and the external coordinate format remains `MGRS`.

All later stdout, report, and file outputs must preserve this boundary. Task 022A does not implement coordinate conversion or assess geographic correctness of caller-provided or placeholder MGRS strings.

## Internal/Debug Coordinate Handling

WGS84 components, EPSG:5179 components, local `x_m` and `y_m`, and raster row/column values remain internal/debug fields.

They must not appear in CLI stdout, JSON stdout, report output, or later file output unless a separate explicitly internal diagnostic contract is approved.

## Source-Zone Metadata Handling

The output contract may preserve:

- `source_zone`
- `source_sensitive`
- `source_zone_reason`

These remain interpretation metadata. Task 022A does not change candidate scoring, LOS/Fresnel values, route scoring, or waypoint scoring.

## Test/CI Result

No source or test code is changed. Cloud Agent does not run local commands. GitHub Actions is used as the checked repository CI result after the pull request is created.

## Overall Status

The current preview pipeline now has an explicit output boundary and a minimal Local implementation plan. The next implementation task is limited to stdout behavior rather than persistent file output or UI/report generation.

## Limitations

This task does not:

- change source code or tests
- implement a CLI
- write files
- generate reports
- render maps, tables, popups, HTML, or application UI
- access real DEM, DSM, landcover, or `METADATA_MAP`
- add GIS dependencies
- convert MGRS coordinates
- assess MGRS geographic correctness
- change scoring, LOS/Fresnel, route, or waypoint logic
- create generated media or report artifacts

## Public Repository Sensitivity Check

Only Markdown documentation and short README/index updates are included. No private absolute path, sensitive coordinate, credential, secret, local terrain data, GIS file, generated media, CSV, PDF, QGIS project, or output artifact is included.

## Follow-Up Tasks

1. Task 022B-Local: implement the minimal synthetic preview CLI and local tests.
2. Task 022C-Local: add persistent JSON/text output only after path, overwrite, encoding, and artifact policies are approved.
3. A later UI or report task may consume the reviewed JSON-ready preview contract.