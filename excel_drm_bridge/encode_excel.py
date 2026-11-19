# -*- coding: utf-8 -*-
"""
encode_excel.py — DRM 권한이 있는 PC에서 실행.

DRM이 걸린 xlsx를 "진짜 Excel"로 정상 오픈(DRM 인증을 그대로 통과)한 뒤,
그 Excel 객체 모델(COM)에서 셀 값/수식/기본 서식/정의된 이름(이름관리자)/
차트 정보를 읽어서 비(非)엑셀 포맷(JSON)으로 저장한다.

이 PC의 DRM 정책은 "xlsx로 저장하면 자동으로 암호화"되는 방식이라고 확인했는데
(md/txt는 안 걸림), **실측해보니 PNG 파일도 걸린다** — chart.Export()로 만든
PNG가 스크립트 실행 중 검증할 땐 멀쩡해 보였는데, 나중에 열어보면 전부
"<## NASCA DRM FILE" 헤더로 암호화돼 있었다(디스크에 이미지 파일로 남는 순간
백그라운드에서 비동기로 가로채 재암호화하는 것으로 추정). 그래서 **차트 이미지를
별도 .png 파일로 두지 않고, base64 문자열로 인코딩해서 JSON 안에 통째로
담는다** — JSON/텍스트는 이미 안전하다고 확인됐으므로 이 방식이면 디스크에
"이미지 파일"이 존재하는 시점 자체가 없어서 안전하다.

이 스크립트 자체가 DRM 암호화를 풀거나 우회하는 게 아니라, 사용자가 이미
정상적으로 열람·편집 권한을 가진 세션에서 보이는 내용을 받아적는 것뿐이다.

사전 준비:
  pip install pywin32 Pillow
  (Pillow는 차트를 클립보드로 캡처해서 PNG 바이트로 바꾸는 데 필요 — 필수)
  대상 파일을 Excel로 더블클릭해서 정상적으로 열리는 상태(DRM 인증 완료)여야 함.

사용법:
  python encode_excel.py "D:\\경로\\대상.xlsx" "D:\\경로\\출력폴더"

출력:
  출력폴더\\<원본파일명>.json          — 시트별 셀 그리드, 정의된 이름, 차트 메타데이터
                                      (차트 이미지는 base64로 이 JSON 안에 포함됨)
  출력폴더\\encode_log_<시각>.txt      — 진행 단계/경고/오류를 전부 남기는 로그.
                                      예상 못한 문제(특정 셀에서 멈춤, 서식 못 읽음,
                                      차트 추출 실패, COM 자체 오류 등)가 생기면
                                      이 로그를 보고 어디서 어떤 예외가 났는지 확인한다.

주의:
  - 서식(글꼴/색/번호서식)은 셀 수가 너무 많으면(MAX_FORMAT_CELLS 초과) 건너뛴다.
    값/수식은 항상 전부 뽑는다.
  - 차트는 "종류 + 소스 범위 문자열 + 스냅샷 이미지(base64)"까지만 뽑는다. 완전히
    동일한 차트 객체를 코드로 자동 재현하는 건 신뢰도가 낮아서, decode_excel.py는
    기본적으로 이미지로만 삽입하고, 실제 데이터 연동 차트가 필요하면 복원된
    값을 기준으로 Excel에서 직접 새로 만드는 걸 권장한다(README 참고).
  - 조건부 서식 "규칙" 자체는 이 스크립트가 다루지 않는다(결과로 보이는 색만
    fill_rgb로 캡처됨) — 규칙이 중요하면 서식 규칙 관리자를 눈으로 보고 따로 적어둘 것.
"""

import sys
import os
import io
import json
import re
import time
import base64
import tempfile
import datetime
import logging
import traceback

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass  # 콘솔이 reconfigure를 지원하지 않아도(구버전 등) 계속 진행

try:
    import win32com.client as win32
    import pywintypes
except ImportError:
    print("pywin32가 설치되어 있지 않습니다. 먼저 `pip install pywin32`를 실행하세요.")
    sys.exit(1)

