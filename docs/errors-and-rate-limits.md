# Errors & Rate Limits — Instagram Graph API

> Generated: 2026-10-13 · Base: `https://graph.facebook.com/v25.0`

Every error has the same shape; always log `code`, `error_subcode`, and `fbtrace_id`:

```json
{ "error": { "message": "(#190) Error validating access token", "type": "OAuthException", "code": 190, "fbtrace_id": "AbC123" } }
```

## Common codes

| Code | Meaning | Agent action |
|---|---|---|
| 190 | Token expired/invalid | Re-run OAuth or token exchange; do not retry |
| 10 / 200 | Permission missing or not approved | Request the permission; check App Review status |
| 100 | Invalid parameter (bad field/metric/ID) | Fix the request; bisect field/metric lists |
| 4 | App-level rate limit | Back off; batch and cache |
| 17 | User-level rate limit | Slow down per-account calls |
| 32 | Page-level rate limit | Serialize Page-token calls |
| 613 | Custom-level throttling (e.g. publishing) | Respect the publishing quota; retry later |
| 1 / 2 | Transient API error | Retry with exponential backoff |

## Rate limits

Usage is tracked per app, per user, and per Page. Responses may include `X-App-Usage`, `X-Page-Usage`, and `X-Business-Use-Case-Usage` headers — read `call_count` / `total_time` percentages and throttle before hitting 100%. Publishing has its own quota: check `GET /{ig-user-id}/content_publishing_limit` (see [media-publishing.md](media-publishing.md)).

## Retry policy (recommended)

- Retry only transient failures (codes 1, 2, 4, 17, 32, HTTP 5xx) with exponential backoff: 1s, 2s, 4s, 8s, max 5 attempts, plus jitter.
- Never retry 190, 10, 100, or validation errors without changing the request or credentials.
- Poll video containers every 5–10s instead of tight loops.
- Honor `Retry-After` when present.

```ts
async function withRetry<T>(fn: () => Promise<T>, tries = 5): Promise<T> {
  let delay = 1000;
  for (let i = 0; ; i++) {
    try { return await fn(); }
    catch (e) {
      if (i >= tries - 1) throw e;
      await new Promise((r) => setTimeout(r, delay + Math.random() * 250));
      delay *= 2;
    }
  }
}
```

Next: [faq.md](faq.md) · [getting-started.md](getting-started.md)
