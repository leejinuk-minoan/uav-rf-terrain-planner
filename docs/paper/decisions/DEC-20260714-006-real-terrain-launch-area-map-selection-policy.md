# DEC-20260714-006 - Real-Terrain Launch-Area Map and Selection Policy

## Decision

Task 035D will connect the Task 035B production-neutral candidate result to:

```text
renderer-neutral candidate cell polygons
+ WGS84 renderer geometry
+ MGRS-only popup fields
+ deterministic legend and summary
+ optional self-contained local HTML/SVG output
+ candidate-ID-based launch-site selection
```

Task 035D will not implement route search, waypoint generation, minimum altitude, automatic recommendation, browser-to-Python callback infrastructure, external-device integration, or field RF validation.

## Context

Task 035B now provides deterministic `CandidateAnalysisRecord` and `CandidateAnalysisMapFeature` sequences with actual EPSG:5179 candidate centers, explicit exclusion states, score/color projections, optional source-zone states, and Fresnel diagnostics.

Existing map/display scaffolds cannot be used directly as the real-terrain boundary because:

- `build_candidate_cell_map_features(...)` accepts synthetic records and uses placeholder x/y geometry;
- `CandidateCellMapFeature` and `CandidateDisplayRecord` require non-null score and source-zone fields that do not represent excluded or unavailable real-terrain candidates;
- the existing `MapOutputPackage` requires routes, waypoints, and a selected route;
- Task 035B intentionally leaves `candidate_cell_mgrs=None` and `coordinate_display_state=projected_only`.

## Input Authority Decision

Task 035D consumes:

```text
RealTerrainLaunchAreaResult.candidate_records
RealTerrainLaunchAreaResult.candidate_features
```

Record and feature sequences must have equal counts, unique IDs, index-aligned candidate IDs, exact projected center parity, and exact state/color/score/reason/source-zone/diagnostic projection parity.

A mismatch is fatal. Task 035D does not reorder, repair, or pass real data through the synthetic placeholder builder.

## Cell Size Decision

Introduce:

```python
@dataclass(frozen=True)
class RealTerrainLaunchAreaMapConfig:
    candidate_cell_size_m: float
    selected_candidate_id: str | None = None
    include_excluded: bool = True
```

`candidate_cell_size_m` is a positive finite non-boolean value supplied explicitly by the caller. Task 035B does not retain the original candidate spacing, so equality with the analysis spacing is a caller responsibility. The map layer must not infer spacing from arbitrary point distances or raster cells.

## Geometry Decision

Cell polygons are built in EPSG:5179 around the actual candidate feature center.

```text
half-size = candidate_cell_size_m / 2
ring = SW → SE → NE → NW → SW
orientation = counter-clockwise in projected x/y
```

Each of four unique corners is independently projected to WGS84. The first converted corner is reused to close the ring.

Polygons are not clipped to operating radius, raster coverage, NoData, coastline, or source-zone boundaries. Candidate radius/state authority remains center-based Task 035B output.

## Coordinate Decision

```text
EPSG:5179:
  analysis authority, polygon construction, selected point for future route engine

WGS84:
  renderer-internal target, center, and polygon geometry only

MGRS:
  target, candidate popup, and selected launch-site default user-facing coordinates
```

Introduce `Wgs84MapPoint(longitude_deg, latitude_deg)` so storage order is explicit and separate from the current `WGS84Point(lat, lon)` placeholder.

Concrete local conversion uses `pyproj` with `always_xy=True`. MGRS output uses five easting and five northing digits, uppercase, and stripped surrounding whitespace. This is formatting precision, not a terrain-accuracy claim.

No coordinate dependency is added. Existing optional `gis` dependencies remain sufficient for the local implementation.

## Renderer-Neutral Schema Decision

Task 035D introduces separate frozen real-terrain schemas for:

```text
WGS84 renderer point
candidate popup
candidate polygon
map target marker
selection outline style
legend entry
map summary
map package
selected launch-site record
```

Existing `MapStyle`, `ColorClass`, `CandidateAnalysisState`, source-zone enums, and Fresnel diagnostics are reused.

Default popup and selected-record dictionaries do not expose EPSG:5179, WGS84, x/y, or raster row/column values.

## Visual Decision

Base candidate colors reuse `style_for_color_class(...)` exactly.

