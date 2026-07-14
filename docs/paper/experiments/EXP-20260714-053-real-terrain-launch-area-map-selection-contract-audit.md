# EXP-20260714-053 - Real-Terrain Launch-Area Map and Selection Contract Audit

## Purpose

Audit the merged Task 035B runtime result, existing synthetic map/display scaffolds, coordinate policy, dependencies, relevant tests, and GPT Master review feedback before implementing a real-terrain colored launch-area map and launch-site selection service.

This is a code/document contract audit. It is not a runtime map experiment, coordinate-conversion execution, GIS smoke, browser test, terrain-accuracy validation, or field RF validation.

## Start and Amendment State

```text
PR #99: merged
Task 035C base: a9886eb12633f27cea3556a8e7b9ab4a142667a1
Issue #98: closed / completed
Issue #100: open
Task 035C branch: agent/task-035c-real-terrain-map-selection-contract
Draft PR #101: open / Draft / unmerged
reviewed pre-amendment head: a670663cba4fcd2eba49a09696fad645d1b33fb6
GPT Master review comment ID: 4965114229
```

Task 035B source, tests, handoff, and EXP-052 were present on main before Task 035C began. The PR diff was documentation-only before this amendment and remains documentation-only.

## Evidence Sources

```text
src/uav_rf_terrain/real_terrain_candidate_analysis.py
src/uav_rf_terrain/map_outputs.py
src/uav_rf_terrain/candidate_display_outputs.py
src/uav_rf_terrain/candidate_display_preview.py
src/uav_rf_terrain/coordinate_io_policy.py
src/uav_rf_terrain/coordinates.py
src/uav_rf_terrain/source_zones.py
src/uav_rf_terrain/schemas.py
pyproject.toml
relevant map/display/coordinate tests
Task 035A architecture and decision documents
Task 035B handoff and EXP-052
MGRS external I/O policy
GPT Master review comment 4965114229
TASK-035C Master Review amendment prompt
```

No local file, raster, coordinate adapter, renderer, browser, or UI was executed.

## Original Audit Questions

1. Which Task 035B objects are authoritative?
2. Can existing synthetic map/display types represent real exclusions and source-zone availability?
3. How is candidate cell size supplied without changing Task 035B?
4. What polygon geometry and order are deterministic?
5. Which coordinate form is authoritative at analysis, renderer, and user boundaries?
6. Which immutable package, popup, legend, and selection types are required?
7. Which candidates are visible and selectable?
8. Which failures are fatal and which produce warnings?
9. Which concrete renderer is the smallest offline-first next step?
10. What exact Task 035D source/test scope minimizes Local Agent ambiguity?

## Master Review Questions

1. Can a user select a candidate from an initial package with `selected_candidate_id=None`?
2. How are WGS84 coordinates transformed into deterministic SVG coordinates?
3. What are the one-dimensional and zero-span rules?
4. What bounds include target-only and hidden-candidate cases?
5. How are data-derived strings escaped in HTML and attributes?
6. Can package data reach executable JavaScript or `innerHTML`?
7. How are package-authoritative selection, browser transient preview, and Python selected records separated?

## Baseline Findings Preserved

### Real input authority

`RealTerrainLaunchAreaResult.candidate_records` and `.candidate_features` preserve deterministic same-order real candidate data. Feature x/y values are actual EPSG:5179 candidate centers, not synthetic placeholder geometry.

The result does not retain candidate spacing. The map layer therefore requires explicit `candidate_cell_size_m`; it cannot independently prove equality with the original analysis spacing.

### Synthetic and display incompatibility

The synthetic builder generates `x=index*500, y=0` and remains a protected regression fixture. Existing display structures require non-null scores and concrete source-zone values and cannot faithfully represent excluded or source-zone-unavailable Task 035B candidates.

A separate immutable real-terrain package/popup/selection schema is required.

### Coordinate and renderer boundary

```text
EPSG:5179: analysis and polygon authority
WGS84: renderer-internal geometry
MGRS: default user-facing coordinates
```

No concrete renderer dependency exists. The optional GIS group already contains `pyproj` and `mgrs`. A pure standard-library HTML/SVG renderer can be deterministic and offline-first.

## Original Alternatives and Decisions

### Map endpoint

| Alternative | Result |
|---|---|
| Popup records only | rejected; no visible geometry milestone |
| Renderer-neutral package and selection | required core |
| Core plus self-contained HTML/SVG | selected for Task 035D |
| Folium/Streamlit application | deferred; broader dependency/callback/UI scope |

### Cell size

| Alternative | Result |
|---|---|
| Add spacing to Task 035B result in Task 035C | rejected; docs-only scope |
| Infer spacing from candidate points | rejected; unsafe for partial/irregular results |
| Explicit map config with caller responsibility | selected |

