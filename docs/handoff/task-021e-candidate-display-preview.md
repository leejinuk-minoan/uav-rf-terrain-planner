# Task 021E Candidate Display Preview Scaffold

## Purpose

Task 021E converts a `CandidateDisplayBundle` into a preview object, a JSON-ready dictionary, and a plain-text preview string.

## Inputs

The input is a synthetic or future runtime `CandidateDisplayBundle` produced by the Task 021D formatter. Each candidate record already contains primitive display metadata and a caller-supplied MGRS coordinate.

## Preview object

`CandidateDisplayPreview` stores the preview title, external coordinate format, user coordinate field, record counts, primitive record dictionaries, the Task 021D summary, and a reason string.

## JSON-ready preview

`build_candidate_display_preview_dict(...)` returns only strings, integers, lists, dictionaries, floats, and booleans. It does not write a JSON file. Candidate records are copied from `CandidateDisplayRecord.to_display_dict()` and tuples are converted to lists.

## Plain-text preview

`format_candidate_display_preview(...)` produces a human-readable string for review. Each row uses the Task 021D display label and adds the overall score and source-zone text. An optional positive `max_records` value limits visible rows and reports the omitted record count.

## MGRS external coordinate handling

The user-facing candidate coordinate remains `candidate_cell_mgrs`, and `external_coordinate_format` remains `MGRS`. This task does not implement MGRS conversion or assess the geographic accuracy of supplied MGRS text.

## Internal/debug coordinate handling

Preview objects, JSON-ready dictionaries, and plain-text output do not contain `x_m`, `y_m`, raster indices, projected-coordinate fields, or WGS84 component fields.

## Test result

Synthetic tests cover preview construction, JSON serialization, MGRS policy fields, internal-coordinate exclusion, plain-text output, truncation, invalid limits, invalid bundle types, summary preservation, and dependency boundaries. Local commands are not run by the Cloud Agent; GitHub Actions provides the checked CI result.

## Overall status

The preview scaffold is implemented as a separate pure Python layer above Task 021D display records.

## Limitations

This task does not write files, implement a command-line interface, render HTML or Markdown, build tables or popups, render maps, convert MGRS, change scoring, recalculate LOS/Fresnel values, or change route and waypoint scoring.

## Public repository sensitivity check

Only source code, synthetic tests, and documentation are included. No local terrain data, `METADATA_MAP` content, GIS datasets, generated media, CSV files, PDFs, or QGIS project files are included.

## Follow-up tasks

1. Connect the preview scaffold to the existing synthetic scenario flow in a separate task.
2. Keep file output and command-line integration outside this scaffold.
3. Preserve MGRS as the user-facing candidate coordinate boundary.
