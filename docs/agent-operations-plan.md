# Cloud Execution Agent 우선 에이전트 운영 플랜

작성일: 2026-07-08  
개정일: 2026-07-08  
대상 저장소: `leejinuk-minoan/uav-rf-terrain-planner`  
운영 원칙: GPT Master 통제하의 Cloud Execution Agent 우선 시행 및 로컬 필요 작업 제한 투입

---

## 1. 운영 결론

본 프로젝트는 앞으로 로컬 실행이 반드시 필요한 작업을 제외하고, GitHub 기반 **Cloud Execution Agent**를 우선 활용한다.

```text
기본 원칙:
GPT Master가 Task 정의
→ Cloud Execution Agent가 클라우드/GitHub에서 가능한 작업 수행
→ PR 생성
→ GPT Master 검토
→ 로컬 검증이 반드시 필요한 경우에만 Codex 또는 Claude Code 투입
→ 사용자 승인 후 merge
```

Codex와 Claude Code는 기본 구현자가 아니라 **로컬 실행·환경검증·UI 확인·GIS 의존성 문제 해결 담당자**로 운용한다.

중요한 제품 기준은 다음이다.

```text
발진기지 기본 출력 = Top 5 점 목록이 아니라 색상 기반 발진 가능구역 지도
경로 추천 = 사용자가 지도상에서 발진기지를 선택한 뒤 경로 후보 3개 제시
```

---

## 2. 역할 정의

| 주체 | 역할 | 주요 책임 |
|---|---|---|
| 사용자 | 최종 승인자 | 데이터 제공, 주요 가정 승인, PR merge 승인, 결과 화면 검수 |
| GPT Master | 총괄 통제 | Task 분해, Issue 작성, Cloud/Codex/Claude 배정, PR 검토, 연구기록 관리 |
| Cloud Execution Agent | 클라우드 시행 담당 | GitHub 파일 생성·수정, 순수 코드 초안, synthetic 테스트 초안, 문서화, PR 생성, 연구기록 초안 |
| Codex | 로컬 필요 구현·수정 담당 | 순수 함수 검증, 로컬 테스트 재현, 제한된 코드 수정, 작은 버그 수정 |
| Claude Code | 로컬 통합·디버깅 담당 | 패키지 설치, CI/로컬 불일치, Streamlit/Folium UI 확인, GIS 의존성 문제 해결 |

---

## 3. 기본 시행 흐름

### 3.1 정상 시행 흐름

```text
1. GPT Master가 Task 이슈 또는 작업 범위를 정의한다.
2. 사용자 또는 GPT Master가 작업 범위를 승인한다.
3. Cloud Execution Agent가 기준 문서와 Issue 범위를 확인한다.
4. Cloud Execution Agent가 브랜치를 생성하고 클라우드에서 가능한 구현·문서 작업을 수행한다.
5. Cloud Execution Agent가 PR을 생성하고 테스트 가능 범위와 로컬 검증 필요 항목을 분리해 보고한다.
6. GPT Master가 PR diff, 파일 내용, 요구사항 충족 여부를 검토한다.
7. 로컬 실행이 반드시 필요한 경우 Codex 또는 Claude Code에 제한 임무를 부여한다.
8. Codex 또는 Claude Code는 로컬 검증·최소 수정 후 결과를 PR에 기록한다.
9. GPT Master가 최종 검토한다.
10. 사용자 승인 후 merge한다.
11. Task 종료 시 연구기록을 업데이트한다.
```

### 3.2 기본 배정 원칙

```text
기본 시행자: Cloud Execution Agent
로컬 검증 필요 시: Codex 또는 Claude Code
최종 검토자: GPT Master
최종 승인자: 사용자
```

---

## 4. Cloud Execution Agent 담당 범위

Cloud Execution Agent는 로컬 실행 없이 GitHub/클라우드에서 처리 가능한 작업을 담당한다.

| 작업 | 가능 여부 | 비고 |
|---|---:|---|
| GitHub 기준 문서 읽기 | 가능 | README, AGENTS, master-plan 등 |
| Issue 본문 작성 | 가능 | GPT Master가 직접 작성할 수도 있음 |
| 브랜치 생성 | 가능 | `agent/task-00X-*` 형식 |
| 문서 파일 생성·수정 | 가능 | `docs/`, `docs/paper/` 포함 |
| `pyproject.toml` 작성 | 가능 | 실제 설치 검증은 로컬 또는 CI 필요 |
| Python 패키지 구조 생성 | 가능 | `src/`, `tests/`, `examples/` |
| 순수 계산 함수 작성 | 가능 | 좌표, 거리, 점수식 등 |
| synthetic 데이터 기반 테스트 코드 작성 | 가능 | 실제 실행 결과는 CI/로컬 확인 필요 |
| CI 설정 수정 | 가능 | GitHub Actions 기준 |
| PR 생성 | 가능 | 목적·구현·테스트·한계 포함 |
| 연구 로그 작성 | 가능 | Task 종료 시 초안 작성 |
| 실험 로그 양식 작성 | 가능 | 실제 실행값은 확인 필요 |
| 논문 초안 작성 | 가능 | 검증 수준 구분 필수 |

