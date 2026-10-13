# Instagram API — Comprehensive Agent Documentation

> Generated: 2026-10-13 · Default version in examples: `v25.0` (Meta's latest is `v26.0`,
> released 2026-07-29 — verify in the [Graph API changelog](https://developers.facebook.com/docs/graph-api/changelog)
> before shipping) · Audience: coding agents and developers building apps that extend Instagram.
>
> Conventions: `{version}` = Graph API version (keep in `GRAPH_VERSION` env var).
> `{ig-user-id}`, `{media-id}`, `{comment-id}` are numeric strings. `{token}` = access token
> (placeholder `EAAB...` / `IGAA...` — never commit real tokens).
> Every endpoint below shows **curl + TypeScript + Python** unless noted.

## Contents

- [0. How coding agents should use this doc](#0-how-coding-agents-should-use-this-doc)
- [1. API landscape: two flavors](#1-api-landscape-two-flavors)
- [2. Concepts and mental model](#2-concepts-and-mental-model)
- [3. App setup](#3-app-setup)
- [4. Authentication](#4-authentication)
- [5. Core conventions](#5-core-conventions)
- [6. Identity and accounts](#6-identity-and-accounts)
- [7. Reading media (feed, Reels, Stories, albums)](#7-reading-media-feed-reels-stories-albums)
- [8. Publishing](#8-publishing)
- [9. Hashtags and Business Discovery](#9-hashtags-and-business-discovery)
- [10. Comments and moderation](#10-comments-and-moderation)
- [11. Insights and analytics](#11-insights-and-analytics)
- [12. Messaging (DMs)](#12-messaging-dms)
- [13. Webhooks](#13-webhooks)
- [14. Mentions and tags](#14-mentions-and-tags)
- [15. Errors, rate limits, retries](#15-errors-rate-limits-retries)
- [16. Permissions, App Review, going live](#16-permissions-app-review-going-live)
- [17. Agent build recipes (extend Instagram)](#17-agent-build-recipes-extend-instagram)
- [18. FAQ and troubleshooting](#18-faq-and-troubleshooting)
- [Appendix A: Endpoint quick reference](#appendix-a-endpoint-quick-reference)
- [Appendix B: Companion files in this bundle](#appendix-b-companion-files-in-this-bundle)

---

## 0. How coding agents should use this doc

1. **Pick a flavor first** (§1). The host, token type, and OAuth flow all follow from that
   choice. Never mix `graph.facebook.com` tokens with `graph.instagram.com` calls.
2. **Keep config in env**: `GRAPH_HOST`, `GRAPH_VERSION`, `IG_USER_ID`, `ACCESS_TOKEN`.
   All examples below assume these are set.
3. **Machine-readable contract**: `openapi.yaml` mirrors these endpoints; `types/instagram-graph.d.ts`
   gives TypeScript shapes; `data/chunks.jsonl` gives one RAG chunk per endpoint.
4. **Copy, don't improvise**: runnable flows live in `examples/` (TypeScript + Python).
   Prefer them over hand-rolled requests.
5. **Verify before shipping**: metric names, permissions, and version availability change.
   Confirm against Meta for Developers and test in Development mode with a role-holding account.

```bash
# Standard env used by every example in this doc
export GRAPH_HOST="https://graph.facebook.com"   # or https://graph.instagram.com
export GRAPH_VERSION="v25.0"
export IG_USER_ID="17841400008460056"
export ACCESS_TOKEN="EAAB..."
export BASE="${GRAPH_HOST}/${GRAPH_VERSION}"
```

TypeScript helper used throughout (save as `examples/lib.ts` or inline):

```ts
// Minimal typed Graph client (fetch, no SDK)
const BASE = `${process.env.GRAPH_HOST ?? "https://graph.facebook.com"}/${process.env.GRAPH_VERSION ?? "v25.0"}`;
const TOKEN = process.env.ACCESS_TOKEN!;

export async function gget<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { headers: { Authorization: `Bearer ${TOKEN}` } });
  const json = (await res.json()) as T & { error?: { message: string; code: number } };
  if (!res.ok) throw new Error(`GET ${path} → ${json.error?.code}: ${json.error?.message ?? res.status}`);
  return json;
}

export async function gpost<T>(path: string, body: Record<string, string> = {}): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({ ...body, access_token: TOKEN }),
  });
  const json = (await res.json()) as T & { error?: { message: string; code: number } };
  if (!res.ok) throw new Error(`POST ${path} → ${json.error?.code}: ${json.error?.message ?? res.status}`);
  return json;
}
```

Python helper used throughout (save as `examples/lib.py` or inline):

```python
# Minimal Graph client (requests, pip install requests)
import os
import requests

BASE = f"{os.environ.get('GRAPH_HOST', 'https://graph.facebook.com')}/{os.environ.get('GRAPH_VERSION', 'v25.0')}"
TOKEN = os.environ["ACCESS_TOKEN"]

def gget(path, params=None):
    r = requests.get(f"{BASE}{path}", headers={"Authorization": f"Bearer {TOKEN}"},
                     params=params or {}, timeout=30)
    data = r.json()
    if r.status_code != 200:
        raise RuntimeError(f"GET {path} -> {data.get('error', r.status_code)}")
    return data

def gpost(path, data=None):
    payload = dict(data or {}); payload["access_token"] = TOKEN
    r = requests.post(f"{BASE}{path}", data=payload, timeout=60)
    body = r.json()
    if r.status_code != 200:
        raise RuntimeError(f"POST {path} -> {body.get('error', r.status_code)}")
    return body
```

## 1. API landscape: two flavors

Meta ships **two Instagram API products**. They overlap in endpoints but differ in host,
auth, and account linkage. Pick one per app — tokens are **not** interchangeable.

|  | Instagram Graph API (Facebook Login) | Instagram API (Instagram Login) |
|---|---|---|
| Host | `https://graph.facebook.com` | `https://graph.instagram.com` |
| Token prefix | `EAA…` (Page access token) | `IGAA…` / `IGQW…` (IG user token) |
| Requires Facebook Page linked to IG? | **Yes** | **No** — token *is* the IG account |
| IG account type | Business or Creator | Business or Creator |
| OAuth dialog host | `www.facebook.com/dialog/oauth` | Instagram OAuth (`instagram.com` / Meta Business Login for Instagram) |
| Scopes look like | `instagram_basic`, `instagram_content_publish`, … | `instagram_business_basic`, `instagram_business_content_publish`, … |
| Typical `IG_USER_ID` | Numeric Page-derived ID (`instagram_business_account.id`) | Numeric IG ID, or `me` for the token owner |
| Webhooks object | Facebook app → Instagram object, often Page-mediated | Instagram object, flat `field`/`value` for content + `messaging[]` for DMs |
| Best for | Agencies/managers handling many Pages, existing Facebook apps | Consumer/creator apps, no-Page onboarding, new builds |

**Which to choose?**

- New app, creators log in with Instagram directly → **Instagram Login** (simpler onboarding).
- Managing Pages/assets you already own, or you need edges only exposed via Pages
  (some `/tags` behaviors, Page-level subscriptions) → **Facebook Login**.
- Either way, the **endpoint paths in §§6–15 are the same shape**; only host, token, and
  scope names differ. Examples in this doc use the Facebook Login host; swap `GRAPH_HOST`
  and scopes for Instagram Login.

> The legacy Instagram Basic Display API (personal-account media read) is retired —
> do not build on it. Personal accounts cannot use either flavor above; the IG account
> must be Business or Creator.

## 2. Concepts and mental model

- **IG User ID** (`ig-user-id`): the Instagram Business/Creator account ID. Most paths hang
  off it: `/media`, `/insights`, `/messages`, `/stories`, `/tags`. With Instagram Login
  you can often use `me` instead of the numeric ID.
- **Media vs container**: publishing is **two-step**. `POST /{ig-user-id}/media` creates a
  *container* (unpublished draft, expires in ~24h); `POST /{ig-user-id}/media_publish`
  with `creation_id` publishes it and returns the real **media ID**. Insights/comments act
  on the media ID, never the container ID.
- **IGSID** (Instagram-scoped ID): the per-app user ID for someone who messaged the account.
  Delivered only via webhooks. You reply to IGSIDs, never to usernames.
- **Page access token** (Facebook Login flavor): derived from a long-lived user token via
  `/me/accounts`. It authorizes IG calls. Effectively non-expiring unless revoked/password
  change (still handle error 190).
- **Permissions gate features**: each feature needs its scope (§16). Missing/ unapproved
  scope → error 10/200. Request least privilege; each scope may need App Review.
- **Versioning**: versions release ~quarterly, supported ~2 years, then deprecated.
  Pin `GRAPH_VERSION`, watch the changelog, and migrate before deprecation.
- **Professional accounts only**: Business or Creator, and (Facebook Login flavor) linked to
  a Facebook Page. Development mode restricts calls to users with a role on the Meta app.

## 3. App setup

### 3.1 Facebook Login flavor (graph.facebook.com)

1. **Professional IG account**: in Instagram → Settings → Account type → Switch to
   professional (Business or Creator).
2. **Link a Facebook Page**: Page Settings → Linked accounts → connect the IG account.
   Confirm the link by viewing the Page's `instagram_business_account` (§4, Step 4).
3. **Create a Meta app** at developers.facebook.com → add products **Facebook Login**
   and reference the Instagram Graph API. Save App ID + App Secret.
4. **Configure OAuth**: valid redirect URI(s), request scopes (§16) for your use case.
5. **Roles for testing**: App Roles → add your test Facebook/IG users. Development mode
   only works for role holders until App Review passes.
6. (Messaging/webhooks) Add the **Webhooks** product, set callback URL + verify token (§13).

### 3.2 Instagram Login flavor (graph.instagram.com)

1. **Professional IG account** (same as above). No Facebook Page needed.
2. **Create a Meta app** with the **Instagram** product configured for **Instagram Login**
   (also called "Business Login for Instagram"). This is a different app product than the
   classic Instagram Graph API — an app with only the classic product cannot mint
   Instagram Login tokens. Save the Instagram App ID + Secret.
3. **Configure OAuth** with `instagram_business_*` scopes (§16) and redirect URI.
4. **Test users**: add IG test accounts with roles on the app; Development mode gating
   applies the same way.

### 3.3 Environment checklist

- [ ] `GRAPH_HOST`, `GRAPH_VERSION`, `IG_USER_ID`, `ACCESS_TOKEN` in a secret store (never in repo/prompts)
- [ ] Token scopes verified via `debug_token` (§4.4)
- [ ] Webhook callback HTTPS + verify token + signature validation (§13)
- [ ] Publishing quota checked (`content_publishing_limit`, §8.8)
- [ ] Error-190 re-auth path implemented (§15), not just retries

## 4. Authentication

### 4.1 Facebook Login flow (full)

**Step 1 — Authorization dialog** (browser redirect):

```text
https://www.facebook.com/v25.0/dialog/oauth
  ?client_id={app-id}
  &redirect_uri={redirect-uri}
  &scope=instagram_basic,instagram_content_publish,instagram_manage_comments,instagram_manage_insights,pages_show_list,pages_read_engagement
  &response_type=code
```

Success returns `{redirect-uri}?code={code}`. Handle `?error=access_denied` when the
user cancels — show reconnect UX, don't retry silently.

**Step 2 — Code → short-lived user token (~1h):**

```bash
curl -G "${BASE}/oauth/access_token" \
  --data-urlencode "client_id=${APP_ID}" \
  --data-urlencode "client_secret=${APP_SECRET}" \
  --data-urlencode "redirect_uri=${REDIRECT_URI}" \
  --data-urlencode "code=${CODE}"
# → {"access_token":"EAABshort...","token_type":"bearer","expires_in":3600}
```

**Step 3 — Short-lived → long-lived user token (~60 days):**

```bash
curl -G "${BASE}/oauth/access_token" \
  --data-urlencode "grant_type=fb_exchange_token" \
  --data-urlencode "client_id=${APP_ID}" \
  --data-urlencode "client_secret=${APP_SECRET}" \
  --data-urlencode "fb_exchange_token=${SHORT_LIVED_TOKEN}"
# → {"access_token":"EAABlong...","token_type":"bearer","expires_in":5184000}
```

Store server-side only. Refresh before expiry by repeating this exchange with a
still-valid long-lived token (returns a fresh ~60-day token).

TypeScript:

```ts
const qs = new URLSearchParams({ grant_type: "fb_exchange_token", client_id: APP_ID,
  client_secret: APP_SECRET, fb_exchange_token: shortLived });
const tok = await fetch(`${BASE}/oauth/access_token?${qs}`).then(r => r.json());
```

Python:

```python
tok = requests.get(f"{BASE}/oauth/access_token", params={
    "grant_type": "fb_exchange_token", "client_id": APP_ID,
    "client_secret": APP_SECRET, "fb_exchange_token": short_lived}, timeout=30).json()
long_lived = tok["access_token"]
```

**Step 4 — Page token + IG User ID:**

```bash
curl -G "${BASE}/me/accounts" \
  --data-urlencode "fields=id,name,access_token,instagram_business_account{id,username}" \
  --data-urlencode "access_token=${LONG_LIVED_USER_TOKEN}"
```

```json
{ "data": [{
    "id": "109876543210", "name": "Example Page", "access_token": "EAABpage...",
    "instagram_business_account": { "id": "17841400008460056", "username": "examplebrand" }
}]}
```

Use the Page `access_token` for all IG calls; `instagram_business_account.id` is `IG_USER_ID`.
If `instagram_business_account` is absent, the Page↔IG link is missing (§3.1 step 2).

**Step 5 — Verify scopes and expiry** (see §4.4).

### 4.2 Instagram Login flow (full)

Same shape, different hosts/scopes — do not mix with §4.1 values:

1. Redirect the creator to the Instagram authorize URL configured for your Instagram app
   with `instagram_business_basic`, `instagram_business_content_publish`, etc. (§16).
2. Exchange `code` at the Instagram token endpoint for a short-lived IG user token.
3. Exchange for a long-lived IG token (~60 days); refresh with a still-valid token via
   the refresh endpoint (`grant_type=ig_refresh_token` style refresh — check current
   Instagram Platform docs for exact params, they differ from `fb_exchange_token`).
4. The token owner is the IG account: use `IG_USER_ID=me` or the numeric IG ID.
5. Verify with `GET /me?fields=user_id,username` on `graph.instagram.com`.

```bash
# Instagram Login flavor: who am I?
curl -G "https://graph.instagram.com/v25.0/me" \
  --data-urlencode "fields=user_id,username,account_type" \
  --data-urlencode "access_token=${IG_TOKEN}"
```

### 4.3 Token storage and rotation rules

- Server-side only (secret manager / env). Never in client bundles, repos, logs, or prompts.
- One row per connected account: `{ ig_user_id, page_id?, token_ciphertext, scopes, expires_at }`.
- Refresh long-lived tokens on a schedule (e.g. day 50 of 60), not on failure.
- On **error 190** (invalid/expired token): mark the connection `needs_reauth` and restart
  OAuth — never retry the same call in a loop.
- Implement the **Data Deletion callback** and **deauthorize webhook** Meta requires for
  App Review (confirm user data removal when they disconnect).

### 4.4 Verify a token (debug_token)

```bash
curl -G "${BASE}/debug_token" \
  --data-urlencode "input_token=${ACCESS_TOKEN}" \
  --data-urlencode "access_token=${APP_ID}|${APP_SECRET}"
```

```json
{ "data": { "is_valid": true, "app_id": "123…", "type": "PAGE",
  "expires_at": 0, "scopes": ["instagram_basic", "instagram_content_publish", "pages_show_list"] }}
```

Gate every new connection on `is_valid=true` + required scopes present. `expires_at: 0`
means non-expiring (typical for Page tokens derived from long-lived user tokens).

## 5. Core conventions

### 5.1 Auth header vs query param

Both work; prefer the header (tokens stay out of logs/URLs):

```bash
curl -H "Authorization: Bearer ${ACCESS_TOKEN}" "${BASE}/${IG_USER_ID}?fields=id,username"
```

Form-encoded `POST` bodies in this doc use `access_token` in the body (Meta convention);
JSON `POST`s (messaging) use the `Authorization` header.

### 5.2 Field selection and expansion

Always pass `fields` — default payloads are sparse and version-dependent:

```bash
# Nested expansion: business discovery + media children in one call
curl -G "${BASE}/${IG_USER_ID}" \
  --data-urlencode "fields=id,username,media.limit(5){id,caption,media_type,children{id,media_type}}" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}"
```

Invalid field → error 100 naming the field. Bisect field lists on failure.

### 5.3 Pagination (cursor-based)

List edges return `paging: { cursors: { before, after }, next? }`. Walk `after` until
`paging.next` is absent. `limit` default 25, max varies by edge (use ≤50 defensively).

TypeScript:

```ts
async function* pages<T>(firstPath: string) {
  let path: string | undefined = firstPath;
  while (path) {
    const url = path.startsWith("http") ? path : `${BASE}${path}`;
    const res = await fetch(url, { headers: { Authorization: `Bearer ${TOKEN}` } });
    const json = await res.json() as { data: T[]; paging?: { cursors?: { after?: string }; next?: string } };
    if (!res.ok) throw new Error(JSON.stringify(json));
    yield* json.data;
    path = json.paging?.next;
  }
}
// usage: for await (const m of pages<Media>(`/${IG_USER_ID}/media?fields=id,caption&limit=50`)) { … }
```

Python:

```python
def pages(first_path, params=None):
    url, params = f"{BASE}{first_path}", dict(params or {})
    while url:
        r = requests.get(url, headers={"Authorization": f"Bearer {TOKEN}"},
                         params=params, timeout=30)
        body = r.json()
        if r.status_code != 200:
            raise RuntimeError(body.get("error", r.status_code))
        yield from body.get("data", [])
        url = (body.get("paging") or {}).get("next")
        params = {}  # 'next' already encodes the cursor
```

### 5.4 Timestamps

- Media/comment `timestamp` fields: ISO 8601 (`2026-10-13T10:00:00+0000`).
- Insights `since`/`until`: **Unix seconds**. Align to full days; partial windows truncate silently.
- Webhook `entry[].time`: Unix seconds.

### 5.5 Reading rate-limit headers

Every response may include `X-App-Usage`, `X-Page-Usage`, `X-Business-Use-Case-Usage`
(JSON like `{"call_count":42,"total_time":31,"total_cputime":28}` = % of limit used).
Throttle proactively past ~70%; see §15 for the full retry policy.

## 6. Identity and accounts

Requires: `instagram_basic` (FB Login) / `instagram_business_basic` (IG Login).

### 6.1 Get IG user profile — `GET /{ig-user-id}`

```bash
curl -G "${BASE}/${IG_USER_ID}" \
  --data-urlencode "fields=id,username,name,biography,account_type,media_count,followers_count,follows_count,profile_picture_url,website" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}"
```

```json
{ "id": "17841400008460056", "username": "examplebrand", "account_type": "BUSINESS",
  "media_count": 42, "followers_count": 120400, "follows_count": 312 }
```

TypeScript / Python (helpers from §0):

```ts
const me = await gget<IgUser>(`/${process.env.IG_USER_ID}?fields=id,username,account_type,media_count,followers_count`);
```

```python
me = gget(f"/{os.environ['IG_USER_ID']}",
          {"fields": "id,username,account_type,media_count,followers_count"})
```

Useful fields: `id,username,name,biography,account_type,media_count,followers_count,
follows_count,profile_picture_url,website`. Shopping-enabled accounts may expose
`shopping_review_status` and related fields — check your version's User reference.

### 6.2 Resolve IG User ID from a Page — `GET /{page-id}`

```bash
curl -G "${BASE}/${PAGE_ID}" \
  --data-urlencode "fields=instagram_business_account{id,username}" \
  -H "Authorization: Bearer ${USER_TOKEN}"
# → {"instagram_business_account": {"id": "178414…", "username": "examplebrand"}, "id": "1098…"}
```

Missing `instagram_business_account` ⇒ Page↔IG link absent. Re-link in Page Settings.

### 6.3 Linked Facebook Page (reverse lookup)

```bash
curl -G "${BASE}/${IG_USER_ID}" \
  --data-urlencode "fields=id,username,connected_facebook_page" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}"
```

## 7. Reading media (feed, Reels, Stories, albums)

Requires: `instagram_basic` / `instagram_business_basic`.

### 7.1 List media — `GET /{ig-user-id}/media`

```bash
curl -G "${BASE}/${IG_USER_ID}/media" \
  --data-urlencode "fields=id,caption,media_type,media_product_type,media_url,thumbnail_url,permalink,timestamp,like_count,comments_count" \
  --data-urlencode "limit=25" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}"
```

- `media_type`: `IMAGE` | `VIDEO` | `CAROUSEL_ALBUM`.
- `media_product_type`: `FEED` | `REELS` | `STORY`.
- Paginate with `paging.next` (§5.3). Filter client-side by `media_product_type` for
  Reels-only views — there is no server-side product-type filter on this edge.

### 7.2 Get one media object — `GET /{media-id}`

Same `fields` as §7.1 plus `owner`, `children{id,media_type,media_url}` for albums,
`is_comment_enabled`. Store `permalink` for link-backs; `media_url` may expire — do not
hotlink it long-term, re-fetch or cache the bytes (respecting rights).

### 7.3 Carousel children — `GET /{media-id}/children`

```bash
curl -G "${BASE}/${MEDIA_ID}/children" \
  --data-urlencode "fields=id,media_type,media_url,thumbnail_url,permalink" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}"
```

### 7.4 Stories — `GET /{ig-user-id}/stories` then `GET /{story-media-id}`

```bash
curl -G "${BASE}/${IG_USER_ID}/stories" \
  --data-urlencode "fields=id,media_type,media_url,timestamp,expiry_time" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}"
```

Stories expire after 24h; `media_url` dies with them. Fetch story insights (§11.4)
while live.

### 7.5 oEmbed (public posts, no token)

For rendering a public post/preview without auth:

```bash
curl -G "${BASE}/instagram_oembed" \
  --data-urlencode "url=https://www.instagram.com/p/${SHORTCODE}/" \
  --data-urlencode "fields=author_name,author_url,provider_name,title,html,thumbnail_url,width,height"
```

Availability and auth requirements for oEmbed have changed across versions — if it
returns an auth error on your version, fall back to `GET /{media-id}` with a token.

TypeScript + Python:

```ts
const stories = await gget<MediaList>(`/${process.env.IG_USER_ID}/stories?fields=id,media_type,timestamp&limit=25`);
for await (const m of pages<Media>(`/${process.env.IG_USER_ID}/media?fields=id,caption,media_product_type,timestamp&limit=50`)) {
  console.log(m.id, m.media_product_type, m.timestamp);
}
```

```python
stories = gget(f"/{os.environ['IG_USER_ID']}/stories",
               {"fields": "id,media_type,timestamp", "limit": "25"})
for m in pages(f"/{os.environ['IG_USER_ID']}/media",
               {"fields": "id,caption,media_product_type,timestamp", "limit": "50"}):
    print(m["id"], m.get("media_product_type"), m.get("timestamp"))
```

## 8. Publishing

Requires: `instagram_basic` + `instagram_content_publish`
(IG Login: `instagram_business_basic` + `instagram_business_content_publish`).

Rules that apply to **every** publish:

1. Assets must be **public HTTPS URLs** Meta's fetcher can reach (no localhost, no
   auth walls, no expiring signed URLs that die mid-processing).
2. **Two steps always**: create container → (video: poll to `FINISHED`) → `media_publish`.
3. Containers expire ~24h unpublished (`EXPIRED` ⇒ recreate, don't retry publish).
4. Quota: capped API publishes per 24h (commonly 25 — read `content_publishing_limit`, §8.8).
5. Only the returned **media ID** works for insights/comments — store both IDs.

### 8.1 Photo (single image)

Step 1 — container:

```bash
curl -X POST "${BASE}/${IG_USER_ID}/media" \
  -d "image_url=https://example.com/photo.jpg" \
  -d "caption=Hello from the API #launch" \
  -d "alt_text=A sunrise over mountains" \
  -d "access_token=${ACCESS_TOKEN}"
# → {"id":"17901234567890123"}
```

Step 2 — publish:

```bash
curl -X POST "${BASE}/${IG_USER_ID}/media_publish" \
  -d "creation_id=17901234567890123" \
  -d "access_token=${ACCESS_TOKEN}"
# → {"id":"17987654321098765"}
```

TypeScript:

```ts
const c = await gpost<{ id: string }>(`/${process.env.IG_USER_ID}/media`,
  { image_url: "https://example.com/photo.jpg", caption: "Hello from the API #launch" });
const pub = await gpost<{ id: string }>(`/${process.env.IG_USER_ID}/media_publish`, { creation_id: c.id });
```

Python:

```python
c = gpost(f"/{os.environ['IG_USER_ID']}/media",
          {"image_url": "https://example.com/photo.jpg", "caption": "Hello from the API #launch"})
pub = gpost(f"/{os.environ['IG_USER_ID']}/media_publish", {"creation_id": c["id"]})
```

Runnable: `examples/publish-photo.ts`, `examples/publish-photo.py`.

### 8.2 Reels (video) — with status polling

Step 1 — container with `media_type=REELS`:

```bash
curl -X POST "${BASE}/${IG_USER_ID}/media" \
  -d "media_type=REELS" \
  -d "video_url=https://example.com/reel.mp4" \
  -d "caption=New reel #reels" \
  -d "share_to_feed=true" \
  -d "access_token=${ACCESS_TOKEN}"
# → {"id":"17901234567890124"}
```

Step 2 — poll until `FINISHED` (video processing is async):

```bash
curl -G "${BASE}/17901234567890124" \
  --data-urlencode "fields=status_code,status" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}"
# → {"id":"17901234567890124","status_code":"IN_PROGRESS"} … eventually FINISHED
```

`status_code`: `IN_PROGRESS` → `FINISHED` → (after publish) `PUBLISHED`;
`ERROR` ⇒ read `status` for the reason (codec, size, URL unreachable) and recreate;
`EXPIRED` ⇒ recreate. Poll every 5–10s, give up after ~10 min.

Step 3 — publish (same `media_publish` call as §8.1).

TypeScript (poll helper):

```ts
async function waitFinished(containerId: string, tries = 120) {
  for (let i = 0; i < tries; i++) {
    const s = await gget<{ status_code: string; status?: string }>(`/${containerId}?fields=status_code,status`);
    if (s.status_code === "FINISHED") return;
    if (s.status_code === "ERROR" || s.status_code === "EXPIRED")
      throw new Error(`container ${s.status_code}: ${s.status ?? "unknown"}`);
    await new Promise(r => setTimeout(r, 5000));
  }
  throw new Error("timed out waiting for FINISHED");
}
```

Python:

```python
import time
def wait_finished(container_id, tries=120):
    for _ in range(tries):
        s = gget(f"/{container_id}", {"fields": "status_code,status"})
        if s["status_code"] == "FINISHED":
            return
        if s["status_code"] in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"container {s['status_code']}: {s.get('status', 'unknown')}")
        time.sleep(5)
    raise TimeoutError("timed out waiting for FINISHED")
```

Runnable: `examples/publish-reel.ts`, `examples/publish-reel.py`.
Video constraints (verify current spec): MP4/MOV, H.264, AAC, aspect ratios per Reel spec,
size/duration caps — `ERROR` status names the violation.

### 8.3 Carousel (album)

Three phases — item containers, parent container, publish:

```bash
# 1) One container per item (up to 10; images and videos can mix per current spec)
curl -X POST "${BASE}/${IG_USER_ID}/media" \
  -d "image_url=https://example.com/1.jpg" -d "is_carousel_item=true" \
  -d "access_token=${ACCESS_TOKEN}"   # → {"id":"C1"}
curl -X POST "${BASE}/${IG_USER_ID}/media" \
  -d "image_url=https://example.com/2.jpg" -d "is_carousel_item=true" \
  -d "access_token=${ACCESS_TOKEN}"   # → {"id":"C2"}

# 2) Parent container
curl -X POST "${BASE}/${IG_USER_ID}/media" \
  -d "media_type=CAROUSEL" -d "children=C1,C2" \
  -d "caption=Swipe through #carousel" \
  -d "access_token=${ACCESS_TOKEN}"   # → {"id":"PARENT"}

# 3) Publish the PARENT id
curl -X POST "${BASE}/${IG_USER_ID}/media_publish" \
  -d "creation_id=PARENT" -d "access_token=${ACCESS_TOKEN}"
```

Video carousel items must reach `FINISHED` before the parent publish. Publish only the
parent — publishing a child fails.

### 8.4 Stories (image/video)

```bash
curl -X POST "${BASE}/${IG_USER_ID}/media" \
  -d "media_type=STORIES" \
  -d "image_url=https://example.com/story.jpg" \
  -d "access_token=${ACCESS_TOKEN}"
# → {"id":"STORY_CONTAINER"} → media_publish as usual
```

Video stories use `video_url` + `media_type=STORIES` and need `FINISHED` first.
Interactive stickers (polls/links) are generally **not** settable via API — publish the
flat asset.

### 8.5 Update published media (caption)

```bash
# Update caption / alt text on a PUBLISHED media id (not a container id)
curl -X POST "${BASE}/${MEDIA_ID}" \
  -d "caption=Edited caption #update" \
  -d "access_token=${ACCESS_TOKEN}"
# → {"success": true}
```

Only whitelisted fields are mutable (caption, alt text where supported). Media bytes,
product type, and timestamps are immutable — delete + republish to change those.

### 8.6 Delete published media

```bash
curl -X DELETE "${BASE}/${MEDIA_ID}?access_token=${ACCESS_TOKEN}"
# → {"success": true}
```

Deletion is permanent and immediate. There is no trash/restore via API — confirm UX-side.

### 8.7 Enable/disable comments on media

```bash
curl -X POST "${BASE}/${MEDIA_ID}" \
  -d "comment_enabled=false" -d "access_token=${ACCESS_TOKEN}"
```

### 8.8 Check publishing quota — `GET /{ig-user-id}/content_publishing_limit`

```bash
curl -G "${BASE}/${IG_USER_ID}/content_publishing_limit" \
  --data-urlencode "fields=quota_usage,rate_limit_settings,config" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}"
```

```json
{ "data": [{ "quota_usage": 7, "rate_limit_settings": [{"limit": 25, "time_duration": 86400}],
  "config": { "quota_total": 25, "quota_duration": 86400 } }] }
```

Check before queueing scheduled posts; surface `quota_total - quota_usage` in scheduler UIs.

### 8.9 Agent rules for publishing

- URL-encode captions (`#` → `%23` in raw form posts; SDK/form encoders handle this).
- Never `media_publish` before video `FINISHED`; never publish a carousel child.
- Store `{container_id, media_id, permalink, timestamp}` per post.
- Scheduler pattern: queue → at fire time check quota → create → poll → publish →
  verify via `GET /{media-id}` → record permalink. Retry transient errors (§15), re-auth
  on 190, recreate on `EXPIRED`.

## 9. Hashtags and Business Discovery

Requires: `instagram_basic` (+ `instagram_manage_insights` for discovered-media insights).

### 9.1 Hashtag search — `GET /ig_hashtag_search`

Resolve a tag name to a hashtag ID (scoped to the querying user):

```bash
curl -G "${BASE}/ig_hashtag_search" \
  --data-urlencode "user_id=${IG_USER_ID}" \
  --data-urlencode "q=paris2026" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}"
# → {"data": [{"id": "178415…", "name": "paris2026"}]}
```

TypeScript / Python:

```ts
const tags = await gget<{ data: { id: string; name: string }[] }>(`/ig_hashtag_search?user_id=${process.env.IG_USER_ID}&q=paris2026`);
```

```python
tags = gget("/ig_hashtag_search", {"user_id": os.environ["IG_USER_ID"], "q": "paris2026"})
tag_id = tags["data"][0]["id"]
```

### 9.2 Top / recent hashtag media — `GET /{hashtag-id}/{top_media|recent_media}`

```bash
curl -G "${BASE}/${HASHTAG_ID}/recent_media" \
  --data-urlencode "user_id=${IG_USER_ID}" \
  --data-urlencode "fields=id,caption,media_type,permalink,timestamp,like_count,comments_count" \
  --data-urlencode "limit=25" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}"
```

`top_media` needs no extra params beyond `user_id`+`fields`. Only public media on
Business/Creator accounts is returned. Paginate via `paging.next`. Use for UGC discovery,
contest entries, and trend boards (§17).

### 9.3 Business Discovery — `GET /{ig-user-id}?fields=business_discovery…`

Look up another professional account's public profile + media without their token:

```bash
curl -G "${BASE}/${IG_USER_ID}" \
  --data-urlencode "fields=business_discovery.username(targetbrand){id,username,media_count,followers_count,media.limit(10){id,caption,like_count,comments_count,timestamp}}" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}"
```

Target must be Business/Creator and public-ish; personal/private accounts return errors.
Rate-limit this edge aggressively — it is the classic quota burner for competitor trackers.

## 10. Comments and moderation

Requires: `instagram_manage_comments` (+ `instagram_basic`).

### 10.1 List comments — `GET /{media-id}/comments`

```bash
curl -G "${BASE}/${MEDIA_ID}/comments" \
  --data-urlencode "fields=id,text,username,timestamp,like_count,hidden,replies{id,text,username,timestamp}" \
  --data-urlencode "limit=50" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}"
```

```json
{ "data": [{ "id": "178700001", "text": "Love this!", "username": "fan",
  "timestamp": "2026-10-13T10:00:00+0000", "like_count": 3, "hidden": false }] }
```

### 10.2 Reply — `POST /{comment-id}/replies`

```bash
curl -X POST "${BASE}/${COMMENT_ID}/replies" \
  -d "message=Thanks! More coming Friday." \
  -d "access_token=${ACCESS_TOKEN}"
# → {"id":"178700002"}
```

TypeScript / Python + list replies:

```ts
const reply = await gpost<{ id: string }>(`/${commentId}/replies`, { message: "Thanks! More coming Friday." });
const replies = await gget<CommentList>(`/${commentId}/replies?fields=id,text,username`);
```

```python
reply = gpost(f"/{comment_id}/replies", {"message": "Thanks! More coming Friday."})
replies = gget(f"/{comment_id}/replies", {"fields": "id,text,username"})
```

Runnable: `examples/reply-to-comment.ts`, `examples/reply-to-comment.py`.

### 10.3 Hide / unhide — `POST /{comment-id}` with `hide`

```bash
curl -X POST "${BASE}/${COMMENT_ID}" -d "hide=true" -d "access_token=${ACCESS_TOKEN}"
# unhide: hide=false
```

Hidden comments are invisible publicly but recoverable — prefer hide over delete when an
audit trail matters. Response: `{"success": true}`.

### 10.4 Delete — `DELETE /{comment-id}`

```bash
curl -X DELETE "${BASE}/${COMMENT_ID}?access_token=${ACCESS_TOKEN}"
# → {"success": true}
```

Only comments the authorized account can moderate (e.g. on its own media). Permanent.

### 10.5 Block / unblock an account — `POST /{ig-user-id}/block`

```bash
curl -X POST "${BASE}/${IG_USER_ID}/block" \
  -d "block_user_id=${OFFENDING_IGSID_OR_ID}" -d "access_token=${ACCESS_TOKEN}"
# unblock: POST /{ig-user-id}/unblock with the same param
```

Confirm the exact param name (`block_user_id` vs `user_id`) against your version's
reference — it has varied. Gate this behind human approval in automation.

### 10.6 Moderation patterns for agents

- **Keyword auto-hide**: webhook `comments` → match blocklist → `hide=true` → log. Keep a
  human allowlist and an unhide path; never auto-delete on first match.
- **Bulk triage**: `pages()` over recent media → comments → score (toxicity/LLM) →
  queue hide/delete/block actions with per-action approval levels.
- **Rate discipline**: batch reads, serialize writes, sleep between deletes; comment
  writes are throttled harder than reads (§15).

## 11. Insights and analytics

Requires: `instagram_manage_insights` (IG Login: `instagram_business_manage_insights`).

Metric names are **versioned** — a metric valid on v25 may not exist on v26 and vice
versa. **One invalid metric fails the whole call** (error 100): on failure, bisect the
metric list. `values[].value` may be a number **or an object** (breakdown) — parse
defensively. Cache daily rows; history rarely changes after ~48h.

### 11.1 Account insights — `GET /{ig-user-id}/insights`

```bash
curl -G "${BASE}/${IG_USER_ID}/insights" \
  --data-urlencode "metric=reach,impressions,profile_views,website_clicks,accounts_engaged,total_interactions" \
  --data-urlencode "period=day" \
  --data-urlencode "since=1759276800" \
  --data-urlencode "until=1759968000" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}"
```

```json
{ "data": [
  { "name": "reach", "period": "day", "id": "178414…/insights/reach/day",
    "values": [{ "value": 1204, "end_time": "2026-10-13T07:00:00+0000" }] } ] }
```

Periods: `day`, `week`, `days_28` depending on metric; `follower_count`-style metrics use
their own period semantics — request them separately. `since`/`until` are Unix seconds,
aligned to full days.

### 11.2 Media insights — `GET /{media-id}/insights`

```bash
curl -G "${BASE}/${MEDIA_ID}/insights" \
  --data-urlencode "metric=reach,impressions,engagement,saved,shares,total_interactions,likes,comments" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}"
```

Valid metrics depend on `media_product_type` (feed vs Reels vs Story). Reels add
plays/watch-time style metrics where supported (e.g. `plays`, average-watch-time variants
— confirm names on your version). No `period` param on media insights.

Runnable: `examples/fetch-insights.ts`, `examples/fetch-insights.py`.

### 11.3 Common metrics (verify per version)

| Surface | Metrics to try first |
|---|---|
| Account | `impressions`, `reach`, `profile_views`, `website_clicks`, `accounts_engaged`, `total_interactions`, `follower_count` |
| Feed media | `impressions`, `reach`, `engagement`, `saved`, `shares`, `total_interactions`, `likes`, `comments` |
| Reels | feed metrics + `plays` and watch-time metrics where exposed |
| Stories | `reach`, `replies`, `taps_forward`, `taps_back`, `exits`, `impressions` |

### 11.4 Story insights

Stories expire in 24h — pipeline: `GET /{ig-user-id}/stories` → for each id
`GET /{story-id}/insights?metric=reach,replies,taps_forward,taps_back,exits` → persist
immediately. There is no backfill after expiry.

### 11.5 Audience / demographic breakdowns

Some account metrics return breakdown objects (`value: {"0-17": n, …}` / city / country).
Request audience metrics explicitly per your version's reference, store raw JSON, and
normalize downstream — key sets shift between versions.

TypeScript / Python:

```ts
const resp = await gget<InsightsResponse>(`/${process.env.IG_USER_ID}/insights?metric=reach,impressions,profile_views&period=day&since=${since}&until=${until}`);
for (const m of resp.data) for (const v of m.values) console.log(m.name, v.end_time, JSON.stringify(v.value));
```

```python
resp = gget(f"/{os.environ['IG_USER_ID']}/insights",
            {"metric": "reach,impressions,profile_views", "period": "day",
             "since": str(since), "until": str(until)})
for m in resp["data"]:
    for v in m["values"]:
        print(m["name"], v.get("end_time"), v["value"])
```

## 12. Messaging (DMs)

Requires: `instagram_manage_messages` (+ `instagram_basic`, Page-linked account for FB Login flavor).

Mental model: the IG account can **reply** to users who messaged it. Recipients are
**IGSIDs from webhooks** (§13) — there is no username→IGSID lookup and no cold outreach.

### 12.1 The 24-hour window

- Inside 24h of the user's last message: free-form replies, `messaging_type: RESPONSE`.
- Outside 24h: only tagged/policy messages where approved
  (`messaging_type: MESSAGE_TAG` + allowed tag such as `HUMAN_AGENT` for human support
  within 7 days). Misuse restricts the account — when in doubt, wait for the user.
- `messaging_type: UPDATE` covers proactive policy-approved updates where Meta allows them.

### 12.2 Send text — `POST /{ig-user-id}/messages`

```bash
curl -X POST "${BASE}/${IG_USER_ID}/messages" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -d '{
    "recipient": { "id": "IGSID_FROM_WEBHOOK" },
    "messaging_type": "RESPONSE",
    "message": { "text": "Hi! Your order ships Friday." }
  }'
# → {"recipient_id":"IGSID…","message_id":"m_abc123"}
```

TypeScript / Python:

```ts
const res = await fetch(`${BASE}/${process.env.IG_USER_ID}/messages`, {
  method: "POST",
  headers: { "Content-Type": "application/json", Authorization: `Bearer ${TOKEN}` },
  body: JSON.stringify({ recipient: { id: igsid }, messaging_type: "RESPONSE",
    message: { text: "Hi! Your order ships Friday." } }),
});
```

```python
r = requests.post(f"{BASE}/{os.environ['IG_USER_ID']}/messages",
    headers={"Authorization": f"Bearer {TOKEN}"},
    json={"recipient": {"id": igsid}, "messaging_type": "RESPONSE",
          "message": {"text": "Hi! Your order ships Friday."}}, timeout=30)
mid = r.json()["message_id"]
```

### 12.3 Send media / attachment

```json
{ "recipient": { "id": "IGSID…" }, "messaging_type": "RESPONSE",
  "message": { "attachment": { "type": "image",
    "payload": { "url": "https://example.com/ship.jpg", "is_reusable": true } } } }
```

`is_reusable` returns an `attachment_id` for repeat sends. Confirm supported
`type` values (image/video/audio/file, templates) on your version.

### 12.4 Message tags (outside the window)

```json
{ "recipient": { "id": "IGSID…" }, "messaging_type": "MESSAGE_TAG",
  "tag": "HUMAN_AGENT", "message": { "text": "Following up on your ticket…" } }
```

Only with approval for that tag; log every tagged send for audit.

### 12.5 Conversations — `GET /{ig-user-id}/conversations`

```bash
curl -G "${BASE}/${IG_USER_ID}/conversations" \
  --data-urlencode "platform=instagram" \
  --data-urlencode "fields=id,participants,updated_time" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}"

# Messages in one conversation:
curl -G "${BASE}/${CONVERSATION_ID}" \
  --data-urlencode "fields=messages{id,message,from,created_time}" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}"
```

### 12.6 Agent rules for messaging

- Reply to the webhook IGSID, never a username; store `message_id` per send.
- Dedupe inbound `mid` — webhooks retry and double-deliver.
- Human handoff: bot answers inside 24h → escalate with `HUMAN_AGENT` tag or hand to an
  agent inbox; log transcripts per conversation.
- Never build spam/cold-DM flows — accounts get restricted and apps fail Review.

## 13. Webhooks

Webhooks push comments, messages, mentions, and story events to your HTTPS endpoint.
Prefer them over polling everywhere.

### 13.1 Setup

1. Meta app dashboard → **Webhooks** product → Callback URL
   (`https://<host>/webhooks/instagram`) + Verify Token (a secret you invent).
2. Subscribe the app to Instagram object fields:
   `comments`, `messages`, `messaging_postbacks`, `messaging_seen`, `messaging_referrals`,
   `mentions`, `story_insights`, `live_comments` (pick what you consume).
3. Subscribe each account: `POST /{page-id}/subscribed_apps?subscribed_fields=…`
   with a Page token (FB Login flavor), or the dashboard per-object subscription.
   Re-subscribe after token/app changes; when events stop, check subscription state first.
4. Implement verification (§13.2) + signature validation (§13.3) before subscribing.

### 13.2 Verification (GET — return `hub.challenge` verbatim)

Meta calls `GET {callback}?hub.mode=subscribe&hub.verify_token=…&hub.challenge=…`.
Return HTTP 200 + challenge **as plain text** only when mode/token match, else 403.

TypeScript (Express):

```ts
app.get("/webhooks/instagram", (req, res) => {
  const { "hub.mode": mode, "hub.verify_token": token, "hub.challenge": challenge } = req.query;
  if (mode === "subscribe" && token === process.env.WEBHOOK_VERIFY_TOKEN && typeof challenge === "string")
    return res.status(200).send(challenge);
  return res.sendStatus(403);
});
```

Python (stdlib, no framework):

```python
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import os

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        q = parse_qs(urlparse(self.path).query)
        if (q.get("hub.mode", [""])[0] == "subscribe"
                and q.get("hub.verify_token", [""])[0] == os.environ["WEBHOOK_VERIFY_TOKEN"]):
            body = q.get("hub.challenge", [""])[0].encode()
            self.send_response(200); self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body))); self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(403); self.end_headers()
```

Runnable: `examples/webhook-handler.ts`, `examples/webhook-handler.py`.

### 13.3 Signature validation (POST — every event)

Meta signs the raw body with your App Secret in `X-Hub-Signature-256: sha256=<hex>`.
**Validate before trusting anything.** Acknowledge 200 immediately, process async.

TypeScript:

```ts
import { createHmac, timingSafeEqual } from "crypto";
function validSignature(rawBody: Buffer, header: string | undefined, appSecret: string): boolean {
  if (!header?.startsWith("sha256=")) return false;
  const expected = createHmac("sha256", appSecret).update(rawBody).digest();
  const got = Buffer.from(header.slice(7), "hex");
  return got.length === expected.length && timingSafeEqual(got, expected);
}
```

Python:

```python
import hashlib, hmac
def valid_signature(raw: bytes, header: str, app_secret: str) -> bool:
    if not header.startswith("sha256="):
        return False
    expected = hmac.new(app_secret.encode(), raw, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, header.removeprefix("sha256="))
```

### 13.4 Event payload catalog

Comment event (`changes[]`):

```json
{ "object": "instagram", "entry": [{
  "id": "17841400008460056", "time": 1720000000,
  "changes": [{ "field": "comments",
    "value": { "id": "178700001", "text": "Love this!",
      "from": { "id": "98765", "username": "fan" },
      "media": { "id": "17987654321098765", "media_product_type": "FEED" } } }] }]}
```

Message event (`messaging[]` — `sender.id` is the IGSID to reply to):

```json
{ "object": "instagram", "entry": [{
  "id": "17841400008460056", "time": 1720000000,
  "messaging": [{ "sender": { "id": "IGSID…" }, "recipient": { "id": "178414…" },
    "timestamp": 1720000000000,
    "message": { "mid": "m_abc123", "text": "Do you ship to Berlin?" } }] }]}
```

Mention/tag events use the `changes[]` shape with `field: "mentions"` (or `live_comments`
for Live). IG Login flavor: content events are flat `field`/`value`; DMs still arrive as
`messaging[]`. Normalize both shapes in one parser keyed on `entry[].changes` vs
`entry[].messaging`.

### 13.5 Subscription management

```bash
# Subscribe a Page's app (FB Login flavor)
curl -X POST "${BASE}/${PAGE_ID}/subscribed_apps" \
  -d "subscribed_fields=comments,messages,mentions" \
  -d "access_token=${PAGE_TOKEN}"

# List subscriptions (app token: APP_ID|APP_SECRET)
curl -G "${BASE}/${APP_ID}/subscriptions" \
  --data-urlencode "access_token=${APP_ID}|${APP_SECRET}"
```

### 13.6 Agent rules for webhooks

- 200 fast (<1s), enqueue, process async — non-200 triggers retries ⇒ duplicates.
- Dedupe by comment ID / message `mid` / `(field, value.id)` with a seen-set (Redis/DB).
- Never process unsigned bodies; rotate App Secret + verify token via config, not code.
- Log full raw bodies (redacting tokens) for replay during development.

## 14. Mentions and tags

### 14.1 Caption mentions — `GET /{ig-user-id}/mentioned_media`

Media where the account was @-mentioned in someone else's caption:

```bash
curl -G "${BASE}/${IG_USER_ID}/mentioned_media" \
  --data-urlencode "fields=id,caption,permalink,username,timestamp" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}"
```

### 14.2 Tags — `GET /{ig-user-id}/tags`

Media where the account was tagged (photo tag):

```bash
curl -G "${BASE}/${IG_USER_ID}/tags" \
  --data-urlencode "fields=id,caption,media_type,permalink" \
  --data-urlencode "limit=25" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}"
```

Note: `/tags` behavior differs between flavors — the Facebook Login flavor is the
reliable one for tagged-media access; verify the Instagram Login behavior on your
version before building UGC flows on it. Pair with `mentions` webhooks (§13) for
real-time capture, and see the UGC repost recipe (§17.4).

## 15. Errors, rate limits, retries

### 15.1 Error shape (always the same)

```json
{ "error": { "message": "(#190) Error validating access token",
  "type": "OAuthException", "code": 190, "error_subcode": 463, "fbtrace_id": "AbC123" } }
```

Always log `code` + `error_subcode` + `fbtrace_id`. The `message` prefix `(#code)` is
parseable but prefer the numeric fields.

### 15.2 Code table → agent action

| Code | Meaning | Action |
|---|---|---|
| 190 | Token expired/invalid/revoked | **Re-auth** (restart OAuth/refresh). Never blind-retry. Mark connection `needs_reauth`. |
| 10 / 200 | Permission missing / not approved | Request scope; check App Review; re-authorize (old tokens lack new scopes); verify `debug_token`. |
| 100 | Invalid parameter (field/metric/ID) | Fix request. Bisect `fields`/metric lists; check ID belongs to this account/version. |
| 4 | App-level rate limit | Back off globally; batch + cache; shed non-critical traffic. |
| 17 | User-level rate limit | Slow per-account calls; per-account queue with leaky bucket. |
| 32 | Page-level rate limit | Serialize Page-token calls; spread across time. |
| 613 | Custom throttling (e.g. publishing quota) | Respect quota; check `content_publishing_limit`; retry after window. |
| 368 | Temporarily blocked for policy violation | Stop the offending action type; human review; appeal if needed. |
| 1 / 2 | Transient API error / service down | Retry with backoff. |
| HTTP 5xx | Server-side failure | Retry with backoff. |
| HTTP 429 | Explicit throttle | Honor `Retry-After`, then backoff. |

### 15.3 Retry policy (implement once, use everywhere)

- Retry **only** transient failures: codes 1, 2, 4, 17, 32, HTTP 5xx/429.
- Backoff: 1s → 2s → 4s → 8s → 16s, + jitter, max 5 attempts, honor `Retry-After`.
- Never retry 190/10/100/368 without changing credentials/request/behavior.
- Poll video containers every 5–10s (§8.2), not in tight loops.
- Watch `X-*-Usage` headers (§5.5); throttle past ~70% before Meta throttles you.

TypeScript:

```ts
const RETRYABLE = new Set([1, 2, 4, 17, 32]);
export async function withRetry<T>(fn: () => Promise<T>, tries = 5): Promise<T> {
  let delay = 1000;
  for (let i = 0; ; i++) {
    try { return await fn(); }
    catch (e: unknown) {
      const code = (e as { code?: number })?.code;
      if (i >= tries - 1 || (code !== undefined && !RETRYABLE.has(code))) throw e;
      await new Promise(r => setTimeout(r, delay + Math.random() * 250));
      delay *= 2;
    }
  }
}
```

Python:

```python
import random, time
RETRYABLE = {1, 2, 4, 17, 32}
def with_retry(fn, tries=5):
    delay = 1.0
    for i in range(tries):
        try:
            return fn()
        except RuntimeError as e:
            if i == tries - 1:
                raise
            time.sleep(delay + random.uniform(0, 0.25))
            delay *= 2
```

## 16. Permissions, App Review, going live

### 16.1 Permission matrix (both flavors)

| Capability | FB Login scope | IG Login scope |
|---|---|---|
| Profile + media read | `instagram_basic` | `instagram_business_basic` |
| Publish / update / delete media | `instagram_content_publish` | `instagram_business_content_publish` |
| Comments read/reply/hide/delete | `instagram_manage_comments` | `instagram_business_manage_comments` |
| Account + media insights | `instagram_manage_insights` | `instagram_business_manage_insights` |
| Messaging | `instagram_manage_messages` | `instagram_business_manage_messages` |
| List user's Pages | `pages_show_list` | — (no Pages) |
| Read Page / linked IG | `pages_read_engagement` | — |
| Business assets | `business_management` | — |

Scope names drift across versions — treat this table as a starting map and confirm in
the permission reference for your `GRAPH_VERSION`. Request least privilege; every scope
beyond basic typically needs App Review for non-role users.

### 16.2 App Review checklist

- [ ] Each scope has an in-product use case + screencast showing the OAuth grant and feature
- [ ] Test credentials / test IG account for reviewers + step-by-step repro
- [ ] Privacy Policy URL, Data Deletion callback implemented, deauthorize handling
- [ ] Business verification completed if required for your scopes
- [ ] Development-mode testing done with role-holding accounts first

### 16.3 Going live

1. Pin `GRAPH_VERSION`; run the full flow matrix (auth → read → publish → insights →
   comments → messaging → webhooks) against a test account.
2. Verify `debug_token` scopes, quota, webhook delivery, and the 190 re-auth path.
3. Submit App Review; keep Development-mode behavior identical to production code paths.
4. After approval: onboard real users, monitor `X-*-Usage` headers + error-code dashboard
   (alert on 190 spikes = systemic token issue; 4/17/32 = scale issue).
5. Track the changelog quarterly; migrate before your version's deprecation date.

## 17. Agent build recipes (extend Instagram)

Each recipe lists the endpoint map + key files. Build in this order: webhook receiver →
read path → write path → scheduler/queue → UI.

### 17.1 Scheduled-post manager

- Endpoints: `content_publishing_limit`, `POST /media`, `GET /{container-id}`,
  `POST /media_publish`, `GET /{media-id}`, `POST /{media-id}` (caption fix).
- Flow: drag-drop calendar → asset upload to public HTTPS → queue row
  `{fire_at, asset_url, caption, status}` → worker fires (§8.9) → permalink recorded.
- Gotchas: quota (25/24h), container expiry, video `FINISHED` gate, timezone-aware `fire_at`.

### 17.2 Comment auto-moderator

- Endpoints: webhook `comments`, `GET /{media-id}/comments`, `POST /{comment-id}`
  (`hide`), `DELETE /{comment-id}`, `POST /{ig-user-id}/block`.
- Flow: webhook → blocklist/LLM score → `hide=true` + mod queue → human approves
  delete/block. Keep allowlist + unhide path; log every action with actor + reason.

### 17.3 Analytics dashboard + reports

- Endpoints: `GET /{ig-user-id}/insights`, `GET /{media-id}/insights`, `/stories`,
  Business Discovery for competitors (§9.3).
- Flow: nightly ETL (account + per-media + stories-before-expiry) → warehouse →
  engagement-rate, best-time-to-post, follower-growth views → weekly PDF/email digest.
- Gotchas: metric bisect on error 100, breakdown-object parsing, 48h cache rule.

### 17.4 UGC repost pipeline (rights-safe)

- Endpoints: webhook `mentions`, `GET /{ig-user-id}/tags`, `GET /{ig-user-id}/mentioned_media`,
  `GET /{hashtag-id}/recent_media`, publish flow.
- Flow: detect tag/mention/hashtag hit → fetch media + author → DM/email rights request →
  on approval, download bytes, re-host on your CDN, publish with credit caption.
- Never republish without explicit consent; store consent receipts.

### 17.5 DM support chatbot + human handoff

- Endpoints: webhook `messaging`, `POST /{ig-user-id}/messages`, `/conversations`,
  `MESSAGE_TAG` fallback (§12.4).
- Flow: inbound `mid` → dedupe → intent/FAQ bot (RESPONSE, inside 24h) → low-confidence
  → human inbox + `HUMAN_AGENT` follow-up where approved. Persist transcripts per IGSID.

### 17.6 Contest / giveaway engine

- Endpoints: hashtag `recent_media`, `GET /{media-id}/comments`, comment reply, insights.
- Flow: define hashtag + window → collect entries (media + comments) → eligibility filter
  (follower? keyword? tag-a-friend?) → random draw + audit log → announce via publish +
  reply to winners. Export entries CSV for transparency.

### 17.7 Cross-posting bridge

- Flow: source (RSS/YouTube/TikTok/webhook) → normalize to image/video + caption →
  flavor-aware publish (§8) → record `{source_id → media_id, permalink}` mapping →
  reconcile failures with dead-letter queue. Respect per-network rights and quotas.

## 18. FAQ and troubleshooting

**Personal account?** Neither flavor supports personal accounts — switch to Business/Creator.
**`instagram_business_account` missing?** Page↔IG link broken — relink in Page Settings.
**190 on every call?** Token expired/revoked or wrong token type — re-run §4; check flavor/host match.
**Error 10 after granting?** Needs App Review for public use, or token predates the grant — re-authorize, check `debug_token` scopes.
**Publish failed after container?** Video not `FINISHED`, container `EXPIRED` (~24h), or asset URL unfetchable — poll, recreate, check URL.
**Whole insights call fails?** One bad metric — bisect the list (§11).
**Can't DM a follower?** Expected — only webhook IGSIDs within 24h (or approved tag).
**Webhooks silent?** Check subscription state, re-subscribe after token changes, verify callback returns challenge as `text/plain`, confirm App Secret signature path.
**`media_url` 404s?** URLs expire (especially Stories) — re-fetch or cache bytes.
**Which version?** Pin via `GRAPH_VERSION`; this doc's examples use `v25.0`, latest known `v26.0` — confirm in the changelog and migrate before deprecation.
**Which flavor?** New creator apps → Instagram Login; Page-centric management → Facebook Login. Never mix tokens/hosts.

Decision tree for a failing call: **190?** → re-auth · **10/200?** → scope/Review ·
**100?** → bisect fields/metrics/IDs · **4/17/32/613/429/5xx?** → backoff (§15) ·
**else?** → log `code/subcode/fbtrace_id`, check changelog for a behavior change.

---

## Appendix A: Endpoint quick reference

| Method | Path | Purpose | Permission |
|---|---|---|---|
| GET | `/oauth/access_token` | Code/token exchange (§4) | — (app secret) |
| GET | `/debug_token` | Verify token + scopes | app token |
| GET | `/{ig-user-id}` | Profile | basic |
| GET | `/{page-id}?fields=instagram_business_account` | Resolve IG ID | pages_* |
| GET | `/{ig-user-id}/media` | List media | basic |
| GET | `/{media-id}` | Media object | basic |
| GET | `/{media-id}/children` | Carousel children | basic |
| GET | `/{ig-user-id}/stories` | Active stories | basic |
| GET | `/instagram_oembed?url=` | Public embed | varies |
| POST | `/{ig-user-id}/media` | Create container (§8) | content_publish |
| GET | `/{container-id}?fields=status_code` | Poll container | content_publish |
| POST | `/{ig-user-id}/media_publish` | Publish | content_publish |
| POST | `/{media-id}` | Update caption / comment_enabled | content_publish |
| DELETE | `/{media-id}` | Delete media | content_publish |
| GET | `/{ig-user-id}/content_publishing_limit` | Quota | content_publish |
| GET | `/ig_hashtag_search?user_id&q` | Hashtag ID | basic |
| GET | `/{hashtag-id}/top_media`, `/recent_media` | Hashtag media | basic |
| GET | `/{ig-user-id}?fields=business_discovery…` | Competitor lookup | basic |
| GET | `/{media-id}/comments` | List comments | manage_comments |
| POST | `/{comment-id}/replies` | Reply | manage_comments |
| POST | `/{comment-id}` (`hide`) | Hide/unhide | manage_comments |
| DELETE | `/{comment-id}` | Delete comment | manage_comments |
| POST | `/{ig-user-id}/block`, `/unblock` | Block/unblock | manage_comments* |
| GET | `/{ig-user-id}/insights` | Account insights | manage_insights |
| GET | `/{media-id}/insights` | Media insights | manage_insights |
| POST | `/{ig-user-id}/messages` | Send DM | manage_messages |
| GET | `/{ig-user-id}/conversations` | List conversations | manage_messages |
| GET | `/{ig-user-id}/mentioned_media` | Caption mentions | basic* |
| GET | `/{ig-user-id}/tags` | Tagged media | basic* |
| GET/POST | your `/webhooks/instagram` | Verify + events (§13) | — (app secret) |
| POST | `/{page-id}/subscribed_apps` | Subscribe webhooks | pages_* |

`*` Confirm exact scope on your version — Meta has moved a few edges between scopes.

## Appendix B: Companion files in this bundle

- `openapi.yaml` — machine-readable contract (source of truth for paths/schemas).
- `types/instagram-graph.d.ts` — TypeScript types for requests/responses.
- `examples/*.ts`, `examples/*.py` — runnable flows (publish, insights, replies, webhooks).
- `postman/instagram-graph.postman_collection.json` + `bruno/` — runnable request collections.
- `mcp/tools.json` + `mcp/server.py` — MCP starter: 14 callable tools for MCP-capable agents.
- `data/chunks.jsonl` — one RAG chunk per endpoint/topic.
- `llms.txt` / `llms-full.txt` — LLM index + single-file full context.
- `site/` — static multi-page human-readable site (landing, API reference, formats,
  guides; built by `scripts/build-site.py`).
- `FORMATS.md` — why each format exists and when to use it.
- `docs/*.md` — topic guides (kept short; this file is the comprehensive reference).