# XlChartType 상수 중 흔한 것들 -> decode_excel.py가 참고할 수 있는 이름.
# (정확한 가능 값은 실행 중 info['chart_type']로 실측값을 JSON에도 같이 남긴다)
CHART_TYPE_NAMES = {
    51: 'column_clustered', 52: 'column_stacked', 53: 'column_stacked100',
    57: 'bar_clustered', 58: 'bar_stacked', 59: 'bar_stacked100',
    4: 'line', 65: 'line_markers',
    5: 'pie', 1: 'area', 76: 'area_stacked',
    -4169: 'scatter', 74: 'scatter_lines', 75: 'scatter_lines_no_markers',
    72: 'scatter_smooth', 73: 'scatter_smooth_no_markers',
}

XL_NONE_COLOR_INDEX = -4142

# [2026-11-19] 예전엔 셀 수가 MAX_FORMAT_CELLS(8000)를 넘는 시트는 서식(글꼴/색/
# 번호서식)을 통째로 건너뛰었다. 사용자 지적대로 이런 대형 시트들은 대개 "같은
# 모양의 시트가 반복"(예: 환산/환산2/환산3, 시트 "1"~"10")되거나 "한 시트 안에서
# 같은 블록이 반복"되는 구조라, 매 시트마다 39,000개 넘는 셀을 COM으로 하나하나
# 다시 읽을 필요가 없다 — 모양(행수x열수)이 같고 텍스트 라벨 배치까지 비슷한
# "같은 템플릿" 시트를 찾으면, 그 템플릿에서 이미 뽑아둔 서식 맵을 그대로
# 재사용한다(셀 값/수식은 항상 각 시트에서 새로 읽음 — 그건 bulk 배열 읽기라 이미
# 빠르고, 시트마다 실제로 다른 부분이니까). 템플릿이 없는 "첫 모양"의 시트만
# 상한 없이 전체 셀을 직접 읽는다 — 그래서 이제 서식이 통째로 빠지는 시트는 없다.
_SHEET_FORMAT_TEMPLATES = {}  # shape(n_rows,n_cols) -> {'fingerprint': {...}, 'formats': {(i,j): {...}}}
TEMPLATE_SIMILARITY_THRESHOLD = 0.6

# 로컬라이즈된 Excel에서 Range.NumberFormat이 영어 "General"이 아니라 그 언어의
# 번역된 이름을 그대로 돌려주는 경우가 실제로 확인됨(한국어 Excel: "표준").
# 이걸 "커스텀 서식"으로 오인해서 그대로 저장하면, 복원 시 Excel이 그 단어를
# 숫자서식 코드로 잘못 해석해서 모든 값이 그 글자 그대로(음수는 "-표준"처럼)
# 표시되는 사고가 났었다(실사용자 리포트로 발견). 흔한 로케일의 "General" 별칭을
# 화이트리스트로 걸러낸다.
GENERAL_FORMAT_ALIASES = {
    'general', '표준', '標準', '常规', '常規', 'estándar', 'standard', 'allgemein',
}
# 진짜 서식 코드라면 숫자/기호/날짜토큰 중 하나는 반드시 들어있다 — 하나도 없는
# 순수 문자열이면 위 화이트리스트에 없는 다른 로케일의 "General" 번역일 가능성이
# 높으므로, 모르면 저장하지 않는 쪽(=기본 서식으로 둠)이 안전하다.
_FORMAT_CODE_MARKER_CHARS = set('0123456789#%$₩¥€.,:/\\ -+()[]@";_*')
_DATE_TIME_TOKENS = ('yyyy', 'yy', 'mm', 'dd', 'hh', 'ss', 'AM/PM', 'am/pm')


def _looks_like_real_format_code(nf):
    if not nf:
        return False
    if nf.strip().lower() in GENERAL_FORMAT_ALIASES:
        return False
    if any(ch in _FORMAT_CODE_MARKER_CHARS for ch in nf):
        return True
    if any(tok in nf for tok in _DATE_TIME_TOKENS):
        return True
    return False

