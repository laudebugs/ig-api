#!/usr/bin/env python3
"""Build a static multi-page HTML docs site from Markdown sources.

Stdlib only. Usage: python scripts/build-site.py (writes into site/)
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

GUIDE_ORDER = [
    "getting-started",
    "authentication",
    "media-publishing",
    "insights",
    "comments-moderation",
    "messaging",
    "webhooks",
    "errors-and-rate-limits",
    "faq",
]

TITLE_MAP = {
    "getting-started": "Getting Started",
    "authentication": "Authentication",
    "media-publishing": "Media Publishing",
    "insights": "Insights",
    "comments-moderation": "Comments & Moderation",
    "messaging": "Messaging",
    "webhooks": "Webhooks",
    "errors-and-rate-limits": "Errors & Rate Limits",
    "faq": "FAQ",
}

# (source markdown, output html relative to site/, nav label, group)
PAGES = [
    (ROOT / "README.md", "index.html", "Home", "Overview"),
    (ROOT / "INSTAGRAM_GRAPH_API.md", "api-reference.html", "API Reference", "Overview"),
    (ROOT / "FORMATS.md", "formats.html", "Formats", "Overview"),
]

# Order docs according to GUIDE_ORDER, appending any other discovered files
docs_dir = ROOT / "docs"
discovered = {p.stem: p for p in docs_dir.glob("*.md")}
ordered_stems = [s for s in GUIDE_ORDER if s in discovered]
for s in sorted(discovered.keys()):
    if s not in ordered_stems:
        ordered_stems.append(s)

for stem in ordered_stems:
    src = discovered[stem]
    label = TITLE_MAP.get(stem, stem.replace("-", " ").title())
    PAGES.append((src, f"docs/{stem}.html", label, "Guides"))

# Stem renames when mapping *.md links to built pages
STEM_MAP = {
    "README": "index",
    "INSTAGRAM_GRAPH_API": "api-reference",
    "FORMATS": "formats",
}

# Repo files/dirs copied verbatim into site/ so relative links work
STATIC_COPIES = [
    "openapi.yaml",
    "llms.txt",
    "llms-full.txt",
    "types",
    "examples",
    "data",
    "postman",
    "bruno",
    "mcp",
    "scripts",
    ".github",
]

RESOURCES = [
    ("openapi.yaml", "OpenAPI Spec (3.1)", "contract"),
    ("types/instagram-graph.d.ts", "TypeScript Types", "types"),
    ("llms.txt", "llms.txt (Fast Index)", "llm"),
    ("llms-full.txt", "llms-full.txt (Full Bundle)", "llm"),
    ("data/chunks.jsonl", "RAG Chunks (JSONL)", "data"),
    ("examples/", "Code Examples", "code"),
    ("bruno/", "Bruno Collection", "api"),
    ("postman/", "Postman Collection", "api"),
]

CSS = """
:root {
  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
  --font-mono: 'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', monospace;

  /* Cream Light Theme */
  --bg: #faf7f2;
  --bg-surface: #f3eee6;
  --bg-subtle: #eae3d7;
  --bg-code: #f4efe6;
  --bg-code-header: #ebe4d6;
  --fg: #1f1b18;
  --fg-muted: #5e5750;
  --fg-subtle: #8c8378;
  --border: #e3dad0;
  --border-subtle: #ede6dc;

  /* Instagram Colors (Light) */
  --accent: #d62976;
  --accent-subtle: rgba(214, 41, 118, 0.09);
  --accent-fg: #be185d;
  --accent-coral: #e1306c;
  --accent-purple: #833ab4;
  --accent-orange: #ea580c;
  --accent-yellow: #f59e0b;
  --ig-grad: linear-gradient(45deg, #f09433 0%, #e6683c 25%, #dc2743 50%, #cc2366 75%, #bc1888 100%);

  --header-bg: rgba(250, 247, 242, 0.92);
  --header-border: #e3dad0;
  --kbd-bg: #eae3d7;
  --kbd-border: #d6ccbe;
  --radius-sm: 4px;
  --radius-md: 6px;
  --radius-lg: 8px;

  /* TanStack Highlight tokens (Instagram Light on Cream) */
  --th-background: #f4efe6;
  --th-token: #1f1b18;
  --th-attr: #833ab4;
  --th-code-inline: #1f1b18;
  --th-command: #833ab4;
  --th-comment: #8c8378;
  --th-deleted: #b91c1c;
  --th-function: #833ab4;
  --th-heading: #1f1b18;
  --th-inserted: #15803d;
  --th-keyword: #c13584;
  --th-link: #d62976;
  --th-literal: #d62976;
  --th-meta: #8c8378;
  --th-number: #e1306c;
  --th-operator: #8c8378;
  --th-property: #c13584;
  --th-selector: #15803d;
  --th-string: #047857;
  --th-tag: #c13584;
  --th-type: #833ab4;
  --th-variable: #ea580c;
}

[data-theme="dark"] {
  /* True Black Dark Theme */
  --bg: #000000;
  --bg-surface: #111111;
  --bg-subtle: #1c1c1c;
  --bg-code: #0a0a0a;
  --bg-code-header: #141414;
  --fg: #fbf8f4;
  --fg-muted: #a8a29e;
  --fg-subtle: #736d66;
  --border: #262320;
  --border-subtle: #1a1816;

  /* Instagram Colors (Dark on Black) */
  --accent: #f75590;
  --accent-subtle: rgba(247, 85, 144, 0.15);
  --accent-fg: #fb7185;
  --accent-coral: #fb7185;
  --accent-purple: #c084fc;
  --accent-orange: #fb923c;
  --accent-yellow: #fde047;
  --ig-grad: linear-gradient(45deg, #f09433 0%, #e6683c 25%, #dc2743 50%, #cc2366 75%, #bc1888 100%);

  --header-bg: rgba(0, 0, 0, 0.9);
  --header-border: #262320;
  --kbd-bg: #1c1a17;
  --kbd-border: #332f2b;

  /* TanStack Highlight tokens (Instagram Dark on Black) */
  --th-background: #0a0a0a;
  --th-token: #fbf8f4;
  --th-attr: #c084fc;
  --th-code-inline: #fbf8f4;
  --th-command: #c084fc;
  --th-comment: #736d66;
  --th-deleted: #f87171;
  --th-function: #c084fc;
  --th-heading: #fbf8f4;
  --th-inserted: #4ade80;
  --th-keyword: #f472b6;
  --th-link: #f75590;
  --th-literal: #f75590;
  --th-meta: #a8a29e;
  --th-number: #fb7185;
  --th-operator: #a8a29e;
  --th-property: #f472b6;
  --th-selector: #4ade80;
  --th-string: #34d399;
  --th-tag: #f472b6;
  --th-type: #c084fc;
  --th-variable: #fb923c;
}

@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --bg: #000000;
    --bg-surface: #111111;
    --bg-subtle: #1c1c1c;
    --bg-code: #0a0a0a;
    --bg-code-header: #141414;
    --fg: #fbf8f4;
    --fg-muted: #a8a29e;
    --fg-subtle: #736d66;
    --border: #262320;
    --border-subtle: #1a1816;

    --accent: #f75590;
    --accent-subtle: rgba(247, 85, 144, 0.15);
    --accent-fg: #fb7185;
    --accent-coral: #fb7185;
    --accent-purple: #c084fc;
    --accent-orange: #fb923c;
    --accent-yellow: #fde047;
    --ig-grad: linear-gradient(45deg, #f09433 0%, #e6683c 25%, #dc2743 50%, #cc2366 75%, #bc1888 100%);

    --header-bg: rgba(0, 0, 0, 0.9);
    --header-border: #262320;
    --kbd-bg: #1c1a17;
    --kbd-border: #332f2b;

    --th-background: #0a0a0a;
    --th-token: #fbf8f4;
    --th-attr: #c084fc;
    --th-code-inline: #fbf8f4;
    --th-command: #c084fc;
    --th-comment: #736d66;
    --th-deleted: #f87171;
    --th-function: #c084fc;
    --th-heading: #fbf8f4;
    --th-inserted: #4ade80;
    --th-keyword: #f472b6;
    --th-link: #f75590;
    --th-literal: #f75590;
    --th-meta: #a8a29e;
    --th-number: #fb7185;
    --th-operator: #a8a29e;
    --th-property: #f472b6;
    --th-selector: #4ade80;
    --th-string: #34d399;
    --th-tag: #f472b6;
    --th-type: #c084fc;
    --th-variable: #fb923c;
  }
}

* { box-sizing: border-box; }
html { scroll-behavior: smooth; font-size: 16px; }
body {
  margin: 0;
  font-family: var(--font-sans);
  color: var(--fg);
  background: var(--bg);
  line-height: 1.65;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* Header */
header.site-header {
  position: sticky;
  top: 0;
  z-index: 50;
  height: 56px;
  background: var(--header-bg);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--header-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 1.25rem;
}
.header-left, .header-right {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}
.brand {
  display: inline-flex;
  align-items: center;
  gap: 0.55rem;
  color: var(--fg);
  text-decoration: none;
  font-weight: 600;
  font-size: 0.95rem;
  letter-spacing: -0.01em;
}
.brand-badge {
  font-size: 0.68rem;
  font-weight: 700;
  padding: 0.15rem 0.45rem;
  background: linear-gradient(135deg, rgba(225, 48, 108, 0.12), rgba(240, 148, 51, 0.12));
  color: var(--accent);
  border-radius: var(--radius-sm);
  border: 1px solid rgba(225, 48, 108, 0.25);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.header-nav {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.header-nav a {
  color: var(--fg-muted);
  text-decoration: none;
  font-size: 0.85rem;
  padding: 0.35rem 0.6rem;
  border-radius: var(--radius-sm);
  transition: color 0.15s, background-color 0.15s;
}
.header-nav a:hover {
  color: var(--fg);
  background: var(--bg-subtle);
}
.mobile-toggle {
  display: none;
  background: none;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 0.4rem;
  color: var(--fg);
  cursor: pointer;
  line-height: 0;
}
.theme-btn {
  background: none;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 0.4rem;
  color: var(--fg-muted);
  cursor: pointer;
  line-height: 0;
  transition: color 0.15s, border-color 0.15s, background-color 0.15s;
}
.theme-btn:hover {
  color: var(--fg);
  border-color: var(--fg-muted);
  background: var(--bg-subtle);
}

/* Layout */
.layout {
  display: flex;
  min-height: calc(100vh - 56px);
}
.backdrop {
  display: none;
}

/* Sidebar */
aside.sidebar {
  width: 280px;
  flex-shrink: 0;
  position: sticky;
  top: 56px;
  height: calc(100vh - 56px);
  overflow-y: auto;
  border-right: 1px solid var(--border);
  padding: 1rem 0.85rem 2rem;
  background: var(--bg);
  scrollbar-width: thin;
}
aside.sidebar::-webkit-scrollbar {
  width: 5px;
}
aside.sidebar::-webkit-scrollbar-thumb {
  background: var(--border);
  border-radius: 4px;
}

.drawer-header {
  display: none;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 0.85rem;
  margin-bottom: 0.85rem;
  border-bottom: 1px solid var(--border);
}
.drawer-title {
  font-weight: 600;
  font-size: 0.95rem;
  color: var(--fg);
}
.drawer-close {
  background: none;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 0.35rem;
  color: var(--fg-muted);
  cursor: pointer;
  line-height: 0;
}
.drawer-close:hover {
  color: var(--fg);
  background: var(--bg-subtle);
}

.search-box {
  position: relative;
  margin-bottom: 1rem;
}
.search-icon {
  position: absolute;
  left: 0.65rem;
  top: 50%;
  transform: translateY(-50%);
  color: var(--fg-subtle);
  pointer-events: none;
}
.search-box input {
  width: 100%;
  padding: 0.45rem 1.8rem 0.45rem 2rem;
  font-family: var(--font-sans);
  font-size: 0.85rem;
  color: var(--fg);
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  outline: none;
  transition: border-color 0.15s, box-shadow 0.15s;
}
.search-box input:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 2px var(--accent-subtle);
}
.search-kbd {
  position: absolute;
  right: 0.5rem;
  top: 50%;
  transform: translateY(-50%);
  font-family: var(--font-mono);
  font-size: 0.7rem;
  color: var(--fg-subtle);
  background: var(--kbd-bg);
  border: 1px solid var(--kbd-border);
  padding: 0.1rem 0.3rem;
  border-radius: 3px;
  pointer-events: none;
}

.sidebar .group-title {
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--fg-subtle);
  margin: 1.1rem 0 0.4rem 0.5rem;
}
.sidebar .nav-list {
  list-style: none;
  padding: 0;
  margin: 0;
}
.sidebar .nav-list a {
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: var(--fg-muted);
  text-decoration: none;
  padding: 0.35rem 0.55rem;
  font-size: 0.88rem;
  border-radius: var(--radius-sm);
  transition: color 0.12s, background-color 0.12s;
  margin-bottom: 1px;
}
.sidebar .nav-list a:hover {
  color: var(--fg);
  background: var(--bg-subtle);
}
.sidebar .nav-list a.current {
  font-weight: 600;
  color: var(--accent);
  background: var(--accent-subtle);
}
.sidebar .nav-list a.h3 {
  padding-left: 1.25rem;
  font-size: 0.82rem;
  color: var(--fg-subtle);
}
.sidebar .nav-list a.h3:hover {
  color: var(--fg-muted);
}
.badge-tag {
  font-family: var(--font-mono);
  font-size: 0.65rem;
  padding: 0.1rem 0.35rem;
  background: var(--bg-subtle);
  color: var(--fg-subtle);
  border-radius: 3px;
  border: 1px solid var(--border);
}

/* Main Content */
main.content {
  flex: 1 1 0;
  max-width: 860px;
  margin: 0 auto;
  padding: 2.25rem 3rem 4rem;
  min-width: 0;
}
.breadcrumbs {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.8rem;
  color: var(--fg-subtle);
  margin-bottom: 1rem;
}
.breadcrumbs a {
  color: var(--fg-subtle);
  text-decoration: none;
}
.breadcrumbs a:hover {
  color: var(--accent);
}
.breadcrumbs span.sep {
  color: var(--border);
}

/* Typography */
h1 {
  font-size: 2rem;
  font-weight: 700;
  letter-spacing: -0.025em;
  line-height: 1.25;
  margin: 0 0 1rem;
  color: var(--fg);
}
h2 {
  font-size: 1.4rem;
  font-weight: 600;
  letter-spacing: -0.02em;
  line-height: 1.35;
  margin: 2.5rem 0 0.75rem;
  padding-bottom: 0.4rem;
  border-bottom: 1px solid var(--border-subtle);
  color: var(--fg);
  scroll-margin-top: 5rem;
}
h3 {
  font-size: 1.15rem;
  font-weight: 600;
  letter-spacing: -0.015em;
  margin: 1.75rem 0 0.5rem;
  color: var(--fg);
  scroll-margin-top: 5rem;
}
h4 {
  font-size: 1rem;
  font-weight: 600;
  margin: 1.25rem 0 0.35rem;
  color: var(--fg);
  scroll-margin-top: 5rem;
}
p {
  margin: 0 0 1rem;
  color: var(--fg);
  line-height: 1.68;
}
a {
  color: var(--accent);
  text-decoration-thickness: 1px;
  text-underline-offset: 2px;
}
a:hover {
  color: var(--accent-fg);
  text-decoration: underline;
}

.header-anchor {
  float: left;
  margin-left: -0.9em;
  padding-right: 0.25em;
  color: var(--fg-subtle);
  text-decoration: none;
  opacity: 0;
  transition: opacity 0.15s, color 0.15s;
  font-weight: 400;
  user-select: none;
}
h1:hover .header-anchor,
h2:hover .header-anchor,
h3:hover .header-anchor,
h4:hover .header-anchor {
  opacity: 0.6;
}
.header-anchor:hover {
  opacity: 1 !important;
  color: var(--accent) !important;
  text-decoration: none !important;
}

ul, ol {
  padding-left: 1.5rem;
  margin: 0 0 1.25rem;
}
li {
  margin-bottom: 0.35rem;
}
li::marker {
  color: var(--fg-subtle);
}

hr {
  border: none;
  border-top: 1px solid var(--border);
  margin: 2rem 0;
}

blockquote {
  border-left: 3px solid var(--accent);
  background: var(--bg-surface);
  margin: 1.25rem 0;
  padding: 0.85rem 1.15rem;
  color: var(--fg-muted);
  border-radius: 0 var(--radius-md) var(--radius-md) 0;
  font-size: 0.92rem;
}
blockquote p:last-child {
  margin-bottom: 0;
}

code {
  font-family: var(--font-mono);
  font-size: 0.86em;
}
:not(pre) > code {
  background: var(--bg-subtle);
  color: var(--fg);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 0.15em 0.38em;
  word-break: break-word;
}

/* Code Blocks */
.code-block {
  margin: 1.25rem 0;
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  background: var(--bg-code);
  overflow: hidden;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}
.code-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.4rem 0.85rem;
  background: var(--bg-code-header);
  border-bottom: 1px solid var(--border);
}
.code-lang {
  font-family: var(--font-mono);
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--fg-muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}
.copy-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  background: transparent;
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  padding: 0.2rem 0.5rem;
  font-family: var(--font-sans);
  font-size: 0.75rem;
  color: var(--fg-muted);
  cursor: pointer;
  transition: all 0.15s ease;
}
.copy-btn:hover {
  background: var(--bg-surface);
  color: var(--fg);
  border-color: var(--border);
}
.copy-btn.copied {
  color: #16a34a;
}
pre {
  margin: 0;
  padding: 1rem 1.15rem;
  overflow-x: auto;
  font-family: var(--font-mono);
  font-size: 0.85rem;
  line-height: 1.6;
  background: var(--bg-code);
  color: var(--fg);
  -webkit-overflow-scrolling: touch;
}
pre code {
  background: none !important;
  border: none !important;
  padding: 0 !important;
  font-size: inherit;
  color: inherit;
}

