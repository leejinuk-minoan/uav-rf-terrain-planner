# Task 017B Local Agent Prompt - Local GeoTIFF Terrain Data Adapter

다음 지시문은 Codex 또는 Claude Code 같은 Local Execution Agent에게 전달한다. 이 Task는 Cloud 단계에서 설계·테스트·리뷰 기준을 선확정한 뒤, 로컬 에이전트가 최소 범위 구현과 검증만 수행하도록 분리한 작업이다.

---

너는 UAV RF Terrain Planner 프로젝트의 Local Execution Agent다.

Repository:

```text
leejinuk-minoan/uav-rf-terrain-planner
```

Base branch:

```text
main
```

New branch:

```text
agent/task-017b-local-geotiff-terrain-adapter
```

Task:

```text
Task 017B - Local GeoTIFF Terrain Data Adapter
```

최근 병합 기준:

```text
PR #38 Task 018A DEM/DSM preprocessing handoff and restore scripts merged
PR #39 Task 017A adapter-based terrain profile extraction merged
PR #39 merge commit: 66b77eb68c75bd42fafa63904a243b1d95c08c22
```

## 1. 먼저 읽을 파일

```bash
sed -n '1,260p' README.md
sed -n '1,260p' docs/tasks/task-017b-cloud-prep-local-geotiff-adapter.md
sed -n '1,280p' docs/data/terrain-data-policy.md
sed -n '1,140p' docs/handoff/dem-processing-checkpoint.md
sed -n '1,140p' docs/handoff/esa-worldcover-dsm-checkpoint.md
sed -n '1,300p' src/uav_rf_terrain/terrain_data.py
sed -n '1,320p' src/uav_rf_terrain/profile.py
sed -n '1,260p' src/uav_rf_terrain/__init__.py
sed -n '1,220p' tests/test_terrain_data.py
sed -n '1,220p' tests/test_profile_adapter.py
```

## 2. 목적

로컬 GeoTIFF DEM/DSM 파일을 `TerrainDataAdapter` interface로 읽는 adapter를 추가한다.

목표 흐름:

```text
Local GeoTIFF DEM/DSM
→ LocalGeoTiffTerrainDataAdapter
→ TerrainDataAdapter interface
→ extract_terrain_profile_from_adapter()
→ TerrainProfile
```

실제 DEM/DSM GeoTIFF 파일 자체는 Git에 커밋하지 않는다.

## 3. 구현 파일

필수 구현:

```text
src/uav_rf_terrain/geotiff_terrain_data.py
tests/test_geotiff_terrain_data.py
examples/local_geotiff_adapter_smoke.py
```

필요 시 수정:

```text
src/uav_rf_terrain/__init__.py
README.md
docs/paper/research-notes/README.md
docs/paper/experiments/README.md
docs/paper/research-notes/RN-20260710-004-local-geotiff-terrain-adapter.md
docs/paper/experiments/EXP-20260710-004-local-geotiff-adapter-tests.md
```

## 4. 구현 요구사항

### 4.1 새 class

```python
LocalGeoTiffTerrainDataAdapter
```

Protocol method:

```python
get_metadata() -> TerrainDatasetMetadata
validate_metadata() -> TerrainDatasetMetadata
get_dem_msl(x_index: int, y_index: int) -> float
get_dsm_msl(x_index: int, y_index: int) -> float
get_surface_delta_m(x_index: int, y_index: int) -> float
```

권장 constructor:

```python
LocalGeoTiffTerrainDataAdapter(
    dem_path: str | Path,
    dsm_path: str | Path,
    *,
    dataset_name: str = "local-geotiff-dem-dsm",
    source_dataset_name: str = "local redistributable processed DEM/DSM",
    source_provider: str = "user-prepared public-source terrain data",
    license_or_terms: str = "see local processing metadata",
    processing_date: str = "2026-07-10",
    processing_tool: str = "Task 018A preprocessing scripts",
    vertical_datum: str = "MSL",
    notes: str = "Local GeoTIFF DEM/DSM adapter metadata; file paths are not stored in public metadata.",
)
```

### 4.2 optional rasterio

`rasterio`는 lazy import로만 사용한다.

허용 예:

```python
import importlib

try:
    rasterio = importlib.import_module("rasterio")
except ModuleNotFoundError as exc:
    raise TerrainDataError("rasterio is required for LocalGeoTiffTerrainDataAdapter runtime use.") from exc
```

금지:

- module top-level `import rasterio`
- `pyproject.toml` 수정
- CI workflow 수정
- package import 시 rasterio 필수화

