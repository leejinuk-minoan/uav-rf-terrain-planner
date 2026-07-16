# CLAUDE.md

이 문서는 Claude Code가 `uav-rf-terrain-planner` 저장소에서 작업할 때 따라야 할 전용 지침이다. 공통 규칙은 `AGENTS.md`를 우선 적용한다.

## 1. Claude Code 작업 목표

Claude Code는 사용자의 감독하에 기능 단위 구현을 수행한다. 본 프로젝트는 연구·교육·시뮬레이션용 지형·전파 차폐 분석 도구이며, 실제 드론 자동조종 또는 실시간 운용 제어 소프트웨어가 아니다.

## 2. 작업 시작 전 확인 순서

Claude Code는 작업을 시작하기 전에 다음을 수행한다.

```bash
git status
ls
```

그 다음 아래 문서를 읽는다.

```text
AGENTS.md
README.md
docs/master-plan.md
docs/research/research-index.md
docs/agent-build-feasibility.md
docs/paper/RESEARCH_BUILD_RECORD.md
```

작업 지시가 문서와 충돌하면 구현하지 말고 충돌 내용을 보고한다.

### 2.1 누적 연구 빌드 기록

모든 Task 시작 시 `docs/paper/RESEARCH_BUILD_RECORD.md`에서 직전 Task의 실제 PR
merge 상태, final head, merge commit, merge date와 Issue closure를 확인한다. 구현
시작 시에는 현재 Task의 branch, base commit, Issue, 계획 capability, data type,
관련 EXP/DEC를 `in progress`로 기록한다. Draft PR 전에는 final branch head, PR,
focused/full tests, compileall, Ruff, mypy, diff check, GitHub Actions 상태와 한계를
기록하고, merge 뒤에는 merge commit/date와 Issue closure를 `merged`로 정합화한다.
기존 수치나 상태 수정은 correction log에 근거와 함께 남긴다. 완료 보고에는 ledger
갱신 여부, Build ID, 이전 Task 정합화, 현재 상태, correction entries, local/CI
verification을 포함한다.

## 3. 권한 및 명령 실행 원칙

### 3.1 허용되는 명령

아래 명령은 일반적으로 허용된다.

```bash
python -m pytest
python -m compileall src tests
python -m pip install -e .
python -m ruff check .
python -m mypy src
```

단, 해당 도구가 설치되어 있지 않으면 설치를 시도하기 전에 사용자에게 보고한다.

### 3.2 주의가 필요한 명령

아래 작업은 사용자 승인 없이 수행하지 않는다.

```text
대형 데이터 다운로드
외부 API 호출
시스템 전역 패키지 설치
파일 대량 삭제
git push --force
토큰/키/인증정보 접근
실제 드론 또는 외부 장비 연결
```

## 4. 구현 우선순위

초기 구현은 다음 순서로 진행한다.

1. Python 패키지 구조 및 pyproject.toml
2. 좌표 변환 모듈
3. synthetic DEM/DSM 테스트 데이터 생성
4. 래스터 샘플링 및 지형 단면 추출
5. LOS 분석
6. Fresnel Zone 분석
7. 차폐점수 모델
8. 발진기지 후보 추천
9. 경로탐색 및 경로 후보 3개
10. 500m 경유점 산출
11. Streamlit/Folium UI
12. CI와 문서 정리

## 5. 코드 작성 기준

- Python 3.11 이상 기준
- 함수와 클래스에 타입 힌트 작성
- 단위는 변수명 또는 docstring에 명확히 기록한다. 예: `distance_m`, `frequency_mhz`, `altitude_agl_m`
- GIS 데이터가 없어도 테스트 가능한 synthetic 데이터 생성기를 둔다.
- 핵심 수학 함수는 순수 함수로 구현하여 테스트 가능하게 한다.
- UI 코드와 계산 엔진을 분리한다.
- 대형 데이터는 저장소에 포함하지 않는다.

## 6. 추천 패키지

초기 pyproject에서 검토할 패키지:

```text
numpy
pandas
pyproj
mgrs
rasterio
shapely
geopandas
networkx
pydantic
streamlit
folium
pytest
ruff
mypy
```

GDAL/rasterio 계열 설치가 환경에서 실패하면, 우선 synthetic 배열 기반 테스트로 진행하고 설치 이슈를 문서화한다.

## 7. 테스트 원칙

각 PR은 최소한 다음 중 하나 이상의 테스트를 포함한다.

- 좌표 변환 테스트
- 3D 거리 계산 테스트
- Fresnel 반경 계산 테스트
- LOS 차단/비차단 synthetic terrain 테스트
- 경로탐색 synthetic grid 테스트
- 500m 경유점 생성 테스트

테스트 데이터는 `tests/fixtures/` 또는 코드 내 synthetic generator를 사용한다.

## 8. PR 작성 원칙

PR 설명에는 반드시 다음을 포함한다.

```markdown
## 목적

## 구현 내용

## 테스트

## 검증 한계

## 다음 작업
```

사용자의 승인을 받기 전에는 main에 merge하지 않는다.

## 9. 금지 사항

- 실제 비행제어 기능 구현 금지
- 탐지 회피, 침투, 공격 지원 목적 기능 구현 금지
- 비공개 지도/군사 데이터 자동 수집 금지
- secret, token, API key 커밋 금지
- 실제 운용 판단을 확정적으로 표현하는 UI 문구 금지

UI 문구는 “추천”, “예상”, “분석 기준”, “시뮬레이션 결과”처럼 보조적 표현을 사용한다.

## 10. 작업 완료 보고 형식

```markdown
## 작업 완료
- 요약:
- 변경 파일:
- 실행한 테스트:
- 실패/주의사항:
- 다음 작업 제안:
```
