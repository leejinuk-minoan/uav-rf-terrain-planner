# UAV RF Terrain Planner

연구·교육·시뮬레이션용 **드론 주파수 차폐 기반 발진기지 및 경로추천 프로그램**입니다.

## 목적

정찰목표지점 MGRS, 드론 운용반경, 허가 운용고도 AGL, 통신 주파수 대역을 입력받아 DEM/DSM 기반 지형 단면과 LOS/Fresnel Zone 차폐 위험을 분석하고, **지도 평면상에서 드론 최대 운용거리를 고려한 발진 가능구역을 색상 레이어로 표시**합니다. 사용자가 지도에서 발진기지를 선택하면 해당 지점부터 목표지점까지 차폐 위험이 낮은 비행경로 후보 3개를 제시합니다.

사용자 입력 좌표와 사용자-facing 출력 좌표는 MGRS를 표준으로 합니다. 내부 계산은 WGS84, EPSG:5179, local metric coordinates, raster row/col을 사용할 수 있으나 기본 사용자 출력에는 MGRS를 표시합니다.

## 핵심 기능

1. MGRS 좌표 입력 및 분석용 좌표계 변환
2. DEM/DSM 기반 지형 단면 분석
3. LOS 및 Fresnel Zone 기반 차폐위험 점수화
4. 드론 최대 운용거리와 차폐위험을 고려한 **발진 가능구역 색상 지도화**
5. 사용자가 지도상에서 발진기지 선택
6. 차폐 최소 / 거리-차폐 균형 / 우회 안정 경로 3개 제시
7. 경로별 실 비행거리 산정
8. 약 500m 단위 경유점 생성 및 AGL 고도·발진기지 기준 고도차 표기
9. DSM 기반 LOS/Fresnel clearance 조건을 만족하는 최소 요구 MSL 및 최고 지표고 기준 AGL 판단 보조
10. 평균 Fresnel score와 dominant obstacle 보조 진단정보의 preview/report 출력 경계

## 발진기지 표시 기준

발진기지는 단순히 Top 5 점 목록이 아니라 색상 기반 발진 가능구역 지도로 표시합니다.

- 추천 가능구역: 운용거리 조건을 만족하고 차폐위험이 낮은 지역
- 제한적 가능구역: 운용거리 조건은 만족하지만 차폐위험이 보통인 지역
- 비추천/위험구역: 차폐위험이 높거나 운용거리 조건에 근접한 지역
- 제외구역: 드론 운용반경을 초과하거나 계산상 도달 불가능한 지역

점수 상위 지점 목록은 디버깅·검증용 보조 출력으로 둘 수 있지만 사용자 기본 출력은 **색상 기반 발진 가능구역 지도**입니다.

## 현재 점수식

```text
overall_score = shielding_stability_score × 0.80 + distance_score × 0.20

shielding_stability_score = dsm_los_score × 0.40
                          + dsm_fresnel_score × 0.60

distance_score = 100 × (1 - distance_3d_m / operating_radius_m)
```

운용반경을 초과하는 후보는 제외합니다. Strict LOS cap은 다음과 같습니다.

```text
if dsm_los_score == 0:
    shielding_stability_score = 0
```

`dsm_fresnel_score`는 경로 sample score의 산술평균이며 `average_fresnel_score`와 같습니다. 별도 DSM 장애물 또는 표면복잡도 점수는 현재 기본 score에 포함되지 않습니다.

이 점수는 현장 링크 성능 검증값이 아닙니다. MVP 점수와 색상 임계값은 **offline terrain/surface-obstacle risk proxy**와 heuristic visualization rule입니다.

## 구현 이력 요약

### Task 002 좌표 및 후보 격자 scaffold

`coordinates.py`는 `WGS84Point`, `LocalPoint`, `CoordinateReference`와 2D/3D 거리 helper를 제공하고, `grid.py`는 목표 주변 후보 발진지 candidate cell 격자를 생성합니다. MGRS/pyproj 변환은 optional GIS dependency 경계를 유지합니다.

### Task 003 synthetic DEM/DSM terrain generator

Pure Python synthetic DEM/DSM grid를 생성하여 flat terrain, ridge, building, canopy, boundary, fixed-AGL, Fresnel-position 시나리오를 테스트합니다. 실제 raster나 GIS 파일은 포함하지 않습니다.

### Task 004 terrain profile extraction

Synthetic DEM/DSM grid에서 DEM MSL, DSM MSL, surface delta, start/end distance를 포함하는 지형 단면을 추출합니다.

