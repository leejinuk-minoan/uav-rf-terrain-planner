# Task 035C Real-Terrain Launch-Area Map and Selection Boundary

## Current Task

Task 035C defines the reviewed implementation boundary for converting the Task 035B real-terrain candidate result into a renderer-neutral colored launch-area map package, optional local offline HTML/SVG output, and deterministic candidate-ID-based launch-site selection.

This Master Review amendment resolves three merge-blocking ambiguities:

```text
initial unselected-package selection lifecycle
deterministic WGS84-to-SVG viewport and zero-span behavior
HTML/JavaScript escaping and browser-preview semantics
```

Task 035C remains documentation/code-contract work only. It does not modify runtime source, tests, examples, workflows, dependencies, or GIS data.

## Existing Repository Objects

```text
repository: leejinuk-minoan/uav-rf-terrain-planner
Issue: #100
branch: agent/task-035c-real-terrain-map-selection-contract
Draft PR: #101
reviewed pre-amendment head: a670663cba4fcd2eba49a09696fad645d1b33fb6
GPT Master review comment: 4965114229
```

Do not create a new Issue, branch, or PR. Keep PR #101 Draft and unmerged until GPT Master re-review and explicit user approval.

## Target Agent for Task 035D

```text
Local Execution Agent — Codex or Claude Code
```

Task 035D requires TDD, Python implementation, optional GIS dependency validation, deterministic HTML inspection, and optional local real-data smoke work. Task 035C does not perform those actions.

## Preserved Authority

Task 035D consumes:

```text
RealTerrainLaunchAreaResult.candidate_records
RealTerrainLaunchAreaResult.candidate_features
```

Do not use `build_candidate_cell_map_features(...)` for real output. Its `x=index*500, y=0` behavior is a protected synthetic regression.

Before conversion, require non-empty equal record/feature counts, unique IDs, index-aligned candidate IDs, `EPSG:5179` geometry, exact center parity, and exact state/color/radius/reason/source-zone/diagnostic/score projection parity. Any mismatch is fatal and must not be repaired or reordered.

## Map Configuration

Implement a frozen config equivalent to:

```python
@dataclass(frozen=True)
class RealTerrainLaunchAreaMapConfig:
    candidate_cell_size_m: float
    selected_candidate_id: str | None = None
    include_excluded: bool = True
```

Rules:

```text
candidate_cell_size_m: positive finite non-boolean value
selected_candidate_id: None or non-empty stripped string
include_excluded: bool
caller passes the same spacing used by Task 035B
spacing is not inferred from result geometry
```

## Candidate Cell Geometry

```text
center authority: CandidateAnalysisMapFeature.x_m/y_m
construction CRS: EPSG:5179
half size: candidate_cell_size_m / 2
ring: SW → SE → NE → NW → SW
orientation: projected counter-clockwise
```

Convert four unique projected corners individually to WGS84 and reuse the converted SW point to close the ring.

Do not use meter-to-degree approximation, candidate index geometry, raster row/col geometry, sampled-cell-center replacement, operating-circle clipping, raster clipping, NoData clipping, coastline clipping, or source-zone clipping.

## Coordinate Boundary

```text
EPSG:5179:
  analysis, candidate centers, polygon construction, future route-engine selected point

WGS84:
  renderer-internal target, center, and polygon geometry

MGRS:
  target, candidate popup, and selected launch-site default external output
```

Implement protocols equivalent to:

```python
class ProjectedToWgs84Converter(Protocol):
    def __call__(self, point: LocalPoint) -> Wgs84MapPoint:
        ...

class ProjectedToMgrsConverter(Protocol):
    def __call__(self, point: LocalPoint, *, precision: int) -> str:
        ...
```

Renderer point:

```python
@dataclass(frozen=True)
class Wgs84MapPoint:
    longitude_deg: float
    latitude_deg: float
```

Concrete local `pyproj` conversion uses `always_xy=True`. MGRS conversion calls the MGRS library with latitude then longitude. MGRS output uses precision 5, uppercase, stripped text, and non-empty validation.

Default popup and selected dictionaries must not expose projected x/y, EPSG:5179, WGS84, raster row/col, or sampled-cell-center data.

## Renderer-Neutral Types

Create frozen types equivalent to:

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

Reuse existing:

```text
MapStyle
ColorClass
CandidateAnalysisState
SourceZoneAvailability
TerrainSourceZone
CandidateFresnelDiagnostics
```

Excluded candidates retain `None` scores and optional source-zone values. Do not invent score zero or ESA-derived metadata.

## Visual Policy

```text
green/yellow/orange/red: existing style_for_color_class values
excluded: existing gray #808080, opacity 0.5
target: blue #1f77b4, white stroke
package selected: black 3 px outline overlay
browser preview: separate transient class/outline
```

