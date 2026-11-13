# -*- coding: utf-8 -*-
"""
decode_excel.py — DRM 권한이 없거나 DRM 정책이 안 걸리는 PC에서 실행.

encode_excel.py가 뽑아낸 JSON(+ 차트 PNG)을 읽어서 새 xlsx를 조립한다.
openpyxl만 쓰므로 Excel 설치가 필요 없다.

복원되는 것: 셀 값, 수식(문자열로 그대로 넣으면 Excel이 다시 계산함),
기본 서식(굵게/기울임/글꼴색/배경색/숫자서식), 열 너비/행 높이, 정의된
이름(이름관리자). 차트는 기본적으로 "이미지"로만 삽입한다 — 소스 범위를
자동으로 다시 연결하는 건 신뢰도가 낮아서(원본 수식 문자열 파싱이
불완전할 수 있음) 일부러 자동화하지 않았다. 데이터와 연동된 실제 차트가
필요하면, 이 스크립트로 복원된 값들을 기준으로 Excel에서 직접 차트를
새로 만드는 걸 권장한다 — 삽입된 참고 이미지를 보면서 같은 종류/범위로
만들면 된다.

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
import json
import datetime
import logging
import traceback

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass  # 콘솔이 reconfigure를 지원하지 않아도(구버전 등) 계속 진행

from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from openpyxl.styles import Font, PatternFill
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


def apply_defined_names(wb, names):
    log.info(f'정의된 이름(이름관리자) 복원 시작 — {len(names)}개')
    ok = 0
    for n in names:
        name = n.get('name', '') or ''
        refers = n.get('refers_to')
        if not name or not refers:
            log.debug(f'  이름/참조가 비어서 건너뜀: {n}')
            continue
        clean_name = name.split('!')[-1]
        try:
            wb.defined_names[clean_name] = DefinedName(clean_name, attr_text=refers.lstrip('='))
            ok += 1
        except Exception as e:
            log.warning(f'  [이름관리자] "{name}" 복원 실패(수동 확인 필요): {e}')
    log.info(f'정의된 이름 복원 완료 — {ok}/{len(names)}개 성공')


def add_charts(wb, charts, folder):
    log.info(f'차트 삽입 시작 — {len(charts)}개')
    for ch in charts:
        sheet_name = ch.get('sheet')
        chart_label = f'"{ch.get("name")}" ({sheet_name})'
        if sheet_name not in wb.sheetnames:
            log.warning(f'  {chart_label} — 대상 시트가 없어서 건너뜀')
            continue
        ws = wb[sheet_name]

        img_file = ch.get('image_file')
        if img_file:
            img_path = os.path.join(folder, img_file)
            if os.path.exists(img_path):
                try:
                    img = XLImage(img_path)
                    anchor_col = get_column_letter(max(1, int(ch.get('left', 0) // 64) + 1))
                    ws.add_image(img, f'{anchor_col}2')
                    log.info(f'  {chart_label} — 이미지로 삽입됨')
                    continue
                except Exception as e:
                    log.warning(f'  {chart_label} — 이미지 삽입 실패: {e}')
            else:
                log.warning(f'  {chart_label} — 이미지 파일을 못 찾음: {img_path}')

        log.warning(f'  {chart_label} — 이미지 없음, 수동 재현 필요. '
                    f'종류: {ch.get("chart_type_name") or ch.get("chart_type")}, '
                    f'시리즈: {[s.get("values_formula") for s in ch.get("series", [])]}')


def main():
    if len(sys.argv) < 3:
        print('사용법: python decode_excel.py <encode 출력 폴더> <결과.xlsx>')
        sys.exit(1)

    folder = os.path.abspath(sys.argv[1])
    out_path = os.path.abspath(sys.argv[2])
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
        add_charts(wb, data.get('charts', []), folder)

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