/* TanStack Highlight tokens */
pre.th-code {
  background: var(--th-background);
  color: var(--th-token);
}
.th-token { color: var(--th-token); }
.th-attr { color: var(--th-attr); }
.th-code-inline { color: var(--th-code-inline); }
.th-command { color: var(--th-command); font-weight: 500; }
.th-comment { color: var(--th-comment); font-style: italic; }
.th-deleted { color: var(--th-deleted); }
.th-function { color: var(--th-function); }
.th-heading { color: var(--th-heading); }
.th-inserted { color: var(--th-inserted); }
.th-keyword { color: var(--th-keyword); font-weight: 500; }
.th-link { color: var(--th-link); }
.th-literal { color: var(--th-literal); }
.th-meta { color: var(--th-meta); }
.th-number { color: var(--th-number); }
.th-operator { color: var(--th-operator); }
.th-property { color: var(--th-property); }
.th-selector { color: var(--th-selector); }
.th-string { color: var(--th-string); }
.th-tag { color: var(--th-tag); }
.th-type { color: var(--th-type); }
.th-variable { color: var(--th-variable); }

/* Tables */
.table-wrap {
  width: 100%;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  margin: 1.25rem 0;
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  background: var(--bg);
}
table {
  border-collapse: collapse;
  width: 100%;
  margin: 0;
  font-size: 0.88rem;
  text-align: left;
}
th {
  background: var(--bg-surface);
  color: var(--fg);
  font-weight: 600;
  padding: 0.6rem 0.85rem;
  border-bottom: 1px solid var(--border);
  border-right: 1px solid var(--border);
  word-break: normal;
  overflow-wrap: break-word;
}
th:last-child {
  border-right: none;
}
td {
  padding: 0.55rem 0.85rem;
  border-bottom: 1px solid var(--border);
  border-right: 1px solid var(--border);
  color: var(--fg);
  word-break: normal;
  overflow-wrap: break-word;
}
td:last-child {
  border-right: none;
}
tr:last-child td {
  border-bottom: none;
}
tbody tr:hover {
  background: var(--bg-surface);
}

