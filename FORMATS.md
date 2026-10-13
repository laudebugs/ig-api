# Formats — beyond Markdown

> Markdown is the narrative layer: readable but not validatable or executable.
> For coding agents, keep Markdown and add machine-readable companions generated
> from one source (`openapi.yaml` + `INSTAGRAM_GRAPH_API.md`).

## What this bundle ships

| Format | File(s) | Consumer | Strength |
|---|---|---|---|
| Comprehensive Markdown | `INSTAGRAM_GRAPH_API.md` | Agents, humans | Full narrative + curl/TS/Python per endpoint; recipes |
| Topic Markdown | `docs/*.md` | Humans, scoped reads | Short guides per flow |
| OpenAPI 3.1 YAML | `openapi.yaml` | Agents, codegen | **Source of truth**: validatable paths, params, schemas, auth |
| TypeScript types | `types/instagram-graph.d.ts` | Agents writing TS | Typed requests/responses/errors |
| LLM index + full dump | `llms.txt`, `llms-full.txt` | LLM context loaders | Compact index; one-file whole-bundle context |
| RAG chunks | `data/chunks.jsonl` | Vector search / retrieval | One slice per endpoint (`id,title,path,method,content`) |
| Runnable examples | `examples/*.ts`, `examples/*.py` | Agents, humans | Copy-paste flows: publish, insights, replies, webhooks |
| Postman collection | `postman/*.json` | Agents, humans, QA | Runnable requests with variables + environments |
| Bruno collection | `bruno/` | Agents, humans (git-native) | Same as Postman, plain-text diffable files |
| Static HTML site | `site/` (multi-page) | Humans | Searchable, linkable, zero-hosting reference |
| MCP starter | `mcp/tools.json`, `mcp/server.py` | Agents (MCP clients) | 14 callable tools: agents *call* the API mid-session |

## Which to use when

- **Agent building a feature**: read `llms.txt` → pull `data/chunks.jsonl` slices for the
  endpoints involved → copy the matching `examples/` flow → type against `.d.ts`.
- **Agent with a big context window**: paste `llms-full.txt` whole, then work from
  `INSTAGRAM_GRAPH_API.md` section numbers.
- **Generating a client SDK**: run OpenAPI codegen on `openapi.yaml`
  (`npx @openapitools/openapi-generator-cli generate -i openapi.yaml -g typescript-fetch …`).
- **Human verifying behavior**: import `postman/` or open `bruno/`, set variables, run
  the request; cross-check against `site/index.html`.
- **RAG pipeline**: embed `data/chunks.jsonl` (30 chunks); re-chunk `INSTAGRAM_GRAPH_API.md`
  by `##` section for long-form retrieval.

## Suggested next formats (not yet built)

| Format | Why | Effort |
|---|---|---|
| MCP server (full) | Extend `mcp/` starter: carousel/story flows, block, conversations, webhook intake, evals | Medium — starter exists, add tools + tests |
| AsyncAPI for webhooks | Machine-readable event catalog (comment/message/mention payloads) mirroring `openapi.yaml` | Small — derive from §13 payloads |
| JSON Schema files | Standalone request/response validation without the full OpenAPI toolchain | Small — extract from `openapi.yaml` components |
| Python type stubs (`.pyi`) / mini-SDK | Typed Python equivalent of the `.d.ts` for agents writing Python | Small — type `examples/lib.py` |
| SDK packages (npm/PyPI) | Versioned client both agents and apps can depend on | Large — needs tests + CI + publishing |
| CLI (`ig` command) | Human/agent shell access: `ig publish photo.jpg --caption …` | Medium — wraps the SDK |
| SQLite/Parquet snapshot | Frozen, queryable dataset of endpoints + metrics for offline evals | Small — export chunks + metric tables |
| Evals (`evals/`) | Ground-truth Q/A + fixture-backed tests proving an agent can use the docs | Medium — highest value for doc-quality measurement |

Recommendation: finish the **MCP server** (extend the starter) and add **AsyncAPI
webhooks** next — they close the loop from "read the docs" to "call the API and handle
its events" for agents.

## Maintenance rule

`openapi.yaml` is the source of truth for paths/params/schemas;
`INSTAGRAM_GRAPH_API.md` is the source of truth for narrative/examples. After editing
either, regenerate derivatives:

```bash
python scripts/build-llms-full.py   # rebuilds llms-full.txt
python scripts/build-site.py        # rebuilds site/index.html
```

`data/chunks.jsonl`, `postman/`, and `bruno/` are hand-synced for now — update the
matching entries when endpoints change (a generator from `openapi.yaml` is a good
follow-up task).
