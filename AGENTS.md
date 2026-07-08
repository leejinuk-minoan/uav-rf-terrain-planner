# AGENTS.md

본 문서는 Codex, Claude Code, 기타 GitHub 연동 AI 에이전트가 `uav-rf-terrain-planner` 저장소에서 작업할 때 따라야 할 공통 작업 규칙이다.

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

중요: 발진기지는 기본 출력에서 단순 Top 5 점 목록으로 제시하지 않는다. 기본 출력은 첨부 예시 이미지처럼 **색상 기반 발진 가능구역 지도**다. 점수 상위 후보점 목록은 디버깅·검증용 보조 출력으로만 둘 수 있다.

## 2. 반드시 읽어야 할 기준 문서

작업 전 아래 문서를 먼저 읽고, 구현 내용이 문서와 충돌하지 않도록 한다.

1. `README.md`
2. `docs/master-plan.md`
3. `docs/research/research-index.md`
4. `docs/agent-build-feasibility.md`
5. `docs/github-app-limit-report.md`
6. `docs/agent-operations-plan.md`

## 3. 개발 범위와 안전 경계

### 3.1 허용 범위

에이전트는 다음 작업을 수행할 수 있다.

- 연구·교육·시뮬레이션용 소프트웨어 구현
- 좌표 변환, 지형 데이터 처리, LOS/Fresnel 계산, 경로탐색, 지도 시각화 구현
- 샘플 또는 synthetic 데이터 기반 테스트 작성
- 문서화, 리팩터링, CI 구성
- GitHub Issue 단위의 기능 구현
- PR 생성 및 테스트 결과 보고

### 3.2 금지 범위

다음 기능은 구현하지 않는다.

- 실제 드론 자동조종, 실시간 비행제어, autopilot 연동
- 특정 실제 작전 수행을 위한 운용 지시 자동 생성
- 감시 회피, 탐지 회피, 공격 지원, 침투 경로 최적화 기능
- 무단 데이터 다운로드, 비공개 데이터 추출, 비인가 API 호출
- API 키, 토큰, 인증정보 저장소 커밋
- 대형 원천 GIS 데이터 직접 커밋

본 프로젝트는 **분석·시뮬레이션·교육용 의사결정 보조 도구**로 유지한다.

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
├── .github/
└── pyproject.toml
```

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
```

## 6. Codex/Claude Code 교대 및 인계 원칙

### 6.1 기본 원칙: Task 경계에서만 교대한다

Codex와 Claude Code는 기본적으로 **Task 경계**에서만 교대한다.

```text
정상 교대 예시:
Codex가 Task 001 완료 → PR 생성 → GPT 검토 → 사용자 승인/merge
→ Claude Code가 Task 002 시작
```

다음 방식은 기본적으로 금지한다.

```text
비권장 방식:
Codex가 Task 004를 절반 구현 → 토큰 소모 → Claude Code가 같은 브랜치에서 즉시 이어쓰기
```

Task 중간 교대는 맥락 손실, 중복 수정, 테스트 누락, 브랜치 충돌 가능성이 높다. 따라서 에이전트 교대는 **완료된 Task, 완료된 PR, 또는 명시적 handoff checkpoint**를 기준으로 한다.

### 6.2 하나의 Task는 하나의 브랜치와 하나의 PR로 관리한다

```text
하나의 Task = 하나의 브랜치 = 하나의 PR
```

예시:

```text
agent/task-001-project-scaffold
agent/task-002-coordinate-core
agent/task-003-terrain-loader
agent/task-004-los-analysis
agent/task-005-fresnel-analysis
agent/task-006-launch-area-map
agent/task-007-route-planner
agent/task-008-waypoints
agent/task-009-streamlit-ui
```

### 6.3 예외: 같은 Task를 다른 에이전트가 이어받아야 하는 경우

다음 상황에서는 같은 Task를 다른 에이전트가 이어받을 수 있다.

1. Codex 또는 Claude Code의 사용량/토큰이 Task 중간에 소진된 경우
2. 로컬 실행 또는 CI 실패가 한 에이전트의 환경에서 해결되지 않는 경우
3. 사용자가 명시적으로 다른 에이전트에게 이어받기를 지시한 경우
4. 기존 에이전트가 draft PR 또는 handoff note를 남긴 경우

단, 같은 Task를 이어받기 전에는 반드시 아래 handoff checkpoint를 남긴다.

### 6.4 Handoff checkpoint 필수 항목

