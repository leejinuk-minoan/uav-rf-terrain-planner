# Task 035C Real-Terrain Launch-Area Map and Selection Boundary

## Current Task

Task 035C defines the implementation boundary for converting the Task 035B real-terrain candidate result into a renderer-neutral colored launch-area map package, optional local offline HTML/SVG output, and deterministic candidate-ID-based launch-site selection.

This task is documentation and code-contract audit work only. It does not modify runtime source, tests, examples, workflows, dependencies, or GIS data.

## Start Gate

Verified before branch creation:

```text
repository: leejinuk-minoan/uav-rf-terrain-planner
PR #99: closed / merged
PR #99 merge commit: a9886eb12633f27cea3556a8e7b9ab4a142667a1
latest main: identical to PR #99 merge commit
Issue #98: closed / completed
Issue #100: open
Task 035B source/tests/handoff/EXP-052: present on main
conflicting open PRs: none
```

## Branch and Draft PR

```text
branch: agent/task-035c-real-terrain-map-selection-contract
Draft PR title: docs: define real-terrain map and selection boundary
Draft PR body: Closes #100
```

The PR remains Draft until GPT Master review and explicit user approval. Task 035C does not mark it ready or merge it.

## Agent Selection

```text
Cloud Execution Agent
```

Reason: the work consists of GitHub source/test/document auditing and architecture/code-contract definition. No local coordinate conversion, renderer, GIS file, browser, or UI execution is required.

Task 035D target agent:

```text
Local Execution Agent — Codex or Claude Code
```

Reason: Task 035D requires Python implementation, TDD, optional GIS dependency validation, local HTML inspection, and optional real-data smoke work.

## Authority Files Audited

Governance and policy:

```text
README.md
AGENTS.md
CLAUDE.md
docs/master-plan.md
docs/research/research-index.md
docs/data/terrain-data-policy.md
docs/architecture/mgrs-external-io-policy.md
docs/architecture/real-terrain-launch-area-analysis-pipeline-boundary.md
docs/paper/decisions/DEC-20260714-005-real-terrain-launch-area-pipeline-policy.md
pyproject.toml
```

Task 035B implementation evidence:

```text
src/uav_rf_terrain/real_terrain_candidate_analysis.py
tests/test_real_terrain_candidate_analysis.py
docs/handoff/task-035b-real-terrain-launch-area-candidate-analysis-implementation.md
docs/paper/experiments/EXP-20260714-052-real-terrain-launch-area-candidate-analysis-implementation.md
```

Map/display/coordinate contracts:

```text
src/uav_rf_terrain/map_outputs.py
src/uav_rf_terrain/candidate_display_outputs.py
src/uav_rf_terrain/candidate_display_preview.py
src/uav_rf_terrain/coordinate_io_policy.py
src/uav_rf_terrain/coordinates.py
src/uav_rf_terrain/source_zones.py
src/uav_rf_terrain/schemas.py
tests/test_map_outputs.py
tests/test_candidate_display_outputs.py
tests/test_coordinate_io_policy.py
```

Relevant preview/report/CLI compatibility tests and current documentation boundaries were also inspected.

## Current Facts

### Task 035B result

`RealTerrainLaunchAreaResult` contains:

```text
candidate_records
candidate_features
summary
warnings
target projected point and terrain heights
dataset metadata
```

The result does not retain `candidate_spacing_m`.

Task 035B records/features preserve:

```text
candidate order and ID
actual EPSG:5179 requested candidate point
explicit candidate state
optional score
color
radius state
reason
source-zone availability and values
Fresnel diagnostics
```

### Synthetic map scaffold

`build_candidate_cell_map_features(...)` accepts synthetic records and creates placeholder geometry:

```text
x_m = index * 500.0
y_m = 0.0
```

Task 035D must not use this path for real output. Existing synthetic behavior remains protected.

### Existing display scaffold

The synthetic display record requires non-null scores, non-empty MGRS, string source zone, and boolean source sensitivity. It cannot faithfully represent Task 035B excluded candidates or source-zone `not_requested`, `unavailable`, and `not_applicable` states.

Task 035D therefore creates a separate real-terrain popup schema rather than widening or breaking the existing display/preview contracts.

### Dependency state

```text
base dependencies: none
optional gis: pyproj>=3.6, mgrs>=1.5
concrete map renderer dependency: none
```

No dependency change is approved for Task 035D.

## Selected Task 035D Pipeline

