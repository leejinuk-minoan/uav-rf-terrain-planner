# EXP-20260714-054 - Real-Terrain Launch-Area Map and Selection Implementation

## Purpose

Record the Task 035D implementation of the reviewed renderer-neutral map package,
candidate-ID selection boundary, lazy coordinate adapters, and offline HTML/SVG output.

## Scope

The implementation consumes Task 035B results without modifying LOS, Fresnel,
scoring, classification, route, waypoint, preview, or CLI contracts. Core tests use
in-memory fake converters. They cover renderer viewport edge cases, deterministic
formatting, package-selection lifecycle, explicit file overwrite policy, and inert
escaping of script-like input. No GIS raster or generated HTML is committed.

## Implemented Output Boundary

The map package retains Task 035B candidate state, color, score projection, source-zone,
and diagnostic metadata after parity validation. Its SVG projection is renderer-only;
EPSG:5179 remains the analysis and polygon-construction authority, while MGRS is the
default user-facing coordinate. Browser clicks are transient preview only and do not
create a Python selected-site record.

## Local Result

The amendment-focused coordinate, map, selection, and renderer tests passed 32 cases;
the full local suite passed 863 cases. `compileall`, Ruff, mypy, and diff validation
also passed. This is source-level verification only: no browser automation, actual GIS
adapter smoke, or real-data rendering was executed.

## Interpretation Limit

Map polygons and SVG are deterministic visualization artifacts for an offline terrain
and surface-obstacle risk proxy. They are not measured RF coverage, terrain accuracy,
communication-success, flight-feasibility, or airspace-approval evidence.
