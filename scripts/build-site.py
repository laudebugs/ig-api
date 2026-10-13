#!/usr/bin/env python3
"""Build a static multi-page HTML docs site from the Markdown sources.

Stdlib only. Usage: python scripts/build-site.py  (writes into site/)
Pages: index.html (README) + api-reference.html + formats.html + docs/*.html,
plus verbatim copies of linked assets (openapi.yaml, examples/, ...) so every
relative link resolves on GitHub Pages.
Optional browser-side Shiki highlighting loads from a pinned CDN URL; code
and navigation remain usable without it or without JavaScript.
"""
import html
import pathlib
import re
import shutil

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = ROOT / "site"

# (source markdown, output html relative to site/, nav label)
PAGES = [
    (ROOT / "README.md", "index.html", "Home"),
    (ROOT / "INSTAGRAM_GRAPH_API.md", "api-reference.html", "API Reference"),
    (ROOT / "FORMATS.md", "formats.html", "Formats"),
]
GUIDE_SOURCES = sorted((ROOT / "docs").glob("*.md"))
for src in GUIDE_SOURCES:
    PAGES.append((src, f"docs/{src.stem}.html", src.stem.replace("-", " ").title()))

# stem renames when mapping *.md links to built pages
STEM_MAP = {"README": "index", "INSTAGRAM_GRAPH_API": "api-reference", "FORMATS": "formats"}

# repo files/dirs copied verbatim into site/ so relative links work
STATIC_COPIES = ["openapi.yaml", "llms.txt", "llms-full.txt", "types", "examples",
                 "data", "postman", "bruno", "mcp", "scripts", ".github"]