/* Pagination */
.pagination-nav {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  margin-top: 3.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid var(--border);
}
.page-link {
  display: flex;
  flex-direction: column;
  padding: 0.9rem 1.15rem;
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  text-decoration: none;
  transition: border-color 0.15s, background-color 0.15s;
}
.page-link:hover {
  border-color: var(--accent);
  background: var(--bg-surface);
  text-decoration: none;
}
.page-link.next {
  text-align: right;
  grid-column: 2;
}
.page-link.prev {
  grid-column: 1;
}
.page-direction {
  font-size: 0.75rem;
  color: var(--fg-subtle);
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.25rem;
}
.page-title {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--fg);
}

/* Right TOC Rail (Desktop) */
aside.toc-sidebar {
  width: 230px;
  flex-shrink: 0;
  position: sticky;
  top: 56px;
  height: calc(100vh - 56px);
  overflow-y: auto;
  padding: 2.25rem 1rem 2rem 0.5rem;
  font-size: 0.82rem;
}
.toc-header {
  font-weight: 700;
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--fg-subtle);
  margin-bottom: 0.6rem;
}
.toc-list {
  list-style: none;
  padding: 0;
  margin: 0;
  border-left: 1px solid var(--border);
}
.toc-list a {
  display: block;
  color: var(--fg-muted);
  text-decoration: none;
  padding: 0.25rem 0 0.25rem 0.85rem;
  line-height: 1.45;
  margin-left: -1px;
  border-left: 1px solid transparent;
  transition: color 0.15s, border-color 0.15s;
}
.toc-list a:hover {
  color: var(--fg);
  border-left-color: var(--fg-subtle);
}
.toc-list a.active {
  color: var(--accent);
  border-left-color: var(--accent);
  font-weight: 500;
}
.toc-list a.h3 {
  padding-left: 1.5rem;
  font-size: 0.78rem;
}