log = logging.getLogger('encode_excel')


def setup_logger(out_dir):
    """콘솔 + 파일(out_dir\\encode_log_<시각>.txt)에 동시에 기록.
    FileHandler는 레코드마다 바로 flush되므로, 중간에 멈추거나 죽어도
    그 직전까지의 로그는 파일에 남는다."""
    log.setLevel(logging.DEBUG)
    fmt = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', '%H:%M:%S')

    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    log_path = os.path.join(out_dir, f'encode_log_{ts}.txt')
    fh = logging.FileHandler(log_path, encoding='utf-8')
    fh.setFormatter(fmt)
    fh.setLevel(logging.DEBUG)
    log.addHandler(fh)

    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    sh.setLevel(logging.INFO)
    log.addHandler(sh)

    return log_path


def bgr_long_to_rrggbb(n):
    """VBA/COM의 Color 속성은 0x00BBGGRR(Long)로 들어오므로 RRGGBB로 뒤집는다."""
    n = int(n) & 0xFFFFFF
    b = (n >> 16) & 0xFF
    g = (n >> 8) & 0xFF
    r = n & 0xFF
    return '%02X%02X%02X' % (r, g, b)


def json_safe(val):
    if isinstance(val, (datetime.datetime, datetime.date)):
        return val.isoformat()
    return val


def flatten_scalar(val, label=''):
    """배열수식(레거시 CSE 등)이 걸린 셀은 COM이 그 위치의 값을 중첩 튜플로 주는
    경우가 실측으로 확인됨(예: ['텍스트'] 형태) — 셀엔 스칼라 하나만 들어갈 수
    있으므로 첫 번째 값만 꺼내 쓴다(실사용 사례는 전부 단일 원소였음)."""
    depth = 0
    while isinstance(val, (tuple, list)):
        if not val:
            return None
        if len(val) > 1 and depth == 0:
            log.debug(f'  {label} 배열수식 셀에 값이 여러 개({len(val)}개) — 첫 값만 사용: {val!r}')
        val = val[0]
        depth += 1
        if depth > 10:
            break
    return val


def normalize_grid(values, formulas, n_rows, n_cols):
    """COM은 셀이 1개면 스칼라, 1행/1열이면 1중 튜플을 주므로 2중 튜플로 통일."""
    if n_rows == 1 and n_cols == 1:
        return ((values,),), ((formulas,),)
    if n_rows == 1:
        return (tuple(values),), (tuple(formulas),)
    if n_cols == 1:
        return tuple((v,) for v in values), tuple((f,) for f in formulas)
    return values, formulas


_LABEL_RE = re.compile(r'^[\s\-+\d.,%]+$')


def build_fingerprint(values, n_rows, n_cols):
    """숫자/빈칸이 아닌 "라벨처럼 보이는" 텍스트 셀의 (위치→내용)만 모은다 —
    실제 데이터값은 시트마다 다르지만, 헤더/라벨 텍스트는 같은 템플릿이면 보통
    동일하므로 이걸로 "같은 모양의 다른 시트가 진짜 같은 템플릿인지"를 가늠한다."""
    fp = {}
    for i in range(n_rows):
        for j in range(n_cols):
            v = values[i][j]
            if isinstance(v, str) and v.strip() and not _LABEL_RE.match(v.strip()):
                fp[(i, j)] = v.strip()
    return fp


def fingerprint_similarity(fp_a, fp_b):
    if not fp_a or not fp_b:
        return 0.0
    keys = set(fp_a) & set(fp_b)
    if not keys:
        return 0.0
    matches = sum(1 for k in keys if fp_a[k] == fp_b[k])
    coverage = len(keys) / max(len(fp_a), len(fp_b))
    return (matches / len(keys)) * coverage


