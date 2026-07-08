# Research Log

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
