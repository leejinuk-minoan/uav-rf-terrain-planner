# Paper Outline

책임 주체: GPT Master Agent  
목적: 학회 풀 페이퍼의 기본 구조를 관리한다.

---

## Working Title

DEM/DSM 기반 주파수 차폐 위험 분석을 활용한 UAV 발진 가능구역 및 경로 후보 추천 시뮬레이션 방법론

---

## 1. Abstract

작성 예정. Task 012~014의 실험 및 검증 결과 확인 후 GPT Master가 작성한다.

---

## 2. Introduction

### 포함할 내용

- UAV 운용에서 지형과 표면장애물이 통신 안정성에 미치는 영향
- 발진기지와 경로를 거리만으로 판단할 때의 한계
- DEM/DSM 기반 오프라인 차폐위험 분석의 필요성
- 본 연구는 실제 드론 제어가 아니라 연구·교육·시뮬레이션용 의사결정 보조 방법론임을 명시

---

## 3. Related Work

### 포함할 내용

- LOS 기반 RF 전파 분석
- Fresnel Zone과 장애물 침범
- Longley-Rice/ITM 및 지형 기반 전파모델
- Radio map 기반 UAV path planning
- GIS 기반 DEM/DSM 활용 연구

---

## 4. Problem Definition

### 포함할 내용

- 입력값: 목표 MGRS, 운용반경, 허가 AGL, 주파수 대역
- 출력값: 색상 기반 발진 가능구역 지도, 선택 발진기지 기준 경로 후보 3개, 500m 경유점
- 제외 범위: 실제 비행, 실제 조종기 제어, 탐지 회피, 공격 지원

---

## 5. System Architecture

### 포함할 내용

- 좌표 변환 모듈
- DEM/DSM 샘플링 모듈
- 지형 단면 추출 모듈
- LOS 분석 모듈
- Fresnel 분석 모듈
- 차폐안정성 점수 모듈
- 발진 가능구역 색상지도 모듈
- 경로 후보 생성 모듈
- UI 모듈

---

## 6. Methodology

### 포함할 내용

- 3D 거리 계산
- AGL/MSL 처리
- LOS 점수
- Fresnel 여유 점수
- DSM 장애물 점수
- 발진 가능구역 종합점수
- 색상 등급 분류
- 경로비용식
- 500m 경유점 생성

---

## 7. Experiment Design

### 포함할 내용

- synthetic DEM/DSM 시나리오
- 공개/샘플 DEM/DSM 검증 계획
- 점수식 민감도 분석
- ablation 분석
- 실제 드론 운용 없음 명시

---

## 8. Results

작성 예정. Task 012~014 결과 확인 후 작성한다.

---

## 9. Discussion

### 포함할 내용

- 차폐위험과 거리의 trade-off
- Top 5 점 추천 대신 색상지도 기반 판단의 장점
- 점수식 가중치의 한계
- 실제 링크상태 데이터가 없는 한계

---

## 10. Limitations and Future Work

### 포함할 내용

- 실제 드론 운용 없음
- 실제 링크상태 검증 없음
- 점수식은 초기 휴리스틱
- DEM/DSM 품질 의존성
- 향후 radio map 및 실제 링크 데이터 보정 가능성

---

## 11. Conclusion

작성 예정. 실험 결과와 한계 정리 후 GPT Master가 작성한다.

---

## Appendix

- Task별 연구 로그
- 실험 파라미터
- 점수식 민감도 결과
- 500m 경유점 예시표
