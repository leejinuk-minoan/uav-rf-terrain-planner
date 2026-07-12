# Preview Output Boundary Plan

## Purpose

This document defines the boundary between the current MGRS-based candidate preview pipeline and later user-output implementation work. It narrows the next Local task to a minimal stdout preview scaffold and separates file writing, report generation, UI formatting, and map rendering into later tasks.

## Current Candidate Preview State

The current in-memory pipeline is:

```text
Synthetic scenario
→ candidate map features
→ source-zone MGRS metadata attachment
→ candidate display records
→ candidate display preview object
→ JSON-ready preview dictionary
→ plain-text preview
```

The current code already provides a JSON-ready dictionary and a plain-text preview string. It does not provide a command-line entrypoint, write files, generate reports, or render a UI.

## Output Surface Candidates

| Output surface | Purpose | Input object | Output format | Cloud design possible | Local implementation required | Included in Task 022A | Recommended follow-up |
|---|---|---|---|---|---|---|---|
| CLI stdout preview | Quick developer review of the synthetic preview path | `SyntheticCandidatePreviewSmokeResult` or its preview text | Plain text on stdout | Yes | Yes | Design only | Task 022B |
| JSON stdout | Machine-readable inspection without file management | JSON-ready preview dictionary | JSON text on stdout | Yes | Yes | Design only | Task 022B optional mode |
| JSON file output | Persist preview data for later tools | JSON-ready preview dictionary | UTF-8 JSON file | Yes | Yes | Boundary only | Task 022C or later |
| Plain-text file output | Persist a human-readable preview | Plain-text preview string | UTF-8 text file | Yes | Yes | Boundary only | Task 022C or later |
| Future UI table/card/popup | Present candidate records interactively | Display bundle or JSON-ready preview dictionary | UI components | Contract discussion only | Yes | Not included | Separate UI task |
| Paper/report appendix table | Present reviewed candidate records in a publication artifact | Reviewed preview data | Formatted table or appendix | Contract discussion only | Yes | Not included | Separate report/artifact task |

## Recommended Output Order

```text
1. CLI stdout preview scaffold
2. optional JSON stdout scaffold
3. optional JSON file output scaffold
4. optional plain-text file output scaffold
5. later UI/report formatting
```

Task 022B should implement only the first item and, if small and non-breaking, the second item. File output should remain outside Task 022B.

## Cloud vs Local Boundary

Cloud Execution Agent responsibilities:

- define output contracts and scope boundaries
- document stdout, JSON, report, and file-output decisions
- prepare the Local Task 022B prompt
- define PR review, protected-path, data-file, and wording checks
- review GitHub diff and GitHub Actions results

Local Execution Agent responsibilities:

- implement the Python CLI or helper entrypoint
- decide whether to use `argparse` or a small module-level `main()`
- execute compile, pytest, ruff, and mypy checks
- test stdout capture and exit behavior
- test JSON serialization and JSON stdout behavior
- confirm that the module runs in the local project environment

## CLI Preview Boundary

The Task 022B CLI is limited to the existing synthetic in-memory preview path.

Allowed behavior:

- invoke the synthetic candidate preview smoke helper
- print the existing plain-text preview to stdout
- accept an optional positive record limit
- optionally print the existing JSON-ready preview dictionary as JSON on stdout
- return a non-zero exit status for invalid arguments or expected input errors
- preserve `candidate_cell_mgrs` as the user-facing coordinate field
- keep internal/debug coordinate values out of stdout

Illustrative commands:

```text
python -m uav_rf_terrain.preview_cli --synthetic
python -m uav_rf_terrain.preview_cli --synthetic --max-records 3
python -m uav_rf_terrain.preview_cli --synthetic --json
```

These commands illustrate the intended contract. Task 022A does not implement them, and Task 022B may adjust the module name after reviewing the existing package structure.

Task 022B must not access real DEM, DSM, or landcover data, access `METADATA_MAP`, convert coordinates, write files, or add rendering behavior.

## Report Preview Boundary

A report preview is not part of Task 022B. A later report task may consume the JSON-ready dictionary or display records to create a reviewed appendix table or narrative summary.