### 4.3 metadata

`dem_path`, `dsm_path`는 runtime 객체 내부에서만 사용한다. `TerrainRasterMetadata`나 `TerrainDatasetMetadata` string field에 private local path를 넣지 않는다.

### 4.4 index conversion

Project index에서 raster row/col로 변환한다.

```python
col = x_index
row = height - 1 - y_index
```

### 4.5 NoData/error handling

다음 상황은 `TerrainDataError`로 처리한다.

- out-of-bounds index
- masked value
- nodata value
- NaN
- infinite value
- DEM/DSM alignment mismatch
- rotated/sheared transform
- x/y pixel size mismatch

`get_surface_delta_m()`은 `get_dsm_msl() - get_dem_msl()`로 계산한다.

## 5. 테스트 요구사항

`tests/test_geotiff_terrain_data.py`를 작성한다.

CI에서 실제 rasterio 또는 실제 GeoTIFF가 없어도 통과해야 한다. fake rasterio module 또는 monkeypatch를 사용한다. 실제 `.tif` 파일 생성 금지.

필수 테스트:

1. rasterio가 없으면 `TerrainDataError` 발생
2. fake DEM/DSM dataset으로 `get_metadata()` 반환
3. CRS mismatch 실패
4. resolution mismatch 실패
5. width/height mismatch 실패
6. bounds mismatch 실패
7. rotated/sheared transform 실패
8. x/y pixel size mismatch 실패
9. y_index to raster row 변환 검증
10. DEM 값 읽기 검증
11. DSM 값 읽기 검증
12. surface delta 계산 검증
13. nodata 처리 검증
14. NaN/inf 처리 검증
15. out-of-bounds 처리 검증
16. metadata string에 private local path 미포함 확인
17. package root import가 rasterio를 요구하지 않는지 확인

## 6. 예제 요구사항

파일:

```text
examples/local_geotiff_adapter_smoke.py
```

CLI 인자:

```text
--dem-path
--dsm-path
--start-x
--start-y
--end-x
--end-y
--sample-spacing-m optional
```

권장 실행 예:

```bash
python examples/local_geotiff_adapter_smoke.py \
  --dem-path METADATA_MAP/DEM_PROCESSED/south_korea_dem_90m_epsg5179_alltiles.tif \
  --dsm-path METADATA_MAP/DSM_PROXY_FROM_ESA_WORLDCOVER/south_korea_temporary_dsm_proxy_90m_epsg5179.tif \
  --start-x 900000 \
  --start-y 1800000 \
  --end-x 900900 \
  --end-y 1800000
```

이 예제는 CI 필수 검증이 아니다. 로컬 DEM/DSM과 rasterio가 있는 환경에서만 optional smoke test로 실행한다.

## 7. README 업데이트

README.md에 Task 017B 섹션을 추가한다.

권장 문구:

```text
## Task 017B local GeoTIFF terrain data adapter

Task 017B adds a local GeoTIFF DEM/DSM adapter that implements the TerrainDataAdapter interface for runtime use with user-prepared local terrain files.

The adapter uses rasterio as an optional local runtime dependency and does not add rasterio to the package dependency list. Actual DEM/DSM GeoTIFF files remain outside Git under METADATA_MAP/. This task does not commit GIS data, render maps, perform field validation, or produce operational assurances.
```

## 8. Sharded paper logs

추가:

```text
docs/paper/research-notes/RN-20260710-004-local-geotiff-terrain-adapter.md
docs/paper/experiments/EXP-20260710-004-local-geotiff-adapter-tests.md
```

Index 업데이트:

```text
docs/paper/research-notes/README.md
docs/paper/experiments/README.md
```

Experiment input data 문구:

```text
CI tests use fake raster objects only. Real GeoTIFF DEM/DSM files are not committed and are used only for optional local smoke tests.
```

## 9. 보호 경로

수정 금지:

```text
pyproject.toml
.github/workflows/ci.yml
docs/deployment/android-tmmr-offline-plan.md
```

## 10. 커밋 금지 파일

```text
*.tif
*.tiff
*.img
*.vrt
*.zip
*.aux.xml
*.ovr
METADATA_MAP/
```

## 11. GitHub Actions 사용량 주의

기존 standard CI 범위를 벗어나는 runner, matrix, artifact, cache, Git LFS, package upload, release asset upload, 대용량 DEM/DSM 다운로드 작업을 추가하지 말 것.

필요하다고 판단되면 구현하지 말고 GPT Master와 사용자에게 먼저 보고할 것.

