# 논문 최종 설계 기준

작성일: 2026-07-09  
책임 주체: GPT Master Agent  
적용 범위: UAV RF Terrain Planner 논문 설계, 시스템 구현 결과 정리, 실제 DEM/DSM 적용 분석, 민감도 분석, ablation 분석

---

## 1. 최종 논문 제목

현재 확정 제목은 다음과 같다.

```text
DSM 기반 LOS 및 Fresnel Clearance를 고려한 여단급 이하 제대의 드론 발진기지 및 비행경로 선정 모델 설계
```

시스템 빌드 완료 이후 실제 DEM/DSM 적용, 민감도 분석, ablation 분석까지 포함하는 확장 제목 후보는 다음과 같다.

```text
DSM 기반 LOS 및 Fresnel Clearance를 고려한 여단급 이하 제대의 드론 발진기지 및 비행경로 선정 모델 설계:
실제 지형 적용 및 민감도·Ablation 분석을 중심으로
```

---

## 2. 최종 논문 성격

본 프로젝트의 논문 최종상태는 **실측 통신품질 검증 논문이 아니다.**

본 프로젝트의 최종 논문은 실제 DEM/DSM 지형자료를 적용한 시스템 구현 결과와 민감도 및 ablation 분석을 통해 DSM, LOS, Fresnel Clearance, 거리 여유도 요소가 드론 발진기지 및 비행경로 선정 결과에 미치는 영향을 분석하는 **모델 설계·구현·분석 논문**이다.

최종 논문은 다음 범위를 포함한다.

1. DSM 기반 LOS 및 Fresnel Clearance 모델 설계
2. 발진기지 후보 cell scoring 및 색상지도 분류 구조
3. 비행경로 후보 및 waypoint 산출 구조
4. 실제 DEM/DSM 지형자료 적용 사례분석
5. 주파수, AGL, 운용반경, 가중치, threshold 변화에 따른 민감도 분석
6. distance-only, DEM-only, LOS-only 등 baseline 대비 ablation 분석
7. 실측자료 부재에 따른 한계와 후속 RF 계측·드론 로그 기반 검증 가능성

---

## 3. 명시적 제외 범위

다음은 본 논문의 최종 범위에서 제외한다.

```text
실제 드론 비행 검증
실제 통신 성공률 검증
RSSI 예측
SINR 예측
packet loss 예측
throughput 예측
latency 예측
실제 작전 운용 보장
통신 가능 여부 보장
최적 발진지 보장
```

단, 향후 별도 후속연구로 RF 계측자료 또는 드론 운용 로그가 확보될 경우, 본 모델의 점수와 실제 링크품질 지표 간 관계를 분석하는 실측 검증 논문으로 확장할 수 있다.

---

## 4. 최종 분석 범위

최종 논문에는 다음 분석을 포함하는 것을 목표로 한다.

```text
1. 모델 설계
2. 시스템 구현
3. 실제 DEM/DSM 지형 적용 사례분석
4. 민감도 분석
5. ablation 분석
6. 한계 및 후속 실측 검증 가능성
```

---

## 5. 실제 지형 적용 사례분석

실제 DEM/DSM을 시스템에 입력하여 다음 산출물을 생성한다.

```text
후보 발진지 색상지도
후보 cell별 LOS/Fresnel/거리/종합점수
후보 cell별 color class 및 classification reason
경로 후보 3종
waypoint별 AGL/MSL/발진기지 대비 고도차/누적거리
```

이 분석은 실제 통신품질 검증이 아니라 **실제 지형자료 기반 적용 가능성 분석**이다. 논문에서는 “실제 지형 적용”, “적용성 분석”, “사례분석”으로 표현하고, “실제 통신성능 검증”으로 표현하지 않는다.

---

## 6. 민감도 분석 항목

최종 논문에서 수행할 민감도 분석 항목은 다음과 같다.

```text
AGL 운용고도 변화
통신 주파수 변화
운용반경 변화
shielding/distance 가중치 변화
LOS/Fresnel 가중치 변화
color classification threshold 변화
```

각 항목은 다음 산출 결과의 변화로 분석한다.

```text
Green/Yellow/Orange/Red/Excluded cell 비율
평균 overall_score
평균 shielding_stability_score
평균 dsm_los_score
평균 dsm_fresnel_score
평균 distance_score
경로 후보별 총거리
경로 후보별 high-risk cell 통과 수
경로 후보별 평균 shielding score
waypoint별 고도 변화
```

민감도 분석의 목적은 모델 입력값과 휴리스틱 가중치 변화가 발진 가능구역 및 경로 후보 결과에 미치는 영향을 확인하는 것이다. 이는 실제 통신품질 검증이 아니라 모델 반응성 분석이다.

---

## 7. Ablation 분석 항목

최종 논문에서 수행할 ablation 분석 항목은 다음과 같다.

```text
distance-only vs proposed model
DEM-only vs DSM-primary
LOS-only vs LOS + Fresnel
Fresnel-only vs LOS + Fresnel
shielding-only vs shielding + distance
Top score list 방식 vs color map 방식
```

