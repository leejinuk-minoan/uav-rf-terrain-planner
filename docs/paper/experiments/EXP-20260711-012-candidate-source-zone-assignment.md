# EXP-20260711-012 - Candidate Source-zone Assignment Scaffold

## Experiment Purpose

Verify that candidate-grid cells can receive source-zone interpretation metadata through a pure Python provider layer before later raster-backed scoring integration.

## Input Data

Synthetic and in-memory candidate cells only. No real raster, `METADATA_MAP`, GIS file, CSV, image, PDF, or QGIS project file is used.

## Method

Add a candidate-grid source-zone assignment scaffold that accepts `CandidateCell` records and a point-based provider callable. The scaffold validates candidate cell IDs and coordinates, calls the provider with candidate x/y coordinates, records source-zone flags, and summarizes source-sensitive counts.

The provider interface remains decoupled from local raster access. A later local task can adapt `LocalSourceZoneRasterClassifier` by using a callable that returns the sample output source zone for each candidate point.

## Expected Result

Candidate cells should receive ESA-derived, WMS gap-filled, DEM-only fallback, or mixed-boundary source-zone flags. The assignment summary should count source zones and source-sensitive records without loading raster files or recalculating scoring outputs.

## Actual Result

Candidate-grid source-zone assignment records, provider integration, summary helpers, and synthetic tests were added. PR #50 GitHub Actions CI completed successfully on the checked head commit.

## Metrics

- Candidate source-zone record count.
- ESA-derived candidate source-zone count.
- WMS gap-filled candidate source-zone count.
- DEM-only fallback candidate source-zone count.
- Mixed-boundary candidate source-zone count.
- Source-sensitive candidate source-zone count.
- Dominant source zone.

## CI / Local Test Result

Cloud Agent did not run local commands. GitHub Actions CI completed successfully for PR #50.

## Interpretation

Source-zone assignment is an interpretation metadata connection layer. It links candidate-grid coordinates to a provider result that can be synthetic now and raster-backed in a later local task.

DEM-only fallback remains a model fallback assumption. It is not evidence that surface obstacles are absent.

## Limitations

- No real DEM/DSM/landcover files are loaded.
- No `METADATA_MAP` files are used.
- No raster or GIS dependency is added.
- No map rendering is implemented.
- Candidate scoring, LOS/Fresnel, route scoring, and waypoint scoring are not recalculated by this scaffold.
- This scaffold does not validate terrain accuracy, obstacle-height accuracy, communication performance, or field outcomes.

## Figure/Table Candidacy

Useful as a small paper table showing candidate-grid source-zone counts before later raster-backed scoring integration.

## Public Repository Sensitivity Check

No private absolute path, sensitive coordinate, credential, token, secret, raster data file, `METADATA_MAP` data file, CSV, image, PDF, or QGIS project file is included.

## Follow-up Tasks

- Connect `LocalSourceZoneRasterClassifier` to candidate-grid smoke testing in a local task.
- Pass `CandidateSourceZoneRecord.source_zone` into later candidate scoring or map output integration steps.
- Consider a paper table comparing output subsets by ESA-derived, WMS gap-filled, DEM-only fallback, and mixed-boundary candidate-grid cells.
