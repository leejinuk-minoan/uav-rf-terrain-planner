# EXP-20260710-006 - Manual QGIS Overlay Verification

## Experiment Purpose

Record a direct QGIS visual review of the local DEM, temporary DSM proxy, surface-delta proxy, and aligned landcover raster.

## Input Data

Four local ignored raster mosaics under `METADATA_MAP/`: DEM, temporary DSM proxy, surface delta, and landcover. No raster is committed.

## Method

QGIS 3.40.14 LTR was launched with all four raster files. The QGIS window was captured directly for visual inspection because another full-screen application obscured normal desktop capture. The layer tree, project CRS indicator, nationwide footprint, coverage boundaries, and default rendering were reviewed.

## Expected Result

All layers should load under `EPSG:5179`, share a common footprint, and permit visual comparison of coastline, NoData boundaries, tile seams, flat areas, and landcover alignment across zoom levels.

## Actual Result

QGIS overlay status: needs manual follow-up.

All four layers loaded and rendered, the project displayed `EPSG:5179`, and the nationwide footprints appeared colocated. Rectangular background or NoData blocks were visible near outer and coastal coverage. Opaque grayscale rendering and incomplete layer toggling prevented conclusive seam, flat-area, landcover, and multi-zoom grid assessment.

## Metrics

- Raster layers loaded: 4 of 4
- Project CRS displayed: `EPSG:5179`
- Overview footprint alignment: observed
- Layer-by-layer toggle comparison: incomplete
- Multi-level zoom comparison: incomplete
- Local screenshots generated: yes
- Screenshot files committed: no

## CI / Local Test Result

Local repository verification and GitHub Actions status are recorded in the Task 018C PR after documentation checks complete.

## Interpretation

The QGIS session confirms that the complete layer set can be loaded and viewed together. It does not yet justify a passed visual-alignment verdict because several required comparisons remain incomplete and rectangular coverage blocks require classification.

## Limitations

The review used default symbology in a partially obstructed desktop environment. It did not validate source accuracy, measured surface height, or any field outcome.

## Figure/Table Candidacy

The local screenshots are verification evidence only and are not committed. A later sanitized QGIS figure may be considered after manual follow-up and separate approval.

## Public Repository Sensitivity Check

No screenshot, image, QGIS project, private absolute path, sensitive coordinate, or raster file is included.

## Follow-up Tasks

Repeat with explicit transparency and distinct symbology, inspect multiple zoom levels and representative boundaries, and record whether visible rectangles are expected NoData footprints or processing artifacts.
