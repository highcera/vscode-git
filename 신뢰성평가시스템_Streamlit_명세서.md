# 신뢰성 평가 시스템 (Streamlit 버전) — 전체 명세서

> **버전**: v1.0 (2026-08-06)  
> **기준 파일**: `D:\SEMCoWork\reliability_deploy\reliability_app.py` (155,423 bytes, 2,772 lines)  
> **목적**: 처음부터 동일한 Streamlit 앱을 재구축할 수 있는 완전 명세서

---

## 1. 프로젝트 개요

### 1.1 기술 스택
| 항목 | 내용 |
|------|------|
| **프레임워크** | Streamlit ≥ 1.28.0 |
| **언어** | Python 3.10+ |
| **파일 구조** | 단일 파일 (`reliability_app.py`) |
| **실행** | `streamlit run reliability_app.py` |
| **포트** | 기본 8501 |

### 1.2 디렉토리 구조
```
reliability_deploy/
├── reliability_app.py    # 메인 앱 (2,772 lines)
├── requirements.txt      # 패키지 의존성
├── setup.bat             # venv 생성 + 패키지 설치 스크립트
├── run.bat               # 실행 스크립트
└── README.md             # 사용 안내
```

### 1.3 필수 패키지 (requirements.txt)
```
streamlit>=1.28.0
numpy>=1.24.0
pandas>=2.0.0
matplotlib>=3.7.0
scipy>=1.10.0
statsmodels>=0.14.0
openpyxl>=3.1.0
reliability>=0.9.0
pywin32>=305
requests>=2.31.0
```

### 1.4 실행 방법
```bash
# 방법 1: 직접 실행
streamlit run reliability_app.py

# 방법 2: venv 사용 (setup.bat 후)
call venv\Scripts\activate.bat
streamlit run reliability_app.py

# 방법 3: run.bat
run.bat
```

---

## 2. 앱 전체 구조

### 2.1 사이드바
```
📊 신뢰성 평가 시스템
─────────────────────
분석 모드 선택 (radio):
  🔧 기본 와이블 분석        → Mode 1
  ✅ 가속성 (동일 형상모수) 검정 → Mode 2
  📊 온도, 전압 가속계수 산출   → Mode 3
─────────────────────
📋 고장/중단 코드
  - 1 = 고장 (Failure)
  - 0 = 중단/생존 (Censored)
```

### 2.2 메인 영역 — 모드별 구성

| 모드 | 제목 | 데이터 입력 | 분석 | 그래프 |
|------|------|------------|------|--------|
| Mode 1 | 🔧 기본 와이블 분석 | 4개 탭 | Weibull 2P 피팅 | 3개 탭 |
| Mode 2 | ✅ 가속성 (동일 형상모수) 검정 | 4개 탭 | LRT 검정 + Weibull | 4개 탭 |
| Mode 3 | 📊 온도, 전압 가속계수 산출 | 4개 탭 | ALT 회귀 + Weibull | 4개 탭 |

---

## 3. 데이터 입력 (공통 — 3개 모드 모두 동일)

### 3.1 입력 탭 구조
```python
tab_paste, tab_excel, tab_file, tab_auto = st.tabs([
    "📋 Excel 전체 붙여넣기",   # Tab 1: 텍스트 붙여넣기
    "📊 표 입력 (Excel 형식)",  # Tab 2: data_editor
    "📁 파일 업로드",           # Tab 3: 파일 업로드
    "🔗 자동 로딩"              # Tab 4: EDMS/NASCA 자동 로딩
])
```

### 3.2 Excel 붙여넣기 형식

**2가지 양식을 자동 감지**하여 파싱한다.

#### 양식 1: 조건행 양식 (기존)
Temp/Volt/병렬수 3행 + 헤더 + 데이터 행 구조.
```
Temp    100     125     150
Volt    3.3     3.3     3.3
병렬수   1       1       1
No.     T_100_3.3  C_100_3.3  T_125_3.3  C_125_3.3  T_150_3.3  C_150_3.3
1       8.6      1         19.9       1         24.2       1
2       137      0         137        0         137        0
...
```

- **1행**: 온도 (Temp, °C)
- **2행**: 전압 (Volt, V)
- **3행**: 병렬수 (채널당 부품 수)
- **4행**: 열 이름 (No., T_xxx_x, C_xxx_x)
- **5행~**: 데이터 (T = 시간, C = 고장/중단 코드)

#### 양식 2: 열이름 양식 (신규)
열 이름에 온도/전압이 포함된 단일 헤더 + 데이터 행 구조. Temp/Volt/병렬수 행 없이 열 이름에서 조건을 자동 추출.
```
	  T_125_5.5  C_125_5.5  T_135_5.5  C_135_5.5  T_145_5.5  C_145_5.5
1   54.1       1.0         24.8       1.0         4.7        1.0
2   67.6       1.0         35.7       1.0         15.4       1.0
3   89.4       1.0         38.2       1.0         16.9       1.0
...
40                                  (빈 셀 = NaN 유지)         43.0       1.0
```