/* Footer */
footer.doc-footer {
  margin-top: 3rem;
  padding-top: 1.5rem;
  border-top: 1px solid var(--border-subtle);
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 0.8rem;
  color: var(--fg-subtle);
  flex-wrap: wrap;
  gap: 0.5rem;
}

/* Responsive & Mobile */
@media (max-width: 1240px) {
  aside.toc-sidebar {
    display: none;
  }
}

@media (max-width: 860px) {
  .mobile-toggle {
    display: inline-flex;
  }
  .header-nav {
    display: none;
  }
  .drawer-header {
    display: flex;
  }
  aside.sidebar {
    position: fixed;
    top: 0;
    left: 0;
    bottom: 0;
    width: 300px;
    max-width: 85vw;
    height: 100vh;
    z-index: 100;
    transform: translateX(-100%);
    transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1);
    box-shadow: none;
    border-right: 1px solid var(--border);
    padding-top: 1rem;
  }
  body.nav-open aside.sidebar {
    transform: translateX(0);
    box-shadow: 0 0 35px rgba(0, 0, 0, 0.45);
  }
  .backdrop {
    display: block;
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.5);
    z-index: 90;
    opacity: 0;
    pointer-events: none;
    transition: opacity 0.2s ease;
    backdrop-filter: blur(2px);
    -webkit-backdrop-filter: blur(2px);
  }
  body.nav-open .backdrop {
    opacity: 1;
    pointer-events: auto;
  }
  body.nav-open {
    overflow: hidden;
  }
  main.content {
    padding: 1.5rem 1.25rem 3rem;
  }
  h1 {
    font-size: 1.65rem;
  }
  h2 {
    font-size: 1.25rem;
    margin-top: 2rem;
  }
  .pagination-nav {
    grid-template-columns: 1fr;
  }
  .page-link.next {
    grid-column: 1;
  }
}
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
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", text)

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
            display_lang = lang if lang else "code"
            raw_code = "\n".join(buf)
            escaped_code = html.escape(raw_code)
            out.append(
                f'<div class="code-block" data-lang="{html.escape(lang)}">'
                f'<div class="code-header">'
                f'<span class="code-lang">{html.escape(display_lang)}</span>'
                f'<button class="copy-btn" type="button" aria-label="Copy code to clipboard" onclick="copyCode(this)">'
                f'<svg class="copy-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
                f'<rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>'
                f'<path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>'
                f'</svg><span>Copy</span></button>'
                f'</div>'
                f'<pre tabindex="0"><code class="language-{html.escape(lang)}">{escaped_code}</code></pre>'
                f'</div>'
            )
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
            anchor = f'<a class="header-anchor" href="#{ident}" aria-label="Permalink to this section">#</a>'
            out.append(f'<h{level} id="{ident}">{anchor}{inline(text)}</h{level}>')
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
            out.append(f"<blockquote><p>{inline(' '.join(buf))}</p></blockquote>")
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


