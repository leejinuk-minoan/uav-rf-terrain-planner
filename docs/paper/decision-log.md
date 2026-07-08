# Decision Log

책임 주체: GPT Master Agent  
목적: 프로젝트의 주요 설계 판단과 사용자 승인 여부를 누적 기록한다.

---

## 기록 원칙

- 점수식, 가중치, 데이터 처리 방식, UI 출력 방식 같은 논문 핵심 판단을 기록한다.
- 사용자 승인 여부를 명확히 남긴다.
- 대안과 선택 이유를 함께 기록한다.

---

## Initial Decisions

### DEC-20260708-01

## 결정 내용

발진기지 기본 출력은 Top 5 점 목록이 아니라 색상 기반 발진 가능구역 지도화로 한다.

## 상태

사용자 지시에 따라 확정.

### DEC-20260708-02

## 결정 내용

학회 풀 페이퍼 최종 작성, 선행연구 해석, 점수식 타당성 검토는 GPT Master Agent가 총괄한다.

## 상태

사용자 지시에 따라 확정.

### DEC-20260708-03

## 관련 Task / Issue / PR

- Task: 001 - Project scaffold and scoring schema preparation
- Issue: #7
- PR: #8

## 결정 내용

Task 001 scaffold의 기본 점수 기준은 다음으로 고정한다.

```text
shielding_stability_score = dsm_los_score × 0.40 + dsm_fresnel_score × 0.60
overall_score = shielding_stability_score × 0.80 + distance_score × 0.20
```

surface complexity score, surface obstacle density score, DSM roughness correction score는 기본 schema와 기본 점수식에서 제외한다.

## 사용자 승인 여부

- 승인: 사용자 지시로 Task 001 기준에 반영
- 보류: 없음
- 반려: 없음

### DEC-20260708-04

## 관련 Task / Issue / PR

- Task: 002 - Coordinate and candidate grid module
- Issue: #9
- PR: #10

## 결정 내용

Task 002에서는 좌표·격자 구조만 구현한다. 실제 DEM/DSM, LOS/Fresnel, 지도 UI는 후속 Task로 분리한다. Top 5 기본 출력이 아니라 색상지도용 candidate cell 구조를 유지한다.

## 사용자 승인 여부

- 승인: 사용자 지시로 Task 002 범위에 반영
- 보류: 없음
- 반려: 없음

### DEC-20260708-05

## 관련 Task / Issue / PR

- Task: 003 - Synthetic DEM/DSM terrain module
- Issue: #11
- PR: #12

## 결정 내용

Task 003에서는 실제 DEM/DSM을 사용하지 않고 pure Python synthetic DEM/DSM grid만 생성한다. Synthetic terrain은 LOS/Fresnel/Scoring 알고리즘의 경계조건 검증용이다. 실제 GeoTIFF, rasterio/GDAL/geopandas, 지도 렌더링은 후속 local-required Task로 분리한다.

## 사용자 승인 여부

- 승인: 사용자 지시로 Task 003 범위에 반영
- 보류: 없음
- 반려: 없음

### DEC-20260708-06

## 관련 Task / Issue / PR

- Task: 004 - Terrain profile extraction module
- Issue: #13
- PR: #14

## 결정 내용

Task 004에서는 synthetic DEM/DSM grid에서 terrain profile sample만 추출한다. LOS 직선고도 계산, DSM LOS 차단 판정, Fresnel 반경 계산, Fresnel clearance, scoring은 후속 Task로 분리한다. 실제 GeoTIFF, rasterio/GDAL/geopandas, 지도 렌더링은 후속 local-required Task로 분리한다.

## 사용자 승인 여부

- 승인: 사용자 지시로 Task 004 범위에 반영
- 보류: 없음
- 반려: 없음

### DEC-20260708-07

## 관련 Task / Issue / PR

- Task: 005 - DSM-based LOS analysis and tests
- Issue: #15
- PR: #16

## 결정 내용

Task 005에서는 TerrainProfile 기반 DSM LOS line analysis만 구현한다. Fresnel 반경/clearance, final scoring, 색상지도 classification은 후속 Task로 분리한다. DSM 표면고도가 LOS line 이상이면 LOS 침범으로 판정한다. 기본 dsm_los_score는 strict LOS cap 정책에 맞춰 blocked sample이 하나라도 있으면 0, 모두 clear이면 100으로 둔다.

## 사용자 승인 여부

- 승인: 사용자 지시로 Task 005 범위에 반영
- 보류: 없음
- 반려: 없음

### DEC-20260708-08

## 관련 Task / Issue / PR

- Task: 006 - DSM-based Fresnel radius and clearance analysis
- Issue: #17
- PR: 생성 예정

## 결정 일자

2026-07-08

## 결정 주체

사용자 지시 / Cloud Execution Agent 반영 / GPT Master 검토 필요

## 결정 내용

Task 006에서는 LOS analysis 결과를 기반으로 DSM Fresnel radius/clearance analysis만 구현한다. Fresnel radius는 `frequency_hz`와 `d1_m`/`d2_m` sample 위치에 따라 달라진다. 최종 `shielding_stability_score`와 `overall_score` 통합은 후속 Task로 분리한다. 실제 GeoTIFF, rasterio/GDAL/geopandas, 지도 렌더링은 후속 local-required Task로 분리한다.

## 배경

Task 005에서 LOS line MSL과 DSM clearance가 준비되었으므로, 후속 최종 scoring 전에 Fresnel radius와 DSM surface intrusion 정도를 독립 component로 계산해야 한다. Fresnel radius는 주파수와 경로상 위치에 민감하므로, 이 민감도를 synthetic test로 검증한다.

## 대안

1. Task 006에서 DSM Fresnel component만 구현
2. Task 006에서 Fresnel component와 shielding_stability_score를 함께 통합
3. Task 006에서 actual radio link metric까지 포함

## 선택 이유

1안을 선택한다. Component 단위 검증을 먼저 완료해야 후속 score model의 가중치와 cap rule을 검토하기 쉽다. 또한 실제 링크 측정값이 없으므로 RSSI/SINR/packet_loss 입력이나 실제 통신성능 검증을 포함하지 않는다.

## 영향받는 모듈

- `src/uav_rf_terrain/fresnel.py`
- `tests/test_fresnel.py`
- `src/uav_rf_terrain/__init__.py`
- 향후 `src/uav_rf_terrain/scoring.py`

## 논문 반영 위치

- 방법론: DSM Fresnel radius and clearance analysis
- 재현성: frequency 및 d1/d2 position sensitivity tests
- 한계: final scoring 및 실제 링크상태 검증 전 단계

## 검증 필요사항

- wavelength 계산
- first Fresnel radius 계산
- endpoint radius zero 처리
- frequency_hz > 0 검증
- 2.4GHz와 5.8GHz radius 차이 검증
- midpoint radius 최대 경향 검증
- clearance/score 관계 검증
- dsm_fresnel_score 평균 계산 검증

## 사용자 승인 여부

- 승인: 사용자 지시로 Task 006 범위에 반영
- 보류: CI/로컬 테스트 결과
- 반려: 없음

## GPT Master 검토 메모

PR 생성 후 실제 DEM/DSM, rasterio/GDAL/geopandas, GeoTIFF, final scoring, 색상지도 classification, UI가 포함되지 않았는지 확인해야 한다.
