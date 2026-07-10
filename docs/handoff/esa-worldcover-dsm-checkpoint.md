# ESA WorldCover 기반 임시 DSM 처리 체크포인트

## 현재 Task

실제 DEM 도엽과 ESA WorldCover 10m 2021 v200을 결합한 남한 임시 DSM 구축

## 담당했던 에이전트

Codex

## 작업한 내용

- ESA WorldCover 원천 GeoTIFF를 225개 DEM 도엽의 범위와 90m 격자에 최근접 이웃 방식으로 정렬했다.
- WorldCover 클래스 코드가 보존된 토지피복 래스터를 도엽별로 생성했다.
- 클래스별 휴리스틱 표면 높이와 `DEM MSL + 표면 높이` 임시 DSM을 생성했다.
- 도엽별 결과를 EPSG:5179 남한 전체 모자이크로 병합했다.
- 권위 코드가 빠진 5개 DEM 도엽은 동일한 Unified CS 매개변수를 확인하고 EPSG:5179로 정규화했다.

## 입력 데이터

- DEM: `METADATA_MAP/DEM_EXTRACTED_LATEST`의 225개 IMG 도엽
- 토지피복: `C:/Users/USER/Desktop/지형분석 데이터/ESA_WorldCover_10m_2021_v200_60deg_macrotile_N30E120`
- 토지피복 원본: EPSG:4326, 10m, ESA WorldCover 2021 v200, CC BY 4.0

## 표면 높이 가정

| WorldCover 코드 | 클래스 | 가정 높이(m) |
|---:|---|---:|
| 10 | 수목 | 14.0 |
| 20 | 관목 | 2.0 |
| 30 | 초지 | 1.0 |
| 40 | 농경지 | 0.5 |
| 50 | 시가지 | 8.0 |
| 60 | 나지/희박 식생 | 0.0 |
| 70 | 눈/얼음 | 0.0 |
| 80 | 영구 수역 | 0.0 |
| 90 | 초본 습지 | 0.5 |
| 95 | 맹그로브 | 4.0 |
| 100 | 이끼/지의류 | 0.2 |

## 주요 산출물

- `METADATA_MAP/DSM_PROXY_FROM_ESA_WORLDCOVER/south_korea_landcover_90m_epsg5179.tif`
- `METADATA_MAP/DSM_PROXY_FROM_ESA_WORLDCOVER/south_korea_surface_delta_proxy_90m_epsg5179.tif`
- `METADATA_MAP/DSM_PROXY_FROM_ESA_WORLDCOVER/south_korea_temporary_dsm_proxy_90m_epsg5179.tif`
- `METADATA_MAP/DSM_PROXY_FROM_ESA_WORLDCOVER/processing_manifest.csv`
- 도엽별 결과: `landcover_tiles`, `surface_delta_tiles`, `dsm_tiles` 각 225개

## 검증 결과

- CRS: EPSG:5179
- 픽셀 크기: 90m x 90m
- 크기: 4057 x 5865
- 경계: 838710, 1555740, 1203840, 2083590
- 임시 DSM 유효 비율: 73.09%
- 표면 높이 범위: 0~14m
- 임시 DSM 범위: 약 -88.70~1899.46m MSL
- 처리 스크립트 문법 검사 통과

## 현재 테스트 상태

- 통과: 단일 도엽 처리, 225개 도엽 처리, CRS/격자/경계 일치, 전국 모자이크, manifest 225행, Python 문법 검사
- 미실행: QGIS 육안 중첩 검사, 실제 건물고·수고 데이터와의 정확도 검증

## 한계

- ESA WorldCover는 토지피복 분류도이며 실제 건물고나 수고를 제공하지 않는다.
- 클래스별 높이는 MVP 시뮬레이션용 휴리스틱 가정이다.
- 특히 시가지 8m와 수목 14m는 지역별 실제 장애물 높이 편차를 표현하지 못한다.
- 결과는 권위 있는 DSM이나 통신 보장 자료로 표현하면 안 된다.

## 다음 에이전트가 해야 할 일

1. QGIS에서 DEM, WorldCover 정렬본, 표면 높이, 임시 DSM을 중첩해 해안과 도엽 경계를 육안 검사한다.
2. 프로젝트 terrain loader에 전국 임시 DSM을 연결해 NoData와 MSL/AGL 처리를 검증한다.
3. 향후 건물 높이와 수고 자료가 확보되면 해당 영역의 휴리스틱 값을 교체한다.

## 논문 기록 필요사항

- 방법론에는 토지피복 기반 장애물 높이 대체 모델로 기록한다.
- 표면 높이값은 초기 설계 가정이며 민감도 분석 대상으로 명시한다.
- 실제 DSM 대비 오차와 클래스 내 높이 분산을 주요 한계로 기록한다.
