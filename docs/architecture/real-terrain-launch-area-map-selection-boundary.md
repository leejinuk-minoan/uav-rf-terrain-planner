# Real-Terrain Launch-Area Map and Selection Boundary

## Purpose

This document defines the reviewed Task 035D implementation contract for converting the Task 035B real-terrain candidate-analysis result into a renderer-neutral colored launch-area map package, optional local offline HTML/SVG output, and deterministic candidate-ID-based launch-site selection.

Task 035C is a documentation and code-contract audit only. It does not modify runtime source or tests, perform coordinate conversion, render a map, open GIS data, create generated output, or validate field RF or flight outcomes.

## Verified Baseline

```text
PR #99: merged to main
PR #99 merge commit / latest main: a9886eb12633f27cea3556a8e7b9ab4a142667a1
Issue #98: closed / completed
Issue #100: open
Task 035B source, focused tests, handoff, and EXP-052: present on main
open PRs before Task 035C: none
```

## Current Runtime Audit

### Task 035B authority

The next implementation consumes the following immutable Task 035B outputs:

```text
RealTerrainLaunchAreaResult.candidate_records
RealTerrainLaunchAreaResult.candidate_features
```

`candidate_records` is authoritative for:

```text
candidate order
candidate ID
candidate projected point
candidate state
reason
2D and optional 3D distance
within-operation-radius state
terrain endpoint fields
CandidateScore availability and values
color class
source-zone availability and values
Fresnel diagnostics
```

`candidate_features` is the rendering-input projection of the same records and is authoritative for:

```text
feature ID
actual projected center x/y
geometry CRS label
style
primitive score projection
renderer-oriented state and metadata projection
```

Task 035D must not route real output through `build_candidate_cell_map_features(...)`. That function accepts `SyntheticCandidateRecord` and intentionally preserves the synthetic regression geometry:

```text
x_m = index * 500.0
y_m = 0.0
```

### Existing map scaffold

`map_outputs.py` provides reusable `MapStyle` and `style_for_color_class(...)` values. Its current `MapOutputPackage`, `CandidateCellMapFeature`, route feature, waypoint feature, and builders are synthetic-era scaffolds. They require non-null score fields and route selection and do not represent Task 035B exclusion states or source-zone availability states.

Task 035D reuses `MapStyle` and `style_for_color_class(...)` but introduces separate real-terrain candidate map schemas. Existing synthetic schemas and builders remain unchanged.

### Existing display and preview scaffold

`CandidateDisplayRecord` requires:

```text
non-empty candidate_cell_mgrs
finite overall and shielding scores
string source_zone
boolean source_sensitive
```

Task 035B correctly permits excluded candidates with no score, `source_zone=None`, and `source_sensitive=None`. It also distinguishes `not_requested`, `unavailable`, and `not_applicable`. Therefore the synthetic display bundle cannot be used as the production real-terrain popup boundary.

Task 035D introduces a separate popup record with optional score and source-zone fields. Existing display, preview, report, appendix, and CLI contracts remain unchanged.

### Coordinate policy

The repository already fixes:

```text
user-facing input/output: MGRS
internal computation: EPSG:5179, WGS84, local x/y, raster row/col
```

Current `coordinates.py` contains `LocalPoint`, `WGS84Point`, and an optional MGRS-to-WGS84 helper. It does not provide the complete EPSG:5179-to-WGS84 and EPSG:5179-to-MGRS output path required by the map package.

### Dependency state

The base dependency list is empty. The optional `gis` extra already contains:

```text
pyproj>=3.6
mgrs>=1.5
```

No Folium, Streamlit, matplotlib, GeoPandas, Shapely, or concrete map renderer dependency is declared.

## Task 035D Endpoint

