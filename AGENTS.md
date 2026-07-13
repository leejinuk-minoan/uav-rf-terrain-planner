# AGENTS.md

본 문서는 Cloud Execution Agent, Codex, Claude Code, 기타 GitHub 연동 AI 에이전트가 `uav-rf-terrain-planner` 저장소에서 작업할 때 따라야 할 공통 작업 규칙이다.

---

## 1. 프로젝트 목적

이 저장소는 연구·교육·시뮬레이션용 **드론 주파수 차폐 기반 발진기지 및 경로추천 프로그램**을 개발하기 위한 저장소다.

프로그램의 기본 목적은 다음과 같다.

```text
정찰목표지점 MGRS + 드론 운용반경 + 허가 운용고도 AGL + 통신 주파수 대역
→ DEM/DSM 기반 지형 단면 분석
→ LOS/Fresnel 기반 주파수·지형 차폐 위험 점수화
→ 드론 최대 운용거리를 고려한 발진 가능구역을 지도 평면에 색상 레이어로 표시
→ 사용자가 지도상에서 발진기지 선택
→ 선택 발진기지 기준 차폐 위험이 낮은 경로 후보 3개 제시
→ 약 500m 단위 경유점과 실 비행거리 출력
```

중요: 발진기지는 기본 출력에서 단순 Top 5 점 목록으로 제시하지 않는다. 기본 출력은 **색상 기반 발진 가능구역 지도**다. 점수 상위 후보점 목록은 디버깅·검증용 보조 출력으로만 둘 수 있다.

---

## 2. 반드시 읽어야 할 기준 문서

작업 전 아래 문서를 먼저 읽고, 구현 내용이 문서와 충돌하지 않도록 한다.

1. `README.md`
2. `AGENTS.md`
3. `CLAUDE.md`
4. `docs/master-plan.md`
5. `docs/research/research-index.md`
6. `docs/agent-build-feasibility.md`
7. `docs/agent-operations-plan.md`
8. `docs/github-app-limit-report.md`
9. `docs/prompts/codex-task-prompts.md`
10. `docs/prompts/claude-code-task-prompts.md`
11. `.github/ISSUE_TEMPLATE/feature_task.md`
12. `.github/workflows/ci.yml`

문서를 읽지 못하면 추측하지 말고, 어떤 파일을 읽지 못했는지 보고한다.

---

## 3. 개발 범위와 안전 경계

### 3.1 허용 범위

에이전트는 다음 작업을 수행할 수 있다.

- 연구·교육·시뮬레이션용 소프트웨어 구현
- 좌표 변환, 지형 데이터 처리, LOS/Fresnel 계산, 경로탐색, 지도 시각화 구현
- 샘플 또는 synthetic 데이터 기반 테스트 작성
- 문서화, 리팩터링, CI 구성
- GitHub Issue 단위의 기능 구현
- PR 생성 및 테스트 결과 보고
- Task별 연구 로그, 실험 로그, 의사결정 로그, PR 검토 로그 작성
- 학회 풀 페이퍼 초안 작성을 위한 근거 기록 정리

### 3.2 금지 범위

다음 기능은 구현하지 않는다.

- 실제 드론 자동조종, 실시간 비행제어, autopilot 연동
- 특정 실제 작전 수행을 위한 운용 지시 자동 생성
- 감시 회피, 탐지 회피, 공격 지원, 침투 경로 최적화 기능
- 무단 데이터 다운로드, 비공개 데이터 추출, 비인가 API 호출
- API 키, 토큰, 인증정보 저장소 커밋
- 대형 원천 GIS 데이터 직접 커밋
- 검증되지 않은 결과를 “통신 보장”, “최적 운용 확정”, “작전 성공 보장”처럼 확정적으로 표현
- 점수식 가중치를 실제 성능 검증값처럼 논문에 서술

본 프로젝트는 **분석·시뮬레이션·교육용 의사결정 보조 도구**로 유지한다.

---

## 4. 권장 저장소 구조

향후 구현 시 아래 구조를 우선 사용한다.

