# Codex / Claude Code 세부 에이전트 운영 플랜

작성일: 2026-07-08  
개정일: 2026-07-08  
대상 저장소: `leejinuk-minoan/uav-rf-terrain-planner`  
운영 원칙: GPT Master 통제하의 Task 단위 에이전트 교대

---

## 1. 운영 결론

본 프로젝트는 Codex와 Claude Code를 번갈아 활용하되, 기본 교대 기준은 **토큰 소모 시점**이 아니라 **Task 경계**로 설정한다.

```text
기본 원칙:
Task 완료 → PR 생성 → GPT 검토 → 사용자 승인/merge → 다음 Task에서 에이전트 교대
```

즉, Codex의 토큰이 아직 남아 있어도 Task가 완료되면 교대할 수 있고, Codex의 토큰이 부족하더라도 가능하면 현재 Task를 마무리하거나 handoff checkpoint를 남긴 뒤 교대한다.

중요한 제품 기준은 다음이다.

```text
발진기지 기본 출력 = Top 5 점 목록이 아니라 색상 기반 발진 가능구역 지도
경로 추천 = 사용자가 지도상에서 발진기지를 선택한 뒤 경로 후보 3개 제시
```

---

## 2. 역할 정의

| 주체 | 역할 | 주요 책임 |
|---|---|---|
| 사용자 | 최종 승인자 | 데이터 제공, PR merge 승인, 주요 가정 승인 |
| GPT Master | 총괄 통제 | Task 분해, Issue 작성, PR 검토, 다음 작업 지시 |
| Codex | 구현 하위 에이전트 | 기능 단위 구현, 테스트 작성, PR 생성 |
| Claude Code | 통합·디버깅 하위 에이전트 | 로컬 실행, CI 실패 수정, 다중 파일 리팩터링 |

---

## 3. 기본 교대 방식

### 3.1 정상 교대 흐름

```text
1. GPT Master가 Task 이슈 작성
2. 사용자 승인
3. Codex 또는 Claude Code가 해당 Task 브랜치 생성
4. 에이전트가 기능 구현 및 테스트 작성
5. 에이전트가 PR 생성
6. GPT Master가 PR 검토
7. 사용자 승인 후 merge
8. 다음 Task에서 다른 에이전트로 교대 가능
```

### 3.2 권장 교대 예시

```text
Task 001: Codex
Task 002: Claude Code
Task 003: Codex
Task 004: Codex
Task 005: Claude Code
Task 006: Codex
Task 007: Claude Code
Task 008: Codex
Task 009: Claude Code
Task 010: Claude Code
Task 011: Codex 또는 Claude Code
Task 012: Claude Code
```

단, 실제 배정은 각 시점의 토큰/사용량, 로컬 실행 필요성, CI 실패 여부에 따라 GPT Master가 조정한다.

---

## 4. Task별 우선 배정안

| Task | 내용 | 1차 담당 | 2차 담당 | 이유 |
|---:|---|---|---|---|
| 001 | 프로젝트 스캐폴딩 | Codex | Claude Code | 구조 생성과 테스트 초안에 적합 |
| 002 | 좌표 변환 | Codex | Claude Code | 순수 함수와 단위 테스트 중심 |
| 003 | synthetic DEM/DSM | Codex | Claude Code | 테스트 데이터 생성 중심 |
| 004 | 지형 단면 추출 | Codex | Claude Code | 알고리즘 구현 중심 |
| 005 | LOS 분석 | Codex | Claude Code | 테스트 기반 구현 가능 |
| 006 | Fresnel 계산 | Codex | Claude Code | 수학 함수와 테스트 중심 |
| 007 | 차폐점수 모델 | Codex | Claude Code | 점수식 구현 중심 |
| 008 | 발진 가능구역 색상 지도화 | Codex | Claude Code | 후보 셀 평가와 색상 등급 분류 중심 |
| 009 | 경로 후보 3개 | Claude Code | Codex | 통합·디버깅 난도가 높음 |
| 010 | 500m 경유점 | Codex | Claude Code | 계산 로직 중심 |
| 011 | Streamlit/Folium UI | Claude Code | Codex | 로컬 실행과 화면 확인 필요 |
| 012 | 통합 테스트/문서화 | Claude Code | Codex | CI·실행성 검증 중심 |

---

## 5. 예외: 같은 Task를 이어받아야 하는 경우

기본적으로 Task 중간 교대는 하지 않는다. 그러나 다음 상황에서는 같은 Task를 다른 에이전트가 이어받을 수 있다.

1. 에이전트의 토큰 또는 사용량이 Task 중간에 소진된 경우
2. 로컬 환경 또는 CI 오류가 특정 에이전트로 해결되지 않는 경우
3. 사용자가 명시적으로 이어받기를 지시한 경우
4. 기존 에이전트가 draft PR, 커밋, handoff note를 남긴 경우
5. 긴급 버그 수정 또는 CI 복구가 필요한 경우

### 5.1 같은 Task 인계 금지 조건

다음 상태에서는 이어받지 않는다.

- 변경 파일 목록이 불명확한 상태
- 테스트 실패 원인이 기록되지 않은 상태
- 어떤 기능이 완료되었고 어떤 기능이 미완성인지 모르는 상태
- 동일 브랜치를 두 에이전트가 동시에 수정하는 상태
- 작업 목적이 Issue 범위를 넘어선 상태

---

## 6. Handoff checkpoint 절차

