# -*- coding: utf-8 -*-
"""
범용 학습자료 뷰어 (오픽노잼 뷰어 방식 포팅)
- D:\\vscode-git\\기타, D:\\vscode-git\\기타2 밑을 재귀적으로 훑어서
  이미지 base64가 통째로 박혀있는 *_독립.md 파일들을 찾아 목록으로 보여주고,
  선택하면 페이지 단위(한 번에 한 페이지만 표시, 이전/다음 버튼+방향키)로
  이미지 + 추출 텍스트를 렌더링해서 보여주는 로컬 웹 뷰어.
- md가 아닌 파일(xlsx/json 등)은 목록 하단에 다운로드/열기 링크로만 노출.
- 실행: python viewer.py  (또는 run_viewer.bat 더블클릭)
- 브라우저가 자동으로 열리고 http://127.0.0.1:8778 에서 볼 수 있음.
- 외부 라이브러리 설치 필요 없음 (표준 라이브러리만 사용).
"""

import os
import re
import html
import base64
import mimetypes
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs, quote, unquote

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)  # D:\vscode-git
DOC_ROOT_NAMES = ['기타', '기타2']
DOCS_ROOTS = [os.path.join(ROOT_DIR, name) for name in DOC_ROOT_NAMES]
PORT = 8778

IMG_PATTERN = re.compile(
    r'!\[([^\]]*)\]\(data:image/(png|jpeg|jpg|gif);base64,([A-Za-z0-9+/=]+)\)'
)
PAGE_HEADER = re.compile(r'## 페이지 (\d+)\n')
TEXT_BLOCK = re.compile(
    r'<details><summary>텍스트 보기</summary>\n\n```\n(.*?)\n```\n\n</details>', re.S
)
TITLE_PATTERN = re.compile(r'^# (.+)$', re.M)

_cache = {}
_cache_lock = threading.Lock()


def _to_rel(abs_path):
    return os.path.relpath(abs_path, ROOT_DIR).replace('\\', '/')


def _resolve_rel(rel_path):
    """rel_path(ROOT_DIR 기준)를 안전하게 절대경로로 변환. 허용된 루트 밖이면 None."""
    abs_path = os.path.normpath(os.path.join(ROOT_DIR, rel_path))
    for root in DOCS_ROOTS:
        root_norm = os.path.normpath(root)
        if abs_path == root_norm or abs_path.startswith(root_norm + os.sep):
            if os.path.isfile(abs_path):
                return abs_path
    return None


def scan_files():
    """(md_rel_paths, other_rel_paths) 재귀 스캔. 매 요청마다 가볍게 다시 스캔."""
    md_files = []
    other_files = []
    for root in DOCS_ROOTS:
        if not os.path.isdir(root):
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames.sort()
            for fn in sorted(filenames):
                if fn.startswith('.'):
                    continue
                full = os.path.join(dirpath, fn)
                rel = _to_rel(full)
                if fn.endswith('_독립.md'):
                    md_files.append(rel)
                else:
                    other_files.append(rel)
    md_files.sort()
    other_files.sort()
    return md_files, other_files


def parse_doc(rel_path):
    """파일을 파싱해서 [(페이지번호, 텍스트, 이미지바이트, ext), ...] 리스트로 캐싱."""
    with _cache_lock:
        cached = _cache.get(rel_path)
    if cached is not None:
        return cached

    abs_path = _resolve_rel(rel_path)
    if abs_path is None:
        raise FileNotFoundError(rel_path)

    with open(abs_path, encoding='utf-8') as f:
        content = f.read()

    title_m = TITLE_PATTERN.search(content)
    title = title_m.group(1).strip() if title_m else os.path.basename(rel_path)

    pages = []
    parts = PAGE_HEADER.split(content)
    for i in range(1, len(parts), 2):
        num = int(parts[i])
        body = parts[i + 1]
        img_m = IMG_PATTERN.search(body)
        text_m = TEXT_BLOCK.search(body)
        text = text_m.group(1) if text_m else ""
        if img_m:
            ext = img_m.group(2)
            if ext == 'jpg':
                ext = 'jpeg'
            raw = base64.b64decode(img_m.group(3))
            pages.append((num, text, raw, ext))
        else:
            pages.append((num, text, None, None))

    result = {'title': title, 'pages': pages}
    with _cache_lock:
        _cache[rel_path] = result
    return result


