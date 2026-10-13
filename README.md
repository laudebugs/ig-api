# Instagram Graph API — Agent Documentation Bundle

> Generated: 2026-10-13
> API base: `https://graph.facebook.com/v25.0` or `https://graph.instagram.com/v25.0`
> (set `GRAPH_HOST`/`GRAPH_VERSION` to match your Meta app; Meta's latest known is `v26.0` — verify in Meta for Developers before shipping)
> Audience: coding agents and developers building apps that extend Instagram (publishing, insights, comments, messaging)

This bundle documents both Instagram API flavors: the Instagram Graph API via Facebook Login
(Business/Creator accounts linked to a Facebook Page) and the Instagram API with Instagram
Login (`graph.instagram.com`, no Page required). Start with the comprehensive reference:
[INSTAGRAM_GRAPH_API.md](INSTAGRAM_GRAPH_API.md).

## How an agent should use this bundle

Three ways in — pick one, don't guess from prose:

1. **Read whole**: paste `llms-full.txt` (entire bundle, one file) into context, or read
   [INSTAGRAM_GRAPH_API.md](INSTAGRAM_GRAPH_API.md) (comprehensive narrative, curl + TypeScript + Python).
2. **Retrieve slices**: query `data/chunks.jsonl` (one JSON object per endpoint/topic) for RAG.
3. **Generate a client**: feed `openapi.yaml` (source of truth for paths/schemas) to your
   OpenAPI codegen, with `types/instagram-graph.d.ts` for TypeScript shapes.

Then copy runnable flows from `examples/` (TypeScript + Python), import
`postman/` or `bruno/` to run requests by hand, and open `site/index.html` for the
human-readable reference. Format rationale: [FORMATS.md](FORMATS.md).

## Contents

| File | Purpose |
|---|---|
| [INSTAGRAM_GRAPH_API.md](INSTAGRAM_GRAPH_API.md) | **Comprehensive reference**: both flavors, all endpoints, full curl/TS/Python examples, recipes |
| [FORMATS.md](FORMATS.md) | Format guide: what each artifact is for and when to use it |
| [docs/getting-started.md](docs/getting-started.md) | Prerequisites, app setup, first request |
| [docs/authentication.md](docs/authentication.md) | OAuth, token exchange, Page → IG user ID, permissions |
| [docs/media-publishing.md](docs/media-publishing.md) | Two-step container → publish flow, Reels, carousels, limits |
| [docs/insights.md](docs/insights.md) | Account/media/story insights and metrics |
| [docs/comments-moderation.md](docs/comments-moderation.md) | Read/reply/hide/delete comments, mentions |
| [docs/messaging.md](docs/messaging.md) | Instagram messaging (DMs), 24-hour window |
| [docs/webhooks.md](docs/webhooks.md) | Webhook verification, subscriptions, payloads |
| [docs/errors-and-rate-limits.md](docs/errors-and-rate-limits.md) | Error codes, throttling, retries |
| [docs/faq.md](docs/faq.md) | Common agent pitfalls |
| [openapi.yaml](openapi.yaml) | OpenAPI 3.1 contract (source of truth) |
| [types/instagram-graph.d.ts](types/instagram-graph.d.ts) | TypeScript types |
| [llms.txt](llms.txt) / [llms-full.txt](llms-full.txt) | LLM index / single-file full context |
| [data/chunks.jsonl](data/chunks.jsonl) | One JSON object per endpoint/topic for retrieval |
| [examples/](examples/) | Runnable TypeScript + Python flows (+ shared `lib.ts`/`lib.py`) |
| [postman/](postman/) | Postman collection (runnable requests) |
| [bruno/](bruno/) | Bruno collection (runnable requests, git-friendly) |
| [site/](site/index.html) | Static multi-page site: landing, API reference, formats, guides (built by `scripts/build-site.py`) |
| [scripts/](scripts/) | Builders: `build-site.py`, `build-llms-full.py` |

## Core concepts

- **Two flavors, one path shape**: Facebook Login (`graph.facebook.com`, `EAA…` Page token, Page required) vs Instagram Login (`graph.instagram.com`, `IGAA…` user token, no Page). Never mix hosts/tokens.
- **IG User ID** (`ig-user-id`): numeric ID of the Instagram Business/Creator account, obtained via the linked Facebook Page (`instagram_business_account`) or `me` on Instagram Login. Most paths hang off it.
- **Media container**: publishing is two-step — `POST /{ig-user-id}/media` creates a container, `POST /{ig-user-id}/media_publish` publishes it.
- **Access token**: Page access token (derived from a long-lived user token) authorizes most calls. Pass as `?access_token=...` or `Authorization: Bearer [REDACTED]` (header preferred).
- **Permissions gate features**: e.g. `instagram_content_publish` for publishing, `instagram_manage_insights` for insights. Missing permission → error 10 / 200 (see errors doc).

## Quick start

```bash
export GRAPH_HOST=https://graph.facebook.com
export GRAPH_VERSION=v25.0
export IG_USER_ID=17841400008460056
export ACCESS_TOKEN=EAAB...

# Who am I?
curl -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  "${GRAPH_HOST}/${GRAPH_VERSION}/${IG_USER_ID}?fields=id,username,media_count"
```

Full flows with responses: [INSTAGRAM_GRAPH_API.md](INSTAGRAM_GRAPH_API.md) and [examples/publish-photo.ts](examples/publish-photo.ts).

## Conventions

- `{version}` = Graph API version (e.g. `v25.0`); `{ig-user-id}`, `{media-id}`, `{comment-id}` are numeric IDs (strings in JSON).
- All examples use placeholder tokens/IDs. Never commit real tokens.
- Dates in examples are illustrative. This bundle was generated 2026-10-13; re-check Meta changelogs for deprecations before relying on a version/metric.
- Regenerate derived files after editing sources: `python scripts/build-llms-full.py` and `npm ci && npm run build` (Python 3 and Node.js 20+).

## Deploying the site (GitHub Pages)

`site/index.html` deploys automatically via [.github/workflows/pages.yml](.github/workflows/pages.yml):
push to `main` touching the Markdown sources, site builder, highlighting modules,
or npm manifests rebuilds the site in CI and publishes it with the official
`deploy-pages` action (or run the workflow manually from the Actions tab).

One-time setup: in the GitHub repo go to **Settings → Pages → Source** and select
**GitHub Actions**. The live URL is shown on the workflow run and in the
`github-pages` environment. To preview locally instead: `npm ci && npm run build`
and open `site/index.html`.

Code highlighting uses **TanStack Highlight**, with only shell/Bash, TypeScript,
Python, and JSON registered; unknown languages remain escaped plain text.
The static build and browser share the same synchronous highlighter. Generated
pages already contain highlighted code, so no JavaScript or CDN is needed to
read them. Locally served ES modules can highlight newly inserted code blocks
via `highlightCodeBlocks()` using `data-language` and optional `data-meta`.
Light/dark code themes use CSS semantic classes on a single markup tree.
Code fences can include `title="First request"`, `highlight={1,3-5}`, and
`lineNumbers`; the shared module also accepts exact character-range decorations.
