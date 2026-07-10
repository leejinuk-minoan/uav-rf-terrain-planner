# DEC-20260710-001 - DEM/DSM redistributable data policy

## Status

Approved

## Date

2026-07-10

## Related Task / Issue / PR

- Task: 016A - Terrain Data Policy Documentation
- PR: TBD

## Decision Owner

GPT Master Agent

## Decision

Public source DEM/DSM data processed by the user is defined as redistributable processed DEM/DSM data when source/license/processing metadata is documented.

Small or manageable redistributable DEM/DSM samples may be included in the Git repository. Large datasets should be reviewed for Git LFS or release asset storage.

## Context

After the repository became public, the project needed a clear rule for whether future DEM/DSM data can be included, how redistributability is assessed, and how ordinary Git operations should be protected from large files.

Actual DEM/DSM data is still being produced by the user and is not required for Task 016A.

## Rationale

The user plans to create project DEM/DSM data by processing public source data. If the resulting files are 공개 가능 파생 데이터 and the source/license/processing metadata is documented, they can support project fixtures or clipped datasets in a public repository.

The policy therefore manages redistributability through documentation rather than treating all DEM/DSM data as prohibited by default.

## Alternatives Considered

- Prohibit all DEM/DSM data from Git commits.
- Continue using only synthetic terrain.
- Manage all real DEM/DSM data only through external paths.
- Include small redistributable datasets in Git while considering Git LFS or release assets for large datasets.

## Impacted Documents

- `docs/data/terrain-data-policy.md`
- `README.md`
- `docs/paper/decisions/README.md`

## Paper Boundary

The paper must clearly distinguish data source, processing workflow, synthetic data, processed DEM/DSM data, and future real DEM/DSM integration.

This decision does not create experiment evidence or field validation evidence.

## Product / Deployment Boundary

Real DEM/DSM connection work is deferred to a later task. Task 016A documents policy only and does not implement terrain adapters or load terrain files.

## Public Repository Sensitivity Check

This decision does not include sensitive coordinates, non-public datasets, credentials, tokens, secrets, account identifiers, or private local paths.

Redistributable processed DEM/DSM data may be stored only when source/license/processing metadata is documented and public repository suitability is reviewed.

## Safety / Non-goals

This decision does not guarantee field communication, field flight, reconnaissance, or airspace approval outcomes.

It is not a field validation and not a real communication or flight guarantee.

## Follow-up Tasks

- Create DEM/DSM metadata templates.
- Define small data fixture placement guidance.
- Implement a real DEM/DSM adapter interface in a separate local-agent task.
- Review Git LFS or release asset handling if large processed datasets are needed.
