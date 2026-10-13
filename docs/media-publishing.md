# Media Publishing — Instagram Graph API

> Generated: 2026-10-13 · Base: `https://graph.facebook.com/v21.0` · Requires: `instagram_basic` + `instagram_content_publish`

Publishing is always two steps: create a container, then publish it. Media must be hosted at a public HTTPS URL the Graph API can fetch (no localhost, no auth-walled URLs). Unpublished containers expire after about 24 hours.

## Single photo

Step 1 — create container:

```bash
curl -X POST "https://graph.facebook.com/v21.0/17841400008460056/media" \
  -d "image_url=https://example.com/photo.jpg" \
  -d "caption=Hello from the API %23launch" \
  -d "access_token=EAAB..."
```

```json
{ "id": "17901234567890123" }
```

Step 2 — publish:

```bash
curl -X POST "https://graph.facebook.com/v21.0/17841400008460056/media_publish" \
  -d "creation_id=17901234567890123" \
  -d "access_token=EAAB..."
```

```json
{ "id": "17987654321098765" }
```

The returned `id` is the published media ID. Runnable code: [../examples/publish-photo.ts](../examples/publish-photo.ts).

## Reel (video)

Step 1 with `media_type=REELS` and `video_url`, then poll the container until `FINISHED` before publishing:

```bash
curl -X POST "https://graph.facebook.com/v21.0/17841400008460056/media" \
  -d "media_type=REELS" \
  -d "video_url=https://example.com/reel.mp4" \
  -d "caption=New reel" \
  -d "share_to_feed=true" \
  -d "access_token=EAAB..."

curl "https://graph.facebook.com/v21.0/17901234567890123?fields=status_code,status&access_token=EAAB..."
```

```json
{ "status_code": "FINISHED", "id": "17901234567890123" }
```

Poll every 5–10 seconds; if `status_code` is `ERROR`, read `status` and fix the asset (format, size, URL reachability). Runnable code: [../examples/publish-reel.ts](../examples/publish-reel.ts).

## Carousel

1. Create one container per item with `is_carousel_item=true` (image or video URL each).
2. Create a parent container with `media_type=CAROUSEL` and `children={id1},{id2},...` plus `caption`.
3. Publish the parent container ID with `media_publish`.

## Check publishing limit

```bash
curl "https://graph.facebook.com/v21.0/17841400008460056/content_publishing_limit?fields=quota_usage,rate_limit_settings&access_token=EAAB..."
```

Accounts are limited to a capped number of published API posts per 24 hours (commonly 25; read the response for your account). Also see [errors-and-rate-limits.md](errors-and-rate-limits.md).

## Read back the post

```bash
curl "https://graph.facebook.com/v21.0/17987654321098765?fields=id,caption,media_type,media_product_type,permalink,timestamp,like_count,comments_count&access_token=EAAB..."
```

## Agent rules

- URL-encode `caption` (hashtags as `%23` in form posts, or use a proper form encoder).
- Never call `media_publish` before a video container is `FINISHED`.
- Store both container ID and media ID; only the media ID works for insights/comments.
- On container `EXPIRED`, recreate the container; do not retry publish.

Next: [insights.md](insights.md) · [comments-moderation.md](comments-moderation.md)
