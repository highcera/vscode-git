# Dividend System Blueprint - Data Step 1
# universe_seed.json - ETF 목록 (88개)

## 개요
이 파일은 배당 유니버스의 ETF 목록을 포함합니다.

---

## universe_seed.json - ETF (Part 1/2)

`us_market/dividend/data/universe_seed.json`:

```json
[
    {"symbol": "SCHD", "type": "ETF", "tags": ["dividend_quality", "core", "quarterly"]},
    {"symbol": "VIG", "type": "ETF", "tags": ["dividend_growth", "core", "quarterly"]},
    {"symbol": "DGRO", "type": "ETF", "tags": ["dividend_growth", "core", "quarterly"]},
    {"symbol": "VYM", "type": "ETF", "tags": ["dividend_quality", "core", "quarterly"]},
    {"symbol": "HDV", "type": "ETF", "tags": ["dividend_quality", "core", "quarterly"]},
    {"symbol": "DVY", "type": "ETF", "tags": ["dividend_quality", "core", "quarterly"]},
    {"symbol": "SDY", "type": "ETF", "tags": ["dividend_quality", "core", "quarterly"]},
    {"symbol": "NOBL", "type": "ETF", "tags": ["dividend_quality", "core", "quarterly"]},
    {"symbol": "SPYD", "type": "ETF", "tags": ["high_yield", "value", "quarterly"]},
    {"symbol": "FDVV", "type": "ETF", "tags": ["dividend_quality", "core", "quarterly"]},
    {"symbol": "RDVY", "type": "ETF", "tags": ["dividend_quality", "core", "quarterly"]},
    {"symbol": "DGRW", "type": "ETF", "tags": ["dividend_growth", "core", "quarterly"]},
    {"symbol": "CGDV", "type": "ETF", "tags": ["dividend_quality", "core", "quarterly"]},
    {"symbol": "FDRR", "type": "ETF", "tags": ["dividend_quality", "core", "quarterly"]},
    {"symbol": "LVHD", "type": "ETF", "tags": ["dividend_quality", "low_vol", "quarterly"]},
    {"symbol": "PEY", "type": "ETF", "tags": ["dividend_quality", "value", "quarterly"]},
    {"symbol": "DON", "type": "ETF", "tags": ["dividend_quality", "value", "quarterly"]},
    {"symbol": "DES", "type": "ETF", "tags": ["dividend_quality", "value", "quarterly"]},
    {"symbol": "SDOG", "type": "ETF", "tags": ["value", "dividend_quality", "quarterly"]},
    {"symbol": "VIGI", "type": "ETF", "tags": ["international_div", "dividend_growth", "quarterly"]},
    {"symbol": "VYMI", "type": "ETF", "tags": ["international_div", "high_yield", "quarterly"]},
    {"symbol": "IDV", "type": "ETF", "tags": ["international_div", "high_yield", "quarterly"]},
    {"symbol": "DVYE", "type": "ETF", "tags": ["international_div", "high_yield", "quarterly"]},
    {"symbol": "SCHY", "type": "ETF", "tags": ["international_div", "dividend_quality", "quarterly"]},
    {"symbol": "GCOW", "type": "ETF", "tags": ["international_div", "dividend_quality", "quarterly"]},
    {"symbol": "JEPI", "type": "ETF", "tags": ["covered_call", "high_yield", "monthly_payer"]},
    {"symbol": "JEPQ", "type": "ETF", "tags": ["covered_call", "high_yield", "monthly_payer"]},
    {"symbol": "QYLD", "type": "ETF", "tags": ["covered_call", "high_yield", "monthly_payer"]},
    {"symbol": "XYLD", "type": "ETF", "tags": ["covered_call", "high_yield", "monthly_payer"]},
    {"symbol": "RYLD", "type": "ETF", "tags": ["covered_call", "high_yield", "monthly_payer"]},
    {"symbol": "DIVO", "type": "ETF", "tags": ["covered_call", "dividend_quality", "monthly_payer"]},
    {"symbol": "NUSI", "type": "ETF", "tags": ["covered_call", "low_vol", "monthly_payer"]},
    {"symbol": "SPYI", "type": "ETF", "tags": ["covered_call", "high_yield", "monthly_payer"]},
    {"symbol": "QQQI", "type": "ETF", "tags": ["covered_call", "high_yield", "monthly_payer"]},
    {"symbol": "XYLG", "type": "ETF", "tags": ["covered_call", "high_yield", "monthly_payer"]},
    {"symbol": "QYLG", "type": "ETF", "tags": ["covered_call", "high_yield", "monthly_payer"]},
    {"symbol": "VNQ", "type": "ETF", "tags": ["reit", "real_assets", "quarterly"]},
    {"symbol": "SCHH", "type": "ETF", "tags": ["reit", "real_assets", "quarterly"]},
    {"symbol": "IYR", "type": "ETF", "tags": ["reit", "real_assets", "quarterly"]},
    {"symbol": "XLRE", "type": "ETF", "tags": ["reit", "real_assets", "quarterly"]},
    {"symbol": "FREL", "type": "ETF", "tags": ["reit", "real_assets", "quarterly"]},
    {"symbol": "USRT", "type": "ETF", "tags": ["reit", "real_assets", "quarterly"]},
    {"symbol": "REZ", "type": "ETF", "tags": ["reit", "real_assets", "quarterly"]},
    {"symbol": "KBWY", "type": "ETF", "tags": ["reit", "high_yield", "quarterly"]},
    {"symbol": "XLU", "type": "ETF", "tags": ["utilities", "low_vol", "quarterly"]},
    {"symbol": "VPU", "type": "ETF", "tags": ["utilities", "low_vol", "quarterly"]},
    {"symbol": "PFF", "type": "ETF", "tags": ["preferreds", "high_yield", "monthly_payer"]},
    {"symbol": "PGX", "type": "ETF", "tags": ["preferreds", "monthly_payer"]},
    {"symbol": "VRP", "type": "ETF", "tags": ["preferreds", "monthly_payer"]},
    {"symbol": "FPE", "type": "ETF", "tags": ["preferreds", "monthly_payer"]},
    {"symbol": "BND", "type": "ETF", "tags": ["bonds", "investment_grade", "quarterly"]},
    {"symbol": "AGG", "type": "ETF", "tags": ["bonds", "investment_grade", "quarterly"]},
    {"symbol": "LQD", "type": "ETF", "tags": ["bonds", "investment_grade", "monthly_payer"]},
    {"symbol": "TLT", "type": "ETF", "tags": ["bonds", "treasuries", "monthly_payer"]},
    {"symbol": "IEF", "type": "ETF", "tags": ["bonds", "treasuries", "monthly_payer"]},
    {"symbol": "SHY", "type": "ETF", "tags": ["bonds", "treasuries", "monthly_payer"]},
    {"symbol": "TIP", "type": "ETF", "tags": ["bonds", "inflation_hedge", "monthly_payer"]},
    {"symbol": "HYG", "type": "ETF", "tags": ["bonds", "high_yield_bonds", "monthly_payer"]},
    {"symbol": "JNK", "type": "ETF", "tags": ["bonds", "high_yield_bonds", "monthly_payer"]},
    {"symbol": "AMLP", "type": "ETF", "tags": ["midstream", "high_yield", "quarterly"]},
    {"symbol": "MLPA", "type": "ETF", "tags": ["midstream", "high_yield", "quarterly"]},
    {"symbol": "ENFR", "type": "ETF", "tags": ["midstream", "high_yield", "quarterly"]},
    {"symbol": "SPHD", "type": "ETF", "tags": ["high_yield", "low_vol", "monthly_payer"]},
    {"symbol": "USMV", "type": "ETF", "tags": ["low_vol", "core", "quarterly"]},
    {"symbol": "SPLV", "type": "ETF", "tags": ["low_vol", "core", "quarterly"]},
    {"symbol": "QUAL", "type": "ETF", "tags": ["dividend_quality", "core", "quarterly"]},
    {"symbol": "USIG", "type": "ETF", "tags": ["bonds", "investment_grade", "monthly_payer"]},
    {"symbol": "BIL", "type": "ETF", "tags": ["bonds", "treasuries", "monthly_payer"]},
    {"symbol": "SGOV", "type": "ETF", "tags": ["bonds", "treasuries", "monthly_payer"]},
    {"symbol": "MINT", "type": "ETF", "tags": ["bonds", "investment_grade", "monthly_payer"]},
    {"symbol": "HYD", "type": "ETF", "tags": ["bonds", "high_yield_bonds", "monthly_payer"]},
    {"symbol": "TLH", "type": "ETF", "tags": ["bonds", "treasuries", "monthly_payer"]},
    {"symbol": "VCIT", "type": "ETF", "tags": ["bonds", "investment_grade", "monthly_payer"]},
    {"symbol": "VCSH", "type": "ETF", "tags": ["bonds", "investment_grade", "monthly_payer"]},
    {"symbol": "BNDW", "type": "ETF", "tags": ["bonds", "investment_grade", "quarterly"]},
    {"symbol": "VTIP", "type": "ETF", "tags": ["bonds", "inflation_hedge", "monthly_payer"]},
    {"symbol": "LTPZ", "type": "ETF", "tags": ["bonds", "inflation_hedge", "monthly_payer"]},
    {"symbol": "IEMG", "type": "ETF", "tags": ["international_div", "quarterly"]},
    {"symbol": "VEA", "type": "ETF", "tags": ["international_div", "quarterly"]},
    {"symbol": "IEFA", "type": "ETF", "tags": ["international_div", "quarterly"]},
    {"symbol": "EEM", "type": "ETF", "tags": ["international_div", "quarterly"]},
    {"symbol": "EWU", "type": "ETF", "tags": ["international_div", "quarterly"]},
    {"symbol": "EWJ", "type": "ETF", "tags": ["international_div", "quarterly"]},
    {"symbol": "EWG", "type": "ETF", "tags": ["international_div", "quarterly"]},
    {"symbol": "EFA", "type": "ETF", "tags": ["international_div", "quarterly"]},
    {"symbol": "SPDW", "type": "ETF", "tags": ["international_div", "quarterly"]},
    {"symbol": "SCHF", "type": "ETF", "tags": ["international_div", "quarterly"]},
    {"symbol": "BIZD", "type": "ETF", "tags": ["bdc", "high_yield", "quarterly"]}
]
```

---

## ETF 카테고리 요약

| 카테고리 | 티커 수 | 주요 티커 |
|----------|---------|-----------|
| **코어 배당** | 19 | SCHD, VIG, DGRO, VYM, HDV |
| **해외 배당** | 16 | VIGI, VYMI, IDV, EFA, VEA |
| **커버드콜** | 11 | JEPI, JEPQ, QYLD, XYLD, DIVO |
| **리츠** | 8 | VNQ, SCHH, IYR, XLRE, KBWY |
| **채권** | 18 | BND, AGG, TLT, LQD, HYG |
| **유틸리티** | 2 | XLU, VPU |
| **우선주** | 4 | PFF, PGX, VRP, FPE |
| **MLP** | 3 | AMLP, MLPA, ENFR |
| **저변동** | 4 | USMV, SPLV, LVHD, SPHD |
| **BDC** | 1 | BIZD |

---

## 다음 단계

**DATA_STEP2.md**에서 개별주 목록(126개)을 추가합니다.
