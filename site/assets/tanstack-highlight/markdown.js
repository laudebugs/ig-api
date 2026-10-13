import { renderNodesToHtml, renderTokens, } from './core.js';
import { parseCodeDiffNotation, prepareCodeFence, tokenizeCodeFence, } from './internal/code-fence.js';
export { getCodeFenceTitle, parseCodeDiffNotation, parseCodeFenceMeta, } from './internal/code-fence.js';
export function renderCodeFence(input, highlighter) {
    const prepared = prepareCodeFence(input);
    return {
        ...highlighter.renderCodeBlockData(prepared),
        decorations: prepared.decorations,
        lineNumbers: prepared.lineNumbers,
    };
}
export function codeFenceToHast(input, highlighter) {
    const rendered = tokenizeCodeFence(input, highlighter);
    return tokensToHast(rendered.tokens, rendered.lang, rendered);
}
export function createTanStackMarkdownHighlighter(highlighter) {
    return (code, lang = 'plaintext', options = {}) => {
        const annotated = parseCodeDiffNotation(code);
        const result = highlighter.tokenize(annotated.code, { lang });
        for (const lines of options.highlightLines || []) {
            annotated.decorations.push({ className: 'th-line--highlighted', lines });
        }
        return renderNodesToHtml(renderTokens(result.tokens, {
            lineNumbers: options.lineNumbers,
            decorations: annotated.decorations,
        }));
    };
}
export function tokensToHast(tokens, lang, options = {}) {
    return {
        type: 'element',
        tagName: 'pre',
        properties: {
            className: [
                'th-code',
                `th-code--${lang}`,
                ...(options.lineNumbers ? ['th-code--line-numbers'] : []),
            ],
            dataLanguage: lang,
            ...(options.title ? { dataTitle: options.title } : {}),
        },
        children: [
            {
                type: 'element',
                tagName: 'code',
                properties: {},
                children: renderTokens(tokens, options).map(renderNodeToHast),
            },
        ],
    };
}
function renderNodeToHast(node) {
    if (node.type === 'text')
        return node;
    const properties = { className: node.classNames };
    if (node.data) {
        for (const [key, value] of Object.entries(node.data)) {
            properties[`data${key[0]?.toUpperCase() || ''}${key.slice(1)}`] = value;
        }
    }
    return {
        type: 'element',
        tagName: 'span',
        properties,
        children: node.children.map(renderNodeToHast),
    };
}
