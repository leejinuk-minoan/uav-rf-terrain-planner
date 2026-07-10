# Terrain Data Policy

## Purpose

This document defines the terrain data policy for UAV RF Terrain Planner before future real DEM/DSM integration.

The policy clarifies what project DEM/DSM data means, when processed terrain data can be stored in the public repository, what metadata must be preserved, and when work should pause because real DEM/DSM files are required but not yet available.

## Data Definition

Project DEM/DSM data means terrain and surface-elevation data prepared for offline DSM-based LOS/Fresnel Clearance proxy analysis, route analysis, waypoint reporting, and future map/UI output.

For this project, DEM/DSM data is defined as redistributable processed DEM/DSM data when it is created by the user from public source data and the source, license, and processing metadata are documented.

The Korean project wording for this category is 공개 가능 파생 데이터.

This definition covers project-specific sample data, small clipped datasets, and reproducible fixtures derived from public source data. It does not assume that raw source datasets are automatically suitable for repository storage.

## Redistributable Processed DEM/DSM Data

Redistributable processed DEM/DSM data is a project-ready derivative dataset that meets all of the following conditions:

1. The original source is public source data.
2. The user has processed or clipped the data for project use.
3. The source/license/processing metadata is documented.
4. The resulting dataset is suitable for public repository review.
5. The dataset does not contain sensitive coordinates, non-public source material, credentials, tokens, secrets, or private local paths.

DEM/DSM data is not defined as prohibited from repository commit for security reasons by default. Redistributability is managed through source/license/processing metadata and repository storage guidance.

## Required Metadata

Every project DEM/DSM sample or clipped dataset should include metadata that records:

- Source dataset name.
- Source provider or publication channel.
- Source URL or public reference, when appropriate.
- License or terms of use.
- Processing date.
- Processing tool or workflow summary.
- Clipping or resampling method.
- CRS.
- Resolution.
- Bounds.
- Width and height.
- NoData value.
- Vertical datum or height convention.
- Whether the file is DEM, DSM, or a paired product.
- Whether the dataset is a data fixture, clipped project dataset, or larger processed dataset.

Metadata should be written so that GPT Master, Cloud Agent, Codex Local Agent, and future reviewers can distinguish source data, processed data, synthetic data, and future real DEM/DSM integration inputs.

## DEM/DSM Pair Requirements

A DEM/DSM pair used for analysis should be aligned before it is treated as a project dataset.

The pair should have matching or documented-compatible:

- CRS.
- Resolution.
- Bounds.
- Width and height.
- NoData convention.
- Vertical datum or height convention.
- Pixel alignment or sampling assumptions.

If these properties do not match, the dataset should not be treated as analysis-ready until the mismatch is documented and resolved in a later local data-preparation task.

## Repository Storage Guidance

Terrain data should be separated by operational use and file size:

- Data fixture: very small files used for examples, documentation checks, and deterministic tests.
- Clipped project dataset: small or moderate redistributable processed DEM/DSM data clipped for project scenarios.
- Large source dataset: original public source data or broad-area data that is not appropriate for ordinary Git commits.
- Large processed dataset: large derivative output that may be useful but can make normal Git operations difficult.

Source, license, and processing metadata must be documented before a project DEM/DSM sample or clipped dataset is added to the repository.

Small or manageable redistributable processed DEM/DSM data may be included in the Git repository. If files are large, Git LFS or release assets should be considered instead of normal Git commits.

Large raw source datasets should normally stay outside ordinary repository commits.

## Current Data Availability

Actual DEM/DSM data is currently being produced by the user and is not present in this repository for Task 016A.

The user plans to generate the data by processing public source data and will provide the local storage location after the data is ready.

This task does not search for, request, load, or validate actual DEM/DSM files.

If a future task requires real DEM/DSM files, the Cloud Agent or local agent should pause and ask the user to confirm data preparation completion and provide the local data path.

## Public Repository Sensitivity

This is a public repository. New terrain data records and metadata must not include:

- Sensitive coordinates.
- Non-public datasets.
- Credentials, tokens, or secrets.
- Private local paths.
- Account identifiers.
- Restricted source details.

The policy allows 공개 가능 파생 데이터 and redistributable processed DEM/DSM data when source/license/processing metadata is documented. It does not allow unreviewed private data or untracked source assumptions.

## Non-goals

This policy is not a terrain adapter implementation.

This policy does not add real DEM/DSM files, load GeoTIFF files, add GIS dependencies, render maps, or perform field validation.

This policy is not a field validation and not a real communication or flight guarantee. It also does not guarantee reconnaissance or airspace approval outcomes.

## Follow-up Tasks

Future tasks may add:

- DEM/DSM metadata templates.
- A small redistributable processed DEM/DSM data fixture, after metadata review.
- A real DEM/DSM adapter interface scaffold.
- Local data-preparation checks for CRS, resolution, bounds, dimensions, NoData, and height convention.
- Git LFS or release asset guidance if larger project datasets are needed.