같은 Task를 이어받아야 할 때는 반드시 handoff checkpoint를 남긴다.

### 6.1 handoff 위치

우선순위는 다음과 같다.

1. 해당 GitHub Issue comment
2. 해당 PR comment
3. `docs/handoff/task-00X-handoff.md`
4. 로컬 작업 메모 후 PR 본문에 포함

### 6.2 handoff 템플릿

```markdown
# Task Handoff

## 현재 Task
Task 00X - 작업명

## 현재 브랜치
agent/task-00X-...

## 담당했던 에이전트
Codex 또는 Claude Code

## 작업한 내용
- 변경 파일 1
- 변경 파일 2
- 구현 완료 기능

## 아직 미완성
- 남은 구현
- 실패한 테스트
- 불확실한 설계 판단

## 실행한 명령
- python -m pytest ...
- python -m compileall ...

## 현재 테스트 상태
- 통과:
- 실패:
- 미실행:

## 다음 에이전트가 해야 할 일
1. ...
2. ...
3. ...

## 주의사항
- 발진기지 기본 출력은 Top 5가 아니라 색상 기반 가능구역 지도
- AGL/MSL 혼동 금지
- 대형 GIS 데이터 커밋 금지
- 실제 드론 제어 기능 구현 금지
```

---

## 7. 에이전트별 운영 규칙

### 7.1 Codex 운영 규칙

Codex는 다음에 우선 사용한다.

- 기능 단위 초안 구현
- 순수 계산 함수 구현
- 단위 테스트 작성
- 문서 업데이트
- 작은 PR 생성

Codex가 Task를 시작할 때는 다음을 수행한다.

```text
1. AGENTS.md 확인
2. docs/master-plan.md 확인
3. 해당 Issue 범위 확인
4. Task 브랜치 생성 또는 지정 브랜치 확인
5. 기능 구현
6. 테스트 작성
7. PR 생성
8. 테스트 결과 및 한계 보고
```

### 7.2 Claude Code 운영 규칙

Claude Code는 다음에 우선 사용한다.

- 로컬 실행 확인
- CI 실패 수정
- 여러 파일 간 구조 정리
- 경로탐색/지도 UI처럼 통합 난도가 높은 작업
- Codex PR의 디버깅 또는 보완

Claude Code가 Task를 시작할 때는 다음을 수행한다.

```bash
git status
git branch --show-current
```

그 다음 기준 문서와 Issue/PR을 읽고 작업한다.

---

## 8. GPT Master의 검토 체크리스트

GPT Master는 각 Task 시작 전 다음을 확인한다.

1. 이 Task가 전체 로드맵에서 어느 위치인가?
2. 입력/출력과 수용 기준이 명확한가?
3. Codex와 Claude Code 중 어느 쪽이 적합한가?
4. 이전 Task 산출물이 merge되었는가?
5. 같은 파일을 동시에 수정할 위험이 있는가?

PR 생성 후에는 다음을 확인한다.

1. Task 범위 초과 여부
2. AGENTS.md 금지 범위 침범 여부
3. AGL/MSL 계산 오류 가능성
4. MGRS/WGS84/투영좌표계 처리 일관성
5. DEM/DSM 없이 synthetic 테스트가 가능한지
6. 테스트가 충분한지
7. 발진기지 출력이 Top 5 기본 출력으로 잘못 구현되지 않았는지
8. 발진 가능구역이 지도 색상 레이어로 표현 가능한 데이터 구조인지
9. 다음 Task에 구조적 부채를 남기지 않는지
10. 사용자가 승인해야 할 판단 사항이 분리되었는지

---

## 9. 사용자 승인 게이트

사용자는 모든 코드를 직접 읽지 않아도 되지만, merge 전 아래 항목은 확인한다.

| 확인 항목 | 설명 |
|---|---|
| Task 범위 | 이 PR이 지정 Task만 수행했는가 |
| 테스트 결과 | pytest/CI가 통과했는가 |
| 출력 형식 | 발진기지가 색상 기반 가능구역 지도로 구현되는가 |
| 알고리즘 가정 | AGL/MSL, 거리, 차폐점수 가정이 승인 가능한가 |
| 다음 단계 영향 | 다음 Task로 넘어가도 되는가 |

---

## 10. 금지 운영 방식

다음 방식은 사용하지 않는다.

```text
1. Codex와 Claude Code가 같은 브랜치를 동시에 수정
2. Task가 끝나지 않았는데 handoff 없이 다른 에이전트가 이어받음
3. 테스트 없이 main에 merge
4. synthetic 테스트 없이 실제 데이터부터 연결
5. 대형 DEM/DSM을 저장소에 직접 커밋
6. 실제 드론 제어 기능을 슬그머니 추가
7. “통신 보장”, “최적 운용 확정” 등 확정적 표현을 UI에 사용
8. 발진기지를 기본 출력에서 Top 5 점 목록으로 단순화
```

---

## 11. 최종 운영 방침

본 프로젝트의 에이전트 운영은 다음 문장으로 요약한다.

```text
GPT Master가 Task를 정의하고,
Codex와 Claude Code는 Task 단위로 교대하며,
발진 가능구역은 색상 지도 레이어로 구현하고,
예외적으로 같은 Task를 이어받을 때는 handoff checkpoint를 남기고,
사용자는 PR 단위로 승인한다.
```

이 방식은 토큰/사용량을 효율적으로 분산하면서도 아키텍처 일관성, 테스트 품질, 사용자 통제력을 유지하는 운영 방식이다.
