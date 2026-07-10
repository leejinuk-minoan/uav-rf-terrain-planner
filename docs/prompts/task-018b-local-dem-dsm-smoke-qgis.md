# Local Execution Agent Prompt - Task 018B Local DEM/DSM Smoke and QGIS Overlay Check

You are the Local Execution Agent for the UAV RF Terrain Planner project.

Repository:

```text
leejinuk-minoan/uav-rf-terrain-planner
```

## Purpose

Perform the local DEM/DSM smoke test and, if available in your environment, the QGIS overlay visual check prepared by the Cloud protocol.

This is a local execution and reporting task. Use the local terrain files that the user prepared. Do not commit those data files.

## Required starting steps

1. Pull the latest `main`.
2. Confirm that PR #41 / Task 017B is already merged into `main`.
3. Create a new branch:

```text
agent/task-018b-local-dem-dsm-smoke-qgis
```

4. Read the protocol:

```text
docs/tasks/task-018b-local-dem-dsm-smoke-qgis-protocol.md
```

## Local files to check

Required:

```text
METADATA_MAP/DEM_PROCESSED/south_korea_dem_90m_epsg5179_alltiles.tif
METADATA_MAP/DSM_PROXY_FROM_ESA_WORLDCOVER/south_korea_temporary_dsm_proxy_90m_epsg5179.tif
```

Optional:

```text
METADATA_MAP/DSM_PROXY_FROM_ESA_WORLDCOVER/south_korea_landcover_90m_epsg5179.tif
METADATA_MAP/DSM_PROXY_FROM_ESA_WORLDCOVER/south_korea_surface_delta_proxy_90m_epsg5179.tif
```

Record existence checks using repository-relative paths only. Do not write local absolute paths into repository documents.

## Local task scope

Perform only the following:

1. Confirm the expected local files exist or document which are missing.
2. Run `examples/local_geotiff_adapter_smoke.py` against the required DEM/DSM files.
3. Run several short coordinate-segment smoke tests inside valid raster areas.
4. Run one intentional NoData, mask, non-finite, or bounds case if a safe test case is available.
5. If possible, open QGIS and visually overlay DEM, DSM proxy, surface delta proxy, and landcover aligned raster.
6. Record whether the QGIS check was `passed`, `failed`, `needs manual follow-up`, or `not run`.
7. Write the handoff checkpoint:

```text
docs/handoff/task-018b-local-dem-dsm-smoke-qgis-checkpoint.md
```

8. Add the sharded experiment record:

```text
docs/paper/experiments/EXP-20260710-005-local-dem-dsm-smoke-qgis.md
```

9. Update the experiments index:

```text
docs/paper/experiments/README.md
```

10. Update README only with a short link to the Task 018B result location. Do not put long local results in README.
11. Create a PR.

## Suggested smoke command pattern

Use repository-relative file arguments. Adjust coordinates locally after checking valid bounds.

```bash
python examples/local_geotiff_adapter_smoke.py \
  --dem-path METADATA_MAP/DEM_PROCESSED/south_korea_dem_90m_epsg5179_alltiles.tif \
  --dsm-path METADATA_MAP/DSM_PROXY_FROM_ESA_WORLDCOVER/south_korea_temporary_dsm_proxy_90m_epsg5179.tif \
  --start-x <sample_start_x> \
  --start-y <sample_start_y> \
  --end-x <sample_end_x> \
  --end-y <sample_end_y>
```

Do not copy private machine paths into docs.

## QGIS visual check

If QGIS is available, load:

- DEM.
- DSM proxy.
- Surface delta proxy, if present.
- Landcover aligned raster, if present.

Check:

- CRS `EPSG:5179`.
- Layer alignment.
- Coastline and NoData boundaries.
- Tile seam artifacts.
- Suspicious zero-elevation or flat areas.
- Landcover and DSM proxy spatial consistency.

If QGIS cannot be run, record `not run` with the reason. Do not imply it was performed.

## Required reports

### Handoff checkpoint

Create:

```text
docs/handoff/task-018b-local-dem-dsm-smoke-qgis-checkpoint.md
```

Include:

- Environment summary.
- Local files checked.
- Metadata validation result.
- DEM/DSM pair result.
- Smoke-test commands.
- Smoke-test results.
- NoData or bounds case result.
- QGIS overlay result.
- Limitations.
- Public repository sensitivity check.
- Follow-up tasks.

### Experiment record

Create:

```text
docs/paper/experiments/EXP-20260710-005-local-dem-dsm-smoke-qgis.md
```

Use the existing experiment record style under `docs/paper/experiments/`.

Update:

```text
docs/paper/experiments/README.md
```

Add the new experiment index link.

## Git protection rules

Do not commit:

- Actual DEM/DSM files.
- Anything inside `METADATA_MAP`.
- Files ending in `.tif`, `.tiff`, `.img`, `.vrt`, `.zip`, `.aux.xml`, or `.ovr`.
- Private absolute paths.
- Sensitive coordinates.
- Secrets, tokens, credentials, or account identifiers.

Do not modify:

- `pyproject.toml`.
- `.github/workflows/ci.yml`.
- `docs/deployment/android-tmmr-offline-plan.md`.

Do not add:

- GitHub Actions runner expansion.
- Matrix expansion.
- Cache or artifact upload expansion.
- Git LFS usage.
- Package upload.
- Release asset upload.
- Automated large terrain-data download.

If any of the above seems necessary, stop and report to GPT Master and the user before implementing it.

## Wording boundaries

Smoke-test success means only that the software path ran on selected local files. It is not terrain-source accuracy proof, not field validation, and not field-outcome assurance.

Do not add prediction or assurance claims for radio link metrics, operational feasibility, reconnaissance outcome, or approval outcome.

Do not add control workflow artifacts or vehicle execution artifacts.

## Local completion report format

Report:

```text
Task:
Branch:
PR:
Commit:
Changed files:
Local files checked:
Smoke test result:
NoData/bounds case result:
QGIS overlay result:
Protected file check:
GIS/METADATA_MAP commit check:
Private path check:
Forbidden wording check:
Tests/commands run:
CI:
Local verification limits:
Ready for GPT Master review:
```
