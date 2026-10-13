#!/usr/bin/env python3
"""Build a static multi-page HTML docs site from the Markdown sources.

Stdlib only. Usage: python scripts/build-site.py  (writes into site/)
Pages: index.html (README) + api-reference.html + formats.html + docs/*.html,
plus verbatim copies of linked assets (openapi.yaml, examples/, ...) so every
relative link resolves on GitHub Pages.
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
:root{--fg:#1a1a1a;--bg:#fff;--muted:#666;--code:#f4f4f4;--accent:#0a58ca;--border:#e2e2e2}
*{box-sizing:border-box}body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;margin:0;color:var(--fg);background:var(--bg);line-height:1.55}
.layout{display:flex;min-height:100vh}nav{width:300px;flex-shrink:0;border-right:1px solid var(--border);padding:1rem;position:sticky;top:0;height:100vh;overflow:auto}
nav input{width:100%;padding:.4rem;margin-bottom:.6rem}nav a{display:block;color:var(--fg);text-decoration:none;padding:.15rem 0;font-size:.9rem}
nav a.h3{padding-left:1rem;color:var(--muted)}nav a:hover{color:var(--accent)}
nav .group{font-size:.75rem;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);margin:.8rem 0 .2rem}
nav a.current{font-weight:700;color:var(--accent)}
main{max-width:900px;padding:2rem 2.5rem}pre{background:var(--code);padding:.8rem;overflow:auto;border-radius:6px}
code{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.88em}pre code{background:none}
table{border-collapse:collapse;width:100%;margin:1rem 0}th,td{border:1px solid var(--border);padding:.4rem .6rem;text-align:left;font-size:.9rem}
blockquote{border-left:3px solid var(--accent);margin:1rem 0;padding:.2rem 1rem;color:var(--muted)}
h1,h2,h3{scroll-margin-top:1rem}h2{border-bottom:1px solid var(--border);padding-bottom:.3rem}
@media(max-width:800px){nav{display:none}main{padding:1rem}}
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
            out.append(f'<pre><code class="language-{html.escape(lang)}">{html.escape(chr(10).join(buf))}</code></pre>')
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
            out.append(f"<table><thead><tr>{thead}</tr></thead><tbody>{tbody}</tbody></table>")
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

    nav = ['<input id="q" placeholder="Filter sections…" oninput="filterNav()">']
    nav.append('<div class="group">Pages</div>')
    for _, rel, page_label in PAGES:
        cls = ' class="current"' if rel == out_rel else ""
        nav.append(f'<a href="{href_for(rel)}"{cls}>{html.escape(page_label)}</a>')
    nav.append('<div class="group">On this page</div>')
    for level, ident, text in toc:
        nav.append(f'<a class="h{level}" href="#{ident}">{html.escape(text)}</a>')
    js = ("<script>function filterNav(){const q=document.getElementById('q').value.toLowerCase();"
          "document.querySelectorAll('nav a').forEach(a=>{a.style.display=a.textContent.toLowerCase().includes(q)?'':'none';});}</script>")
    return ("<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
            "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
            f"<title>{html.escape(title)} — Instagram API Docs</title>"
            f"<style>{CSS}</style></head><body><div class=\"layout\"><nav>{''.join(nav)}</nav>"
            f"<main>{body}</main></div>{js}</body></html>")


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
