# Streamlit 버전 vs FastAPI 버전 — 공통점과 차이점

> **작성일**: 2026-08-06  
> **비교 대상**:  
> - **Streamlit 버전**: `D:\SEMCoWork\reliability_deploy\reliability_app.py` (단일 파일, 2,772줄)  
> - **FastAPI 버전**: `D:\reliability_web\` (멀티 파일, FastAPI + 순수 Python)

---

## 1. 아키텍처 비교

| 항목 | Streamlit 버전 | FastAPI 버전 |
|------|---------------|-------------|
| **프레임워크** | Streamlit (Python 웹앱) | FastAPI + Uvicorn (REST API) |
| **파일 구조** | 단일 파일 (`reliability_app.py`) | 멀티 파일 (`main.py` + `core/` + `static/`) |
| **프론트엔드** | Streamlit 위젯 자동 생성 | HTML/CSS/JS (수동 작성) |
| **백엔드** | Streamlit 서버 (단일 스레드) | FastAPI 비동기 서버 |
| **실행 명령** | `streamlit run reliability_app.py` | `python -m uvicorn main:app --port 8090` |
| **접속 방식** | `http://localhost:8501` | `http://127.0.0.1:8090` |
| **다중 사용자** | ❌ (단일 세션) | ✅ (다중 동시 접속 가능) |
| **배포 방식** | venv + batch 파일 | uvicorn 직접 실행 |

---

## 2. 공통점

### 2.1 수학적 모델 (100% 동일)

| 항목 | 내용 |
|------|------|
| **Weibull 2P 분포** | \( F(t) = 1 - \exp\left(-(t/\alpha)^\beta\right) \) |
| **MTTF** | \( \alpha \times \Gamma(1 + 1/\beta) \) |
| **Bx 수명** | \( \alpha \times (-\ln(1 - x/100))^{1/\beta} \) |
| **Arrhenius 변환** | \( \text{Minitab\_Temp} = \frac{11604.83}{T + 273.15} \) |
| **ALT 회귀 모델** | \( \ln(\eta) = \beta_0 + \beta_1 \cdot \text{Minitab\_Temp} + \beta_2 \cdot \ln(V) \) |
| **활성화에너지** | \( E_a = \beta_1 \) (eV) |
| **전압지수** | \( n = -\beta_2 \) |
| **가속계수(AF)** | \( AF = \exp\left(E_a \left(\frac{11604.83}{T_u+273.15} - \frac{11604.83}{T_s+273.15}\right) + n \cdot \ln\frac{V_s}{V_u}\right) \) |
| **LRT 검정통계량** | \( LR = 2(\ell_{\text{unconstrained}} - \ell_{\text{constrained}}) \) |
| **극치분포 NLL** | \( -\ell = -\sum_{f}\left(\frac{y_i-\mu}{\sigma} - \ln\sigma - e^{(y_i-\mu)/\sigma}\right) - \sum_{c}\left(-e^{(y_i-\mu)/\sigma}\right) \) |

### 2.2 공통 함수 (동일 로직)

| 함수 | 역할 | 코드 동일성 |
|------|------|------------|
| `ev_group_nll()` | 극치분포 음의 로그우도 | ✅ 100% 동일 |
| `minitab_lrt_test()` | LRT 동일 형상모수 검정 | ✅ 100% 동일 |
| `minitab_alt_temp_only()` | 온도만 ALT 회귀 | ⚠️ `sm.add_constant` vs `np.column_stack` |
| `minitab_alt_temp_volt()` | 온도×전압 ALT 회귀 | ⚠️ `sm.add_constant` vs `np.column_stack` |
| `preprocess_parallel_systems()` | 병렬 시스템 전처리 | ✅ 100% 동일 |
| `parse_excel_paste()` | Excel 붙여넣기 파싱 | ✅ 100% 동일 |
| `table_to_groups()` | 테이블→그룹 변환 | ✅ 100% 동일 |
| `make_col_names()` | 열 이름 생성 | ✅ 100% 동일 |

### 2.3 공통 기능

| 기능 | Streamlit | FastAPI |
|------|-----------|---------|
| Excel 전체 붙여넣기 | ✅ | ✅ |
| 병렬 채널 데이터 처리 | ✅ | ✅ |
| Weibull 2P 분석 | ✅ | ✅ |
| LRT 동일 형상모수 검정 | ✅ | ✅ |
| ALT 온도 가속 (Arrhenius) | ✅ | ✅ |
| ALT 온도×전압 가속 | ✅ | ✅ |
| 사용조건 수명 추정 | ✅ | ✅ |
| Bx 수명 계산 | ✅ | ✅ |
| 이상점 제거 | ✅ | ✅ |
| 3개 분석 모드 | ✅ | ✅ |

---

## 3. 차이점

