# -*- coding: utf-8 -*-
"""
decode_excel.py — DRM 권한이 없거나 DRM 정책이 안 걸리는 PC에서 실행.

encode_excel.py가 뽑아낸 JSON을 읽어서 새 xlsx를 조립한다. 차트 이미지는 별도
파일이 아니라 JSON 안에 base64로 들어있다(인코더 쪽 DRM이 디스크에 쓰인 이미지
파일을 나중에 가로채 재암호화하는 문제가 실측으로 확인돼서, 이미지 파일 자체를
아예 안 만드는 방식으로 바뀜 — 2026-11-18). openpyxl만 쓰므로 Excel 설치가
필요 없다.

복원되는 것: 셀 값, 수식(문자열로 그대로 넣으면 Excel이 다시 계산함),
기본 서식(굵게/기울임/글꼴색/배경색/숫자서식), 열 너비/행 높이, 정의된
이름(이름관리자).

차트: 종류가 단일(막대/선/원형/영역/분산 중 하나)이고 시리즈 수식(SERIES(...))을
문제없이 파싱할 수 있으면 **실제 데이터와 연동된 차트 객체**로 재구성한다
(2026-11-19 추가). 종류가 "콤보"(여러 종류가 섞인 차트, chart_type이 -4111 등으로
잡힌 경우 — 시리즈별 세부 종류를 인코딩 단계에서 따로 안 뽑아놔서 어떤 시리즈가
막대고 어떤 게 선인지 구분이 안 됨)이거나 파싱에 실패하면, 캡처해둔 스냅샷
이미지로 대체한다 — 데이터와 연동된 실제 차트가 필요하면 복원된 값을 기준으로
Excel에서 직접 새로 만드는 걸 권장한다.

복원되지 않는 것(수작업 필요): 조건부 서식 "규칙"(결과 색만 fill_rgb로
남아있음), 표(Excel Table) 지정, 테두리/병합 셀 등 세부 서식.

사용법:
  python decode_excel.py <encode_excel.py 출력폴더> <결과.xlsx>

필요 패키지:
  pip install openpyxl Pillow   (Pillow는 차트를 이미지로 삽입할 때 필요)

로그:
  <결과.xlsx가 저장될 폴더>\\decode_log_<시각>.txt 에 단계별 진행/경고/오류를
  남긴다. 셀 하나, 이름 하나, 차트 하나가 실패해도 전체를 멈추지 않고
  건너뛰면서 로그에 "어디서 왜 실패했는지" 기록하므로, 결과 파일을 열어보기
  전에 로그만 봐도 뭐가 빠졌는지 알 수 있다.
"""

import sys
import os
import io
import json
import base64
import datetime
import logging
import traceback

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass  # 콘솔이 reconfigure를 지원하지 않아도(구버전 등) 계속 진행

from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from openpyxl.utils.cell import range_boundaries
from openpyxl.styles import Font, PatternFill
from openpyxl.chart import ScatterChart, LineChart, BarChart, PieChart, AreaChart, Series, Reference
from openpyxl.workbook.defined_name import DefinedName
from openpyxl.drawing.image import Image as XLImage

log = logging.getLogger('decode_excel')


def setup_logger(out_dir):
    log.setLevel(logging.DEBUG)
    fmt = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', '%H:%M:%S')

    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    log_path = os.path.join(out_dir, f'decode_log_{ts}.txt')
    fh = logging.FileHandler(log_path, encoding='utf-8')
    fh.setFormatter(fmt)
    fh.setLevel(logging.DEBUG)
    log.addHandler(fh)

    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    sh.setLevel(logging.INFO)
    log.addHandler(sh)

    return log_path


def find_manifest(folder):
    candidates = [fn for fn in os.listdir(folder) if fn.endswith('.json')]
    if not candidates:
        raise FileNotFoundError('폴더에서 encode_excel.py가 만든 JSON을 찾지 못했습니다: ' + folder)
    if len(candidates) > 1:
        log.warning(f'JSON이 여러 개({candidates}) 있어서 첫 번째({candidates[0]})만 사용함')
    return os.path.join(folder, candidates[0])