```text
RealTerrainLaunchAreaResult
+ explicit map configuration
+ EPSG:5179-to-WGS84 converter
+ EPSG:5179-to-MGRS converter
→ validate record/feature parity
→ deterministic projected candidate cell polygons
→ renderer-internal WGS84 geometry
→ MGRS-only user-facing popup properties
→ immutable renderer-neutral map package
→ optional self-contained local HTML/SVG renderer
→ candidate-ID selection service
→ immutable selected launch-site record
```

Task 035D does not include:

```text
route search
three route alternatives
waypoint generation
minimum-altitude integration
browser-to-Python callback server
automatic launch-site recommendation
Top-N replacement
field RF validation
external device integration
autopilot or flight control
```

## Input and Parity Contract

### Result validation

Before any coordinate conversion or polygon creation, Task 035D validates:

1. `result` is `RealTerrainLaunchAreaResult`.
2. `candidate_records` is non-empty.
3. `candidate_features` is non-empty.
4. Record and feature counts are equal.
5. Candidate IDs are non-empty and unique in each sequence.
6. Candidate IDs match by index.
7. Each feature ID is non-empty and unique.
8. `feature.geometry_crs == "EPSG:5179"`.
9. `feature.x_m/y_m` exactly equal the record candidate point x/y.
10. Feature state, color, radius flag, reason, source-zone fields, and diagnostics equal the record projection.
11. For scored records, feature overall and shielding scores exactly equal `record.candidate_score` values.
12. For excluded records, feature score projections are `None` and color is `ColorClass.EXCLUDED`.
13. `candidate_cell_mgrs is None` and `coordinate_display_state == "projected_only"` at the Task 035B boundary.

Any mismatch is fatal `RealTerrainLaunchAreaMapError`. Task 035D does not repair or silently reorder input.

## Map Configuration

```python
@dataclass(frozen=True)
class RealTerrainLaunchAreaMapConfig:
    candidate_cell_size_m: float
    selected_candidate_id: str | None = None
    include_excluded: bool = True
```

Validation:

| Field | Contract |
|---|---|
| `candidate_cell_size_m` | positive finite non-boolean float |
| `selected_candidate_id` | `None` or non-empty stripped string |
| `include_excluded` | bool |

The same cell size is used for every candidate.

Task 035B does not retain `candidate_spacing_m` in `RealTerrainLaunchAreaResult`. Task 035D must not infer spacing from arbitrary candidate distances or raster geometry. The caller is responsible for passing the same value used by the Task 035B analysis config. A later backward-compatible result/config provenance enhancement requires a separate reviewed task.

The map builder does not mutate the result, config, records, features, popup data, or converter inputs.

## Candidate Cell Geometry

### Authority CRS

```text
cell construction CRS: EPSG:5179
cell center: CandidateAnalysisMapFeature.x_m / y_m
cell side length: RealTerrainLaunchAreaMapConfig.candidate_cell_size_m
half size: candidate_cell_size_m / 2
```

### Projected corner order

For center `(x, y)` and half-size `h`, the four unique corners are:

```text
southwest = (x - h, y - h)
southeast = (x + h, y - h)
northeast = (x + h, y + h)
northwest = (x - h, y + h)
```

The authoritative closed ring is:

```text
southwest
southeast
northeast
northwest
southwest
```

This is counter-clockwise in projected x/y space. The first converted WGS84 corner is reused to close the ring; the southwest converter is not called twice.

Each unique projected corner is converted individually. Task 035D must not use:

```text
meter-to-degree constants
manual latitude-dependent approximation
candidate index multiplied by spacing
raster row/column polygons
sampled-cell-center replacement geometry
```

The candidate requested projected point remains the center authority, including candidates whose center lies outside raster coverage or on NoData.

### Radius and clipping

The polygon may extend beyond the operating circle. The authoritative radius state remains the Task 035B center/3D analysis state.

Task 035D does not clip cell polygons to:

```text
operating circle
raster extent
NoData footprint
coastline
source-zone boundary
```

Clipping would create a new visual geometry interpretation and is deferred.

### Visibility

