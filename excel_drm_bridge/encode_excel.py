# -*- coding: utf-8 -*-
"""
encode_excel.py — DRM 권한이 있는 PC에서 실행.

DRM이 걸린 xlsx를 "진짜 Excel"로 정상 오픈(DRM 인증을 그대로 통과)한 뒤,
그 Excel 객체 모델(COM)에서 셀 값/수식/기본 서식/정의된 이름(이름관리자)/
차트 정보를 읽어서 비(非)엑셀 포맷(JSON + PNG)으로 저장한다.

이 PC의 DRM 정책은 "xlsx로 저장하면 자동으로 암호화"되는 방식이라고
확인했으므로(md/txt는 안 걸림), 출력은 전부 JSON/PNG로만 내보낸다 —
이 스크립트 자체가 DRM 암호화를 풀거나 우회하는 게 아니라, 사용자가 이미
정상적으로 열람·편집 권한을 가진 세션에서 보이는 내용을 받아적는 것뿐이다.

사전 준비:
  pip install pywin32
  대상 파일을 Excel로 더블클릭해서 정상적으로 열리는 상태(DRM 인증 완료)여야 함.

사용법:
  python encode_excel.py "D:\\경로\\대상.xlsx" "D:\\경로\\출력폴더"

출력:
  출력폴더\\<원본파일명>.json          — 시트별 셀 그리드, 정의된 이름, 차트 메타데이터
  출력폴더\\chart_<시트>_<차트명>.png   — 차트 스냅샷(참고/대체용 이미지)
  출력폴더\\encode_log_<시각>.txt      — 진행 단계/경고/오류를 전부 남기는 로그.
                                      예상 못한 문제(특정 셀에서 멈춤, 서식 못 읽음,
                                      차트 추출 실패, COM 자체 오류 등)가 생기면
                                      이 로그를 보고 어디서 어떤 예외가 났는지 확인한다.

주의:
  - 서식(글꼴/색/번호서식)은 셀 수가 너무 많으면(MAX_FORMAT_CELLS 초과) 건너뛴다.
    값/수식은 항상 전부 뽑는다.
  - 차트는 "종류 + 소스 범위 문자열 + 스냅샷 이미지"까지만 뽑는다. 완전히
    동일한 차트 객체를 코드로 자동 재현하는 건 신뢰도가 낮아서, decode_excel.py는
    기본적으로 이미지로만 삽입하고, 실제 데이터 연동 차트가 필요하면 복원된
    값을 기준으로 Excel에서 직접 새로 만드는 걸 권장한다(README 참고).
  - 조건부 서식 "규칙" 자체는 이 스크립트가 다루지 않는다(결과로 보이는 색만
    fill_rgb로 캡처됨) — 규칙이 중요하면 서식 규칙 관리자를 눈으로 보고 따로 적어둘 것.
"""

import sys
import os
import json
import re
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
    -4169: 'scatter',
}

MAX_FORMAT_CELLS = 8000  # 서식까지 셀 단위로 읽을 때 너무 느려지지 않게 상한
XL_NONE_COLOR_INDEX = -4142

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


def normalize_grid(values, formulas, n_rows, n_cols):
    """COM은 셀이 1개면 스칼라, 1행/1열이면 1중 튜플을 주므로 2중 튜플로 통일."""
    if n_rows == 1 and n_cols == 1:
        return ((values,),), ((formulas,),)
    if n_rows == 1:
        return (tuple(values),), (tuple(formulas),)
    if n_cols == 1:
        return tuple((v,) for v in values), tuple((f,) for f in formulas)
    return values, formulas


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
    do_format = (n_rows * n_cols) <= MAX_FORMAT_CELLS
    if not do_format:
        log.warning(f'  [{ws.Name}] 셀 수({n_rows*n_cols})가 MAX_FORMAT_CELLS({MAX_FORMAT_CELLS})를 '
                    f'넘어서 서식(글꼴/색/번호서식)은 건너뜀 — 값/수식만 추출')

    cells = []
    format_fail_count = 0
    for i in range(n_rows):
        for j in range(n_cols):
            val = values[i][j]
            formula = formulas[i][j]
            if val is None and (formula in (None, '')):
                continue

            row = start_row + i
            col = start_col + j
            cell_info = {'row': row, 'col': col, 'value': json_safe(val)}
            if isinstance(formula, str) and formula.startswith('='):
                cell_info['formula'] = formula

            if do_format:
                try:
                    rng = ws.Cells(row, col)
                    nf = rng.NumberFormat
                    if nf and nf != 'General':
                        cell_info['number_format'] = nf
                    if rng.Font.Bold:
                        cell_info['bold'] = True
                    if rng.Font.Italic:
                        cell_info['italic'] = True
                    try:
                        if rng.Interior.ColorIndex != XL_NONE_COLOR_INDEX:
                            cell_info['fill_rgb'] = bgr_long_to_rrggbb(rng.Interior.Color)
                    except Exception as e:
                        log.debug(f'  [{ws.Name}] R{row}C{col} 배경색 읽기 실패: {e}')
                    try:
                        fc = rng.Font.Color
                        if fc is not None:
                            cell_info['font_rgb'] = bgr_long_to_rrggbb(fc)
                    except Exception as e:
                        log.debug(f'  [{ws.Name}] R{row}C{col} 글꼴색 읽기 실패: {e}')
                except Exception as e:
                    format_fail_count += 1
                    log.warning(f'  [{ws.Name}] R{row}C{col} 서식 전체 읽기 실패: {e}')
            cells.append(cell_info)

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


def extract_charts(wb, out_dir):
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
                    series.append({
                        'name': str(sc.Name) if sc.Name else None,
                        'values_formula': sc.Formula,
                    })
            except Exception as e:
                log.warning(f'  [{ws.Name}] 차트 "{co.Name}" 시리즈 읽기 실패: {e}')
            info['series'] = series

            safe_name = re.sub(r'[^A-Za-z0-9가-힣_-]', '_', f'{ws.Name}_{co.Name}')
            img_name = f'chart_{safe_name}.png'
            try:
                chart.Export(os.path.join(out_dir, img_name), 'PNG')
                info['image_file'] = img_name
            except Exception as e:
                log.warning(f'  [{ws.Name}] 차트 "{co.Name}" PNG 내보내기 실패 '
                            f'(복원 시 이미지 없이 메타데이터만 남음): {e}')
                info['image_file'] = None

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
            'charts': extract_charts(wb, out_dir),
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
