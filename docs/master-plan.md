# 드론 주파수 차폐 기반 발진기지 및 경로추천 프로그램 Master Plan

작성일: 2026-07-08  
개정일: 2026-07-13  
문서 성격: 연구·교육·시뮬레이션용 프로그램 기획 및 설계 문서  
프로젝트명: UAV RF Terrain Planner

> 본 문서는 실제 현장 운용 지시서가 아니라 프로그램 개발을 위한 마스터 플랜이다. 본 체계는 지형·전파 차폐 위험을 정량화하여 사용자의 비교 판단을 보조하는 연구·교육·시뮬레이션용 의사결정 지원 도구다.

## Current Task Status

Task 032AB and Task 032CD are complete.

```text
Task 032AB
→ pure single knife-edge nu/loss helpers

Task 032CD
→ FresnelAnalysis.average_fresnel_score
→ FresnelAnalysis.worst_obstacle_score
→ FresnelAnalysis.dominant_obstacle
→ dsm_fresnel_score == average_fresnel_score 유지
```

Task 033A defines the dominant-obstacle preview/report output boundary and reconciles documentation. Task 033A changes no runtime source, tests, schema, formatter, CLI behavior, scoring, color, ranking, route, or waypoint behavior.

Task 033B is the separate future implementation candidate for the reviewed optional preview/report diagnostic projection.

---

## 1. 프로젝트 개요

### 1.1 한 줄 정의

사용자가 정찰목표지점 MGRS, 드론 운용반경, 허가 운용고도 AGL, 통신 주파수 대역을 입력하면 DEM/DSM 등 지형자료를 기반으로 주파수·지형 차폐 위험을 분석하고, **지도 평면상에서 드론 최대 운용거리를 고려한 발진 가능구역을 색상 레이어로 표시**한 뒤, 사용자가 선택한 발진기지에서 목표지점까지 차폐 위험이 낮은 경로 후보 3개를 제시하는 프로그램이다.

### 1.2 핵심 출력 원칙

발진기지 출력의 기본 방식은 Top 5 점 추천이 아니다.

```text
기본 출력:
목표 주변 분석구역 → 격자화 → 운용반경/차폐위험 평가 → 색상 기반 발진 가능구역 표시

보조 출력:
점수 상위 후보점 목록, preview/report diagnostics는 검토·설명용으로만 제공 가능
```

### 1.3 해결하려는 문제

운용자는 목표지점과 운용 위치 사이의 능선, 산악, 건물, 수목 등 지형·표면 장애물에 따른 LOS/Fresnel 위험을 정량적으로 비교하기 어렵다. 단순히 고도가 높은 위치가 항상 유리하지 않으므로 방향별 지형 단면과 주파수별 Fresnel 여유를 함께 분석한다.

후속 고도 판단 보조 기능은 DSM 기반 LOS/Fresnel clearance 조건을 만족하는 최소 요구 MSL과 최고 DEM 지표고 기준 AGL을 산출한다. 이 값은 실제 통신, 정찰, 비행 또는 공역승인 결과를 보장하지 않는다.

---

## 2. 확정된 설계 가정

| 항목 | 확정 기준 |
|---|---|
| 드론 최대 통제거리 | 최대 운용거리와 동일한 값으로 판단 |
| 발진기지 안테나 높이 | 조종기 위치는 지면으로 판단 |
| 드론 비행고도 | 사용자가 입력한 허가 운용고도 AGL 기준 |
| 안전 여유율 | 본 체계에서는 미고려, 드론 자체 기능 내장으로 판단 |
| 발진지역 제한 | 본 체계에서는 미고려 |
| 비행금지구역 | 본 체계에서는 미고려 |
| 지형데이터 | DEM, DSM, 경사도, 산림/수목, 건물, 토지피복 등 포함 |
| 드론 상승/하강 | 자유롭게 가능하다고 가정 |
| 운용거리 개념 | 조종자 위치 중심 3차원 구형 운용반경 |
| 발진기지 평가요소 | 정찰목표와의 지형·주파수 차폐, 거리 |
| 발진기지 기본 출력 | 색상 기반 발진 가능구역 지도 |
| 경로 추천 기준 | 선택 발진기지에서 차폐위험이 낮은 경로 우선 |
| 최소 요구 고도 산출 | DSM LOS/Fresnel clearance 기반 최소 요구 MSL 및 AGL 변환 |