```text
include_excluded=True:
  include all Task 035B candidates in source order

include_excluded=False:
  omit only state != valid_scored / ColorClass.EXCLUDED polygons
  preserve source result, source summary, and source warnings unchanged
```

`outside_operating_radius`, `outside_raster_extent`, `terrain_nodata`, surface, coincident, profile, and analysis exclusions share the existing excluded gray style but retain distinct state and reason in popup data when visible.

A Task 035B result created with `include_out_of_radius=False` naturally contains a partial grid. Task 035D does not invent omitted cells.

## Coordinate Conversion Contract

### Immutable renderer point

```python
@dataclass(frozen=True)
class Wgs84MapPoint:
    longitude_deg: float
    latitude_deg: float
```

Validation:

```text
longitude_deg: finite and within [-180, 180]
latitude_deg: finite and within [-90, 90]
```

Storage and polygon order are longitude first, latitude second. This avoids ambiguity with the current `WGS84Point(lat, lon)` placeholder.

### Converter protocols

```python
class ProjectedToWgs84Converter(Protocol):
    def __call__(self, point: LocalPoint) -> Wgs84MapPoint:
        ...

class ProjectedToMgrsConverter(Protocol):
    def __call__(self, point: LocalPoint, *, precision: int) -> str:
        ...
```

Task 035D concrete local adapters use EPSG:5179 as source CRS and WGS84/EPSG:4326 as destination CRS. `pyproj.Transformer` must use `always_xy=True` so input is easting/x then northing/y and output is longitude then latitude.

The MGRS adapter converts through WGS84 and calls the MGRS library using latitude then longitude as required by that library. Axis order must be covered by tests.

### MGRS precision and normalization

Task 035D uses:

```text
precision: 5 digits each for easting and northing
case: uppercase
leading/trailing whitespace: removed
empty output: fatal
```

Five-digit MGRS is a coordinate formatting precision, not a claim that 90 m or proxy terrain data has 1 m physical accuracy. Popup interpretation must preserve the terrain-data limitation.

### Deterministic converter call order

After parity and config validation:

1. Convert target projected point to WGS84 once.
2. Convert target projected point to MGRS once with precision 5.
3. Iterate included candidates in Task 035B order.
4. For each included candidate, convert the candidate center to WGS84 once.
5. Convert the candidate center to MGRS once with precision 5.
6. Convert unique projected corners in SW, SE, NE, NW order, once each.
7. Reuse the converted SW point to close the ring.

Thus each included candidate uses:

```text
center WGS84 calls: 1
center MGRS calls: 1
corner WGS84 calls: 4
corner MGRS calls: 0
```

Selection from an already-built package reuses popup MGRS and performs no coordinate conversion.

Any target, center, or corner conversion failure is fatal for the whole package. Candidate omission with a warning is not allowed because complete geometry/popup parity is required for the included set.

## Renderer-Neutral Schemas

All schemas are frozen dataclasses.

### Popup record

```python
@dataclass(frozen=True)
class RealTerrainCandidatePopup:
    candidate_id: str
    candidate_cell_mgrs: str
    external_coordinate_format: str
    user_coordinate_field: str
    state: CandidateAnalysisState
    color_class: ColorClass
    color_name: str
    selectable: bool
    overall_score: float | None
    shielding_stability_score: float | None
    distance_3d_m: float | None
    within_operation_radius: bool
    candidate_reason: str
    source_zone: TerrainSourceZone | None
    source_zone_state: SourceZoneAvailability
    source_sensitive: bool | None
    source_zone_reason: str
    fresnel_diagnostics: CandidateFresnelDiagnostics | None
```

`external_coordinate_format == "MGRS"` and `user_coordinate_field == "candidate_cell_mgrs"`.

The default user-facing dictionary contains no:

```text
x_m
y_m
EPSG:5179 values
WGS84 longitude/latitude
raster row/col
sampled cell center
```

Excluded candidates retain `None` scores. Source-zone `None` and optional sensitivity values are preserved rather than defaulted.

### Candidate polygon