Cloud Execution Agent는 `python -m pytest` 실행, Streamlit 화면 확인, rasterio/GDAL 설치 확인, 실제 DEM/DSM 연결을 완료했다고 단정하지 않는다. 해당 항목은 로컬 검증 필요사항으로 분리한다.

---

## 5. 로컬에서 반드시 필요한 작업

다음 항목은 Codex 또는 Claude Code에 제한 임무로 부여한다.

| 로컬 필요 작업 | 추천 담당 | 이유 |
|---|---|---|
| `python -m pip install -e .` 실제 설치 확인 | Claude Code | 환경 의존성 확인 필요 |
| `python -m pytest` 로컬 재현 | Codex 또는 Claude Code | 실패 원인 재현 필요 |
| `rasterio`, `GDAL`, `geopandas` 설치 문제 해결 | Claude Code | OS/패키지 의존성 큼 |
| Streamlit/Folium 화면 실행 확인 | Claude Code | 실제 UI 확인 필요 |
| 지도 색상 레이어 시각 확인 | Claude Code | 브라우저/지도 렌더링 확인 필요 |
| 로컬 DEM/DSM 파일 연결 테스트 | Claude Code | 대형 데이터는 GitHub에 커밋하지 않음 |
| 실제 데이터 기반 샘플 실행 | Claude Code | 데이터 경로와 좌표계 확인 필요 |
| CI와 로컬 결과 불일치 해결 | Claude Code | 환경 차이 분석 필요 |
| 복잡한 다중 파일 리팩터링 | Claude Code | 통합 맥락 확인 필요 |
| 수학 함수의 빠른 단위 테스트 보완 | Codex | 제한된 순수 함수 수정에 적합 |

---

## 6. Task별 수정 배정안

| Task | 내용 | 1차 시행자 | 로컬 투입 조건 |
|---:|---|---|---|
| 001 | 프로젝트 스캐폴딩 | Cloud Execution Agent | 패키지 설치 또는 CI 실패 시 Claude Code |
| 002 | MGRS/WGS84/투영좌표계 변환 | Cloud Execution Agent | `mgrs`, `pyproj` 설치·실행 오류 시 Claude Code |
| 003 | synthetic DEM/DSM 및 래스터 샘플링 | Cloud Execution Agent | rasterio/GDAL 실제 설치 확인 필요 시 Claude Code |
| 004 | 지형 단면 추출 | Cloud Execution Agent | 성능·좌표 샘플링 오류 재현 시 Codex/Claude Code |
| 005 | LOS 분석 및 테스트 | Cloud Execution Agent | 테스트 실패 재현 어려울 때 Codex |
| 006 | Fresnel Zone 계산 | Cloud Execution Agent | 수식 검산 보완 시 Codex |
| 007 | 차폐안정성 점수 모델 | Cloud Execution Agent | 원칙적으로 로컬 불필요 |
| 008 | 발진 가능구역 격자 평가 및 색상 지도화 | Cloud Execution Agent | 실제 지도 레이어 시각 확인은 Claude Code |
| 009 | 경로탐색 기반 경로 후보 3개 생성 | Cloud Execution Agent 초안 | 경로 중복·속도·통합 문제 확인 시 Claude Code |
| 010 | 500m 단위 경유점 및 실 비행거리 계산 | Cloud Execution Agent | 좌표 변환 연동 오류 시 Codex/Claude Code |
| 011 | Streamlit/Folium MVP UI | Claude Code | 처음부터 로컬 화면 확인 필요 |
| 012 | 통합 테스트, 문서화, 샘플 실행 시나리오 | Claude Code | 로컬 실행·화면·CI 검증 필요 |
| 013 | 논문용 연구기록 구조 생성 | Cloud Execution Agent 또는 GPT Master | 로컬 불필요 |
| 014 | 실험 결과·그림·표 후보 정리 | GPT Master + Cloud Execution Agent | 실제 화면 캡처는 Claude Code |
| 015 | 학회 풀 페이퍼 초안 | GPT Master | 로컬 불필요 |