- **1행**: 열 이름만 (`T_{온도}_{전압}`, `C_{온도}_{전압}` 형식)
- **2행~**: 데이터 (T = 시간, C = 고장/중단 코드)
- **빈 셀**: NaN으로 유지 (열 정렬 보존)
- **병렬수**: 기본값 1 (별도 행 없음)

#### 자동 감지 규칙
1. 첫 번째 행의 셀 중 `T_{숫자}_{숫자}` 패턴이 하나라도 있으면 → **양식 2** (열이름 양식)
2. 그 외 → **양식 1** (조건행 양식)

#### 파싱 규칙 (공통)
- 빈 셀은 NaN으로 유지 (열 정렬 보존)
- `T_` 열 = 시간 데이터, `C_` 열 = 고장(1)/중단(0) 코드
- 열 이름에서 온도/전압을 추출하여 조건으로 사용

### 3.3 표 입력 (data_editor)
- `st.data_editor`로 조건 테이블 + 데이터 테이블 편집
- 조건 테이블: Temp, Volt, 병렬수
- 데이터 테이블: T_xxx_x, C_xxx_x 열

### 3.4 파일 업로드
- `.xlsx` 파일 업로드
- 시트 자동 감지: '와이블_가속성' → '가속계수' → 첫 번째 시트
- `load_excel_file(uploaded_file)` 함수로 파싱

### 3.5 자동 로딩 (EDMS/NASCA)
- EDMS 샘플 데이터 로딩
- NASCA Excel 파일 읽기 (`read_nasca_excel`)
- EDMS URL에서 데이터 읽기 (`read_edms_url`)

---

## 4. Mode 1: 기본 와이블 분석

### 4.1 설정
| 항목 | 위젯 | 기본값 | key |
|------|------|--------|-----|
| 채널당 병렬 부품 수 | `st.number_input` | 1 | `ppc` |
| 피팅 방법 | `st.selectbox` | "MLE" | `fit_method` |
| | 옵션: MLE, LS, RRX, RRY | | |

> **Bx 수명 기준 (%)** 입력창은 제거됨. B0.4329 (0.4329%) 수명을 고정값으로 산출.

### 4.2 분석 로직
```python
# 1. table_to_groups() → 그룹 리스트
# 2. 각 그룹별:
#    a. 병렬 채널 분해 (ppc > 1 시)
#    b. Fit_Weibull_2P(failures, right_censored)  # reliability 패키지
#    c. β, α, MTTF, B0.1, B0.4329, B1 계산
# 3. 결과를 session_state['wp_results']에 저장
```

### 4.3 결과 표시
1. **조건별 분석 결과 테이블** (단일 테이블, 중복 테이블 제거됨):

| 조건 | β (형상모수) | α (척도모수) | B0.1 (h) | B0.4329 (h) | B1 (h) | MTTF (h) | 고장수 | 중단수 |
|------|------------|------------|----------|-------------|--------|----------|--------|--------|

   - B0.1: 0.1% 수명 (고정)
   - B0.4329: 0.4329% 수명 (고정, 입력창 없음)
   - B1: 1% 수명 (고정)
   - MTTF: 평균수명

2. **조건별 상세 결과** (expander): β, α, 신뢰구간, 로그우도, AIC, BIC
3. **그래프** (3개 탭):
   - 와이블 확률도 (`plot_weibull_probability`)
   - 누적 고장률 (`plot_cumulative_failure`)
   - 신뢰도 곡선 (`plot_reliability_curve`)

### 4.4 그래프 축 범위 설정
- X축 최소/최대 (Time, log 스케일)
- Y축 최소/최대 (F %, Weibull 확률 스케일)
- 자동 범위: `10^floor(log10(min))` ~ `10^ceil(log10(max))`

---

## 5. Mode 2: 가속성 (동일 형상모수) 검정

### 5.1 설정
| 항목 | 위젯 | 기본값 | key |
|------|------|--------|-----|
| 유의수준 α | `st.number_input` | 0.05 | `alpha_m2` |

### 5.2 분석 로직
```python
# 1. table_to_groups() → 그룹 리스트
# 2. 각 그룹별 개별 Weibull 2P 피팅 (Fit_Weibull_2P)
# 3. minitab_lrt_test(df_clean, groups) → LRT 검정
#    - 개별 β 모델 (Unconstrained) NLL
#    - 공통 β 모델 (Constrained) NLL
#    - LR 통계량 = 2 × (ll_unconstrained - ll_constrained)
#    - p-value = 1 - chi2.cdf(LR, df)
# 4. 결과: p_value, LR_statistic, conclusion
```

