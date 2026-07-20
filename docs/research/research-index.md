# 드론 주파수 차폐 경로추천 프로젝트 선행연구 자료집

작성일: 2026-07-08  
개정일: 2026-07-14  
문서 성격: 연구·교육·시뮬레이션용 선행연구 정리 자료  
프로젝트명: 드론 주파수 차폐 기반 발진기지 및 경로추천 프로그램

> 본 문서는 실제 현장 운용 지시서가 아니라 프로그램 설계와 연구 검토를 위한 선행연구 자료집이다. 모든 알고리즘은 시뮬레이션·교육·의사결정 보조 목적의 정량 분석 모델로 정의한다.

---

## 1. 프로젝트와 선행연구의 연결 구조

본 프로젝트는 사용자가 정찰목표지점 MGRS, 드론 운용반경, 허가 운용고도 AGL, 통신 주파수 대역을 입력하면 지형·전파 차폐 위험을 계산하여 **지도 평면상 발진 가능구역을 색상 레이어로 표시**하고, 사용자가 선택한 발진기지에서 목표까지의 경로 후보를 제시하는 프로그램이다.

선행연구는 다음 축으로 반영한다.

| 축 | 선행연구 분야 | 프로그램 반영 |
|---|---|---|
| 전파 물리 | LOS, Fresnel Zone, 회절 모델 | 발진 가능구역 셀별 차폐위험 점수와 진단정보의 물리적 근거 |
| 지형 전파모델 | Longley-Rice / ITM | 고도화 단계의 전파감쇠 예측 모델 후보 |
| UAV 경로계획 | Radio Map, Connectivity-Aware Planning | 차폐위험지도 기반 발진 가능구역 지도화 및 경로탐색 |
| 고도 판단 보조 | DSM 기반 LOS/Fresnel Clearance | 최소 요구 MSL / AGL 산출 개념 |

---

## 2. 핵심 선행연구 및 표준

### 2.1 LOS 기반 지형 차폐 분석

LOS(Line of Sight)는 송신점과 수신점 사이에 직접 가시선이 확보되는지를 판단하는 기본 개념이다. 발진기지 또는 조종자 위치와 드론 또는 목표 방향 사이에 능선, 산지, 건물, 수목 등이 위치하면 직접 가시선이 차단될 수 있다.

프로그램 반영 방식:

1. 발진 가능구역 후보 셀과 정찰목표점 또는 경로점 사이의 직선 단면을 생성한다.
2. 단면상의 DEM/DSM 높이를 샘플링한다.
3. 통신선 높이와 중간 장애물 높이를 비교한다.
4. 장애물이 통신선을 넘으면 직접 차폐로 판단한다.

```text
지형 또는 장애물 높이 > 통신선 높이 → LOS 차단
지형 또는 장애물 높이 ≤ 통신선 높이 → LOS 확보
```

### 2.2 Fresnel Zone

무선통신은 수학적 직선 하나만을 따라 전달되는 것이 아니라 송수신점 사이 직선 주변의 일정 공간을 함께 사용한다. LOS가 직접 차단되지 않더라도 제1 Fresnel Zone에 지형이나 장애물이 침범하면 신호 품질 저하 가능성이 커질 수 있다.

| 판단 상태 | 의미 | 프로그램 위험도 |
|---|---|---|
| LOS 직접 차단 | 장애물이 통신선을 초과 | 높음 |
| LOS 확보, Fresnel 침범 | 직접선은 열려 있으나 전파 공간이 부족 | 중간 |
| LOS 및 Fresnel 여유 확보 | 통신선과 주변 공간 모두 확보 | 낮음 |

사용자가 입력한 통신 주파수 대역은 Fresnel Zone 반경 계산에 사용한다. 주파수가 낮을수록 Fresnel Zone 반경이 커지므로 동일 지형에서도 차폐위험이 더 크게 나타날 수 있다.

### 2.2.1 최소 요구 MSL / AGL 산출 개념

