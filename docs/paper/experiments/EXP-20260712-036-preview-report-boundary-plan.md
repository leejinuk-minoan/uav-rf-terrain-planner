# EXP-20260712-036 - Preview Report Boundary Plan

## Experiment Purpose

Record the documentation-only boundary plan for a future pure preview report formatter that transforms an existing reviewed preview mapping into a deterministic human-readable Markdown/plain-text string.

## Input Data

Existing repository documentation, source, and tests only:

- current preview pipeline and CLI contract documents;
- current preview artifact workflow documentation;
- preview documentation reconciliation record;
- `preview_cli.py`;
- `preview_appendix_table.py`;
- existing preview CLI, contract, table, saved-input, and workflow smoke tests;
- Task 028A handoff and experiment record;
- README and experiment index;
- repository agent guidance.

No CLI execution, JSON read/write, appendix-table generation, report generation, real raster, `METADATA_MAP` content, GIS file, QGIS project, generated output, or external dataset is used.

## Method

1. Confirm the current source and output selectors from implemented documentation and source.
2. Confirm the existing preview JSON and appendix-table validation contract.
3. Identify the narrow pure formatter boundary.
4. Define deterministic proposed report sections.
5. Preserve the MGRS external coordinate and internal-coordinate exclusion boundary.
6. Preserve source-zone fields as interpretation metadata.
7. Separate pure formatting from CLI and report-file output.
8. Define Task 029B Local scope and acceptance criteria.
9. Resolve the experiment identifier collision by reserving EXP-20260712-037 for Task 029B.
10. Add a Local implementation prompt, handoff record, and experiment-index entry.
11. Review the GitHub diff for documentation-only scope.

## Expected Result

- One architecture plan defines the pure formatter boundary.
- One Local prompt narrows Task 029B to formatter code and focused tests.
- One handoff document records the planned contracts and exclusions.
- The report uses the existing preview mapping without a new schema.
- Existing appendix-table validation is reused when practical.
- CLI options and file-output behavior remain unchanged.
- Coordinate, metadata, scoring, route, waypoint, and artifact boundaries remain unchanged.
- No generated report or data artifact is committed.

## Actual Result

Task 029A prepares:

```text
docs/architecture/preview-report-boundary-plan.md
docs/prompts/local-task-029b-preview-report-formatter.md
docs/handoff/task-029a-preview-report-boundary-plan.md
docs/paper/experiments/EXP-20260712-036-preview-report-boundary-plan.md
```

The proposed public boundary is:

```text
format_preview_report(preview: Mapping[str, object], *, include_table: bool = True) -> str
```

The proposed report sections are Summary, Source and Output Context, Candidate Overview, Source-Zone Interpretation, Coordinate Boundary, optional Appendix Table, and Limitations.

Task 029B is assigned EXP-20260712-037 to avoid reusing the Task 029A experiment identifier.

## Metrics

- Architecture plan documents added: 1
- Local implementation prompts added: 1
- Handoff documents added: 1
- Experiment records added: 1
- Proposed public formatter functions: 1
- Proposed handled formatter exceptions: 1
- Proposed fixed report sections: 7
- Existing source selectors preserved: 2
- Existing output selectors preserved: 5
- New CLI selectors added: 0
- Source files changed: 0
- Test files changed: 0
- Preview schema changes: 0
- Generated runtime artifacts committed: 0
- Terrain or GIS files added: 0

## CI / Local Test Result

Local compile, pytest, Ruff, mypy, CLI execution, JSON read/write, table generation, and report generation are not run by the Cloud Agent for this documentation-only task.

GitHub Actions is checked after PR creation on the final documentation head and reported in the completion report. The workflow, runners, matrix, cache, and artifact policy are not changed.

## Interpretation

The proposed boundary keeps report generation compositional:

```text
reviewed preview mapping
→ pure report formatter
→ deterministic report string
```

Optional appendix-table content is delegated to the existing formatter instead of duplicating its field validation and table behavior.

Separating Task 029B from later CLI/file-output work reduces the risk that report formatting changes source selection, process status codes, overwrite policy, path handling, or artifact behavior.

## Limitations

This record does not implement or execute the formatter. It does not inspect runtime report text, verify terminal-newline behavior, assess actual MGRS geography, connect real terrain data, validate field RF conditions, or test Local environment dependencies.

The candidate overview design uses only existing counts and score ranges. It does not establish new analytical validity or operational suitability.

## Figure/Table Candidacy

The fixed report-section sequence and the three-stage formatter/CLI/file-output task split are candidates for a future developer architecture table.

No rendered figure, screenshot, generated table artifact, report file, image, or PDF is created.

## Public Repository Sensitivity Check

Only repository Markdown documentation and an index update are included. No private path, account data, credential, terrain raster, GIS file, `METADATA_MAP` content, generated JSON/text/report artifact, QGIS project, CSV, PDF, image, archive, or external data is included.

The plan keeps the output within research, education, simulation, and human-review boundaries and excludes external-device command behavior.

## Follow-Up Tasks

1. Task 029B-Local: implement the pure preview report formatter and focused tests using EXP-20260712-037.
2. Task 030A-Cloud: define report stdout and explicit file-output behavior only after Task 029B is merged.
3. Task 030B-Local: implement approved CLI/file-output behavior without changing preview schema or scoring.
4. Keep UI, rendered artifacts, real-terrain integration, and field validation as separate reviewed tasks.
