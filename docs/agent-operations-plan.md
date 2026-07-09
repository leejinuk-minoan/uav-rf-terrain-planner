# Cloud Execution Agent 우선 에이전트 운영 플랜

작성일: 2026-07-08  
개정일: 2026-07-08  
대상 저장소: `leejinuk-minoan/uav-rf-terrain-planner`  
운영 원칙: GPT Master 통제하의 Cloud Execution Agent 우선 시행 및 로컬 필요 작업 제한 투입

---

## 1. 운영 결론

본 프로젝트는 로컬 실행이 반드시 필요한 작업을 제외하고, GitHub 기반 **Cloud Execution Agent**를 우선 활용한다.

```text
GPT Master가 Task 정의
→ Cloud Execution Agent가 클라우드/GitHub에서 가능한 작업 수행
→ PR 생성
→ GPT Master 검토
→ 로컬 검증이 반드시 필요한 경우에만 Codex 또는 Claude Code 투입
→ 사용자 승인 후 merge
```

Codex와 Claude Code는 기본 구현자가 아니라 **로컬 실행·환경검증·UI 확인·GIS 의존성 문제 해결 담당자**로 운용한다.

논문 작성은 Cloud Execution Agent가 수행하지 않는다. **학회 풀 페이퍼의 최종 구조 설계, 논지 구성, 문장 작성, 선행연구 해석, 점수식 타당성 검증, 결과 해석은 GPT Master Agent가 총괄한다.** Cloud Execution Agent, Codex, Claude Code는 논문 작성에 필요한 근거 기록과 작업 산출물을 남기는 역할을 한다.

중요한 제품 기준은 다음이다.

```text
발진기지 기본 출력 = Top 5 점 목록이 아니라 색상 기반 발진 가능구역 지도
경로 추천 = 사용자가 지도상에서 발진기지를 선택한 뒤 경로 후보 3개 제시
최소 요구 고도 = DSM 기반 LOS/Fresnel Clearance 조건을 만족하는 MSL 및 최고 지표고 기준 AGL 판단 보조
```

---

## 2. 역할 정의

| 주체 | 역할 | 주요 책임 |
|---|---|---|
| 사용자 | 최종 승인자 | 데이터 제공, 주요 가정 승인, PR merge 승인, 결과 화면 검수 |
| GPT Master | 총괄 통제 및 논문 작성 책임자 | Task 분해, Issue 작성, Cloud/Codex/Claude 배정, PR 검토, 작업기록 추적, 점수식 검증, 논문 최종 작성 |
| Cloud Execution Agent | 클라우드 시행 담당 | GitHub 파일 생성·수정, 순수 코드 초안, synthetic 테스트 초안, 문서화, PR 생성, 연구기록 초안 작성 |
| Codex | 로컬 필요 구현·수정 담당 | 순수 함수 검증, 로컬 테스트 재현, 제한된 코드 수정, 작은 버그 수정, 작업기록 작성 |
| Claude Code | 로컬 통합·디버깅 담당 | 패키지 설치, CI/로컬 불일치, Streamlit/Folium UI 확인, GIS 의존성 문제 해결, 작업기록 작성 |

---

## 3. 기본 시행 흐름

```text
1. GPT Master가 Task 이슈 또는 작업 범위를 정의한다.
2. 사용자 또는 GPT Master가 작업 범위를 승인한다.
3. Cloud Execution Agent가 기준 문서와 Issue 범위를 확인한다.
4. Cloud Execution Agent가 브랜치를 생성하고 클라우드에서 가능한 구현·문서 작업을 수행한다.
5. Cloud Execution Agent가 PR을 생성하고 테스트 가능 범위와 로컬 검증 필요 항목을 분리해 보고한다.
6. GPT Master가 PR diff, 파일 내용, 요구사항 충족 여부, 논문 기록 적합성을 검토한다.
7. 로컬 실행이 반드시 필요한 경우 Codex 또는 Claude Code에 제한 임무를 부여한다.
8. Codex 또는 Claude Code는 로컬 검증·최소 수정 후 실행 명령과 결과를 PR 또는 handoff에 기록한다.
9. GPT Master가 최종 검토하고, 논문 반영 가능성과 한계를 정리한다.
10. 사용자 승인 후 merge한다.
11. GPT Master가 Task별 작업기록을 추적·관리하고 논문 작성 자료로 편입한다.
```

