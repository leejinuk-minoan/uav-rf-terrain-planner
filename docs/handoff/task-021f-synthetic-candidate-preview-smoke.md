# Task 021F Synthetic Candidate Display Preview Smoke

## Purpose

Task 021F connects the existing synthetic scenario flow to candidate display preview outputs through a pure Python in-memory smoke layer.

## Synthetic flow

The smoke follows this sequence:

1. Build the synthetic end-to-end scenario.
2. Build candidate map features.
3. Create deterministic placeholder MGRS strings.
4. Build source-zone metadata and attach it through the existing map package path.
5. Build candidate display records.
6. Build preview object, JSON-ready dictionary, and plain-text preview.

## Inputs

Inputs are the repository synthetic scenario records and deterministic placeholder MGRS metadata only. No local terrain datasets are read.

## Dummy MGRS handling

The user-facing candidate coordinate is `candidate_cell_mgrs`, and `external_coordinate_format` is `MGRS`. The generated strings are synthetic placeholder MGRS only. They are not produced by coordinate conversion and are not assessed for geographic accuracy.

## Source-zone metadata handling

Each candidate metadata mapping preserves `source_zone`, `source_sensitive`, and `source_zone_reason` from its synthetic map feature. It also contains `cell_id`, `candidate_cell_mgrs`, `external_coordinate_format`, `user_coordinate_field`, and `internal_debug_available`.

## Preview output

The smoke returns a result containing scenario and record counts, a JSON-ready preview dictionary, a plain-text preview, and an interpretation reason. It does not write a JSON file or any other output file.

## Internal/debug coordinate handling

Preview dictionaries and text do not contain `x_m`, `y_m`, raster row or column fields, EPSG:5179 components, or WGS84 components. Internal geometry may remain inside the map feature layer but is not copied into user-facing preview output.

## Test result

Synthetic tests cover the complete in-memory flow, JSON serialization, placeholder MGRS generation, source-zone metadata construction, record-count consistency, source-sensitive counts, preview truncation, invalid identifiers, internal-coordinate exclusion, dependency boundaries, and restricted wording checks. Local commands are not run by the Cloud Agent; GitHub Actions provides the checked CI result.

## Overall status

The synthetic scenario can be connected to MGRS-based candidate preview output without changing the existing scenario, scoring, route, waypoint, display, or preview APIs.

## Limitations

This task does not read real DEM, DSM, or landcover files. It does not access `METADATA_MAP`, write files, implement a command-line interface, render HTML or Markdown, render tables or popups, render maps, use Streamlit or Folium, convert MGRS, assess MGRS geographic accuracy, change scoring, recalculate LOS/Fresnel values, or change route and waypoint scoring.

## Public repository sensitivity check

Only source code, synthetic tests, and documentation are included. No local absolute path, sensitive coordinate, credential, secret, local terrain data, `METADATA_MAP` content, GIS dataset, generated media, CSV file, PDF, or QGIS project file is included.

## Follow-up tasks

1. Document the current preview pipeline as a concise architecture diagram or schema table.
2. Keep file output, command-line behavior, and rendering outside this smoke layer.
3. Preserve MGRS as the user-facing candidate coordinate boundary.