```python
@dataclass(frozen=True)
class RealTerrainCandidatePolygon:
    feature_id: str
    candidate_id: str
    center_wgs84: Wgs84MapPoint
    polygon_wgs84: tuple[Wgs84MapPoint, ...]
    state: CandidateAnalysisState
    color_class: ColorClass
    style: MapStyle
    selectable: bool
    is_selected: bool
    popup: RealTerrainCandidatePopup
```

Validation:

```text
polygon length == 5
first point == last point
four unique pre-closure points
candidate_id matches popup
state/color/selectable match popup
style matches existing color style
is_selected implies selectable
```

### Target marker

```python
@dataclass(frozen=True)
class RealTerrainTargetMarker:
    marker_id: str
    target_mgrs: str
    position_wgs84: Wgs84MapPoint
    style: MapStyle
    label: str
```

Required values:

```text
marker_id = "target-marker"
label = "target"
style = MapStyle(
    color_name="target",
    fill_hex="#1f77b4",
    stroke_hex="#ffffff",
    opacity=1.0,
)
```

Target MGRS is the only default user-facing target coordinate.

### Selection style

```python
@dataclass(frozen=True)
class MapSelectionStyle:
    stroke_hex: str = "#000000"
    stroke_width: float = 3.0
    opacity: float = 1.0
```

The selected outline is an overlay. It does not replace the base candidate fill or color class.

### Legend

```python
@dataclass(frozen=True)
class LaunchAreaLegendEntry:
    key: str
    label: str
    fill_hex: str
    stroke_hex: str
    opacity: float
    count: int
```

Fixed legend order:

```text
green
yellow
orange
red
excluded
selected
target
```

Color entries reuse `style_for_color_class(...)`. `selected` uses the selection outline and count 0 or 1. `target` uses the target style and count 1. Color counts refer to polygons included in the package, not hidden excluded source records.

### Summary

```python
@dataclass(frozen=True)
class RealTerrainLaunchAreaMapSummary:
    source_candidate_count: int
    rendered_candidate_count: int
    selectable_candidate_count: int
    selected_candidate_count: int
    hidden_excluded_count: int
    color_counts: tuple[tuple[str, int], ...]
    state_counts: tuple[tuple[str, int], ...]
    source_zone_state_counts: tuple[tuple[str, int], ...]
```

Ordering follows the existing enum declaration order. Source state counts describe the full Task 035B result. Rendered color counts describe included polygons.

### Package

```python
@dataclass(frozen=True)
class RealTerrainLaunchAreaMapPackage:
    scenario_name: str
    target_marker: RealTerrainTargetMarker
    candidate_polygons: tuple[RealTerrainCandidatePolygon, ...]
    selected_candidate_id: str | None
    selection_style: MapSelectionStyle
    legend: tuple[LaunchAreaLegendEntry, ...]
    summary: RealTerrainLaunchAreaMapSummary
    warnings: tuple[str, ...]
```

Candidate polygon order is filtered Task 035B order. Warnings begin with Task 035B warnings unchanged, followed by deterministic map-package warnings without duplicates.

## Visual and Popup Policy

### Base styles

```text
green/yellow/orange/red: existing style_for_color_class values
excluded: existing gray #808080 with opacity 0.5
target: blue fill, white stroke
selected: black 3 px outline overlay
```

Source-zone state and dominant-obstacle diagnostics do not alter fill, score, order, or selectability.

No Top-N filtering or automatic best-site selection is introduced.

### Selectability

A candidate is selectable if and only if:

```text
state is CandidateAnalysisState.VALID_SCORED
candidate_score is not None
color_class is not ColorClass.EXCLUDED
within_operation_radius is True
```

A valid red candidate remains selectable. Its color and risk reason remain visible.

Map visibility and selectability are independent. Excluded candidates may be visible but are never selectable.

## Selection Contract

### Package-based API