CSS = """
:root{--fg:#293b38;--bg:#fffdf9;--muted:#586963;--code:#f3eadc;--accent:#24665c;--border:#dfdfd3;--tint:#e8f0e9}
*{box-sizing:border-box}body{font-family:"Trebuchet MS","Segoe UI",sans-serif;margin:0;color:var(--fg);background:var(--bg);line-height:1.7}
a{color:var(--accent);text-underline-offset:.2em}a:hover{text-decoration-thickness:2px}
:focus-visible{outline:3px solid var(--accent);outline-offset:4px}
.skip-link{position:absolute;left:1rem;top:-5rem;background:var(--bg);padding:.6rem;z-index:2}.skip-link:focus{top:1rem}
.layout{display:flex;min-height:100vh;max-width:1440px;margin:auto}
.sidebar{width:280px;flex-shrink:0;border-right:1px solid var(--border);background:#f5f5ee;padding:1.5rem;position:sticky;top:0;height:100vh;overflow:auto}
.brand{display:block;font-family:Georgia,serif;font-size:1.5rem;font-weight:bold;color:var(--fg);text-decoration:none}
.tagline{margin:.25rem 0 1.5rem;color:var(--muted);font-size:.85rem}
.navigation summary{display:none}.navigation nav{display:block}
nav input{width:100%;padding:.7rem;border:1px solid var(--border);border-radius:8px;background:var(--bg);font:inherit;font-size:.85rem}
nav a{display:block;color:var(--fg);text-decoration:none;padding:.4rem .65rem;font-size:.9rem;border-radius:6px;margin:.15rem 0;overflow-wrap:anywhere}
nav a[hidden]{display:none}
nav a.h3{padding-left:1.3rem;color:var(--muted);font-size:.83rem}nav a:hover{color:var(--accent);background:var(--tint)}
nav .group{font-size:.7rem;text-transform:uppercase;letter-spacing:.12em;color:var(--muted);margin:1.5rem 0 .5rem;font-weight:bold}
nav a.current{font-weight:bold;color:var(--accent);background:var(--tint);box-shadow:inset 3px 0 var(--accent)}
main{width:100%;min-width:0;max-width:1000px;padding:3rem 4rem}
.eyebrow{color:var(--accent);font-size:.75rem;text-transform:uppercase;letter-spacing:.12em;font-weight:bold}
h1,h2,h3{scroll-margin-top:1.5rem;line-height:1.25}
h1,h2{font-family:Georgia,"Times New Roman",serif;font-weight:normal;letter-spacing:-.025em}
h1{font-size:clamp(2rem,4vw,3rem);margin:.8rem 0 1.5rem}h2{font-size:1.8rem;margin-top:2.5rem;border-bottom:1px solid var(--border);padding-bottom:.6rem}
h3{font-size:1.15rem;margin-top:1.8rem}p,li{overflow-wrap:anywhere}li{margin:.3rem 0}
.code-block{margin:1.5rem 0;border:1px solid #dfd0b8;border-radius:10px;overflow:hidden;background:var(--code)}
.code-language{display:block;padding:.4rem 1rem;border-bottom:1px solid #dfd0b8;color:#66553e;font-size:.7rem;font-weight:bold;text-transform:uppercase;letter-spacing:.1em}
pre{background:var(--code);color:#24292e;margin:0;padding:1rem;overflow:auto;line-height:1.6}
code{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.86em;background:var(--code);padding:.15em .3em;border-radius:4px}
pre code{background:none;padding:0;border-radius:0}
.table-wrap{overflow:auto;margin:1.5rem 0;border:1px solid var(--border);border-radius:8px}
table{border-collapse:collapse;width:100%}th,td{border-bottom:1px solid var(--border);padding:.7rem .8rem;text-align:left;font-size:.88rem}
th{background:var(--tint)}tr:last-child td{border-bottom:0}
blockquote{border-left:3px solid var(--accent);background:var(--tint);border-radius:0 8px 8px 0;margin:1.5rem 0;padding:.8rem 1.2rem;color:var(--muted)}
hr{border:0;border-top:1px solid var(--border);margin:2rem 0}
.page-nav{display:flex;gap:1rem;justify-content:space-between;margin-top:3rem;padding-top:1.5rem;border-top:1px solid var(--border)}
.page-nav a{flex:1;max-width:50%;padding:1rem;border:1px solid var(--border);border-radius:8px;text-decoration:none;overflow-wrap:anywhere}
.page-nav a:hover{background:var(--tint)}.page-nav small{display:block;color:var(--muted)}.page-nav .next{margin-left:auto;text-align:right}
@media(max-width:1050px){main{padding:2.5rem 2rem}.sidebar{width:250px}}
@media(max-width:800px){.layout{display:block}.sidebar{position:static;width:100%;height:auto;padding:1rem 1.25rem;border-right:0;border-bottom:1px solid var(--border)}
.tagline{margin-bottom:.75rem}.navigation summary{display:list-item;cursor:pointer;color:var(--accent);font-weight:bold;padding:.5rem 0}
.navigation:not([open]) nav{display:none}main{padding:1.5rem 1.25rem}.page-nav{gap:.6rem}.page-nav a{padding:.75rem}}
"""

HIGHLIGHT_JS = """
<script type="module">
try {
  const blocks = [...document.querySelectorAll('pre code')];
  if (blocks.length) {
    const { createHighlighter } = await import('https://cdn.jsdelivr.net/npm/shiki@4.5.0/dist/bundle-web.mjs/+esm');
    const highlighter = await createHighlighter({
      themes: ['github-light'], langs: ['bash', 'typescript', 'python', 'json', 'html']
    });
    const aliases = {ts: 'typescript', sh: 'bash', shell: 'bash', py: 'python'};
    const supported = new Set(highlighter.getLoadedLanguages());
    for (const block of blocks) {
      const raw = block.className.replace('language-', '');
      const lang = aliases[raw] || raw;
      const { tokens } = highlighter.codeToTokens(block.textContent, {
        lang: supported.has(lang) ? lang : 'text', theme: 'github-light'
      });
      const content = document.createDocumentFragment();
      tokens.forEach((line, index) => {
        if (index) content.append(document.createTextNode('\\n'));
        for (const token of line) {
          const span = document.createElement('span');
          span.textContent = token.content;
          span.style.color = token.color;
          content.append(span);
        }
      });
      block.replaceChildren(content);
    }
    highlighter.dispose();
  }
} catch {
  // Keep readable, escaped code when the highlighter is unavailable.
}
</script>
"""


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def map_md_link(target):
    """Rewrite a markdownHref *.md link to its built *.html page, preserving #fragments."""
    if re.match(r"^(https?:|mailto:|#)", target):
        return target
    path, hashmark, frag = target.partition("#")
    if path == "site" or path == "site/":
        path = "index.html"
    elif path.startswith("site/"):
        path = path[len("site/"):]
    if not path.endswith(".md"):
        return path + (hashmark + frag if hashmark else "")
    head, sep, stem = path.rpartition("/")
    stem = STEM_MAP.get(stem[:-3], stem[:-3])
    mapped = f"{head}{sep}{stem}.html" if sep else f"{stem}.html"
    return mapped + (hashmark + frag if hashmark else "")


