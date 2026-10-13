import { createHighlighter, escapeHtml } from '@tanstack/highlight/core';
import { parseCodeFenceMeta } from '@tanstack/highlight/markdown';
import { shell } from '@tanstack/highlight/languages/shell';
import { ts } from '@tanstack/highlight/languages/ts';
import { python } from '@tanstack/highlight/languages/python';
import { json } from '@tanstack/highlight/languages/json';

export const highlighter = createHighlighter({
  languages: [shell, ts, python, json],
});

export function highlightFence({ code, lang, meta, decorations = [] }) {
  const parsed = parseCodeFenceMeta(meta);
  const result = highlighter.highlight(code, {
    lang,
    lineNumbers: parsed.lineNumbers,
    decorations: [...parsed.decorations, ...decorations],
  });
  return {
    html: result.html.replace('<pre ',
      `<pre tabindex="0" data-highlighted="true" aria-label="${escapeHtml(parsed.title || `${result.lang} code example`)}" `),
    lang: result.lang,
    title: parsed.title,
  };
}
