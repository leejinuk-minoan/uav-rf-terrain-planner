# 점수식 보완 및 검증 계획

작성일: 2026-07-08  
개정일: 2026-07-08  
책임 주체: GPT Master Agent  
적용 범위: 연구·교육·시뮬레이션용 UAV RF Terrain Planner  
중요 제한: 실제 드론 운용, 실제 비행, 실시간 제어, 현장 통신 보장 검증, 실제 링크품질 보장 검증은 수행하지 않는다.

---

## 1. 목적

본 문서는 발진 가능구역 종합점수와 차폐안정성 점수의 타당성을 보완·검증하기 위한 계획이다.

본 계획의 핵심 기준은 다음이다.

1. 점수식 보완은 실제 드론운용 없이 산출 가능한 데이터만 사용한다.
2. LOS와 Fresnel 침범률 계산의 기본 기준면은 DEM이 아니라 DSM이다.
3. DEM은 DSM이 없을 때의 fallback, AGL 기준고도, DSM-DEM 차이 분석용 보조자료로 사용한다.
4. 사용자가 입력한 AGL 운용고도를 단일 고정 운용고도로 보고 계산한다.
5. 고도별 반복계산은 기본 기능이 아니라 선택적 민감도 분석 기능으로 분리한다.
6. 점수는 실제 통신 성공률이 아니라 오프라인 지형·표면장애물 기반 차폐위험 proxy이다.

---

## 2. 기준 점수식

기본 구조는 다음과 같다.

```text
발진 가능구역 종합점수 = 차폐안정성 점수 × 0.80 + 거리점수 × 0.20
```

차폐안정성 점수는 다음 구조로 계산한다.

```text
차폐안정성 점수 = DSM 기반 LOS 점수 × 0.45
                 + DSM 기반 Fresnel 여유 점수 × 0.45
                 + 표면장애물 복잡도 보정점수 × 0.10
```

거리점수는 다음과 같다.

```text
거리점수 = 100 × (1 - 목표까지 3D 거리 / 드론 운용반경)
```

3D 거리는 다음과 같다.

```text
3D 거리 = sqrt(Δx² + Δy² + Δz²)
```

---

## 3. DSM 우선 기준

### 3.1 DSM을 기본 기준면으로 사용하는 이유

DEM은 지형고도만 표현한다. 따라서 산, 능선, 계곡 같은 지형 차폐는 확인할 수 있지만 건물, 수목, 구조물 같은 표면장애물은 반영하지 못한다.

반면 DSM은 다음을 포함한다.

```text
지형고도
건물 높이
수목 높이
구조물 높이
기타 표면장애물
```

따라서 같은 지역에서 DEM상 LOS가 열려 있어도 DSM상 건물 또는 수목 때문에 LOS 차단이나 Fresnel 침범이 발생할 수 있다.

이에 따라 본 프로젝트의 기본 계산 기준은 다음으로 한다.

| 항목 | 기본 기준 | 이유 |
|---|---|---|
| LOS 판정 | DSM | 건물·수목에 의한 중심선 차단 반영 |
| Fresnel 침범률 | DSM | 전파 통로 주변 표면장애물 침범 반영 |
| 표면장애물 보정 | DSM-DEM 차이 또는 DSM roughness | 장애물 밀도와 복잡도 보조 반영 |
| 거리점수 | 좌표·고도 계산값 | 지형 차폐가 아니라 운용반경 여유도 |
| DEM | 보조자료 | DSM 부재 시 fallback, terrain/surface 차이 분석, AGL 기준고도 산정 |

### 3.2 DEM의 역할

DEM은 버리지 않는다. 다만 기본 차폐 판정 기준에서 DSM보다 우선하지 않는다.

DEM은 다음 용도로 사용한다.

1. DSM이 없는 지역의 fallback 자료
2. AGL 기준 비행고도 산정의 지형 기준고도
3. DSM-DEM 차이를 이용한 표면장애물 높이 추정
4. 지형 자체와 표면장애물의 영향을 분리하는 ablation 분석
5. 논문에서 DEM-only와 DSM-primary 결과 비교