```text
RealTerrainLaunchAreaResult
+ RealTerrainLaunchAreaMapConfig
+ projected-to-WGS84 converter
+ projected-to-MGRS converter
→ strict record/feature parity validation
→ EPSG:5179 cell polygons
→ WGS84 renderer geometry
→ MGRS-only popup values
→ renderer-neutral package
→ optional self-contained local HTML/SVG
→ candidate-ID selection
→ immutable selected launch-site record
```

Excluded:

```text
route search
three route alternatives
waypoints
minimum altitude
automatic best-site selection
Top-N default output
browser-to-Python callback server
Streamlit/Folium integration
field RF validation
device/autopilot/flight control
```

## Input and Parity Rules

Use both:

```text
result.candidate_records
result.candidate_features
```

Before conversion:

```text
counts equal and non-zero
candidate IDs unique
feature IDs unique
candidate IDs match by index
feature geometry_crs == EPSG:5179
feature x/y == record candidate point x/y
state/color/radius/reason/source/diagnostics match
scored record score values match feature projection
excluded record has None scores and excluded color
Task 035B MGRS fields remain None/projected_only at input
```

Any mismatch is fatal. Do not reorder or repair input.

## Map Configuration

```python
@dataclass(frozen=True)
class RealTerrainLaunchAreaMapConfig:
    candidate_cell_size_m: float
    selected_candidate_id: str | None = None
    include_excluded: bool = True
```

`candidate_cell_size_m` is positive, finite, and not a bool. The caller must pass the original Task 035B candidate spacing. The value cannot be reliably recovered from the result and must not be inferred.

## Cell Polygon

```text
center authority: CandidateAnalysisMapFeature.x_m/y_m
CRS: EPSG:5179
half-size: candidate_cell_size_m / 2
ring: SW → SE → NE → NW → SW
orientation: counter-clockwise in projected x/y
```

Convert the four unique corners individually and reuse the converted southwest point to close the ring.

Do not use meter-to-degree approximation, candidate indices, raster row/col, sampled-cell centers, or polygon clipping.

A polygon may extend outside the operating circle or raster. Candidate state and radius remain center-based Task 035B authority.

## Coordinate Boundary

```text
EPSG:5179:
  candidate centers, polygon construction, internal selected point

WGS84:
  renderer-internal target, center, and polygon geometry

MGRS:
  target popup, candidate popup, selected launch-site external output
```

Protocols:

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

Use longitude first in renderer structures. Concrete `pyproj` conversion uses `always_xy=True`. MGRS conversion uses latitude then longitude when calling the MGRS library.

MGRS policy:

```text
precision = 5
uppercase
strip surrounding whitespace
non-empty output required
```

This formatting precision does not assert one-meter terrain or RF accuracy.

Default popup and selected dictionaries block EPSG:5179, WGS84, x/y, and raster row/col fields.

## Converter Call Order

```text
1. target WGS84 once
2. target MGRS once
3. included candidates in Task 035B order
4. candidate center WGS84 once
5. candidate center MGRS once
6. corners SW, SE, NE, NW once each
7. reuse SW to close
```

Selection from the package performs no conversion.

Any required conversion failure is fatal for the entire package.

## Renderer-Neutral Types

Task 035D creates frozen types equivalent to:

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
```

Reuse:

```text
MapStyle
ColorClass
CandidateAnalysisState
SourceZoneAvailability
TerrainSourceZone
CandidateFresnelDiagnostics
```

## Visual Policy

```text
green/yellow/orange/red: existing style_for_color_class
excluded: existing #808080, opacity 0.5
target: blue #1f77b4 with white stroke
selected: black 3 px outline overlay
```

Selected fill remains the original color.

Legend order:

```text
green
yellow
orange
red
excluded
selected
target
```

Source-zone and dominant-obstacle diagnostics are popup details only. They do not alter score, color, order, or selectability.

## Visibility and Partial Results

```text
include_excluded=True:
  all Task 035B candidates shown in source order

include_excluded=False:
  excluded polygons omitted only from the package