후보 발진기지와 목표 또는 경로점 사이의 가능 여부는 3차원 거리로 계산한다.

```text
3D 거리 = sqrt(Δx² + Δy² + Δz²)
```

---

## 3. 사용자 입력값

| 입력값 | 설명 |
|---|---|
| 정찰목표지점 | MGRS 좌표 |
| 드론 운용반경 | 조종자 중심 3D 운용반경 |
| 허가 운용고도 | AGL 기준 고도 |
| 드론 통신 주파수 대역 | Fresnel Zone 계산용 |

입력 처리:

1. MGRS를 분석용 좌표계로 변환한다.
2. AGL은 경로점 지형고도와 결합해 MSL로 해석한다.
3. 주파수는 Fresnel 반경 계산에 사용한다.

```text
비행고도 MSL = 해당 지점 지형고도 + 사용자 입력 AGL
```

사용자-facing 좌표는 MGRS를 유지한다. WGS84, EPSG:5179, local x/y, raster row/col은 내부 계산용이다.

---

## 4. 필요한 데이터

| 데이터 | 용도 | MVP 포함 여부 |
|---|---|---|
| DEM | 지표면 고도 분석 | 필수 |
| DSM | 건물·수목 포함 표면고도 분석 | 필수 권장 |
| 경사도 | 지형 기복 분석 | 포함 |
| 토지피복도 | 산림·도심·수계 구분 | 포함 |
| 산림/임상도 | 수목 차폐 해석 | 포함 |
| 건물 높이/윤곽 | 도심 장애물 해석 | 포함 |
| MGRS 변환 | 사용자 좌표 입력 처리 | 필수 |
| WGS84/투영좌표계 | 지도 전시 및 거리 계산 | 필수 |

실제 DEM/DSM과 `METADATA_MAP` 자료는 저장소에 커밋하지 않는다. 실제 데이터 연결은 사용자 제공 로컬 경로와 별도 Local Task를 전제로 한다.

---

## 5. 전파·지형 분석 모델

### 5.1 LOS

```text
중간 DSM 높이 > 통신선 높이 → LOS 차단
중간 DSM 높이 ≤ 통신선 높이 → LOS 확보
```

Strict LOS cap:

```text
if dsm_los_score == 0:
    shielding_stability_score = 0
```

### 5.2 Fresnel Zone

제1 Fresnel Zone 반경과 DSM clearance를 sample별로 계산하고, sample score의 산술평균을 `dsm_fresnel_score`로 사용한다.

```text
dsm_fresnel_score == average_fresnel_score
```

### 5.3 Dominant Fresnel obstacle

Task 032CD는 eligible interior sample 중 clearance ratio가 가장 작은 sample을 dominant obstacle로 선택한다. 동률이면 낮은 sample index를 선택하며 endpoint와 zero-radius sample은 제외한다.

```text
average_fresnel_score
worst_obstacle_score
dominant_obstacle
```

Single knife-edge loss는 additional diffraction-loss proxy다. Full link budget, 측정 RF 결과, RSSI, SINR, packet loss 또는 통신 성공 예측이 아니다.

Task 033A는 이 값을 preview/report 보조정보로 출력하는 계약을 정의한다. Task 033B 전에는 runtime preview/report가 해당 필드를 제공한다고 표현하지 않는다.

### 5.4 ITM 및 고도화 모델

Longley-Rice/ITM은 후속 선택 모듈이다. 현재 MVP의 필수 score 또는 dependency가 아니다.

---

## 6. 발진 가능구역 지도화 알고리즘

### 6.1 전체 절차

```text
입력: 목표 MGRS, 운용반경 R, 허가고도 H_AGL, 주파수 f, DEM/DSM

1. 목표 좌표 변환
2. 목표 주변 분석범위 생성
3. 분석범위 격자화
4. 후보 셀 생성
5. 3D 거리 계산 및 운용반경 필터
6. 지형 단면 추출
7. DSM LOS 분석
8. DSM Fresnel 분석
9. 차폐안정성 점수 계산
10. 거리점수 계산
11. 종합점수 계산
12. 색상 등급 분류
13. 발진 가능구역 색상 레이어 생성
```