---

## 4. AGL 운용고도와 LOS/Fresnel 기하 기준

### 4.1 기본 원칙

사용자가 입력한 AGL은 드론이 해당 위치의 지표면 기준으로 비행한다고 가정하는 단일 운용고도다.

```text
사용자 입력 AGL = 150m
→ 드론은 평가 대상 위치의 지형고도 기준 150m 상공에서 비행한다고 가정
→ 기본 계산은 AGL 150m 조건으로 1회 수행
```

다만 차폐 판정은 DSM 표면고도를 기준으로 한다. 즉, 비행고도는 DEM 기준으로 산정하고, 장애물은 DSM으로 판정한다.

```text
terrain_msl = DEM 고도
surface_msl = DSM 고도
flight_msl = terrain_msl + user_agl
obstacle_surface_msl = DSM 고도
```

### 4.2 발진기지 안테나 고도

발진기지의 통신 시작점은 조종기 또는 안테나 위치다. 현재 MVP에서는 별도 안테나 높이를 고려하지 않으므로 발진기지 지표면 고도를 안테나 고도로 본다.

```text
launch_ground_msl = 발진기지 지표면 고도
controller_antenna_agl = 0m
launch_antenna_msl = launch_ground_msl + controller_antenna_agl
```

향후 안테나 높이를 입력값으로 확장하면 다음과 같이 계산한다.

```text
launch_antenna_msl = launch_ground_msl + user_controller_antenna_agl
```

### 4.3 드론 비행고도

드론 비행고도는 사용자가 입력한 AGL 운용고도를 기준으로 계산한다.

```text
drone_flight_msl = drone_position_terrain_msl + user_operating_agl
```

예를 들어 목표 지점 또는 경로상 드론 위치의 DEM 고도가 30m이고 사용자가 운용고도 AGL 150m를 입력했다면 다음과 같다.

```text
drone_flight_msl = 30m + 150m = 180m
```

### 4.4 LOS 직선고도

LOS는 발진기지 안테나 고도와 드론 비행고도를 잇는 3차원 직선이다. 장애물 영향은 장애물의 절대높이뿐 아니라 발진기지와 드론 사이에서의 상대적 위치에 따라 달라진다.

수평거리 기준으로 단순화하면 샘플 지점의 LOS 직선고도는 다음과 같이 계산한다.

```text
ratio = 발진기지에서 샘플 지점까지의 수평거리 / 발진기지에서 드론까지의 수평거리
los_line_msl = launch_antenna_msl + ratio × (drone_flight_msl - launch_antenna_msl)
```

DSM 표면고도가 `los_line_msl` 이상이면 LOS 차단 또는 침범으로 본다.

```text
if DSM_surface_msl >= los_line_msl:
    LOS 침범 발생
else:
    LOS 통과
```

### 4.5 고도 예시

예시는 다음과 같다.

```text
발진기지 지표면 고도 = 50m MSL
발진기지 안테나 높이 = 0m
드론 위치 DEM 고도 = 30m MSL
사용자 입력 운용고도 = AGL 150m
드론 비행고도 = 30m + 150m = 180m MSL
발진기지~드론 수평거리 = 1,000m
전방 차폐점 DSM 고도 = 80m MSL
```

이때 LOS 직선고도는 차폐점의 위치에 따라 달라진다.

| 차폐점 위치 | ratio | LOS 직선고도 | DSM 80m 영향 |
|---:|---:|---:|---|
| 발진기지에서 100m | 0.10 | 63m | LOS 침범 가능 |
| 발진기지에서 300m | 0.30 | 89m | LOS 중심선은 통과 가능 |
| 발진기지에서 500m | 0.50 | 115m | LOS 영향 제한 |
| 발진기지에서 800m | 0.80 | 154m | LOS 영향 작음 |

따라서 같은 80m 차폐점이라도 발진기지에 가까우면 LOS를 침범할 수 있고, 드론 쪽에 가까우면 영향이 제한될 수 있다.