공역사용승인 신청 고도 판단 보조를 위해 DSM 기반 LOS/Fresnel clearance 조건을 만족하는 최소 요구 MSL을 산출하는 개념을 연구 항목으로 둔다. 직선 운용구간의 DSM 표면고도와 Fresnel clearance requirement를 함께 고려하고, 산출된 최소 요구 MSL을 같은 구간의 최고 DEM 지표고 기준 AGL로 변환한다.

이 값은 실제 통신 가능 또는 실제 정찰 성공 보장이 아니라 오프라인 지형·표면장애물 기반 clearance proxy다.

### 2.3 ITU-R P.526 계열과 Task 032AB/032CD

ITU-R P.526 계열은 장애물에 의한 전파 회절과 Fresnel Zone 여유를 다루는 모델 계열이다. 본 프로젝트는 전체 권고안을 구현하지 않고, 현재 단계에서 다음을 반영한다.

1. 직접 가시선 차단 여부
2. 제1 Fresnel Zone 반경과 clearance ratio
3. 경로 sample별 침범 정도
4. 경로 평균 Fresnel sample score
5. 가장 제한적인 eligible interior sample
6. 해당 sample의 single knife-edge 추가 회절손실 proxy

Task 032AB 완료 상태:

```text
knife-edge nu 계산 helper
single knife-edge loss helper
입력 검증 및 수식 단위 테스트 경계
```

Task 032CD 완료 상태:

```text
FresnelAnalysis.average_fresnel_score
FresnelAnalysis.worst_obstacle_score
FresnelAnalysis.dominant_obstacle
dsm_fresnel_score == average_fresnel_score
```

Dominant obstacle은 eligible interior sample 중 clearance ratio가 가장 작은 sample이며, 동률이면 낮은 sample index를 선택한다. endpoint와 Fresnel radius가 0인 sample은 제외한다.

Single knife-edge loss는 **additional diffraction-loss proxy**다. 자유공간경로손실, 송신출력, 안테나 이득, 수신감도, 반사·산란·다중 장애물 상호작용을 포함하는 full link budget이 아니다.

현재 이 값은 scoring에 반영하지 않는다. Task 033B는 PR #85를 통해 optional diagnostics를 preview JSON, plain text, report에 구현했고, Task 034B는 PR #91을 통해 기본 11-column table을 보존하는 별도 14-column diagnostic appendix formatter를 `main`에 구현했다. Task 034D는 PR #95를 통해 `--diagnostic-table`과 `--output-diagnostic-table PATH` opt-in CLI stdout/file output을 `main`에 구현했으며 report composition은 변경하지 않았다. Task 035A가 정의한 actual-geometry real-terrain candidate contract는 Task 035B와 PR #99를 통해 구현됐고, Task 035D는 score/color를 바꾸지 않고 EPSG:5179 candidate polygon, WGS84 renderer geometry, MGRS popup, legend와 immutable candidate-ID launch-site selection으로 연결했다. Task 035EF는 선택된 발진기지에서 목표까지 terrain-derived route proxy를 구현하되 dominant-obstacle diagnostics를 route cost에 반영하지 않는다. Field RF validation은 별도 future research 범위다.

### 2.4 Longley-Rice / ITM

Longley-Rice 또는 ITM(Irregular Terrain Model)은 지형 프로파일을 이용해 전파 감쇠를 추정하는 대표적 모델이다. 지형고도, 주파수, 송수신점 높이, 거리 등을 반영할 수 있으므로 산악·구릉 지형의 고도화 모델 후보가 될 수 있다.

| 단계 | 반영 수준 |
|---|---|
| 현재 MVP | DSM LOS/Fresnel 기반 차폐위험 점수와 보조 진단 proxy |
| 후속 | 지형 단면 기반 추가 감쇠 추정식 검토 |
| 고도화 | ITM 라이브러리 또는 외부 모델 연동 검토 |
| 검증 단계 | 실제 링크상태 피드백 기반 보정 연구 |

ITM은 초기 필수 구현 대상이 아니다. 모델 파라미터와 검증 요구가 많으므로 현재는 사용자가 이해하고 synthetic 조건에서 검증하기 쉬운 LOS/Fresnel 중심 모델을 유지한다.

