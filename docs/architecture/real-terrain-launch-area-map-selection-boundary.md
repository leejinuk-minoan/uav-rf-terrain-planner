# Real-Terrain Launch-Area Map and Selection Boundary

## Purpose

This document defines the reviewed Task 035D implementation contract for converting the Task 035B real-terrain candidate-analysis result into a renderer-neutral colored launch-area map package, optional local offline HTML/SVG output, and deterministic candidate-ID-based launch-site selection.

Task 035C and this Master Review amendment are documentation and code-contract work only. They do not modify runtime source or tests, perform coordinate conversion, render a map, open GIS data, create generated output, or validate field RF or flight outcomes.

## Verified Baseline

```text
PR #99: merged to main
PR #99 merge commit / Task 035C base: a9886eb12633f27cea3556a8e7b9ab4a142667a1
Issue #98: closed / completed
Issue #100: open
Task 035B source, focused tests, handoff, and EXP-052: present on main
Task 035C branch: agent/task-035c-real-terrain-map-selection-contract
Draft PR #101: open / Draft / unmerged
reviewed pre-amendment head: a670663cba4fcd2eba49a09696fad645d1b33fb6
GPT Master review comment: 4965114229
```

## Preserved Contract

The amendment does not change the following reviewed boundaries:

```text
Task 035B records/features are the real input authority
synthetic placeholder builder is prohibited for real output
candidate_cell_size_m is explicit
candidate cell polygons are constructed in EPSG:5179
ring order is SW → SE → NE → NW → SW
WGS84 is renderer-internal geometry
MGRS is the default user-facing coordinate output
record/feature parity is validated before conversion
existing color styles are reused
excluded candidates are visible by default
valid red candidates remain selectable
source-zone and Fresnel diagnostics remain non-scoring
pure HTML/SVG remains the selected local renderer
no new dependency is approved
route, waypoint, and minimum-altitude work remain deferred
runtime source, tests, examples, workflows, dependencies, and GIS data remain protected
```

## Current Runtime Audit

### Task 035B authority

Task 035D consumes the following immutable Task 035B outputs:

```text
RealTerrainLaunchAreaResult.candidate_records
RealTerrainLaunchAreaResult.candidate_features
```

`candidate_records` is authoritative for candidate order, candidate ID, projected candidate point, candidate state, reason, distance, within-operation-radius state, terrain endpoint fields, score availability and values, color, source-zone availability and values, and Fresnel diagnostics.

`candidate_features` is the renderer-input projection of the same records and is authoritative for feature ID, actual projected center x/y, geometry CRS, style, primitive score projection, and renderer-oriented state metadata.

Task 035D must not route real output through `build_candidate_cell_map_features(...)`. That function remains a protected synthetic scaffold with placeholder geometry:

```text
x_m = index * 500.0
y_m = 0.0
```

### Existing map and display scaffolds

Existing synthetic map/display structures cannot represent the full Task 035B real-terrain contract without breaking compatibility. In particular, they require non-null scores, concrete source-zone values, or route/waypoint state that excluded and source-zone-unavailable candidates do not possess.

Task 035D therefore introduces separate frozen real-terrain map, popup, summary, selection, and renderer configuration types. Existing synthetic map/display, preview, report, appendix, and CLI contracts remain unchanged.

### Coordinate and dependency state

```text
user-facing input/output: MGRS
analysis and polygon construction: EPSG:5179
renderer-internal geometry: WGS84
raster row/col and sampled-cell centers: internal/debug only
base dependencies: none
optional GIS dependencies: pyproj>=3.6, mgrs>=1.5
new renderer dependency: none
```

## Task 035D Endpoint

```text
RealTerrainLaunchAreaResult
+ explicit map configuration
+ EPSG:5179-to-WGS84 converter
+ EPSG:5179-to-MGRS converter
→ validate record/feature parity
→ deterministic EPSG:5179 candidate cell polygons
→ renderer-internal WGS84 geometry
→ MGRS-only user-facing popup properties
→ immutable renderer-neutral map package
→ optional self-contained local HTML/SVG renderer
→ candidate-ID selection service
→ immutable selected launch-site record
```

Task 035D does not include route search, three route alternatives, waypoint generation, minimum-altitude integration, browser-to-Python callback infrastructure, automatic launch-site recommendation, Top-N replacement, field RF validation, external-device integration, autopilot, or flight control.