### 4.6 Fresnel 여유와 고도

LOS 중심선이 통과하더라도 Fresnel Zone은 침범될 수 있다. Fresnel 평가는 LOS 중심선 주변의 전파 통로 여유를 평가한다.

각 샘플 지점에서 다음을 계산한다.

```text
clearance_m = los_line_msl - DSM_surface_msl
fresnel_radius_m = 제1 Fresnel Zone 반경
fresnel_clearance_ratio = clearance_m / fresnel_radius_m
```

예를 들어 `clearance_m = 20m`이고 해당 지점의 `fresnel_radius_m = 30m`이면 LOS는 통과하더라도 Fresnel 여유는 부족하다.

```text
fresnel_clearance_ratio = 20 / 30 = 0.67
Fresnel 일부 침범 또는 여유 부족으로 감점
```

따라서 운용고도 AGL 150m인 드론은 낮은 장애물의 영향을 적게 받을 수 있지만, 장애물의 위치와 Fresnel 반경에 따라 감점은 여전히 발생할 수 있다.

---

## 5. 오프라인 데이터 사용 원칙

본 프로젝트의 점수식 보완은 다음 데이터만 사용한다.

| 데이터 구분 | 사용 여부 | 설명 | 논문 표현 |
|---|---:|---|---|
| Synthetic DEM | 사용 | 임의 생성 지형고도 | 알고리즘 경계조건 검증 |
| Synthetic DSM | 사용 | 임의 생성 건물·수목·장애물 표면고도 | DSM 기반 차폐 판정 검증 |
| 공개 DEM | 사용 가능 | 공개 지형고도 자료 | 오프라인 지형자료 기반 재현성 |
| 공개 DSM | 사용 가능 | 공개 표면고도 자료 | 표면장애물 반영 검토 |
| 사용자 승인 샘플 DEM/DSM | 사용 가능 | 사용자가 제공하거나 사용을 승인한 샘플 | 사례지역 오프라인 검증 |
| 좌표·거리·고도 계산값 | 사용 | MGRS/WGS84/투영좌표, AGL/MSL, 3D 거리 | 입력·전처리 산출값 |
| DSM 기반 LOS 차단 여부 | 사용 | 표면고도 단면 기반 계산값 | 표면장애물 포함 차폐 proxy |
| DSM 기반 Fresnel 침범률 | 사용 | 주파수·거리·DSM 단면 기반 계산값 | Fresnel clearance proxy |
| DSM-DEM 차이 | 사용 | 표면장애물 높이 추정 | 장애물 복잡도 보조지표 |
| RSSI | 사용 금지 | 실제 송수신 측정 필요 | 향후 연구 |
| SINR | 사용 금지 | 실제 간섭·잡음 측정 필요 | 향후 연구 |
| Packet loss | 사용 금지 | 실제 통신 실험 필요 | 향후 연구 |
| 실제 비행 로그 | 사용 금지 | 실제 드론운용 필요 | 본 연구 범위 제외 |
| 실제 통신 성공률 | 사용 금지 | 실제 운용·측정 필요 | 본 연구 범위 제외 |

---

## 6. 검증 원칙

| 원칙 | 설명 |
|---|---|
| 실제 운용 배제 | 실제 드론 비행, 실제 조종기 연결, 실시간 링크 측정은 수행하지 않는다. |
| 오프라인 산출값만 사용 | DEM/DSM, 좌표, 거리, 고도, DSM 기반 LOS, DSM 기반 Fresnel, 표면장애물 proxy만 사용한다. |
| DSM 우선 | LOS와 Fresnel 계산은 DSM을 기본 기준면으로 사용한다. |
| DEM 보조 | DEM은 DSM fallback, AGL 산정 기준, DSM-DEM 차이 분석에 사용한다. |
| 고정 AGL | 사용자가 입력한 AGL을 단일 운용고도로 보고 계산한다. |
| 위치 기반 차폐판정 | 차폐물 영향은 절대높이뿐 아니라 발진기지와 드론 사이에서의 상대적 위치에 따라 평가한다. |
| 고도 민감도 분리 | 여러 AGL 반복계산은 기본 기능이 아니라 선택적 분석 기능이다. |
| 링크품질 직접 주장 금지 | RSSI/SINR/packet loss 없이 통신품질 보장 표현을 쓰지 않는다. |
| 가중치 고정값 경계 | 가중치는 초기 휴리스틱으로만 기록한다. |
| 민감도 분석 필수 | 가중치를 바꿨을 때 색상지도와 경로 후보가 얼마나 변하는지 비교한다. |
| 논문 표현 제한 | 성능 입증이 아니라 오프라인 방법론 검증으로 표현한다. |