### 5.3 LRT 검정 결과
| 항목 | 설명 |
|------|------|
| p-value | 유의확률 |
| LR 통계량 | 우도비 통계량 |
| 자유도 | 그룹 수 - 1 |
| 결론 | p < α → "기각 (형상모수가 동일하지 않음)" |

### 5.4 이상점 제거 기능
- 각 조건별 데이터를 시간 오름차순으로 `st.data_editor`에 표시
- 사용자가 이상점 행 삭제 후 "이상점 제거 후 재분석" 버튼 클릭
- "원본 데이터로 복원" 버튼으로 원래 데이터 복구
- `session_state['outlier_groups']`에 제거 후 데이터 저장
- 자동 재분석 옵션 (`auto_reanalyze`)

### 5.5 그래프 (4개 탭)
1. **개별 β Weibull 확률도**: 각 조건별 개별 피팅 라인
2. **공통 β Weibull 확률도**: LRT 검정 결과의 공통 β(`beta_common`)를 사용하여 재피팅한 라인
   - 공통 β가 0이면 개별 β의 중앙값(median)으로 fallback
3. **누적 고장률 (CDF)**: 각 조건별 CDF 곡선 (공통 β 반영)
4. **신뢰도 곡선**: 각 조건별 신뢰도 곡선 (공통 β 반영)

### 5.6 그래프 축 범위 설정
- X축 최소/최대 (Time)
- Y축 최소/최대 (F %)
- 자동 범위 계산 후 number_input으로 조절 가능

---

## 6. Mode 3: 온도, 전압 가속계수 산출

### 6.1 설정
| 항목 | 위젯 | 기본값 | key |
|------|------|--------|-----|
| 사용 조건 온도 (°C) | `st.number_input` | 105 | `use_temp` |
| 사용 조건 전압 (V) | `st.number_input` | 4.0 | `use_volt` |
| Bx 수명 기준 (%) | `st.multiselect` | [1, 10, 50] | `bx3` |

### 6.2 분석 로직
```python
# 1. table_to_groups() → 그룹 리스트
# 2. 각 그룹별 개별 Weibull 2P 피팅
# 3. ALT 유형 자동 판단:
#    - 온도만 다름 → minitab_alt_temp_only()
#    - 전압만 다름 → minitab_alt_temp_volt()
#    - 둘 다 다름 → minitab_alt_temp_volt()
# 4. 회귀 결과: Ea, n_exp, est_intercept, shape
# 5. 사용 조건에서의 수명 추정: η_use, MTTF_use, B10_use, B1_use
```

### 6.3 ALT 회귀 결과
| 항목 | 설명 |
|------|------|
| 절편 (β₀) | est_intercept |
| 온도계수 (β₁) | Ea (활성화에너지, eV) |
| 전압계수 (β₂) | -n_exp (전압지수) |
| 형상모수 (β) | Weibull shape parameter |
| 사용조건 η | 사용 온도/전압에서의 특성수명 |
| 사용조건 MTTF | 평균수명 |
| 가속계수 테이블 | 조건별 AF (Acceleration Factor) |

### 6.4 그래프 (4개 탭)
1. **수명 예측**:
   - Minitab 스타일 Arrhenius Plot (°C 축)
   - Minitab 스타일 Voltage-Life Plot
   - Life Prediction Contour (Temp × Volt) — 온도+전압 모두 다중 조건일 때만 표시
2. **개별 β Weibull 확률도**
3. **공통 β Weibull 확률도**: ALT 분석 결과의 공통 β(`shape`)를 사용하여 재피팅
   - 공통 β가 0이면 개별 β의 중앙값(median)으로 fallback
4. **누적 고장률 (CDF)**: 공통 β 반영

### 6.5 Arrhenius Plot 상세
- X축: 온도 (°C, 선형 스케일)
- Y축: 특성수명 η (log 스케일)
- 각 전압별 데이터 포인트 + fitting line
- 사용 조건 온도에 수직 점선
- 사용 조건에서의 예측 수명 표시

### 6.6 Voltage-Life Plot 상세
- X축: 전압 (V, log 스케일)
- Y축: 특성수명 η (log 스케일)
- 각 온도별 데이터 포인트 + fitting line
- 시험 전압 구간: 실선
- 사용 전압 구간: 점선 (외삽)
- 사용 조건에서의 예측 수명 표시

