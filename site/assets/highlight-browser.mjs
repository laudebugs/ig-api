import { highlightFence } from './highlight.mjs';

export function highlightCodeBlocks(root = document) {
  for (const pre of root.querySelectorAll('pre[data-language]:not([data-highlighted])')) {
    const code = pre.querySelector('code');
    if (!code) continue;
    const result = highlightFence({
      code: code.textContent,
      lang: pre.dataset.language,
      meta: pre.dataset.meta,
    });
    const template = document.createElement('template');
    template.innerHTML = result.html;
    pre.replaceWith(template.content);
  }
}

highlightCodeBlocks();