---

## 7. 항목별 계산 방식

## 7.1 DSM 기반 LOS 점수

### 목적

후보 발진점과 목표 상공 드론 위치 사이의 중심선이 DSM 표면고도에 의해 차단되는지 계산한다.

### 입력

```text
launch_point
target_or_drone_position
user_agl
DEM
DSM
controller_antenna_agl
```

### 기준

```text
launch_antenna_msl = launch_ground_msl + controller_antenna_agl
drone_flight_msl = drone_position_terrain_msl + user_agl
los_line_msl = launch_antenna_msl + ratio × (drone_flight_msl - launch_antenna_msl)
surface_profile_msl = DSM 단면고도
```

DSM 표면고도가 LOS 직선고도를 침범하면 차단으로 본다.

### 점수화

MVP 기본형:

| 상태 | LOS 점수 |
|---|---:|
| DSM 표면고도가 LOS를 침범하지 않음 | 100 |
| DSM 표면고도가 LOS에 근접 | 50 |
| DSM 표면고도가 LOS를 침범 | 0 |

개선형:

```text
LOS 점수 = 100 × (1 - normalized_los_intrusion)
```

여기서 `normalized_los_intrusion`은 LOS 침범 높이, 침범 샘플 수, 침범 구간 길이를 종합한 0~1 값이다.

---

## 7.2 DSM 기반 Fresnel 여유 점수

### 목적

DSM 표면고도가 후보점과 드론 비행위치 사이의 제1 Fresnel Zone을 얼마나 침범하는지 계산한다.

### 입력

```text
launch_point
target_or_drone_position
user_agl
frequency
DEM
DSM
controller_antenna_agl
```

### 기준

각 단면 샘플 지점에서 다음을 계산한다.

```text
d1 = 발진점에서 샘플 지점까지 거리
d2 = 샘플 지점에서 드론 비행위치까지 거리
F1 = 제1 Fresnel 반경
clearance_m = los_line_msl - DSM_surface_msl
fresnel_clearance_ratio = clearance_m / F1
```

### 침범률 산정

`clearance_m`이 0 이하이면 LOS 침범이며, Fresnel 점수도 강하게 감점한다.

`clearance_m`이 양수라도 `clearance_m < F1`이면 Fresnel Zone 여유가 부족하므로 감점한다.

```text
fresnel_intrusion_ratio = max(0, 1 - clearance_m / F1)
```

단, `F1 = 0`에 가까운 시작점과 끝점 주변은 수치 안정성을 위해 최소 거리 기준을 둔다.

### 점수화

내부 계산은 연속 점수로 한다.

```text
Fresnel 점수 = 100 × (1 - fresnel_intrusion_ratio)
```

논문과 로그 표시용으로는 10% 단위 구간도 함께 기록한다.

| Fresnel 침범률 | 표시 등급 | 대표 점수 |
|---:|---:|---:|
| 0~10% | F10 | 100~90 |
| 10~20% | F20 | 90~80 |
| 20~30% | F30 | 80~70 |
| 30~40% | F40 | 70~60 |
| 40~50% | F50 | 60~50 |
| 50~60% | F60 | 50~40 |
| 60~70% | F70 | 40~30 |
| 70~80% | F80 | 30~20 |
| 80~90% | F90 | 20~10 |
| 90~100% | F100 | 10~0 |

