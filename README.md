# UAV RF Terrain Planner

연구·교육·시뮬레이션용 **드론 주파수 차폐 기반 발진기지 및 경로추천 프로그램**입니다.

## 목적

정찰목표지점 MGRS, 드론 운용반경, 허가 운용고도 AGL, 통신 주파수 대역을 입력받아 DEM/DSM 기반 지형 단면과 LOS/Fresnel Zone 차폐 위험을 분석하고, **지도 평면상에서 드론 최대 운용거리를 고려한 발진 가능구역을 색상 레이어로 표시**합니다. 사용자가 지도에서 발진기지를 선택하면 해당 지점부터 목표지점까지 차폐 위험이 낮은 비행경로 후보 3개를 제시합니다.

사용자 입력 좌표와 사용자-facing 출력 좌표는 MGRS를 표준으로 한다. 내부 계산은 WGS84, EPSG:5179, local metric coordinates, raster row/col을 사용할 수 있으나 기본 사용자 출력에는 MGRS를 표시한다.

## 핵심 기능

1. MGRS 좌표 입력 및 분석용 좌표계 변환
2. DEM/DSM 기반 지형 단면 분석
3. LOS 및 Fresnel Zone 기반 차폐위험 점수화
4. 드론 최대 운용거리와 차폐위험을 고려한 **발진 가능구역 색상 지도화**
5. 사용자가 지도상에서 발진기지 선택
6. 차폐 최소 / 거리-차폐 균형 / 우회 안정 경로 3개 제시
7. 경로별 실 비행거리 산정
8. 약 500m 단위 경유점 생성 및 AGL 고도·발진기지 기준 고도차 표기
9. 향후 기능: DSM 기반 LOS/Fresnel Clearance 조건을 만족하는 최소 요구 MSL 산출 및 직선 운용구간 내 최고 지표고 기준 AGL 변환

## 발진기지 표시 기준

발진기지는 단순히 Top 5 점 목록이 아니라 색상 기반 발진 가능구역 지도로 표시한다. 분석 평면을 격자화하고 각 격자점을 평가하여 다음과 같은 색상 구역으로 표시한다.

- 추천 가능구역: 운용거리 조건을 만족하고 차폐위험이 낮은 지역
- 제한적 가능구역: 운용거리 조건은 만족하지만 차폐위험이 보통인 지역
- 비추천/위험구역: 차폐위험이 높거나 운용거리 조건에 근접한 지역
- 제외구역: 드론 운용반경을 초과하거나 계산상 도달 불가능한 지역

점수 상위 지점 목록은 디버깅·검증용 보조 출력으로 둘 수 있지만, 사용자 기본 출력은 **색상 기반 발진 가능구역 지도**다.

## Task 001 기준 점수식

Task 001에서는 실제 LOS/Fresnel 알고리즘을 완성하지 않고, 이후 구현을 위한 config와 schema 기준만 고정한다.

```text
overall_score = shielding_stability_score × 0.80 + distance_score × 0.20

shielding_stability_score = dsm_los_score × 0.40
                          + dsm_fresnel_score × 0.60

distance_score = 100 × (1 - distance_3d_m / operating_radius_m)
```

운용반경을 초과하는 후보는 제외한다. 기본 LOS cap 규칙은 다음과 같다.

```text
if dsm_los_score == 0:
    shielding_stability_score = 0
```

이 점수는 현장 링크 성능 검증값이 아니다. 본 프로젝트의 MVP 점수는 **offline terrain/surface-obstacle risk proxy**로만 사용한다.

## Task 002 좌표 및 후보 격자 scaffold

Task 002는 local coordinate and candidate-grid scaffolding을 추가한다. `coordinates.py`는 `WGS84Point`, `LocalPoint`, `CoordinateReference`와 2D/3D 거리 helper를 제공하고, `grid.py`는 목표 주변 후보 발진지 candidate cell 격자를 생성한다.