PAGE_TEMPLATE = """<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
  :root {{
    --bg:#f7f7f8; --card:#fff; --text:#1d1d1f; --muted:#6b6b70; --accent:#2563eb; --border:#e3e3e6;
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{ --bg:#17181c; --card:#232428; --text:#eceef0; --muted:#9a9ca1; --accent:#6ea8fe; --border:#34353a; }}
  }}
  * {{ box-sizing: border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--text);
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Apple SD Gothic Neo","Malgun Gothic",sans-serif;
    padding:0 16px 24px; }}
  a {{ color: var(--accent); text-decoration:none; }}

  #stickyHead {{
    position: sticky; top: 0; z-index: 20;
    background: var(--bg); margin: 0 -16px; padding: 12px 16px 10px;
    border-bottom: 1px solid var(--border);
  }}
  .head-row {{ max-width:1100px; margin:0 auto; display:flex; align-items:baseline;
    justify-content:space-between; gap:12px; flex-wrap:wrap; }}
  .back {{ display:inline-block; font-size:0.85rem; }}
  h1 {{ font-size:1.2rem; margin:0; }}
  .sub {{ color:var(--muted); font-size:0.85rem; white-space:nowrap; }}

  .controls {{ max-width:1100px; margin:10px auto 0; display:flex; align-items:center;
    justify-content:space-between; gap:12px; flex-wrap:wrap; }}

  .layout-toggle {{ display:flex; gap:6px; flex-shrink:0; }}
  .layout-toggle button {{
    border:1px solid var(--border); background:var(--card); color:var(--text);
    border-radius:6px; padding:5px 10px; font-size:0.8rem; cursor:pointer;
  }}
  .layout-toggle button.active {{ background:var(--accent); color:#fff; border-color:var(--accent); }}

  .pager {{ display:flex; align-items:center; gap:8px; flex-shrink:0; }}
  .pager button {{
    border:1px solid var(--border); background:var(--card); color:var(--text);
    border-radius:6px; padding:5px 10px; font-size:0.85rem; cursor:pointer;
  }}
  .pager button:disabled {{ opacity:0.4; cursor:default; }}

  nav.toc {{ display:flex; flex-wrap:wrap; gap:6px; max-width:1100px; margin:10px auto 0; }}
  nav.toc button {{
    border:1px solid var(--border); background:var(--card); color:var(--text);
    border-radius:6px; padding:3px 9px; font-size:0.8rem; cursor:pointer;
  }}
  nav.toc button.active {{ background:var(--accent); color:#fff; border-color:var(--accent); }}

  main {{ max-width:1100px; margin:18px auto 0; }}
  .slide {{ display:none; background:var(--card); border:1px solid var(--border); border-radius:12px; overflow:hidden; }}
  .slide.active {{ display:flex; flex-direction:column; }}
  main.layout-right .slide.active {{ flex-direction:row; align-items:stretch; }}

  .slide-head {{ padding:9px 14px; font-weight:600; font-size:0.8rem; color:var(--accent);
    border-bottom:1px solid var(--border); }}
  main.layout-right .slide.active .slide-head {{ display:none; }}

  .slide-media {{ display:flex; flex-direction:column; min-width:0; }}
  main.layout-right .slide.active .slide-media {{ flex:1 1 55%; }}
  .slide img {{ display:block; width:100%; height:auto; background:#fff; }}
  .slide-text {{ padding:12px 14px; font-size:0.92rem; line-height:1.6; }}
  main.layout-right .slide.active .slide-text {{ flex:1 1 45%; overflow-y:auto; max-height:80vh;
    border-top:none; border-left:1px solid var(--border); }}

  @media (max-width: 860px) {{
    main.layout-right .slide.active {{ flex-direction:column; }}
    main.layout-right .slide.active .slide-text {{ border-left:none; max-height:none; }}
  }}
</style>
</head>
<body>
<div id="stickyHead">
  <div class="head-row">
    <div>
      <a class="back" href="/">&larr; 목록으로</a>
      <h1>{title}</h1>
    </div>
    <div class="sub">페이지 <span id="curPageNum">1</span> / {count}</div>
  </div>
  <div class="controls">
    <div class="layout-toggle">
      <span class="sub">텍스트 위치:</span>
      <button type="button" data-layout="col" class="active">아래</button>
      <button type="button" data-layout="row">오른쪽</button>
    </div>
    <div class="pager">
      <button type="button" id="prevBtn">&#9664; 이전</button>
      <button type="button" id="nextBtn">다음 &#9654;</button>
    </div>
  </div>
  <nav class="toc" id="toc">{toc}</nav>
</div>
<main id="pageArea">{sections}</main>
<script>
(function() {{
  var main = document.getElementById('pageArea');
  var slides = Array.prototype.slice.call(main.querySelectorAll('.slide'));
  var tocBtns = Array.prototype.slice.call(document.querySelectorAll('#toc button'));
  var curNum = document.getElementById('curPageNum');
  var prevBtn = document.getElementById('prevBtn');
  var nextBtn = document.getElementById('nextBtn');
  var total = slides.length;

  function pageIndexFromHash() {{
    var m = /^#p(\\d+)$/.exec(location.hash);
    if (m) {{
      var idx = slides.findIndex(function(s) {{ return s.id === 'p' + m[1]; }});
      if (idx >= 0) return idx;
    }}
    return 0;
  }}

  var current = pageIndexFromHash();

  function show(idx) {{
    if (idx < 0) idx = 0;
    if (idx >= total) idx = total - 1;
    current = idx;
    slides.forEach(function(s, i) {{ s.classList.toggle('active', i === idx); }});
    tocBtns.forEach(function(b, i) {{ b.classList.toggle('active', i === idx); }});
    curNum.textContent = idx + 1;
    prevBtn.disabled = idx === 0;
    nextBtn.disabled = idx === total - 1;
    history.replaceState(null, '', '#' + slides[idx].id);
    var activeTocBtn = tocBtns[idx];
    if (activeTocBtn && activeTocBtn.scrollIntoView) {{
      activeTocBtn.scrollIntoView({{ block: 'nearest', inline: 'nearest' }});
    }}
  }}

  tocBtns.forEach(function(b, i) {{
    b.addEventListener('click', function() {{ show(i); }});
  }});
  prevBtn.addEventListener('click', function() {{ show(current - 1); }});
  nextBtn.addEventListener('click', function() {{ show(current + 1); }});
  document.addEventListener('keydown', function(e) {{
    if (e.key === 'ArrowLeft') show(current - 1);
    if (e.key === 'ArrowRight') show(current + 1);
  }});

  var layoutBtns = Array.prototype.slice.call(document.querySelectorAll('.layout-toggle button'));
  function applyLayout(mode) {{
    main.classList.toggle('layout-right', mode === 'row');
    layoutBtns.forEach(function(b) {{ b.classList.toggle('active', b.dataset.layout === mode); }});
    try {{ localStorage.setItem('viewer_layout', mode); }} catch (e) {{}}
  }}
  layoutBtns.forEach(function(b) {{
    b.addEventListener('click', function() {{ applyLayout(b.dataset.layout); }});
  }});
  var savedLayout = 'col';
  try {{ savedLayout = localStorage.getItem('viewer_layout') || 'col'; }} catch (e) {{}}
  applyLayout(savedLayout);

  show(current);
}})();
</script>
</body>
</html>"""