def render_page(label, group, title, body, toc, out_rel):
    depth = out_rel.count("/")

    def href_for(target_rel):
        if depth == 0:
            return target_rel
        if target_rel.startswith("docs/"):
            return target_rel.split("/", 1)[1]
        return "../" + target_rel

    # Sidebar Navigation Building
    nav = []
    nav.append('<div class="drawer-header">')
    nav.append('<div class="drawer-title">Navigation</div>')
    nav.append('<button class="drawer-close" aria-label="Close navigation" onclick="toggleNav(false)" type="button">')
    nav.append('<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>')
    nav.append('</button>')
    nav.append('</div>')

    nav.append('<div class="search-box">')
    nav.append('<svg class="search-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>')
    nav.append('<input id="q" type="search" placeholder="Filter sections…" oninput="filterNav()" aria-label="Filter navigation">')
    nav.append('<span class="search-kbd">/</span>')
    nav.append('</div>')

    # Group Pages
    grouped = {}
    for _, rel, page_label, p_group in PAGES:
        grouped.setdefault(p_group, []).append((rel, page_label))

    for grp_name in ("Overview", "Guides"):
        if grp_name in grouped:
            nav.append(f'<div class="group-title">{html.escape(grp_name)}</div>')
            nav.append('<ul class="nav-list">')
            for rel, page_label in grouped[grp_name]:
                cls = ' class="current"' if rel == out_rel else ""
                nav.append(f'<li><a href="{href_for(rel)}"{cls}>{html.escape(page_label)}</a></li>')
            nav.append('</ul>')

    # Machine-readable assets group
    nav.append('<div class="group-title">Resources</div>')
    nav.append('<ul class="nav-list">')
    for res_rel, res_label, tag in RESOURCES:
        nav.append(f'<li><a href="{href_for(res_rel)}" target="_blank" rel="noopener">{html.escape(res_label)}<span class="badge-tag">{tag}</span></a></li>')
    nav.append('</ul>')

    # In-page TOC for sidebar
    if toc:
        nav.append('<div class="group-title on-this-page-sidebar">On This Page</div>')
        nav.append('<ul class="nav-list on-this-page-list">')
        for level, ident, text in toc:
            cls = f'h{level}'
            nav.append(f'<li><a class="{cls}" href="#{ident}">{html.escape(text)}</a></li>')
        nav.append('</ul>')

    # Right TOC Rail (Desktop)
    toc_rail = []
    if toc:
        toc_rail.append('<aside class="toc-sidebar" aria-label="Table of contents">')
        toc_rail.append('<div class="toc-header">On this page</div>')
        toc_rail.append('<ul class="toc-list">')
        for level, ident, text in toc:
            cls = f'h{level}'
            toc_rail.append(f'<li><a class="{cls}" href="#{ident}">{html.escape(text)}</a></li>')
        toc_rail.append('</ul>')
        toc_rail.append('</aside>')

    # Pagination calculation
    page_idx = -1
    for i, (_, rel, _, _) in enumerate(PAGES):
        if rel == out_rel:
            page_idx = i
            break

    pagination = []
    if page_idx > 0:
        _, prev_rel, prev_label, _ = PAGES[page_idx - 1]
        pagination.append(
            f'<a class="page-link prev" href="{href_for(prev_rel)}">'
            f'<span class="page-direction">← Previous</span>'
            f'<span class="page-title">{html.escape(prev_label)}</span>'
            f'</a>'
        )
    if 0 <= page_idx < len(PAGES) - 1:
        _, next_rel, next_label, _ = PAGES[page_idx + 1]
        pagination.append(
            f'<a class="page-link next" href="{href_for(next_rel)}">'
            f'<span class="page-direction">Next →</span>'
            f'<span class="page-title">{html.escape(next_label)}</span>'
            f'</a>'
        )

    pagination_html = f'<nav class="pagination-nav" aria-label="Documentation navigation">{"".join(pagination)}</nav>' if pagination else ""

    breadcrumb_html = (
        f'<div class="breadcrumbs">'
        f'<a href="{href_for("index.html")}">Docs</a>'
        f'<span class="sep">/</span>'
        f'<span>{html.escape(group)}</span>'
        f'<span class="sep">/</span>'
        f'<span>{html.escape(label)}</span>'
        f'</div>'
    )

    footer_html = (
        f'<footer class="doc-footer">'
        f'<span>Instagram Graph API Documentation · Target Meta v25.0 / v26.0</span>'
        f'<span>Deployed to GitHub Pages</span>'
        f'</footer>'
    )

    script = """<script>
// Mobile navigation toggle
function toggleNav(force) {
  const body = document.body;
  const isOpen = typeof force === 'boolean' ? force : !body.classList.contains('nav-open');
  body.classList.toggle('nav-open', isOpen);
  const btn = document.querySelector('.mobile-toggle');
  if (btn) btn.setAttribute('aria-expanded', String(isOpen));
}

// Close mobile navigation when clicking links
document.querySelectorAll('aside.sidebar a').forEach(a => {
  a.addEventListener('click', () => {
    if (document.body.classList.contains('nav-open')) toggleNav(false);
  });
});

// Escape key closes mobile nav
window.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' && document.body.classList.contains('nav-open')) {
    toggleNav(false);
  }
  if (e.key === '/' && document.activeElement.tagName !== 'INPUT' && document.activeElement.tagName !== 'TEXTAREA') {
    e.preventDefault();
    const q = document.getElementById('q');
    if (q) { q.focus(); q.select(); }
  }
});

// Sidebar search / filter
function filterNav() {
  const q = (document.getElementById('q').value || '').toLowerCase().trim();
  document.querySelectorAll('aside.sidebar .nav-list li').forEach(li => {
    const text = li.textContent.toLowerCase();
    li.style.display = !q || text.includes(q) ? '' : 'none';
  });
  // Hide empty group headers when searching
  document.querySelectorAll('aside.sidebar .group-title').forEach(title => {
    let next = title.nextElementSibling;
    let anyVisible = false;
    if (next && next.classList.contains('nav-list')) {
      next.querySelectorAll('li').forEach(li => {
        if (li.style.display !== 'none') anyVisible = true;
      });
      title.style.display = anyVisible ? '' : 'none';
      next.style.display = anyVisible ? '' : 'none';
    }
  });
}

// Dark / Light Mode Toggle
function initTheme() {
  const saved = localStorage.getItem('theme');
  if (saved === 'dark' || saved === 'light') {
    document.documentElement.setAttribute('data-theme', saved);
  }
}
function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme') || 
    (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
  const next = current === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('theme', next);
}
initTheme();

// Copy Code Button
function copyCode(btn) {
  const block = btn.closest('.code-block');
  const code = block ? block.querySelector('pre code') : null;
  if (!code) return;
  const text = code.innerText || code.textContent;
  navigator.clipboard.writeText(text).then(() => {
    const original = btn.innerHTML;
    btn.classList.add('copied');
    btn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6L9 17l-5-5"/></svg><span>Copied!</span>`;
    setTimeout(() => {
      btn.innerHTML = original;
      btn.classList.remove('copied');
    }, 2000);
  }).catch(() => {});
}

// Active TOC Scrollspy
if ('IntersectionObserver' in window) {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const id = entry.target.getAttribute('id');
        document.querySelectorAll('aside.toc-sidebar a').forEach(a => {
          a.classList.toggle('active', a.getAttribute('href') === '#' + id);
        });
      }
    });
  }, { rootMargin: '0px 0px -70% 0px' });
  document.querySelectorAll('h2[id], h3[id]').forEach(h => observer.observe(h));
}
</script>"""

    # TanStack Highlight script using jsDelivr ESM CDN
    highlight_cdn_script = """<script type="module">
import { highlightToHtml } from 'https://cdn.jsdelivr.net/npm/@tanstack/highlight@1.1.0/+esm';

const LANG_MAP = {
  bash: 'shell', sh: 'shell', zsh: 'shell', curl: 'shell', console: 'shell',
  py: 'python', python: 'python',
  ts: 'ts', typescript: 'ts',
  js: 'js', javascript: 'js',
  json: 'json', jsonc: 'json',
  yaml: 'yaml', yml: 'yaml',
  http: 'http', https: 'http',
  html: 'html', xml: 'html',
  sql: 'sql',
  md: 'markdown', markdown: 'markdown',
  text: 'plaintext', txt: 'plaintext'
};

function highlightAll() {
  document.querySelectorAll('.code-block pre').forEach((pre) => {
    if (pre.dataset.highlighted) return;
    const code = pre.querySelector('code');
    if (!code) return;
    const block = pre.closest('.code-block');
    let rawLang = (block ? block.dataset.lang : '') || '';
    if (!rawLang) {
      const cls = code.className || '';
      const m = cls.match(/language-([a-zA-Z0-9_-]+)/);
      if (m) rawLang = m[1];
    }
    rawLang = rawLang.toLowerCase().trim();
    const text = code.textContent || '';
    let targetLang = LANG_MAP[rawLang] || rawLang;
    if (!targetLang || targetLang === 'code') {
      if (/^(GET|POST|DELETE|PUT|PATCH|HTTP\/)\\s/m.test(text)) {
        targetLang = 'http';
      } else {
        targetLang = 'plaintext';
      }
    }
    try {
      const resHtml = highlightToHtml(text, { lang: targetLang });
      if (resHtml) {
        const temp = document.createElement('template');
        temp.innerHTML = resHtml;
        const newPre = temp.content.querySelector('pre');
        if (newPre) {
          newPre.tabIndex = 0;
          newPre.dataset.highlighted = 'true';
          pre.replaceWith(newPre);
        }
      }
    } catch (e) {
      console.warn('TanStack Highlight error:', targetLang, e);
    }
  });
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', highlightAll);
} else {
  highlightAll();
}
</script>"""

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <title>{html.escape(title)} — Instagram API Docs</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <style>{CSS}</style>
</head>
<body>
  <header class="site-header">
    <div class="header-left">
      <button class="mobile-toggle" aria-label="Toggle navigation menu" onclick="toggleNav()" type="button">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="3" y1="12" x2="21" y2="12"></line><line x1="3" y1="6" x2="21" y2="6"></line><line x1="3" y1="18" x2="21" y2="18"></line></svg>
      </button>
      <a class="brand" href="{href_for('index.html')}">
        <svg class="brand-glyph" width="22" height="22" viewBox="0 0 24 24" fill="none">
          <defs>
            <linearGradient id="ig-grad-{out_rel.replace('/', '-').replace('.', '-')}" x1="0%" y1="100%" x2="100%" y2="0%">
              <stop offset="0%" stop-color="#f09433"/>
              <stop offset="25%" stop-color="#e6683c"/>
              <stop offset="50%" stop-color="#dc2743"/>
              <stop offset="75%" stop-color="#cc2366"/>
              <stop offset="100%" stop-color="#bc1888"/>
            </linearGradient>
          </defs>
          <rect x="2" y="2" width="20" height="20" rx="5.5" ry="5.5" stroke="url(#ig-grad-{out_rel.replace('/', '-').replace('.', '-')})" stroke-width="2"/>
          <path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z" stroke="url(#ig-grad-{out_rel.replace('/', '-').replace('.', '-')})" stroke-width="2"/>
          <circle cx="17.5" cy="6.5" r="1.2" fill="url(#ig-grad-{out_rel.replace('/', '-').replace('.', '-')})"/>
        </svg>
        <span>Instagram API</span>
        <span class="brand-badge">Docs</span>
      </a>
    </div>
    <div class="header-right">
      <nav class="header-nav">
        <a href="{href_for('api-reference.html')}">API Reference</a>
        <a href="{href_for('formats.html')}">Formats</a>
        <a href="{href_for('openapi.yaml')}" target="_blank">OpenAPI</a>
        <a href="{href_for('llms.txt')}" target="_blank">llms.txt</a>
        <a href="https://github.com/laudebugs/ig-api" target="_blank" rel="noopener" aria-label="GitHub repository">GitHub</a>
      </nav>
      <button class="theme-btn" onclick="toggleTheme()" aria-label="Toggle dark mode" type="button">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>
      </button>
    </div>
  </header>
  <div class="backdrop" onclick="toggleNav(false)"></div>
  <div class="layout">
    <aside class="sidebar">
      {''.join(nav)}
    </aside>
    <main class="content">
      {breadcrumb_html}
      {body}
      {pagination_html}
      {footer_html}
    </main>
    {''.join(toc_rail)}
  </div>
  {script}
  {highlight_cdn_script}
</body>
</html>"""


def main():
    if SITE.exists():
        shutil.rmtree(SITE)
    (SITE / "docs").mkdir(parents=True)
    for src, rel, label, group in PAGES:
        md = src.read_text(encoding="utf-8")
        body, toc = convert(md)
        page = render_page(label, group, title_of(md), body, toc, rel)
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
