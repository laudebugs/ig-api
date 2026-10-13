export function patternTokenizer(patterns) {
    return (code) => collectPatternRanges(code, patterns);
}
export function collectPatternRanges(code, patterns, initial = [], occupied = new Uint8Array(code.length)) {
    const ranges = [...initial];
    for (const range of initial)
        occupied.fill(1, range.start, range.end);
    for (const pattern of patterns) {
        if ('collect' in pattern) {
            for (const range of pattern.collect(code))
                addRange(ranges, occupied, range);
            continue;
        }
        const regex = cloneRegex(pattern.regex);
        let match;
        while ((match = regex.exec(code))) {
            const value = pattern.group ? match[pattern.group] : match[0];
            if (!value) {
                if (!match[0].length)
                    regex.lastIndex++;
                continue;
            }
            const offset = pattern.group ? match[0].length - value.length : 0;
            const start = match.index + offset;
            addRange(ranges, occupied, {
                start,
                end: start + value.length,
                className: typeof pattern.className === 'function'
                    ? pattern.className(match)
                    : pattern.className,
            });
        }
    }
    return ranges;
}
export function offsetRanges(ranges, offset) {
    return ranges.map((range) => ({
        ...range,
        start: range.start + offset,
        end: range.end + offset,
    }));
}
export function addRange(ranges, occupied, range) {
    if (range.start >= range.end ||
        range.start < 0 ||
        range.end > occupied.length ||
        hasOverlap(occupied, range.start, range.end)) {
        return false;
    }
    ranges.push(range);
    occupied.fill(1, range.start, range.end);
    return true;
}
function cloneRegex(regex) {
    return new RegExp(regex.source, regex.global ? regex.flags : `${regex.flags}g`);
}
function hasOverlap(occupied, start, end) {
    for (let index = start; index < end; index++) {
        if (occupied[index])
            return true;
    }
    return false;
}
