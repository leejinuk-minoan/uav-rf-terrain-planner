# Claude Code 작업 프롬프트 모음

이 문서는 Claude Code에 기능 단위 작업을 지시하기 위한 프롬프트 모음이다. Claude Code는 로컬 또는 GitHub 연동 환경에서 저장소를 읽고 수정할 수 있으므로, 작업 범위를 명확히 제한해야 한다.

## 공통 Claude Code 지시문

```text
저장소: leejinuk-minoan/uav-rf-terrain-planner

먼저 AGENTS.md와 CLAUDE.md를 읽어라. 그 다음 README.md, docs/master-plan.md, docs/research/research-index.md, docs/agent-build-feasibility.md, docs/agent-operations-plan.md를 읽고 작업하라.

본 프로젝트는 연구·교육·시뮬레이션용 지형·전파 차폐 분석 도구다. 실제 드론 자동조종, 실시간 비행제어, 탐지 회피, 공격 지원 기능은 구현하지 말라. 대형 GIS 원천 데이터는 커밋하지 말고, 테스트에는 synthetic 데이터를 사용하라.

중요: 발진기지 기본 출력은 Top 5 점 목록이 아니다. 지도 평면에 드론 최대 운용거리와 차폐위험을 고려한 발진 가능구역을 색상 레이어로 표시하는 것이 기본 출력이다. 점수 상위 후보점 목록은 디버깅·검증용 보조 출력으로만 허용된다.

작업은 현재 이슈 또는 지정된 Task 범위에 한정하라. 작업 전 git status를 확인하고, 작업 후 테스트를 실행하라. PR 설명에는 목적, 구현 내용, 테스트 결과, 한계 및 다음 작업을 정리하라.
```

---

## Claude Code 초기 세션 프롬프트

```text
이 저장소를 분석하고 개발 준비 상태를 점검하라.

수행할 것:
1. AGENTS.md와 CLAUDE.md를 읽는다.
2. docs/master-plan.md와 docs/research/research-index.md를 읽는다.
3. 현재 저장소 구조를 요약한다.
4. 아직 구현되지 않은 핵심 모듈을 식별한다.
5. Task 001부터 순차적으로 구현 가능한 계획을 제안한다.
6. 발진기지 출력이 Top 5가 아니라 색상 기반 발진 가능구역 지도인지 확인한다.

하지 말 것:
- 코드를 수정하지 말 것.
- 외부 데이터를 다운로드하지 말 것.
- 실제 드론 제어 기능을 제안하지 말 것.

출력 형식:
## 저장소 상태
## 기준 문서 요약
## 구현 공백
## 발진 가능구역 지도화 기준 확인
## 권장 작업 순서
## 사용자 승인 필요사항
```

---

## Task 001 - 프로젝트 스캐폴딩

```text
공통 Claude Code 지시문을 따른다.

브랜치:
agent/task-001-project-scaffold

목표:
Python 기반 패키지 개발이 가능한 최소 프로젝트 구조를 만든다.

구현:
1. pyproject.toml 생성
2. src/uav_rf_terrain/ 패키지 생성
3. tests/ 디렉터리 생성
4. examples/ 디렉터리 생성
5. 기본 smoke test 작성
6. README에 설치 및 테스트 실행 방법 추가

주의:
- 실제 지형 데이터는 추가하지 말라.
- rasterio/GDAL 설치 문제가 발생할 수 있으므로 optional dependency를 고려하라.

검증:
python -m pytest
python -m compileall src tests
```

---

## Task 002 - 좌표 변환 모듈

```text
공통 Claude Code 지시문을 따른다.

브랜치:
agent/task-002-coordinate-core

목표:
MGRS/WGS84/투영좌표계 변환 모듈을 구현한다.

구현:
1. src/uav_rf_terrain/coordinates.py 작성
2. MGRS → 위도/경도
3. 위도/경도 → MGRS
4. WGS84 → 지정 EPSG 투영좌표계
5. 투영좌표계 → WGS84
6. 좌표 변환 실패 예외 처리
7. tests/test_coordinates.py 작성

주의:
- 테스트에는 공개 또는 synthetic 좌표만 사용한다.
- 단위와 좌표계 이름을 docstring에 명시한다.

검증:
python -m pytest tests/test_coordinates.py
```