def extract_cell_format(ws, row, col):
    """셀 하나의 서식(번호서식/굵게/기울임/배경색/글꼴색)을 COM으로 직접 읽는다.
    실패한 속성은 그냥 빠지고(값은 영향 없음), 전체가 실패하면 None을 돌려준다."""
    fmt = {}
    try:
        rng = ws.Cells(row, col)
        nf = rng.NumberFormat
        if _looks_like_real_format_code(nf):
            fmt['number_format'] = nf
        elif nf and nf.strip().lower() not in GENERAL_FORMAT_ALIASES:
            log.debug(f'  [{ws.Name}] R{row}C{col} 서식 코드로 보기 애매해서 생략: {nf!r}')
        if rng.Font.Bold:
            fmt['bold'] = True
        if rng.Font.Italic:
            fmt['italic'] = True
        try:
            if rng.Interior.ColorIndex != XL_NONE_COLOR_INDEX:
                fmt['fill_rgb'] = bgr_long_to_rrggbb(rng.Interior.Color)
        except Exception as e:
            log.debug(f'  [{ws.Name}] R{row}C{col} 배경색 읽기 실패: {e}')
        try:
            fc = rng.Font.Color
            if fc is not None:
                fmt['font_rgb'] = bgr_long_to_rrggbb(fc)
        except Exception as e:
            log.debug(f'  [{ws.Name}] R{row}C{col} 글꼴색 읽기 실패: {e}')
        return fmt
    except Exception as e:
        log.debug(f'  [{ws.Name}] R{row}C{col} 서식 전체 읽기 실패: {e}')
        return None


def extract_sheet(ws):
    log.info(f'시트 처리 시작: {ws.Name}')
    used = ws.UsedRange
    start_row = used.Row
    start_col = used.Column
    n_rows = used.Rows.Count
    n_cols = used.Columns.Count
    log.debug(f'  [{ws.Name}] 사용 범위: row {start_row}~{start_row+n_rows-1}, '
              f'col {start_col}~{start_col+n_cols-1} ({n_rows}x{n_cols} = {n_rows*n_cols}셀)')

    values, formulas = normalize_grid(used.Value, used.Formula, n_rows, n_cols)

    shape = (n_rows, n_cols)
    fingerprint = build_fingerprint(values, n_rows, n_cols)
    candidate = _SHEET_FORMAT_TEMPLATES.get(shape)
    template = None
    if candidate is not None:
        sim = fingerprint_similarity(fingerprint, candidate['fingerprint'])
        if sim >= TEMPLATE_SIMILARITY_THRESHOLD:
            template = candidate
            log.info(f'  [{ws.Name}] 같은 모양({n_rows}x{n_cols})의 템플릿 시트("{candidate["source"]}") '
                      f'서식을 재사용함(유사도 {sim:.0%}) — 서식 COM 호출 생략, 값/수식은 그대로 새로 읽음')
        else:
            log.debug(f'  [{ws.Name}] 모양은 같지만({n_rows}x{n_cols}) 라벨 유사도 {sim:.0%}로 낮아 '
                      f'별도 템플릿으로 전체 추출')

    if template is None:
        log.info(f'  [{ws.Name}] 새 템플릿으로 서식 전체 추출 — 셀 {n_rows*n_cols}개 '
                 f'(모양이 크면 시간이 걸릴 수 있음)')

    cells = []
    format_fail_count = 0
    new_formats = {} if template is None else None
    for i in range(n_rows):
        for j in range(n_cols):
            row = start_row + i
            col = start_col + j
            val = flatten_scalar(values[i][j], label=f'[{ws.Name}] R{row}C{col}')
            formula = flatten_scalar(formulas[i][j], label=f'[{ws.Name}] R{row}C{col} 수식')
            if val is None and (formula in (None, '')):
                continue

            cell_info = {'row': row, 'col': col, 'value': json_safe(val)}
            if isinstance(formula, str) and formula.startswith('='):
                cell_info['formula'] = formula

            if template is not None:
                fmt = template['formats'].get((i, j))
                if fmt:
                    cell_info.update(fmt)
            else:
                fmt = extract_cell_format(ws, row, col)
                if fmt is None:
                    format_fail_count += 1
                elif fmt:
                    cell_info.update(fmt)
                    new_formats[(i, j)] = fmt
            cells.append(cell_info)

    if template is None:
        _SHEET_FORMAT_TEMPLATES[shape] = {
            'source': ws.Name, 'fingerprint': fingerprint, 'formats': new_formats,
        }

    if format_fail_count:
        log.warning(f'  [{ws.Name}] 서식 읽기 실패 {format_fail_count}건 (값/수식은 정상 추출됨)')

    col_widths = {}
    row_heights = {}
    try:
        for j in range(n_cols):
            w = ws.Columns(start_col + j).ColumnWidth
            if w is not None:
                col_widths[str(start_col + j)] = w
    except Exception as e:
        log.warning(f'  [{ws.Name}] 열 너비 읽기 실패: {e}')
    try:
        for i in range(n_rows):
            h = ws.Rows(start_row + i).RowHeight
            if h is not None:
                row_heights[str(start_row + i)] = h
    except Exception as e:
        log.warning(f'  [{ws.Name}] 행 높이 읽기 실패: {e}')

    log.info(f'시트 처리 완료: {ws.Name} — 셀 {len(cells)}개 추출')
    return {
        'name': ws.Name,
        'cells': cells,
        'col_widths': col_widths,
        'row_heights': row_heights,
    }