Legend order:

```text
green, yellow, orange, red, excluded, selected, target
```

Source-zone and dominant-obstacle diagnostics remain popup-only and non-scoring.

## Visibility and Selectability

```text
include_excluded=True:
  include all candidates in Task 035B order

include_excluded=False:
  omit only excluded polygons
  preserve source result, summary, and warnings
```

Selectable iff:

```text
state == valid_scored
candidate_score is present
color_class != excluded
within_operation_radius is true
```

A valid red candidate remains selectable. Excluded candidates may be visible but are never selectable.

# Amendment A — Exact Selection Lifecycle

## Map builder rules

When `config.selected_candidate_id is None`:

```text
all polygon.is_selected=False
package.selected_candidate_id=None
summary.selected_candidate_count=0
legend selected count=0
```

When `config.selected_candidate_id` is set:

```text
candidate exists in source result
candidate is included in package
candidate is selectable
exactly one polygon.is_selected=True
package.selected_candidate_id matches that polygon
summary.selected_candidate_count=1
legend selected count=1
```

Unknown, hidden, excluded, or non-selectable config-selected IDs are fatal.

## Selection service rules

Implement:

```python
select_launch_site(
    result: RealTerrainLaunchAreaResult,
    package: RealTerrainLaunchAreaMapPackage,
    candidate_id: str,
) -> SelectedLaunchSiteRecord
```

Exact lifecycle:

```text
package.selected_candidate_id is None:
  included selectable requested candidate succeeds

package.selected_candidate_id == requested candidate_id:
  succeeds

package.selected_candidate_id is another non-None candidate:
  conflicting package selection error
```

The service returns only `SelectedLaunchSiteRecord` and does not mutate the package.

Recommended controller flow:

```text
1. build package(selected_candidate_id=None)
2. browser/controller obtains candidate_id
3. call select_launch_site(result, package, candidate_id)
4. receive SelectedLaunchSiteRecord
5. optionally rebuild package(selected_candidate_id=candidate_id)
6. rerender synchronized package-selected outline and counts
```

Selection reuses popup MGRS and the Task 035B projected point. It performs no terrain, LOS, Fresnel, score, color, ranking, or coordinate recomputation and never substitutes another candidate.

## Selection tests

```text
unselected package + valid selection succeeds
matching selected package + same candidate succeeds
selected package + different candidate fails
selection does not mutate package
selected record reuses popup MGRS
rebuilt selected package has exactly one selected polygon
rebuilt selected summary/legend counts equal one
None-selected package counts equal zero
unknown/hidden/excluded/non-selectable config-selected ID fatal
blank/unknown/duplicate/missing-MGRS selection fatal
```

# Amendment B — Deterministic HTML/SVG Viewport

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
width_px and height_px: positive non-boolean int
padding_px: non-negative non-boolean int
2 * padding_px < width_px
2 * padding_px < height_px
```

## Bounds

Use all WGS84 points from included candidate polygon rings plus the target marker. Hidden candidate geometry is excluded. The target is always included. Ignore repeated ring-closure points when computing unique reference values.

```text
reference_longitude_deg = mean(unique bound-input longitude values)
reference_latitude_deg = mean(unique bound-input latitude values)
```

## Local renderer-only transform

```python
x_local = radians(longitude_deg - reference_longitude_deg) * cos(
    radians(reference_latitude_deg)
)
y_local = radians(latitude_deg - reference_latitude_deg)
```

This transform is schematic display geometry only. It is not analysis geometry, distance authority, cell-size authority, or geodetic measurement output.

## Antimeridian

```python
if max(longitude_deg) - min(longitude_deg) > 180:
    raise LocalHtmlMapRendererError
