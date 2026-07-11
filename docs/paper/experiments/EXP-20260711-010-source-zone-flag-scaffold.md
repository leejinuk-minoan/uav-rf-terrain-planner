# EXP-20260711-010 - Source-zone Flag Scaffold

## Experiment Purpose

Verify that synthetic candidate, route, waypoint, and map-ready output records can carry source-zone interpretation metadata.

## Input Data

Synthetic and in-memory records only. No real raster, `METADATA_MAP`, GIS file, CSV, image, PDF, or QGIS project file is used.

## Method

Add a typed source-zone model and propagate source-zone flags through candidate records, route cells, route summaries, waypoint source points, waypoint outputs, and map-ready feature records.

The synthetic scenario includes:

- ESA-derived candidate and output records.
- WMS gap-filled candidate and output records.
- DEM-only fallback candidate and output records.
- Mixed-boundary candidate and output records.

## Expected Result

Output records should identify their source zone, route-level summaries should count mixed source zones, and scenario/map summaries should expose source-sensitive counts without changing the project into a rendered map or raster-processing task.

## Actual Result

Pending CI result for this PR. Implementation adds source-zone scaffold records and synthetic tests.

## Metrics

- Source-zone counts by type.
- Source-sensitive candidate count.
- Source-sensitive route count.
- Source-sensitive waypoint count.
- DEM-only fallback waypoint count.
- Mixed-boundary output count.

## CI / Local Test Result

Cloud Agent did not run local commands. GitHub Actions CI status is recorded on the PR.

## Interpretation

Source-zone flags are interpretation metadata. They help distinguish ESA-derived, WMS gap-filled, DEM-only fallback, and mixed-boundary outputs in later analysis.

DEM-only fallback means the project model uses `surface_delta_proxy_m = 0` and DSM proxy equals DEM for that record. It is a model fallback assumption, not evidence that surface obstacles are absent.

## Limitations

- No real DEM/DSM files are loaded.
- No raster or GIS dependency is added.
- No map rendering is implemented.
- Source-zone flags do not validate terrain accuracy.
- Source-zone flags do not validate field outcomes.

## Figure/Table Candidacy

Useful as a small paper table showing source-zone counts by candidate, route, and waypoint outputs.

## Public Repository Sensitivity Check

No private absolute path, sensitive coordinate, credential, token, secret, raster data file, `METADATA_MAP` data file, CSV, image, PDF, or QGIS project file is included.

## Follow-up Tasks

- Review whether source-zone flags should be visualized in the future UI.
- Apply the same source-zone metadata to later real-data adapter outputs after local raster validation.
- Consider paper ablation tables comparing ESA-derived, WMS gap-filled, and DEM-only fallback output subsets.