def apply_cell(ws, c):
    cell = ws.cell(row=c['row'], column=c['col'])
    if c.get('formula'):
        cell.value = c['formula']
    elif c.get('value') is not None:
        cell.value = c['value']
    else:
        return

    if c.get('number_format'):
        try:
            cell.number_format = c['number_format']
        except Exception as e:
            log.debug(f'  R{c["row"]}C{c["col"]} 숫자서식 적용 실패: {e}')

    font_kwargs = {}
    if c.get('bold'):
        font_kwargs['bold'] = True
    if c.get('italic'):
        font_kwargs['italic'] = True
    if c.get('font_rgb'):
        font_kwargs['color'] = c['font_rgb']
    if font_kwargs:
        try:
            cell.font = Font(**font_kwargs)
        except Exception as e:
            log.debug(f'  R{c["row"]}C{c["col"]} 글꼴 적용 실패: {e}')

    if c.get('fill_rgb'):
        try:
            cell.fill = PatternFill(start_color=c['fill_rgb'], end_color=c['fill_rgb'], fill_type='solid')
        except Exception as e:
            log.debug(f'  R{c["row"]}C{c["col"]} 배경색 적용 실패: {e}')


def build_sheet(wb, sheet_data, is_first):
    name = sheet_data.get('name', 'Sheet')
    log.info(f'시트 생성: {name}')
    if is_first:
        ws = wb.active
        ws.title = name
    else:
        ws = wb.create_sheet(name)

    cell_fail = 0
    for c in sheet_data.get('cells', []):
        try:
            apply_cell(ws, c)
        except Exception as e:
            cell_fail += 1
            log.warning(f'  [{name}] R{c.get("row")}C{c.get("col")} 셀 복원 실패, 건너뜀: {e}')
    if cell_fail:
        log.warning(f'  [{name}] 셀 복원 실패 {cell_fail}건')

    for col_str, width in sheet_data.get('col_widths', {}).items():
        try:
            ws.column_dimensions[get_column_letter(int(col_str))].width = width
        except Exception as e:
            log.debug(f'  [{name}] 열 너비(col={col_str}) 적용 실패: {e}')
    for row_str, height in sheet_data.get('row_heights', {}).items():
        try:
            ws.row_dimensions[int(row_str)].height = height
        except Exception as e:
            log.debug(f'  [{name}] 행 높이(row={row_str}) 적용 실패: {e}')

    log.info(f'시트 생성 완료: {name} — 셀 {len(sheet_data.get("cells", []))}개 중 성공 '
             f'{len(sheet_data.get("cells", [])) - cell_fail}개')
    return ws


# Excel 내부 예약 이름(인쇄영역/자동필터 등). AutoFilter·페이지설정 같은 다른 XML
# 구조와 맞물려 있어서, 그냥 DefinedName으로만 복원하면 그 연결이 깨진 반쪽짜리
# 참조가 되고 — 실제로 "명명된 범위가 제거됨" Excel 복구 경고의 흔한 원인이다.
# 인쇄영역 자체는 서식 수준이라 중요도가 낮으므로, 여기서는 아예 건너뛴다.
BUILTIN_NAME_WORDS = {
    'print_area', 'print_titles', 'database', 'criteria', 'extract',
    'consolidate_area', 'sheet_title', '_filterdatabase', 'filterdatabase',
}


def _is_builtin_name(clean_name):
    return clean_name.lstrip('_').lower() in BUILTIN_NAME_WORDS