A report layer must remain separate from the current scoring and preview layers. It must not reinterpret source-zone metadata as a new score or alter candidate ordering.

## JSON File Output Boundary

Task 022B should not write JSON files.

File output introduces additional policy decisions:

- output path handling
- directory creation
- overwrite behavior
- UTF-8 encoding
- deterministic formatting and indentation
- private-path leakage checks
- generated-artifact cleanup
- generated-file commit risk

These concerns should be handled in Task 022C-Local or a later dedicated file-output task.

## Plain-Text File Output Boundary

Task 022B should not write plain-text files. It should return or print the existing plain-text preview only.

A later file-output task must define path handling, overwrite policy, encoding, newline behavior, output-directory policy, cleanup, and repository-exclusion rules before writing text files.

## MGRS External Coordinate Boundary

All user-facing candidate coordinates remain:

- field: `candidate_cell_mgrs`
- format: `MGRS`

CLI stdout, JSON stdout, later report output, and later file output must preserve this boundary. The current task family does not implement coordinate conversion or assess geographic correctness of supplied or placeholder MGRS text.

## Internal/Debug Coordinate Boundary

The following fields remain internal/debug data and must not appear in CLI, report, stdout, or file output:

- `x_m`
- `y_m`
- `row`
- `col`
- `epsg5179_x_m`
- `epsg5179_y_m`
- `wgs84_lat`
- `wgs84_lon`
- `local_x_m`
- `local_y_m`
- `raster_row`
- `raster_col`

Internal geometry may remain inside map-feature or raster-processing objects, but output adapters must not expose it by default.

## Source-Zone Interpretation Boundary

The following values remain output interpretation metadata:

- `source_zone`
- `source_sensitive`
- `source_zone_reason`

They may be printed in plain-text or JSON output. They do not change candidate scoring, LOS/Fresnel values, route scoring, or waypoint scoring.

## Non-Goals

Task 022A does not:

- change source code or tests
- implement a CLI
- write JSON or text files
- generate a report
- render a map, table, popup, HTML page, or application UI
- add Streamlit or Folium behavior
- access real terrain data or `METADATA_MAP`
- add GIS dependencies
- convert MGRS coordinates
- assess MGRS geographic correctness
- change scoring, LOS/Fresnel, route, or waypoint logic
- add vehicle-control integration

## Task 022B Local Implementation Scope

Task 022B should be a minimal Local implementation task:

1. Add one small CLI/helper module, with `src/uav_rf_terrain/preview_cli.py` as a suggested path.
2. Invoke `build_synthetic_candidate_preview_smoke(...)`.
3. Print `preview_text` to stdout by default.
4. Support a positive `--max-records` option.
5. Optionally support `--json` to serialize `preview_dict` to stdout.
6. Add focused tests, with `tests/test_preview_cli.py` as a suggested path.
7. Do not write files.
8. Do not access real terrain data.
9. Do not expose internal/debug coordinates.
10. Do not change scoring or existing preview contracts.

## Acceptance Criteria for Task 022B

Task 022B is acceptable when:

- the default command prints the synthetic plain-text preview to stdout
- `--max-records` passes a positive integer limit to the existing smoke/preview path
- invalid limits produce a concise error and non-zero exit status
- optional JSON mode emits valid JSON to stdout
- JSON output preserves `candidate_cell_mgrs` and `external_coordinate_format = MGRS`
- stdout does not contain internal/debug coordinate fields
- no file is created
- existing preview/scoring/map APIs remain unchanged unless a minimal import/export adjustment is required
- focused tests cover text stdout, JSON stdout, limits, and error behavior
- compileall, pytest, ruff, and mypy complete successfully in the Local environment
- the PR changes remain limited to the CLI/helper, focused tests, and concise task records

## Follow-Up Tasks

1. Task 022B-Local: implement the minimal stdout CLI and optional JSON stdout mode.
2. Task 022C-Local: define and implement file-output policy only if persistent output is required.
3. A later UI task may consume either the display bundle or JSON-ready dictionary after the user-output contract is reviewed.
4. A later report/artifact task may format reviewed output as a paper appendix table.