```text
uav-rf-terrain-planner/
├── src/
│   └── uav_rf_terrain/
│       ├── __init__.py
│       ├── config.py
│       ├── coordinates.py
│       ├── terrain.py
│       ├── profile.py
│       ├── fresnel.py
│       ├── shielding.py
│       ├── launch_sites.py
│       ├── route_planner.py
│       ├── waypoints.py
│       └── schemas.py
├── app/
│   └── streamlit_app.py
├── tests/
├── examples/
│   ├── sample_config.yaml
│   └── synthetic_terrain.py
├── docs/
│   └── paper/
│       ├── paper-outline.md
│       ├── research-log.md
│       ├── experiment-log.md
│       ├── decision-log.md
│       ├── pr-review-log.md
│       ├── figures-plan.md
│       ├── tables-plan.md
│       ├── related-work-notes.md
│       ├── limitations.md
│       ├── score-model-validation-plan.md
│       └── full-paper-draft.md
├── .github/
└── pyproject.toml
```

---

## 5. 기능 단위 작업 원칙

한 번에 전체 시스템을 구현하지 않는다. 반드시 기능 단위로 나누어 작업한다.

권장 태스크 순서:

```text
Task 001: 프로젝트 스캐폴딩, pyproject.toml, 기본 패키지 구조
Task 002: MGRS/WGS84/투영좌표계 변환 모듈
Task 003: DEM/DSM 래스터 로딩 및 샘플링 모듈
Task 004: 지형 단면 추출 모듈
Task 005: LOS 분석 및 테스트
Task 006: Fresnel Zone 반경/침범률 계산
Task 007: 차폐안정성 점수 모델
Task 008: 발진 가능구역 격자 평가 및 색상 지도화
Task 009: 경로탐색 기반 경로 후보 3개 생성
Task 010: 500m 단위 경유점 및 실 비행거리 계산
Task 011: Streamlit/Folium 기반 MVP UI
Task 012: 통합 테스트, 문서화, 샘플 실행 시나리오
Task 013: 논문용 연구기록 구조 생성 및 기존 기록 정리
Task 014: 실험 결과·그림·표 후보 정리
Task 015: 학회 풀 페이퍼 초안 작성
```

각 Task 종료 시 논문 작성용 연구기록 업데이트 항목을 남긴다.

---

## 6. 에이전트 운영 원칙

### 6.1 기본 원칙: Cloud Execution Agent 우선

본 프로젝트는 로컬 실행이 반드시 필요한 작업을 제외하고 **Cloud Execution Agent**를 우선 활용한다.

```text
GPT Master가 Task를 정의하고,
Cloud Execution Agent가 클라우드에서 가능한 구현·문서·PR 작업을 먼저 수행하며,
Codex와 Claude Code는 로컬 실행이 반드시 필요한 검증·수정 작업에만 투입하고,
사용자는 PR 단위로 최종 승인한다.
```

Cloud Execution Agent는 다음 작업을 우선 담당한다.

- GitHub 문서 조회
- Issue/PR 본문 작성
- 브랜치 생성
- 문서 생성·수정
- 순수 Python 모듈 초안 작성
- synthetic 테스트 코드 작성
- CI 설정 초안 작성
- 연구 로그, 실험 로그, 의사결정 로그, PR 검토 로그 초안 작성
- 로컬 검증 필요사항 분리

Cloud Execution Agent는 로컬에서 실행하지 않은 테스트를 통과했다고 말하지 않는다. `python -m pytest`, 패키지 설치, Streamlit/Folium 화면 확인, rasterio/GDAL 설치, 실제 DEM/DSM 연결은 로컬 검증 필요사항으로 분리한다.

### 6.2 논문 작성 책임

학회 풀 페이퍼 초안 작성은 GPT Master Agent가 총괄한다. Cloud Execution Agent, Codex, Claude Code는 논문 작성을 위한 근거 기록을 남기되, 최종 논문 구조 설계·문장 작성·결론 도출·선행연구 해석·점수식 타당성 판단은 GPT Master 책임이다.

GPT Master는 다음을 추적·관리한다.

- Cloud Execution Agent의 Issue, PR, 문서 변경, 연구 로그 초안
- Codex의 구현 기록, 테스트 결과, 수정 내역
- Claude Code의 로컬 실행 기록, UI 확인 결과, GIS 의존성 문제 해결 기록
- GitHub PR diff와 merge 이력
- Task별 실험 조건, synthetic/실제 데이터 구분, 검증 한계
- 점수식 변경 이력과 사용자 승인 여부

### 6.3 점수식 검증 책임

현재 구현된 MVP 점수식은 다음과 같다.

