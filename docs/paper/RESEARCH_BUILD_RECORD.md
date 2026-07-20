# Research Build Record

## Document Metadata

| Field | Value |
|---|---|
| Project | UAV RF Terrain Planner |
| Research purpose | Offline research, education, and simulation support for DSM-based terrain/RF shielding proxy analysis, launch-area visualization, route analysis, and waypoint reporting. |
| Created | 2026-07-16 |
| Last updated | 2026-07-21 |
| Authoritative branch | `main` for merged evidence; `agent/task-036b-real-terrain-minimum-altitude-core` for current Task 036B evidence. |
| Ledger content basis | `f3a075834092b3f782139333a7b58a443c0548ea` (PR #109 merge commit; final head `4107547`, CI #899 / run 29710579465 success). |
| Record responsibility | GPT Master owns paper interpretation; Local Execution Agents record only verified build, test, PR, CI, and limitation evidence. |
| Research limit | Results are terrain/surface-obstacle proxies, not actual RF, flight-feasibility, reconnaissance-success, or approval evidence. |

This ledger connects, but does not replace, the historical
`experiment-log.md`, individual [experiments](experiments/README.md),
[decisions](decisions/README.md), and task handoffs.

## Non-Recursive Final-Head Evidence Policy

This ledger records the verified content basis available when it is committed. It must
not be amended by a follow-up commit solely to chase the CI result of that new commit.
For an open Draft PR, the exact final-head GitHub Actions run is recorded in the PR
completion/review comment and the Local Execution Agent completion report. After merge,
the next Task or a dedicated reconciliation records the final head, merge commit, Issue
closure, and exact CI evidence here. This preserves an auditable record without an
infinite commit-to-CI update cycle.

## Research System Summary

| Boundary | Current evidence |
|---|---|
| Input | MGRS user-facing coordinates; internally projected EPSG:5179 points; synthetic or local prepared DEM/DSM through adapters. |
| Processing | DSM profile, LOS/Fresnel proxy, heuristic score/color, selected launch area, deterministic route graph/Dijkstra, handoff-based waypoint reporting, and a documented future route-level altitude-proxy boundary. |
| Output | Color launch-area records, MGRS-facing selected site, route candidates, and approximately 500 m MGRS waypoint reports. |
| Implemented scope | Task 035G adds reporting over Task 035EF complete route handoffs. Task 036A is merged approved contract evidence; Task 036B is in progress for pure prepared-evidence contracts and calculation only. |
| Explicit non-claims | No autopilot, route execution, field RF validation, real flight validation, obstacle absence proof, or airspace approval. |

## Core Formula and Policy Ledger

| Policy | Current rule | Evidence |
|---|---|---|
| LOS | DSM samples are compared with the line between endpoint flight/antenna MSL. | `src/uav_rf_terrain/los.py`; EXP-005; EXP-052 |
| Fresnel | First Fresnel radius and DSM clearance/intrusion are derived per profile sample. | `src/uav_rf_terrain/fresnel.py`; EXP-006; EXP-052 |
| Strict LOS cap | `dsm_los_score == 0` forces shielding stability to zero. | `src/uav_rf_terrain/scoring.py`; EXP-007 |
| Shielding score | `0.40 * DSM LOS + 0.60 * DSM Fresnel average`. | `AGENTS.md`; `scoring.py`; EXP-007 |
| Overall score | `0.80 * shielding stability + 0.20 * distance score`. | `AGENTS.md`; `scoring.py`; EXP-007 |
| Color | Green/yellow/orange/red/excluded are heuristic visualization classes, not field outcomes. | `classification.py`; EXP-008; DEC-005 |
| 3D radius | Valid real-terrain nodes require 3D airborne distance within operation radius. | `real_terrain_route_analysis.py`; EXP-055; DEC-007 |
| Route modes | Shielding minimum 0.90/0.10, balanced 0.70/0.30, detour stability 0.85/0.15 with reviewed risk multiplier. | `real_terrain_route_outputs.py`; EXP-055; DEC-007 |
| Dijkstra/diversity | Deterministic ordering, bounded expansion, duplicate rejection, and directed-edge overlap retry. | `route_pathfinding.py`; EXP-055; DEC-007 |
| Waypoint sampling | Cumulative route 3D handoff distance, exact-node reuse, linear elevation interpolation, conservative color/min-score interpolation. | `real_terrain_waypoint_reporting.py`; EXP-056; DEC-008 |
| Route altitude | Approved complete route authority plus authoritative actual selected launch, exact-parity terrain session, and dedicated bounded radial DSM/DEM profiles; one constant-MSL result plus independent fixed-AGL margin assessment per source route. | Task 036A architecture; EXP-057; approved DEC-009 |

## Build Chronology

Legacy Task 001-034 records remain linked by their individual EXP entries. Earlier
head/merge/CI data not revalidated in this amendment is deliberately marked legacy
rather than inferred.

| Build ID | Date | Task | Purpose | Issue / PR | Base / final / merge | Data type | Focused / full tests | Local / Actions | Status | EXP / DEC / handoff | Limitations and paper contribution |
|---|---|---|---|---|---|---|---|---|---|---|---|
| BUILD-20260708-001 | 2026-07-08 | 001-012 | Core synthetic coordinate, terrain, LOS/Fresnel, scoring, classification, route/waypoint, and map-ready scaffolds. | Legacy Issues/PRs #7-#32; see EXP-001..012. | Legacy metadata retained in archives; not revalidated here. | Synthetic/in-memory only. | Individual evidence in EXP-001..012. | CI evidence varies by individual EXP; local status is archival. | Merged historical scope. | EXP-001..012; `experiment-log.md`. | Methods scaffolds, not GIS/RF/flight evidence. |
| BUILD-20260709-002 | 2026-07-09 | 013-015 | Research records, paper preparation, and minimum-altitude scaffold. | Legacy PRs; see experiment index. | Legacy archive. | Documentation/synthetic profiles. | Individual EXP entries. | Archival evidence only. | Merged historical scope. | EXP-013..015; decision log. | Minimum altitude is proxy support, not approval evidence. |
| BUILD-20260710-003 | 2026-07-10 | 016A-018F | Terrain-data policy, local preprocessing handoff, adapter, and source-boundary records. | Legacy PRs; see EXP-002..009. | Local GIS remains outside Git. | Local/public prepared DEM/DSM plus synthetic tests. | Individual EXP entries. | Local GIS checks are distinct from CI. | Merged historical scope. | Terrain policy and handoffs. | No repository GIS raster or field validation. |
| BUILD-20260711-004 | 2026-07-11 | 020A-021C | Source-zone metadata/classifier and MGRS output boundary. | Legacy PRs; see EXP-010..017. | Legacy archive. | Synthetic plus local source-zone smoke. | Individual EXP entries. | Local raster smoke not CI evidence. | Merged historical scope. | EXP-010..017; MGRS policy. | Source-zone labels are interpretation metadata. |
| BUILD-20260712-005 | 2026-07-12 | 021D-031B | Candidate preview, JSON/table/report formatter, CLI, and documentation reconciliation. | Legacy PRs; see EXP-018..041. | Legacy archive. | Synthetic preview data. | Individual EXP entries. | CI/local evidence separated per EXP. | Merged historical scope. | EXP-018..041. | No real terrain/UI/field output claim. |
| BUILD-20260713-006 | 2026-07-13 | 032AB-032CD | Dominant-obstacle and diagnostic appendix integration. | Legacy PRs; see EXP-042..047. | Legacy archive. | Synthetic diagnostics. | Individual EXP entries. | Archival CI/local evidence. | Merged historical scope. | EXP-042..047; DEC-002/003. | Diagnostic proxy does not alter primary score/color. |
| BUILD-20260714-007 | 2026-07-14 | 034B-034D, 035A-035D | Diagnostic delivery, real-terrain contract, candidate analysis, map, and selection. | PR #103. | Final `8fb29c7`; merge `1933ce2`; merged 2026-07-16. | Synthetic adapters and renderer fakes. | 33 focused; 864 full. | Local checks passed; CI #874 / 29460010316 success. | Merged. | EXP-048..054; DEC-004..006; Task 035D handoff. | No real GIS/browser/field validation. |
| BUILD-20260716-008 | 2026-07-16 | 035EF | Complete selected-launch route recommendation and handoff contract. | Issue #104; PR #105. | Final `4308aba`; merge `7c49c8f`; merged 2026-07-16. | Synthetic in-memory adapter. | graph 7 + pathfinding 4 + analysis 5 + outputs 12 = 28; 892 full. | Local checks passed; CI #881 / 29469082285 success. | Merged; Issue #104 closed/completed. | EXP-055; DEC-007; Task 035EF handoff. | No GIS route/browser/field validation. |
| BUILD-20260716-009 | 2026-07-16 | 035G | Real-terrain route waypoint reporting over complete handoffs. | Issue #106; PR #107. | Final `36935ac`; merge `7b39a21`; merged 2026-07-19. | Synthetic immutable route contracts. | Initial focused 7/full 899; review-amendment focused 22/full 914. | Exact final-head CI #890 / 29473229092 success. | Merged; Issue #106 closed/completed. | EXP-056; DEC-008; Task 035G handoff. | No terrain reanalysis, GIS report, browser/UI, or field validation. |
| BUILD-20260716-010 | 2026-07-20 | 036A | Define real-terrain minimum-altitude analysis boundary. | Issue #108; PR #109. | Final `4107547`; merge `f3a0758`; merged 2026-07-20. | Documentation and existing synthetic contracts only. | Focused 19; full 913 passed, 1 skipped. | CI #899 / 29710579465 success. | Merged; Issue #108 closed/completed. | EXP-057; approved DEC-009; Task 036A handoff. | No runtime, GIS, field, browser/UI, or operational output. |
| BUILD-20260720-011 | 2026-07-20 | 036B | Implement immutable prepared-evidence contracts and a pure minimum-altitude proxy engine. | Issue #110; Draft PR #111. | Base `f3a0758`; local final amendment verified. | Synthetic prepared profiles only. | Focused 106; related Task 035EF/035G plus legacy 58; full 1019 passed, 1 skipped. | Fresh local verification complete; exact final-head CI remains pending for the external completion report. | Local verification complete; publish/review pending. | EXP-058; DEC-009; Task 036B handoff. | No terrain session, GIS sampling, route selection, UI, device, or field claim. |

## Experiment Evidence Ledger

| EXP ID | Purpose / data type | Method and actual result | Verification and paper use | Limitations / related build |
|---|---|---|---|---|
| EXP-001..012 | Core scaffold through map-ready output; synthetic/in-memory. | Coordinate, terrain, profile, LOS, Fresnel, score, color, route, waypoint, scenario, and map-output boundaries were added. | Individual historical EXP records; method tables only. | BUILD-20260708-001; no GIS, RF, or flight evidence. |
| EXP-013..017 | Paper/altitude, terrain policy/adapter, and MGRS/source-zone boundaries. | Documentation, synthetic adapter, and local-policy evidence. | Individual records and handoffs; methods/provenance tables. | BUILD-20260709-002 / 20260710-003 / 20260711-004; no field evidence. |
| EXP-018..041 | Preview/formatter/CLI/report workflow. | Deterministic synthetic preview outputs and explicit files were implemented. | Individual records; output-contract tables. | BUILD-20260712-005; not real terrain/UI validation. |
| EXP-042..047 | Dominant-obstacle diagnostics. | Optional diagnostic projection and appendix integration retained primary scoring. | Individual records; diagnostic-method tables. | BUILD-20260713-006; diagnostic proxy only. |
| EXP-048..050 | Diagnostic appendix table/delivery. | Formatter and opt-in CLI output were verified. | Individual records; appendix-output tables. | BUILD-20260714-007; no operational evidence. |
| EXP-051..053 | Real-terrain analysis/map contract audits. | Boundaries, synthetic adapter records, renderer-neutral map/selection contracts were recorded. | Individual records; architecture figures/tables. | BUILD-20260714-007. |
| EXP-054 | Map/selection implementation; synthetic converter/fakes. | Final focused 33 and full 864; CI #874 success. | Candidate/map contract table; corrected below. | BUILD-20260714-007; no browser/GIS/field run. |
| EXP-055 | Route recommendation; synthetic adapter. | Final focused 28 and full 892; CI #881 success. | Graph/route mode/verification table. | BUILD-20260716-008; no GIS route/browser/field run. |
| EXP-056 | Waypoint reporting; synthetic complete route contract. | Initial focused 7/full 899 plus review-amendment authority, endpoint, warning, guard, and mutation checks. | Final focused 22/full 914; CI #890 success; waypoint semantics/verification table. | BUILD-20260716-009; no GIS/UI/field run. |
| EXP-057 | Real-terrain minimum-altitude contract audit; documentation and synthetic-contract sources. | Proposed actual selected-launch, exact-parity session, dedicated radial profile, constant-MSL, and independent fixed-AGL baseline boundary; no runtime added. | Future authority/distance/formula table only. | BUILD-20260716-010; no GIS/UI/field run. |

All individual EXP files remain the authoritative detailed method and limitation record.

## Data Provenance

| Data category | Availability and permitted interpretation |
|---|---|
| Synthetic DEM/DSM | Present as in-memory test fixtures; suitable for deterministic code boundary tests only. |
| Local/public DEM/DSM | Local prepared data and scripts/checkpoints exist outside ordinary Git; use requires documented source/license/processing metadata. |
| Source-zone data | Policy/classifier metadata and local smoke records exist; labels are interpretation metadata. |
| Actual RF measurement | Not available; not performed. |
| Actual flight data | Not available; not performed. |
| Generated artifact | Not committed; generated HTML/JSON/CSV/images and GIS outputs remain outside repository evidence. |

## Verification Ledger

| Evidence | Current verified record | Interpretation |
|---|---|---|
| Local focused tests | Initial Task 035G evidence: reporting 5, outputs 2; review-amendment focused suite: 22 passed. | Local source-contract verification only. |
| Local full tests | Initial Task 035G evidence: 899 passed; review-amendment full suite: 914 passed. | Local regression evidence only. |
| Compileall / Ruff / mypy / diff | Passed for the initial Task 035G head and the review-amendment content basis. | Build-quality evidence; not field validation. |
| GitHub Actions | Task 035G final `36935ac`: CI #890 / 29473229092 success; merged through `7b39a21`. | Independent hosted source checks; exact final head confirmed after merge. |
| Real GIS smoke | Local terrain preprocessing/adapter checks exist in specific handoffs; real route smoke not performed. | Do not generalize to route/waypoint validation. |
| Browser smoke | Not performed for Task 035EF/035G. | No browser/UI claim. |
| Field RF validation | Not performed. | No communication-performance claim. |

## Paper Evidence Matrix

| Paper section | Claim | Build / EXP / DEC evidence | Potential table or figure | Limitation |
|---|---|---|---|---|
| Method: terrain analysis | DSM-based LOS/Fresnel proxy processing exists. | BUILD-20260708-001; EXP-004..007. | Formula and synthetic case table. | No field RF correlation. |
| Method: score/color | Heuristic score and visual classes are explicit. | EXP-007/008; `scoring.py`; DEC-005. | Weights and thresholds table. | Weights are not calibrated performance values. |
| System: terrain provenance | Data policy distinguishes synthetic/local/public records. | BUILD-20260710-003; terrain policy. | Provenance table. | No Git-hosted broad GIS dataset. |
| System: map/selection | Renderer-neutral candidate map and immutable selection exist. | BUILD-20260714-007; EXP-054; DEC-006. | Package/selection architecture diagram. | No browser or real GIS rendering result. |
| System: route | Deterministic bounded route candidates exist. | BUILD-20260716-008; EXP-055; DEC-007. | Route mode and guard table. | No real route or flight validation. |
| System: waypoint | Deterministic handoff-based reports exist. | BUILD-20260716-009; EXP-056; DEC-008. | Sampling/value-semantics table. | No waypoint usability study or field data. |
| Future system: altitude | A proposed actual-launch, route-authority, exact-parity-session, and dedicated-profile contract is recorded. | BUILD-20260716-010; EXP-057; DEC-009. | Authority, distance, MSL/AGL, and baseline-margin table. | No altitude runtime, GIS smoke, or field evidence. |

## Open Research Questions

1. Real GIS route smoke with documented local raster inputs.
2. Field RF validation and actual link-state correlation.
3. Score-weight and color-threshold calibration.
4. ITM or other propagation-model comparison.
5. Minimum-required altitude validation against terrain/obstacle evidence.
6. Waypoint report usability and human-review study.

## Correction Log

| Date | Affected document | Old value | Corrected value | Evidence | Reason |
|---|---|---|---|---|---|
| 2026-07-16 | EXP-054 | focused 32; full 863 | focused 33; full 864 | PR #103 final `8fb29c7`; merge `1933ce2`; CI #874 / 29460010316 success | Final amendment test counts were not reflected. |
| 2026-07-16 | EXP-055, master plan, research index | PR #105 Draft/pending phrasing or incomplete reproduction fields | PR #105 merged; Issue #104 completed; final 28 focused, 892 full, CI #881 | PR #105 final `4308aba`; merge `7c49c8f`; CI #881 / 29469082285 | Final merge and reproduction evidence required reconciliation. |
| 2026-07-16 | This ledger | No cumulative build ledger | Build chronology and verification ledger added | Current repository, Git history, and read-only GitHub metadata | Preserve auditable cross-task research evidence. |
| 2026-07-20 | BUILD-20260716-009 and EXP-056 | Draft/pending PR #107 evidence | Final `36935ac`; merge `7b39a21`; Issue #106 completed; CI #890 / 29473229092 success | GitHub PR #107 and Issue #106 state | Post-merge reconciliation required by the non-recursive policy. |
