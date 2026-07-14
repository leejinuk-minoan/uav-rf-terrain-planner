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

The GPT Master review amendment additionally fixes:

```text
selection from an initially unselected package
deterministic WGS84-to-SVG viewport projection and zero-span rules
HTML/attribute escaping and JavaScript data safety
package-authoritative selection versus transient browser preview
```

Task 035D will not implement route search, waypoints, minimum altitude, automatic recommendation, browser-to-Python callback infrastructure, external-device integration, autopilot, flight control, or field RF validation.

## Context

Task 035B provides ordered `CandidateAnalysisRecord` and `CandidateAnalysisMapFeature` sequences with actual EPSG:5179 candidate centers, explicit exclusion states, score/color projections, optional source-zone states, and Fresnel diagnostics.

Existing synthetic map/display scaffolds cannot serve as the real-terrain boundary because:

- the synthetic candidate builder uses placeholder geometry;
- existing display types require non-null scores and concrete source-zone values;
- existing map packages require route/waypoint state;
- Task 035B intentionally leaves user-facing MGRS unpopulated at its projected engine boundary.

The original Task 035C contract selected a standard-library HTML/SVG renderer and package-based selection service. GPT Master review identified three ambiguities: initial `None` selection, unspecified SVG viewport math, and unsafe/undefined HTML click handling. This amendment resolves only those items and preserves the previously reviewed runtime, coordinate, scoring, and dependency boundaries.

## Input Authority Decision

Task 035D consumes:

```text
RealTerrainLaunchAreaResult.candidate_records
RealTerrainLaunchAreaResult.candidate_features
```

Record and feature sequences must have equal non-zero counts, unique IDs, index-aligned candidate IDs, exact projected center parity, and exact state/color/score/reason/source-zone/diagnostic projection parity.

Any mismatch is fatal. Task 035D does not reorder, repair, or pass real output through the synthetic placeholder builder.

## Cell Size and Geometry Decision

Introduce:

```python
@dataclass(frozen=True)
class RealTerrainLaunchAreaMapConfig:
    candidate_cell_size_m: float
    selected_candidate_id: str | None = None
    include_excluded: bool = True
```

`candidate_cell_size_m` is explicitly supplied, positive, finite, and non-boolean. Equality with the original Task 035B candidate spacing is the caller's responsibility; Task 035D does not infer it.

Cell polygons are constructed around the actual candidate center in EPSG:5179:

```text
half-size = candidate_cell_size_m / 2
ring = SW → SE → NE → NW → SW
orientation = projected counter-clockwise
```

Each unique corner is converted separately to WGS84 and SW is reused for closure. Polygons are not clipped to operating radius, raster coverage, NoData, coastline, or source-zone boundaries.

## Coordinate Decision

```text
EPSG:5179:
  analysis authority, polygon construction, future route-engine selected point

WGS84:
  renderer-internal target, center, and polygon geometry

MGRS:
  target, candidate popup, and selected launch-site default user-facing coordinates
```

Use an explicit `Wgs84MapPoint(longitude_deg, latitude_deg)`. Concrete local conversion uses `pyproj` with `always_xy=True`; MGRS output uses five digits for easting and northing, uppercase, stripped whitespace, and non-empty validation.

No new dependency is added. Existing optional `pyproj` and `mgrs` dependencies remain the only concrete coordinate adapters approved for local validation.

## Renderer-Neutral Schema Decision

Task 035D introduces frozen real-terrain schemas for:

```text
Wgs84MapPoint
candidate popup
candidate polygon
map target marker
selection outline style
legend entry
map summary
map package
selected launch-site record
LocalHtmlMapRenderConfig
```

Existing `MapStyle`, `ColorClass`, `CandidateAnalysisState`, source-zone enums, and Fresnel diagnostics are reused.

Default popup and selected-record dictionaries do not expose EPSG:5179, WGS84, x/y, raster row/col, or sampled-cell-center fields. Excluded candidates retain `None` scores and optional source-zone fields.

## Visual and Visibility Decision