### 3.1 Weibull 피팅 방식 (가장 큰 차이)

| 항목 | Streamlit 버전 | FastAPI 버전 |
|------|---------------|-------------|
| **Mode 1 피팅** | `reliability.Fitters.Fit_Weibull_2P` (서드파티) | `weibull_2p_mle()` (순수 Python 구현) |
| **Mode 2/3 개별 피팅** | `Fit_Weibull_2P` | `weibull_2p_mle()` |
| **피팅 방법 선택** | MLE / LS / RRX / RRY 선택 가능 | MLE만 지원 |
| **reliability 패키지** | ✅ 필수 의존 | ❌ 미사용 |
| **최적화 엔진** | reliability 내부 (scipy 기반) | 직접 구현 (Nelder-Mead → BFGS) |
| **신뢰구간** | reliability에서 자동 제공 | 수동 계산 (헤시안 역행렬) |

**영향**: Mode 1에서 `Fit_Weibull_2P`를 사용하면 β, α 값이 미세하게 다를 수 있음 (최적화 알고리즘 차이). Mode 2/3의 LRT/ALT는 동일한 `ev_group_nll` 기반이므로 결과 동일.

### 3.2 그래프 시스템

| 항목 | Streamlit 버전 | FastAPI 버전 |
|------|---------------|-------------|
| **그래프 렌더링** | `st.pyplot(fig)` (서버 사이드) | Base64 PNG → `<img>` 태그 (클라이언트) |
| **Mode 1 그래프** | `plot_weibull_probability()` + `plot_cumulative_failure()` + `plot_reliability_curve()` | `plot_weibull_probability()` + `plot_cumulative_hazard()` + `plot_reliability_function()` |
| **Mode 2 그래프** | 인라인 matplotlib 코드 (4개 탭) | 별도 함수 4개 (`plot_lrt_*`) |
| **Mode 3 수명예측** | Arrhenius Plot + Voltage-Life Plot (2개) | Arrhenius + Contour + Voltage-Life + 가속계수 2개 (5개) |
| **사용온도/전압 마커** | ❌ | ✅ 빨간 별표(★) + 수직 점선 |
| **가속계수 그래프** | ❌ | ✅ ln(MTTF) vs 1/(kT), ln(MTTF) vs ln(V) |
| **Contour 그래프** | ❌ | ✅ 온도+전압 등고선 |
| **축 범위 조절** | number_input (Streamlit 위젯) | HTML input (프론트엔드) |
| **그래프 함수 분리** | Mode 1만 함수화, Mode 2/3은 인라인 | 전체 함수화 (12개 plot 함수) |

### 3.3 데이터 입력

| 항목 | Streamlit 버전 | FastAPI 버전 |
|------|---------------|-------------|
| **Excel 붙여넣기** | ✅ `st.text_area` | ✅ `<textarea>` |
| **표 입력 (data_editor)** | ✅ `st.data_editor` (셀 편집) | ❌ (그룹별 input 필드) |
| **파일 업로드** | ✅ `st.file_uploader` (.xlsx) | ❌ |
| **EDMS 자동 로딩** | ✅ win32com → EDMS URL 파싱 | ❌ |
| **NASCA Excel 로드** | ✅ openpyxl 기반 | ❌ |
| **가속계수 표 생성** | ✅ Minitab용 스택 테이블 | ❌ |
| **데이터 입력 탭** | 4개 (붙여넣기/표/파일/자동) | 1개 (붙여넣기 + 그룹 입력) |

### 3.4 UI/UX

| 항목 | Streamlit 버전 | FastAPI 버전 |
|------|---------------|-------------|
| **모드 전환** | 사이드바 라디오 버튼 | 상단 탭 버튼 |
| **결과 표시** | `st.dataframe`, `st.metric`, `st.expander` | HTML 테이블, 카드 UI |
| **이상점 제거 UI** | `st.data_editor` (행 삭제) | 별도 UI (삭제 버튼) |
| **Bx 수명 선택** | `st.multiselect` (다중 선택) | 고정 (B1, B10 등) |
| **피팅 방법 선택** | MLE/LS/RRX/RRY | MLE만 |
| **반응형 디자인** | Streamlit 기본 | 커스텀 CSS |
| **한글 폰트** | Streamlit 서버 설정 필요 | CSS 웹폰트 |

### 3.5 배포 및 실행 환경

| 항목 | Streamlit 버전 | FastAPI 버전 |
|------|---------------|-------------|
| **Python 패키지** | 10개 (streamlit, reliability, pywin32 등) | 8개 (fastapi, uvicorn 등, reliability 불필요) |
| **설치 스크립트** | `setup.bat` (venv 생성 + pip install) | 직접 실행 |
| **실행 스크립트** | `run.bat` | 명령어 직접 입력 |
| **Windows 의존성** | pywin32 (EDMS 연동용) | 없음 |
| **외부 의존성** | reliability 패키지 필수 | 없음 (순수 Python) |
| **포터빌리티** | 낮음 (Windows + pywin32) | 높음 (크로스 플랫폼) |