### Renderer

| Alternative | Offline | Click path | CI | Decision |
|---|---|---|---|---|
| Folium/Leaflet | tile policy required | callback integration extra | moderate | defer |
| Streamlit component | local server | strong | broad setup | defer |
| matplotlib | yes | static | good | reject for selection milestone |
| self-contained HTML/SVG | yes | client-side preview/ID | deterministic text | select |

## Preserved Selected Contract

```text
cell CRS: EPSG:5179
cell center: Task 035B feature x/y
cell side: explicit positive map config value
ring: SW → SE → NE → NW → SW
orientation: projected counter-clockwise
clipping: none
WGS84 conversion: each unique corner
MGRS: precision 5, uppercase, stripped
excluded visible by default
valid red selectable
source-zone/diagnostics non-scoring
```

The package contains target marker, ordered candidate polygons, selected ID, selection style, fixed-order legend, source/rendered summaries, and warnings.

# Master Review Finding A — Selection Lifecycle

## Problem found

The pre-amendment contract allowed an initial package with:

```text
selected_candidate_id=None
```

It also rejected a requested ID inconsistent with the package-selected ID without saying whether `None` was inconsistent. This made first selection from the initial map ambiguous.

## Alternatives considered

| Rule | Result |
|---|---|
| Require package to be preselected before service call | rejected; prevents normal first-selection flow |
| Ignore every package-selected mismatch | rejected; permits conflict with visible authoritative state |
| Allow `None` and exact match; reject different non-None ID | selected |

## Selected exact rule

```text
package.selected_candidate_id is None:
  included selectable requested candidate succeeds

package.selected_candidate_id == requested candidate_id:
  succeeds

package.selected_candidate_id is another candidate:
  conflicting package selection error
```

The service returns only an immutable `SelectedLaunchSiteRecord` and does not mutate the package. A controller may rebuild the package with the candidate ID to synchronize selected polygon, summary, and legend.

## Builder-selected rules

```text
None selected ID:
  zero selected polygons
  summary selected count 0
  legend selected count 0

non-None selected ID:
  source candidate exists
  polygon is included
  candidate is selectable
  exactly one selected polygon
  summary selected count 1
  legend selected count 1
```

Unknown, hidden, excluded, or non-selectable config-selected IDs are fatal.

# Master Review Finding B — Deterministic SVG Viewport

## Problem found

The pre-amendment renderer consumed WGS84 geometry but did not specify viewport dimensions, reference coordinates, local projection, aspect fitting, y inversion, antimeridian handling, zero spans, target-only output, numeric formatting, or element order.

## Renderer config selected

```python
@dataclass(frozen=True)
class LocalHtmlMapRenderConfig:
    width_px: int = 1000
    height_px: int = 800
    padding_px: int = 40
```

Dimensions are positive non-boolean integers; padding is a non-negative non-boolean integer; twice the padding must be smaller than each dimension.

## Bounds selected

```text
all included candidate polygon WGS84 ring points
plus target marker
hidden candidate geometry excluded
target always included
```

Reference coordinates are the arithmetic means of unique bound-input longitude and latitude values.

## Display transform selected

```python
x_local = radians(lon - reference_lon) * cos(radians(reference_lat))
y_local = radians(lat - reference_lat)
```

This is a renderer-only schematic transform, not analysis or geodetic measurement authority.

If raw longitude span exceeds 180 degrees, the renderer raises `LocalHtmlMapRendererError` and does not unwrap longitude.

## Fit selected

Both spans non-zero:

```python
scale = min(usable_width / x_span, usable_height / y_span)
```

The fitted content is centered in the padded viewport and y is inverted for SVG.

```text
zero x span: x centered, y fitted
zero y span: y centered, x fitted
both spans zero: all points at viewport center
target-only: valid both-zero-span rendering
```

## Determinism selected

```text
viewBox 0 0 width_px height_px
candidate order = package order
target after candidate polygons
legend and side-panel contract order
fixed six-decimal SVG geometry values
negative zero normalized
UTF-8, newline \n, final newline
```

# Master Review Finding C — HTML/JavaScript Safety

## Problem found

Package-controlled strings may contain script tags, quotes, MGRS text, reasons, warnings, and attribute-breaking text. The pre-amendment contract did not freeze escaping or safe script data flow.

## Escaping selected

Every data-derived text or attribute value uses semantics equivalent to:

```python
html.escape(value, quote=True)
```

This includes scenario, IDs, MGRS, reasons, diagnostics, warnings, labels, side-panel content, titles, and `data-candidate-id`.

## Prohibited behavior selected