LIST_TEMPLATE = """<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>범용 학습자료 뷰어</title>
<style>
  :root {{ --bg:#f7f7f8; --card:#fff; --text:#1d1d1f; --muted:#6b6b70; --accent:#2563eb; --border:#e3e3e6; }}
  @media (prefers-color-scheme: dark) {{
    :root {{ --bg:#17181c; --card:#232428; --text:#eceef0; --muted:#9a9ca1; --accent:#6ea8fe; --border:#34353a; }}
  }}
  * {{ box-sizing: border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--text);
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Apple SD Gothic Neo","Malgun Gothic",sans-serif;
    padding:16px; }}
  header {{ max-width:900px; margin:0 auto 16px; }}
  h1 {{ font-size:1.3rem; margin:0 0 4px; }}
  .sub {{ color:var(--muted); font-size:0.9rem; }}
  #search {{
    width:100%; max-width:900px; display:block; margin:0 auto 16px; padding:10px 12px;
    border-radius:8px; border:1px solid var(--border); background:var(--card); color:var(--text); font-size:0.95rem;
  }}
  main {{ max-width:900px; margin:0 auto; }}
  details.folder {{ border:1px solid var(--border); border-radius:8px; margin-bottom:8px; background:var(--card); }}
  details.folder > summary {{ cursor:pointer; padding:8px 12px; font-weight:600; list-style:none; }}
  details.folder > summary::-webkit-details-marker {{ display:none; }}
  .count {{ color:var(--muted); font-weight:400; font-size:0.85rem; }}
  .folder-body {{ padding:4px 12px 10px 24px; display:flex; flex-direction:column; gap:4px; }}
  a.doc-link {{ color:var(--accent); text-decoration:none; padding:4px 6px; border-radius:6px; font-size:0.9rem; }}
  a.doc-link:hover {{ background:var(--border); }}
  a.doc-link.other {{ color:var(--muted); }}
  .hidden {{ display:none !important; }}
</style>
</head>
<body>
<header>
  <h1>범용 학습자료 뷰어</h1>
  <div class="sub">총 {count}개 문서 · 기타, 기타2 하위 _독립.md 슬라이드 자료</div>
</header>
<input id="search" type="text" placeholder="파일(제목)로 검색...">
<main id="list">
{body}
{other}
</main>
<script>
  var search = document.getElementById('search');
  search.addEventListener('input', function() {{
    var q = search.value.trim().toLowerCase();
    document.querySelectorAll('a.doc-link').forEach(function(a) {{
      var match = !q || a.textContent.toLowerCase().indexOf(q) !== -1;
      a.classList.toggle('hidden', !match);
    }});
    document.querySelectorAll('details.folder').forEach(function(d) {{
      var anyVisible = d.querySelectorAll('a.doc-link:not(.hidden)').length > 0;
      d.classList.toggle('hidden', !!q && !anyVisible);
      if (q && anyVisible) d.open = true;
    }});
  }});
</script>
</body>
</html>"""