---

## 4. 논문 작성 및 연구기록 관리 원칙

### 4.1 최종 논문 작성 책임

학회 제출용 풀 페이퍼 초안 작성은 GPT Master가 담당한다. Cloud Execution Agent는 논문 초안을 독자적으로 작성하지 않는다.

GPT Master는 다음 자료를 추적한다.

- Cloud Execution Agent의 Issue, PR, 문서 변경, 연구 로그 초안
- Codex의 구현 기록, 테스트 결과, 수정 내역
- Claude Code의 로컬 실행 기록, UI 확인 결과, GIS 의존성 문제 해결 기록
- GitHub PR diff와 merge 이력
- Task별 실험 조건, synthetic/실제 데이터 구분, 검증 한계
- 점수식 변경 이력과 사용자 승인 여부

### 4.2 Cloud Execution Agent의 논문 관련 역할

Cloud Execution Agent는 다음만 수행한다.

- Task별 연구 로그 초안 작성
- 실험 로그 양식 작성
- 의사결정 로그 초안 작성
- PR 검토 로그용 기초 정보 정리
- 그림/표 후보 제안
- 참고문헌 필요 항목 표시
- GPT Master가 논문에 반영할 수 있도록 근거와 한계 정리

Cloud Execution Agent는 다음을 하지 않는다.

- 최종 논문 초안 독자 작성
- 검증되지 않은 실험 결과 서술
- 선행연구를 확인하지 않은 주장 삽입
- 점수식의 타당성을 확정적으로 단정
- GPT Master 검토 없이 논문용 결론 작성

### 4.3 Codex/Claude Code의 논문 관련 역할

Codex와 Claude Code는 작업 완료 시 다음을 남긴다.

- 변경 파일 목록
- 실행한 명령
- 통과/실패/미실행 테스트
- 구현 한계
- 로컬 환경 이슈
- 논문에 반영 가능한 결과와 반영 불가능한 결과
- 추가 검증 필요사항

### 4.4 Task 014 이후 논문 기록 분산 구조

Task 014 이후 신규 논문 기록은 장문 누적 로그에 직접 계속 추가하지 않고 `docs/paper/log-structure.md`의 규칙을 따른다.

- 의사결정 기록은 `docs/paper/decisions/` 아래에 개별 파일로 작성한다.
- 연구 노트는 `docs/paper/research-notes/` 아래에 개별 파일로 작성한다.
- 실험 기록은 `docs/paper/experiments/` 아래에 개별 파일로 작성한다.
- PR 검토 기록은 `docs/paper/pr-reviews/` 아래에 개별 파일로 작성한다.
- 신규 기록은 `docs/paper/templates/`의 해당 템플릿을 사용한다.
- 기존 `docs/paper/research-log.md`, `docs/paper/decision-log.md`, `docs/paper/experiment-log.md`, `docs/paper/pr-review-log.md`는 historical archive 및 legacy index로 유지한다.
- GPT Master가 기록 구조, 논문 반영 경계, 제품/배포 경계를 최종 판단한다.
- Codex는 긴 문서 직접 수정이 필요한 경우에만 제한적으로 투입하고, 신규 기록은 가능한 한 개별 파일로 작성한다.
- 공개 저장소에 남길 수 없는 좌표, 작전성 데이터, 계정 정보, 토큰, 키, 비공개 경로는 기록하지 않는다.

---

## 5. 점수식 검증 및 보완 원칙

현재 기준 점수식은 MVP 초기 가정이다.

```text
발진 가능구역 종합점수 = 차폐안정성 점수 × 0.80 + 거리점수 × 0.20
차폐안정성 점수 = LOS 점수 × 0.50 + Fresnel 여유 점수 × 0.35 + DSM 장애물 점수 × 0.15
```

이 가중치는 연구 결과로 확정된 값이 아니라, MVP에서 차폐 안정성을 거리보다 우선하기 위한 초기 설계 가정이다. 따라서 논문에서는 다음처럼 구분한다.

