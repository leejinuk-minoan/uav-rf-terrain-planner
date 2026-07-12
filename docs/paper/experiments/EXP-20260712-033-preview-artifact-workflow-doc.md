# EXP-20260712-033 - Preview Artifact Workflow Documentation

## Experiment Purpose

Record the documentation-only consolidation of the implemented preview artifact workflow from synthetic preview generation to saved JSON reuse and appendix-table output.

## Input Data

Existing repository source files, tests, architecture documents, handoff records, experiment records, README content, and agent-operation guidance only.

No runtime preview artifact, real raster, `METADATA_MAP` content, GIS file, QGIS project, CSV, PDF, image, or archive is used.

## Method

Review the implemented preview CLI, appendix-table formatter, source and output regression tests, saved-input tests, prior architecture plans, handoff records, and experiment records.

Document:

- current capabilities;
- source and output selectors;
- nine end-to-end commands;
- synthetic and saved-input flows;
- table behavior;
- status-code meanings;
- MGRS and source-zone boundaries;
- internal/debug coordinate exclusion;
- artifact path, overwrite, cleanup, and repository policies;
- current limitations and follow-up boundaries.

No CLI command, JSON read/write, table generation, or runtime artifact inspection is performed by the Cloud Agent.

## Expected Result

- One architecture document records the complete current workflow.
- One user-facing usage document provides command-only examples.
- Existing runtime behavior remains unchanged.
- Source and output compatibility is unambiguous.
- Status codes 0 through 3 remain documented.
- MGRS and source-zone boundaries remain intact.
- Artifact handling prohibits committed generated outputs.
- One handoff record and one experiment record are added.
- README and experiment index receive concise updates.

## Actual Result

The architecture workflow document, user usage guide, Task 027A handoff, and EXP-20260712-033 record were prepared. README receives one Task 027A summary sentence and the experiment index receives one entry.

No source, test, CLI, formatter, schema, terrain, scoring, route, waypoint, report, UI, or file-output behavior is changed.

## Metrics

- Architecture documents added: 1
- Usage documents added: 1
- Handoff documents added: 1
- Experiment records added: 1
- End-to-end command workflows documented: 9
- Source selectors documented: 2
- Output selectors documented: 5
- Status-code meanings documented: 4
- Source files changed: 0
- Test files changed: 0
- Generated runtime artifacts committed: 0
- Terrain or GIS files added: 0

## CI / Local Test Result

Local compile, pytest, Ruff, mypy, CLI execution, JSON read/write, and table generation are not run by the Cloud Agent. GitHub Actions is checked after PR creation on the final documentation head and reported in the Task completion report.

## Interpretation

The preview feature family now has an implementation-aligned workflow reference that separates source selection, projection selection, saved-artifact reuse, validation, and explicit file handling without creating a new runtime contract.

The usage document gives operators a concise sequence for generating JSON, producing tables directly, and reusing reviewed JSON while keeping runtime artifacts outside the repository.

## Limitations

This documentation does not execute commands, verify generated content, alter runtime behavior, validate supplied MGRS geography, connect real terrain data, generate a report, or render a user interface.

Historical architecture documents may still describe the state that existed before later Tasks implemented table and saved-input features.

## Figure/Table Candidacy

The source/output compatibility matrix and the left-to-right workflow descriptions are candidates for a future implementation appendix or methodology figure.

No rendered figure, screenshot, generated table artifact, image, or PDF is created.

## Public Repository Sensitivity Check

Only repository Markdown documentation and index updates are included. No private path, account data, terrain raster, GIS file, `METADATA_MAP` content, generated input/output artifact, QGIS project, image, PDF, or archive is included.

## Follow-Up Tasks

1. Run a Local smoke verification of the documented command set if execution evidence is required.
2. Consider a later documentation cleanup for older planned-state preview documents.
3. Keep report generation, UI consumption, plain-text reconstruction from saved JSON, and real-terrain integration as separate reviewed tasks.