### 6.7 그래프 조건부 표시
| 그래프 | 온도만 다름 | 전압만 다름 | 온도+전압 모두 다름 |
|--------|------------|------------|-------------------|
| 가속계수 ln(MTTF) vs 1/(kT) | ✅ 표시 | ❌ 숨김 | ✅ 표시 |
| Arrhenius Plot | ✅ 표시 | ❌ 숨김 | ✅ 표시 |
| 가속계수 ln(MTTF) vs ln(V) | ❌ 숨김 | ✅ 표시 | ✅ 표시 |
| Voltage-Life Plot | ❌ 숨김 | ✅ 표시 | ✅ 표시 |
| Contour (Temp×Volt) | ❌ 숨김 | ❌ 숨김 | ✅ 표시 |

- Contour는 온도와 전압이 **모두** 2종류 이상일 때만 표시

### 6.8 그래프 x축 자동 범위
| 그래프 | x축 | 자동 범위 |
|--------|-----|----------|
| Arrhenius Plot | 온도(°C) | `min(시험온도, 사용온도) - 10` ~ `max(시험온도, 사용온도) + 10` |
| Voltage-Life Plot | 전압(V) | `min(시험전압, 사용전압) × 0.8` ~ `max(시험전압, 사용전압) × 1.2` |
| Contour (Temp×Volt) | 온도(°C) | Arrhenius와 동일 |

- 사용온도/사용전압이 항상 그래프 범위에 포함되도록 자동 계산

---

## 7. 핵심 함수 명세

### 7.1 데이터 처리 함수

#### `parse_excel_paste(text)`
```
입력: Excel에서 복사한 탭 구분 텍스트
출력: (conditions_df, data_df) 또는 (None, None)
로직:
  1. 줄바꿈으로 분할, 빈 줄 제거
  2. 1행: 온도 값 파싱
  3. 2행: 전압 값 파싱
  4. 3행: 병렬수 파싱
  5. 4행: 열 이름 (No., T_xxx_x, C_xxx_x)
  6. 5행~: 데이터 파싱 (빈 셀 → NaN)
  7. conditions_df: Temp(°C), Volt(V), 병렬수
  8. data_df: T_xxx_x, C_xxx_x 열
```

#### `table_to_groups(conditions_df, data_df, raw_data_df=None)`
```
입력: 조건 DataFrame, 데이터 DataFrame, 원본 정밀도 DataFrame
출력: [{temp_c, volt, 병렬수, durations, events}, ...]
로직:
  1. raw_data_df가 있으면 원본 정밀도 사용
  2. 각 조건별 T_xxx_x, C_xxx_x 열에서 데이터 추출
  3. NaN 제거 후 durations, events 리스트 생성
```

#### `preprocess_parallel_systems(df_stack)`
```
입력: DataFrame (Temp, Volt, Time, Censoring, System_ID?)
출력: 전처리된 DataFrame
로직:
  1. System_ID 열이 없으면 원본 그대로 반환
  2. (Temp, Volt, System_ID) 그룹별:
     - 고장이 있으면: 최소 고장시간 1개만 고장(1), 나머지 중단(0)
     - 고장이 없으면: 최대 시간에 전부 중단(0)
```

#### `make_col_names(conditions_df)`
```
입력: 조건 DataFrame (Temp, Volt)
출력: ['T_100_3.3', 'C_100_3.3', 'T_125_3.3', ...]
로직: f"T_{temp}_{volt_int}", f"C_{temp}_{volt_int}" 형식
```

#### `groups_to_data_df(groups, conditions_df)`
```
입력: 그룹 리스트, 조건 DataFrame
출력: data_df (이상점 제거 후 동기화용)
```

#### `build_empty_data_df(col_names, n_rows=40)`
```
입력: 열 이름 리스트, 행 수
출력: 빈 데이터 DataFrame (NaN으로 채움)
```

#### `generate_stacked_table(groups)`
```
입력: 그룹 리스트
출력: stacked DataFrame (Temp, Volt, Time, Censoring)
```

#### `generate_paste_text(cond_df, data_df)`
```
입력: 조건 DataFrame, 데이터 DataFrame
출력: Excel 붙여넣기용 텍스트 (탭 구분)
```

### 7.2 파일 로딩 함수

#### `load_excel_file(uploaded_file)`
```
입력: Streamlit UploadedFile (.xlsx)
출력: (cond_df, data_df) 또는 에러 메시지
로직:
  1. openpyxl로 워크북 로딩
  2. '와이블_가속성' 시트 → parse_weibull_sheet()
  3. '가속계수' 시트 → parse_stack_sheet()
  4. 첫 번째 시트 fallback
```

#### `parse_weibull_sheet(xls_or_wb, sheet_name='와이블_가속성')`
```
입력: Excel 워크북/파일경로, 시트명
출력: (cond_df, data_df)
로직:
  1. 시트 읽기
  2. 조건행 파싱 (Temp, Volt, 병렬수)
  3. 데이터행 파싱
```

#### `parse_stack_sheet(xls_or_wb, sheet_name='가속계수')`
```
입력: Excel 워크북/파일경로, 시트명
출력: (cond_df, data_df)
로직: stacked 형식 → 조건별로 분해
```

