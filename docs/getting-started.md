# Getting Started — Instagram Graph API

> Generated: 2026-10-13 · Base: `https://graph.facebook.com/v25.0`

## Prerequisites

1. **Instagram Business or Creator account** (personal accounts cannot use this API). Switch in Instagram: Settings → Account type and tools → Switch to professional account.
2. **Facebook Page linked** to that Instagram account (Page Settings → Linked accounts).
3. **Meta app** at developers.facebook.com with the Instagram / Facebook Login product, App ID and App Secret.
4. **Permissions** requested for your use case (see [authentication.md](authentication.md)); development mode only allows accounts with a role on the app until App Review.

## Step 1 — Get a token and the IG User ID

Follow [authentication.md](authentication.md): OAuth → short-lived user token → long-lived token (60 days) → Page access token → `instagram_business_account.id` is your `{ig-user-id}`.

## Step 2 — First request

```bash
curl "https://graph.facebook.com/v25.0/17841400008460056?fields=id,username,media_count&access_token=EAAB..."
```

```json
{ "id": "17841400008460056", "username": "examplebrand", "media_count": 42 }
```

TypeScript:

```ts
const res = await fetch(
  `https://graph.facebook.com/v25.0/${process.env.IG_USER_ID}?fields=id,username,media_count`,
  { headers: { Authorization: `Bearer ${process.env.ACCESS_TOKEN}` } },
);
if (!res.ok) throw new Error(await res.text());
console.log(await res.json());
```

## Step 3 — List recent media

```bash
curl "https://graph.facebook.com/v25.0/17841400008460056/media?fields=id,caption,media_type,permalink,timestamp&limit=5&access_token=EAAB..."
```

Paginate with `paging.cursors.after` → `&after=<cursor>` until no `paging.next`.

## Next

- Publish: [media-publishing.md](media-publishing.md) · Runnable code: [../examples/publish-photo.ts](../examples/publish-photo.ts)
- Measure: [insights.md](insights.md) · Errors: [errors-and-rate-limits.md](errors-and-rate-limits.md)