## Input and Parity Contract

Before any coordinate conversion or polygon construction, Task 035D validates:

1. `result` is `RealTerrainLaunchAreaResult`.
2. Candidate records and features are both non-empty.
3. Record and feature counts are equal.
4. Candidate IDs are non-empty and unique in both sequences.
5. Candidate IDs match by index.
6. Feature IDs are non-empty and unique.
7. `feature.geometry_crs == "EPSG:5179"`.
8. Feature x/y exactly equal the corresponding record candidate point x/y.
9. State, color, radius flag, reason, source-zone fields, and diagnostics match.
10. Scored feature values exactly match the record score projection.
11. Excluded features have `None` score projections and `ColorClass.EXCLUDED`.
12. Task 035B MGRS fields remain `None` with `coordinate_display_state == "projected_only"` at input.

Any mismatch is fatal `RealTerrainLaunchAreaMapError`. The builder does not reorder, repair, or synthesize missing input.

## Map Configuration

```python
@dataclass(frozen=True)
class RealTerrainLaunchAreaMapConfig:
    candidate_cell_size_m: float
    selected_candidate_id: str | None = None
    include_excluded: bool = True
```

Validation:

```text
candidate_cell_size_m: positive finite non-boolean numeric value
selected_candidate_id: None or non-empty stripped string
include_excluded: bool
```

Task 035B does not retain the original candidate spacing in `RealTerrainLaunchAreaResult`. The caller must pass the same spacing used by the Task 035B analysis config. Task 035D must not infer spacing from candidate distances, raster geometry, or arbitrary neighboring points.

## Candidate Cell Geometry

```text
construction CRS: EPSG:5179
center: CandidateAnalysisMapFeature.x_m / y_m
side length: candidate_cell_size_m
half size: candidate_cell_size_m / 2
ring: SW → SE → NE → NW → SW
orientation: counter-clockwise in projected x/y
```

For center `(x, y)` and half-size `h`:

```text
SW = (x - h, y - h)
SE = (x + h, y - h)
NE = (x + h, y + h)
NW = (x - h, y + h)
```

Each unique corner is converted separately to WGS84. The converted SW point is reused to close the ring. Task 035D does not use meter-to-degree constants, candidate indices, raster row/col polygons, sampled-cell-center replacement geometry, or polygon clipping.

Candidate polygons are not clipped to the operating circle, raster extent, NoData footprint, coastline, or source-zone boundaries. Candidate radius and state authority remain the center-based Task 035B result.

## Visibility and Partial Results

```text
include_excluded=True:
  include all Task 035B candidates in source order

include_excluded=False:
  omit only excluded polygons from the map package
  preserve the source result, source summary, and source warnings
```

A Task 035B partial grid remains partial. Task 035D does not invent omitted cells.

A zero-candidate source result is fatal. A candidate source with zero selectable records remains a valid package and includes:

```text
no selectable launch-site candidates were produced
```

When excluded candidates are hidden and no polygon remains, the package is still valid and adds:

```text
no candidate polygons were included by the map configuration
```

## Coordinate Conversion Contract

### WGS84 renderer point

```python
@dataclass(frozen=True)
class Wgs84MapPoint:
    longitude_deg: float
    latitude_deg: float
```

Longitude is stored first. Longitude must be finite and within `[-180, 180]`; latitude must be finite and within `[-90, 90]`.

### Converter protocols

```python
class ProjectedToWgs84Converter(Protocol):
    def __call__(self, point: LocalPoint) -> Wgs84MapPoint:
        ...

class ProjectedToMgrsConverter(Protocol):
    def __call__(self, point: LocalPoint, *, precision: int) -> str:
        ...
```

Concrete local EPSG:5179-to-WGS84 conversion uses `pyproj.Transformer(..., always_xy=True)`. The MGRS adapter converts through WGS84 and calls the MGRS library with latitude then longitude, as required by that library.

MGRS output uses five easting and five northing digits, uppercase, stripped surrounding whitespace, and non-empty validation. This formatting precision is not a one-meter terrain or RF accuracy claim.

### Deterministic conversion order

```text
1. target projected point → WGS84 once
2. target projected point → MGRS once, precision 5
3. included candidates in Task 035B order
4. candidate center → WGS84 once
5. candidate center → MGRS once, precision 5
6. unique corners → WGS84 in SW, SE, NE, NW order
7. reuse converted SW to close the ring
```

