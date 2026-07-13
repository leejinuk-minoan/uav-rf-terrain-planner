# Task 031A Preview Report CLI Documentation Reconciliation

## Purpose
Reconcile documentation with implemented report stdout/file output.
## Documents Updated
Four current workflow/contract documents, this handoff, EXP-040, and the index.
## Current Implemented CLI Surface
Two source selectors and seven mutually exclusive output selectors, including report stdout/file.
## Current Source and Output Compatibility
Saved JSON supports table and report stdout/file only.
## Current Report Workflow
The pure formatter is reused and includes its appendix table by default; no report row limit exists.
## Current File-Output Policy
Explicit UTF-8 path, no parent creation, protected existing file, optional `--force`.
## Current Status-Code Policy
Success 0, handled input/formatter 1, argument 2, output-file 3.
## Coordinate and Metadata Boundary
MGRS and source-zone interpretation metadata remain unchanged.
## Code/Test Change Check
No code or test changes.
## Test/CI Result
Repository checks are recorded in the PR; CI pending initially.
## Overall Status
Documentation reconciled.
## Limitations
Documentation-only.
## Public Repository Sensitivity Check
No private path, generated artifact, or GIS data.
## Follow-Up Tasks
Review future consumers separately.
