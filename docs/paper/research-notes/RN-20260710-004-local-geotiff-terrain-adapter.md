# RN-20260710-004 - Local GeoTIFF Terrain Adapter

## Research Question

Can user-prepared local DEM/DSM GeoTIFFs supply terrain profiles through the existing adapter interface without making GIS tooling a package dependency?

## Background

Task 017A separated profile extraction from storage, while Task 018A prepared aligned local DEM and temporary DSM proxy outputs.

## Method / Reasoning

The adapter lazily loads rasterio, converts bottom-left project indices to top-left raster rows, maps raster metadata into the existing policy schema, and rejects invalid or missing cells.

## Findings

The adapter interface supports metadata validation and profile sampling while keeping local paths and large GIS files outside public metadata and Git.

## Relevance to Paper

This establishes a reproducible boundary between terrain analysis logic and locally managed raster inputs.

## Relevance to Implementation

The same extract_terrain_profile_from_adapter workflow now accepts synthetic fixtures and aligned local GeoTIFF terrain sources.

## Limitations

The local DSM is a land-cover-derived temporary proxy, not measured building or vegetation height. Runtime behavior depends on locally installed rasterio and user-provided aligned files.

## Public Repository Sensitivity Check

No private absolute path, credential, sensitive coordinate, or GIS raster is committed.

## Follow-up Tasks

Perform QGIS visual alignment review and evaluate authoritative building-height and vegetation-height sources.
