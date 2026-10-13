export function defineLanguage(definition) {
    return definition;
}
export function createHighlighter({ fallbackLanguage = 'plaintext', languages, }) {
    const definitions = new Map();
    const aliases = new Map();
    for (const definition of languages) {
        const name = normalizeName(definition.name);
        definitions.set(name, definition);
        aliases.set(name, name);
        for (const alias of definition.aliases || []) {
            aliases.set(normalizeName(alias), name);
        }
    }
    const fallback = normalizeName(fallbackLanguage);
    function normalizeLanguage(lang) {
        return aliases.get(normalizeName(lang || fallback)) || fallback;
    }
    function tokenizeRanges(code, lang, depth = 0) {
        const definition = definitions.get(normalizeLanguage(lang));
        if (!definition || depth > 24)
            return [];
        const context = {
            hasLanguage(candidate) {
                const resolved = aliases.get(normalizeName(candidate));
                return Boolean(resolved && definitions.has(resolved));
            },
            tokenize(embeddedCode, embeddedLanguage) {
                return tokenizeRanges(embeddedCode, embeddedLanguage, depth + 1);
            },
        };
        return normalizeTokenRanges(code.length, definition.tokenize(code, context));
    }
    function tokenize(code, options = {}) {
        const lang = normalizeLanguage(options.lang);
        const ranges = tokenizeRanges(code, lang);
        return {
            code,
            lang,
            tokens: ranges.length ? rangesToTokens(code, ranges) : [{ value: code }],
        };
    }
    function highlight(code, options = {}) {
        const result = tokenize(code, options);
        const children = renderTokens(result.tokens, options);
        const innerHtml = renderNodesToHtml(children);
        return {
            ...result,
            html: `<pre class="th-code th-code--${escapeHtml(result.lang)}${options.lineNumbers ? ' th-code--line-numbers' : ''}" data-language="${escapeHtml(result.lang)}"><code>${innerHtml}</code></pre>`,
        };
    }
    function renderCodeBlockData({ code, decorations, lang, lineNumbers, title, }) {
        const copyText = code.trimEnd();
        const result = highlight(copyText, { decorations, lang, lineNumbers });
        return {
            copyText,
            htmlMarkup: result.html,
            lang: result.lang,
            title,
            tokens: result.tokens,
        };
    }
    return {
        highlight,
        highlightToHtml(code, options = {}) {
            return highlight(code, options).html;
        },
        listLanguages() {
            return [...definitions.keys()];
        },
        normalizeLanguage,
        renderCodeBlockData,
        tokenize,
    };
}
export function renderTokens(tokens, options = {}) {
    const rangeDecorations = [];
    const lineDecorations = [];
    for (const decoration of options.decorations || []) {
        if (decoration.range)
            rangeDecorations.push(decoration);
        else
            lineDecorations.push(decoration);
    }
    const wrapLines = Boolean(options.lineNumbers || lineDecorations.length);
    const cursor = { index: 0, offset: 0 };
    if (!wrapLines) {
        return renderTokenSlice(tokens, 0, Infinity, rangeDecorations, cursor);
    }
    const code = tokens.map((token) => token.value).join('');
    const nodes = [];
    const lineStarts = getLineStarts(code);
    for (let index = 0; index < lineStarts.length; index++) {
        const line = index + 1;
        const start = lineStarts[index];
        const nextStart = lineStarts[index + 1] ?? code.length;
        const hasNewline = nextStart > start && code[nextStart - 1] === '\n';
        const end = hasNewline ? nextStart - 1 : nextStart;
        const active = lineDecorations.filter((decoration) => includesLine(decoration.lines, line));
        nodes.push({
            type: 'element',
            classNames: [
                'th-line',
                ...active.flatMap((decoration) => splitClassNames(decoration.className)),
            ],
            data: {
                ...mergeData(active),
                line: String(line),
            },
            children: renderTokenSlice(tokens, start, end, rangeDecorations, cursor),
        });
        if (hasNewline)
            nodes.push({ type: 'text', value: '\n' });
    }
    return nodes;
}
export function renderNodesToHtml(nodes) {
    let html = '';
    for (const node of nodes) {
        if (node.type === 'text') {
            html += escapeHtml(node.value);
            continue;
        }
        const className = escapeHtml(node.classNames.join(' '));
        let data = '';
        if (node.data) {
            for (const [key, value] of Object.entries(node.data)) {
                data += ` data-${normalizeDataKey(key)}="${escapeHtml(value)}"`;
            }
        }
        html += `<span${className ? ` class="${className}"` : ''}${data}>${renderNodesToHtml(node.children)}</span>`;
    }
    return html;
}
const htmlEscapes = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
};
export function escapeHtml(value) {
    return value.replace(/[&<>"']/g, (character) => htmlEscapes[character]);
}
function normalizeName(value) {
    return value.trim().toLowerCase();
}
function normalizeTokenRanges(codeLength, input) {
    const ranges = [];
    let sorted = true;
    let previousStart = 0;
    for (const candidate of input) {
        if (!Number.isInteger(candidate.start) || !Number.isInteger(candidate.end))
            continue;
        const start = Math.max(0, Math.min(codeLength, candidate.start));
        const end = Math.max(0, Math.min(codeLength, candidate.end));
        if (start >= end)
            continue;
        if (start < previousStart)
            sorted = false;
        previousStart = start;
        ranges.push({ className: candidate.className, start, end });
    }
    if (!sorted)
        ranges.sort((a, b) => a.start - b.start);
    let end = 0;
    let count = 0;
    for (const candidate of ranges) {
        if (candidate.start < end)
            continue;
        ranges[count++] = candidate;
        end = candidate.end;
    }
    ranges.length = count;
    return ranges;
}
function rangesToTokens(code, ranges) {
    const tokens = [];
    let index = 0;
    for (const range of ranges) {
        if (range.start > index)
            tokens.push({ value: code.slice(index, range.start) });
        tokens.push({
            className: range.className,
            value: code.slice(range.start, range.end),
        });
        index = range.end;
    }
    if (index < code.length)
        tokens.push({ value: code.slice(index) });
    return tokens;
}
function renderTokenSlice(tokens, start, end, decorations, cursor) {
    const nodes = [];
    for (; cursor.index < tokens.length; cursor.index++) {
        const token = tokens[cursor.index];
        const tokenStart = cursor.offset;
        const tokenEnd = tokenStart + token.value.length;
        const sliceStart = Math.max(start, tokenStart);
        const sliceEnd = Math.min(end, tokenEnd);
        if (sliceStart < sliceEnd) {
            let sorted = [sliceStart, sliceEnd];
            if (decorations.length) {
                const boundaries = new Set(sorted);
                for (const decoration of decorations) {
                    const [decorationStart, decorationEnd] = decoration.range;
                    if (decorationEnd <= sliceStart || decorationStart >= sliceEnd)
                        continue;
                    boundaries.add(Math.max(sliceStart, decorationStart));
                    boundaries.add(Math.min(sliceEnd, decorationEnd));
                }
                sorted = [...boundaries].sort((a, b) => a - b);
            }
            for (let index = 0; index < sorted.length - 1; index++) {
                const segmentStart = sorted[index];
                const segmentEnd = sorted[index + 1];
                let node = {
                    type: 'text',
                    value: token.value.slice(segmentStart - tokenStart, segmentEnd - tokenStart),
                };
                if (token.className) {
                    node = {
                        type: 'element',
                        classNames: ['th-token', `th-${token.className}`],
                        children: [node],
                    };
                }
                for (const decoration of decorations) {
                    if (decoration.range[0] > segmentStart ||
                        decoration.range[1] < segmentEnd)
                        continue;
                    node = {
                        type: 'element',
                        classNames: [
                            'th-decoration',
                            ...splitClassNames(decoration.className),
                        ],
                        data: stringifyData(decoration.data),
                        children: [node],
                    };
                }
                nodes.push(node);
            }
        }
        // Keep a token that crosses the line boundary for the next slice.
        if (tokenEnd > end)
            break;
        cursor.offset = tokenEnd;
    }
    return nodes;
}
function getLineStarts(code) {
    const starts = [0];
    for (let index = 0; index < code.length; index++) {
        if (code[index] === '\n' && index + 1 < code.length)
            starts.push(index + 1);
    }
    return starts;
}
function includesLine(lines, line) {
    return typeof lines === 'number'
        ? lines === line
        : line >= lines[0] && line <= lines[1];
}
function mergeData(decorations) {
    const data = {};
    for (const decoration of decorations) {
        Object.assign(data, stringifyData(decoration.data));
    }
    return data;
}
function stringifyData(data) {
    if (!data)
        return undefined;
    return Object.fromEntries(Object.entries(data).map(([key, value]) => [
        normalizeDataKey(key),
        String(value),
    ]));
}
function normalizeDataKey(value) {
    return toKebabCase(value).replace(/[^a-z0-9_.:-]/gi, '-');
}
function splitClassNames(className) {
    return className?.trim().split(/\s+/).filter(Boolean) || [];
}
function toKebabCase(value) {
    return value.replace(/[A-Z]/g, (character) => `-${character.toLowerCase()}`);
}