| 구분 | 논문 표현 기준 |
|---|---|
| 초기 가중치 | 설계 가정 또는 heuristic weighting |
| synthetic 테스트 | 알고리즘 동작 확인 |
| 실제 DEM/DSM 검증 | 실제 지형 데이터 기반 검증 |
| 실제 링크상태 검증 | 향후 연구 또는 추가 검증 필요 |
| 성능 입증 | 실제 링크상태 데이터와 비교 검증 전에는 사용 금지 |

GPT Master는 선행연구를 확인하여 다음을 검토한다.

1. LOS 차단 여부를 강하게 반영하는 것이 타당한가?
2. Fresnel Zone 침범률을 별도 점수로 반영하는 것이 타당한가?
3. DSM 장애물 점수를 독립 항목으로 둘지, LOS/Fresnel 침범 계산에 통합할지?
4. 거리점수 20%가 경로 안정성 관점에서 과도하거나 부족하지 않은가?
5. 실제 데이터가 없는 상태에서 가중치를 고정값으로 둘 때 논문상 한계를 어떻게 명시할 것인가?
6. 향후 실제 링크상태 데이터 또는 radio map 기반 보정으로 가중치를 학습·보정할 수 있는가?

점수식을 변경해야 할 경우 GPT Master는 변경안, 근거, 영향, 테스트 방법, 논문 반영 방식을 제시하고 사용자 승인을 받은 뒤 반영한다.

---

## 6. Cloud Execution Agent 담당 범위

Cloud Execution Agent는 로컬 실행 없이 GitHub/클라우드에서 처리 가능한 작업을 담당한다.

| 작업 | 가능 여부 | 비고 |
|---|---:|---|
| GitHub 기준 문서 읽기 | 가능 | README, AGENTS, master-plan 등 |
| Issue 본문 작성 | 가능 | GPT Master가 직접 작성할 수도 있음 |
| 브랜치 생성 | 가능 | `agent/task-00X-*` 형식 |
| 문서 파일 생성·수정 | 가능 | `docs/`, `docs/paper/` 포함 |
| `pyproject.toml` 작성 | 가능 | 실제 설치 검증은 로컬 또는 CI 필요 |
| Python 패키지 구조 생성 | 가능 | `src/`, `tests/`, `examples/` |
| 순수 계산 함수 작성 | 가능 | 좌표, 거리, 점수식 등 |
| synthetic 데이터 기반 테스트 코드 작성 | 가능 | 실제 실행 결과는 CI/로컬 확인 필요 |
| CI 설정 수정 | 가능 | GitHub Actions 기준 |
| PR 생성 | 가능 | 목적·구현·테스트·한계 포함 |
| 연구 로그 초안 작성 | 가능 | Task 종료 시 초안 작성 |
| 실험 로그 양식 작성 | 가능 | 실제 실행값은 확인 필요 |
| 논문 최종 작성 | 불가 | GPT Master 전담 |

Cloud Execution Agent는 `python -m pytest` 실행, Streamlit 화면 확인, rasterio/GDAL 설치 확인, 실제 DEM/DSM 연결을 완료했다고 단정하지 않는다. 해당 항목은 로컬 검증 필요사항으로 분리한다.

---

## 7. 로컬에서 반드시 필요한 작업

다음 항목은 Codex 또는 Claude Code에 제한 임무로 부여한다.

| 로컬 필요 작업 | 추천 담당 | 이유 |
|---|---|---|
| `python -m pip install -e .` 실제 설치 확인 | Claude Code | 환경 의존성 확인 필요 |
| `python -m pytest` 로컬 재현 | Codex 또는 Claude Code | 실패 원인 재현 필요 |
| `rasterio`, `GDAL`, `geopandas` 설치 문제 해결 | Claude Code | OS/패키지 의존성 큼 |
| Streamlit/Folium 화면 실행 확인 | Claude Code | 실제 UI 확인 필요 |
| 지도 색상 레이어 시각 확인 | Claude Code | 브라우저/지도 렌더링 확인 필요 |
| 로컬 DEM/DSM 파일 연결 테스트 | Claude Code | 대형 데이터는 GitHub에 커밋하지 않음 |
| 실제 데이터 기반 샘플 실행 | Claude Code | 데이터 경로와 좌표계 확인 필요 |
| CI와 로컬 결과 불일치 해결 | Claude Code | 환경 차이 분석 필요 |
| 복잡한 다중 파일 리팩터링 | Claude Code | 통합 맥락 확인 필요 |
| 수학 함수의 빠른 단위 테스트 보완 | Codex | 제한된 순수 함수 수정에 적합 |

