# Task 035D Real-Terrain Map and Selection Implementation

## Current Task

Task 035D adds a renderer-neutral map package, optional lazy coordinate adapters,
candidate-ID selection, and deterministic local HTML/SVG rendering for a completed
`RealTerrainLaunchAreaResult`. It does not change terrain analysis, scoring, route,
waypoint, preview, or CLI behavior.

## Implemented Boundary

- Actual Task 035B record/feature parity is validated before conversion.
- EPSG:5179 centers produce square cell rings; WGS84 is renderer-internal only.
- MGRS is the default user-facing candidate and target coordinate field.
- The package is immutable; selection accepts an unselected or matching selected package,
  returns an immutable MGRS-facing record, and does not recompute terrain, LOS, Fresnel,
  score, color, or coordinate conversion.
- HTML/SVG is self-contained, deterministic, uses a fixed six-decimal schematic viewport,
  escapes data-derived content, uses the reviewed CSP, is explicit-path only, and does not
  open a browser.

## Safety and Limits

- Optional `pyproj` and `mgrs` imports remain lazy.
- Generated HTML, GIS data, private paths, and operational coordinates are not committed.
- The local smoke example consumes an application-prepared map package and does not create
  a terrain analysis result or publish coordinates.
- The output remains a research/education/simulation visualization, not RF, flight, or approval evidence.
