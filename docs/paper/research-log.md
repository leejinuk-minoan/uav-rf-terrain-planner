# Research Log

> Task 014 이후 이 문서는 historical archive 및 legacy index로 유지한다.
> 신규 기록은 장문 누적을 피하기 위해 docs/paper/research-notes/ 아래의 개별 파일로 작성한다.
> 기존 기록은 삭제하거나 축약하지 않는다.

책임 주체: GPT Master Agent  
목적: Task별 연구적 의미, 구현 근거, 논문 반영 위치를 누적 기록한다.

---

## 기록 원칙

- Cloud Execution Agent, Codex, Claude Code가 남긴 작업기록을 GPT Master가 검토한 뒤 편입한다.
- 실제 실행하지 않은 테스트는 `미실행`으로 기록한다.
- synthetic 검증, 공개/샘플 DEM/DSM 검증, 실제 링크상태 검증을 구분한다.
- 검증되지 않은 결과는 논문 결론으로 쓰지 않는다.

---

## Template

```markdown
# Research Log - Task 00X

## 작업 일자

## 관련 Issue / PR

## 담당 에이전트
Cloud Execution Agent / Codex / Claude Code / GPT Master

## 작업 목적

## 연구상 의미

## 구현 또는 문서 변경 내용

## 알고리즘 또는 모델 변경점

## 입력 데이터
- synthetic:
- 공개/샘플 DEM/DSM:
- 실제 링크상태 데이터:

## 출력 데이터

## 테스트 또는 검증
- 실행:
- 미실행:
- 실패:

## 결과 요약

## 한계

## 논문 반영 위치

## 그림/표 후보

## 참고문헌 필요 여부

## GPT Master 검토 메모
```

---

## Task Records

# Research Log - Task 001

## 작업 일자

2026-07-08

## 관련 Issue / PR

- Issue: #7
- PR: 생성 예정

## 담당 에이전트

Cloud Execution Agent

## 작업 목적

Python 프로젝트 기본 구조와 최신 DSM-primary 점수 기준을 코드 scaffold에 반영한다.

## 연구상 의미

Task 001은 이후 좌표 변환, synthetic DEM/DSM, DSM 기반 LOS/Fresnel, 색상 기반 발진 가능구역 지도화 실험을 재현 가능한 Python 패키지 구조로 누적하기 위한 기반 작업이다.

## 구현 또는 문서 변경 내용

- Python package scaffold 초안
- 최신 점수 가중치 config 초안
- 실제 링크 측정값을 요구하지 않는 schema 초안
- 색상 지도 기본 출력 기준 README 보강
- synthetic terrain metadata 예제 초안

## 알고리즘 또는 모델 변경점

- 실제 알고리즘 구현 없음
- 최신 기준 점수식 scaffold 반영:
  - `dsm_los_score × 0.40 + dsm_fresnel_score × 0.60`
  - `shielding_stability_score × 0.80 + distance_score × 0.20`
- surface complexity score는 기본 schema에서 제외

## 입력 데이터

- synthetic: metadata placeholder only
- 공개/샘플 DEM/DSM: 없음
- 실제 링크상태 데이터: 없음

## 출력 데이터

- config constants
- schema dataclasses
- smoke test source
- sample configuration

## 테스트 또는 검증

- 실행: 없음
- 미실행: `python -m pytest`, `python -m compileall src tests examples`, `python -m pip install -e .`
- 실패: 없음

## 결과 요약

Cloud/GitHub 기반으로 Task 001 scaffold를 작성했다. 실제 실행 결과는 CI 또는 로컬 검증 전까지 확정하지 않는다.

## 한계

- 실제 DEM/DSM 연결 없음
- 실제 LOS/Fresnel 계산 없음
- 실제 지도 화면 없음
- 실제 드론운용 및 실제 링크품질 검증 없음

## 논문 반영 위치

- 구현 환경 및 재현성
- 방법론의 baseline scoring schema
- 실험 설계 준비 단계

## 그림/표 후보

- Table: 프로젝트 의존성 및 모듈 구조
- Table: Task 001 기준 점수 가중치

## 참고문헌 필요 여부