```

Do not unwrap silently.

## Fit rules

```text
usable_width = width_px - 2 * padding_px
usable_height = height_px - 2 * padding_px
```

Both spans non-zero:

```python
scale = min(usable_width / x_span, usable_height / y_span)
fitted_width = x_span * scale
fitted_height = y_span * scale
left = padding_px + (usable_width - fitted_width) / 2
top = padding_px + (usable_height - fitted_height) / 2
x_svg = left + (x_local - x_min) * scale
y_svg = top + (y_max - y_local) * scale
```

Zero-x only:

```text
x_svg = width_px / 2
scale y to usable height
y_svg = padding_px + (y_max - y_local) * scale
```

Zero-y only:

```text
y_svg = height_px / 2
scale x to usable width
x_svg = padding_px + (x_local - x_min) * scale
```

Both zero:

```text
x_svg = width_px / 2
y_svg = height_px / 2
```

The y formula inverts the upward WGS84/local axis into the downward SVG axis. Never divide by zero.

## Empty polygon package

When no candidate polygons are included, render target, legend, summary, and warnings using target-only both-zero-span behavior. Do not fail solely because the polygon tuple is empty.

## Determinism

```text
viewBox = 0 0 width_px height_px
candidate elements follow package order
target element follows all candidate polygons
legend follows contract order
side-panel fields follow popup contract order
SVG geometry coordinates use fixed 6 decimals
-0.000000 is normalized to 0.000000
UTF-8
newline = \n
final newline present
```

Do not sort by geometry, score, color, or ID.

## Viewport tests

```text
default config
invalid dimensions/padding and bool values
bounds use target and visible polygons only
local equirectangular formula
aspect-ratio preservation
y-axis inversion
zero-x span
zero-y span
both spans zero
target-only package
antimeridian rejection
candidate element order
target after polygons
fixed 6 decimals
negative-zero normalization
deterministic repeated output
```

# Amendment C — HTML/JavaScript Safety

## Escaping

Escape every data-derived HTML text or attribute value with semantics equivalent to:

```python
html.escape(value, quote=True)
```

Apply this to scenario name, candidate ID, candidate MGRS, candidate reason, source-zone reason, target MGRS, diagnostic text, warnings, labels, side-panel text, titles, and `data-candidate-id`.

## Prohibited behavior

```text
no raw data interpolation into executable JavaScript
no data-derived innerHTML assignment
no eval
no Function constructor
no document.write with package data
no data-derived inline event-handler attribute
no external script/font/tile/image/network URL
no raw package JSON in a script element
```

Client updates use `textContent`, `classList`, and `dataset` against already-rendered escaped DOM values. Task 035D does not embed package JSON.

## Content security policy

Include the exact CSP meta content:

```text
default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; img-src data:;
```

## Click semantics

Distinguish three states:

```text
package-authoritative selection
transient browser preview
Python SelectedLaunchSiteRecord
```

Package selection comes only from `package.selected_candidate_id`; it controls initial selected outline and static summary/legend selected counts.

A selectable browser click may update side-panel details, expose candidate ID to the controller, and apply a class labeled `preview only` or equivalent. It must not mutate package state, change static summary/legend counts, create a selected record, or claim Python selection succeeded.

A non-selectable/excluded click may show details, `selectable=false`, and exclusion reason, but cannot receive the selectable preview class.

Clearing preview or resetting the page restores the package-selected outline, or no selected outline when the package is unselected.

## HTML safety tests

Use malicious values containing:

```text
<script>
</script>
quotes
apostrophes
ampersands
angle brackets
attribute-breaking text
```

Verify:

```text
malicious values are escaped inert text
no raw closing-script injection
no raw event-handler injection
no data-derived innerHTML
safe data-candidate-id escaping
no eval/Function/document.write with package data
no raw package JSON
exact CSP present
no external resources
non-selectable candidate cannot receive selectable preview class
browser preview does not alter serialized summary/legend counts
package-selected and transient-preview states remain separate
preview clear/reset restores package-selected state
browser click does not create or claim SelectedLaunchSiteRecord
```

## Local Renderer File Boundary

```text
standard library only
no tile or network
explicit output path
force=True required for overwrite
no browser auto-open
no committed generated HTML
UTF-8 deterministic output
```

Generated HTML may contain WGS84 and MGRS data. Treat it as a local potentially sensitive artifact.

## Task 035D Implementation Scope

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

Narrowly update:

```text
src/uav_rf_terrain/__init__.py
README.md
Task 035D handoff/EXP/index records
```

No dependency or workflow change is approved. Pure tests use fake converters and standard-library behavior. Concrete GIS adapters use lazy optional imports and local validation.

## Protected Scope

Do not modify without separate evidence and scope review:

```text
Task 035B analysis and GeoTIFF/session code
profile, LOS, Fresnel, diagnostics, scoring, classification
synthetic scenario/map/display builders
preview/report/appendix/CLI
routing and waypoints
.github/workflows/
pyproject.toml
lock files
```

Do not commit GIS data, `METADATA_MAP`, generated HTML/images/JSON/CSV, private paths, actual coordinates, credentials, operational commands, device commands, autopilot commands, or flight-control outputs.

## Verification Required for Task 035D

Task 035D must use TDD and run:

```text
focused pure tests
full pytest
compile/syntax checks
Ruff
mypy
local optional pyproj/mgrs validation
local deterministic HTML inspection
optional real-data smoke only when explicitly authorized
```

Do not claim measured RF, terrain accuracy, communication success, reconnaissance success, flight feasibility, or airspace approval.

## Task 035C Amendment Status

```text
runtime files modified: 0
test files modified: 0
example files modified: 0
workflow/dependency files modified: 0
GIS/generated files modified: 0
Draft PR #101 remains Draft and unmerged
```