---

## 7.3 표면장애물 복잡도 보정점수

### 목적

LOS와 Fresnel이 이미 DSM을 사용하므로, 별도의 `DSM 장애물 점수`를 강하게 중복 반영하지 않는다. 대신 DSM-DEM 차이 또는 DSM roughness를 사용하여 표면장애물 복잡도 보정점수로 약하게 반영한다.

### 입력

```text
DEM
DSM
candidate corridor buffer
```

### 계산 후보

```text
surface_height = DSM - DEM
surface_obstacle_density = corridor 내 surface_height가 threshold 이상인 셀 비율
surface_roughness = corridor 내 DSM 고도 변화량
```

### 점수화

```text
표면장애물 복잡도 보정점수 = 100 × (1 - normalized_surface_complexity)
```

이 항목은 이미 LOS/Fresnel에서 반영된 직접 침범을 다시 벌점화하기 위한 항목이 아니다. 직접 침범은 LOS/Fresnel 점수에서 처리하고, 이 항목은 표면장애물 밀집도와 복잡도에 대한 약한 보조지표로만 사용한다.

---

## 7.4 거리점수

거리점수는 운용반경 여유도만 의미한다. 통신품질 점수가 아니다.

```text
거리점수 = 100 × (1 - 목표까지 3D 거리 / 드론 운용반경)
```

운용반경을 초과하면 점수 계산 대상에서 제외한다.

---

## 8. 발진 가능구역 종합점수 산출

최종 계산은 다음 순서로 수행한다.

```text
1. 목표 MGRS를 좌표로 변환한다.
2. 사용자가 입력한 AGL을 단일 운용고도로 고정한다.
3. 목표 주변 후보 격자를 생성한다.
4. 후보점별 3D 거리를 계산하고 운용반경 초과 후보를 제외한다.
5. 발진기지 안테나 고도와 드론 비행고도를 계산한다.
6. 후보점과 목표 상공점 사이 DSM 단면을 추출한다.
7. 각 샘플 지점에서 LOS 직선고도를 계산한다.
8. DSM 표면고도와 LOS 직선고도를 비교하여 DSM 기반 LOS 점수를 계산한다.
9. 각 샘플 지점에서 Fresnel 반경과 DSM 침범률을 계산한다.
10. DSM 기반 Fresnel 여유 점수를 계산한다.
11. DSM-DEM 차이 또는 DSM roughness 기반 표면장애물 복잡도 보정점수를 계산한다.
12. 거리점수를 계산한다.
13. 차폐안정성 점수를 계산한다.
14. 발진 가능구역 종합점수를 계산한다.
15. 종합점수를 색상 등급으로 변환한다.
```

---

## 9. 색상 등급

초기 MVP 색상 등급은 다음과 같이 둔다. 임계값은 config로 분리한다.

| 종합점수 | 색상 | 의미 |
|---:|---|---|
| 80~100 | 녹색 | 추천 가능구역 |
| 60~80 | 노란색 | 제한적 가능구역 |
| 40~60 | 주황색 | 주의구역 |
| 0~40 | 적색 | 비추천구역 |
| 운용반경 초과 | 회색/투명 | 제외구역 |

---

## 10. 검증계획

## Stage 0. 기준선 고정

- DSM-primary 점수식을 기준선으로 고정한다.
- 모든 점수 범위를 0~100으로 통일한다.
- 100점은 좋음, 0점은 나쁨으로 방향성을 통일한다.
- 가중치 합이 1.0인지 검증한다.
- 실제 링크 측정값 없이도 계산 가능한 값만 입력 schema에 둔다.

## Stage 1. DSM 기반 정규화 검증

- DSM 기반 LOS 점수 정규화
- DSM 기반 Fresnel 점수 정규화
- 표면장애물 복잡도 보정점수 정규화
- 거리점수 정규화
- 실제 RSSI, SINR, packet loss를 요구하지 않는지 확인