MGRS/pyproj 기반 변환은 optional GIS dependencies와 로컬 검증이 필요하다. 기본 dev 환경과 CI가 무거운 GIS 의존성 때문에 깨지지 않도록 MGRS 변환은 optional runtime import 구조로 둔다.

Candidate grid는 색상 기반 발진 가능구역 지도 생성을 위한 grid/cell 구조이며, Top 5 발진지 기본 출력 구조가 아니다. 실제 DEM/DSM loading, DSM-based LOS/Fresnel computation, final scoring, and map rendering remain future tasks.

좌표 외부 I/O 정책은 `docs/architecture/mgrs-external-io-policy.md`에 둔다. `x_m`, `y_m`, raster `row`/`col`, EPSG:5179 좌표는 internal/debug 좌표이며 기본 사용자-facing 좌표 표시에는 MGRS를 사용한다.

## Task 003 synthetic DEM/DSM terrain generator

Task 003 adds pure Python synthetic DEM/DSM terrain generators. Synthetic terrain is for algorithm boundary-condition testing only.

The generator creates small in-memory DEM/DSM grids for scenarios such as flat terrain, single ridge, building obstacle, tree canopy, obstacle-position variation, operating-radius boundary, fixed-AGL case, and Fresnel-position variation.

No real DEM/DSM files are loaded. No GeoTIFF, rasterio, GDAL, geopandas, QGIS, or map-rendering work is included. LOS/Fresnel/scoring/map rendering remain future tasks.

## Task 018A DEM/DSM preprocessing handoff

Task 018A adds local DEM/DSM regeneration scripts and checkpoint documentation; it does not commit actual GIS data. Large source and generated GIS files remain local under `METADATA_MAP/`, which is excluded from Git.

## Task 004 terrain profile extraction

Task 004 adds pure Python terrain profile extraction over synthetic DEM/DSM grids.

The profile records DEM MSL, DSM MSL, DSM-DEM surface delta, distance from start, and distance to end. This prepares inputs for later DSM-based LOS and Fresnel modules.

No real DEM/DSM files are loaded. No LOS/Fresnel/scoring/map rendering is implemented in this task.

## Task 005 DSM-based LOS analysis

Task 005 adds pure Python DSM-based LOS analysis over synthetic terrain profiles.

The LOS line is calculated between `launch_antenna_msl` and `drone_flight_msl`. Each profile sample records LOS line MSL, DSM clearance, and blocked/clear status. The default `dsm_los_score` follows the strict LOS cap policy: any blocked DSM sample yields `0.0`; all clear samples yield `100.0`.

This task does not implement Fresnel, final scoring, real DEM/DSM loading, color-map classification, or map rendering.

## Task 006 DSM-based Fresnel analysis

Task 006 adds pure Python DSM-based Fresnel radius and clearance analysis over LOS results.

The module calculates wavelength, first Fresnel radius, clearance ratio, intrusion ratio, and DSM Fresnel sample score. Fresnel radius depends on both frequency and obstacle/sample position along the path. The task produces `dsm_fresnel_score` as a component score only.

This task does not implement final scoring, real DEM/DSM loading, color-map classification, or map rendering.

## Task 007 scoring integration

Task 007 adds pure Python scoring integration. The score combines DSM LOS, DSM Fresnel, and operating-radius distance components.

`shielding_stability_score` uses DSM LOS 40% and DSM Fresnel 60%, with a strict LOS cap. `overall_score` uses shielding stability 80% and distance reserve 20%. The distance reserve is an operating-radius proxy, not a field link-performance measurement.

This task does not implement color-map classification, real DEM/DSM loading, Streamlit/Folium UI, or map rendering.

## Task 008 color classification

Task 008 adds pure Python color classification for launch-area candidate cells.

Classification uses `CandidateScore`, operation-radius inclusion, DSM LOS status, and overall score thresholds. The output is classification data for a future color launch-area map. Green/Yellow/Orange/Red/Excluded thresholds are MVP heuristic visualization rules and are not field outcome guarantees.