### 7.3 EDMS/NASCA 함수

#### `get_edms_sample_data()`
```
출력: 샘플 DataFrame (EDMS 형식)
```

#### `read_edms_url(url)`
```
입력: EDMS 데이터 URL
출력: DataFrame
로직: requests로 CSV/Excel 다운로드 후 파싱
```

#### `read_nasca_excel(filepath)`
```
입력: NASCA Excel 파일 경로
출력: DataFrame
로직: win32com.client (Outlook/Excel COM)으로 파일 읽기
```

### 7.4 통계 분석 함수

#### `weibull_2p_mle(failures, right_censored=None)` (reliability 패키지 래핑)
```
Streamlit 버전에서는 Fit_Weibull_2P()를 직접 사용:
  wb = Fit_Weibull_2P(failures=failures, right_censored=censored)
  beta = wb.beta
  alpha = wb.alpha
```

#### `ev_group_nll(params, y, censor)`
```
입력: params=[mu, ln_sigma], y=로그시간, censor=중단여부
출력: 음의 로그우도 (극치분포 기반)
용도: LRT 검정의 개별/공통 β 모델 피팅
```

#### `minitab_lrt_test(df_clean, groups)`
```
입력: DataFrame (Log_Time, Censoring, Group), 그룹명 리스트
출력: {p_value, LR_statistic, degrees_of_freedom, ll_unconstrained, ll_constrained, beta_common, conclusion}
로직:
  1. 개별 β 모델: 각 그룹별 ev_group_nll 최적화 → NLL 합
  2. 공통 β 모델: shared_shape_total_nll 최적화 → NLL
  3. LR = 2 × (ll_uncon - ll_con)
  4. p = 1 - chi2.cdf(LR, df = n_groups - 1)
  5. conclusion: p < α → "기각", else → "채택"
```

#### `minitab_alt_temp_only(df_clean, use_temp_c)`
```
입력: DataFrame, 사용온도(°C)
출력: {success, intercept, temp_coef, shape, Ea, eta_use, MTTF_use, reg_table, res_reg}
로직:
  1. Minitab_Temp = 11604.83 / (T + 273.15)
  2. X = [1, Minitab_Temp], y = Log_Time
  3. MLE 회귀 (극치분포 NLL 최소화)
  4. Ea = temp_coef
  5. 사용온도에서 η, MTTF 추정
```

#### `minitab_alt_temp_volt(df_clean, use_temp_c, use_volt, fixed_shape=None)`
```
입력: DataFrame, 사용온도, 사용전압, 고정 형상모수(옵션)
출력: {success, intercept, temp_coef, volt_coef, shape, Ea, n_exp, eta_use, MTTF_use, B10_use, reg_table, af_table, res_reg}
로직:
  1. Minitab_Temp = 11604.83 / (T + 273.15)
  2. Minitab_Volt = ln(V)
  3. X = [1, Minitab_Temp, Minitab_Volt], y = Log_Time
  4. MLE 회귀 (fixed_shape 있으면 β 고정)
  5. Ea = temp_coef, n_exp = -volt_coef
  6. 사용조건에서 η, MTTF, B10 추정
  7. 가속계수(AF) 테이블 생성
```

### 7.5 그래프 함수

#### `setup_weibull_axes(ax, log_min, log_max, lnln_min, lnln_max, f_min, f_max, f_to_lnln_func)`
```
입력: matplotlib axes, 축 범위, 변환 함수
출력: 설정된 axes
로직:
  1. X축: log 스케일 (시간)
  2. Y축: Weibull 확률 스케일 (ln(-ln(1-F)) → F% 변환)
  3. 그리드, 라벨 설정
```

#### `plot_weibull_probability(failures, right_censored=None, title="Weibull Probability Plot", fit_method='MLE')`
```
입력: 고장시간, 중단시간, 제목, 피팅 방법
출력: matplotlib Figure
로직:
  1. plotting_positions(failures, right_censored, a=0.3) → (x_pp, y_pp)
  2. ln_t = log(x_pp), ln_ln = log(-log(1 - y_pp))
  3. 산점도 표시
  4. Fit_Weibull_2P → fitting line
  5. setup_weibull_axes()로 축 설정
```

#### `plot_cumulative_failure(wb_model, max_time=None, title="누적 고장률 곡선")`
```
입력: Fit_Weibull_2P 결과 객체, 최대 시간
출력: matplotlib Figure
로직:
  1. CDF = 1 - exp(-(t/α)^β)
  2. X축: 시간 (log 스케일)
  3. Y축: 0~100%
```

