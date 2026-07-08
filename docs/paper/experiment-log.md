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
- PR: #8

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
- CI: GitHub Actions CI success observed for PR #8 before this minor log update; follow-up CI is expected after the minor review-fix commits.

## 실행 명령

- Local commands: Not run in this cloud/GitHub-only context.
- CI commands: GitHub Actions executed install, syntax check, pytest, ruff, and mypy successfully on the checked PR #8 run.

## 결과

- Task 001 scaffold CI status: success on the checked PR #8 run
- package install in CI: success
- syntax check in CI: success
- pytest in CI: success
- ruff in CI: success
- mypy in CI: success
- 색상 등급별 셀 수: 미산출
- 제외구역 비율: 미산출
- 경로 후보별 실 비행거리: 미산출
- 경로 후보별 평균 차폐점수: 미산출
- 500m 경유점 수: 미산출

## 해석

Task 001은 실험 결과가 아니라 재현 가능한 구현·검증 환경 준비 단계로 해석한다. CI success는 scaffold/test 품질 확인에 한정하며, 실제 DEM/DSM 실험 결과를 의미하지 않는다.

## 한계

- 로컬 직접 테스트 실행 없음
- 실제 DEM/DSM 없음
- 실제 링크상태 검증 없음
- 실제 드론운용 없음
- 지도 렌더링 확인 없음

## 논문 반영 가능 여부

구현 환경 및 재현성 장에는 반영 가능. 결과 장에는 반영 불가.

## GPT Master 검토 메모

PR #8의 Task 001 scaffold CI success가 확인되었다. 이 로그 업데이트 이후 추가 minor fix commit에 대한 follow-up CI 결과도 merge 전 확인해야 한다.

---

# Experiment EXP-20260708-002

## 관련 Task / Issue / PR

- Task: 002 - Coordinate and candidate grid module
- Issue: #9
- PR: 생성 예정

## 목적

실제 실험 실행이 아니라, 좌표 dataclass, 2D/3D 거리 helper, 후보 발진지 candidate grid scaffold 및 테스트 준비 상태를 기록한다.

## 데이터 종류

- synthetic DEM: 없음
- synthetic DSM: 없음
- 공개/샘플 DEM: 없음
- 공개/샘플 DSM: 없음
- 실제 링크상태 데이터: 없음
- actual_drone_operation: false
- actual_link_measurement: false

## 좌표계 및 범위

- Local metric coordinate scaffold only
- WGS84/MGRS conversion helper는 optional dependency 구조이며 실제 군사좌표 정확도 검증은 후속 로컬 검증 필요

## 입력 파라미터

- 목표 MGRS: optional helper input only
- 운용반경: `CandidateGridConfig.radius_m`
- 허가 AGL: 사용하지 않음, 후속 DEM/DSM 및 LOS/Fresnel task 범위
- 주파수 대역: 사용하지 않음, 후속 Fresnel task 범위
- 격자 해상도: `CandidateGridConfig.spacing_m`
- 색상 등급 임계값: Task 006 이후 정의 예정
- 점수식 가중치: 사용하지 않음, Task 006 이후 적용

## 방법

Cloud/GitHub 기반으로 순수 Python 좌표 및 grid scaffold를 작성한다. 실제 DEM/DSM loading, LOS/Fresnel computation, scoring, map rendering은 수행하지 않는다.

## 실행 환경

- Cloud: GitHub connector file operations
- Local: Not run in this cloud/GitHub-only context.
- CI: PR 생성 후 확인 필요

## 실행 명령

- Local commands: Not run in this cloud/GitHub-only context.
- CI commands: PR 생성 후 GitHub Actions가 install, syntax check, pytest, ruff, mypy를 실행할 것으로 예상

## 결과

- 좌표 dataclass scaffold: 작성
- 2D/3D 거리 helper: 작성
- candidate grid scaffold: 작성
- 운용반경 이내/초과 후보 구분: 작성
- 색상 등급별 셀 수: 미산출
- 제외구역 비율: 미산출
- 경로 후보별 실 비행거리: 미산출
- 경로 후보별 평균 차폐점수: 미산출
- 500m 경유점 수: 미산출

## 해석

Task 002는 색상 기반 발진 가능구역 지도를 만들기 위한 candidate cell 구조 준비 단계다. 이 기록은 실제 지형분석 또는 링크품질 검증 결과가 아니다.

## 한계

- 실제 DEM/DSM 없음
- 실제 MGRS 운용 정확도 검증 없음
- 실제 링크상태 검증 없음
- 실제 드론운용 없음
- LOS/Fresnel 알고리즘 없음
- 지도 렌더링 확인 없음

## 논문 반영 가능 여부

방법론의 좌표/격자 scaffold와 재현성 설명에는 반영 가능. 실험 결과 또는 성능 결과로는 반영 불가.

## GPT Master 검토 메모

Task 002 PR 생성 후 diff와 CI 결과를 기준으로 편입 여부를 판단한다.