def apply_defined_names(wb, names):
    log.info(f'정의된 이름(이름관리자) 복원 시작 — {len(names)}개')
    ok = 0
    skipped_builtin = 0
    dup_count = 0
    for n in names:
        name = n.get('name', '') or ''
        refers = n.get('refers_to')
        scope = n.get('scope', 'workbook')
        if not name or not refers:
            log.debug(f'  이름/참조가 비어서 건너뜀: {n}')
            continue

        clean_name = name.split('!')[-1]
        if _is_builtin_name(clean_name):
            skipped_builtin += 1
            log.debug(f'  "{name}" — Excel 내부 예약 이름이라 생략(인쇄영역/자동필터 등)')
            continue

        attr_text = refers.lstrip('=')
        try:
            if scope == 'workbook':
                if clean_name in wb.defined_names:
                    dup_count += 1
                    # 이름이 몇천 개 단위면 중복도 흔해서, 건마다 콘솔에 찍으면 화면이
                    # 묻혀버린다(실제로 사용자가 겪은 문제) — 상세는 파일(DEBUG)에만 남기고
                    # 콘솔에는 끝에 집계 한 줄만 보여준다.
                    log.debug(f'  [이름관리자] "{clean_name}"가 이미 있어서 덮어씀(통합문서 범위 중복)')
                wb.defined_names[clean_name] = DefinedName(clean_name, attr_text=attr_text)
                ok += 1
            elif scope in wb.sheetnames:
                ws = wb[scope]
                if clean_name in ws.defined_names:
                    dup_count += 1
                    log.debug(f'  [이름관리자] "{scope}!{clean_name}"가 이미 있어서 덮어씀')
                ws.defined_names[clean_name] = DefinedName(clean_name, attr_text=attr_text)
                ok += 1
            else:
                log.debug(f'  [이름관리자] "{name}" — scope "{scope}" 시트를 못 찾아서 '
                          f'통합문서 범위로 대신 등록')
                wb.defined_names[clean_name] = DefinedName(clean_name, attr_text=attr_text)
                ok += 1
        except Exception as e:
            log.warning(f'  [이름관리자] "{name}" 복원 실패(수동 확인 필요): {e}')
    summary = f'정의된 이름 복원 완료 — {ok}/{len(names)}개 성공'
    if skipped_builtin:
        summary += f', 예약 이름 {skipped_builtin}개 생략'
    if dup_count:
        summary += f', 같은 이름 중복 {dup_count}건(마지막 값으로 덮어씀 — 상세는 로그 파일 DEBUG 라인 참고)'
    log.info(summary)


# XlChartType 숫자 코드 -> (scatterStyle) 매핑. encode_excel.py의 CHART_TYPE_NAMES에
# 이름이 없는 산점도 변형들(72/73/74/75, -4169)도 숫자 코드로 직접 받아서 처리한다.
SCATTER_STYLE_BY_CODE = {
    -4169: 'marker',   # xlXYScatter
    74: 'lineMarker',  # xlXYScatterLines
    75: 'line',        # xlXYScatterLinesNoMarkers
    72: 'smoothMarker',  # xlXYScatterSmooth
    73: 'smooth',        # xlXYScatterSmoothNoMarkers
}
SCATTER_STYLE_BY_NAME = {'scatter': 'marker'}

SIMPLE_CHART_CLASS = {
    'column_clustered': (BarChart, {'type': 'col', 'grouping': 'clustered'}),
    'column_stacked': (BarChart, {'type': 'col', 'grouping': 'stacked'}),
    'column_stacked100': (BarChart, {'type': 'col', 'grouping': 'percentStacked'}),
    'bar_clustered': (BarChart, {'type': 'bar', 'grouping': 'clustered'}),
    'bar_stacked': (BarChart, {'type': 'bar', 'grouping': 'stacked'}),
    'bar_stacked100': (BarChart, {'type': 'bar', 'grouping': 'percentStacked'}),
    'line': (LineChart, {}),
    'line_markers': (LineChart, {}),
    'pie': (PieChart, {}),
    'area': (AreaChart, {}),
    'area_stacked': (AreaChart, {'grouping': 'stacked'}),
}

# encode_excel.py의 CHART_TYPE_NAMES와 동일한 숫자코드->이름 매핑(시리즈별
# ChartType을 콤보 재현에 쓰려면 여기서도 똑같이 이름을 붙일 수 있어야 함).
CHART_TYPE_NAME_BY_CODE = {
    51: 'column_clustered', 52: 'column_stacked', 53: 'column_stacked100',
    57: 'bar_clustered', 58: 'bar_stacked', 59: 'bar_stacked100',
    4: 'line', 65: 'line_markers',
    5: 'pie', 1: 'area', 76: 'area_stacked',
    -4169: 'scatter', 74: 'scatter_lines', 75: 'scatter_lines_no_markers',
    72: 'scatter_smooth', 73: 'scatter_smooth_no_markers',
}


def _chart_spec_for_code(code):
    """시리즈별 ChartType 숫자 코드를 ('scatter', scatterStyle) 또는
    ('simple', SIMPLE_CHART_CLASS의 키)로 변환. 모르는 코드면 (None, None)."""
    if code in SCATTER_STYLE_BY_CODE:
        return ('scatter', SCATTER_STYLE_BY_CODE[code])
    name = CHART_TYPE_NAME_BY_CODE.get(code)
    if name in SIMPLE_CHART_CLASS:
        return ('simple', name)
    return (None, None)