#### `plot_reliability_curve(wb_model, max_time=None, title="신뢰도 곡선")`
```
입력: Fit_Weibull_2P 결과 객체, 최대 시간
출력: matplotlib Figure
로직:
  1. R(t) = exp(-(t/α)^β)
  2. X축: 시간 (log 스케일)
  3. Y축: 0~100%
```

### 7.6 유틸리티 함수

#### `format_float_full(x)`
```
입력: float
출력: 전체 정밀도 문자열 (소수점 이하 자릿수 보존)
```

#### `prepare_data_for_editor(data_df)`
```
입력: DataFrame
출력: data_editor용 DataFrame (정렬된 열 순서)
```

#### `extract_log_likelihood(model_object)`
```
입력: Fit_Weibull_2P 결과 객체
출력: 로그우도 값
```

#### `show_stacked_dialog(stacked_df)`
```
입력: stacked DataFrame
출력: st.dataframe 다이얼로그 표시
```

---

## 8. Session State 키

| 키 | 타입 | 용도 |
|----|------|------|
| `analysis_mode` | str | 현재 선택된 분석 모드 |
| `cond_df` | DataFrame | 조건 테이블 |
| `data_df` | DataFrame | 데이터 테이블 |
| `raw_data_df` | DataFrame | 원본 정밀도 데이터 |
| `data_version` | int | 데이터 변경 카운터 |
| `analysis_groups` | list | 분석용 그룹 리스트 |
| `wp_results` | list | Mode 1 분석 결과 |
| `wp_bx_pct` | float | Mode 1 Bx 기준 |
| `analysis_ind_results` | list | Mode 2/3 개별 피팅 결과 |
| `outlier_groups` | list | 이상점 제거 후 그룹 |
| `original_data_df_backup` | DataFrame | 이상점 제거 전 원본 data_df |
| `original_raw_data_df_backup` | DataFrame | 이상점 제거 전 원본 raw_data_df |
| `outlier_version` | int | 이상점 제거 버전 카운터 |
| `auto_reanalyze` | bool | 이상점 제거 후 자동 재분석 여부 |
| `_prev_analysis_mode` | str | 이전 분석 모드 (변경 감지용) |
| `edms_sample_loaded` | bool | EDMS 샘플 로딩 여부 |
| `edms_sample_df` | DataFrame | EDMS 샘플 데이터 |
| `df_weibull` | DataFrame | Weibull 시트 데이터 |
| `col_names` | list | 열 이름 리스트 |

---

## 9. 핵심 수식

### 9.1 Weibull 2모수 분포
\[
f(t) = \frac{\beta}{\alpha}\left(\frac{t}{\alpha}\right)^{\beta-1} \exp\left[-\left(\frac{t}{\alpha}\right)^{\beta}\right]
\]

### 9.2 수명 지표
\[
\text{MTTF} = \alpha \cdot \Gamma\left(1 + \frac{1}{\beta}\right)
\]
\[
B_x = \alpha \cdot \left(-\ln\left(1 - \frac{x}{100}\right)\right)^{1/\beta}
\]

### 9.3 Arrhenius 가속 모델
\[
\ln(\eta) = \beta_0 + \beta_1 \cdot \frac{11604.83}{T + 273.15}
\]
- \(\beta_1 = E_a\) (활성화에너지, eV)
- \(11604.83 = 1/k_B\) (Boltzmann 상수 역수)

### 9.4 Arrhenius + Power 가속 모델
\[
\ln(\eta) = \beta_0 + E_a \cdot \frac{11604.83}{T + 273.15} + (-n_{exp}) \cdot \ln(V)
\]

### 9.5 가속계수 (Acceleration Factor)
\[
AF = \frac{\eta_{stress}}{\eta_{use}} = \exp\left[E_a \cdot 11604.83 \left(\frac{1}{T_{use}} - \frac{1}{T_{stress}}\right) + n_{exp} \cdot \ln\left(\frac{V_{stress}}{V_{use}}\right)\right]
\]

### 9.6 LRT 검정 통계량
\[
LR = 2 \times (\ell_{unconstrained} - \ell_{constrained})
\]
\[
p = 1 - F_{\chi^2}(LR,\ df = k - 1)
\]
- \(k\): 그룹 수

---

## 9.5 한글 폰트 설정

### 9.5.1 폰트 설정 개요
모든 그래프의 한글 라벨, 제목, 범례가 깨지지 않도록 Malgun Gothic 폰트를 적용한다.

### 9.5.2 설정 코드
```python
import matplotlib
matplotlib.use('Agg')
import matplotlib.font_manager as fm

# Malgun Gothic 폰트 등록
font_path = 'C:/Windows/Fonts/malgun.ttf'
fm.fontManager.addfont(font_path)
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False
```

### 9.5.3 적용 범위
| 항목 | 적용 여부 |
|------|----------|
| 그래프 제목 | O |
| 축 라벨 | O |
| 범례 | O |
| 음수 부호 표시 | O (axes.unicode_minus = False) |