## 12. 검증 명령

반드시 실행:

```bash
python -m compileall src tests examples scripts
python -m pytest
python -m ruff check .
python -m mypy src
git diff --check
git status --short
git diff --name-only
```

추가 확인:

```bash
git diff --name-only | grep -E '^(\.github/workflows/ci\.yml|pyproject\.toml|docs/deployment/android-tmmr-offline-plan\.md)$' && echo "FORBIDDEN PATH CHANGED" || true

git diff --name-only | grep -E '\.(tif|tiff|img|vrt|zip|aux.xml|ovr)$' && echo "GIS FILE COMMITTED" || true

git diff --name-only | grep '^METADATA_MAP/' && echo "METADATA_MAP FILE COMMITTED" || true

grep -n "C:\\\\Users\\|/Users/\\|/home/\\|file://" -R README.md docs src tests examples || true

python - <<'PY'
import sys
sys.modules.pop("rasterio", None)
import uav_rf_terrain
print("package_import_ok_without_explicit_rasterio")
PY
```

Optional local smoke test:

```bash
python examples/local_geotiff_adapter_smoke.py \
  --dem-path METADATA_MAP/DEM_PROCESSED/south_korea_dem_90m_epsg5179_alltiles.tif \
  --dsm-path METADATA_MAP/DSM_PROXY_FROM_ESA_WORLDCOVER/south_korea_temporary_dsm_proxy_90m_epsg5179.tif \
  --start-x 900000 \
  --start-y 1800000 \
  --end-x 900900 \
  --end-y 1800000
```

완료 보고에는 optional smoke test를 다음 중 하나로 기록한다.

```text
Local GeoTIFF smoke test: passed
```

또는

```text
Local GeoTIFF smoke test: not run, because rasterio/local files were unavailable in the execution context
```

## 13. Commit

```bash
git add README.md \
  src/uav_rf_terrain/geotiff_terrain_data.py \
  src/uav_rf_terrain/__init__.py \
  tests/test_geotiff_terrain_data.py \
  examples/local_geotiff_adapter_smoke.py \
  docs/paper/research-notes/README.md \
  docs/paper/experiments/README.md \
  docs/paper/research-notes/RN-20260710-004-local-geotiff-terrain-adapter.md \
  docs/paper/experiments/EXP-20260710-004-local-geotiff-adapter-tests.md

git commit -m "feat: add local geotiff terrain data adapter"
git push origin agent/task-017b-local-geotiff-terrain-adapter
```

## 14. PR title

```text
feat: add local geotiff terrain data adapter
```

## 15. PR body

```markdown
## Purpose

Add a local GeoTIFF DEM/DSM terrain data adapter that implements the TerrainDataAdapter interface for runtime use with user-prepared local terrain files.

## Implemented

- Added LocalGeoTiffTerrainDataAdapter.
- Added lazy optional rasterio import behavior.
- Added GeoTIFF metadata extraction into TerrainDatasetMetadata.
- Added DEM/DSM alignment validation through existing metadata validation.
- Added project-grid to raster-row index conversion.
- Added NoData, NaN, infinity, and bounds error handling.
- Added fake-raster tests that do not require real GeoTIFF files.
- Added local smoke example using CLI paths.
- Added README Task 017B documentation.
- Added sharded research note and experiment record.

## Not Included

- No real DEM/DSM files committed.
- No METADATA_MAP files committed.
- No pyproject dependency change.
- No CI workflow change.
- No map rendering.
- No Android/TMMR implementation.
- No field validation.
- No operational assurance claims.

## Verification

- python -m compileall src tests examples scripts
- python -m pytest
- python -m ruff check .
- python -m mypy src
- git diff --check
- protected-path, GIS-file, private-path, and forbidden-wording checks
- optional local GeoTIFF smoke test: <passed / not run with reason>
```

## 16. 완료 보고 형식

```text
Task:
Branch:
PR:
Commit:
Changed files:
Summary:
New/updated module(s):
New tests:
New example(s):
LocalGeoTiffTerrainDataAdapter:
Optional rasterio behavior:
Metadata extraction:
Index conversion:
NoData/error handling:
Compatibility with extract_terrain_profile_from_adapter:
README update:
Sharded research note:
Sharded experiment record:
Forbidden wording check:
Public repository sensitivity check:
Changed forbidden paths:
GIS file commit check:
METADATA_MAP commit check:
Package dependency check:
Tests:
Optional local GeoTIFF smoke test:
CI:
Local verification limits:
Ready for GPT Master review:
```