```text
green/yellow/orange/red: existing styles
excluded: existing gray, opacity 0.5
target: distinct blue marker with white stroke
selected: black outline overlay; base fill unchanged
```

Legend order is:

```text
green, yellow, orange, red, excluded, selected, target
```

Source-zone state and dominant-obstacle diagnostics remain popup interpretation data only and do not change color, score, order, or selectability.

## Visibility Decision

`include_excluded=True` includes all Task 035B candidates in source order.

`include_excluded=False` omits only excluded polygons from the map package. It does not mutate the Task 035B result or full source summary.

A Task 035B partial grid remains partial; the map builder does not invent missing candidates.

## Selection Decision

Selection key:

```text
candidate_id
```

A candidate is selectable only when:

```text
state == valid_scored
candidate_score is present
color_class != excluded
within_operation_radius is true
```

A valid red candidate remains selectable and retains its risk reason.

Use a package-based service:

```python
select_launch_site(result, package, candidate_id) -> SelectedLaunchSiteRecord
```

The service reuses the package popup MGRS and Task 035B projected point. It does not recompute terrain, LOS, Fresnel, score, color, ranking, or coordinates. It never automatically substitutes another candidate.

## Failure Decision

Fatal package errors:

```text
zero source records/features
record/feature mismatch or duplicate IDs
invalid/non-finite geometry
coordinate conversion failure
empty target or candidate MGRS
invalid selected ID
selected hidden or non-selectable candidate
```

Non-fatal package state:

```text
candidates exist but zero selectable
source-zone not requested/unavailable/not applicable
all excluded candidates hidden by config
```

Deterministic warnings include:

```text
no selectable launch-site candidates were produced
no candidate polygons were included by the map configuration
```

## Renderer Decision

Audited options:

- Folium/Leaflet: deferred because tile/offline and callback behavior require additional dependency and integration policy.
- Streamlit: deferred because server/component and UI test scope is broader.
- matplotlib: rejected for the selection milestone because it is static and adds a dependency.
- pure HTML/SVG: selected for Task 035D.

The selected local renderer is self-contained, standard-library-only, tile-free, network-free, and testable as deterministic text. It may provide browser-side visual highlight and candidate-ID display through inline JavaScript, but authoritative Python selection remains the explicit selection service.

The renderer writes only to an explicit path, requires opt-in overwrite, opens no browser automatically, and produces an uncommitted local artifact that may contain WGS84 and MGRS data.

## Task 035D Scope Decision

Create:

```text
src/uav_rf_terrain/coordinate_conversion.py
src/uav_rf_terrain/real_terrain_launch_area_map.py
src/uav_rf_terrain/launch_site_selection.py
src/uav_rf_terrain/local_html_map_renderer.py
examples/local_real_terrain_launch_area_map_smoke.py
tests/test_coordinate_conversion.py
tests/test_real_terrain_launch_area_map.py
tests/test_launch_site_selection.py
tests/test_local_html_map_renderer.py
```

Narrowly update `src/uav_rf_terrain/__init__.py` and documentation only.

No dependency or workflow change is approved. Core tests use fake converters; concrete GIS adapters are lazy imports and require separate local verification.

Task 035D is assigned to a Local Execution Agent, must use TDD, and must keep its PR Draft until GPT Master review and explicit user approval.

## Compatibility Boundary

Unchanged:

```text
Task 035B result fields and semantics
synthetic map/display builders and tests
LOS/Fresnel formulas and dominant-obstacle rules
score weights, strict LOS cap, color thresholds
source-zone non-scoring semantics
route and waypoint costs
preview/report/appendix/CLI contracts
MGRS external-output policy
```

## Paper Boundary

The renderer-neutral package may support later figures showing candidate state/color distributions and selected-site metadata. It is not measured RF evidence, a terrain-accuracy validation, a full link budget, communication-success evidence, reconnaissance-success evidence, or flight-feasibility evidence.

## Product and Deployment Boundary

The HTML/SVG renderer is a local offline development/MVP visualization. Browser-to-Python callbacks, Streamlit, Android/TMMR, map tiles, base maps, remote services, and device integration require separate reviewed tasks.

## Public Repository Sensitivity Check

This decision contains no actual coordinate, private path, raster, generated HTML, screenshot, credential, operational command, external-device command, autopilot command, or flight-control output.
