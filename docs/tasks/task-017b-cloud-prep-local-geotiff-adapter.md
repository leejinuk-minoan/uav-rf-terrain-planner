# Task 017B Cloud Prep - Local GeoTIFF Terrain Data Adapter

작성일: 2026-07-10

## 1. 목적

이 문서는 Task 017B를 바로 로컬 에이전트에게 넘기지 않고, Cloud/GitHub 단계에서 먼저 확정할 수 있는 설계·테스트·리뷰 기준을 정리한다.

에이전트 운용 목적은 로컬 에이전트의 토큰 소모와 작업 부담을 줄이는 것이다. 따라서 Cloud 단계는 설계와 범위 확정을 담당하고, Local Execution Agent는 실제 파일 수정과 로컬 검증만 수행한다.

## 2. 현재 main 기준 선행 상태

- Task 016B: `TerrainDataAdapter`, `TerrainDatasetMetadata`, `TerrainRasterMetadata`, `SyntheticTerrainDataAdapter`가 존재한다.
- Task 017A: `extract_terrain_profile_from_adapter()`가 adapter interface를 통해 profile sample을 추출한다.
- Task 018A: 로컬 DEM/DSM 복원 스크립트와 handoff 문서가 존재하며, 실제 GIS 파일은 Git에 커밋하지 않는다.

## 3. Cloud에서 확정한 Task 017B 설계

### 3.1 새 모듈

```text
src/uav_rf_terrain/geotiff_terrain_data.py
```

### 3.2 새 클래스

```python
LocalGeoTiffTerrainDataAdapter
```

이 클래스는 `TerrainDataAdapter` protocol을 만족해야 한다.

필수 메서드:

```python
get_metadata() -> TerrainDatasetMetadata
validate_metadata() -> TerrainDatasetMetadata
get_dem_msl(x_index: int, y_index: int) -> float
get_dsm_msl(x_index: int, y_index: int) -> float
get_surface_delta_m(x_index: int, y_index: int) -> float
```

### 3.3 optional rasterio 원칙

`rasterio`는 로컬 GeoTIFF adapter 실행 시에만 필요한 optional runtime dependency다.

금지:

- `pyproject.toml` 수정
- `.github/workflows/ci.yml` 수정
- package import 시점에 rasterio import 요구
- CI가 rasterio 설치를 전제로 하도록 변경

허용:

- `geotiff_terrain_data.py` 내부 lazy import
- `importlib.import_module("rasterio")` 사용
- rasterio가 없을 때 명시적 `TerrainDataError` 발생
- 테스트에서 fake rasterio 또는 monkeypatch 사용

### 3.4 metadata 보안 원칙

`dem_path`, `dsm_path`는 runtime 객체 내부에서만 사용한다. `TerrainRasterMetadata` 또는 `TerrainDatasetMetadata`의 문자열 필드에는 private local path를 넣지 않는다.

금지 예:

```text
C:\Users\...
/Users/...
/home/...
file://...
```

허용 예:

```text
local user-prepared DEM/DSM
Task 018A preprocessing scripts
see local processing metadata
```

### 3.5 GeoTIFF metadata 매핑

`get_metadata()`는 DEM/DSM source에서 다음 정보를 읽어 `TerrainRasterMetadata`를 구성한다.

```text
crs: src.crs.to_string() 또는 EPSG 문자열
resolution_m: pixel size
width: src.width
height: src.height
bounds: (left, bottom, right, top)
nodata_value: src.nodata
vertical_datum: constructor value
raster_type: DEM 또는 DSM
is_synthetic: False
is_redistributable_processed_data: True
```

검증 기준:

- DEM/DSM CRS 일치
- resolution 일치
- width/height 일치
- bounds 일치
- nodata finite 또는 None
- width/height > 0
- resolution > 0
- transform rotation/shear 없음
- x/y pixel size 동일

### 3.6 index convention

Task 017A의 project grid convention은 다음이다.

