# RN-20260710-001 - Minimum Required Altitude Model

## Date

2026-07-10

## Related Task / Issue / PR

- Task: 015 - Minimum Required Altitude Model Scaffold
- Issue: none
- PR: #35

## Research Question

How should the project calculate the minimum required MSL and AGL conversions that satisfy DSM LOS/Fresnel clearance proxy conditions?

## Background

Task 013 documented the altitude aid concept, and Task 014 introduced sharded paper logs. Task 015 turns the documented concept into a pure Python scaffold over existing synthetic terrain profiles.

## Method / Reasoning

The model uses analytic per-sample endpoint altitude inversion. For each valid profile sample, it computes path ratio, first Fresnel radius, required DSM clearance, required LOS MSL, and the endpoint MSL needed for the launch-to-target line to satisfy that sample. The final minimum required MSL is the maximum endpoint requirement across valid samples.

## Findings

The scaffold can identify a limiting sample and produce a minimum required MSL over synthetic profiles. It also converts the MSL result to AGL over the highest DEM sample and over the target DEM sample.

## Relevance to Paper

This provides a candidate feature for quantifying altitude-planning support in the airspace-use request context while keeping the method bounded to an offline DSM-based LOS/Fresnel clearance proxy.

## Relevance to Implementation

The implementation adds a pure Python module using the existing `TerrainProfile` data structure. It does not require real DEM/DSM loading or heavy GIS dependencies.

## Limitations

The output is not evidence of real communication success, reconnaissance success, field link validation, flight safety, or airspace approval suitability. Real DEM/DSM adapters, map rendering, and field validation remain outside this task.

## References Needed

- Fresnel clearance threshold references for interpreting the MVP proxy threshold
- Prior work on terrain-profile altitude planning for offline UAV path analysis
- Validation references for separating DSM proxy outputs from field link outcomes

## Public Repository Sensitivity Check

Synthetic data only. No sensitive coordinates, operational details, account information, tokens, keys, private paths, or restricted datasets are included.

## Follow-up Tasks

- Compare synthetic scenarios after more terrain/profile cases are available.
- Decide whether the clearance ratio should remain fixed or become a scenario parameter.
- Add real DEM/DSM adapter validation only in a later controlled task.
