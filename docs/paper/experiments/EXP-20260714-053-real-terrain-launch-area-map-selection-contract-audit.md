# EXP-20260714-053 - Real-Terrain Launch-Area Map and Selection Contract Audit

## Purpose

Audit the merged Task 035B runtime result, existing synthetic map/display scaffolds, coordinate policy, dependencies, and relevant tests before implementing a real-terrain colored launch-area map and launch-site selection service.

This is a code/document contract audit. It is not a runtime map experiment, coordinate-conversion execution, GIS smoke, UI test, terrain-accuracy validation, or field RF validation.

## Start State

```text
PR #99: merged
merge commit / latest main: a9886eb12633f27cea3556a8e7b9ab4a142667a1
Issue #98: closed / completed
Issue #100: open
conflicting open PRs: none
```

Task 035B source, tests, handoff, and EXP-052 were present on latest main before Task 035C documentation work began.

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
tests/test_real_terrain_candidate_analysis.py
tests/test_map_outputs.py
tests/test_candidate_display_outputs.py
tests/test_coordinate_io_policy.py
Task 035A architecture/decision documents
Task 035B handoff and EXP-052
MGRS external I/O policy
```

No local file, raster, renderer, or browser was accessed.

## Audit Questions

1. Which Task 035B objects are the authoritative input?
2. Can existing synthetic map/display types represent real exclusions and source-zone availability?
3. How is candidate cell size supplied without changing the Task 035B result?
4. What polygon geometry and order are deterministic?
5. Which coordinate form is authoritative at analysis, renderer, and user boundaries?
6. Which immutable map/popup/legend/selection types are required?
7. Which candidates are visible and selectable?
8. Which failures are fatal and which produce warnings?
9. Which concrete renderer is the smallest offline-first next step?
10. What exact Task 035D source/test scope minimizes Local Execution Agent work?

## Findings

### Task 035B authority

`RealTerrainLaunchAreaResult.candidate_records` and `.candidate_features` preserve deterministic same-order candidate data. The real feature x/y values are actual projected candidate points in EPSG:5179, not synthetic placeholder values.

The result does not retain candidate spacing. A future map layer therefore needs an explicit cell-size input and cannot independently prove it equals the original analysis spacing.

### Synthetic map incompatibility

The current synthetic builder generates `x=index*500, y=0`, and the existing map package requires route and waypoint structures. It is protected as a regression fixture and is not a real-terrain integration path.

### Display incompatibility

The current display schema requires non-null scores and concrete source-zone values. Task 035B exclusions correctly use `None` scores, and source-zone states may be `not_requested`, `unavailable`, or `not_applicable`. A separate real-terrain popup schema is required.

### Coordinate boundary

Repository policy requires MGRS for default user-facing target, candidate, and launch-site coordinates. EPSG:5179 remains the cell construction and downstream route-engine authority. WGS84 is renderer-internal geometry.

The current coordinate module lacks a complete projected-output conversion path, but the optional GIS dependency group already includes `pyproj` and `mgrs`.

### Renderer boundary

No concrete renderer dependency exists. Package/selection correctness can remain pure Python and dependency-neutral.

## Alternatives

### Map endpoint

| Alternative | Result |
|---|---|
| Candidate popup records only | rejected; no visible geometry progress |
| Renderer-neutral package and selection service | required core |
| Core plus local self-contained HTML/SVG | selected for Task 035D |
| Folium/Streamlit interactive application | deferred; broader dependency/callback/UI boundary |

### Cell size

| Alternative | Result |
|---|---|
| Add spacing to Task 035B result in Task 035C | rejected; docs-only task and frozen runtime contract |
| Infer from candidate points | rejected; arbitrary partial/irregular results make inference unsafe |
| Explicit map config with caller responsibility | selected |

### Coordinate conversion failure

| Alternative | Result |
|---|---|
| Omit one failed candidate with warning | rejected; breaks included-set geometry/popup parity |
| Fatal package error | selected |

### Renderer

| Alternative | Offline | Click path | CI | Decision |
|---|---|---|---|---|
| Folium/Leaflet | tile policy required | browser click possible; Python callback extra | moderate | defer |
| Streamlit component | local server | strong | broad UI setup | defer |
| matplotlib | yes | static | good | reject for selection milestone |
| self-contained HTML/SVG | yes | client-side highlight/ID | deterministic text | select |

## Selected Contract

### Cell geometry

```text
CRS: EPSG:5179
center: Task 035B feature x/y
side: explicit positive map config value
ring: SW → SE → NE → NW → SW
orientation: projected counter-clockwise
clipping: none
```

Four unique corners are converted individually to WGS84; the converted southwest point closes the ring.

### Coordinate conversion

```text
EPSG:5179 → WGS84: renderer geometry, always_xy
EPSG:5179 → MGRS: user-facing target/candidate/launch-site fields
MGRS precision: 5 digits, uppercase, stripped
```

The five-digit formatting policy does not assert one-meter terrain or RF accuracy.

### Popup and package

A separate immutable real-terrain popup permits optional scores, optional source-zone values, explicit source-zone availability, candidate state/reason, MGRS, and approved Fresnel diagnostics.

The package contains target marker, ordered candidate polygons, selected ID, selection style, fixed-order legend, full/source and rendered counts, and warnings.

### Visibility and selection

Excluded polygons are visible by default and gray. They may be omitted by map config without mutating the Task 035B result.

Selectable candidates satisfy:

```text
valid_scored
score present
non-excluded color
within operating radius
```

A valid red candidate remains selectable. Selection is by exact candidate ID, one active selection only, with no automatic best-site choice or recomputation.

### Failure policy

Fatal:

```text
zero source candidates
record/feature mismatch or duplicate IDs
invalid geometry
required coordinate conversion failure
unknown, hidden, or non-selectable selected ID
missing required MGRS
```

Warning/non-fatal:

```text
zero selectable candidates
all excluded polygons hidden
source-zone unavailable/not requested/not applicable
```

### Local renderer

Task 035D may render a self-contained HTML/SVG artifact with no base tile, external network, external script, or added package dependency. Browser-side click may highlight and display `candidate_id`; authoritative selection remains the Python selection service.

File output is explicit, overwrite-protected, never committed, and potentially sensitive because it contains WGS84 and MGRS data.

## Task 035D Handoff Value

The audit freezes:

```text
exact module and test candidates
immutable schemas
record/feature parity rules
polygon construction and order
converter protocols and call counts
MGRS output policy
style/legend/popup behavior
selection and failure semantics
offline renderer and file policy
protected runtime modules
```

This reduces the Local Execution Agent task to bounded TDD implementation and local optional-dependency/render verification.

## Historical Evidence Limitation

Task 035B local full-pytest counts differ across historical records:

```text
PR #99 body: 831 passed
Task 035B handoff: 821 passed
EXP-052: 782 passed
```

This audit does not choose one historical count or claim a new local result. The merged runtime API and Task 035C final-head GitHub Actions result are used for the current contract. The provenance discrepancy may be reconciled separately.

## Actual Result

```text
architecture contract: created
decision record: created
Task 035D handoff: created
runtime source/test changes: none
coordinate conversion executed: no
map rendered: no
candidate selected: no
GIS dependency installed or invoked: no
```

## Metrics

```text
runtime files modified: 0
test files modified: 0
example files modified: 0
workflow/dependency files modified: 0
GIS/generated files added: 0
```

The exact documentation-only changed-file count and final-head standard CI result are recorded in the Draft PR and completion report.

## Interpretation

The selected contract visibly advances toward the project’s colored launch-area map requirement while preserving numerical and synthetic compatibility. It separates analysis authority, renderer geometry, user-facing coordinates, local visualization, and launch-site selection so failures remain testable and isolated.

## Limitations

- No map package or renderer implementation exists in Task 035C.
- No coordinate conversion was executed.
- No HTML/SVG artifact was generated or reviewed.
- No real candidate click or selected record was produced.
- Candidate cell polygons remain a future visualization of center-based analysis, not per-point area validation.
- No measured RF, terrain accuracy, communication, reconnaissance, flight, or approval outcome was validated.

## Figure and Table Candidacy

Future Task 035D validated output may support:

```text
candidate color/state count table
renderer-neutral schema diagram
sanitized synthetic/offline map figure
selection record field table
```

No current figure or map is produced by this audit.

## Public Repository Sensitivity Check

This record contains only public code contracts and aggregate process facts. It contains no actual coordinate, private path, raster, generated HTML, screenshot, credential, operational command, device command, autopilot command, or flight-control output.