def render_doc_page(rel_path):
    doc = parse_doc(rel_path)
    toc = ' '.join(f'<button type="button">{num}</button>' for num, _, _, _ in doc['pages'])
    sections = []
    for num, text, raw, ext in doc['pages']:
        esc_text = html.escape(text).replace('\n', '<br>')
        img_tag = (
            f'<img src="/img?file={quote(rel_path)}&idx={num}" alt="페이지 {num}" loading="lazy">'
            if raw else ''
        )
        sections.append(
            f'<section class="slide" id="p{num}">'
            f'<div class="slide-head">페이지 {num}</div>'
            f'<div class="slide-media">{img_tag}</div>'
            f'<div class="slide-text">{esc_text}</div>'
            f'</section>'
        )
    return PAGE_TEMPLATE.format(
        title=html.escape(doc['title']),
        count=len(doc['pages']),
        toc=toc,
        sections=''.join(sections),
    )


def _build_tree(md_files):
    root = {'files': [], 'subs': {}}
    for rel in md_files:
        parts = rel.split('/')
        node = root
        for p in parts[:-1]:
            node = node['subs'].setdefault(p, {'files': [], 'subs': {}})
        display = re.sub(r'_독립\.md$', '', parts[-1])
        node['files'].append((display, rel))
    return root