def parse_series_formula(formula):
    """'=SERIES(이름,범주범위,값범위,순서)' 문자열을 네 조각으로 분리.
    인자 안의 "..." 문자열 리터럴에 들어있는 쉼표는 구분자로 보지 않는다
    (Excel 시트 이름엔 애초에 쉼표가 올 수 없어서 그 외엔 단순 split으로 충분)."""
    if not formula or not formula.startswith('=SERIES(') or not formula.endswith(')'):
        return None
    inner = formula[len('=SERIES('):-1]
    parts, cur, in_quote = [], '', False
    for ch in inner:
        if ch == '"':
            in_quote = not in_quote
            cur += ch
        elif ch == ',' and not in_quote:
            parts.append(cur)
            cur = ''
        else:
            cur += ch
    parts.append(cur)
    while len(parts) < 4:
        parts.append('')
    name, cats, vals, order = (p.strip() for p in parts[:4])
    return {'name': name, 'categories': cats, 'values': vals, 'order': order}


def ref_from_range_str(wb, range_str):
    """"'시트명'!$B$2:$B$10" 같은 문자열을 openpyxl Reference로 변환. 실패하면 None."""
    if not range_str or '!' not in range_str:
        return None
    sheet_part, cell_part = range_str.split('!', 1)
    sheet_name = sheet_part.strip().strip("'")
    if sheet_name not in wb.sheetnames:
        return None
    cell_part = cell_part.replace('$', '').strip()
    try:
        min_col, min_row, max_col, max_row = range_boundaries(cell_part)
    except Exception:
        return None
    if min_col is None or min_row is None:
        return None
    return Reference(wb[sheet_name], min_col=min_col, min_row=min_row, max_col=max_col, max_row=max_row)


def series_title(name_field):
    """SERIES()의 첫 인자 — "문자열 리터럴"이면 그걸 제목으로 쓰고, 셀 참조(동적 제목)면
    복잡해서 생략한다(제목 없이 둠 — 데이터 자체는 영향 없음)."""
    name_field = (name_field or '').strip()
    if name_field.startswith('"') and name_field.endswith('"'):
        return name_field[1:-1]
    return None


def _make_chart_shell(kind, info):
    """kind='scatter'면 info=scatterStyle, kind='simple'이면 info=SIMPLE_CHART_CLASS 키.
    빈 openpyxl 차트 객체(시리즈 없음)를 만들어 돌려준다."""
    if kind == 'scatter':
        chart = ScatterChart()
        chart.scatterStyle = info
        return chart, True
    cls, kwargs = SIMPLE_CHART_CLASS[info]
    chart = cls()
    for k, v in kwargs.items():
        setattr(chart, k, v)
    return chart, False


def _add_series_to_chart(wb, chart, is_scatter, series_defs, cats_already_set):
    """series_defs의 SERIES(...) 수식을 파싱해서 chart에 시리즈로 추가.
    실제로 추가된 개수를 돌려준다. cats_already_set은 (리스트라 참조로 공유되는)
    1개짜리 가변 플래그 — 범주축은 차트당 한 번만 설정해야 해서 호출 간에 공유."""
    added = 0
    for sdef in series_defs:
        parsed = parse_series_formula(sdef.get('values_formula'))
        if not parsed:
            continue
        values_ref = ref_from_range_str(wb, parsed['values'])
        if values_ref is None:
            continue
        title = series_title(parsed['name'])
        cats_ref = ref_from_range_str(wb, parsed['categories'])

        if is_scatter:
            if cats_ref is None:
                continue  # 분산형은 x값 없이는 의미가 없어서 이 시리즈만 건너뜀
            s = Series(values_ref, xvalues=cats_ref, title=title)
        else:
            s = Series(values_ref, title=title)
            if cats_ref is not None and not cats_already_set[0]:
                chart.set_categories(cats_ref)
                cats_already_set[0] = True
        chart.series.append(s)
        added += 1
    return added