Selection from an already-built package performs no coordinate conversion.

## Renderer-Neutral Schemas

Task 035D introduces frozen dataclasses equivalent to:

```text
Wgs84MapPoint
RealTerrainCandidatePopup
RealTerrainCandidatePolygon
RealTerrainTargetMarker
MapSelectionStyle
LaunchAreaLegendEntry
RealTerrainLaunchAreaMapSummary
RealTerrainLaunchAreaMapPackage
SelectedLaunchSiteRecord
LocalHtmlMapRenderConfig
```

Existing `MapStyle`, `ColorClass`, `CandidateAnalysisState`, source-zone enums, and Fresnel diagnostics are reused.

The default popup and selected-record dictionaries do not expose projected x/y, EPSG:5179 values, WGS84 longitude/latitude, raster row/col, or sampled-cell-center data.

Excluded candidates retain `None` scores. Source-zone `None`, availability state, and optional sensitivity values are preserved and are never replaced with invented defaults.

## Visual and Legend Policy

```text
green/yellow/orange/red: existing style_for_color_class values
excluded: existing gray #808080 with opacity 0.5
target: blue #1f77b4 with white stroke
package-selected: black 3 px outline overlay; base fill unchanged
browser transient preview: separate preview class/outline, never package authority
```

Legend order is fixed:

```text
green
yellow
orange
red
excluded
selected
target
```

Source-zone fields and dominant-obstacle diagnostics remain popup interpretation data only. They do not change score, color, order, selectability, route cost, or waypoint cost.

## Selectability

A candidate is selectable if and only if:

```text
state == CandidateAnalysisState.VALID_SCORED
candidate_score is not None
color_class is not ColorClass.EXCLUDED
within_operation_radius is True
```

A valid red candidate remains selectable and retains its risk reason. Visibility and selectability are independent; an excluded candidate may be visible but is never selectable.

# Master Review Amendment A — Selection Lifecycle

## Map-builder selected-ID validation

When `RealTerrainLaunchAreaMapConfig.selected_candidate_id is None`:

```text
all candidate polygons have is_selected=False
package.selected_candidate_id is None
summary.selected_candidate_count == 0
legend selected count == 0
```

When `selected_candidate_id` is not `None`, the builder requires:

```text
the candidate exists in the source result
the candidate is included in the package
the candidate is selectable
exactly one polygon has is_selected=True
package.selected_candidate_id equals that polygon candidate_id
summary.selected_candidate_count == 1
legend selected count == 1
```

Unknown, hidden, excluded, or non-selectable config-selected IDs are fatal. The builder never silently clears or substitutes an invalid selected ID.

## Selection service lifecycle

```python
def select_launch_site(
    result: RealTerrainLaunchAreaResult,
    package: RealTerrainLaunchAreaMapPackage,
    candidate_id: str,
) -> SelectedLaunchSiteRecord:
    ...
```

Exact package-state rules:

```text
Case 1:
package.selected_candidate_id is None
→ requested candidate may be selected when it is included and selectable

Case 2:
package.selected_candidate_id == requested candidate_id
→ selection succeeds

Case 3:
package.selected_candidate_id is not None
and package.selected_candidate_id != requested candidate_id
→ raise conflicting package selection error
```

The selection service does not mutate the immutable package. It returns only an immutable `SelectedLaunchSiteRecord`. It reuses the package popup MGRS and Task 035B projected point and performs no terrain, LOS, Fresnel, score, color, ranking, or coordinate recomputation.

Recommended controller lifecycle:

```text
1. build package(selected_candidate_id=None)
2. browser/controller obtains candidate_id
3. call select_launch_site(result, package, candidate_id)
4. receive SelectedLaunchSiteRecord
5. optionally rebuild package with selected_candidate_id=candidate_id
6. render synchronized package-selected outline, summary, and legend
```

Selection rejects blank, unknown, duplicate, hidden, excluded, non-selectable, missing-MGRS, record/feature/package-mismatched, or conflicting package-selected IDs. It never auto-selects a green or highest-score candidate and never substitutes another candidate.

## Selection tests frozen for Task 035D

```text
unselected package + valid candidate selection succeeds
matching selected package + same candidate succeeds
selected package + different requested candidate fails
selection does not mutate package
returned record reuses popup MGRS
optional rebuilt package has exactly one selected polygon
selected summary and legend count are exactly one after rebuild
unknown/hidden/excluded/non-selectable config-selected ID is fatal
None config produces zero selected polygon/summary/legend counts
```

