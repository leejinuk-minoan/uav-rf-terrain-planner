# UAV RF Terrain Planner

연구·교육·시뮬레이션용 **드론 주파수 차폐 기반 발진기지 및 경로추천 프로그램**입니다.

## 목적

정찰목표지점 MGRS, 드론 운용반경, 허가 운용고도 AGL, 통신 주파수 대역을 입력받아 DEM/DSM 기반 지형 단면과 LOS/Fresnel Zone 차폐 위험을 분석하고, **지도 평면상에서 드론 최대 운용거리를 고려한 발진 가능구역을 색상 레이어로 표시**합니다. 사용자가 지도에서 발진기지를 선택하면 해당 지점부터 목표지점까지 차폐 위험이 낮은 비행경로 후보 3개를 제시합니다.

## 핵심 기능

1. MGRS 좌표 입력 및 분석용 좌표계 변환
2. DEM/DSM 기반 지형 단면 분석
3. LOS 및 Fresnel Zone 기반 차폐위험 점수화
4. 드론 최대 운용거리와 차폐위험을 고려한 **발진 가능구역 색상 지도화**
5. 사용자가 지도상에서 발진기지 선택
6. 차폐 최소 / 거리-차폐 균형 / 우회 안정 경로 3개 제시
7. 경로별 실 비행거리 산정
8. 약 500m 단위 경유점 생성 및 AGL 고도·발진기지 기준 고도차 표기

## 발진기지 표시 기준

발진기지는 단순히 Top 5 점 목록으로 제시하지 않는다. 첨부 예시 이미지처럼 분석 평면을 격자화하고 각 격자점을 평가하여 다음과 같은 색상 구역으로 표시한다.

- 추천 가능구역: 운용거리 조건을 만족하고 차폐위험이 낮은 지역
- 제한적 가능구역: 운용거리 조건은 만족하지만 차폐위험이 보통인 지역
- 비추천/위험구역: 차폐위험이 높거나 운용거리 조건에 근접한 지역
- 제외구역: 드론 운용반경을 초과하거나 계산상 도달 불가능한 지역

점수 상위 지점 목록은 디버깅·검증용 보조 출력으로 둘 수 있지만, 사용자 기본 출력은 **색상 기반 발진 가능구역 지도**다.

## Task 001 기준 점수식

Task 001에서는 실제 LOS/Fresnel 알고리즘을 완성하지 않고, 이후 구현을 위한 config와 schema 기준만 고정한다.

```text
overall_score = shielding_stability_score × 0.80 + distance_score × 0.20

shielding_stability_score = dsm_los_score × 0.40
                          + dsm_fresnel_score × 0.60

distance_score = 100 × (1 - distance_3d_m / operating_radius_m)
```

운용반경을 초과하는 후보는 제외한다. 기본 LOS cap 규칙은 다음과 같다.

```text
if dsm_los_score == 0:
    shielding_stability_score = 0
```

이 점수는 실제 통신 성공률, 실제 링크품질, RSSI, SINR, packet loss 검증값이 아니다. 본 프로젝트의 MVP 점수는 **offline terrain/surface-obstacle risk proxy**로만 사용한다.

## Task 002 좌표 및 후보 격자 scaffold

Task 002는 local coordinate and candidate-grid scaffolding을 추가한다. `coordinates.py`는 `WGS84Point`, `LocalPoint`, `CoordinateReference`와 2D/3D 거리 helper를 제공하고, `grid.py`는 목표 주변 후보 발진지 candidate cell 격자를 생성한다.

MGRS/pyproj 기반 변환은 optional GIS dependencies와 로컬 검증이 필요하다. 기본 dev 환경과 CI가 무거운 GIS 의존성 때문에 깨지지 않도록 MGRS 변환은 optional runtime import 구조로 둔다.

Candidate grid는 색상 기반 발진 가능구역 지도 생성을 위한 grid/cell 구조이며, Top 5 발진지 기본 출력 구조가 아니다. 실제 DEM/DSM loading, DSM-based LOS/Fresnel computation, final scoring, and map rendering remain future tasks.

## Task 003 synthetic DEM/DSM terrain generator

Task 003 adds pure Python synthetic DEM/DSM terrain generators. Synthetic terrain is for algorithm boundary-condition testing only.

The generator creates small in-memory DEM/DSM grids for scenarios such as flat terrain, single ridge, building obstacle, tree canopy, obstacle-position variation, operating-radius boundary, fixed-AGL case, and Fresnel-position variation.

No real DEM/DSM files are loaded. No GeoTIFF, rasterio, GDAL, geopandas, QGIS, or map-rendering integration is included. LOS/Fresnel/scoring/map rendering remain future tasks.

## DSM/DEM 기준

- LOS 판정 기본 기준면: DSM
- Fresnel 침범률 기본 기준면: DSM
- DEM 역할: DSM fallback, AGL 기준 지형고도, DSM-DEM 차이 참고, DEM-only vs DSM-primary 비교
- 사용자 입력 AGL은 단일 고정 운용고도로 해석한다.

표면장애물 복잡도 보정점수는 기본 점수식에서 제외한다. DSM 기반 LOS와 DSM 기반 Fresnel이 표면장애물 영향을 이미 반영하므로, 별도 복잡도 점수는 중복 감점 위험이 있다.

## 설치 및 테스트 초안

Task 001은 프로젝트 스캐폴딩 단계다. 로컬 또는 CI에서 다음 명령으로 확인한다.

```bash
python -m pip install -e '.[dev]'
python -m pytest
python -m compileall src tests examples
```

Cloud Execution Agent는 로컬 명령을 직접 실행하지 않는다. 실제 실행 결과는 GitHub Actions, Codex, 또는 Claude Code의 로컬 검증 결과로 분리해 기록한다.

## 문서 구조

- `docs/master-plan.md`: 전체 마스터 플랜
- `docs/research/research-index.md`: 선행연구 자료집 및 모델 반영안
- `docs/agent-operations-plan.md`: Codex/Claude Code 교대 운영 플랜
- `docs/github-app-limit-report.md`: GitHub 앱 작업 가능 범위 점검 보고
- `docs/paper/score-model-validation-plan.md`: 실제 드론운용 없는 오프라인 점수식 검증 계획

## 개발 원칙

본 프로젝트는 실제 현장 운용 지시서가 아니라 연구·교육·시뮬레이션 및 의사결정 보조 목적의 정량 분석 도구로 개발합니다.

금지 범위:

- 실제 드론 제어
- 실시간 조종 또는 자동 비행 제어
- 침투·회피·공격 경로 제공
- 실제 통신 성공률 또는 링크품질 보장 표현
- RSSI/SINR/packet loss를 필수 입력으로 요구하는 MVP schema
- 대형 GIS 원천 데이터 저장소 커밋