```python
def select_launch_site(
    result: RealTerrainLaunchAreaResult,
    package: RealTerrainLaunchAreaMapPackage,
    candidate_id: str,
) -> SelectedLaunchSiteRecord:
    ...
```

The package-based API reuses the already-converted MGRS popup value and performs no terrain, LOS, Fresnel, score, color, ranking, or coordinate recomputation.

### Selected record

```python
@dataclass(frozen=True)
class SelectedLaunchSiteRecord:
    candidate_id: str
    launch_site_mgrs: str
    external_coordinate_format: str
    user_coordinate_field: str
    projected_point: LocalPoint
    color_class: ColorClass
    overall_score: float
    shielding_stability_score: float
    distance_3d_m: float
    candidate_reason: str
    source_zone: TerrainSourceZone | None
    source_zone_state: SourceZoneAvailability
    source_sensitive: bool | None
    source_zone_reason: str
    fresnel_diagnostics: CandidateFresnelDiagnostics | None
```

Required external fields:

```text
external_coordinate_format = "MGRS"
user_coordinate_field = "launch_site_mgrs"
```

`projected_point` is retained for the future route engine but excluded from the default user-facing dictionary.

### Deterministic failures

The selection service rejects:

```text
blank candidate ID
unknown candidate ID
duplicate candidate IDs in result or package
record/feature/package mismatch
candidate omitted from the package
non-selectable or excluded candidate
missing or empty MGRS popup value
package selected ID inconsistent with requested ID
```

Only one active selection is allowed. `selected_candidate_id` is either `None` or exactly one selectable candidate ID.

Selection does not choose another candidate and does not automatically select a green or highest-score candidate.

## Zero, Partial, and Warning Policies

### Zero source candidates

A result with zero candidate records or zero candidate features is fatal `RealTerrainLaunchAreaMapError`. There is no candidate layer to build.

### Candidates but zero selectable

The map package remains valid. When excluded candidates are visible they are rendered. The package uses:

```text
selected_candidate_id = None
warning = "no selectable launch-site candidates were produced"
```

When `include_excluded=False`, an all-excluded source result may produce an empty polygon tuple. The target, source summary, and warnings remain valid, with an additional warning:

```text
"no candidate polygons were included by the map configuration"
```

### Coordinate failure

Any required target, included center, or included corner WGS84/MGRS conversion failure is fatal and chained as `RealTerrainLaunchAreaMapError`.

### Source-zone unavailable

`not_requested`, `unavailable`, and `not_applicable` are preserved in popup data and are not fatal.

### Selected ID

Unknown, hidden, or non-selectable selected IDs are fatal. The package does not silently clear an invalid requested selection.

## Renderer Decision

### Audited options

| Option | Offline correctness | Selection support | CI testability | Dependency impact | Decision |
|---|---|---|---|---|---|
| Folium/Leaflet HTML | tiles are normally network-backed; offline tile policy needed | browser click possible but Python callback needs more integration | moderate | new dependency | defer |
| Streamlit + map component | local server and component callback possible | strong | weak without UI environment | multiple new dependencies | defer |
| matplotlib static preview | offline | no candidate click workflow | strong | new dependency | reject for MVP selection |
| pure HTML/SVG | self-contained and no tile/network requirement | client-side highlight and candidate ID display possible | strong via deterministic text tests | standard library only | **selected** |

### Task 035D local renderer

Task 035D includes an optional self-contained HTML/SVG renderer in a separate module. The renderer:

```text
consumes only RealTerrainLaunchAreaMapPackage
imports no concrete GIS library
uses no base tile or external network resource
renders polygons, target, legend, popup/side-panel text, and selected outline
uses data-candidate-id attributes
allows browser-side visual click highlighting and ID display
writes only to an explicit output path
requires force=True to overwrite an existing file
opens no browser automatically
```

Browser-side click state is not the authoritative Python selection record. The user/controller passes the displayed candidate ID to `select_launch_site(...)`. A browser-to-Python callback server or Streamlit component is deferred to a later UI task.