def extract_names(wb):
    """통합문서 범위 이름 + 시트별 범위 이름을 모두 모은다."""
    log.info('정의된 이름(이름관리자) 추출 시작')
    names = []

    def add(nm, scope):
        try:
            names.append({'name': nm.Name, 'refers_to': nm.RefersTo, 'scope': scope})
        except Exception as e:
            log.warning(f'  이름 하나 읽기 실패(scope={scope}): {e}')
            names.append({'name': getattr(nm, 'Name', '?'), 'scope': scope, 'error': str(e)})

    try:
        for nm in wb.Names:
            add(nm, 'workbook')
    except Exception as e:
        log.warning(f'  통합문서 범위 이름 목록 자체를 못 읽음: {e}')

    for ws in wb.Worksheets:
        try:
            for nm in ws.Names:
                add(nm, ws.Name)
        except Exception as e:
            log.debug(f'  [{ws.Name}] 시트 범위 이름 없음/읽기 실패: {e}')

    log.info(f'정의된 이름 {len(names)}개 추출 완료')
    return names


PNG_MAGIC = b'\x89PNG\r\n\x1a\n'


def _is_valid_png_bytes(data):
    return bool(data) and len(data) > 100 and data[:8] == PNG_MAGIC


def capture_chart_png_bytes(co, chart, label):
    """차트를 PNG 바이트로 캡처한다(파일로는 절대 남기지 않음).

    1차: 차트를 비트맵으로 클립보드에 복사 → 메모리에서 바로 읽음. 디스크를
    전혀 거치지 않으므로 "이미지 파일을 쓰는 순간 DRM이 나중에 가로채 재암호화"
    하는 문제(실측으로 확인됨 — chart.Export()로 만든 PNG가 스크립트 실행 중
    검증할 땐 멀쩡했는데 나중에 열어보면 전부 암호화돼 있었음)에서 안전하다.

    2차 폴백(1차가 실패했을 때만): chart.Export()로 임시 파일을 만들고 즉시
    읽어서 바이트만 챙긴 뒤 바로 삭제한다. 디스크에 남는 시간을 최소화하지만
    1차보다는 덜 안전하다."""
    try:
        from PIL import ImageGrab
        # CopyPicture(Appearance=xlScreen(1), Format=xlBitmap(2)) — 레거시 메타파일(EMF) 대신
        # 래스터 비트맵으로 클립보드에 올려야 ImageGrab.grabclipboard()가 안정적으로 읽어들인다.
        chart.CopyPicture(1, 2)
        time.sleep(0.3)
        img = ImageGrab.grabclipboard()
        if img is not None:
            buf = io.BytesIO()
            img.save(buf, 'PNG')
            data = buf.getvalue()
            if _is_valid_png_bytes(data):
                return data
            log.debug(f'  {label} — 클립보드 캡처 결과가 비정상, Export 방식으로 재시도')
        else:
            log.debug(f'  {label} — 클립보드에서 이미지를 못 가져옴, Export 방식으로 재시도')
    except ImportError:
        log.warning(f'  {label} — Pillow(PIL)가 없어서 클립보드 캡처 불가 '
                    f'(`pip install Pillow` 필수) — Export 방식만 시도')
    except Exception as e:
        log.debug(f'  {label} — 클립보드 캡처 실패({e}), Export 방식으로 재시도')

    tmp_path = os.path.join(tempfile.gettempdir(), f'_chart_tmp_{os.getpid()}_{id(co)}.png')
    try:
        chart.Export(tmp_path, 'PNG')
        with open(tmp_path, 'rb') as f:
            data = f.read()
        if _is_valid_png_bytes(data):
            return data
        log.warning(f'  {label} — PNG 확보 실패(클립보드/Export 둘 다 실패), '
                    f'이미지 없이 메타데이터(종류/시리즈 범위)만 남음 — decode 시 수동 재현 필요')
        return None
    except Exception as e:
        log.warning(f'  {label} — chart.Export() 실패: {e}')
        return None
    finally:
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception as e:
            log.debug(f'  {label} — 임시 PNG 삭제 실패(무시): {e}')