```text
no raw data interpolation into executable JavaScript
no data-derived innerHTML
no eval
no Function constructor
no document.write with package data
no raw package JSON in script
no data-derived inline event handlers
no external script/font/tile/image/network URL
```

Client updates use `textContent`, `classList`, and `dataset` on escaped DOM values.

Exact CSP selected:

```text
default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; img-src data:;
```

## Click semantics selected

Three different states are frozen:

```text
package-authoritative selection
browser transient preview
Python SelectedLaunchSiteRecord
```

A selectable click may display details and a preview-only highlight and expose ID to a controller. It does not mutate package state, alter static summary/legend counts, create a selected record, or claim Python selection succeeded.

A non-selectable click may show details and exclusion reason but cannot receive the selectable preview class. Reset restores package-selected state.

## Task 035D Test Matrix Added by Amendment

### Selection lifecycle

```text
unselected package selection succeeds
matching selected package succeeds
conflicting selected package fails
selection does not mutate package
selected record reuses popup MGRS
optional rebuilt package has one selected polygon
None-selected package has zero selected counts
invalid config-selected IDs are fatal
```

### SVG viewport

```text
default and invalid renderer config
bounds include target and visible polygons only
local equirectangular formula
aspect-ratio preservation
y-axis inversion
zero-x, zero-y, both-zero spans
target-only rendering
antimeridian rejection
candidate order and target-after-candidates
six-decimal formatting
negative-zero normalization
repeated-output determinism
```

### HTML and click safety

Use malicious values containing script tags, closing-script text, quotes, apostrophes, ampersands, angle brackets, and attribute-breaking text.

```text
escaped inert output only
no closing-script or event-handler injection
no data-derived innerHTML
safe data-candidate-id
no eval/Function/document.write/raw package JSON
exact CSP
no external resources
non-selectable cannot receive selectable preview class
click does not alter serialized summary/legend counts
package-selected and transient-preview remain separate
reset restores package-selected state
browser does not create/claim Python selected record
```

## Task 035D Handoff Value

The amended audit now freezes:

```text
real input authority
cell-size responsibility
projected polygon order
coordinate adapters and MGRS policy
immutable map/popup/summary/selection types
initial and rebuilt selection lifecycle
renderer config and viewport mathematics
one-dimensional and zero-span behavior
antimeridian rejection
HTML and attribute escaping
JavaScript restrictions and CSP
package selection versus transient preview
complete focused test matrix
protected runtime and dependency scope
```

This reduces Task 035D to bounded TDD implementation and local optional-dependency/render verification.

## Actual Amendment Result

```text
architecture contract: amended
Task 035D handoff: amended
decision record: amended
EXP-053 audit: amended
Draft PR body: amended separately
runtime source changes: none
test/example changes: none
workflow/dependency changes: none
GIS/generated changes: none
coordinate conversion executed: no
map rendered: no
browser tested: no
candidate selected at runtime: no
```

## Historical Evidence Limitation

Task 035B local full-pytest totals differ across historical records:

```text
PR #99 body: 831 passed
Task 035B handoff: 821 passed
EXP-052: 782 passed
```

This audit does not choose one historical count or claim a new local result. Current merged runtime API and exact Task 035C final-head GitHub Actions evidence are the authorities for this documentation contract.

## Metrics

```text
runtime files modified: 0
test files modified: 0
example files modified: 0
workflow/dependency files modified: 0
GIS/generated files modified: 0
new Issues/branches/PRs: 0
```

## Interpretation

The amended contract advances toward the colored launch-area map while separating analysis authority, renderer geometry, schematic SVG projection, user-facing coordinates, package-selected state, browser-only preview, and Python selection records.

The resulting HTML/SVG remains a local schematic visualization of center-based offline terrain/surface-obstacle risk proxy results. It is not measured RF coverage, terrain-accuracy evidence, a link budget, communication-success evidence, reconnaissance-success evidence, flight-feasibility evidence, or airspace-approval evidence.

## Limitations

- No map package or renderer implementation exists in Task 035C.
- No coordinate conversion was executed.
- No HTML/SVG artifact was generated or visually inspected.
- No JavaScript or browser behavior was executed.
- No real candidate click or selected record was produced.
- Candidate polygons remain future visualizations of center-based analysis, not per-point area validation.

## Figure and Table Candidacy

Future validated Task 035D output may support candidate state/color count tables, renderer-neutral schema diagrams, sanitized synthetic/offline map figures, selection lifecycle diagrams, and selected-record field tables.

No current figure or map is produced by this audit.

## Public Repository Sensitivity Check

This record contains only public code contracts and aggregate process facts. It contains no actual coordinate, private path, GIS raster, generated HTML, screenshot, credential, operational command, device command, autopilot command, or flight-control output.