---

## 4. 기능 매트릭스

| 기능 | Streamlit | FastAPI | 비고 |
|------|:---------:|:-------:|------|
| Weibull 2P 분석 | ✅ | ✅ | 피팅 엔진 다름 |
| LRT 동일 형상모수 검정 | ✅ | ✅ | 동일 알고리즘 |
| ALT 온도 가속 | ✅ | ✅ | 동일 알고리즘 |
| ALT 온도×전압 가속 | ✅ | ✅ | 동일 알고리즘 |
| 수명 추정 (MTTF, Bx) | ✅ | ✅ | 동일 수식 |
| 병렬 시스템 전처리 | ✅ | ✅ | 동일 로직 |
| Excel 붙여넣기 | ✅ | ✅ | 동일 파서 |
| 표 입력 (data_editor) | ✅ | ❌ | Streamlit 전용 |
| 파일 업로드 (.xlsx) | ✅ | ❌ | Streamlit 전용 |
| EDMS 연동 | ✅ | ❌ | Streamlit 전용 (win32com) |
| NASCA Excel 로드 | ✅ | ❌ | Streamlit 전용 |
| 피팅 방법 선택 | ✅ | ❌ | MLE만 |
| 이상점 제거 | ✅ | ✅ | UI 다름 |
| 가속계수 그래프 | ❌ | ✅ | FastAPI 전용 |
| Contour 그래프 | ❌ | ✅ | FastAPI 전용 |
| 사용온도/전압 마커 | ❌ | ✅ | FastAPI 전용 |
| 그래프 축 범위 조절 | ✅ | ✅ | UI 다름 |
| 다중 사용자 | ❌ | ✅ | FastAPI 장점 |
| REST API | ❌ | ✅ | FastAPI 장점 |
| 가속계수 표 생성 | ✅ | ❌ | Streamlit 전용 |
| Bx 멀티셀렉트 | ✅ | ❌ | Streamlit 전용 |

---

## 5. 코드 구조 비교

### Streamlit 버전 (단일 파일)

```
reliability_app.py (2,772줄)
├── L1~29:     Imports
├── L30~83:    setup_weibull_axes()
├── L84~93:    format_float_full()
├── L95~105:   prepare_data_for_editor()
├── L107~120:  extract_log_likelihood()
├── L122~134:  ev_group_nll()
├── L136~152:  get_edms_sample_data()
├── L154~186:  read_edms_url()
├── L188~238:  read_nasca_excel()
├── L240~264:  preprocess_parallel_systems()
├── L266~306:  minitab_lrt_test()
├── L308~380:  minitab_alt_temp_only()
├── L382~506:  minitab_alt_temp_volt()
├── L508~516:  make_col_names()
├── L518~531:  groups_to_data_df()
├── L533~538:  build_empty_data_df()
├── L540~609:  parse_excel_paste()
├── L611~635:  table_to_groups()
├── L637~681:  generate_stacked_table() / generate_paste_text()
├── L683~831:  load_excel_file() / parse_weibull_sheet()
├── L833~903:  parse_stack_sheet()
├── L905~960:  plot_weibull_probability()
├── L962~975:  plot_cumulative_failure()
├── L977~990:  plot_reliability_curve()
├── L992~1050:  show_stacked_dialog()
├── L1052~1400: Mode 1 UI (기본 와이블 분석)
├── L1402~1679: Mode 1 결과 + 그래프
├── L1682~2076: Mode 2/3 UI + 데이터 입력
├── L2077~2226: Mode 2/3 분석 실행 + LRT 결과
├── L2228~2475: Mode 2/3 Weibull 확률도 그래프 (인라인)
└── L2476~2772: Mode 3 수명 예측 그래프 (인라인)
```

### FastAPI 버전 (멀티 파일)

```
reliability_web/
├── main.py (946줄)
│   ├── Imports + 유틸리티 (safe_json, clean_result)
│   ├── Pydantic 데이터 모델 (6개)
│   ├── API 엔드포인트 (7개)
│   └── 정적 파일 서빙
├── core/
│   ├── weibull.py (478줄)
│   │   ├── weibull_2p_mle()        ← 순수 Python MLE
│   │   ├── ev_group_nll()
│   │   ├── preprocess_parallel_systems()
│   │   ├── minitab_lrt_test()
│   │   ├── minitab_alt_temp_only()
│   │   ├── minitab_alt_temp_volt()
│   │   ├── parse_excel_paste()
│   │   └── table_to_groups()
│   └── plotting.py (960줄)
│       ├── plot_weibull_probability()
│       ├── plot_cumulative_hazard()
│       ├── plot_reliability_function()
│       ├── plot_lrt_weibull_individual()
│       ├── plot_lrt_weibull_common()
│       ├── plot_lrt_cdf()
│       ├── plot_lrt_reliability()
│       ├── plot_alt_arrhenius()
│       ├── plot_alt_volt_life()
│       ├── plot_alt_volt_contour()
│       ├── plot_accel_temp()
│       └── plot_accel_volt()
└── static/
    ├── index.html (34,865 bytes)
    ├── css/style.css (10,366 bytes)
    └── js/app.js (69,035 bytes)
```

