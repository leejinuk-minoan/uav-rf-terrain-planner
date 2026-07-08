# Experiment Log

책임 주체: GPT Master Agent  
목적: synthetic 및 공개/샘플 DEM·DSM 기반 실험 조건과 결과를 누적 기록한다.

---

## 기록 원칙

- 실제 드론 운용 없이 수행한 오프라인 실험만 기록한다.
- synthetic 데이터와 실제 지형 데이터는 반드시 구분한다.
- 실제 링크상태 데이터가 없으면 RSSI/SINR/packet loss 검증을 수행한 것처럼 기록하지 않는다.
- 실험마다 재현 가능한 입력 파라미터를 남긴다.

---

## Template

```markdown
# Experiment EXP-YYYYMMDD-XX

## 관련 Task / Issue / PR

## 목적

## 데이터 종류
- synthetic DEM:
- synthetic DSM:
- 공개/샘플 DEM:
- 공개/샘플 DSM:
- 실제 링크상태 데이터:

## 좌표계 및 범위

## 입력 파라미터
- 목표 MGRS:
- 운용반경:
- 허가 AGL:
- 주파수 대역:
- 격자 해상도:
- 색상 등급 임계값:
- 점수식 가중치:

## 방법

## 실행 환경
- Cloud:
- Local:
- CI:

## 실행 명령

## 결과
- 색상 등급별 셀 수:
- 제외구역 비율:
- 경로 후보별 실 비행거리:
- 경로 후보별 평균 차폐점수:
- 500m 경유점 수:

## 해석

## 한계

## 논문 반영 가능 여부

## GPT Master 검토 메모
```

---

## Experiment Records

# Experiment EXP-20260708-001

## 관련 Task / Issue / PR

- Task: 001 - Project scaffold and scoring schema preparation
- Issue: #7
- PR: 생성 예정

## 목적

실험 실행이 아니라, 향후 synthetic 및 공개/샘플 DEM·DSM 실험을 위한 package/config/schema/test scaffold 준비 상태를 기록한다.

## 데이터 종류

- synthetic DEM: 없음, metadata placeholder only
- synthetic DSM: 없음, metadata placeholder only
- 공개/샘플 DEM: 없음
- 공개/샘플 DSM: 없음
- 실제 링크상태 데이터: 없음
- actual_drone_operation: false
- actual_link_measurement: false

## 좌표계 및 범위

Task 002 이후 정의 예정.

## 입력 파라미터

- 목표 MGRS: placeholder only
- 운용반경: `5000.0 m` sample config placeholder
- 허가 AGL: `120.0 m` sample config placeholder
- 주파수 대역: `2.4 GHz` sample config placeholder
- 격자 해상도: `100.0 m` synthetic metadata placeholder
- 색상 등급 임계값: Task 006 이후 정의 예정
- 점수식 가중치: DSM LOS 0.40, DSM Fresnel 0.60, shielding 0.80, distance 0.20

## 방법

Cloud/GitHub 기반 파일 생성 및 schema/test scaffold 작성. 실제 실험은 수행하지 않음.

## 실행 환경

- Cloud: GitHub connector file operations
- Local: Not run in this cloud/GitHub-only context.
- CI: PR 생성 후 확인 필요

## 실행 명령

Not run in this cloud/GitHub-only context.

## 결과

- 색상 등급별 셀 수: 미산출
- 제외구역 비율: 미산출
- 경로 후보별 실 비행거리: 미산출
- 경로 후보별 평균 차폐점수: 미산출
- 500m 경유점 수: 미산출

## 해석

Task 001은 실험 결과가 아니라 재현 가능한 구현·검증 환경 준비 단계로 해석한다.

## 한계

- 실제 테스트 실행 없음
- 실제 DEM/DSM 없음
- 실제 링크상태 검증 없음
- 실제 드론운용 없음

## 논문 반영 가능 여부

구현 환경 및 재현성 장에는 반영 가능. 결과 장에는 반영 불가.

## GPT Master 검토 메모

CI 및 로컬 검증 결과 확인 후 실험 로그 상태를 업데이트해야 한다.