---

## 8. Task별 수정 배정안

| Task | 내용 | 1차 시행자 | 로컬 투입 조건 | 논문 관리 |
|---:|---|---|---|---|
| 001 | 프로젝트 스캐폴딩 | Cloud Execution Agent | 패키지 설치 또는 CI 실패 시 Claude Code | GPT Master가 기록 구조 확인 |
| 002 | MGRS/WGS84/투영좌표계 변환 | Cloud Execution Agent | `mgrs`, `pyproj` 오류 시 Claude Code | GPT Master가 좌표계 설명 관리 |
| 003 | synthetic DEM/DSM 및 래스터 샘플링 | Cloud Execution Agent | rasterio/GDAL 확인 필요 시 Claude Code | GPT Master가 데이터/전처리 장 관리 |
| 004 | 지형 단면 추출 | Cloud Execution Agent | 성능·좌표 샘플링 오류 시 Codex/Claude Code | GPT Master가 알고리즘 장 관리 |
| 005 | LOS 분석 및 테스트 | Cloud Execution Agent | 테스트 실패 재현 어려울 때 Codex | GPT Master가 LOS 근거 검토 |
| 006 | Fresnel Zone 계산 | Cloud Execution Agent | 수식 검산 보완 시 Codex | GPT Master가 Fresnel 근거 검토 |
| 007 | 차폐안정성 점수 모델 | Cloud Execution Agent | 필요 시 Codex | GPT Master가 점수식 타당성 검토 |
| 008 | 발진 가능구역 격자 평가 및 색상 지도화 | Cloud Execution Agent | 지도 레이어 확인은 Claude Code | GPT Master가 핵심 제안기법 관리 |
| 009 | 경로탐색 기반 경로 후보 3개 생성 | Cloud Execution Agent 초안 | 경로 중복·속도 확인 시 Claude Code | GPT Master가 경로비용식 관리 |
| 010 | 500m 단위 경유점 및 실 비행거리 계산 | Cloud Execution Agent | 좌표 변환 연동 오류 시 Codex/Claude Code | GPT Master가 결과표 후보 관리 |
| 011 | Streamlit/Folium MVP UI | Claude Code | 처음부터 로컬 화면 확인 필요 | GPT Master가 UI 그림 후보 관리 |
| 012 | 통합 테스트, 문서화, 샘플 실행 시나리오 | Claude Code | 로컬 실행·화면·CI 검증 필요 | GPT Master가 검증 장 관리 |
| 013 | 논문용 연구기록 구조 생성 | Cloud Execution Agent 또는 GPT Master | 로컬 불필요 | GPT Master 총괄 |
| 013-A | 문서 기준 정리 및 고도 판단 보조 개념 반영 | Codex | 장문 문서 diff 안전검증 필요 | GPT Master가 논문 경계 확인 |
| 014 | 실험 결과·그림·표 후보 정리 | GPT Master + Cloud Execution Agent | 실제 화면 캡처는 Claude Code | GPT Master 총괄 |
| 015 | 학회 풀 페이퍼 초안 작성 | GPT Master | 로컬 불필요 | GPT Master 전담 |

향후 추가 Task 분장은 다음 원칙을 따른다.

- Minimum Required MSL and AGL Estimation Scaffold는 순수 Python 계산 모듈로 우선 구현한다.
- 실제 DEM/DSM adapter와 UI/map rendering은 후속 Task로 분리한다.
- Android/TMMR offline은 제품/배포 로드맵 Task로 분리하고 논문 핵심 기능으로 다루지 않는다.

---

## 9. Handoff checkpoint 절차

Cloud Execution Agent, Codex, Claude Code 사이에 작업이 넘어갈 때는 handoff checkpoint를 남긴다. 특히 Cloud Execution Agent가 만든 PR을 로컬 에이전트가 이어받을 때는 로컬 검증 범위를 명확히 제한한다.