---

## 6. 수치 결과 비교

### 6.1 동일한 결과가 나오는 분석

| 분석 | 이유 |
|------|------|
| **LRT 검정** | 동일한 `ev_group_nll` + `minitab_lrt_test` 사용 |
| **ALT 회귀** | 동일한 `minitab_alt_temp_only` / `minitab_alt_temp_volt` 사용 |
| **수명 추정** | 동일한 수식 (MTTF, Bx) |
| **가속계수** | 동일한 Arrhenius/Power 모델 |

### 6.2 미세한 차이가 발생할 수 있는 분석

| 분석 | Streamlit | FastAPI | 차이 원인 |
|------|-----------|---------|----------|
| **Mode 1 Weibull 2P** | `Fit_Weibull_2P` | `weibull_2p_mle()` | 최적화 알고리즘 차이 |
| **Mode 2/3 개별 β** | `Fit_Weibull_2P` | `weibull_2p_mle()` | 최적화 알고리즘 차이 |

> **차이 수준**: β·α는 소수점 3~4째 자리, MTTF·Bx는 소수점 1~2째 자리 수준

### 6.3 `sm.add_constant` vs `np.column_stack` 차이

```python
# Streamlit 버전
X_reg = sm.add_constant(df[['Minitab_Temp']]).values

# FastAPI 버전
X_reg = np.column_stack([np.ones(len(df)), df[['Minitab_Temp']].values])
```

> 수학적으로 동일한 결과. `sm.add_constant`는 내부적으로 `np.column_stack([np.ones, X])`와 동일.

---

## 7. 장단점 비교

### Streamlit 버전

| 장점 | 단점 |
|------|------|
| 빠른 프로토타이핑 | 단일 사용자만 접속 가능 |
| `data_editor`로 직관적 데이터 편집 | reliability 패키지 의존 |
| EDMS/NASCA 연동 | Windows 전용 (pywin32) |
| 파일 업로드 간편 | 그래프 코드가 인라인 (유지보수 어려움) |
| 피팅 방법 선택 (MLE/LS/RRX/RRY) | 배포 시 venv 설정 필요 |
| Bx 수명 멀티셀렉트 | Streamlit 서버 리소스 사용量大 |

### FastAPI 버전

| 장점 | 단점 |
|------|------|
| 다중 사용자 동시 접속 | 프론트엔드 수동 작성 (공수 큼) |
| REST API로 타 시스템 연동 가능 | data_editor 없음 |
| reliability 패키지 불필요 | 파일 업로드 미구현 |
| 크로스 플랫폼 (Linux/Mac) | EDMS 연동 없음 |
| 그래프 함수 분리 (유지보수 용이) | 피팅 방법 MLE만 |
| 가속계수/Contour 그래프 추가 | Bx 멀티셀렉트 없음 |
| 사용온도/전압 마커 표시 | 표 입력 UI 미흡 |

---

## 8. 마이그레이션 시 고려사항

### Streamlit → FastAPI 마이그레이션 필요 작업

| 기능 | 난이도 | 비고 |
|------|--------|------|
| `data_editor` → HTML 테이블 편집 | 🔴 높음 | 상당한 JS 작업 필요 |
| 파일 업로드 | 🟡 중간 | FastAPI `UploadFile` 사용 |
| EDMS 연동 | 🔴 높음 | win32com → API/브라우저 자동화 |
| 피팅 방법 선택 | 🟢 낮음 | `weibull_2p_mle`에 LS/RRX 모드 추가 |
| Bx 멀티셀렉트 | 🟢 낮음 | 프론트엔드 체크박스 추가 |

### FastAPI → Streamlit 마이그레이션 필요 작업

| 기능 | 난이도 | 비고 |
|------|--------|------|
| 가속계수 그래프 | 🟢 낮음 | 인라인 matplotlib 코드 추가 |
| Contour 그래프 | 🟡 중간 | matplotlib contour 코드 추가 |
| 사용온도/전압 마커 | 🟢 낮음 | scatter + axvline 추가 |
| 그래프 함수 분리 | 🟡 중간 | 인라인 코드 → 함수 추출 |