def _count_files(node):
    c = len(node['files'])
    for sub in node['subs'].values():
        c += _count_files(sub)
    return c


def _render_node(node, label, depth):
    out = [f'<details {"open" if depth < 1 else ""} class="folder">']
    out.append(f'<summary>{html.escape(label)} <span class="count">({_count_files(node)})</span></summary>')
    out.append('<div class="folder-body">')
    for name in sorted(node['subs'].keys()):
        out.append(_render_node(node['subs'][name], name, depth + 1))
    for display, rel in sorted(node['files']):
        out.append(f'<a class="doc-link" href="/doc?file={quote(rel)}">{html.escape(display)}</a>')
    out.append('</div></details>')
    return '\n'.join(out)


def render_list():
    md_files, other_files = scan_files()
    tree = _build_tree(md_files)
    body_parts = [_render_node(tree['subs'][top], top, 0) for top in sorted(tree['subs'].keys())]

    other_html = ''
    if other_files:
        items = '\n'.join(
            f'<a class="doc-link other" href="/raw?file={quote(rel)}">{html.escape(rel)}</a>'
            for rel in other_files
        )
        other_html = (
            '<details class="folder"><summary>관리 밖 파일 (다운로드/열기) '
            f'<span class="count">({len(other_files)})</span></summary>'
            f'<div class="folder-body">{items}</div></details>'
        )

    return LIST_TEMPLATE.format(count=len(md_files), body=''.join(body_parts), other=other_html)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # 콘솔 조용하게

    def _send_html(self, body, status=200):
        data = body.encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)

        if parsed.path == '/':
            self._send_html(render_list())
            return

        if parsed.path == '/doc':
            rel_path = unquote(qs.get('file', [''])[0])
            if _resolve_rel(rel_path) is None or not rel_path.endswith('_독립.md'):
                self._send_html('<h1>파일을 찾을 수 없습니다.</h1>', 404)
                return
            try:
                self._send_html(render_doc_page(rel_path))
            except Exception as e:
                self._send_html(f'<pre>오류: {html.escape(str(e))}</pre>', 500)
            return

        if parsed.path == '/img':
            rel_path = unquote(qs.get('file', [''])[0])
            idx = int(qs.get('idx', ['0'])[0])
            if _resolve_rel(rel_path) is None:
                self.send_response(404)
                self.end_headers()
                return
            try:
                doc = parse_doc(rel_path)
            except Exception:
                self.send_response(404)
                self.end_headers()
                return
            found = None
            for num, text, raw, ext in doc['pages']:
                if num == idx and raw:
                    found = (raw, ext)
                    break
            if not found:
                self.send_response(404)
                self.end_headers()
                return
            raw, ext = found
            self.send_response(200)
            self.send_header('Content-Type', f'image/{ext}')
            self.send_header('Content-Length', str(len(raw)))
            self.send_header('Cache-Control', 'max-age=3600')
            self.end_headers()
            self.wfile.write(raw)
            return

        if parsed.path == '/raw':
            rel_path = unquote(qs.get('file', [''])[0])
            abs_path = _resolve_rel(rel_path)
            if abs_path is None:
                self.send_response(404)
                self.end_headers()
                return
            ctype = mimetypes.guess_type(abs_path)[0] or 'application/octet-stream'
            size = os.path.getsize(abs_path)
            fname = os.path.basename(abs_path)
            self.send_response(200)
            self.send_header('Content-Type', ctype)
            self.send_header('Content-Length', str(size))
            self.send_header(
                'Content-Disposition',
                "inline; filename*=UTF-8''" + quote(fname),
            )
            self.end_headers()
            with open(abs_path, 'rb') as f:
                while True:
                    chunk = f.read(65536)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
            return

        self.send_response(404)
        self.end_headers()


def main():
    server = ThreadingHTTPServer(('127.0.0.1', PORT), Handler)
    url = f'http://127.0.0.1:{PORT}/'
    print(f'뷰어 서버 시작: {url}  (종료하려면 Ctrl+C)')
    threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