---

## Task 003 - synthetic 지형 및 래스터 인터페이스

```text
공통 Claude Code 지시문을 따른다.

브랜치:
agent/task-003-terrain-loader

목표:
실제 DEM/DSM이 없어도 테스트 가능한 synthetic terrain과 래스터 샘플링 인터페이스를 구현한다.

구현:
1. src/uav_rf_terrain/terrain.py 작성
2. TerrainGrid 또는 유사 데이터 클래스 작성
3. 평탄 지형 생성 함수
4. 중간 능선 지형 생성 함수
5. DSM 장애물 추가 함수
6. 좌표별 고도 샘플링
7. 선분 샘플링
8. tests/test_terrain.py 작성

주의:
- rasterio가 없어도 numpy 기반 테스트가 통과해야 한다.
- 실제 대형 지형자료를 커밋하지 않는다.

검증:
python -m pytest tests/test_terrain.py
```

---

## Task 004 - LOS 분석

```text
공통 Claude Code 지시문을 따른다.

브랜치:
agent/task-004-los-analysis

목표:
발진 가능구역의 각 후보 셀과 목표/경로점 사이의 직접 가시선 차폐 여부를 분석한다.

구현:
1. src/uav_rf_terrain/profile.py 작성
2. src/uav_rf_terrain/shielding.py 작성 또는 확장
3. 두 점 사이 지형 단면 샘플링
4. 통신선 높이 계산
5. 장애물 높이와 통신선 비교
6. LOS 확보/차단 판정
7. 최소 여유고도, 차단 지점, LOS 점수 반환
8. tests/test_los.py 작성

중요 가정:
- 발진기지 안테나 높이: 지면 0m
- 드론 고도: 해당 지점 지형고도 + 사용자 입력 AGL

검증:
python -m pytest tests/test_los.py
```

---

## Task 005 - Fresnel 분석

```text
공통 Claude Code 지시문을 따른다.

브랜치:
agent/task-005-fresnel-analysis

목표:
주파수 대역을 입력받아 Fresnel Zone 반경과 침범률을 계산한다.

구현:
1. src/uav_rf_terrain/fresnel.py 작성
2. MHz/GHz 입력 파싱
3. 제1 Fresnel Zone 반경 계산
4. 지형 단면 샘플별 Fresnel 여유고도 계산
5. 침범률 산출
6. Fresnel 여유 점수 산출
7. tests/test_fresnel.py 작성

검증 포인트:
- 2.4GHz보다 5.8GHz의 Fresnel 반경이 작아야 한다.
- 장애물 높이가 증가하면 침범률이 증가해야 한다.
- 침범률이 높을수록 점수가 낮아져야 한다.

검증:
python -m pytest tests/test_fresnel.py
```

---

## Task 006 - 발진 가능구역 색상 지도화