```markdown
# Task Handoff

## 현재 Task
Task 00X - 작업명

## 현재 브랜치
agent/task-00X-...

## 담당했던 에이전트
Cloud Execution Agent / Codex / Claude Code

## 작업한 내용
- 변경 파일 1
- 변경 파일 2
- 구현 완료 기능

## 아직 미완성
- 남은 구현
- 실패한 테스트
- 불확실한 설계 판단
- 로컬 검증 필요사항

## 실행한 명령
- Cloud Execution Agent는 실제 로컬 명령을 실행하지 않았다면 "미실행"으로 기록
- Codex/Claude Code는 실제 실행한 명령만 기록

## 현재 테스트 상태
- 통과:
- 실패:
- 미실행:

## 다음 에이전트가 해야 할 일
1. ...
2. ...
3. ...

## 논문 기록 필요사항
- 이 Task가 논문 어느 장에 반영되는가?
- 실험/테스트 결과가 있는가?
- 그림/표 후보가 있는가?
- 한계 또는 검증 필요사항이 있는가?
- GPT Master가 확인해야 할 논문 쟁점이 있는가?

## 주의사항
- 발진기지 기본 출력은 Top 5가 아니라 색상 기반 가능구역 지도
- AGL/MSL 혼동 금지
- 대형 GIS 데이터 커밋 금지
- 실제 드론 제어 기능 구현 금지
```

---

## 10. 에이전트별 운영 규칙

### 10.1 Cloud Execution Agent 운영 규칙

Cloud Execution Agent는 다음에 우선 사용한다.

- GitHub 문서 조회
- Issue/PR 본문 작성
- 브랜치 생성
- 문서 생성·수정
- 순수 Python 모듈 초안 작성
- synthetic 테스트 코드 작성
- CI 설정 초안 작성
- 연구 로그, 실험 로그, 의사결정 로그, PR 검토 로그 초안 작성
- 로컬 검증 필요사항 분리

Cloud Execution Agent는 다음을 하지 않는다.

- 로컬에서 실행하지 않은 테스트를 통과했다고 말하기
- Streamlit/Folium 화면을 확인했다고 단정하기
- rasterio/GDAL 설치 문제를 해결했다고 단정하기
- 실제 DEM/DSM 연결 결과를 확인했다고 단정하기
- 실제 드론 제어, 탐지 회피, 침투, 공격 지원 기능 구현하기
- 학회 풀 페이퍼 최종 초안을 독자 작성하기
- 점수식의 타당성을 선행연구 검토 없이 확정하기

### 10.2 Codex 운영 규칙

Codex는 다음에 제한적으로 사용한다.

- 순수 함수 단위의 로컬 테스트 보완
- 작은 버그 수정
- 테스트 실패 재현 및 최소 수정
- 수학 함수 검산
- Cloud Execution Agent PR의 제한된 보완

Codex는 작업 완료 시 실행한 명령과 결과를 기록한다. 실행하지 않은 테스트는 미실행으로 기록한다.

### 10.3 Claude Code 운영 규칙

Claude Code는 다음에 우선 사용한다.

- 로컬 설치 확인
- CI 실패 수정
- 여러 파일 간 구조 정리
- Streamlit/Folium UI 실행 확인
- 지도 색상 레이어 화면 검증
- rasterio/GDAL/geopandas 의존성 문제 해결
- 실제 DEM/DSM 경로 연결 테스트
- Cloud Execution Agent PR의 로컬 디버깅 또는 보완

Claude Code가 로컬 작업을 시작할 때는 다음을 수행한다.

```bash
git status
git branch --show-current
```

그 다음 기준 문서, Issue, PR, handoff checkpoint를 읽고 작업한다.

---

## 11. GPT Master의 검토 체크리스트

GPT Master는 각 Task 시작 전 다음을 확인한다.

1. 이 Task가 전체 로드맵에서 어느 위치인가?
2. 클라우드에서 가능한 작업인가, 로컬 실행이 필요한 작업인가?
3. 입력/출력과 수용 기준이 명확한가?
4. Cloud Execution Agent, Codex, Claude Code 중 어느 쪽이 적합한가?
5. 이전 Task 산출물이 merge되었는가?
6. 같은 파일을 동시에 수정할 위험이 있는가?
7. 논문에 반영할 수 있는 산출물과 한계가 무엇인가?

PR 생성 후에는 다음을 확인한다.