### 2.5 Radio Map Based UAV Path Planning

Radio map 기반 UAV 경로계획 연구는 공간을 2D 또는 3D 격자로 나누고 각 격자에 통신품질 또는 위험 proxy를 부여한 뒤 경로탐색 문제로 변환한다.

본 프로젝트의 반영 방식:

```text
DEM/DSM 기반 차폐위험지도
→ 임시 radio map 역할
→ 목표 주변 평면 격자별 발진 가능성 점수 부여
→ 발진 가능구역 색상 레이어 생성
→ 사용자가 선택한 발진기지 기준 경로 비용지도 생성
→ A* 또는 Dijkstra 경로탐색
→ 차폐 위험이 낮은 경로 후보 산출
```

현재 실제 RSSI, SINR, packet loss 측정값을 요구하지 않는다. Terrain-derived shielding score는 물리 기반 위험 proxy이며 실제 통신품질 측정값으로 표현하지 않는다.

### 2.6 Connectivity-Aware UAV Path Planning

Connectivity-aware path planning은 비행경로의 거리뿐 아니라 연결성 유지 가능성을 제약조건 또는 비용함수로 반영한다. 본 프로젝트에서는 차폐위험이 높은 영역을 높은 경로비용 영역으로 취급한다.

반영 방식:

1. 격자별 차폐위험 점수를 생성한다.
2. 고위험 격자에 높은 비용을 부여한다.
3. 운용반경을 초과하는 격자는 발진 가능구역에서 제외한다.
4. 발진 가능구역은 색상 등급으로 지도에 표시한다.
5. 사용자가 선택한 발진기지를 기준으로 차폐위험이 낮은 경로를 탐색한다.
6. 사용자가 비교할 수 있도록 경로 후보 3개를 제시한다.

---

## 3. 모델 설계에 반영되는 항목

### 3.1 입력값

| 입력값 | 선행연구 반영 이유 |
|---|---|
| 정찰목표 MGRS | 지형 단면 및 목표 위치 기준점 |
| 드론 운용반경 | 발진 가능구역 및 거리 제약 |
| 허가 운용고도 AGL | 통신선 및 비행고도 계산 |
| 드론 통신 주파수 대역 | Fresnel Zone 계산 |

### 3.2 출력값

| 출력값 | 선행연구 반영 이유 |
|---|---|
| 발진 가능구역 색상 지도 | Radio map/coverage map 개념을 발진기지 선정 문제에 적용 |
| 차폐 위험지도 | Radio map의 초기 대체물 |
| 사용자가 선택한 발진기지 | 색상 가능구역 내 사용자 판단 지점 |
| 경로 후보 3개 | Connectivity-aware path planning 반영 |
| 500m 경유점 | 경로별 고도와 차폐위험 해석 가능성 확보 |
| 실 비행거리 | 3D 경로 비용 및 운용반경 검토 |
| 최소 요구 MSL / AGL | 공역사용승인 신청 고도 판단 보조 및 고도 민감도 분석 |
| dominant obstacle diagnostics | 평균 Fresnel score를 변경하지 않는 보조 해석정보 |
| renderer-neutral candidate polygons | Task 035B center-based candidate result를 색상 셀 geometry로 전환 |
| MGRS candidate popup / selected launch-site record | 내부 projected/WGS84 좌표를 기본 user-facing 좌표와 분리 |

---

## 4. 알고리즘 반영안

### 4.1 현재 발진 가능구역 차폐점수

```text
차폐안정성 점수
= DSM LOS 점수 × 0.40
+ DSM Fresnel 평균점수 × 0.60
```

Strict LOS cap:

```text
if dsm_los_score == 0:
    shielding_stability_score = 0
```

#### LOS 점수

- 모든 DSM sample에서 통신선 여유 확보: 높은 점수
- 하나 이상의 DSM sample이 통신선을 차단: `dsm_los_score = 0`
- strict LOS cap에 따라 차폐안정성 점수도 0

#### Fresnel 평균점수