### 9.5.4 주의사항
- Malgun Gothic 폰트는 Windows 환경에서만 사용 가능
- 다른 OS에서는 해당 OS의 한글 폰트(Noto Sans CJK 등)로 대체 필요
- matplotlib.use('Agg')를 사용하여 GUI 백엔드 의존성 제거

---

## 10. Mode 1 vs Mode 2/3 그래프 차이

### 10.1 Mode 1 그래프 (reliability 패키지 직접 사용)
| 그래프 | 함수 | 피팅 방식 |
|--------|------|-----------|
| Weibull 확률도 | `plot_weibull_probability()` | `Fit_Weibull_2P` (reliability) |
| 누적 고장률 | `plot_cumulative_failure()` | `Fit_Weibull_2P` 결과 사용 |
| 신뢰도 곡선 | `plot_reliability_curve()` | `Fit_Weibull_2P` 결과 사용 |

### 10.2 Mode 2/3 그래프 (순수 matplotlib + Minitab 방식)
| 그래프 | 피팅 방식 | 특징 |
|--------|-----------|------|
| 개별 β Weibull 확률도 | `ev_group_nll` 최적화 | 각 조건별 개별 β |
| 공통 β Weibull 확률도 | `shared_shape_total_nll` 최적화 | LRT 공통 β 적용 |
| 누적 고장률 (CDF) | Weibull CDF 공식 | 공통 β 기반 |
| 신뢰도 곡선 | Weibull R(t) 공식 | 공통 β 기반 |
| Arrhenius Plot | `minitab_alt_temp_volt` 결과 | °C 축, log η 축 |
| Voltage-Life Plot | `minitab_alt_temp_volt` 결과 | log V 축, log η 축 |

---

## 11. 이상점 제거 기능 상세

### 11.1 동작 흐름
```
1. LRT 검정 완료 후 "이상점 제거" 섹션 표시
2. 각 조건별 데이터를 st.data_editor에 시간 오름차순 표시
3. 사용자가 이상점 행 삭제
4. "이상점 제거 후 재분석" 버튼 클릭
5. session_state['outlier_groups']에 수정된 데이터 저장
6. 자동 재분석 (auto_reanalyze=True 시) 또는 수동 실행
7. "원본 데이터로 복원" 버튼으로 원래 데이터 복구
```

### 11.2 백업/복원
```python
# 백업
st.session_state['original_data_df_backup'] = st.session_state['data_df'].copy()
st.session_state['original_raw_data_df_backup'] = st.session_state['raw_data_df'].copy()

# 복원
st.session_state['data_df'] = st.session_state['original_data_df_backup']
st.session_state['raw_data_df'] = st.session_state['original_raw_data_df_backup']
st.session_state['outlier_groups'] = None
```

---

## 12. 배포 스크립트

### 12.1 setup.bat
```batch
@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"

REM Python 설치 확인
python --version >nul 2>&1
if errorlevel 1 (
    echo [오류] Python이 설치되어 있지 않습니다.
    pause & exit /b 1
)

REM 기존 venv 제거
if exist "venv" rmdir /s /q venv

REM 가상환경 생성
python -m venv venv
call venv\Scripts\activate.bat

REM pip 업그레이드 + 패키지 설치
python -m pip install --upgrade pip
pip install -r requirements.txt

echo 설치 완료! run.bat으로 실행하세요.
pause
```

### 12.2 run.bat
```batch
@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"

if not exist "venv" (
    echo 가상환경이 없습니다. setup.bat을 먼저 실행하세요.
    pause & exit /b 1
)

call venv\Scripts\activate.bat
streamlit run reliability_app.py --server.port 8501
```

---

## 13. Streamlit 버전 vs FastAPI 웹 버전 차이점

| 항목 | Streamlit 버전 | FastAPI 웹 버전 |
|------|---------------|----------------|
| **파일 구조** | 단일 파일 (2,772 lines) | 다중 파일 (main.py + core/ + static/) |
| **프레임워크** | Streamlit | FastAPI + Uvicorn |
| **피팅 엔진** | `reliability` 패키지 (`Fit_Weibull_2P`) | 순수 Python MLE (`weibull_2p_mle`) |
| **그래프** | `st.pyplot()` (인터랙티브) | Base64 이미지 (정적) |
| **데이터 편집** | `st.data_editor` | HTML input 필드 |
| **이상점 제거** | data_editor에서 행 삭제 | 별도 UI |
| **EDMS/NASCA** | pywin32 COM 자동 로딩 | 미지원 |
| **파일 업로드** | `st.file_uploader` | 미지원 (Excel 붙여넣기만) |
| **Contour 그래프** | 미지원 | 지원 (`plot_alt_volt_contour`) |
| **가속계수 그래프** | 미지원 | 지원 (`plot_accel_temp`, `plot_accel_volt`) |
| **배포** | venv + batch 파일 | uvicorn 서버 |

