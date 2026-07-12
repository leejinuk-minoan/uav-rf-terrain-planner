# Task 022B Preview CLI Scaffold

## Environment

- Windows local execution environment
- Repository base: PR #60 merge commit `27b2a0a`
- Standard-library argparse and JSON serialization only

## Implemented scope

`src/uav_rf_terrain/preview_cli.py` adds a minimal module CLI for the existing synthetic in-memory candidate preview path:

```text
python -m uav_rf_terrain.preview_cli --synthetic
python -m uav_rf_terrain.preview_cli --synthetic --max-records 3
python -m uav_rf_terrain.preview_cli --synthetic --json
```

The implementation contains `build_parser()`, `run_preview_cli()`, and `main()`. It invokes `build_synthetic_candidate_preview_smoke()` without modifying the existing preview, scoring, route, or waypoint contracts.

## Plain-text stdout

Default mode prints the existing `preview_text` to stdout. It includes the `Candidate display preview` title, external coordinate format `MGRS`, and user coordinate field `candidate_cell_mgrs`.

`--max-records 3` limits visible candidate rows to three and preserves the existing omitted-record message. Values must be positive integers. Invalid, zero, negative, non-integer, and malformed values return argparse status 2 with concise stderr.

## JSON stdout

`--json` serializes the existing `preview_dict` with standard-library `json.dumps(..., ensure_ascii=False)`. The output parses as JSON, contains `external_coordinate_format = MGRS`, and preserves `candidate_cell_mgrs` in every record. Dataclasses and enum objects are not serialized directly.

`--max-records` controls plain-text row visibility. JSON mode continues to print the existing complete preview dictionary rather than mutating its record contract.

## Coordinate boundary

User-facing coordinates remain MGRS through `candidate_cell_mgrs`. Plain-text and JSON stdout exclude internal/debug coordinate fields defined by the project coordinate I/O policy. No coordinate conversion or geographic-accuracy assessment is implemented.

## File and terrain boundary

- No file writing
- No output-directory creation
- No report or rendering output
- No real DEM/DSM/landcover access
- No `METADATA_MAP` access
- No GIS dependency

## Error handling

Expected preview errors return status 1 with concise stderr and no traceback. Parser errors return status 2. Successful text and JSON modes return status 0.

## Test result

- Focused CLI tests: passed
- Plain-text, record limit, malformed limits, JSON parsing, MGRS fields, internal-coordinate exclusion, file non-creation, deterministic status, and expected error handling covered
- Existing candidate preview and synthetic preview tests remain passing
- Manual text, limited-text, and JSON commands completed successfully

## Overall status

**passed**.

The existing synthetic MGRS candidate preview can now be inspected through stdout in plain-text or JSON form without persistent output.

## Limitations

- Synthetic placeholder MGRS strings are reused; no conversion or geographic validation is performed.
- JSON mode emits the existing full preview dictionary even when a plain-text limit is supplied.
- This is a developer inspection scaffold, not a report or UI implementation.
- No real terrain input or scoring recalculation is included.

## Public repository sensitivity check

No private path, coordinate source data, raster, generated output, CSV, PDF, image, QGIS project, or archive is committed. CLI stdout uses only existing synthetic preview values.

## Follow-up tasks

1. Define persistent file-output policy separately if saved previews are required.
2. Keep report and UI rendering outside this stdout scaffold.
3. Preserve the MGRS external boundary and internal-coordinate exclusion in future output adapters.