def build_combo_chart(wb, ch, series_defs):
    """시리즈별 ChartType(series_chart_type)을 보고 같은 타입끼리 묶어 서브차트를
    만든 뒤, openpyxl의 콤보 결합(+=)으로 겹쳐서 재현한다. 타입을 모르는
    시리즈는 그냥 빠진다(그 부분만 빠지고 나머지는 재현됨)."""
    groups = {}  # (kind, info) -> [series_dict, ...]
    for sdef in series_defs:
        kind, info = _chart_spec_for_code(sdef.get('series_chart_type'))
        if kind is None:
            continue
        groups.setdefault((kind, info), []).append(sdef)

    if not groups:
        return None

    sub_charts = []
    for (kind, info), defs in groups.items():
        sub, is_scatter = _make_chart_shell(kind, info)
        added = _add_series_to_chart(wb, sub, is_scatter, defs, [False])
        if added:
            sub_charts.append(sub)

    if not sub_charts:
        return None

    combo = sub_charts[0]
    for extra in sub_charts[1:]:
        try:
            combo += extra
        except Exception as e:
            log.debug(f'  콤보 결합 중 일부 실패(나머지는 반영됨): {e}')
    return combo


def build_native_chart(wb, ch):
    """시리즈 수식을 파싱해서 데이터와 연동된 실제 차트 객체를 재구성한다.
    차트 전체가 단일 종류면 그대로, "콤보"(여러 종류 혼합)면 시리즈별
    ChartType을 보고 같은 타입끼리 묶어 서브차트로 나눈 뒤 겹친다. 파싱/타입
    매핑에 완전히 실패하면 None을 돌려줘서 호출 측이 이미지로 대체하게 한다."""
    series_defs = ch.get('series') or []
    if not series_defs:
        return None

    type_name = ch.get('chart_type_name')
    type_code = ch.get('chart_type')
    scatter_style = SCATTER_STYLE_BY_NAME.get(type_name) or SCATTER_STYLE_BY_CODE.get(type_code)

    if scatter_style:
        chart, is_scatter = _make_chart_shell('scatter', scatter_style)
    elif type_name in SIMPLE_CHART_CLASS:
        chart, is_scatter = _make_chart_shell('simple', type_name)
    else:
        # 차트 전체 타입을 모르거나 콤보임 — 시리즈별 타입이 있으면 콤보로 재시도
        chart = build_combo_chart(wb, ch, series_defs)
        if chart is not None and ch.get('title'):
            chart.title = ch['title']
        return chart

    added = _add_series_to_chart(wb, chart, is_scatter, series_defs, [False])
    if added == 0:
        return None
    if ch.get('title'):
        chart.title = ch['title']
    return chart


