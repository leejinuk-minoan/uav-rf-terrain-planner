# Decision Log

책임 주체: GPT Master Agent  
목적: 프로젝트의 주요 설계 판단과 사용자 승인 여부를 누적 기록한다.

---

## 기록 원칙

- 점수식, 가중치, 데이터 처리 방식, UI 출력 방식 같은 논문 핵심 판단을 기록한다.
- 사용자 승인 여부를 명확히 남긴다.
- 대안과 선택 이유를 함께 기록한다.

---

## Template

```markdown
# Decision DEC-YYYYMMDD-XX

## 관련 Task / Issue / PR

## 결정 일자

## 결정 주체

## 결정 내용

## 배경

## 대안
1. 
2. 
3.

## 선택 이유

## 영향받는 모듈

## 논문 반영 위치

## 검증 필요사항

## 사용자 승인 여부
- 승인:
- 보류:
- 반려:

## GPT Master 검토 메모
```

---

## Initial Decisions

### DEC-20260708-01

## 결정 내용

발진기지 기본 출력은 Top 5 점 목록이 아니라 색상 기반 발진 가능구역 지도화로 한다.

## 논문 반영 위치

제안 시스템 구조, 알고리즘 설계, 결과 시각화.

## 상태

사용자 지시에 따라 확정.

### DEC-20260708-02

## 결정 내용

학회 풀 페이퍼 최종 작성, 선행연구 해석, 점수식 타당성 검토는 GPT Master Agent가 총괄한다.

## 논문 반영 위치

전체 논문 작성 관리 원칙.

## 상태

사용자 지시에 따라 확정.

### DEC-20260708-03

## 관련 Task / Issue / PR

- Task: 001 - Project scaffold and scoring schema preparation
- Issue: #7
- PR: 생성 예정

## 결정 일자

2026-07-08

## 결정 주체

사용자 지시 / Cloud Execution Agent 반영 / GPT Master 검토 필요

## 결정 내용

Task 001 scaffold의 기본 점수 기준은 다음으로 고정한다.

```text
shielding_stability_score = dsm_los_score × 0.40 + dsm_fresnel_score × 0.60
overall_score = shielding_stability_score × 0.80 + distance_score × 0.20
```

surface complexity score, surface obstacle density score, DSM roughness correction score는 기본 schema와 기본 점수식에서 제외한다.

## 배경

DSM 기반 LOS와 DSM 기반 Fresnel이 표면장애물의 중심선 차단과 제1 Fresnel Zone 침범을 이미 반영하므로, 별도 표면복잡도 점수는 중복 감점 위험이 있다.

## 대안

1. DSM LOS/Fresnel만 사용
2. DSM LOS/Fresnel + surface complexity score 추가
3. DEM-only 기준으로 단순화

## 선택 이유

실제 링크 측정값 없이 검증되지 않은 추가 보정항을 넣지 않고, 오프라인 DSM 기반 차폐위험 proxy로 제한하기 위해 1안을 채택한다.

## 영향받는 모듈

- `src/uav_rf_terrain/config.py`
- `src/uav_rf_terrain/schemas.py`
- 향후 `los.py`, `fresnel.py`, `scoring.py`, `pipeline.py`

## 논문 반영 위치

- 방법론
- 점수식 정의
- 한계 및 향후 연구

## 검증 필요사항

- Task 006에서 LOS cap rule 구현 확인
- Task 008에서 가중치 민감도 분석
- DSM-primary vs DEM-only ablation 분석

## 사용자 승인 여부

- 승인: 사용자 지시로 Task 001 기준에 반영
- 보류: CI/로컬 테스트 결과
- 반려: 없음

## GPT Master 검토 메모

PR 생성 후 점수식과 schema가 사용자 지시와 충돌하지 않는지 검토해야 한다.

### DEC-20260708-04

## 관련 Task / Issue / PR

- Task: 002 - Coordinate and candidate grid module
- Issue: #9
- PR: 생성 예정

## 결정 일자

2026-07-08

## 결정 주체

사용자 지시 / Cloud Execution Agent 반영 / GPT Master 검토 필요

## 결정 내용

Task 002에서는 좌표·격자 구조만 구현한다. 실제 DEM/DSM, LOS/Fresnel, 지도 UI는 후속 Task로 분리한다. Top 5 기본 출력이 아니라 색상지도용 candidate cell 구조를 유지한다.

## 배경

발진 가능구역 지도화는 목표 주변 candidate cell 생성과 운용반경 필터링을 먼저 필요로 한다. 그러나 실제 지형고도, DSM 표면고도, LOS/Fresnel 및 최종 score는 별도 검증과 후속 모듈이 필요하다.

## 대안

1. Task 002에서 좌표·격자 구조만 구현
2. Task 002에서 MGRS 변환, DEM/DSM loading, LOS/Fresnel 일부까지 함께 구현
3. Task 002를 문서 작업만으로 제한

## 선택 이유

1안을 선택한다. 이 방식은 CI 안정성을 유지하면서 순수 Python으로 검증 가능한 구조를 먼저 만들고, 무거운 GIS dependency와 실제 지형분석은 후속 local-required task로 분리할 수 있다.

## 영향받는 모듈

- `src/uav_rf_terrain/coordinates.py`
- `src/uav_rf_terrain/grid.py`
- `src/uav_rf_terrain/__init__.py`
- `tests/test_coordinates.py`
- `tests/test_grid.py`

## 논문 반영 위치

- 방법론: 좌표/격자 생성 단계
- 재현성: 순수 Python scaffold와 CI 테스트
- 한계: 실제 좌표 정확도 및 지형자료 검증은 후속 검증 필요

## 검증 필요사항

- optional GIS dependency 기반 MGRS 변환 정확도 로컬 검증
- Task 003 이후 synthetic DEM/DSM와 연결
- Task 004 이후 LOS/Fresnel 계산과 연결
- Task 006 이후 색상 등급 산출과 연결

## 사용자 승인 여부

- 승인: 사용자 지시로 Task 002 범위에 반영
- 보류: CI/로컬 테스트 결과
- 반려: 없음

## GPT Master 검토 메모

PR 생성 후 Top 5 기본 출력 구조가 없는지, 실제 DEM/DSM·LOS/Fresnel·지도 UI가 포함되지 않았는지, candidate cell 구조가 색상지도 생성에 적합한지 검토해야 한다.