- 제1 Fresnel Zone 여유 충분: 높은 sample score
- 일부 침범: 중간 sample score
- 대규모 침범: 낮은 sample score
- `dsm_fresnel_score`는 경로 sample score의 산술평균
- `dsm_fresnel_score == average_fresnel_score`

#### DSM 표면장애물 처리

별도 `DSM 장애물 점수 × 0.15` 항목은 현재 기본 점수식에 포함되지 않는다. 건물·수목 등 DSM 표면장애물 영향은 DSM 기반 LOS와 DSM 기반 Fresnel 계산에 반영한다. 별도 표면복잡도 점수를 추가하면 중복 감점 가능성이 있으므로 별도 검토 없이 사용하지 않는다.

#### Dominant obstacle 보조 진단

```text
worst_obstacle_score
dominant_obstacle
dominant_obstacle.diffraction_loss_db
```

이 값들은 현재 차폐안정성 점수에 입력되지 않는다. Scoring, color threshold, candidate ranking, overall score, route cost, waypoint cost를 변경하지 않는 보조 진단값이다.

### 4.2 발진 가능구역 종합점수

```text
발진 가능구역 종합점수
= 차폐안정성 점수 × 0.80
+ 거리점수 × 0.20
```

이 점수는 Top 5 후보점을 기본 출력하기 위한 값이 아니라 지도상 각 격자 셀을 색상 등급으로 분류하기 위한 내부 heuristic indicator다.

기본 색상 등급:

```text
녹색 = 추천 가능구역
노란색 = 제한적 가능구역
주황색/적색 = 비추천 또는 차폐위험구역
회색/투명 = 운용반경 초과 또는 계산 제외구역
```

가중치와 임계값은 실제 성능 검증값이 아니라 초기 heuristic weighting이다.

Task 035D map/selection boundary는 기존 색상과 점수를 그대로 polygon fill과 popup에 전달한다. Source-zone state와 dominant-obstacle diagnostics는 popup interpretation data이며 색상이나 selectability를 재계산하지 않는다. Task 035EF route graph도 같은 score/color와 source-zone non-scoring 경계를 유지한다.

### 4.3 경로비용

사용자가 지도상에서 발진기지를 선택한 뒤 경로비용을 계산한다.

```text
경로비용 = 차폐위험 비용 × W_shield + 실 비행거리 비용 × W_dist + 위험구간 페널티
```

| 후보 | W_shield | W_dist | 목적 |
|---|---:|---:|---|
| 1안 | 0.90 | 0.10 | 차폐 최소 |
| 2안 | 0.70 | 0.30 | 거리-차폐 균형 |
| 3안 | 0.85 | 0.15 | 우회 안정 |

Dominant obstacle diagnostics는 현재 경로비용에 반영하지 않는다.

---

## 5. 검증해야 할 연구 질문

1. LOS/Fresnel 기반 차폐점수가 실제 링크 안정성과 어떤 상관관계를 가지는가?
2. 주파수 대역별 Fresnel Zone 침범률이 발진 가능구역 색상 분포를 얼마나 바꾸는가?
3. DEM만 사용한 결과와 DSM까지 사용한 결과는 어느 정도 차이가 나는가?
4. 고도 AGL 값 변화가 발진 가능구역 색상 분포에 어떤 영향을 주는가?
5. 색상 등급 임계값이 사용자 판단에 적절한가?
6. 차폐 최소 경로가 실제 비행거리 증가를 어느 정도 유발하는가?
7. 500m 단위 경유점 표기가 경로 이해와 검토에 충분한가?
8. 평균 Fresnel score와 dominant obstacle diagnostic을 함께 제시했을 때 해석성이 개선되는가?
9. Single knife-edge proxy가 복잡한 지형에서 어느 범위까지 설명력을 가지는가?
10. 실제 GeoTIFF 후보 분석에서 raster extent, NoData, source-zone availability와 mixed-source boundary가 후보 상태·색상 분포에 어떤 영향을 주는가?
11. EPSG:5179 square cell polygon과 WGS84 renderer projection이 후보 center/order/state와 일치하는가?
12. MGRS popup과 candidate-ID selection이 내부 좌표를 노출하지 않으면서 사용자 판단을 지원하는가?
13. Excluded visibility, zero-selectable warning과 valid red candidate selection이 색상 지도의 해석성을 유지하는가?