def add_charts(wb, charts):
    log.info(f'차트 삽입 시작 — {len(charts)}개')
    for ch in charts:
        sheet_name = ch.get('sheet')
        chart_label = f'"{ch.get("name")}" ({sheet_name})'
        if sheet_name not in wb.sheetnames:
            log.warning(f'  {chart_label} — 대상 시트가 없어서 건너뜀')
            continue
        ws = wb[sheet_name]

        try:
            native = build_native_chart(wb, ch)
        except Exception as e:
            native = None
            log.debug(f'  {chart_label} — 네이티브 차트 재구성 중 예외(이미지로 대체): {e}')
        if native is not None:
            try:
                anchor_col = get_column_letter(max(1, int(ch.get('left', 0) // 64) + 1))
                ws.add_chart(native, f'{anchor_col}2')
                # openpyxl 차트의 _charts는 기본값이 [self]이고, +=로 결합하면 거기에
                # 덧붙는 식이라 "자기 자신 포함" 리스트다 — 그래서 이거 하나로만 합산.
                sub_charts_list = getattr(native, '_charts', [native])
                total_series = sum(len(c.series) for c in sub_charts_list)
                combo_note = f', 콤보 {len(sub_charts_list)}종류 결합' if len(sub_charts_list) > 1 else ''
                log.info(f'  {chart_label} — 데이터 연동 차트로 복원됨 (시리즈 {total_series}개{combo_note})')
                continue
            except Exception as e:
                log.warning(f'  {chart_label} — 네이티브 차트 삽입 실패, 이미지로 대체 시도: {e}')

        b64 = ch.get('image_b64')
        if b64:
            try:
                data = base64.b64decode(b64)
                from PIL import Image as PILImage
                # .load()를 호출하면 PIL이 다 읽었다고 보고 내부 fp를 None으로 비우는데,
                # openpyxl은 wb.save() 시점에 그 fp.seek(0)을 다시 호출해서 바이트를 꺼내므로
                # load()를 부르면 안 된다(실측으로 'NoneType' seek 오류 확인) — PIL Image가
                # 이 BytesIO를 계속 들고 있게 그대로 둬서 저장 시점까지 열려있게 한다.
                pil_img = PILImage.open(io.BytesIO(data))
                img = XLImage(pil_img)
                anchor_col = get_column_letter(max(1, int(ch.get('left', 0) // 64) + 1))
                ws.add_image(img, f'{anchor_col}2')
                log.info(f'  {chart_label} — 이미지로 삽입됨')
                continue
            except ImportError:
                log.warning(f'  {chart_label} — Pillow(PIL)가 없어서 이미지 삽입 불가 '
                            f'(`pip install Pillow` 후 다시 시도)')
            except Exception as e:
                log.warning(f'  {chart_label} — 이미지 삽입 실패: {e}')
        else:
            log.debug(f'  {chart_label} — JSON에 이미지 데이터 없음(인코딩 시 캡처 실패)')

        log.warning(f'  {chart_label} — 이미지 없음, 수동 재현 필요. '
                    f'종류: {ch.get("chart_type_name") or ch.get("chart_type")}, '
                    f'시리즈: {[s.get("values_formula") for s in ch.get("series", [])]}')


def main():
    if len(sys.argv) < 3:
        print('사용법: python decode_excel.py <encode 출력 폴더> "<결과.xlsx>"')
        print('(결과 파일 경로에 공백이 있으면 반드시 따옴표로 감싸주세요)')
        sys.exit(1)

    folder = os.path.abspath(sys.argv[1])
    if len(sys.argv) > 3:
        # 출력 경로에 공백이 있는데 따옴표 없이 입력하면 쉘이 여러 인자로 쪼개서 뒷부분이
        # 통째로 사라지는 사고가 실제로 있었음(예: "...\신뢰성 OJT.xlsx" → "...\신뢰성"만 저장됨)
        # — 남은 인자를 공백으로 다시 합쳐서 구제한다.
        out_path_raw = ' '.join(sys.argv[2:])
        print(f'[안내] 결과 경로 인자가 여러 개로 쪼개져 들어왔습니다(따옴표 없이 공백 포함 '
              f'경로를 쓰신 것으로 보입니다) — "{out_path_raw}"로 합쳐서 처리합니다. '
              f'다음엔 따옴표로 감싸주세요.')
    else:
        out_path_raw = sys.argv[2]
    if not out_path_raw.lower().endswith(('.xlsx', '.xlsm')):
        print(f'[안내] 결과 경로에 확장자가 없어서 .xlsx를 붙입니다: "{out_path_raw}" -> "{out_path_raw}.xlsx"')
        out_path_raw += '.xlsx'
    out_path = os.path.abspath(out_path_raw)
    out_dir = os.path.dirname(out_path) or '.'
    os.makedirs(out_dir, exist_ok=True)

    log_path = setup_logger(out_dir)
    log.info(f'=== decode_excel.py 시작 === 입력 폴더: {folder}')
    log.info(f'로그 파일: {log_path}')

    try:
        manifest_path = find_manifest(folder)
        log.info(f'JSON 로드: {manifest_path}')
        with open(manifest_path, encoding='utf-8') as f:
            data = json.load(f)

        wb = Workbook()
        sheets = data.get('sheets', [])
        if not sheets:
            log.warning('JSON에 시트가 없습니다.')
        for i, sheet_data in enumerate(sheets):
            build_sheet(wb, sheet_data, is_first=(i == 0))

        apply_defined_names(wb, data.get('defined_names', []))
        add_charts(wb, data.get('charts', []))

        wb.save(out_path)
    except Exception as e:
        log.error(f'치명적 오류로 중단됨: {e}')
        log.error(traceback.format_exc())
        print(f'\n오류로 중단됐습니다. 자세한 내용은 로그 파일을 확인하세요:\n{log_path}')
        sys.exit(1)

    log.info(f'완료: {out_path}')
    print(f'\n완료: {out_path}')
    print(f'로그: {log_path}')
    print('차트는 이미지로만 삽입됐습니다 — 실제 데이터와 연결된 차트가 필요하면')
    print('복원된 셀 값을 기준으로 Excel에서 직접 차트를 새로 만드는 걸 권장합니다.')


if __name__ == '__main__':
    main()
