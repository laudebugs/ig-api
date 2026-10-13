# Comments & Moderation — Instagram Graph API

> Generated: 2026-10-13 · Base: `https://graph.facebook.com/v21.0` · Requires: `instagram_manage_comments`

## List comments on media

```bash
curl "https://graph.facebook.com/v21.0/17987654321098765/comments?fields=id,text,username,timestamp,like_count,hidden&access_token=EAAB..."
```

```json
{ "data": [{ "id": "178700001", "text": "Love this!", "username": "fan", "timestamp": "2026-10-13T10:00:00+0000", "like_count": 3 }] }
```

## Reply to a comment

```bash
curl -X POST "https://graph.facebook.com/v21.0/178700001/replies" \
  -d "message=Thanks! More coming Friday." \
  -d "access_token=EAAB..."
```

```json
{ "id": "178700002" }
```

Runnable code: [../examples/reply-to-comment.ts](../examples/reply-to-comment.ts). List replies with `GET /{comment-id}/replies`.

## Hide / unhide a comment

```bash
curl -X POST "https://graph.facebook.com/v21.0/178700001" \
  -d "hide=true" \
  -d "access_token=EAAB..."
```

## Delete a comment

Only comments the authorized account can moderate (e.g. comments on its own media, per permission rules):

```bash
curl -X DELETE "https://graph.facebook.com/v21.0/178700001?access_token=EAAB..."
```

```json
{ "success": true }
```

## Mentions

Media where the account was mentioned in a caption:

```bash
curl "https://graph.facebook.com/v21.0/17841400008460056/mentioned_media?fields=id,caption,permalink&access_token=EAAB..."
```

Comment the account was tagged in: `GET /{ig-user-id}/tags`, then act on the returned media/comment IDs per the fields you requested.

## Agent rules

- Reply via `/{comment-id}/replies`, not by posting a new top-level comment.
- Hide before delete when an audit trail matters; hidden comments can be unhidden.
- Webhook `comments` events are faster than polling — see [webhooks.md](webhooks.md).
- Respect rate limits when bulk-moderating; batch reads, serialize writes.

Next: [messaging.md](messaging.md) · [webhooks.md](webhooks.md)