## Stage 2. Synthetic 지형 검증

다음 synthetic 시나리오를 사용한다.

| 시나리오 | 설명 | 기대 결과 |
|---|---|---|
| S1 평탄지 | DEM/DSM 모두 평탄 | LOS/Fresnel 점수 높음 |
| S2 단일 능선 | DEM과 DSM 모두 능선 포함 | 능선 뒤쪽 점수 하락 |
| S3 DEM 평탄 + DSM 건물 | 지형은 평탄하지만 건물 존재 | DEM-only는 통과, DSM-primary는 감점 |
| S4 DEM 평탄 + DSM 수목 | 수목 표면고도 존재 | Fresnel/복잡도 점수 감점 |
| S5 협곡/계곡 | 지형 단면 변화 큼 | 경로/발진 후보의 차폐위험 차이 발생 |
| S6 운용반경 경계 | 거리만 증가 | 거리점수 하락, 초과 지역 제외 |
| S7 고정 AGL 비교 | 사용자가 입력한 AGL 하나로 계산 | 기본 계산은 단일 AGL 결과만 산출 |
| S8 장애물 위치 변화 | 같은 높이 장애물을 발진기지 근처/중간/드론 근처에 배치 | 장애물 위치에 따라 LOS/Fresnel 영향이 달라짐 |

## Stage 3. DEM-only vs DSM-primary 비교

DEM-only 결과와 DSM-primary 결과를 비교한다.

목적은 DSM-primary가 건물·수목에 의한 추가 차폐위험을 반영하는지 확인하는 것이다.

## Stage 4. AGL 기하 검증

사용자가 입력한 AGL이 고정된 상태에서, 같은 장애물 높이라도 장애물의 상대 위치에 따라 차폐 영향이 달라지는지 검증한다.

예시 검증:

```text
launch_antenna_msl = 50m
drone_flight_msl = 180m
DSM_obstacle_msl = 80m
horizontal_distance = 1,000m
```

장애물이 100m 지점에 있으면 LOS 침범 가능성이 높고, 500m 또는 800m 지점에 있으면 LOS 영향이 제한되는지 확인한다.

## Stage 5. 가중치 민감도 분석

종합점수 가중치:

| 케이스 | 차폐안정성 | 거리 |
|---|---:|---:|
| O1 | 0.90 | 0.10 |
| O2 | 0.80 | 0.20 |
| O3 | 0.70 | 0.30 |
| O4 | 0.60 | 0.40 |

차폐안정성 내부 가중치:

| 케이스 | DSM LOS | DSM Fresnel | 표면복잡도 |
|---|---:|---:|---:|
| S1 | 0.50 | 0.40 | 0.10 |
| S2 | 0.45 | 0.45 | 0.10 |
| S3 | 0.40 | 0.50 | 0.10 |
| S4 | 0.50 | 0.50 | 0.00 |

## Stage 6. Ablation 분석

다음 케이스를 비교한다.

| 케이스 | 설명 |
|---|---|
| A0 | 전체 DSM-primary 점수식 사용 |
| A1 | 거리점수 제거 |
| A2 | DSM LOS 제거 |
| A3 | DSM Fresnel 제거 |
| A4 | 표면복잡도 보정 제거 |
| A5 | DSM LOS만 사용 |
| A6 | DSM LOS + DSM Fresnel만 사용 |
| A7 | 거리만 사용 |
| A8 | DEM-only 계산 |

## Stage 7. 공개/샘플 DEM·DSM 오프라인 검증

허용 데이터:

- 공개 DEM
- 공개 DSM
- 사용자가 명시적으로 제공한 샘플 DEM/DSM

금지 데이터:

- 실제 비행 로그
- 실제 조종기 로그
- 실제 통신 장비 측정 RSSI/SINR/packet loss
- 실제 운용 성공/실패 결과
- 비공개·비인가 지형자료

## Stage 8. 전파모델 대조 검증

현재 점수식 결과를 dB 손실로 단정 변환하지 않는다. 전파모델과 방향성만 비교한다.

