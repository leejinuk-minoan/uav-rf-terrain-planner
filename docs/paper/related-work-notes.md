# Related Work Notes

책임 주체: GPT Master Agent  
목적: 학회 논문 관련연구 장에 사용할 선행연구 후보와 반영 방향을 관리한다.

---

## 정리 원칙

- 본 파일은 참고문헌 후보 노트이며, 최종 논문 인용문은 GPT Master가 원문 확인 후 작성한다.
- 웹 요약이나 2차 자료만으로 논문 결론을 단정하지 않는다.
- 실제 드론 운용 또는 실제 링크상태 검증이 없는 경우, 관련연구와 본 연구의 검증 수준을 명확히 구분한다.

---

## Related Work Categories

## 1. LOS 기반 RF 전파 분석

### 논문 반영 방향

LOS는 지형 차폐 판단의 1차 기준으로 사용할 수 있다. 단, LOS 확보가 곧 통신 품질 보장을 의미하지는 않는다.

### 본 프로젝트 반영

- LOS 점수를 차폐안정성 점수의 핵심 항목으로 사용
- DEM/DSM 기반 지형 단면에서 차단 여부 판정

### 추가 확인 필요

- LOS 판정과 RF LOS 차이
- 지구곡률/굴절 반영 여부
- 거리 범위별 적용 한계

---

## 2. Fresnel Zone 및 회절/차폐

### 논문 반영 방향

Fresnel Zone은 직접 가시선이 확보되어도 장애물 침범 시 신호 약화가 발생할 수 있음을 설명하는 근거가 된다.

### 본 프로젝트 반영

- Fresnel 여유 점수를 별도 항목으로 반영
- 주파수 대역 입력에 따라 Fresnel 반경 변화

### 추가 확인 필요

- 제1 Fresnel Zone clearance 기준
- 침범률을 0~100 점수로 변환하는 방식
- ITU-R P.526 등 회절 모델과의 관계

---

## 3. Irregular Terrain Model / Longley-Rice 계열

### 논문 반영 방향

Longley-Rice/ITM은 불규칙 지형에서 전파 손실을 추정하는 대표 모델이다. 본 프로젝트는 ITM을 직접 구현하는 것이 아니라, MVP 단계에서 지형 차폐 proxy 점수를 사용한다.

### 본 프로젝트 반영

- 지형 프로파일을 이용한다는 점에서 개념적 연계 가능
- 실제 수신전력 예측값이 아니라 차폐위험 점수임을 명확히 구분

### 추가 확인 필요

- ITM 적용 주파수/거리/입력 조건
- point-to-point mode와 area mode의 차이
- 실제 도입 여부는 향후 연구로 판단

---

## 4. Radio Map / Communication-aware UAV Path Planning

### 논문 반영 방향

Radio map 또는 aerial coverage map 기반 UAV 경로계획은 공간 격자별 통신품질 정보를 경로계획 비용으로 활용한다. 본 프로젝트의 색상 기반 발진 가능구역 지도와 경로비용 지도는 이 계열 연구와 구조적으로 유사하다.

### 본 프로젝트 반영

- 실제 radio map 대신 terrain-derived shielding score 사용
- 격자 기반 색상지도 생성
- 경로탐색 비용에 차폐위험 반영

### 추가 확인 필요

- radio map 기반 연구와 본 프로젝트의 차이점 명확화
- 실제 링크 측정이 없는 한계 명시
- 향후 RSSI/SINR/packet loss 기반 보정 가능성 제시

---

## 5. GIS 기반 지형 분석 및 DSM/DEM 활용

### 논문 반영 방향

DEM은 지형고도, DSM은 수목·건물 등 표면고도를 반영한다. DSM을 LOS/Fresnel 계산에 사용할 경우 DSM 장애물 점수와 중복 반영될 수 있으므로 주의가 필요하다.

### 본 프로젝트 반영

- DEM 기반 지형 차폐
- DSM 기반 표면장애물 보조 지표
- DEM-only / DSM-integrated / Hybrid 모드 비교 예정

---

## Reference Candidates

| ID | 주제 | 후보 자료 | 논문 반영 상태 |
|---|---|---|---|
| REF-LOS-01 | LOS propagation | RF line-of-sight / wireless link planning 자료 | 원문 확인 필요 |
| REF-FR-01 | Fresnel Zone | Fresnel Zone clearance 관련 자료 | 원문 확인 필요 |
| REF-ITU-01 | Diffraction | ITU-R P.526 | 원문 확인 필요 |
| REF-ITM-01 | Terrain propagation | Longley-Rice / ITM | 원문 확인 필요 |
| REF-RM-01 | Radio Map UAV path planning | Radio Map Based Path Planning for Cellular-Connected UAV | 원문 확인 필요 |
| REF-RM-02 | 3D Radio Map UAV path planning | Radio Map Based 3D Path Planning for Cellular-Connected UAV | 원문 확인 필요 |
| REF-COV-01 | Aerial coverage maps | Connectivity-Aware UAV Path Planning with Aerial Coverage Maps | 원문 확인 필요 |

---

## GPT Master Notes

관련연구 장에서는 본 프로젝트를 실제 통신품질 보장 시스템으로 포장하지 않는다. 정확한 표현은 다음과 같다.

```text
본 연구는 실제 링크상태 측정 기반 radio map이 없는 상황에서 DEM/DSM 기반 지형 차폐 proxy를 사용하여 발진 가능구역과 경로 후보를 시뮬레이션하는 방법론을 제안한다.
```