현재 없음. 관련연구 인용은 GPT Master가 별도 원문 확인 후 반영한다.

## GPT Master 검토 메모

PR 생성 후 diff와 CI 결과를 기준으로 편입 여부를 판단한다.

---

# Research Log - Task 013

## 작업 일자

2026-07-09

## 관련 Issue / PR

- Issue: 생성 또는 연결 필요
- PR: 생성 예정

## 담당 에이전트

Codex / GPT Master

## 작업 목적

새로 확정된 두 가지 문서 결정사항을 프로젝트 기준 문서와 논문 준비 문서에 반영한다.

## 연구상 의미

현장 문제정의의 주체를 “여단급 이하 제대의 지휘소”로 확정하고, 공역사용승인 신청 또는 예하부대 드론 운용 고도 조정 시 필요한 고도를 사전에 정량적으로 판단하기 어렵다는 문제를 논문 문제정의에 반영한다.

또한 DSM 기반 LOS/Fresnel Clearance 조건을 만족하는 최소 요구 MSL과 직선 운용구간 내 최고 지표고 기준 AGL 변환을 논문 핵심 산출 구조로 반영한다. 이 기능은 공역사용승인 신청 고도의 과소·과도 산정을 줄이기 위한 의사결정 보조이며, 실제 정찰 성공이나 실제 통신 가능을 보장하는 기능이 아니다.

Android/TMMR offline은 논문 핵심 기능이 아니라 현장 운용자의 사용성을 보장하기 위한 제품화·배포 전략으로 분리한다. 따라서 논문 본문, 연구 결과, 구현 완료 사항으로 오해되지 않도록 제품 로드맵 문서와 decision log에서만 관리한다.

## 구현 또는 문서 변경 내용

- 최소 요구 MSL/AGL 산출 개념을 프로젝트 및 논문 설계 문서에 반영
- 현장 문제정의 주체를 여단급 이하 제대의 지휘소로 정리
- Android/TMMR offline을 논문 범위 밖 제품화·배포 로드맵으로 분리
- 논문 준비 문서에는 Android/TMMR offline을 기록하지 않는 경계 설정

## 알고리즘 또는 모델 변경점

- 코드 알고리즘 변경 없음
- 향후 모델 산출 항목으로 `minimum_required_msl_m`, `highest_dem_msl_m`, `required_agl_above_highest_dem_m`을 문서화
- 해당 산출값은 DSM 기반 LOS/Fresnel Clearance proxy로만 해석

## 입력 데이터

- synthetic: 없음
- 공개/샘플 DEM/DSM: 없음
- 실제 링크상태 데이터: 없음

## 출력 데이터

- 문서화된 연구 판단
- 제품 로드맵 경계
- 후속 구현 Task 기준

## 테스트 또는 검증

- 실행: 문서 diff, 금지어 검색, Android/TMMR 경계 검색, `git diff --check`
- 미실행: 로컬 pytest, 실제 DEM/DSM, 실제 링크상태 검증
- 실패: 없음

## 결과 요약

최소 요구 MSL/AGL 산출 기능은 논문·프로젝트 핵심 기능으로 반영하고, Android/TMMR offline은 논문 범위가 아닌 제품화·배포 로드맵으로 분리한다.

## 한계

- 실제 최소 요구 고도 계산 구현 없음
- 실제 DEM/DSM 연결 없음
- 실제 통신품질 검증 없음
- 실제 단말 검증 없음

## 논문 반영 위치

- 서론 및 문제정의
- 제안 모델
- 시스템 산출 데이터
- 민감도 분석 및 ablation 분석
- 한계 및 향후 연구

## 그림/표 후보

- Table: 최소 요구 MSL/AGL 산출 항목
- Figure: DSM 기반 LOS/Fresnel Clearance와 minimum_required_msl_m 개념도

## 참고문헌 필요 여부

LOS/Fresnel Clearance와 공역 고도 판단 보조를 연결하는 선행연구 또는 표준 검토가 필요하다.

## GPT Master 검토 메모

Android/TMMR offline이 논문 본문 또는 논문 준비 문서에 혼입되지 않았는지 merge 전 검색으로 확인해야 한다.
