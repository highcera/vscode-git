# -*- coding: utf-8 -*-
"""
오픽노잼 학습자료 뷰어
- 폴더 안의 .md 파일(이미지 base64가 통째로 박혀있는 파일)들을 목록으로 보여주고,
  선택하면 페이지별로 이미지 + 추출 텍스트를 렌더링해서 보여주는 로컬 웹 뷰어.
- 실행: python viewer.py  (또는 run_viewer.bat 더블클릭)
- 브라우저가 자동으로 열리고 http://127.0.0.1:8777 에서 볼 수 있음.
- 외부 라이브러리 설치 필요 없음 (표준 라이브러리만 사용).
"""

import os
import re
import html
import base64
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs, quote, unquote

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOCS_DIR = os.path.dirname(BASE_DIR)  # 상위 폴더(오픽노잼)의 .md 파일들을 대상으로 함
PORT = 8777

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


def list_md_files():
    files = [f for f in os.listdir(DOCS_DIR) if f.lower().endswith('.md')]
    files.sort()
    return files


def parse_doc(filename):
    """파일을 파싱해서 [(페이지번호, 텍스트, 이미지바이트, ext), ...] 리스트로 캐싱."""
    with _cache_lock:
        if filename in _cache:
            return _cache[filename]

    path = os.path.join(DOCS_DIR, filename)
    with open(path, encoding='utf-8') as f:
        content = f.read()

    title_m = TITLE_PATTERN.search(content)
    title = title_m.group(1).strip() if title_m else filename

    # 이미지들을 순서대로 추출하면서, 각 이미지 뒤에 바로 오는 텍스트 블록도 같이 수집
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
        _cache[filename] = result
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
    try {{ localStorage.setItem('opic_viewer_layout', mode); }} catch (e) {{}}
  }}
  layoutBtns.forEach(function(b) {{
    b.addEventListener('click', function() {{ applyLayout(b.dataset.layout); }});
  }});
  var savedLayout = 'col';
  try {{ savedLayout = localStorage.getItem('opic_viewer_layout') || 'col'; }} catch (e) {{}}
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
<title>오픽노잼 학습자료 뷰어</title>
<style>
  :root {{ --bg:#f7f7f8; --card:#fff; --text:#1d1d1f; --muted:#6b6b70; --accent:#2563eb; --border:#e3e3e6; }}
  @media (prefers-color-scheme: dark) {{
    :root {{ --bg:#17181c; --card:#232428; --text:#eceef0; --muted:#9a9ca1; --accent:#6ea8fe; --border:#34353a; }}
  }}
  * {{ box-sizing: border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--text);
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Apple SD Gothic Neo","Malgun Gothic",sans-serif;
    padding:16px; }}
  h1 {{ max-width:640px; margin:0 auto 16px; font-size:1.3rem; }}
  ul {{ max-width:640px; margin:0 auto; list-style:none; padding:0; display:flex; flex-direction:column; gap:8px; }}
  li a {{ display:block; background:var(--card); border:1px solid var(--border); border-radius:10px;
    padding:12px 14px; color:var(--text); text-decoration:none; font-size:0.95rem; }}
  li a:hover {{ border-color: var(--accent); }}
</style>
</head>
<body>
<h1>오픽노잼 학습자료 뷰어 ({count}개 파일)</h1>
<ul>{items}</ul>
</body>
</html>"""


def render_doc_page(filename):
    doc = parse_doc(filename)
    toc = ' '.join(f'<button type="button">{num}</button>' for num, _, _, _ in doc['pages'])
    sections = []
    for num, text, raw, ext in doc['pages']:
        esc_text = html.escape(text).replace('\n', '<br>')
        img_tag = (
            f'<img src="/img?file={quote(filename)}&idx={num}" alt="페이지 {num}" loading="lazy">'
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


def render_list():
    files = list_md_files()
    items = []
    for f in files:
        display = re.sub(r'_독립\.md$', '', f)
        items.append(f'<li><a href="/doc?file={quote(f)}">{html.escape(display)}</a></li>')
    return LIST_TEMPLATE.format(count=len(files), items=''.join(items))


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
            filename = unquote(qs.get('file', [''])[0])
            if filename not in list_md_files():
                self._send_html('<h1>파일을 찾을 수 없습니다.</h1>', 404)
                return
            try:
                self._send_html(render_doc_page(filename))
            except Exception as e:
                self._send_html(f'<pre>오류: {html.escape(str(e))}</pre>', 500)
            return

        if parsed.path == '/img':
            filename = unquote(qs.get('file', [''])[0])
            idx = int(qs.get('idx', ['0'])[0])
            if filename not in list_md_files():
                self.send_response(404)
                self.end_headers()
                return
            doc = parse_doc(filename)
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
