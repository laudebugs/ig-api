# Authentication — Instagram Graph API

> Generated: 2026-10-13 · Base: `https://graph.facebook.com/v25.0`

This guide covers the Instagram Graph API via Facebook Login. The newer Instagram Platform API (Instagram Login, `graph.instagram.com`) uses a different OAuth host and token flow; do not mix the two.

## Flow overview

1. User authorizes your app via Facebook Login → authorization code.
2. Exchange code for a short-lived user access token (~1 hour).
3. Exchange short-lived token for a long-lived user token (~60 days).
4. List the user's Pages, derive a Page access token.
5. Read `instagram_business_account.id` from the Page — that is `{ig-user-id}` for all Instagram calls.

## Permissions

| Permission | Unlocks |
|---|---|
| `instagram_basic` | Profile and media read |
| `instagram_content_publish` | Media containers and publishing |
| `instagram_manage_comments` | Comment read, reply, hide, delete |
| `instagram_manage_insights` | Account and media insights |
| `instagram_manage_messages` | Instagram messaging |
| `pages_show_list` | List Pages the user manages |
| `pages_read_engagement` | Read Page / linked IG account |
| `business_management` | Business-owned accounts and assets |

Request only what you need; each permission may require App Review for public use. In Development mode, only users with a role on the Meta app can authorize.

## Step 1 — Dialog redirect

```text
https://www.facebook.com/v25.0/dialog/oauth?client_id={app-id}&redirect_uri={redirect-uri}&scope=instagram_basic,instagram_content_publish,pages_show_list,pages_read_engagement&response_type=code
```

On success the browser returns to `{redirect-uri}?code={code}`.

## Step 2 — Code → short-lived token

```bash
curl -X GET "https://graph.facebook.com/v25.0/oauth/access_token?client_id={app-id}&client_secret={app-secret}&redirect_uri={redirect-uri}&code={code}"
```

```json
{ "access_token": "EAABshort...", "token_type": "bearer", "expires_in": 3600 }
```

## Step 3 — Short-lived → long-lived token (60 days)

```bash
curl -X GET "https://graph.facebook.com/v25.0/oauth/access_token?grant_type=fb_exchange_token&client_id={app-id}&client_secret={app-secret}&fb_exchange_token={short-lived-token}"
```

Store the long-lived user token server-side only. Refresh it before expiry by repeating this exchange with a still-valid long-lived token.

## Step 4 — Pages and Page access token

```bash
curl "https://graph.facebook.com/v25.0/me/accounts?fields=id,name,access_token,instagram_business_account{id,username}&access_token={long-lived-user-token}"
```

```json
{
  "data": [{
    "id": "109876543210",
    "name": "Example Page",
    "access_token": "EAABpage...",
    "instagram_business_account": { "id": "17841400008460056", "username": "examplebrand" }
  }]
}
```

Use the Page `access_token` for Instagram calls. A Page token derived from a long-lived user token does not expire unless the user changes their password, revokes the app, or the token is invalidated (error 190).

## Step 5 — Verify

```bash
curl "https://graph.facebook.com/v25.0/debug_token?input_token={page-token}&access_token={app-id}|{app-secret}"
```

Check `is_valid`, `expires_at`, and `scopes` in the response before calling the API.

## Agent rules

- Never embed tokens in client apps, repos, or prompts; load from env/secret store.
- On error 190, restart at Step 1 or 3; do not retry the same call.
- Keep `GRAPH_VERSION` configurable; Meta deprecates versions on a schedule.

Next: [media-publishing.md](media-publishing.md) · Errors: [errors-and-rate-limits.md](errors-and-rate-limits.md)
