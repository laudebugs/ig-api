import { highlightFence } from './highlight.mjs';

let input = '';
for await (const chunk of process.stdin) input += chunk;
process.stdout.write(JSON.stringify(JSON.parse(input).map(highlightFence)));
