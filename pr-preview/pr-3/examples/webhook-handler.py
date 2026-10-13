"""Instagram webhook receiver: verification (GET) + signed event intake (POST).
Generated: 2026-10-13
Env: PORT (default 3000), WEBHOOK_VERIFY_TOKEN, APP_SECRET
Run: python webhook-handler.py  (expose via ngrok/cloudflared for Meta to reach it)

Stdlib only — no framework dependency.
"""
import hashlib
import hmac
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

VERIFY_TOKEN = os.environ.get("WEBHOOK_VERIFY_TOKEN", "")
APP_SECRET = os.environ.get("APP_SECRET", "")
SEEN = set()  # replace with Redis/DB in production


def valid_signature(raw: bytes, header: str) -> bool:
    if not header.startswith("sha256=") or not APP_SECRET:
        return False
    expected = hmac.new(APP_SECRET.encode(), raw, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, header.removeprefix("sha256="))


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        url = urlparse(self.path)
        if url.path != "/webhooks/instagram":
            return self.send_response(404), self.end_headers()
        q = parse_qs(url.query)
        if (q.get("hub.mode", [""])[0] == "subscribe"
                and q.get("hub.verify_token", [""])[0] == VERIFY_TOKEN
                and VERIFY_TOKEN):
            body = q.get("hub.challenge", [""])[0].encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(403)
            self.end_headers()

    def do_POST(self):
        url = urlparse(self.path)
        if url.path != "/webhooks/instagram":
            return self.send_response(404), self.end_headers()
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length)
        if not valid_signature(raw, self.headers.get("X-Hub-Signature-256", "")):
            self.send_response(401)
            return self.end_headers()
        self.send_response(200)  # ack fast, process async
        self.end_headers()
        try:
            body = json.loads(raw.decode("utf-8"))
        except ValueError as e:
            print("bad webhook body:", e)
            return
        for entry in body.get("entry", []):
            for change in entry.get("changes", []) or []:
                key = f"{change.get('field')}:{(change.get('value') or {}).get('id')}"
                if key in SEEN:
                    continue
                SEEN.add(key)
                print("change:", change.get("field"), json.dumps(change.get("value")))
                # TODO: enqueue -> hide/comment-reply/mention pipeline
            for msg in entry.get("messaging", []) or []:
                mid = (msg.get("message") or {}).get("mid")
                if not mid or f"msg:{mid}" in SEEN:
                    continue
                SEEN.add(f"msg:{mid}")
                print("message from", (msg.get("sender") or {}).get("id"),
                      ":", (msg.get("message") or {}).get("text"))
                # TODO: enqueue -> DM bot reply via POST /{ig-user-id}/messages

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "3000"))
    print(f"webhook listening on :{port}/webhooks/instagram")
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()