### Task 005 DSM-based LOS analysis

발진 안테나 MSL과 드론 비행 MSL 사이 LOS line을 계산하고 DSM clearance와 blocked/clear 상태를 기록합니다. 차단 sample이 하나라도 있으면 `dsm_los_score = 0.0`입니다.

### Task 006 DSM-based Fresnel analysis

파장, 제1 Fresnel 반경, clearance ratio, intrusion ratio, DSM Fresnel sample score를 계산합니다.

### Task 007 scoring integration

DSM LOS 40%, DSM Fresnel 평균 60%, shielding 80%, distance 20%를 결합합니다. Strict LOS cap을 유지합니다.

### Task 008 color classification

`CandidateScore`, 운용반경 포함 여부, LOS 상태와 overall score threshold를 사용해 Green/Yellow/Orange/Red/Excluded data를 생성합니다. 이는 map-ready classification이며 field outcome guarantee가 아닙니다.

### Task 009 route candidate evaluation scaffold

차폐 최소, 거리-차폐 균형, 우회 안정 경로 후보용 pure Python data structure와 cost 계산을 제공합니다.

### Task 010 waypoint output scaffold

누적거리, 구간거리, AGL, MSL, 발진지 기준 고도차, color class, shielding score를 포함하는 offline reporting waypoint를 제공합니다.

### Task 011 synthetic end-to-end scenario output scaffold

Candidate scoring, color classification, route evaluation, waypoint reporting을 synthetic scenario로 연결합니다.

### Task 012 map/UI output data scaffold

Candidate cell, route, waypoint feature record를 map-ready data로 변환합니다. 실제 지도 렌더링은 포함하지 않습니다.

### Task 015 minimum required altitude scaffold

DSM LOS/Fresnel clearance proxy 조건을 만족하는 최소 요구 MSL과 highest DEM/target DEM 기준 AGL을 산출하는 synthetic-profile model을 제공합니다.

### Task 016A terrain data policy

프로젝트 DEM/DSM data는 source, license, processing metadata가 문서화된 사용자 제작 redistributable processed data로 정의합니다. 실제 GIS data는 저장소에 포함하지 않습니다.

### Task 016B terrain data adapter interface

Future DEM/DSM integration을 위한 pure Python adapter interface, metadata structure, synthetic adapter와 validation helper를 제공합니다.

### Task 017A adapter-based terrain profile extraction

`TerrainDataAdapter`를 통해 terrain sample을 제공하면서 기존 synthetic profile workflow와 호환되는 extraction path를 제공합니다.

### Task 017B local GeoTIFF adapter

User-prepared local DEM/DSM GeoTIFF를 위한 optional rasterio runtime adapter를 제공합니다. Rasterio는 package 필수 dependency가 아니며 실제 files는 `METADATA_MAP/` 아래 로컬에 유지합니다.

### Task 018A~018F local terrain verification

DEM/DSM regeneration, local smoke, QGIS overlay, WMS gap-fill, mixed-source boundary quantification 결과는 `docs/handoff/`와 `docs/paper/experiments/`에 기록되어 있습니다. GIS data는 커밋하지 않습니다.

### Task 020A~020E source-zone and coordinate policy

Candidate, route, waypoint output에 ESA-derived, WMS gap-filled, mixed-boundary, DEM-only fallback interpretation metadata를 추가하고 MGRS를 external input/output coordinate boundary로 정의했습니다.

### Task 021A~021G candidate preview pipeline

Source-zone metadata를 map feature에 연결하고 `CandidateDisplayRecord`, JSON-ready preview dictionary, plain-text preview와 synthetic smoke path를 구현했습니다. Internal x/y, projected coordinate, raster index는 user-facing output에서 제외됩니다.

### Task 022A~028A preview artifact workflow

Synthetic preview CLI, JSON/plain-text file output, appendix-table formatter, saved JSON input, table stdout/file, artifact workflow documentation과 regression smoke coverage를 구현·정리했습니다.

### Task 029A~031B preview report workflow

Pure `format_preview_report(...)` formatter, report stdout/file CLI surface, current workflow documentation reconciliation, synthetic/saved-JSON report artifact smoke coverage를 구현했습니다.

### Task 032AB knife-edge formula foundation

Single knife-edge `nu`와 additional diffraction-loss helper를 pure function으로 구현했습니다. Full P.526 또는 full link budget 구현이 아닙니다.

### Task 032CD Fresnel dominant obstacle integration

`FresnelAnalysis`에 다음 값을 추가했습니다.

