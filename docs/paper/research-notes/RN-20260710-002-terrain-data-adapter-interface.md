# RN-20260710-002 - terrain data adapter interface

## Date

2026-07-10

## Related Task / Issue / PR

Task 016B - Terrain Data Adapter Interface Scaffold

## Research Question

How should the project represent future DEM/DSM terrain access without adding real terrain files or external geospatial dependencies before the data policy and local data path are ready?

## Background

Task 016A established that project terrain data should be user-produced, redistributable processed data with source, license, processing, CRS, and alignment metadata. Task 016B turns that policy into a narrow software boundary that future terrain loaders can implement.

## Method / Reasoning

The scaffold defines immutable metadata dataclasses, a terrain adapter protocol, a metadata alignment validator, and an in-memory synthetic adapter. The design keeps DEM and DSM access behind index-based methods so later storage-specific loaders can be added without changing downstream LOS, Fresnel, scoring, or altitude-planning code.

## Findings

- DEM/DSM metadata alignment should be checked before analysis code consumes terrain samples.
- CRS, resolution, width, height, bounds, and vertical datum are the minimum alignment checks for the current scaffold.
- Synthetic in-memory terrain remains sufficient for adapter tests and does not require real terrain files.
- Metadata strings need a public repository sensitivity guard so local private paths do not enter committed records.

## Relevance to Paper

This note supports the paper's reproducibility and data-governance discussion by separating the algorithmic interface from the acquisition and redistribution status of real terrain data.

## Relevance to Implementation

Future DEM/DSM loaders can implement the same adapter interface while preserving the current pure Python tests and synthetic fixtures.

## Limitations

The scaffold does not prove real data correctness, terrain-source suitability, CRS transformation behavior, vertical datum conversion accuracy, or field outcome validity.

## References Needed

Future work should cite the specific public terrain data provider metadata and license terms selected by the user.

## Public Repository Sensitivity Check

No real terrain files, private coordinates, private local paths, credentials, account identifiers, or restricted source data are included.

## Follow-up Tasks

- Add a real terrain loader only after the user provides a local processed data path and source metadata.
- Extend validation if future data requires documented vertical datum conversion.