def inline(text):
    text = html.escape(text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)

    def link(m):
        return f'<a href="{map_md_link(m.group(2))}">{m.group(1)}</a>'

    return re.sub(r"\[([^\]]+)\]\(([^)]+)\)", link, text)


def convert(md):
    """Minimal Markdown subset: fences, tables, headings, lists, quotes, rules, paragraphs."""
    lines = md.splitlines()
    out, toc = [], []
    i, in_list = 0, False
    while i < len(lines):
        line = lines[i]
        if line.startswith("```"):
            lang = line[3:].strip()
            buf = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            language = html.escape(lang or "text")
            out.append(f'<div class="code-block"><span class="code-language">{language}</span>'
                       f'<pre tabindex="0" aria-label="{language} code example"><code class="language-{language}">'
                       f'{html.escape(chr(10).join(buf))}</code></pre></div>')
            continue
        if line.startswith("|") and i + 1 < len(lines) and re.match(r"^\|[\s:|-]+\|$", lines[i + 1] or ""):
            headers = [c.strip() for c in line.strip().strip("|").split("|")]
            i += 2
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            thead = "".join(f"<th>{inline(c)}</th>" for c in headers)
            tbody = "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in rows)
            out.append(f'<div class="table-wrap"><table><thead><tr>{thead}</tr></thead><tbody>{tbody}</tbody></table></div>')
            continue
        m = re.match(r"^(#{1,4})\s+(.*)", line)
        if m:
            if in_list:
                out.append("</ul>")
                in_list = False
            level, text = len(m.group(1)), m.group(2).strip()
            ident = slug(re.sub(r"[#*`]", "", text))
            if level in (2, 3):
                toc.append((level, ident, re.sub(r"[#*`]", "", text)))
            out.append(f"<h{level} id=\"{ident}\">{inline(text)}</h{level}>")
            i += 1
            continue
        if re.match(r"^(\s*[-*]|\s*\d+\.)\s+", line):
            if not in_list:
                out.append("<ul>")
                in_list = True
            item = re.sub(r"^(\s*[-*]|\s*\d+\.)\s+", "", line)
            if item.strip().startswith("[ ]") or item.strip().startswith("[x]"):
                item = "☐ " + item.strip()[3:] if item.strip().startswith("[ ]") else "☑ " + item.strip()[3:]
            out.append(f"<li>{inline(item)}</li>")
            i += 1
            continue
        if line.startswith(">"):
            if in_list:
                out.append("</ul>")
                in_list = False
            buf = []
            while i < len(lines) and lines[i].startswith(">"):
                buf.append(lines[i][1:].strip())
                i += 1
            out.append(f"<blockquote>{inline(' '.join(buf))}</blockquote>")
            continue
        if re.match(r"^-{3,}$", line.strip()):
            if in_list:
                out.append("</ul>")
                in_list = False
            out.append("<hr>")
            i += 1
            continue
        if not line.strip():
            if in_list:
                out.append("</ul>")
                in_list = False
            i += 1
            continue
        if in_list:
            out.append("</ul>")
            in_list = False
        buf = [line]
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(r"^(#{1,4}\s|```|\||\s*[-*]\s|\s*\d+\.\s|>|-{3,}$)", lines[i]):
            buf.append(lines[i].strip())
            i += 1
        out.append(f"<p>{inline(' '.join(b.strip() for b in buf))}</p>")
    if in_list:
        out.append("</ul>")
    return "\n".join(out), toc


