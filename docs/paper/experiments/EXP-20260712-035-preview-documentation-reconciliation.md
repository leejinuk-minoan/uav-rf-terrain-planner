# EXP-20260712-035 - Preview Documentation Reconciliation

## Experiment Purpose

Record the documentation-only reconciliation of current implemented preview workflow references and earlier planning-boundary documents.

## Input Data

Existing repository documentation and tests only:

- current preview architecture and usage documents;
- earlier preview planning documents;
- preview CLI, formatter, saved-input, and workflow smoke tests;
- Task 027A and Task 027B handoff records;
- EXP-20260712-033 and EXP-20260712-034 records;
- README and experiment index content;
- repository agent guidance.

No runtime CLI execution, JSON read/write, table-file generation, real raster, `METADATA_MAP` content, GIS file, QGIS project, generated media, or external dataset is used.

## Method

1. Identify the current implemented architecture, user workflow, and smoke-test references.
2. Identify earlier planning documents whose future-tense statements may be mistaken for current behavior.
3. Define a documentation reading order and precedence rule.
4. Add one reconciliation guide.
5. Add a short non-destructive current implementation note to each of four planning documents.
6. Preserve historical document bodies.
7. Record the current source/output, artifact, validation, coordinate, metadata, and artifact-handling contracts.
8. Add a handoff record, README summary, and experiment-index entry.
9. Review the final GitHub diff for documentation-only scope.

## Expected Result

- One reconciliation guide identifies current implemented references.
- Four historical planning documents receive short implementation-reference notes.
- Historical reasoning remains preserved.
- Current source and output selectors are unambiguous.
- Current workflow and status-code contracts are summarized.
- Coordinate, metadata, and artifact boundaries remain unchanged.
- No source, test, CLI, formatter, schema, or file-output behavior changes.
- No generated runtime artifact is committed.

## Actual Result

A reconciliation guide, Task 028A handoff, and EXP-20260712-035 record were prepared. Four historical planning documents receive the same short current implementation note. README receives one Task 028A summary sentence, and the experiment index receives one entry.

The current references are identified as:

```text
docs/architecture/preview-artifact-workflow.md
docs/usage/preview-artifact-workflow.md
tests/test_preview_artifact_workflow_smoke.py
```

The historical planning documents remain in place and retain their original task content.

## Metrics

- Reconciliation architecture documents added: 1
- Handoff documents added: 1
- Experiment records added: 1
- Historical planning documents marked: 4
- Current primary references identified: 3
- Related regression test files indexed: 6
- Source selectors summarized: 2
- Output selectors summarized: 5
- Status-code meanings summarized: 4
- Source files changed: 0
- Test files changed: 0
- Generated runtime artifacts committed: 0
- Terrain or GIS files added: 0

## CI / Local Test Result

Local compile, pytest, Ruff, mypy, CLI execution, JSON read/write, and table generation are not run by the Cloud Agent for this documentation-only task. GitHub Actions is checked after PR creation on the final documentation head and reported in the completion report.

## Interpretation

The preview document family now distinguishes three kinds of evidence:

1. current implemented architecture and usage references;
2. executable regression references;
3. historical planning rationale.

This reduces the risk that a pre-implementation statement is treated as the latest CLI or artifact contract while preserving the task history that led to the implementation.

## Limitations

This record does not execute preview workflows, inspect generated output, validate supplied MGRS geography, connect real terrain data, or assess runtime behavior beyond repository documentation and existing test references.

The reconciliation notes do not rewrite each historical statement. Readers must use the linked current references for present behavior.

## Figure/Table Candidacy

The documentation-role table and recommended reading order are candidates for a future developer appendix or architecture documentation map.

No rendered figure, screenshot, generated table artifact, image, or PDF is created.

## Public Repository Sensitivity Check

Only repository Markdown documentation and index updates are included. No private path, account data, terrain raster, GIS file, `METADATA_MAP` content, generated JSON/text/table input or output, QGIS project, CSV, PDF, image, or archive is included.

## Follow-Up Tasks

1. Use the reconciliation guide as the entry point when future preview tasks cite architecture documents.
2. Consider a compact preview documentation index only if the document set grows further.
3. Keep plain-text reconstruction, report formatting, interactive consumption, and real-terrain integration as separate reviewed tasks.