This task does not render maps, use Folium/Streamlit, load real DEM/DSM files, or create Top 5 launch-site output.

## Task 009 route candidate evaluation scaffold

Task 009 adds pure Python route candidate evaluation scaffolding.

The route candidates are offline analysis data structures for future map/UI output. The task defines shielding-minimum, distance-shielding balanced, and detour-stability route candidate types. Costs combine shielding risk, distance cost, and DSM shielding high-risk cell penalty.

This task does not implement field execution workflows, control-system workflows, map rendering, real DEM/DSM loading, or field link validation.

## Task 010 waypoint output scaffold

Task 010 adds pure Python waypoint output scaffolding.

Waypoints are offline analysis/reporting points, not vehicle-execution records. The output includes cumulative distance, segment distance, AGL, MSL, launch-height difference, color class, and shielding score.

This task does not implement field execution workflows, control-system workflows, map rendering, real DEM/DSM loading, or field link validation.

## Task 011 synthetic end-to-end scenario output scaffold

Task 011 adds a pure Python synthetic end-to-end scenario output scaffold.

The scenario connects candidate scoring, color classification, route candidate evaluation, and waypoint reporting. The output is an offline synthetic analysis example, not a real map, real DEM/DSM result, vehicle-execution record, or field link validation.

## Task 012 map/UI output data scaffold

Task 012 adds pure Python map/UI output data scaffolding.

The output package contains candidate cell, route, and waypoint feature records for future UI/map rendering. The output is map-ready data, not a rendered map.

This task does not implement real DEM/DSM loading, Folium/Streamlit, map rendering, vehicle-execution records, or field link validation.

## Task 015 minimum required altitude scaffold

Task 015 adds a pure Python synthetic-profile model that estimates the minimum required MSL satisfying DSM-based LOS/Fresnel clearance proxy conditions and converts it to AGL over the highest DEM sample and the target DEM sample.

This is an offline altitude planning aid and not a field outcome guarantee.

No real DEM/DSM loading, GIS dependency, map rendering, Android/TMMR implementation, or control-system output is included.

## Task 016A terrain data policy documentation

Task 016A defines the project terrain data policy before real DEM/DSM integration.

Project DEM/DSM data is defined as redistributable processed data created by the user from public source data, when source, license, and processing metadata are documented.

Actual DEM/DSM data is still being produced by the user and is not required for this task. When a future task requires real DEM/DSM files, work should pause until the user provides the local data path.

This is a documentation-only task. It does not add terrain adapters, load real GeoTIFF files, add GIS dependencies, render maps, or validate field outcomes.

## Task 016B terrain data adapter interface scaffold

Task 016B adds a pure Python terrain data adapter interface scaffold and synthetic adapter for future DEM/DSM integration. It defines metadata structures and validation helpers based on the Task 016A terrain data policy. It does not load real DEM/DSM files, add GIS dependencies, render maps, or validate field outcomes.

## Task 017A adapter-based terrain profile extraction

Task 017A adds adapter-based terrain profile extraction so future DEM/DSM loaders can provide terrain samples through the `TerrainDataAdapter` interface while preserving the existing synthetic terrain profile workflow.

The implementation remains pure Python and uses synthetic/in-memory adapter tests only. It does not load real DEM/DSM files, add GIS dependencies, render maps, or validate field outcomes.

## Task 017B local GeoTIFF terrain data adapter

Task 017B adds a local GeoTIFF DEM/DSM adapter that implements the TerrainDataAdapter interface for runtime use with user-prepared local terrain files.

The adapter uses rasterio as an optional local runtime dependency and does not add rasterio to the package dependency list. Actual DEM/DSM GeoTIFF files remain outside Git under METADATA_MAP/. This task does not commit GIS data, render maps, validate field outcomes, or guarantee communication or flight performance.