분석 목적은 다음과 같다.

```text
거리만 고려할 때와 DSM 기반 차폐위험을 함께 고려할 때 결과가 어떻게 달라지는지 확인한다.
DEM만 사용할 때와 DSM을 사용할 때 건물·수목·구조물 반영 차이를 확인한다.
LOS만 사용할 때와 Fresnel Clearance를 함께 사용할 때 후보지 구분력이 어떻게 달라지는지 확인한다.
차폐안정성만 사용할 때와 거리 여유도를 함께 사용할 때 운용반경 경계 후보 처리가 어떻게 달라지는지 확인한다.
Top score list 방식과 color map 방식이 사용자 의사결정에 제공하는 정보량 차이를 비교한다.
```

Ablation 분석은 본 연구의 학술적 설득력을 높이는 핵심 분석이다. 특히 “드론 발진기지 선정은 단순 거리 문제가 아니라 DSM 기반 LOS 및 Fresnel Clearance를 함께 고려해야 하는 문제”라는 논지를 뒷받침한다.

---

## 8. 시스템 산출 데이터 활용 계획

최종 시스템에서 논문 분석에 활용할 데이터 항목은 다음과 같다.

```text
candidate cell id
candidate coordinate
DEM elevation
DSM elevation
surface_delta
distance_2d_m
distance_3d_m
within_operation_radius
dsm_los_score
dsm_fresnel_score
distance_score
shielding_stability_score
overall_score
color_class
classification_reason
route_type
route_total_distance
route_mean_shielding_score
route_high_risk_cell_count
waypoint_id
waypoint AGL
waypoint MSL
waypoint height difference from launch site
waypoint cumulative distance
```

이 데이터는 실측 ground truth가 아니다. 논문에서는 모델 산출 결과 분석, 내부 일관성 검증, 실제 지형 적용성 분석, 민감도 분석, ablation 분석에 사용한다.

---

## 9. 논문에서 가능한 주장

다음 표현은 허용된다.

```text
제안 모델을 설계하였다.
제안 시스템을 구현하였다.
실제 DEM/DSM 지형자료에 적용하였다.
실제 지형 적용 사례분석을 수행하였다.
민감도 분석을 수행하였다.
ablation 분석을 수행하였다.
DSM 반영 여부에 따른 후보지 분류 차이를 분석하였다.
LOS/Fresnel 요소가 발진지 평가 결과에 미치는 영향을 분석하였다.
거리-only 방식과 제안 모델의 의사결정 결과 차이를 비교하였다.
주파수·AGL·운용반경 변화에 따른 발진 가능구역 변화를 분석하였다.
```

---

## 10. 논문에서 금지할 주장

다음 표현은 금지한다.

```text
실제 통신 성공률을 검증하였다.
RSSI/SINR/packet loss를 예측하였다.
실제 드론 비행에서 효과를 입증하였다.
실제 작전 운용 가능성을 보장한다.
최적 발진지를 보장한다.
통신 가능 여부를 보장한다.
제안 점수가 실제 링크품질을 직접 예측한다.
```

---

## 11. 최종 논문 권장 구성

최종 논문 구성은 다음을 기준으로 한다.

```text
1. 서론
2. 관련연구
3. 문제정의
4. 제안 모델
   4.1 후보 발진지 격자 모델
   4.2 DSM 기반 LOS 분석 모델
   4.3 DSM 기반 Fresnel Clearance 분석 모델
   4.4 거리 여유도 및 종합점수 모델
   4.5 색상지도 분류 및 경로 후보 모델
5. 시스템 구현
6. 실제 DEM/DSM 지형 적용 사례분석
7. 민감도 분석
8. Ablation 분석
9. 논의
10. 한계 및 향후 연구
11. 결론
```

---

## 12. 후속 Task 연결

향후 구현 Task는 이 문서의 최종 논문 목표를 기준으로 기록되어야 한다.

```text
Task 008 이후: color classification 결과를 Green/Yellow/Orange/Red/Excluded cell 비율 분석에 연결
실제 DEM/DSM 연동 이후: 실제 지형 적용 사례분석에 연결
경로 후보 구현 이후: 경로별 거리·위험도·waypoint 분석에 연결
민감도 분석 Task 이후: 주파수/AGL/운용반경/가중치/threshold 변화 결과를 논문 결과 장에 연결
ablation 분석 Task 이후: distance-only, DEM-only, LOS-only 등 baseline 비교를 논문 핵심 결과로 연결
```

---

## 13. GPT Master 관리 기준

논문 최종 구조, 문장, 결론, 선행연구 해석, 민감도 및 ablation 결과 해석은 GPT Master Agent가 관리한다.

Cloud Execution Agent, Codex, Claude Code는 논문 근거가 되는 구현 기록, 실험 기록, PR 기록, 로컬 검증 기록을 남긴다. 단, 논문 결론을 임의로 확정하거나 실측 검증이 수행된 것처럼 서술하지 않는다.