1. Task 범위 초과 여부
2. AGENTS.md 금지 범위 침범 여부
3. Cloud Execution Agent가 로컬 실행 결과를 과장하지 않았는지
4. AGL/MSL 계산 오류 가능성
5. MGRS/WGS84/투영좌표계 처리 일관성
6. DEM/DSM 없이 synthetic 테스트가 가능한지
7. 테스트가 충분한지
8. 발진기지 출력이 Top 5 기본 출력으로 잘못 구현되지 않았는지
9. 발진 가능구역이 지도 색상 레이어로 표현 가능한 데이터 구조인지
10. 로컬 검증 필요사항이 Codex/Claude Code 인계사항으로 분리되었는지
11. 다음 Task에 구조적 부채를 남기지 않는지
12. 사용자가 승인해야 할 판단 사항이 분리되었는지
13. 연구 로그·실험 로그·의사결정 로그·PR 검토 로그 업데이트 항목이 있는지
14. 점수식·선행연구·검증 한계가 논문에서 과장 없이 표현될 수 있는지

---

## 12. 사용자 승인 게이트

사용자는 모든 코드를 직접 읽지 않아도 되지만, merge 전 아래 항목은 확인한다.

| 확인 항목 | 설명 |
|---|---|
| Task 범위 | 이 PR이 지정 Task만 수행했는가 |
| 시행자 구분 | Cloud Execution Agent 작업과 로컬 검증 작업이 구분되는가 |
| 테스트 결과 | 실제 실행된 테스트와 미실행 테스트가 구분되는가 |
| 출력 형식 | 발진기지가 색상 기반 가능구역 지도로 구현되는가 |
| 알고리즘 가정 | AGL/MSL, 거리, 차폐점수 가정이 승인 가능한가 |
| 로컬 검증 필요성 | Codex/Claude Code 투입이 필요한 항목이 분리되었는가 |
| 연구기록 | Task 종료 시 논문용 기록이 남는가 |
| 논문 책임 | 최종 논문 작성과 점수식 검증이 GPT Master 책임으로 남아 있는가 |
| 다음 단계 영향 | 다음 Task로 넘어가도 되는가 |

---

## 13. 금지 운영 방식

다음 방식은 사용하지 않는다.

```text
1. Codex와 Claude Code가 같은 브랜치를 동시에 수정
2. Cloud Execution Agent와 로컬 에이전트가 같은 파일을 조율 없이 동시 수정
3. Task가 끝나지 않았는데 handoff 없이 다른 에이전트가 이어받음
4. Cloud Execution Agent가 실행하지 않은 로컬 테스트를 통과했다고 보고
5. 테스트 없이 main에 merge
6. synthetic 테스트 없이 실제 데이터부터 연결
7. 대형 DEM/DSM을 저장소에 직접 커밋
8. 실제 드론 제어 기능을 슬그머니 추가
9. “통신 보장”, “최적 운용 확정” 등 확정적 표현을 UI에 사용
10. 발진기지를 기본 출력에서 Top 5 점 목록으로 단순화
11. Cloud Execution Agent가 학회 풀 페이퍼 최종 초안을 독자 작성
12. 점수식 가중치를 검증된 성능값처럼 논문에 서술
```

---

## 14. 최종 운영 방침

본 프로젝트의 에이전트 운영은 다음 문장으로 요약한다.

```text
GPT Master가 Task를 정의하고,
Cloud Execution Agent가 클라우드에서 가능한 구현·문서·PR 작업을 먼저 수행하며,
Codex와 Claude Code는 로컬 실행이 반드시 필요한 검증·수정 작업에만 투입하고,
발진 가능구역은 Top 5가 아니라 색상 기반 지도 레이어로 구현하며,
Cloud/Codex/Claude의 Task별 작업기록은 GPT Master가 추적·관리하고,
점수식 타당성 검토와 학회 풀 페이퍼 최종 작성은 GPT Master가 총괄하며,
사용자는 PR 단위로 최종 승인한다.
```

이 방식은 클라우드에서 가능한 작업을 빠르게 선행하면서도, 로컬 실행이 필요한 GIS·UI·패키지 의존성 검증을 별도 통제점으로 분리하고, 논문 작성 책임과 연구기록 추적 책임을 GPT Master에 집중시키는 운영 방식이다.