비교 가능 지표:

- 거리
- 주파수
- DSM 기반 LOS 차단 여부
- DSM 기반 Fresnel 침범률
- 표면장애물 복잡도
- 자유공간손실 상대값
- 지형회절 위험 proxy

---

## 11. 논문 반영 기준

| 검증 수준 | 논문 표현 |
|---|---|
| synthetic 검증 | 알고리즘 동작 및 경계조건 검증 |
| AGL 기하 검증 | 동일 장애물이라도 상대 위치에 따라 차폐 영향이 달라지는지 검증 |
| DEM-only vs DSM-primary 비교 | DSM이 건물·수목 등 표면장애물을 반영하는지 검토 |
| 공개 DEM/DSM 검증 | 지형자료 기반 오프라인 재현성 확인 |
| 전파모델 대조 | 점수 방향성 비교 |
| 실제 링크 측정 없음 | 한계 및 향후 연구 |
| 실제 드론 운용 없음 | 연구·교육·시뮬레이션용 방법론 |

---

## 12. 최종 권고

MVP 단계에서는 다음을 적용한다.

1. LOS와 Fresnel 계산은 DSM을 기본 기준면으로 한다.
2. DEM은 DSM fallback, AGL 지형 기준고도, DSM-DEM 차이 분석에 사용한다.
3. 사용자 입력 AGL은 드론의 단일 고정 운용고도로 사용한다.
4. 발진기지 안테나 고도와 드론 비행고도를 잇는 3차원 LOS 직선을 기준으로 차폐를 판정한다.
5. 같은 높이의 장애물이라도 발진기지와 드론 사이의 상대 위치에 따라 LOS/Fresnel 영향이 다르게 계산되어야 한다.
6. 기존 DSM 장애물 점수는 표면장애물 복잡도 보정점수로 재정의한다.
7. 차폐안정성 점수는 `DSM LOS 0.45 + DSM Fresnel 0.45 + 표면복잡도 0.10`으로 시작한다.
8. Fresnel 점수는 내부적으로 연속 점수로 계산하고, 로그와 논문에는 10% 구간도 함께 기록한다.
9. 고도별 반복계산은 기본 기능이 아니라 선택적 민감도 분석 기능으로 분리한다.
10. RSSI, SINR, packet loss, 실제 통신 성공률은 산출 대상에서 제외한다.
11. 모든 실험 로그에 `actual_drone_operation = false`, `actual_link_measurement = false`를 기록한다.

---

## 13. Cloud Execution Agent 구현 지시 기준

Cloud Execution Agent가 점수식 관련 Task를 수행할 때는 다음 조건을 지킨다.

1. 실제 드론운용 데이터를 요구하지 않는다.
2. 실제 링크 측정값을 입력 schema에 필수값으로 넣지 않는다.
3. LOS와 Fresnel 기본 계산은 DSM 기준으로 설계한다.
4. DEM-only 계산은 fallback 또는 비교실험으로 분리한다.
5. 사용자 입력 AGL을 단일 고정 운용고도로 계산한다.
6. 발진기지 안테나 고도와 드론 비행고도를 잇는 LOS 직선고도를 샘플 지점별로 계산한다.
7. DSM 표면고도와 LOS 직선고도, Fresnel 반경을 비교하여 차폐위험 proxy를 산출한다.
8. 고도별 반복계산은 기본 기능이 아니라 선택적 민감도 분석으로 분리한다.
9. synthetic DEM/DSM으로 재현 가능한 테스트를 우선 작성한다.
10. 공개/샘플 DEM·DSM은 경로와 메타데이터만 기록하고 원천 대형 데이터는 커밋하지 않는다.
11. 출력값 이름에는 `proxy`, `risk`, `score`, `offline` 등 표현을 사용하고 `guaranteed`, `verified link quality`, `communication success` 표현은 사용하지 않는다.
12. 논문 기록에는 실제 드론운용 없이 산출된 오프라인 분석 결과임을 명시한다.