Base candidate styles reuse `style_for_color_class(...)`.

```text
green/yellow/orange/red: existing styles
excluded: existing gray, opacity 0.5
target: blue marker with white stroke
package-selected: black 3 px outline overlay
transient browser preview: separate preview class/outline
```

Legend order is:

```text
green, yellow, orange, red, excluded, selected, target
```

`include_excluded=True` includes all Task 035B candidates in source order. `include_excluded=False` omits only excluded polygons without changing the source result or full source summary. A partial source grid remains partial.

Source-zone and dominant-obstacle fields remain popup-only interpretation data and do not alter score, color, order, or selectability.

## Selectability Decision

A candidate is selectable only when:

```text
state == valid_scored
candidate_score is present
color_class != excluded
within_operation_radius is true
```

A valid red candidate remains selectable and retains its risk reason.

# Master Review Amendment A — Selection Lifecycle Decision

## Map package selected state

When `RealTerrainLaunchAreaMapConfig.selected_candidate_id is None`:

```text
all polygons are unselected
package.selected_candidate_id is None
summary.selected_candidate_count is 0
legend selected count is 0
```

When a selected ID is configured:

```text
the candidate must exist in the source result
the candidate must be included in the package
the candidate must be selectable
exactly one polygon is selected
package.selected_candidate_id matches the selected polygon
summary.selected_candidate_count is 1
legend selected count is 1
```

Unknown, hidden, excluded, or non-selectable config-selected IDs are fatal.

## Selection service state machine

Use:

```python
select_launch_site(result, package, candidate_id) -> SelectedLaunchSiteRecord
```

Exact decisions:

```text
package selected ID is None:
  selecting an included selectable candidate succeeds

package selected ID equals requested candidate:
  selection succeeds

package selected ID is a different non-None candidate:
  conflicting package selection error
```

The service does not mutate the package. It returns only an immutable selected record. A controller may rebuild the package with the selected ID to synchronize the package-selected outline, summary, and legend.

Recommended lifecycle:

```text
build unselected package
obtain candidate_id through browser/controller
create SelectedLaunchSiteRecord through Python service
optionally rebuild selected package
rerender authoritative selected outline and counts
```

The service reuses popup MGRS and the Task 035B projected point and performs no analysis or coordinate recomputation.

## Selection test decision

Task 035D tests must cover unselected success, matching-selected success, conflicting-selected failure, package immutability, popup MGRS reuse, one selected polygon after rebuild, zero selected counts for a `None` package, and fatal unknown/hidden/excluded/non-selectable config-selected IDs.

# Master Review Amendment B — SVG Viewport Decision

## Renderer config

```python
@dataclass(frozen=True)
class LocalHtmlMapRenderConfig:
    width_px: int = 1000
    height_px: int = 800
    padding_px: int = 40
```

`width_px` and `height_px` are positive non-boolean integers. `padding_px` is a non-negative non-boolean integer. Twice the padding must be smaller than both dimensions.

## Bounds and local projection

Viewport bounds use all included candidate polygon WGS84 ring points plus the target marker. Hidden candidate geometry is excluded; the target is always included.

```text
reference longitude = mean of unique bound-input longitude values
reference latitude = mean of unique bound-input latitude values
```

Renderer-only local display coordinates are:

```python
x_local = radians(lon - reference_lon) * cos(radians(reference_lat))
y_local = radians(lat - reference_lat)
```

This transform is schematic display geometry, not analysis, distance, cell-size, or geodetic measurement authority.

If the longitude span exceeds 180 degrees, raise `LocalHtmlMapRendererError`; do not unwrap silently.

## Aspect fit and zero spans

```text
usable_width = width_px - 2 * padding_px
usable_height = height_px - 2 * padding_px
```

When both spans are non-zero, use the smaller x/y scale and center the fitted result inside the padded viewport. SVG y is inverted.

When x span alone is zero, center x and fit y. When y span alone is zero, center y and fit x. When both spans are zero, place all points at the viewport center without division.

