# EXP-20260713-044 - Dominant Obstacle Output Boundary Review

## Experiment Purpose

Record a code/document contract audit for the dominant Fresnel obstacle diagnostic output boundary.

This is not an RF experiment, runtime output test, communication-performance validation, or field measurement.

## Input Data

Existing repository source, documentation, Issue #82, and PR #81 metadata only:

- `src/uav_rf_terrain/fresnel.py`;
- candidate/scenario, map, display, preview, table, report, and CLI source files;
- current preview/report architecture and usage documents;
- Task 032AB and Task 032CD architecture, handoff, and experiment records;
- current score-model and project governance documents.

No CLI execution, preview/report generation, JSON read/write, real raster, `METADATA_MAP` content, GIS file, QGIS project, generated output, or external dataset is used.

## Method

1. Verify PR #81 merge metadata and `main` base commit.
2. Inspect the implemented `FresnelAnalysis` and nested dominant-obstacle model.
3. Trace the actual synthetic candidate-to-preview object path.
4. Identify every layer where diagnostic values are absent.
5. Review current preview primitive-value, table-column, and report-section contracts.
6. Define a flat optional diagnostic projection.
7. Define legacy, enriched-with-obstacle, enriched-without-obstacle, and invalid partial-set states.
8. Define JSON, plain-text, report, and appendix-table policies.
9. Reconcile score semantics and documentation boundaries.
10. Record a separate Task 033B implementation scope.

## Expected Result

- the current transfer gap is documented using verified file, class, and function names;
- an exact optional flat field set is defined;
- legacy saved previews remain valid;
- no-eligible-obstacle and unavailable-diagnostics states are distinct;
- partial diagnostic sets are rejected by the proposed contract;
- JSON and human-readable precision policies are separated;
- report output gains a future diagnostic section while appendix-table columns remain unchanged;
- scoring, color, ranking, route, and waypoint behavior remain unchanged;
- no runtime or generated artifact is changed by Task 033A.

## Actual Result

The audit found that the dominant diagnostic terminates at `FresnelAnalysis`. The current preview path begins from synthetic scalar candidate scores and carries only overall/shielding scores and source-zone metadata through `SyntheticCandidateRecord`, `CandidateCellMapFeature`, `CandidateDisplayRecord`, and the preview dictionary.

The audit defines an all-or-none ten-field flat projection and distinguishes:

```text
legacy/un-enriched record
complete enriched record with eligible obstacle
complete enriched record with no eligible obstacle
invalid partial diagnostic record
```

The planned report section is `## Fresnel Diagnostics`. Existing appendix-table columns remain unchanged for Task 033B.

## Metrics

- code/document contract paths audited: 9
- proposed optional user-facing diagnostic fields: 10
- user-facing sample-index fields approved: 0
- compatibility states defined: 4
- output surfaces reviewed: 4
- current scoring formulas changed: 0
- source files changed by Task 033A: 0
- test files changed by Task 033A: 0
- generated runtime artifacts committed: 0
- terrain or GIS files added: 0

## CI / Local Test Result

The Cloud Agent does not claim local compileall, pytest, Ruff, mypy, CLI execution, preview/report generation, or JSON/file-output testing.

GitHub Actions is checked on the final Draft PR head. The existing workflow, runner, matrix, cache, and artifact policy are unchanged.

## Interpretation

The diagnostic can improve explanation of path-local Fresnel restriction without changing the historical average Fresnel score or downstream selection behavior.

The audit also shows that Task 033B is a multi-layer data-contract task rather than a change to the Fresnel formula implementation itself.

## Limitations

This audit does not implement the projection or execute it. It does not verify runtime formatting, saved JSON compatibility, actual MGRS geography, field RF conditions, real DEM/DSM behavior, or communication outcomes.

The single knife-edge loss remains an idealized additional diffraction-loss proxy and not a full propagation model.

## Figure/Table Candidacy

The verified transfer-path gap table and the four-state compatibility model are candidates for a future developer appendix.

No rendered figure, screenshot, generated table artifact, report file, image, or PDF is created.

## Public Repository Sensitivity Check

Only repository-relative source/document references and contract findings are recorded. No private path, credential, raster, GIS file, `METADATA_MAP` content, generated JSON/text/report artifact, QGIS project, CSV, PDF, image, archive, or external data is included.

## Follow-Up Tasks

1. Task 033B: implement the optional diagnostic bridge and formatter output with local regression tests.
2. Keep appendix-table extension separate.
3. Keep any scoring use separate and subject to explicit validation and approval.