def extract_charts(wb):
    log.info('차트 추출 시작')
    charts = []
    for ws in wb.Worksheets:
        try:
            chart_objs = ws.ChartObjects()
            count = chart_objs.Count
        except Exception as e:
            log.debug(f'  [{ws.Name}] ChartObjects 접근 실패(차트 없음일 수 있음): {e}')
            continue

        for i in range(1, count + 1):
            try:
                co = chart_objs(i)
                chart = co.Chart
            except Exception as e:
                log.warning(f'  [{ws.Name}] 차트 #{i} 객체 접근 실패, 건너뜀: {e}')
                continue

            info = {
                'sheet': ws.Name,
                'name': co.Name,
                'top': co.Top, 'left': co.Left,
                'width': co.Width, 'height': co.Height,
            }
            log.info(f'  [{ws.Name}] 차트 처리 중: {co.Name}')
            try:
                ct = int(chart.ChartType)
                info['chart_type'] = ct
                info['chart_type_name'] = CHART_TYPE_NAMES.get(ct)
                if info['chart_type_name'] is None:
                    log.warning(f'  [{ws.Name}] 차트 "{co.Name}" 타입 코드 {ct}는 '
                                f'CHART_TYPE_NAMES에 없는 종류 — decode 쪽에서 이미지로만 대체됨')
            except Exception as e:
                log.warning(f'  [{ws.Name}] 차트 "{co.Name}" 타입 읽기 실패: {e}')
            try:
                info['title'] = chart.ChartTitle.Text if chart.HasTitle else None
            except Exception as e:
                log.debug(f'  [{ws.Name}] 차트 "{co.Name}" 제목 읽기 실패: {e}')
                info['title'] = None

            series = []
            try:
                sc_coll = chart.SeriesCollection()
                for s in range(1, sc_coll.Count + 1):
                    sc = sc_coll(s)
                    sdef = {
                        'name': str(sc.Name) if sc.Name else None,
                        'values_formula': sc.Formula,
                    }
                    # [2026-11-19] 차트 전체가 "콤보"(여러 종류 혼합, chart.ChartType이
                    # -4111 같은 애매한 값)라도, 시리즈 하나하나는 자기만의 ChartType을
                    # 갖고 있어서 이렇게 개별로 읽을 수 있다 — decode 쪽에서 같은 타입끼리
                    # 묶어 서브차트를 만들고 겹쳐서(openpyxl 콤보 결합) 재현하는 데 쓴다.
                    try:
                        sdef['series_chart_type'] = int(sc.ChartType)
                    except Exception as e:
                        sdef['series_chart_type'] = None
                        log.debug(f'  [{ws.Name}] 차트 "{co.Name}" 시리즈 {s} ChartType 읽기 실패: {e}')
                    series.append(sdef)
            except Exception as e:
                log.warning(f'  [{ws.Name}] 차트 "{co.Name}" 시리즈 읽기 실패: {e}')
            info['series'] = series

            label = f'차트 "{co.Name}" ({ws.Name})'
            data = capture_chart_png_bytes(co, chart, label)
            if data:
                info['image_b64'] = base64.b64encode(data).decode('ascii')
            else:
                info['image_b64'] = None

            charts.append(info)
    log.info(f'차트 {len(charts)}개 추출 완료')
    return charts