Optional local smoke test, not required in CI:

    python examples/local_geotiff_adapter_smoke.py --dem-path METADATA_MAP/DEM_PROCESSED/south_korea_dem_90m_epsg5179_alltiles.tif --dsm-path METADATA_MAP/DSM_PROXY_FROM_ESA_WORLDCOVER/south_korea_temporary_dsm_proxy_90m_epsg5179.tif --start-x 900000 --start-y 1800000 --end-x 900900 --end-y 1800000

The local smoke CLI formats expected terrain data and profile input errors as concise stderr messages.

Task 018B local smoke and QGIS verification results are recorded in [the Task 018B checkpoint](docs/handoff/task-018b-local-dem-dsm-smoke-qgis-checkpoint.md).

Task 018C manual QGIS overlay findings are recorded in [the Task 018C verification record](docs/handoff/task-018c-manual-qgis-overlay-verification.md).

Task 018D QGIS overlay follow-up results are recorded in [the Task 018D verification record](docs/handoff/task-018d-qgis-overlay-followup.md).

Task 018E MCEE WMS landcover gap-fill results are recorded in [the Task 018E handoff](docs/handoff/task-018e-mcee-wms-landcover-gap-fill.md).

Task 018F mixed-source boundary quantification results are recorded in [the Task 018F verification record](docs/handoff/task-018f-mixed-source-boundary-quantification.md).

Task 020A adds source-zone flags for candidate, route, and waypoint output records so ESA-derived, WMS gap-filled, mixed-boundary, and DEM-only fallback results can be identified in later analysis.

Task 020B local source-zone raster classifier results are recorded in [the Task 020B handoff](docs/handoff/task-020b-local-source-zone-raster-classifier.md).

Task 020C adds a pure Python candidate-grid source-zone assignment scaffold so candidate cells can receive ESA-derived, WMS gap-filled, mixed-boundary, or DEM-only fallback interpretation metadata before later raster-backed scoring integration.

Task 020D records the local raster-backed candidate source-zone smoke that connects `LocalSourceZoneRasterClassifier` output to candidate-grid source-zone assignment without committing raster data.

Task 020E defines MGRS as the external input/output coordinate boundary while keeping WGS84, EPSG:5179, local x/y, and raster row/col as internal/debug computation coordinates.

Task 021A adds a candidate source-zone output metadata scaffold that preserves `candidate_cell_mgrs` as the user-facing candidate coordinate field while summarizing source-zone interpretation metadata.

Task 021B adds a candidate source-zone map metadata bridge that converts MGRS-based candidate source-zone output records into future map-ready properties without rendering maps or exposing internal projected coordinates.

Task 021C attaches candidate source-zone map metadata to candidate map features as optional MGRS-based properties while keeping existing internal geometry fields and map output constructors backward-compatible.

Task 021D adds a candidate display formatter scaffold that converts MGRS-based candidate metadata into user-facing table/popup-ready records without exposing internal geometry coordinates.

Task 021E adds a candidate display preview scaffold that converts MGRS-based display records into JSON-ready and plain-text previews without exposing internal geometry coordinates or writing files.

Task 021F connects the synthetic scenario flow to MGRS-based candidate display previews as an in-memory smoke path without file output, rendering, or internal coordinate exposure.

Task 021G documents the current candidate preview pipeline from synthetic scenario records to MGRS-based JSON-ready and plain-text preview outputs.

Task 022A documents the boundary between the current MGRS-based candidate preview pipeline and future CLI, report, and file-output implementation work.

Task 022B adds a synthetic candidate preview CLI with plain-text and optional JSON stdout, without file output or real terrain access.

Task 022C adds explicit `--output-json` and `--output-text` preview file output with opt-in `--force` overwrite behavior; existing stdout modes remain available and generated previews are not committed.

Task 023A documents the preview CLI output contract across stdout, JSON, explicit files, MGRS fields, status codes, and file-output policy.

Task 024A documents the boundary for transforming reviewed preview JSON output into paper appendix or developer review tables without changing CLI, terrain, scoring, or UI behavior.