```text
bounds = (x_min, y_min, x_max, y_max)
x = x_min + ix * resolution_m
y = y_min + iy * resolution_m
ix range: 0 <= ix < width
iy range: 0 <= iy < height
```

GeoTIFF/raster row convention은 일반적으로 top-left origin이므로 adapter 내부에서 변환한다.

```python
col = x_index
row = height - 1 - y_index
```

필수 테스트 예:

```text
height=3, y_index=0 -> row=2
height=3, y_index=2 -> row=0
```

### 3.7 NoData/error handling

다음 상황에서는 `TerrainDataError`를 발생시킨다.

- out-of-bounds index
- masked value
- nodata value
- NaN
- infinite value
- DEM/DSM metadata mismatch

`get_surface_delta_m()`은 `dsm - dem`으로 계산한다.

## 4. Local Execution Agent에게 남길 최소 구현 범위

Local Execution Agent는 다음 파일만 중심으로 구현한다.

```text
src/uav_rf_terrain/geotiff_terrain_data.py
src/uav_rf_terrain/__init__.py
tests/test_geotiff_terrain_data.py
examples/local_geotiff_adapter_smoke.py
README.md
docs/paper/research-notes/RN-20260710-004-local-geotiff-terrain-adapter.md
docs/paper/experiments/EXP-20260710-004-local-geotiff-adapter-tests.md
docs/paper/research-notes/README.md
docs/paper/experiments/README.md
```

## 5. Local 테스트 요구사항

CI에서 실제 rasterio 또는 실제 GeoTIFF가 없어도 통과해야 한다.

필수 테스트:

1. rasterio가 없으면 `TerrainDataError` 발생
2. fake DEM/DSM dataset으로 metadata 반환
3. CRS mismatch 실패
4. resolution mismatch 실패
5. width/height mismatch 실패
6. bounds mismatch 실패
7. rotated/sheared transform 실패
8. x/y pixel size mismatch 실패
9. project y_index to raster row 변환 검증
10. DEM 값 읽기 검증
11. DSM 값 읽기 검증
12. surface delta 계산 검증
13. nodata 처리 검증
14. NaN/inf 처리 검증
15. out-of-bounds 처리 검증
16. metadata string에 private local path가 들어가지 않는지 검증
17. package root import가 rasterio를 요구하지 않는지 검증

## 6. Local smoke example 기준

예제 파일:

```text
examples/local_geotiff_adapter_smoke.py
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

이 예제는 CI 필수 검증이 아니다. rasterio와 로컬 DEM/DSM 파일이 있는 환경에서만 optional smoke test로 수행한다.

## 7. 보호 경로

다음 파일은 수정하지 않는다.

```text
pyproject.toml
.github/workflows/ci.yml
docs/deployment/android-tmmr-offline-plan.md
```

## 8. GitHub Actions 사용량 주의

기존 standard CI 범위를 벗어나는 runner, matrix, artifact, cache, Git LFS, package upload, release asset upload, 대용량 DEM/DSM 다운로드 작업을 추가하지 않는다. 필요하다고 판단되면 구현하지 말고 GPT Master와 사용자에게 먼저 보고한다.

## 9. PR review 기준

Task 017B PR이 생성되면 다음을 중점 확인한다.

- `rasterio` lazy import 구조
- `pyproject.toml` 미변경
- CI workflow 미변경
- GIS 파일 미커밋
- `METADATA_MAP/` 파일 미커밋
- private path 미포함
- fake-raster tests로 CI 통과 가능
- `extract_terrain_profile_from_adapter()`와 연결 가능한 interface 유지
- map rendering, Android/TMMR, control output 범위 미포함
- field outcome validation으로 오해될 표현 없음

## 10. 다음 단계

이 Cloud prep 문서가 main에 병합된 뒤 Local Execution Agent에게 `docs/prompts/task-017b-local-geotiff-terrain-adapter.md`의 지시문을 전달한다.