---

## 6. 향후 확장 방향

1. 실제 운용 또는 통제된 시뮬레이션 피드백 수집 방안을 검토한다.
2. 차폐점수와 관측 링크상태의 차이를 분석하는 별도 검증 설계를 수립한다.
3. 격자별 보정값을 누적하는 경험적 radio map 확장을 검토한다.
4. ITM 또는 더 정교한 전파모델을 선택적으로 연결한다.
5. 발진 가능구역 색상 임계값과 경로추천 가중치는 검증 후 별도 Task에서 보정한다.
6. Task 033B는 PR #85를 통해 `main`에 완료됐으며 dominant obstacle diagnostics를 preview JSON, plain text, report에 제공하지만 scoring과 route/waypoint cost에는 사용하지 않는다.
7. Task 034B는 PR #91을 통해 별도 14-column diagnostic appendix formatter를 `main`에 구현했고, Task 034D는 PR #95를 통해 diagnostic-table CLI stdout/file output을 구현했다.
8. Task 035B는 PR #99를 통해 EPSG:5179 target과 real DEM/DSM adapter를 production-neutral candidate records 및 actual-geometry features까지 연결했고, Task 035D는 PR #103을 통해 renderer-neutral package, lazy coordinate conversion, immutable selection과 explicit-path HTML/SVG writer를 구현했다. Task 035EF는 PR #105를 통해 선택된 발진기지에서 target까지 bounded graph, fixed-AGL 3D radius, deterministic Dijkstra와 최대 3개 diverse route proxy 및 complete waypoint handoff를 구현했고, Task 035G는 PR #107을 통해 이 handoff를 약 500m MGRS-facing report로 변환했다.
9. Task 036A는 complete route authority, authoritative actual selected-launch record, exact terrain-session metadata parity와 dedicated DSM/DEM radial profile을 결합한 route별 minimum-required constant MSL proxy 계약을 승인했다. Task 036B는 2D profile sampling/3D source total을 분리하고 모든 route sample의 current fixed-AGL margin을 별도로 평가하는 prepared-evidence pure core를 구현한다. terrain-session runtime, route ranking change, field claim은 추가하지 않는다.
10. Tile-based Folium/Leaflet, Streamlit callback UI, waypoint-report usability, altitude runtime, report composition, scoring 반영과 field RF validation은 각각 별도의 reviewed Task로 분리한다.

---

## 7. 요약

```text
LOS/Fresnel/회절 이론
→ DSM 기반 LOS와 Fresnel 평균점수
→ dominant obstacle 및 single knife-edge 보조 진단
→ 발진 가능구역 색상 지도화

Task 035B real-terrain candidate result
→ EPSG:5179 candidate center와 explicit cell polygon
→ WGS84 renderer geometry
→ MGRS popup과 candidate-ID launch-site selection

Longley-Rice / ITM
→ 고도화 단계의 지형 전파감쇠 모델 후보

Radio Map 기반 UAV 경로계획
→ 차폐위험지도 기반 발진 가능구역 및 경로탐색

Connectivity-Aware Path Planning
→ 통신 위험 proxy를 고려하는 경로 후보 생성
```

1차 MVP는 검증 가능한 LOS/Fresnel 기반 heuristic score로 시작한다. 기본 출력은 **Top 5 점 추천이 아니라 색상 기반 발진 가능구역 지도**다. Dominant obstacle과 single knife-edge loss는 해석을 위한 보조 proxy이며 실제 통신 성공, RSSI, SINR, packet loss 또는 실제 비행 가능성을 예측하거나 보장하지 않는다. Candidate cell polygon과 local HTML/SVG는 Task 035B center-based analysis의 시각화이며 polygon 내부 모든 지점의 별도 RF 검증을 의미하지 않는다.