# Master Review Amendment B — Deterministic HTML/SVG Viewport

## Renderer configuration

```python
@dataclass(frozen=True)
class LocalHtmlMapRenderConfig:
    width_px: int = 1000
    height_px: int = 800
    padding_px: int = 40
```

Validation:

```text
width_px: positive non-boolean int
height_px: positive non-boolean int
padding_px: non-negative non-boolean int
2 * padding_px < width_px
2 * padding_px < height_px
```

## Bounds authority

Viewport bounds use all WGS84 points from included candidate polygon rings plus the target marker position. Repeated ring-closure points do not change bounds and are ignored when computing unique reference values. Hidden candidate geometry is not used. The target is always included.

For deterministic reference values:

```text
reference_longitude_deg = arithmetic mean of unique bound-input longitude values
reference_latitude_deg = arithmetic mean of unique bound-input latitude values
```

## Local display projection

For each WGS84 point:

```python
x_local = radians(longitude_deg - reference_longitude_deg) * cos(
    radians(reference_latitude_deg)
)
y_local = radians(latitude_deg - reference_latitude_deg)
```

This is renderer-only schematic display geometry. It is not analysis geometry, distance authority, cell-size authority, or geodetic measurement output.

## Antimeridian rule

```python
if max(longitude_deg) - min(longitude_deg) > 180:
    raise LocalHtmlMapRendererError
```

Task 035D does not silently unwrap longitude.

## SVG fitting

```text
usable_width = width_px - 2 * padding_px
usable_height = height_px - 2 * padding_px
x_span = x_max - x_min
y_span = y_max - y_min
```

### Both spans non-zero

```python
scale = min(usable_width / x_span, usable_height / y_span)
fitted_width = x_span * scale
fitted_height = y_span * scale
left = padding_px + (usable_width - fitted_width) / 2
bottom = padding_px + (usable_height - fitted_height) / 2
x_svg = left + (x_local - x_min) * scale
y_svg = bottom + (y_max - y_local) * scale
```

The `y_svg` formula inverts the upward local y-axis into the downward SVG y-axis while preserving aspect ratio.

### Zero x span only

```text
x_svg = width_px / 2
scale = usable_height / y_span
y_svg = padding_px + (y_max - y_local) * scale
```

### Zero y span only

```text
y_svg = height_px / 2
scale = usable_width / x_span
x_svg = padding_px + (x_local - x_min) * scale
```

### Both spans zero

All points are placed at:

```text
x_svg = width_px / 2
y_svg = height_px / 2
```

No division by zero is permitted.

## Empty-polygon package

A package may contain zero candidate polygons when excluded candidates are hidden. The renderer still renders the target marker, legend, summary, and warnings. It uses the target-only both-zero-span behavior and does not fail solely because the polygon tuple is empty.

## Deterministic SVG output

```text
SVG viewBox: 0 0 width_px height_px
candidate polygon element order: package candidate order
target element: rendered after all candidate polygons
legend order: contract legend order
side-panel field order: popup contract order
SVG geometry coordinates: fixed 6 decimal places
negative zero: normalize -0.000000 to 0.000000
encoding: UTF-8
newline: \n
final newline: required
```

The renderer never sorts candidates by geometry, score, color, or ID.

## Viewport tests frozen for Task 035D

```text
default renderer config
invalid width/height/padding and bool rejection
bounds include target and visible polygons only
local equirectangular formula
aspect-ratio preservation
y-axis inversion
zero-x span
zero-y span
both spans zero
target-only package
antimeridian rejection
candidate SVG element order
target after polygons
fixed 6-decimal formatting
negative-zero normalization
deterministic repeated output
```

# Master Review Amendment C — HTML/JavaScript Safety and Click Semantics

## Escaping contract

Every data-derived value inserted into HTML text or an HTML attribute is escaped with standard-library semantics equivalent to:

```python
html.escape(value, quote=True)
```

This applies to scenario name, candidate ID, MGRS, candidate reason, source-zone reason, target MGRS, diagnostics, warnings, legend labels, side-panel text, titles, and `data-candidate-id` attributes. MGRS and reason fields are always text, never markup.

## Prohibited HTML/JavaScript behavior

