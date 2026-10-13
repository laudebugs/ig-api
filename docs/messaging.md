# Messaging — Instagram Graph API

> Generated: 2026-10-13 · Base: `https://graph.facebook.com/v21.0` · Requires: `instagram_manage_messages` (+ `instagram_basic`, Page-linked account)

Instagram messaging lets your app send and receive Instagram DMs for a Business/Creator account. The recipient is identified by an IGSID (Instagram-scoped ID) delivered in webhook `messaging` events — you cannot message arbitrary usernames.

## The 24-hour window

- You may send free-form replies within 24 hours of the user's last message (`messaging_type: RESPONSE`).
- Outside the window, use `messaging_type: MESSAGE_TAG` with an allowed tag (e.g. `HUMAN_AGENT` where approved for human support within 7 days). Policy violations get accounts restricted; when in doubt, wait for the user to message again.

## Send a text message

```bash
curl -X POST "https://graph.facebook.com/v21.0/17841400008460056/messages" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer EAAB..." \
  -d '{
    "recipient": { "id": "IGSID_FROM_WEBHOOK" },
    "messaging_type": "RESPONSE",
    "message": { "text": "Hi! Your order ships Friday." }
  }'
```

```json
{ "recipient_id": "IGSID_FROM_WEBHOOK", "message_id": "m_abc123" }
```

## Receive messages

Subscribe to the `messages` webhook field (see [webhooks.md](webhooks.md)). Each event gives `sender.id` (the IGSID to reply to), `message.text`, and `message.mid`.

## Read conversations (optional)

```bash
curl "https://graph.facebook.com/v21.0/17841400008460056/conversations?platform=instagram&fields=id,participants,updated_time&access_token=EAAB..."
curl "https://graph.facebook.com/v21.0/{conversation-id}?fields=messages{id,message,from,created_time}&access_token=EAAB..."
```

## Agent rules

- Always reply to the IGSID from the webhook, never to a username.
- Dedupe inbound `mid` values; webhooks retry.
- Store `message_id` from the send response for support/debugging.
- Handle the `HUMAN_AGENT` tag only if your app is approved for it.

Next: [webhooks.md](webhooks.md) · [errors-and-rate-limits.md](errors-and-rate-limits.md)