```text
차폐안정성 점수 = DSM LOS 점수 × 0.40 + DSM Fresnel 평균점수 × 0.60
발진 가능구역 종합점수 = 차폐안정성 점수 × 0.80 + 거리점수 × 0.20

if dsm_los_score == 0:
    shielding_stability_score = 0
```

`dsm_fresnel_score`는 경로 sample의 산술평균이며 `average_fresnel_score`와 같다. Task 032CD의 `worst_obstacle_score`, `dominant_obstacle`, single knife-edge diffraction loss는 보조 진단 proxy이며 현재 점수식, 색상 임계값, 후보 순위, route cost, waypoint cost에 반영하지 않는다.

별도 DSM 장애물 또는 표면복잡도 점수는 현재 기본 차폐안정성 점수에 포함되지 않는다. DSM 표면장애물 영향은 DSM 기반 LOS와 Fresnel 계산을 통해 반영한다.

GPT Master는 선행연구와 표준을 확인하여 점수식의 근거를 검토하고, 필요 시 보완방안을 제시한다. 실제 데이터 검증 전에는 이 가중치를 성능이 입증된 값으로 표현하지 않고, `heuristic weighting`, `초기 설계 가정`, `synthetic 검증 대상`으로 기록한다.

### 6.4 Codex와 Claude Code 투입 기준

Codex와 Claude Code는 기본 구현자가 아니라 로컬 실행·환경검증·UI 확인·GIS 의존성 문제 해결 담당자로 운용한다.

| 작업 | 추천 담당 |
|---|---|
| 순수 함수 단위 테스트 보완 | Codex |
| 작은 버그 수정 | Codex |
| 로컬 `pytest` 재현 | Codex 또는 Claude Code |
| 패키지 설치 확인 | Claude Code |
| rasterio/GDAL/geopandas 설치 문제 | Claude Code |
| Streamlit/Folium 화면 확인 | Claude Code |
| 지도 색상 레이어 시각 검증 | Claude Code |
| 실제 DEM/DSM 파일 연결 테스트 | Claude Code |
| CI와 로컬 결과 불일치 해결 | Claude Code |
| 복잡한 다중 파일 리팩터링 | Claude Code |

### 6.5 하나의 Task는 하나의 브랜치와 하나의 PR로 관리한다

```text
하나의 Task = 하나의 브랜치 = 하나의 PR
```

Cloud Execution Agent, Codex, Claude Code는 같은 브랜치를 동시에 수정하지 않는다. 로컬 에이전트가 Cloud Execution Agent 작업을 이어받아야 할 때는 handoff checkpoint를 먼저 확인한다.

---

## 7. Handoff checkpoint 필수 항목

handoff는 GitHub Issue comment, PR comment, 또는 `docs/handoff/` 문서로 남긴다.

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
- GPT Master가 확인해야 할 논문 쟁점이 있는가?

## 주의사항
- 발진기지 기본 출력은 Top 5가 아니라 색상 기반 가능구역 지도
- AGL/MSL 혼동 금지
- 대형 GIS 데이터 커밋 금지
- 실제 드론 제어 기능 구현 금지
```

---

## 8. 브랜치 전략

각 기능은 별도 브랜치에서 작업한다.

```text
main
├── agent/task-001-project-scaffold
├── agent/task-002-coordinate-core
├── agent/task-003-terrain-loader
├── agent/task-004-los-analysis
├── agent/task-005-fresnel-analysis
├── agent/task-006-launch-area-map
├── agent/task-007-route-planner
├── agent/task-008-waypoints
└── agent/task-009-streamlit-ui
```

PR 제목 형식:

```text
[Task 00X] 작업명
```

---

## 9. 코드 품질 기준

- Python 3.11 이상을 기준으로 한다.
- 함수와 클래스에 타입 힌트를 작성한다.
- 입력/출력 단위는 변수명 또는 docstring에 명확히 기록한다.
- GIS 데이터가 없어도 테스트 가능한 synthetic 데이터 생성기를 둔다.
- 핵심 수학 함수는 순수 함수로 구현하여 테스트 가능하게 한다.
- UI 코드와 계산 엔진을 분리한다.
- 대형 데이터는 저장소에 포함하지 않는다.
- 발진기지 기본 출력이 Top 5 목록으로 축소되지 않도록 테스트와 문서에서 확인한다.
- 각 Task 종료 시 연구기록 업데이트 항목을 남긴다.
- 점수식 가중치는 실제 데이터 검증 전까지 초기 설계 가정으로 기록한다.