### 6.2 현재 점수식

```text
차폐안정성 점수
= dsm_los_score × 0.40
+ dsm_fresnel_score × 0.60

발진 가능구역 종합점수
= shielding_stability_score × 0.80
+ distance_score × 0.20

거리점수
= 100 × (1 - 목표까지 3D 거리 / 드론 운용반경)
```

별도 DSM 장애물 또는 표면복잡도 점수는 현재 기본 score에 포함하지 않는다. DSM 표면장애물은 LOS/Fresnel 계산에 반영한다.

이 가중치는 field-validated performance value가 아니라 MVP heuristic weighting이다.

### 6.3 불변 경계

Dominant obstacle diagnostics는 다음을 변경하지 않는다.

```text
shielding_stability_score
overall_score
strict LOS cap
color thresholds
candidate order/ranking
route cost
waypoint cost
```

---

## 7. 경로 추천 알고리즘

사용자가 지도상에서 발진기지를 선택한 뒤 3개 후보를 제시한다.

| 후보 | 성격 | 목적 |
|---|---|---|
| 1안 | 차폐 최소 | 차폐위험 최소화 |
| 2안 | 거리-차폐 균형 | 거리와 위험 균형 |
| 3안 | 우회 안정 | 고위험 영역 우회 |

```text
경로비용 = 차폐위험 비용 × W_shield + 실 비행거리 비용 × W_dist + 위험구간 페널티
```

| 후보 | W_shield | W_dist |
|---|---:|---:|
| 차폐 최소 | 0.90 | 0.10 |
| 균형 | 0.70 | 0.30 |
| 우회 안정 | 0.85 | 0.15 |

1차 구현은 격자 기반 A* 또는 Dijkstra를 사용한다. Dominant obstacle diagnostics는 현재 경로비용에 반영하지 않는다.

---

## 8. 경유점 및 최소 요구 고도

경로는 약 500m 단위 경유점을 생성한다.

| 항목 | 설명 |
|---|---|
| WP 번호 | WP-000, WP-001 등 |
| 누적 실 비행거리 | 발진기지부터 해당 지점까지 3D 거리 합 |
| MGRS 좌표 | 사용자-facing 경유점 좌표 |
| 지형고도 | DEM/DSM 기반 고도 |
| AGL / MSL | 사용자 고도와 지형고도의 결합 |
| 발진기지 기준 고도차 | 경유점 비행 MSL - 발진기지 지형고도 |
| 차폐위험 점수 | 발진기지와 해당 지점 사이 위험 proxy |

최소 요구 고도 보조 출력 후보:

```text
minimum_required_msl_m
highest_dem_msl_m
required_agl_above_highest_dem_m
clearance_condition
frequency_hz
```

이 값은 실제 통신·정찰·비행 또는 공역승인 결과를 보장하지 않는다.

---

## 9. 시스템 아키텍처

```text
사용자 입력 UI
→ 좌표 변환
→ 지형 데이터 adapter
→ 후보 격자 및 운용반경 필터
→ 지형 단면
→ DSM LOS/Fresnel 분석
→ scoring / color classification
→ 발진 가능구역 map-ready data
→ 사용자 발진기지 선택
→ 경로 후보 및 경유점
→ preview/report/UI consumer
```

Preview/report는 계산 엔진과 분리한다. 사용자-facing 출력은 MGRS를 유지하고 internal coordinate를 노출하지 않는다.

---

## 10. 데이터 구조 방향

### Candidate cell

```text
cell_id
candidate_cell_mgrs
within_operation_radius
dsm_los_score
dsm_fresnel_score
shielding_stability_score
distance_score
overall_score
color_class
source-zone interpretation metadata
optional dominant-obstacle diagnostics
```

Task 033B의 optional diagnostic fields는 preview/report용 보조 projection이며 저장·표시 여부가 scoring을 변경하지 않는다.

### Route and waypoint

Route와 waypoint는 선택 발진기지, 경로 유형, 거리, 차폐위험, 경유점 고도와 MGRS를 보유한다. Dominant obstacle diagnostics는 현재 route/waypoint score 입력이 아니다.

---

## 11. MVP 범위

### MVP-1

- MGRS/운용반경/AGL/주파수 입력
- DEM/DSM adapter
- 후보 격자와 운용반경 필터
- LOS/Fresnel 분석
- 색상 기반 발진 가능구역 출력 데이터