```text
공통 Claude Code 지시문을 따른다.

브랜치:
agent/task-006-launch-area-map

목표:
목표 주변 후보 격자를 생성하고, 드론 최대 운용거리와 차폐위험 기준으로 각 셀을 평가하여 발진 가능구역 색상 레이어를 만든다. 발진기지 Top 5 표가 아니라 지도에 표시할 색상 기반 가능구역을 만드는 것이 핵심이다.

구현:
1. src/uav_rf_terrain/launch_sites.py 작성
2. src/uav_rf_terrain/schemas.py 작성
3. 목표 주변 분석범위 생성
4. 분석범위 격자 생성
5. 후보 셀 중심점 좌표 계산
6. 운용반경 기반 3D 거리 필터링
7. LOS/Fresnel/DSM 점수 결합
8. 거리점수 계산
9. 종합점수 계산
10. color_class 부여
11. 지도 시각화에 사용할 launch area layer 반환
12. tests/test_launch_sites.py 작성

점수식:
발진 가능구역 종합점수 = 차폐안정성 점수 × 0.80 + 거리점수 × 0.20
차폐안정성 점수 = LOS 점수 × 0.50 + Fresnel 여유 점수 × 0.35 + DSM 장애물 점수 × 0.15

색상 등급 기본안:
- green: 추천 가능구역
- yellow: 제한적 가능구역
- orange/red: 비추천 또는 차폐위험구역
- excluded: 운용반경 초과 또는 계산 제외구역

검증:
python -m pytest tests/test_launch_sites.py
```

---

## Task 007 - 경로 후보 3개 생성

```text
공통 Claude Code 지시문을 따른다.

브랜치:
agent/task-007-route-planner

목표:
사용자가 지도상 발진 가능구역에서 선택한 발진기지에서 목표지점까지 차폐 위험을 고려한 경로 후보 3개를 생성한다.

구현:
1. src/uav_rf_terrain/route_planner.py 작성
2. 격자 그래프 생성
3. 운용반경 초과 격자 제외
4. 차폐위험 비용과 거리 비용 부여
5. A* 또는 Dijkstra 경로탐색 구현
6. 차폐 최소, 균형, 우회 안정 3개 후보 생성
7. 중복 경로 방지 페널티 구현
8. tests/test_route_planner.py 작성

경로 후보:
- 1안: 차폐 최소
- 2안: 거리-차폐 균형
- 3안: 우회 안정

검증:
python -m pytest tests/test_route_planner.py
```

---

## Task 008 - 500m 경유점 및 실 비행거리

```text
공통 Claude Code 지시문을 따른다.

브랜치:
agent/task-008-waypoints

목표:
경로별 실 비행거리와 약 500m 단위 경유점을 산출한다.

구현:
1. src/uav_rf_terrain/waypoints.py 작성
2. 경로 구간별 3D 거리 계산
3. 총 실 비행거리 계산
4. 약 500m 단위 경유점 보간
5. 경유점별 누적거리 계산
6. 경유점별 MGRS 변환
7. 경유점별 AGL, MSL, 발진기지 기준 고도차 계산
8. tests/test_waypoints.py 작성

검증:
- 1.6km 경로에서 0m, 500m, 1000m, 1500m, 종점이 생성되는지 확인
- 고도차가 MSL 기준으로 계산되는지 확인

검증 명령:
python -m pytest tests/test_waypoints.py
```

---

## Task 009 - MVP UI

```text
공통 Claude Code 지시문을 따른다.

브랜치:
agent/task-009-streamlit-ui

목표:
Streamlit/Folium 기반 MVP UI를 구현한다.

구현:
1. app/streamlit_app.py 작성
2. 입력 폼 구현
3. synthetic terrain 선택 기능
4. 발진 가능구역 색상 지도 레이어 출력
5. 사용자가 지도상에서 발진기지 선택 또는 선택값 입력
6. 경로 후보 3개 표 출력
7. 500m 경유점 표 출력
8. README에 실행 방법 추가

UI 문구:
- “추천 가능구역”
- “제한적 가능구역”
- “예상 차폐위험”
- “분석 기준”
- “시뮬레이션 결과”

금지 문구:
- “발진기지 Top 5 추천”을 기본 UI로 표시
- “실제 운용 최적 경로 확정”
- “통신 보장”
- “작전 성공 보장”

검증:
streamlit run app/streamlit_app.py
python -m pytest
```

---

## Claude Code PR 완료 보고 템플릿

```markdown
## 작업 완료

### 요약

### 변경 파일

### 실행한 명령

### 테스트 결과

### 구현 한계

### 사용자 검토 필요사항

### 다음 권장 작업
```