```

The source result and source summary remain unchanged. A Task 035B partial grid remains partial.

Zero source records/features is fatal.

Candidates with zero selectable records still produce a valid package and warning:

```text
no selectable launch-site candidates were produced
```

When all excluded candidates are hidden, add:

```text
no candidate polygons were included by the map configuration
```

## Selection Contract

Selectable if and only if:

```text
state == valid_scored
candidate_score is not None
color_class != excluded
within_operation_radius is true
```

A valid red candidate is selectable and retains its risk reason.

API:

```python
select_launch_site(
    result: RealTerrainLaunchAreaResult,
    package: RealTerrainLaunchAreaMapPackage,
    candidate_id: str,
) -> SelectedLaunchSiteRecord
```

The selected record includes:

```text
candidate_id
launch_site_mgrs
external_coordinate_format = MGRS
user_coordinate_field = launch_site_mgrs
internal projected LocalPoint for the future route engine
color and score
distance and reason
source-zone fields
Fresnel diagnostics
```

The internal projected point is omitted from the default user-facing dictionary.

Reject blank, unknown, duplicate, hidden, excluded, non-selectable, mismatched, or missing-MGRS selection. Never substitute another candidate and never auto-select.

## Renderer Decision

Audited:

```text
Folium/Leaflet
Streamlit map components
matplotlib
pure HTML/SVG
```

Selected for Task 035D:

```text
self-contained standard-library HTML/SVG local renderer
```

Reasons:

```text
works without tiles or network
adds no dependency
can be tested as deterministic text in CI
supports colored polygons, target, legend, popup/side panel
can expose data-candidate-id and browser-side visual highlight
```

Browser click state is not the authoritative Python selection. A controller passes the displayed candidate ID to `select_launch_site(...)`. Browser-to-Python callback infrastructure is deferred.

Renderer file policy:

```text
explicit output path
force=True required to overwrite
no browser auto-open
no external scripts, fonts, tiles, or network URLs
no committed generated HTML
```

Generated HTML may contain WGS84 and MGRS data and is treated as a local potentially sensitive artifact.

## Task 035D Source and Tests

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
Task 035D handoff/EXP/indexes
```

No dependency or workflow change is approved. Pure tests use fake converters. Concrete `pyproj` and MGRS adapters use lazy optional imports and are locally validated.

## Protected Files

Do not modify without a proven blocker and explicit scope review:

```text
real_terrain_candidate_analysis.py
geotiff_terrain_data.py
profile.py
los.py
fresnel.py
fresnel_diagnostics.py
scoring.py
classification.py
scenario_outputs.py
map_outputs.py
candidate_display_outputs.py
candidate_display_preview.py
preview_report.py
preview_cli.py
routing.py
waypoints.py
.github/workflows/
pyproject.toml
lock files
```

Preserve all Task 035B scoring, color, order, state, source-zone, diagnostics, and actual-geometry behavior, plus all synthetic and preview/report/CLI regressions.

## Task 035D Test Matrix

```text
map config validation
record/feature count, ID, field, and geometry parity
duplicate IDs
actual center geometry and no placeholder path
SW/SE/NE/NW/closed counter-clockwise ring
converter order and exact call counts
WGS84 range and longitude/latitude axis order
MGRS precision 5 and normalization
coordinate failure fatal
include_excluded true/false
partial grid order
zero source candidates fatal
zero selectable and hidden-all warnings
style and legend order/counts
target and selected metadata
valid red selection
blank/unknown/hidden/excluded selection rejection
selected record exact reuse and no recomputation
no internal coordinates in user dictionaries
source-zone unavailable preservation
diagnostics popup-only behavior
package builder writes no files
offline deterministic HTML/SVG
explicit output and force overwrite
no external URLs or browser auto-open
no eager pyproj/mgrs import
existing map/display/preview/report/CLI regressions
```

Task 035D must use TDD.

## Historical Verification Record Note

Task 035B historical local test totals are inconsistent across records:

```text
PR #99 body: full pytest 831 passed
Task 035B handoff: full pytest 821 passed
EXP-052: full pytest 782 passed
```

Task 035C does not reinterpret or overwrite these historical local claims. The current runtime API, merged GitHub state, and exact Task 035C final-head GitHub Actions result are the authorities for this contract task. A separate documentation reconciliation task may resolve the historical count provenance if required.

## Local Execution Claims

The Cloud Execution Agent did not execute:

```text
coordinate conversion
pyproj or mgrs
map package code
HTML/SVG rendering
browser click
pytest
compileall
Ruff
mypy
GeoTIFF/rasterio/GDAL/QGIS
real GIS smoke
```

GitHub Actions evidence is recorded in the Draft PR and completion report after the exact final head completes.

## Limitations

- This document defines a future implementation contract; it is not map or selection runtime evidence.
- Candidate polygons visualize center-based cells. They do not establish that every point inside the polygon was separately sampled.
- MGRS precision does not imply terrain, DSM, RF, or field accuracy.
- The optional HTML/SVG renderer is not a measured coverage map.
- No communication, reconnaissance, flight, or airspace outcome is validated or guaranteed.

## Public Repository Sensitivity Check

No coordinate, private path, GIS raster, `METADATA_MAP` content, generated HTML, image, screenshot, QGIS project, credential, operational command, external-device command, autopilot command, or flight-control output is added.
