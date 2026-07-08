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

아직 누적된 실험 기록 없음.
