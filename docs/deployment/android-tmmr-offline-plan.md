# Android/TMMR Offline Deployment Plan

## Purpose

현장 드론 운용자가 사용할 수 있는 전자기기가 Android 기반 TMMR 휴대용 단말기라는 운용환경을 고려하여, 최종 빌드 완료 이후 Android offline 분화 버전을 검토한다.

## Scope

- 논문 핵심 기능이 아니라 제품화·배포 전략
- 오프라인 운용 가능성 확보
- 사전 탑재 데이터 또는 사전 산출 map-ready package 활용
- 현장 사용자 접근성 향상

## Non-goals

- 논문 본문 반영
- 실제 Android 구현 완료 주장
- 실제 TMMR 검증 완료 주장
- 실제 드론 제어
- autopilot/control integration
- 실시간 통신품질 검증
- RSSI/SINR/packet_loss 검증

## Phased Roadmap

### Android offline viewer

PC/서버에서 산출한 map-ready package를 Android에서 조회한다.

### Android lightweight offline planner

사전 가공된 terrain/profile data를 활용해 일부 계산을 수행한다.

### Android full offline planner

단말 내 DEM/DSM tile 처리, LOS/Fresnel, 고도 산출, 지도 표시까지 확장 검토한다.

## Paper Boundary

Android/TMMR offline은 본 논문의 핵심 연구범위에 포함하지 않는다. 해당 기능은 현장 운용자의 사용성을 높이기 위한 제품화·배포 전략으로 별도 관리한다.
