# Codex 작업 프롬프트 모음

이 문서는 GitHub 연동 Codex에 기능 단위 구현을 지시하기 위한 프롬프트 모음이다. 각 프롬프트는 GitHub Issue 또는 Codex 작업 입력에 그대로 사용할 수 있도록 작성했다.

## 공통 Codex 지시문

```text
저장소: leejinuk-minoan/uav-rf-terrain-planner

작업 전 AGENTS.md, README.md, docs/master-plan.md, docs/research/research-index.md, docs/agent-build-feasibility.md, docs/agent-operations-plan.md를 반드시 읽어라.

본 프로젝트는 연구·교육·시뮬레이션용 지형·전파 차폐 분석 도구다. 실제 드론 자동조종, 실시간 비행제어, 탐지 회피, 공격 지원 기능은 구현하지 말라. 대형 GIS 원천 데이터는 커밋하지 말고, 테스트에는 synthetic 데이터를 사용하라.

중요: 발진기지 기본 출력은 Top 5 점 목록이 아니다. 지도 평면에 드론 최대 운용거리와 차폐위험을 고려한 발진 가능구역을 색상 레이어로 표시하는 것이 기본 출력이다. 점수 상위 후보점 목록은 디버깅·검증용 보조 출력으로만 허용된다.

기능 단위로 구현하고, 반드시 테스트를 추가하라. PR 설명에는 목적, 구현 내용, 테스트 결과, 한계, 다음 작업을 적어라.
```

---

## Task 001 - 프로젝트 스캐폴딩

```text
공통 Codex 지시문을 따른다.

목표:
Python 패키지 기본 구조를 생성하라.

구현 범위:
1. pyproject.toml 생성
2. src/uav_rf_terrain/ 패키지 생성
3. tests/ 디렉터리 생성
4. examples/ 디렉터리 생성
5. 기본 __init__.py 작성
6. 최소 smoke test 작성

권장 패키지:
- numpy
- pandas
- pyproj
- mgrs
- rasterio
- shapely
- geopandas
- networkx
- pydantic
- streamlit
- folium
- pytest
- ruff
- mypy

주의:
rasterio/GDAL 설치가 CI에서 실패할 가능성이 있으면 optional dependency로 분리하거나 import fallback을 설계하라.

완료 조건:
- python -m pytest 통과
- python -m compileall src tests 통과
- README에 로컬 실행 방법 간단 추가
```

---

## Task 002 - 좌표 변환 모듈

```text
공통 Codex 지시문을 따른다.

목표:
MGRS, WGS84, 투영좌표계 변환 모듈을 구현하라.

구현 파일 제안:
- src/uav_rf_terrain/coordinates.py
- tests/test_coordinates.py

기능:
1. MGRS 문자열을 위도/경도로 변환
2. 위도/경도를 MGRS로 변환
3. 위도/경도를 지정 EPSG 투영좌표계로 변환
4. 투영좌표계 좌표를 위도/경도로 변환
5. 거리 계산용 좌표계 선택을 설정값으로 받을 수 있게 설계

주의:
- 단위는 명확히 기록하라.
- 좌표계 변환 실패 시 명확한 예외를 발생시켜라.
- 실제 군사 좌표 예시는 넣지 말고 synthetic 또는 공개 예시 좌표를 사용하라.

완료 조건:
- 단위 테스트 포함
- docstring 포함
```

---

## Task 003 - synthetic DEM/DSM 및 래스터 샘플링

```text
공통 Codex 지시문을 따른다.

목표:
실제 GIS 데이터 없이도 테스트 가능한 synthetic terrain generator와 래스터 샘플링 인터페이스를 구현하라.

구현 파일 제안:
- src/uav_rf_terrain/terrain.py
- examples/synthetic_terrain.py
- tests/test_terrain.py

기능:
1. 평탄 지형 synthetic DEM 생성
2. 중간 능선이 있는 synthetic DEM 생성
3. DSM 장애물 레이어 synthetic 생성
4. 좌표점에서 고도 샘플링
5. 경로 선분을 일정 간격으로 샘플링

주의:
- 실제 DEM/DSM 파일이 없어도 테스트가 동작해야 한다.
- rasterio가 없을 때도 numpy 배열 기반 테스트는 통과해야 한다.

완료 조건:
- 평탄 지형 샘플링 테스트
- 능선 지형 샘플링 테스트
- DSM 장애물 샘플링 테스트
```

---

## Task 004 - 지형 단면 및 LOS 분석

```text
공통 Codex 지시문을 따른다.

목표:
발진 가능구역의 각 후보 셀과 목표점 또는 경로점 사이의 지형 단면을 추출하고 LOS 차단 여부를 계산하라.

구현 파일 제안:
- src/uav_rf_terrain/profile.py
- src/uav_rf_terrain/shielding.py
- tests/test_los.py

기능:
1. 두 점 사이를 일정 간격으로 샘플링
2. 각 샘플점의 DEM/DSM 높이 조회
3. 송신점/수신점 고도 기준 통신선 높이 계산
4. 중간 장애물이 통신선을 초과하는지 판단
5. LOS 점수 산출

주의:
- AGL과 MSL을 혼동하지 말라.
- 발진기지 조종기 높이는 지면 기준 0m로 둔다.
- 드론 고도는 해당 경로점 지형고도 + 사용자 입력 AGL이다.

완료 조건:
- 평탄 지형에서는 LOS 확보
- 중간 능선 지형에서는 LOS 차단
- 결과 객체에 차단 위치와 최소 여유고도 포함
```

---

## Task 005 - Fresnel Zone 분석