def run(src_path, out_dir):
    excel = None
    wb = None
    try:
        log.info('Excel COM 애플리케이션 시작 시도')
        excel = win32.Dispatch('Excel.Application')
        excel.Visible = True  # DRM 플러그인이 띄우는 UI/인증 과정을 볼 수 있게 보이게 연다
        excel.DisplayAlerts = False
        log.info('Excel COM 애플리케이션 시작 성공')

        log.info(f'파일 여는 중: {src_path}')
        wb = excel.Workbooks.Open(src_path, ReadOnly=True)
        log.info('파일 열기 성공 (DRM 인증 통과)')

        result = {
            'workbook_name': os.path.splitext(os.path.basename(src_path))[0],
            'sheets': [],
            'defined_names': extract_names(wb),
            'charts': extract_charts(wb),
        }
        for ws in wb.Worksheets:
            try:
                result['sheets'].append(extract_sheet(ws))
            except Exception as e:
                log.error(f'시트 "{ws.Name}" 전체 추출 실패, 이 시트는 건너뜀: {e}')
                log.debug(traceback.format_exc())

        return result
    finally:
        try:
            if wb is not None:
                wb.Close(SaveChanges=False)
                log.info('워크북 닫음(저장 안 함)')
        except Exception as e:
            log.warning(f'워크북 닫기 중 오류(무시): {e}')
        try:
            if excel is not None:
                excel.Quit()
                log.info('Excel 종료')
        except Exception as e:
            log.warning(f'Excel 종료 중 오류(무시): {e}')


def main():
    if len(sys.argv) < 3:
        print('사용법: python encode_excel.py <대상.xlsx> <출력폴더>')
        sys.exit(1)

    src_path = os.path.abspath(sys.argv[1])
    out_dir = os.path.abspath(sys.argv[2])
    os.makedirs(out_dir, exist_ok=True)

    log_path = setup_logger(out_dir)
    log.info(f'=== encode_excel.py 시작 === 대상: {src_path}')
    log.info(f'로그 파일: {log_path}')

    try:
        result = run(src_path, out_dir)
    except (pywintypes.com_error, Exception) as e:
        log.error(f'치명적 오류로 중단됨: {e}')
        log.error(traceback.format_exc())
        print(f'\n오류로 중단됐습니다. 자세한 내용은 로그 파일을 확인하세요:\n{log_path}')
        sys.exit(1)

    out_json = os.path.join(out_dir, result['workbook_name'] + '.json')
    try:
        with open(out_json, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=1)
    except Exception as e:
        log.error(f'JSON 저장 실패: {e}')
        log.error(traceback.format_exc())
        print(f'\nJSON 저장에 실패했습니다. 로그 파일을 확인하세요:\n{log_path}')
        sys.exit(1)

    log.info(f'완료: {out_json}')
    log.info(f'시트 {len(result["sheets"])}개, 정의된 이름 {len(result["defined_names"])}개, '
             f'차트 {len(result["charts"])}개')
    print(f'\n완료: {out_json}')
    print(f'로그: {log_path}')


if __name__ == '__main__':
    main()