---

## 7. Handoff checkpoint 절차

Cloud Execution Agent, Codex, Claude Code 사이에 작업이 넘어갈 때는 handoff checkpoint를 남긴다. 특히 Cloud Execution Agent가 만든 PR을 로컬 에이전트가 이어받을 때는 로컬 검증 범위를 명확히 제한한다.

### 7.1 handoff 위치

우선순위는 다음과 같다.

1. 해당 GitHub Issue comment
2. 해당 PR comment
3. `docs/handoff/task-00X-handoff.md`
4. 로컬 작업 메모 후 PR 본문에 포함

### 7.2 handoff 템플릿

```markdown
# Task Handoff

## 현재 Task
Task 00X - 작업명

## 현재 브랜치
agent/task-00X-...

## 담당했던 에이전트
Cloud Execution Agent / Codex / Claude Code

## 작업한 내용
- 변경 파일 1
- 변경 파일 2
- 구현 완료 기능

## 아직 미완성
- 남은 구현
- 실패한 테스트
- 불확실한 설계 판단
- 로컬 검증 필요사항

## 실행한 명령
- Cloud Execution Agent는 실제 로컬 명령을 실행하지 않았다면 "미실행"으로 기록
- Codex/Claude Code는 실제 실행한 명령만 기록

## 현재 테스트 상태
- 통과:
- 실패:
- 미실행:

## 다음 에이전트가 해야 할 일
1. ...
2. ...
3. ...

## 논문 기록 필요사항
- 이 Task가 논문 어느 장에 반영되는가?
- 실험/테스트 결과가 있는가?
- 그림/표 후보가 있는가?
- 한계 또는 검증 필요사항이 있는가?

## 주의사항
- 발진기지 기본 출력은 Top 5가 아니라 색상 기반 가능구역 지도
- AGL/MSL 혼동 금지
- 대형 GIS 데이터 커밋 금지
- 실제 드론 제어 기능 구현 금지
```

---

## 8. 에이전트별 운영 규칙

### 8.1 Cloud Execution Agent 운영 규칙

Cloud Execution Agent는 다음에 우선 사용한다.

- GitHub 문서 조회
- Issue/PR 본문 작성
- 브랜치 생성
- 문서 생성·수정
- 순수 Python 모듈 초안 작성
- synthetic 테스트 코드 작성
- CI 설정 초안 작성
- 연구 로그, 실험 로그, 의사결정 로그, PR 검토 로그 초안 작성
- 로컬 검증 필요사항 분리

Cloud Execution Agent가 Task를 시작할 때는 다음을 수행한다.

```text
1. README.md 확인
2. AGENTS.md 확인
3. CLAUDE.md 확인
4. docs/master-plan.md 확인
5. docs/research/research-index.md 확인
6. docs/agent-build-feasibility.md 확인
7. docs/agent-operations-plan.md 확인
8. 해당 Issue 범위 확인
9. 클라우드에서 가능한 작업만 수행
10. 로컬 실행 필요사항은 별도 인계사항으로 기록
```

Cloud Execution Agent는 다음을 하지 않는다.

- 로컬에서 실행하지 않은 테스트를 통과했다고 말하기
- Streamlit/Folium 화면을 확인했다고 단정하기
- rasterio/GDAL 설치 문제를 해결했다고 단정하기
- 실제 DEM/DSM 연결 결과를 확인했다고 단정하기
- 실제 드론 제어, 탐지 회피, 침투, 공격 지원 기능 구현하기

### 8.2 Codex 운영 규칙

Codex는 다음에 제한적으로 사용한다.

- 순수 함수 단위의 로컬 테스트 보완
- 작은 버그 수정
- 테스트 실패 재현 및 최소 수정
- 수학 함수 검산
- Cloud Execution Agent PR의 제한된 보완

Codex는 Task 전체를 임의로 재설계하지 않는다. 지정된 PR 또는 Issue 범위 안에서만 작업한다.

### 8.3 Claude Code 운영 규칙

Claude Code는 다음에 우선 사용한다.

- 로컬 설치 확인
- CI 실패 수정
- 여러 파일 간 구조 정리
- Streamlit/Folium UI 실행 확인
- 지도 색상 레이어 화면 검증
- rasterio/GDAL/geopandas 의존성 문제 해결
- 실제 DEM/DSM 경로 연결 테스트
- Cloud Execution Agent PR의 로컬 디버깅 또는 보완