```text
공통 Codex 지시문을 따른다.

목표:
사용자가 입력한 통신 주파수 대역을 이용하여 Fresnel Zone 반경과 침범률을 계산하라.

구현 파일 제안:
- src/uav_rf_terrain/fresnel.py
- tests/test_fresnel.py

기능:
1. 주파수 MHz/GHz 입력 처리
2. 제1 Fresnel Zone 반경 계산
3. 샘플점별 Fresnel 여유고도 계산
4. 침범률 계산
5. Fresnel 여유 점수 산출

주의:
- 단위 변환을 명확히 하라.
- 주파수가 낮을수록 Fresnel 반경이 커져야 한다.
- 수식은 docstring과 테스트에 설명하라.

완료 조건:
- 2.4GHz와 5.8GHz 비교 테스트
- 침범률 0%, 부분 침범, 완전 침범 케이스 테스트
```

---

## Task 006 - 발진 가능구역 색상 지도화

```text
공통 Codex 지시문을 따른다.

목표:
목표지점 주변 평면 격자를 생성하고, 각 격자 셀을 드론 최대 운용거리와 차폐위험 기준으로 평가하여 발진 가능구역 색상 레이어를 생성하라. Top 5 점 목록 추천이 아니라, 지도에 표시할 색상 등급 raster/vector layer를 만드는 것이 핵심이다.

구현 파일 제안:
- src/uav_rf_terrain/launch_sites.py
- src/uav_rf_terrain/schemas.py
- tests/test_launch_sites.py

기능:
1. 목표점 주변 분석범위 생성
2. 분석범위 격자 생성
3. 셀별 중심점 좌표 계산
4. 셀별 3D 거리 계산
5. 운용반경 초과 셀 제외 처리
6. LOS/Fresnel/DSM 차폐안정성 점수 계산
7. 거리점수 계산
8. 종합점수 산출
9. 종합점수와 운용반경 조건에 따라 색상 등급 부여
10. 지도 시각화 모듈이 사용할 수 있는 launch area layer 데이터 반환

점수식:
발진 가능구역 종합점수 = 차폐안정성 점수 × 0.80 + 거리점수 × 0.20
차폐안정성 점수 = LOS 점수 × 0.50 + Fresnel 여유 점수 × 0.35 + DSM 장애물 점수 × 0.15

색상 등급 기본안:
- green: 추천 가능구역
- yellow: 제한적 가능구역
- orange/red: 비추천 또는 차폐위험구역
- excluded: 운용반경 초과 또는 계산 제외구역

완료 조건:
- synthetic terrain에서 색상 등급별 셀 분류 테스트
- 운용반경 초과 셀 제외 테스트
- 결과에 거리점수, 차폐점수, 종합점수, color_class 포함
- Top 5 목록이 기본 출력이 아님을 README 또는 docstring에 명시
```

---

## Task 007 - 경로 후보 3개 및 500m 경유점

```text
공통 Codex 지시문을 따른다.

목표:
사용자가 지도상 발진 가능구역에서 선택한 발진기지로부터 목표지점까지 차폐 위험이 낮은 경로 후보 3개를 생성하고, 각 경로의 실 비행거리와 약 500m 단위 경유점을 산출하라.

구현 파일 제안:
- src/uav_rf_terrain/route_planner.py
- src/uav_rf_terrain/waypoints.py
- tests/test_route_planner.py
- tests/test_waypoints.py

경로 후보:
1. 차폐 최소 경로
2. 거리-차폐 균형 경로
3. 우회 안정 경로

기능:
1. 격자 그래프 생성
2. 운용반경 초과 격자 제외
3. 격자별 차폐위험 비용 부여
4. A* 또는 Dijkstra 경로탐색
5. 후보별 가중치 다르게 적용
6. 중복 경로 방지를 위한 페널티 적용
7. 각 경로 실 비행거리 계산
8. 약 500m 단위 경유점 생성
9. 경유점별 MGRS, 누적거리, AGL, MSL, 발진기지 기준 고도차 계산

완료 조건:
- synthetic grid에서 3개 경로 후보 생성
- 경로별 실 비행거리 출력
- 약 500m 간격 경유점 생성 테스트
```

---

## Task 008 - Streamlit/Folium MVP UI

```text
공통 Codex 지시문을 따른다.

목표:
분석 결과를 사용자가 확인할 수 있는 MVP UI를 구현하라.

구현 파일 제안:
- app/streamlit_app.py
- src/uav_rf_terrain/visualization.py
- tests/test_smoke_app.py

UI 입력:
1. 정찰목표지점 MGRS
2. 드론 운용반경 m 또는 km
3. 허가 운용고도 AGL m 또는 ft
4. 통신 주파수 대역 MHz 또는 GHz
5. synthetic terrain 또는 샘플 데이터 선택

UI 출력:
1. 발진 가능구역 색상 지도 레이어
2. 차폐위험 지도 레이어
3. 사용자가 선택한 발진기지 표시
4. 선택 발진기지 기준 경로 후보 3개
5. 경로별 실 비행거리
6. 500m 단위 경유점 표

주의:
- UI 문구는 ‘추천 가능구역’, ‘제한적 가능구역’, ‘예상 차폐위험’, ‘분석 기준’으로 표현하라.
- ‘발진기지 Top 5 추천’이 기본 UI가 되면 안 된다.
- 실제 운용 확정 표현을 쓰지 말라.

완료 조건:
- streamlit 실행 방법 README 추가
- synthetic 데이터로 데모 가능
- 지도에 색상 기반 발진 가능구역 표시
```
