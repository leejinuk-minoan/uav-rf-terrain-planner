# RN-20260710-003 - Terrain Profile Adapter Integration

## Research Question

Can terrain profile extraction consume a storage-independent adapter while preserving the existing synthetic profile behavior?

## Background

Task 016B introduced `TerrainDataAdapter`, but profile extraction still read `SyntheticTerrainGrid` directly.

## Method / Reasoning

A metadata-based coordinate conversion layer and adapter extraction entry point reuse the existing profile sample structures and shared sampling algorithm.

## Findings

Synthetic direct and adapter paths produce compatible sample counts, indices, distances, and DEM/DSM values.

## Relevance to Paper

The adapter boundary separates profile methodology from terrain storage format and supports reproducible synthetic verification.

## Relevance to Implementation

Future local loaders can implement `TerrainDataAdapter` without changing downstream profile data structures.

## Limitations

Only synthetic in-memory terrain is evaluated. No GeoTIFF or field data is loaded.

## Public Repository Sensitivity Check

No private path, sensitive coordinate, credential, or GIS data file is recorded.

## Follow-up Tasks

Implement the separately scoped optional local GeoTIFF adapter and perform local-only smoke verification.
