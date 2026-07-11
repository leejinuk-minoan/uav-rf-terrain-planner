# Task 021D Candidate Display Formatter Scaffold

## Purpose

Task 021D converts `CandidateCellMapFeature` records with attached MGRS metadata into pure Python display records.

## Inputs

Input records are `CandidateCellMapFeature` values whose optional metadata includes `candidate_cell_mgrs`, `external_coordinate_format`, `user_coordinate_field`, `source_zone`, `source_sensitive`, and `source_zone_reason`.

## Display records

Display records contain candidate identifier, MGRS coordinate, color, scores, source-zone metadata, candidate reason, and a label. Display dictionaries contain primitive values only.

## MGRS external coordinate handling

The user-facing candidate coordinate is `candidate_cell_mgrs`. `external_coordinate_format` is `MGRS`. This task does not implement MGRS conversion or verify the geographic accuracy of supplied MGRS text.

## Internal/debug coordinate handling

Internal values such as `x_m`, `y_m`, raster indices, projected coordinates, and WGS84 components are not included in display records or display dictionaries.

## Source-zone metadata handling

`source_zone` is returned as text. `source_sensitive` remains a boolean. `source_zone_reason` is preserved.

## Candidate table/popup compatibility

The bundle and by-candidate-id helper prepare data for later candidate tables, detail panels, and UI cards. This task does not render tables, panels, HTML, Markdown, Folium, Streamlit, or maps.

## Test result

Synthetic tests cover conversion, MGRS policy fields, labels, score and reason preservation, summary counts, duplicate identifiers, missing metadata, invalid metadata, internal-coordinate exclusion, and dependency boundaries.

## Overall status

The formatter scaffold is implemented for CI review without changing existing map output constructors.

## Limitations

This task does not perform rendering, MGRS conversion, coordinate-accuracy assessment, scoring changes, LOS/Fresnel recalculation, route or waypoint scoring changes, or real terrain-file loading.

## Public repository sensitivity check

Only source and documentation changes are included. No local data files, GIS datasets, images, PDFs, CSV files, or QGIS project files are included.

## Follow-up tasks

1. Add a separate plain-text or JSON preview scaffold.
2. Keep rendering separate from this formatter.
3. Preserve internal geometry values as internal implementation data.
