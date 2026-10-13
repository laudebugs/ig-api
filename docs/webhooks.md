# Webhooks — Instagram Graph API

> Generated: 2026-10-13 · Base: `https://graph.facebook.com/v21.0`

Webhooks push Instagram events to your HTTPS endpoint. Use them instead of polling for comments, messages, mentions, and story insights.

## Setup

1. In your Meta app dashboard, add the Webhooks product and set a Callback URL (`https://your-app.example.com/webhooks/instagram`) and a Verify Token (a secret string you invent).
2. Subscribe the app to the Instagram object fields you need: `comments`, `messages`, `messaging_postbacks`, `mentions`, `story_insights`, `live_comments`.
3. Subscribe each Page/IG account: `POST /{page-id}/subscribed_apps?subscribed_fields=...` with a Page token, or use the dashboard's per-object subscription.

## Verification (GET)

Meta calls your callback with query params. Return `hub.challenge` verbatim as plain text with HTTP 200 only when the mode and token match:

```ts
// Express-style handler
app.get("/webhooks/instagram", (req, res) => {
  const mode = req.query["hub.mode"];
  const token = req.query["hub.verify_token"];
  const challenge = req.query["hub.challenge"];
  if (mode === "subscribe" && token === process.env.WEBHOOK_VERIFY_TOKEN) {
    return res.status(200).send(challenge);
  }
  return res.sendStatus(403);
});
```

## Events (POST)

Acknowledge with HTTP 200 immediately, then process asynchronously. Validate `X-Hub-Signature-256` against your App Secret before trusting the body.

Comment event:

```json
{
  "object": "instagram",
  "entry": [{
    "id": "17841400008460056",
    "time": 1720000000,
    "changes": [{
      "field": "comments",
      "value": { "id": "178700001", "text": "Love this!", "from": { "id": "98765", "username": "fan" }, "media": { "id": "17987654321098765" } }
    }]
  }]
}
```

Message event (entry uses `messaging[]` with `sender.id` = IGSID, `message.mid`, `message.text`) — see [messaging.md](messaging.md).

## Agent rules

- Respond 200 fast; heavy work goes to a queue. Non-200 responses trigger retries and duplicate events — dedupe by comment ID / message `mid`.
- Verify the signature header on every POST; never process unsigned bodies.
- Re-subscribe after token/app changes; check subscription state when events stop.

Next: [errors-and-rate-limits.md](errors-and-rate-limits.md) · [faq.md](faq.md)