Generated HTML contains renderer WGS84 geometry and MGRS popup data. It is a local potentially sensitive artifact, is excluded from Git, and must not be attached to public records without separate review.

Renderer unavailability is not a package error because the renderer uses only the Python standard library. File permission, invalid path, or overwrite-policy failures are renderer-specific errors and do not invalidate the package.

## Task 035D Source Scope

Target agent:

```text
Local Execution Agent — Codex or Claude Code
```

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

Narrow update:

```text
src/uav_rf_terrain/__init__.py
README.md
Task 035D handoff / EXP / indexes
```

No dependency change is approved. The existing optional `gis` extra is used for local concrete coordinate adapters. Core map-package, selection, and HTML/SVG tests use fake converters and standard-library behavior so standard CI does not require GIS packages.

Task 035D must use TDD and keep its PR Draft until GPT Master review and explicit user approval.

## Protected Runtime Scope

Do not modify without an evidenced blocker and explicit scope review:

```text
src/uav_rf_terrain/real_terrain_candidate_analysis.py
src/uav_rf_terrain/geotiff_terrain_data.py
src/uav_rf_terrain/profile.py
src/uav_rf_terrain/los.py
src/uav_rf_terrain/fresnel.py
src/uav_rf_terrain/fresnel_diagnostics.py
src/uav_rf_terrain/scoring.py
src/uav_rf_terrain/classification.py
src/uav_rf_terrain/scenario_outputs.py
src/uav_rf_terrain/map_outputs.py
src/uav_rf_terrain/candidate_display_outputs.py
src/uav_rf_terrain/candidate_display_preview.py
src/uav_rf_terrain/preview_report.py
src/uav_rf_terrain/preview_cli.py
src/uav_rf_terrain/routing.py
src/uav_rf_terrain/waypoints.py
.github/workflows/
pyproject.toml
lock files
```

Preserve:

```text
Task 035B candidate order, state, score, color, and actual geometry
dsm_fresnel_score == average_fresnel_score
existing score weights and strict LOS cap
existing color thresholds
source-zone non-scoring semantics
route and waypoint costs
synthetic placeholder builder regression
preview/report/appendix/CLI behavior
MGRS external-output policy
```

## Test Matrix for Task 035D

At minimum:

```text
map config positive finite non-boolean cell size
result/record/feature type validation
record/feature count and ID parity
duplicate IDs
state/color/score/reason/source/diagnostic parity
actual center geometry; no placeholder values
projected SW/SE/NE/NW/closed-ring order
counter-clockwise projected ring
four unique corner converter calls
center and target converter call order/count
WGS84 longitude/latitude range and axis order
MGRS precision 5 and non-empty uppercase output
converter failure fatal
include_excluded true/false
partial grid order preservation
zero source candidates fatal
zero selectable warning
all-excluded hidden polygon warning
existing color style reuse
legend order and counts
target and selected visual metadata
red valid candidate selectable
unknown/blank/hidden/excluded selection failures
selected record exact reuse without recomputation
no internal coordinates in default popup/selected dictionaries
source-zone unavailable preservation
dominant diagnostics popup-only behavior
package builder writes no file
HTML/SVG deterministic offline output
explicit output and force-overwrite behavior
HTML contains no external script, tile, font, or network URL
no browser auto-open
no committed generated artifact
existing map/display/preview/report/CLI regressions
package import does not eagerly import pyproj or mgrs
```

## Interpretation Limits

The map displays Task 035B offline terrain/surface-obstacle risk proxy results. It is not a measured coverage map, RF link budget, terrain-accuracy certificate, communication guarantee, reconnaissance guarantee, flight-feasibility determination, or airspace approval result.

Candidate polygons visualize center-based analysis cells. Polygon area does not mean every point inside the cell was separately sampled or validated.

## Public Repository Sensitivity Check

This contract includes no actual coordinate, private path, GIS raster, generated HTML, screenshot, QGIS project, credential, operational command, external-device command, autopilot command, or flight-control output.
