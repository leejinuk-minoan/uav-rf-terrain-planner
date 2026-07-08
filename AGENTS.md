# AGENTS.md

본 문서는 Codex, Claude Code, 기타 GitHub 연동 AI 에이전트가 `uav-rf-terrain-planner` 저장소에서 작업할 때 따라야 할 공통 작업 규칙이다.

## 1. 프로젝트 목적

이 저장소는 연구·교육·시뮬레이션용 **드론 주파수 차폐 기반 발진기지 및 경로추천 프로그램**을 개발하기 위한 저장소다.

프로그램의 기본 목적은 다음과 같다.

```text
정찰목표지점 MGRS + 드론 운용반경 + 허가 운용고도 AGL + 통신 주파수 대역
→ DEM/DSM 기반 지형 단면 분석
→ LOS/Fresnel 기반 주파수·지형 차폐 위험 점수화
→ 발진기지 후보 Top 5 추천
→ 차폐 위험이 낮은 경로 후보 3개 제시
→ 약 500m 단위 경유점과 실 비행거리 출력
```

## 2. 반드시 읽어야 할 기준 문서

작업 전 아래 문서를 먼저 읽고, 구현 내용이 문서와 충돌하지 않도록 한다.

1. `README.md`
2. `docs/master-plan.md`
3. `docs/research/research-index.md`
4. `docs/agent-build-feasibility.md`
5. `docs/github-app-limit-report.md`

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
Task 008: 발진기지 후보 생성 및 Top 5 추천
Task 009: 경로탐색 기반 경로 후보 3개 생성
Task 010: 500m 단위 경유점 및 실 비행거리 계산
Task 011: Streamlit/Folium 기반 MVP UI
Task 012: 통합 테스트, 문서화, 샘플 실행 시나리오
```

## 6. 브랜치 전략

각 기능은 별도 브랜치에서 작업한다.

```text
main
├── agent/task-001-project-scaffold
├── agent/task-002-coordinate-core
├── agent/task-003-terrain-loader
├── agent/task-004-los-fresnel
├── agent/task-005-launch-recommendation
├── agent/task-006-route-planner
└── agent/task-007-streamlit-ui
```

PR 제목 형식:

```text
[Task 00X] 작업명
```

예시:

```text
[Task 004] Implement LOS terrain profile analysis
```

## 7. 코드 품질 기준

- Python 3.11 이상을 기준으로 한다.
- 타입 힌트를 적극 사용한다.
- 좌표, 거리, 고도 단위는 명시한다.
- 함수는 작게 유지하고, 단위 테스트 가능한 구조로 작성한다.
- GIS 원천 데이터가 없어도 synthetic raster 기반 테스트가 동작해야 한다.
- 모든 계산 함수는 입력 단위와 출력 단위를 docstring에 기록한다.
- 테스트 없이 핵심 알고리즘을 추가하지 않는다.

## 8. 데이터 처리 원칙

- 대형 DEM/DSM 원천 파일은 저장소에 커밋하지 않는다.
- 테스트에는 synthetic raster 또는 작은 샘플 파일을 사용한다.
- 실제 데이터 경로는 `.env`, 로컬 설정 파일, 또는 사용자 입력으로 처리한다.
- 좌표계는 반드시 명시한다.
- MGRS → WGS84 → 투영좌표계 변환 흐름을 문서화한다.

## 9. 알고리즘 기준

### 9.1 발진기지 점수

기본 점수식은 `docs/master-plan.md`를 따른다.

```text
발진기지 종합점수 = 차폐안정성 점수 × 0.80 + 거리점수 × 0.20
차폐안정성 점수 = LOS 점수 × 0.50 + Fresnel 여유 점수 × 0.35 + DSM 장애물 점수 × 0.15
거리점수 = 100 × (1 - 목표까지 3D 거리 / 드론 운용반경)
```

### 9.2 경로 후보

반드시 3개 후보를 생성한다.

1. 차폐 최소 경로
2. 거리-차폐 균형 경로
3. 우회 안정 경로

각 경로에는 실 비행거리, 평균 차폐점수, 최저 차폐점수, 약 500m 단위 경유점이 포함되어야 한다.

## 10. PR 완료 조건

PR에는 다음을 포함한다.

- 작업 요약
- 구현한 파일 목록
- 테스트 결과
- 남은 한계
- 사용자가 검토해야 할 사항

PR은 테스트가 통과해야 하며, `main` 병합은 사용자가 승인할 때만 수행한다.

## 11. 에이전트 응답 형식

작업 완료 보고는 아래 형식을 사용한다.

```markdown
## 작업 요약

## 변경 파일

## 테스트 결과

## 구현 한계

## 다음 권장 작업
```