### MVP-2

- 사용자 발진기지 선택
- 차폐 최소/균형/우회 안정 경로
- 실 비행거리
- 약 500m 경유점
- 경유점별 AGL/MSL와 발진기지 기준 고도차

### Diagnostic output extension

- Task 033A: contract and documentation only
- Task 033B: optional preview/report field implementation candidate
- appendix-table extension: separate reviewed task
- scoring use: separate validation and decision required

제외 범위:

- 실제 재밍/전자전 모델
- 실제 드론 제어
- autopilot/flight command
- field communication guarantee
- 대형 GIS 데이터 저장소 커밋

---

## 12. 기술스택

| 목적 | 기술 |
|---|---|
| 지형 래스터 처리 | Python, optional Rasterio/GDAL |
| 좌표 변환 | PyProj, mgrs |
| 벡터 처리 | GeoPandas, Shapely |
| 경로탐색 | NetworkX, NumPy, SciPy |
| 웹 API | FastAPI 후보 |
| 프로토타입 UI | Streamlit 후보 |
| 지도 시각화 | Folium, Leaflet, MapLibre 후보 |
| 데이터 저장 | SQLite, GeoPackage, Parquet 후보 |

GIS dependency와 UI는 기본 pure-Python CI 경계와 분리한다.

---

## 13. 검증 계획

### 정량·synthetic 검증

1. LOS 차단/비차단 단면
2. 주파수 변화에 따른 Fresnel 반경과 sample score
3. 평균 Fresnel score 호환성
4. dominant obstacle endpoint 제외와 tie-break
5. no-eligible-obstacle optional state
6. DEM-only와 DSM-primary 비교
7. 색상 임계값 민감도
8. 경로거리와 차폐위험 trade-off
9. legacy/enriched preview backward compatibility

### 실제 데이터 검증 경계

실제 DEM/DSM, QGIS 시각 확인, rasterio/GDAL 설치, field RF 비교는 별도 Local Task다. 실행하지 않은 검증을 완료했다고 표현하지 않는다.

---

## 14. 개발 로드맵

| 단계 | 목표 | 산출물 |
|---|---|---|
| Phase 0 | 프로젝트 구조화 | GitHub 문서, 마스터플랜 |
| Phase 1 | 좌표변환/지형 로딩 | MGRS와 DEM/DSM adapter |
| Phase 2 | 차폐분석 | LOS/Fresnel 및 dominant diagnostic |
| Phase 3 | 발진 가능구역 지도화 | 색상 기반 가능구역 레이어 |
| Phase 4 | 발진기지 선택/경로추천 | 경로 후보 3개, 실 비행거리 |
| Phase 5 | 경유점 출력 | 500m 단위 WP |
| Phase 6 | 검증 및 보정 | 시나리오 테스트, 가중치 검토 |
| Phase 7 | 최소 요구 고도 | 최소 요구 MSL/AGL 보조값 |
| Phase 8 | 제품화·배포 | Android/TMMR offline 별도 검토 |

Task status:

```text
Task 032AB: complete
Task 032CD: complete
Task 033A: documentation/output boundary
Task 033B: proposed Local implementation
```

---

## 15. 최종 개발 방향

1차 목표는 지형과 전파 차폐를 정량화하는 수치분석 엔진을 안정적으로 구축하는 것이다. 실제 링크 데이터가 축적되기 전에는 heuristic score와 진단 proxy를 실측 성능값으로 표현하지 않는다.

본 프로그램은 다음 질문에 대한 비교 판단을 보조한다.

```text
목표지점 주변 어느 구역이 지형·주파수 차폐 측면에서 상대적으로 유리한가?

선택 발진기지에서 목표까지 어떤 경로 후보가 차폐위험과 거리 측면에서 비교 가능한가?

각 경로의 실 비행거리와 경유점 고도는 어떻게 되는가?

DSM LOS/Fresnel clearance 조건을 만족하는 최소 요구 고도 proxy는 얼마인가?

평균 Fresnel score와 dominant obstacle diagnostics는 경로의 어떤 제한 sample을 설명하는가?
```

Android/TMMR offline은 논문 핵심 기능이 아니라 제품화·배포 전략으로 분리한다.