```text
no raw data interpolation into executable JavaScript
no data-derived innerHTML assignment
no eval
no Function constructor
no document.write with package data
no inline event-handler attributes derived from data
no external script, font, tile, image, or network URL
no raw package JSON embedded inside a script element
```

Client-side updates use only safe DOM APIs such as:

```text
textContent
classList
dataset
```

The inline script operates on already-rendered, escaped DOM attributes and text elements. If a future task requires embedded structured data, it must separately define safe JSON serialization that neutralizes `<`, `>`, `&`, U+2028, U+2029, and closing-script sequences. Task 035D does not embed package JSON.

## Local content security policy

The HTML includes the following exact deterministic CSP meta content:

```text
default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; img-src data:;
```

No network origin is allowed.

## Three selection states

The renderer and documentation must distinguish:

```text
1. package-authoritative selection
2. transient browser preview
3. Python SelectedLaunchSiteRecord
```

### Package-authoritative selection

Package-authoritative selection comes only from `package.selected_candidate_id`. It sets the initial selected outline and the static selected counts in summary and legend.

### Transient browser preview

A selectable candidate click may update side-panel details, expose the candidate ID for the controller, and apply a transient preview outline. The UI labels this state `preview only` or an equivalent concise phrase.

A transient preview:

```text
does not mutate the immutable package
does not change package.selected_candidate_id
does not alter static summary or legend counts
does not create SelectedLaunchSiteRecord
does not claim Python selection succeeded
```

A non-selectable or excluded candidate click may show details but must not receive the selectable preview class. It displays `selectable=false` and the exclusion reason.

Clearing transient preview or resetting the page deterministically restores the package-selected outline, or no selected outline when `package.selected_candidate_id is None`.

## Safety and click tests frozen for Task 035D

Malicious values include:

```text
<script>
</script>
double quotes
apostrophes
ampersands
angle brackets
attribute-breaking text
```

Required tests verify:

```text
malicious values appear only as escaped inert text
no raw closing-script injection
no raw event-handler attribute injection
no data-derived innerHTML assignment
data-candidate-id is safely escaped
no eval, Function, or document.write with package data
no embedded raw package JSON
exact CSP string is present
no external URLs or resources
selectable click may receive transient preview class
non-selectable click cannot receive selectable preview class
browser click does not alter serialized summary or legend counts
initial package-selected state is represented separately
preview clear/reset restores package-selected state
browser click does not create or claim a Python selected record
```

## Renderer File Boundary

The optional renderer:

```text
consumes only RealTerrainLaunchAreaMapPackage and LocalHtmlMapRenderConfig
writes only to an explicit output path
requires force=True to overwrite
opens no browser automatically
uses no base tile or external network resource
adds no dependency
produces deterministic UTF-8 text
```

Generated HTML contains renderer WGS84 geometry and MGRS popup data. It is a local potentially sensitive artifact, is not committed, and is not attached to public records without separate review.

## Task 035D Source and Test Scope

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
Task 035D handoff, EXP, and indexes
```

No dependency or workflow change is approved. Core map-package, selection, viewport, escaping, and HTML tests use fake converters and standard-library behavior so standard CI does not require GIS packages. Concrete coordinate adapters use lazy optional imports and require local validation.

Task 035D must use TDD and keep its PR Draft until GPT Master review and explicit user approval.

## Protected Runtime Scope

Do not modify without an evidenced blocker and separate scope review:

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

Preserve Task 035B candidate order, state, score, color, actual geometry, score weights, strict LOS cap, color thresholds, source-zone non-scoring semantics, route and waypoint costs, synthetic placeholder regressions, preview/report/appendix/CLI behavior, and MGRS external-output policy.

## Interpretation Limits

The map displays Task 035B offline terrain/surface-obstacle risk proxy results. It is not a measured coverage map, RF link budget, terrain-accuracy certificate, communication guarantee, reconnaissance guarantee, flight-feasibility determination, or airspace approval result.

Candidate polygons visualize center-based analysis cells. Polygon area does not mean every point inside the cell was separately sampled or validated. The local equirectangular SVG transform is a schematic display projection and is not an analysis or geodetic measurement authority.

## Public Repository Sensitivity Check

This contract contains no actual coordinate, private local path, GIS raster, generated HTML, screenshot, credential, operational command, external-device command, autopilot command, or flight-control output.