Claude Code가 로컬 작업을 시작할 때는 다음을 수행한다.

```bash
git status
git branch --show-current
```

그 다음 기준 문서, Issue, PR, handoff checkpoint를 읽고 작업한다.

---

## 9. GPT Master의 검토 체크리스트

GPT Master는 각 Task 시작 전 다음을 확인한다.

1. 이 Task가 전체 로드맵에서 어느 위치인가?
2. 클라우드에서 가능한 작업인가, 로컬 실행이 필요한 작업인가?
3. 입력/출력과 수용 기준이 명확한가?
4. Cloud Execution Agent, Codex, Claude Code 중 어느 쪽이 적합한가?
5. 이전 Task 산출물이 merge되었는가?
6. 같은 파일을 동시에 수정할 위험이 있는가?

PR 생성 후에는 다음을 확인한다.

1. Task 범위 초과 여부
2. AGENTS.md 금지 범위 침범 여부
3. Cloud Execution Agent가 로컬 실행 결과를 과장하지 않았는지
4. AGL/MSL 계산 오류 가능성
5. MGRS/WGS84/투영좌표계 처리 일관성
6. DEM/DSM 없이 synthetic 테스트가 가능한지
7. 테스트가 충분한지
8. 발진기지 출력이 Top 5 기본 출력으로 잘못 구현되지 않았는지
9. 발진 가능구역이 지도 색상 레이어로 표현 가능한 데이터 구조인지
10. 로컬 검증 필요사항이 Codex/Claude Code 인계사항으로 분리되었는지
11. 다음 Task에 구조적 부채를 남기지 않는지
12. 사용자가 승인해야 할 판단 사항이 분리되었는지
13. 연구 로그·실험 로그·의사결정 로그·PR 검토 로그 업데이트 항목이 있는지

---

## 10. 사용자 승인 게이트

사용자는 모든 코드를 직접 읽지 않아도 되지만, merge 전 아래 항목은 확인한다.

| 확인 항목 | 설명 |
|---|---|
| Task 범위 | 이 PR이 지정 Task만 수행했는가 |
| 시행자 구분 | Cloud Execution Agent 작업과 로컬 검증 작업이 구분되는가 |
| 테스트 결과 | 실제 실행된 테스트와 미실행 테스트가 구분되는가 |
| 출력 형식 | 발진기지가 색상 기반 가능구역 지도로 구현되는가 |
| 알고리즘 가정 | AGL/MSL, 거리, 차폐점수 가정이 승인 가능한가 |
| 로컬 검증 필요성 | Codex/Claude Code 투입이 필요한 항목이 분리되었는가 |
| 연구기록 | Task 종료 시 논문용 기록이 남는가 |
| 다음 단계 영향 | 다음 Task로 넘어가도 되는가 |

---

## 11. 금지 운영 방식

다음 방식은 사용하지 않는다.

```text
1. Codex와 Claude Code가 같은 브랜치를 동시에 수정
2. Cloud Execution Agent와 로컬 에이전트가 같은 파일을 조율 없이 동시 수정
3. Task가 끝나지 않았는데 handoff 없이 다른 에이전트가 이어받음
4. Cloud Execution Agent가 실행하지 않은 로컬 테스트를 통과했다고 보고
5. 테스트 없이 main에 merge
6. synthetic 테스트 없이 실제 데이터부터 연결
7. 대형 DEM/DSM을 저장소에 직접 커밋
8. 실제 드론 제어 기능을 슬그머니 추가
9. “통신 보장”, “최적 운용 확정” 등 확정적 표현을 UI에 사용
10. 발진기지를 기본 출력에서 Top 5 점 목록으로 단순화
```

---

## 12. 최종 운영 방침

본 프로젝트의 에이전트 운영은 다음 문장으로 요약한다.

```text
GPT Master가 Task를 정의하고,
Cloud Execution Agent가 클라우드에서 가능한 구현·문서·PR 작업을 먼저 수행하며,
Codex와 Claude Code는 로컬 실행이 반드시 필요한 검증·수정 작업에만 투입하고,
발진 가능구역은 Top 5가 아니라 색상 기반 지도 레이어로 구현하며,
각 Task 종료 시 논문 작성용 연구기록을 남기고,
사용자는 PR 단위로 최종 승인한다.
```

이 방식은 클라우드에서 가능한 작업을 빠르게 선행하면서도, 로컬 실행이 필요한 GIS·UI·패키지 의존성 검증을 별도 통제점으로 분리하여 아키텍처 일관성, 테스트 품질, 사용자 통제력을 유지하는 운영 방식이다.