Task 025A documents the planned CLI and explicit file-output surface for appendix table previews while preserving existing JSON, text, terrain, scoring, and UI boundaries.

## 향후 고도 판단 보조 기능

향후 Task에서는 공역사용승인 신청 고도의 과소·과도 산정을 줄이기 위해 DSM 기반 LOS/Fresnel Clearance 조건을 만족하는 최소 요구 MSL을 산출하고, 직선 운용구간 내 최고 지표고 기준 AGL로 변환하는 기능을 검토한다.

이 기능은 오프라인 DSM 기반 LOS/Fresnel Clearance 조건을 만족하는 고도 판단 보조 기능이며, 현장 결과나 승인 결과를 보장하지 않는다.

## 제품화·배포 로드맵

Android/TMMR offline은 논문 핵심 기능이 아니라 현장 운용자의 사용성을 높이기 위한 제품화·배포 전략으로 별도 관리한다. 구체 계획은 `docs/deployment/android-tmmr-offline-plan.md`에 둔다.

## DSM/DEM 기준

- LOS 판정 기본 기준면: DSM
- Fresnel 침범률 기본 기준면: DSM
- DEM 역할: DSM fallback, AGL 기준 지형고도, DSM-DEM 차이 참고, DEM-only vs DSM-primary 비교
- 사용자 입력 AGL은 단일 고정 운용고도로 해석한다.

표면장애물 복잡도 보정점수는 기본 점수식에서 제외한다. DSM 기반 LOS와 DSM 기반 Fresnel이 표면장애물 영향을 이미 반영하므로, 별도 복잡도 점수는 중복 감점 위험이 있다.

## 설치 및 테스트 초안

Task 001은 프로젝트 스캐폴딩 단계다. 로컬 또는 CI에서 다음 명령으로 확인한다.

```bash
python -m pip install -e '.[dev]'
python -m pytest
python -m compileall src tests examples
```

Cloud Execution Agent는 로컬 명령을 직접 실행하지 않는다. 실제 실행 결과는 GitHub Actions, Codex, 또는 Claude Code의 로컬 검증 결과로 분리해 기록한다.

## 문서 구조

- `docs/master-plan.md`: 전체 마스터 플랜
- `docs/research/research-index.md`: 선행연구 자료집 및 모델 반영안
- `docs/agent-operations-plan.md`: Codex/Claude Code 교대 운영 플랜
- `docs/github-app-limit-report.md`: GitHub 앱 작업 가능 범위 점검 보고
- `docs/data/terrain-data-policy.md`: DEM/DSM 데이터 정책 및 redistributable processed data 기준
- `docs/architecture/mgrs-external-io-policy.md`: MGRS external input/output boundary policy
- `docs/paper/log-structure.md`: Task 014 이후 논문 기록 분산 구조와 작성 규칙
- `docs/paper/score-model-validation-plan.md`: 실제 드론운용 없는 오프라인 점수식 검증 계획
- `docs/deployment/android-tmmr-offline-plan.md`: Android/TMMR offline 제품화·배포 로드맵

Task 014 이후 논문용 의사결정, 연구 노트, 실험 기록, PR 검토 기록은 장문 누적 로그에 계속 덧붙이지 않고 `docs/paper/decisions/`, `docs/paper/research-notes/`, `docs/paper/experiments/`, `docs/paper/pr-reviews/` 아래의 개별 파일로 작성한다. 기존 `docs/paper/*-log.md` 파일은 historical archive 및 legacy index로 보존한다.

## 개발 원칙

본 프로젝트는 실제 현장 운용 지시서가 아니라 연구·교육·시뮬레이션 및 의사결정 보조 목적의 정량 분석 도구로 개발합니다.

금지 범위:

- 실제 드론 제어
- 실시간 조종 또는 자동 비행 제어
- 침투·회피·공격 경로 제공
- 현장 링크 성능 보장 표현
- 실측 링크지표를 필수 입력으로 요구하는 MVP schema
- 대형 GIS 원천 데이터 저장소 커밋