handoff는 GitHub Issue comment, PR comment, 또는 `docs/handoff/` 문서로 남긴다.

```markdown
# Task Handoff

## 현재 Task
Task 00X - 작업명

## 현재 브랜치
agent/task-00X-...

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
- AGL/MSL 혼동 금지
- 대형 GIS 데이터 커밋 금지
- 실제 드론 제어 기능 구현 금지
```

### 6.5 이어받는 에이전트의 의무

이어받는 Codex 또는 Claude Code는 다음을 먼저 수행한다.

1. `git status` 확인
2. 현재 브랜치 확인
3. 기존 PR 또는 handoff checkpoint 확인
4. 변경된 파일 diff 확인
5. 실패한 테스트 재현
6. 기존 구현 의도를 보존하면서 최소 수정

이어받는 에이전트는 기존 작업을 전면 재작성하지 않는다. 재작성이 필요하면 먼저 이유를 PR 또는 Issue에 기록한다.

### 6.6 GPT Master 검토 의무

에이전트 교대가 발생할 때 GPT Master는 다음을 확인한다.

1. Task 범위가 유지되었는가?
2. 같은 파일을 서로 다른 에이전트가 충돌되게 수정하지 않았는가?
3. handoff checkpoint가 충분한가?
4. 테스트 실패 원인이 기록되었는가?
5. 다음 에이전트가 수행할 작업이 명확한가?

## 7. 브랜치 전략

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

예시:

```text
[Task 006] Implement launch feasible area map layer
```

## 8. 코드 품질 기준

- Python 3.11 이상을 기준으로 한다.
- 타입 힌트를 적극 사용한다.
- 좌표, 거리, 고도 단위는 명시한다.
- 함수는 작게 유지하고, 단위 테스트 가능한 구조로 작성한다.
- GIS 원천 데이터가 없어도 synthetic raster 기반 테스트가 동작해야 한다.
- 모든 계산 함수는 입력 단위와 출력 단위를 docstring에 기록한다.
- 테스트 없이 핵심 알고리즘을 추가하지 않는다.

## 9. 데이터 처리 원칙

- 대형 DEM/DSM 원천 파일은 저장소에 커밋하지 않는다.
- 테스트에는 synthetic raster 또는 작은 샘플 파일을 사용한다.
- 실제 데이터 경로는 `.env`, 로컬 설정 파일, 또는 사용자 입력으로 처리한다.
- 좌표계는 반드시 명시한다.
- MGRS → WGS84 → 투영좌표계 변환 흐름을 문서화한다.

## 10. 알고리즘 기준

### 10.1 발진 가능구역 점수

기본 점수식은 `docs/master-plan.md`를 따른다. 이 점수는 사용자에게 점 목록을 우선 제시하기 위한 것이 아니라, 지도 평면의 격자/셀을 색상 등급으로 분류하기 위한 내부 점수다.

```text
발진 가능구역 종합점수 = 차폐안정성 점수 × 0.80 + 거리점수 × 0.20
차폐안정성 점수 = LOS 점수 × 0.50 + Fresnel 여유 점수 × 0.35 + DSM 장애물 점수 × 0.15
거리점수 = 100 × (1 - 목표까지 3D 거리 / 드론 운용반경)
```

색상 등급 기본안:

```text
녹색: 추천 가능구역
노란색: 제한적 가능구역
주황색/적색: 비추천 또는 차폐위험구역
회색/투명: 운용반경 초과 또는 계산 제외구역
```

### 10.2 경로 후보

사용자가 지도상에서 발진기지를 선택한 뒤 반드시 3개 경로 후보를 생성한다.

1. 차폐 최소 경로
2. 거리-차폐 균형 경로
3. 우회 안정 경로

각 경로에는 실 비행거리, 평균 차폐점수, 최저 차폐점수, 약 500m 단위 경유점이 포함되어야 한다.

## 11. PR 완료 조건

PR에는 다음을 포함한다.

- 작업 요약
- 구현한 파일 목록
- 테스트 결과
- 남은 한계
- 사용자가 검토해야 할 사항
- 에이전트 교대 여부 및 handoff 여부

PR은 테스트가 통과해야 하며, `main` 병합은 사용자가 승인할 때만 수행한다.

## 12. 에이전트 응답 형식

작업 완료 보고는 아래 형식을 사용한다.

```markdown
## 작업 요약

## 변경 파일

## 테스트 결과

## 구현 한계

## 에이전트 교대 여부

## 다음 권장 작업
```
