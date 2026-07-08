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