A target-only package is valid and uses the both-zero-span behavior.

## Determinism decision

```text
viewBox = 0 0 width_px height_px
candidate SVG order = package order
target rendered after candidates
legend and side panel follow contract order
geometry coordinates = fixed 6 decimals
-0.000000 becomes 0.000000
UTF-8, newline \n, final newline
```

Task 035D tests must cover formulas, bounds, aspect ratio, y inversion, one- and two-dimensional zero spans, target-only rendering, antimeridian rejection, element order, six-decimal formatting, negative-zero normalization, and repeated-output determinism.

# Master Review Amendment C — HTML and JavaScript Safety Decision

## Escaping

Every data-derived HTML text and attribute value uses escaping equivalent to:

```python
html.escape(value, quote=True)
```

This includes scenario, candidate ID, candidate/target MGRS, candidate/source reasons, diagnostics, warnings, legend text, side-panel text, titles, and `data-candidate-id`.

## JavaScript restrictions

```text
no raw data interpolation into executable JavaScript
no data-derived innerHTML assignment
no eval
no Function constructor
no document.write with package data
no raw package JSON inside script
no data-derived inline event handler
no external script/font/tile/image/network URL
```

DOM updates use `textContent`, `classList`, and `dataset` against already-rendered escaped DOM values.

Include the exact CSP:

```text
default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; img-src data:;
```

## Click-state decision

Three states are distinct:

```text
package-authoritative selection
transient browser preview
Python SelectedLaunchSiteRecord
```

Package selection controls initial selected outline and static summary/legend selected counts.

A selectable click may show details and a `preview only` transient outline and expose candidate ID to a controller. It does not mutate the package, change static counts, create a selected record, or claim Python selection succeeded.

A non-selectable/excluded click may show details and exclusion reason but cannot receive the selectable preview class. Clearing preview restores the package-selected outline or the unselected state.

## Security test decision

Task 035D uses malicious strings containing script tags, closing-script text, quotes, apostrophes, ampersands, angle brackets, and attribute-breaking text. Tests require escaped inert output, no closing-script or event-handler injection, no data-derived `innerHTML`, safe candidate-ID attributes, exact CSP, no external resources, immutable counts, separate package/preview state, and no browser-created Python selected record.

## Failure Decision

Fatal package or selection errors include:

```text
zero source records/features
record/feature mismatch or duplicate IDs
invalid or non-finite geometry
required coordinate conversion failure
empty target or candidate MGRS
invalid config-selected ID
selected hidden/excluded/non-selectable candidate
conflicting non-None package selection
antimeridian span over 180 degrees
invalid renderer dimensions or padding
```

Non-fatal states include zero selectable candidates, source-zone unavailable/not requested/not applicable, and all excluded candidates hidden by config.

## Renderer and File Decision

The selected renderer remains self-contained, standard-library-only, tile-free, network-free, and testable as deterministic text. It writes only to an explicit path, requires opt-in overwrite, opens no browser automatically, and produces an uncommitted local potentially sensitive artifact containing WGS84/MGRS data.

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

Narrowly update `src/uav_rf_terrain/__init__.py` and Task 035D documentation. No dependency or workflow change is approved. Core tests use fake converters and standard-library behavior; concrete GIS adapters use lazy optional imports and local validation.

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

## Paper and Interpretation Boundary

The renderer-neutral package and local SVG may support later sanitized figures and candidate count tables. They are not measured RF evidence, terrain-accuracy validation, a full link budget, communication-success evidence, reconnaissance-success evidence, flight-feasibility evidence, or airspace-approval evidence.

The local equirectangular SVG transform is a deterministic schematic display transform only.

## Product and Deployment Boundary

Browser-to-Python callbacks, Streamlit, Folium, Android/TMMR, map tiles, base maps, remote services, route/waypoint generation, and device integration require separate reviewed tasks.

## Public Repository Sensitivity Check

This decision contains no actual coordinate, private path, GIS raster, generated HTML, screenshot, credential, operational command, external-device command, autopilot command, or flight-control output.
