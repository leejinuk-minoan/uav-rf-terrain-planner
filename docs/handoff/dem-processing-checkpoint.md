# DEM Processing Checkpoint

작성일: 2026-07-10

## 현재 Task

Task 018A - DEM/DSM Preprocessing Handoff and Restore Scripts

## 담당했던 에이전트

Codex

## 작업한 내용

- `<LOCAL_PROJECT_ROOT>/METADATA_MAP` 아래 공개 DEM zip 파일 342개 확인
- 파일명 기준 도엽 225개 식별
- 도엽별 최신 연도 1개를 선택
  - 2025년 도엽: 220개
  - 2024년 도엽: 5개
- 최신 zip 225개를 `METADATA_MAP\DEM_EXTRACTED_LATEST` 아래 추출
- 추출된 `.img` 225개를 GDAL VRT로 병합
- 전체 DEM GeoTIFF 생성

## 생성된 로컬 산출물

Git 커밋 대상이 아닌 로컬 데이터 산출물이다.

```text
METADATA_MAP/dem_latest_manifest.csv
METADATA_MAP/DEM_EXTRACTED_LATEST/
METADATA_MAP/DEM_PROCESSED/dem_img_list_nobom.txt
METADATA_MAP/DEM_PROCESSED/south_korea_dem_90m_epsg5179_alltiles.vrt
METADATA_MAP/DEM_PROCESSED/south_korea_dem_90m_epsg5179_alltiles.tif
```

## 최종 DEM 검증 요약

```text
driver: GTiff
crs: EPSG:5179
resolution: 90m x 90m
size: 4057 x 5865 pixels
nodata: -9999
valid ratio: 73.09%
bounds EPSG:5179:
  left: 838710
  bottom: 1555740
  right: 1203840
  top: 2083590
elevation statistics:
  min: -88.697m
  max: 1898.456m
  mean: 191.249m
  p50: 92.532m
  p99: 1006.121m
```

## 실행한 명령

- PowerShell `Get-ChildItem`로 zip/도엽/연도 집계
- PowerShell `Expand-Archive`로 도엽별 최신 zip 추출
- QGIS 3.40.14 GDAL `gdalbuildvrt.exe`로 VRT 생성
- QGIS 3.40.14 GDAL `gdal_translate.exe`로 LZW 압축 GeoTIFF 생성
- Python `rasterio`로 최종 GeoTIFF 메타데이터와 통계 확인

## 현재 테스트 상태

- 통과:
  - 최신 도엽 225개 선택
  - IMG 225개 추출
  - VRT source 225개 포함 확인
  - 최종 GeoTIFF `EPSG:5179`, 90m 해상도 확인
- 실패 후 수정:
  - 최초 VRT 생성 때 UTF-8 BOM과 좌표계 문자열 차이로 6개 도엽 누락
  - BOM 없는 file list와 `-allow_projection_difference`, `-a_srs EPSG:5179`로 재생성
- 미실행:
  - 실제 분석 모듈과 최종 DEM 연결 테스트
  - DSM 구축 및 DEM/DSM 정합 검증

## 다음 에이전트가 해야 할 일

1. `src/uav_rf_terrain/terrain_data.py` 또는 후속 로더에서 최종 DEM GeoTIFF를 읽는 샘플 연결 테스트를 수행한다.
2. DSM 구축용 원천자료를 확보한다.
3. 건물높이, 수목/토지피복 자료를 DEM과 같은 EPSG:5179 격자로 정렬한다.
4. `DSM = DEM + surface_delta` 형태의 1차 DSM 또는 실제 DSM 모자이크를 만든다.
5. DEM/DSM 수직 기준과 단위가 같은지 검증한다.

## 논문 기록 필요사항

- 이 DEM은 공개 DEM 도엽을 병합한 90m 해상도 EPSG:5179 래스터다.
- 실제 DSM은 아직 생성되지 않았다.
- 본 DEM 연결은 지형 기반 offline analysis 입력자료 구축 단계이며, 실제 통신 성능 검증 결과가 아니다.
- 해안/바다/미포함 영역의 NoData 비율이 있으므로 분석영역 클리핑과 NoData 처리 정책을 논문 한계에 기록해야 한다.

## 주의사항

- 대형 GIS 원천 데이터와 처리 산출물은 Git에 커밋하지 않는다.
- 발진기지 기본 출력은 Top 5가 아니라 색상 기반 가능구역 지도다.
- AGL/MSL 혼동 금지.
- 실제 드론 제어 기능 구현 금지.