---

## 14. 재구축 체크리스트

- [ ] `reliability_deploy/` 디렉토리 생성
- [ ] `requirements.txt` 작성 (10개 패키지)
- [ ] `reliability_app.py` 단일 파일 작성
  - [ ] Import 섹션 (L1~L28)
  - [ ] 유틸리티 함수 (L30~L120)
  - [ ] EDMS/NASCA 함수 (L136~L240)
  - [ ] 데이터 처리 함수 (L240~L680)
  - [ ] 파일 로딩 함수 (L683~L905)
  - [ ] 그래프 함수 (L905~L1030)
  - [ ] 사이드바 UI (L1030~L1052)
  - [ ] Mode 1 UI + 로직 (L1052~L1680)
  - [ ] Mode 2/3 UI + 로직 (L1680~L2772)
- [ ] `setup.bat` 작성
- [ ] `run.bat` 작성
- [ ] `README.md` 작성
- [ ] venv 생성 + 패키지 설치 테스트
- [ ] `streamlit run reliability_app.py` 실행 테스트
- [ ] Mode 1/2/3 각각 분석 테스트
- [ ] Excel 붙여넣기 테스트
- [ ] 이상점 제거 테스트
- [ ] 파일 업로드 테스트


---

## 12. 수정 이력

### 2026-08-07 (Streamlit 버전 반영)

이번 세션에서 FastAPI 웹 버전에 적용된 수정 사항 중 Streamlit 버전에도 해당하는 7개 항목을 반영했다.

| # | 수정 항목 | 반영 섹션 | 설명 |
|---|----------|----------|------|
| 4 | Contour 그래프 표시 조건 | 6.4 | 온도+전압 모델일 때만 Contour 그래프 표시, 단일 조건(온도만 또는 전압만)일 때는 관련 그래프 숨김 |
| 7 | Mode 3 x축 자동 범위 | 6.5, 6.6 | 각 그래프별로 데이터 범위에 맞춰 x축 자동 설정 (그래프마다 개별 범위 적용) |
| 8 | 한글 폰트 설정 | 9.5 | Malgun Gothic 폰트 적용으로 한글 라벨/제목/범례 깨짐 방지 |
| 9 | 공통 형상모수(β) 그래프 반영 | 5.5, 6.4 | Mode 2/3 그래프에서 공통 β로 재피팅한 결과가 그래프에 반영되도록 수정 |
| 10 | Mode 1 중복 테이블 제거 | 4.3 | 조건별 분석 결과 테이블 1개로 통합 (이전: 2개 중복 표시) |
| 11 | Mode 1 Bx 입력창 제거, B0.4329 고정 | 4.1, 4.2 | Bx 수명(%) 입력창 제거, B0.4329를 고정값으로 산출 |
| 12 | Mode 1 MTTF 컬럼 추가 | 4.3 | 결과 테이블에 MTTF (h) 컬럼 추가 (B1과 고장수 사이) |

#### 상세 내용

**항목 10-12: Mode 1 결과 테이블 변경**
- 기존: 조건별 비교 테이블 2개 (중복) → 변경: 1개로 통합
- 기존 컬럼: 조건, β, α, MTTF, B10, B1, B50, Bx, 고장수, 중단수
- 변경 후 컬럼: 조건, β (형상모수), α (척도모수), B0.1 (h), B0.4329 (h), B1 (h), MTTF (h), 고장수, 중단수
- Bx 수명(%) 입력창 제거, B0.4329를 고정값으로 산출

**항목 9: 공통 형상모수(β) 그래프 반영**
- Mode 2: 공통 β Weibull 확률도, CDF, 신뢰도 곡선에 공통 β 적용
- Mode 3: 공통 β Weibull 확률도, CDF에 공통 β 적용

**항목 8: 한글 폰트 설정**
- `matplotlib.rcParams['font.family']`에 Malgun Gothic 등록
- `axes.unicode_minus = False`로 마이너스 기호 깨짐 방지

**항목 4, 7: Mode 3 그래프 조건부 표시 및 자동 범위**
- 온도+전압 모델: Contour, Arrhenius, Voltage-Life 그래프 모두 표시
- 온도만 모델: Arrhenius 그래프만 표시, Contour/Voltage-Life 숨김
- 각 그래프별로 데이터 범위에 맞춰 x축 자동 설정
### 2026-08-07 (추가 반영)

| # | 수정 항목 | 설명 |
|---|----------|------|
| 13 | Excel 붙여넣기 새 양식 지원 | `T_125_5.5`/`C_125_5.5` 패턴 열이름 양식 자동 감지 추가 (양식 2) |