def title_of(md):
    m = re.search(r"^#\s+(.*)", md, re.M)
    return re.sub(r"[#*`]", "", m.group(1)).strip() if m else "Docs"


def render_page(label, title, body, toc, out_rel):
    depth = out_rel.count("/")

    def href_for(target_rel):
        # cross-page nav links, relative to the current page's directory
        if depth == 0:
            return target_rel
        if target_rel.startswith("docs/"):
            return target_rel.split("/", 1)[1]
        return "../" + target_rel
        if depth == 0:
            return target_rel
        if target_rel.startswith("docs/"):
            return target_rel.split("/", 1)[1]
        return "../" + target_rel

    nav = ['<input id="q" type="search" aria-label="Filter pages and sections" placeholder="Find a page or section…" oninput="filterNav()">']
    nav.append('<div class="group">Pages</div>')
    for _, rel, page_label in PAGES:
        cls = ' class="current" aria-current="page"' if rel == out_rel else ""
        nav.append(f'<a href="{href_for(rel)}"{cls}>{html.escape(page_label)}</a>')
    nav.append('<div class="group">On this page</div>')
    for level, ident, text in toc:
        nav.append(f'<a class="h{level}" href="#{ident}">{html.escape(text)}</a>')
    page_index = next(i for i, (_, rel, _) in enumerate(PAGES) if rel == out_rel)
    pagination = []
    for index, direction in ((page_index - 1, "Previous"), (page_index + 1, "Next")):
        if 0 <= index < len(PAGES):
            _, rel, page_label = PAGES[index]
            pagination.append(f'<a class="{direction.lower()}" href="{href_for(rel)}" rel="{("prev" if direction == "Previous" else "next")}">'
                              f'<small>{direction} page</small>{html.escape(page_label)}</a>')
    js = ("<script>function filterNav(){const q=document.getElementById('q').value.toLowerCase();"
          "document.querySelectorAll('#page-navigation a').forEach(a=>{a.hidden=!a.textContent.toLowerCase().includes(q);});}"
          "const mobile=window.matchMedia('(max-width:800px)');"
          "function updateNavigation(){document.querySelector('.navigation').open=!mobile.matches;}"
          "updateNavigation();mobile.addEventListener('change',updateNavigation);</script>")
    return ("<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
            "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
            f"<title>{html.escape(title)} — Instagram API Docs</title>"
            f'<style>{CSS}</style></head><body><a class="skip-link" href="#content">Skip to content</a><div class="layout">'
            f'<aside class="sidebar"><a class="brand" href="{href_for("index.html")}">Instagram API</a>'
            '<p class="tagline">A practical guide to building with Instagram.</p>'
            f'<details class="navigation" open><summary>Browse documentation</summary><nav id="page-navigation" aria-label="Documentation">{"".join(nav)}</nav></details></aside>'
            f'<main id="content" tabindex="-1"><div class="eyebrow">Documentation / {html.escape(label)}</div>{body}'
            f'<nav class="page-nav" aria-label="Previous and next pages">{"".join(pagination)}</nav></main></div>{js}{HIGHLIGHT_JS}</body></html>')


def main():
    if SITE.exists():
        shutil.rmtree(SITE)
    (SITE / "docs").mkdir(parents=True)
    for src, rel, label in PAGES:
        md = src.read_text(encoding="utf-8")
        body, toc = convert(md)
        page = render_page(label, title_of(md), body, toc, rel)
        dest = SITE / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(page, encoding="utf-8")
        print(f"wrote {dest} ({dest.stat().st_size} bytes)")
    for name in STATIC_COPIES:
        src = ROOT / name
        if not src.exists():
            continue
        dest = SITE / name
        if src.is_dir():
            shutil.copytree(src, dest)
        else:
            shutil.copy2(src, dest)
        print(f"copied {src} -> {dest}")


if __name__ == "__main__":
    main()