```text
average_fresnel_score
worst_obstacle_score
dominant_obstacle
```

호환성:

```text
dsm_fresnel_score == average_fresnel_score
```

Eligible interior sample 중 clearance ratio가 가장 작은 지점을 dominant obstacle로 선택합니다. Endpoint와 zero-radius sample은 제외합니다. 새 값은 scoring, color, overall score, ranking, route cost, waypoint cost를 변경하지 않는 보조 analysis proxy입니다.

### Task 033A dominant obstacle output boundary

Task 033A는 **문서와 code/document contract audit만 수행**합니다.

새 boundary:

```text
docs/architecture/dominant-obstacle-preview-report-output-boundary.md
```

결정 사항:

- dominant obstacle diagnostics는 향후 preview/report 보조정보로 표시
- JSON은 optional flat field와 원래 float 정밀도 유지
- plain-text는 concise summary
- report는 향후 `## Fresnel Diagnostics` section 사용
- legacy saved preview backward compatibility 유지
- no eligible interior sample과 unavailable diagnostics를 구분
- appendix table columns는 Task 033B에서 변경하지 않음
- scoring, color, ranking, route, waypoint는 변경하지 않음

Task 033A는 runtime preview JSON schema, formatter, CLI behavior 또는 source/test code를 변경하지 않습니다.

### Task 033B proposed implementation

Task 033B는 candidate/scenario, map feature, display record, preview dictionary와 report formatter를 통해 approved optional diagnostics를 전달하는 별도 Local implementation Task입니다.

Task 033B가 병합되기 전에는 runtime preview/report가 dominant-obstacle fields를 제공한다고 표현하지 않습니다.

## 향후 고도 판단 보조 기능

DSM 기반 LOS/Fresnel clearance 조건을 만족하는 최소 요구 MSL을 산출하고 직선 운용구간 내 최고 DEM 지표고 기준 AGL로 변환합니다.

이 기능은 의사결정 보조용 offline proxy이며 현장 결과나 승인 결과를 보장하지 않습니다.

## 제품화·배포 로드맵

Android/TMMR offline은 논문 핵심 기능이 아니라 현장 사용성을 위한 제품화·배포 전략으로 별도 관리합니다. 구체 계획은 `docs/deployment/android-tmmr-offline-plan.md`에 있습니다.

## DSM/DEM 기준

- LOS 판정 기본 기준면: DSM
- Fresnel 침범률 기본 기준면: DSM
- DEM 역할: DSM fallback, AGL 기준 지형고도, DSM-DEM 차이, DEM-only vs DSM-primary 비교
- 사용자 입력 AGL은 단일 고정 운용고도로 해석
- 표면장애물 복잡도 별도 score는 기본 점수식에서 제외

## 설치 및 테스트

```bash
python -m pip install -e '.[dev]'
python -m pytest
python -m compileall src tests examples
```

Cloud Execution Agent는 실행하지 않은 로컬 명령을 성공했다고 말하지 않습니다. 실제 실행 결과는 GitHub Actions 또는 Local Execution Agent 기록으로 구분합니다.

## 주요 문서

- `docs/master-plan.md`: 전체 마스터 플랜
- `docs/research/research-index.md`: 선행연구와 모델 반영안
- `docs/architecture/dominant-obstacle-preview-report-output-boundary.md`: Task 033A output contract
- `docs/architecture/preview-artifact-workflow.md`: current preview/report artifact workflow
- `docs/data/terrain-data-policy.md`: DEM/DSM data policy
- `docs/architecture/mgrs-external-io-policy.md`: MGRS external I/O boundary
- `docs/paper/score-model-validation-plan.md`: offline score validation plan
- `docs/deployment/android-tmmr-offline-plan.md`: 별도 배포 roadmap

Task 014 이후 논문용 decision, research note, experiment, PR review 기록은 `docs/paper/` 하위 개별 파일과 index로 관리합니다.

## 개발 원칙

본 프로젝트는 실제 현장 운용 지시서가 아니라 연구·교육·시뮬레이션 및 의사결정 보조 목적의 정량 분석 도구입니다.

금지 범위:

- 실제 드론 제어 또는 autopilot integration
- 실시간 조종 또는 flight command generation
- 침투·회피·공격 경로 제공
- 현장 링크 성능 또는 통신·정찰·비행 성공 보장 표현
- RSSI/SINR/packet-loss 결과를 현재 terrain proxy에서 예측했다고 표현
- 대형 GIS 원천 또는 생성 data 저장소 커밋
