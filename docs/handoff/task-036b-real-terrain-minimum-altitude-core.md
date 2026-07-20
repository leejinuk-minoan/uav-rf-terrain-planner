# Task Handoff

## Current Task

Task 036B - Real-Terrain Minimum-Altitude Core

## Current Branch

`agent/task-036b-real-terrain-minimum-altitude-core`

## Scope

Stage 1 adds immutable prepared-evidence and MGRS-facing output contracts plus a
pure Fresnel inversion engine. It consumes route authority, selected-launch authority,
and already prepared `TerrainProfile` evidence. It does not open a terrain session,
call `sample_point` or `extract_profile`, or load GIS data.

## Current Status

- PR #109 merged at `f3a0758`; Issue #108 closed; DEC-009 approved by GPT Master.
- Task 036B amendment work is local-only under Issue #110 and Draft PR #111.
- The pure core validates exact route/selection authority, prepared 2D and radial
  profile parity, bounded resource inputs, tolerance-aware limiters, and recursive
  immutable MGRS-facing result contracts. The local amendment additionally retains
  private exact source/prepared authority, rejects direct/coordinated mutation and
  list substitution, and validates finite LocalPoint/profile interpolation parity.
- Fresh local evidence: minimum-altitude focused `101 passed`; related Task 035EF/035G
  and legacy regression `58 passed`; full suite `1014 passed, 1 skipped`. The final
  local amendment uses one canonical compact authority snapshot plus a deterministic
  fingerprint and radial replay. Local verification is complete; exact final-head CI
  remains pending until the permitted one-time publish step.
- The target output remains an offline DSM/LOS/Fresnel clearance proxy, not terrain
  clearance certification, flight-safety approval, communication-success evidence, or
  regulatory authorization.

## Next Agent Boundary

Task 036C may open exactly one terrain session and prepare the evidence needed by the
Task 036B pure engine. It must retain the Task 036A exact metadata-parity and
fail-before-profile-sampling sequence.
