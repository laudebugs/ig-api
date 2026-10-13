/**
 * Instagram webhook receiver: verification (GET) + signed event intake (POST).
 * Generated: 2026-10-13
 * Env: PORT (default 3000), WEBHOOK_VERIFY_TOKEN, APP_SECRET
 * Run: npx tsx webhook-handler.ts  (expose via ngrok/cloudflared for Meta to reach it)
 *
 * Uses only node:http — no framework dependency.
 */
import { createHmac, timingSafeEqual } from "node:crypto";
import { createServer, IncomingMessage, ServerResponse } from "node:http";

const VERIFY_TOKEN = process.env.WEBHOOK_VERIFY_TOKEN ?? "";
const APP_SECRET = process.env.APP_SECRET ?? "";
const seen = new Set<string>(); // replace with Redis/DB in production

function validSignature(raw: Buffer, header: string | undefined): boolean {
  if (!header?.startsWith("sha256=") || !APP_SECRET) return false;
  const expected = createHmac("sha256", APP_SECRET).update(raw).digest();
  const got = Buffer.from(header.slice(7), "hex");
  return got.length === expected.length && timingSafeEqual(got, expected);
}

function readBody(req: IncomingMessage): Promise<Buffer> {
  return new Promise((resolve, reject) => {
    const chunks: Buffer[] = [];
    req.on("data", (c) => chunks.push(c));
    req.on("end", () => resolve(Buffer.concat(chunks)));
    req.on("error", reject);
  });
}

function dedupe(key: string): boolean {
  if (seen.has(key)) return true;
  seen.add(key);
  return false;
}

const server = createServer(async (req: IncomingMessage, res: ServerResponse) => {
  const url = new URL(req.url ?? "/", "http://localhost");
  if (req.method === "GET" && url.pathname === "/webhooks/instagram") {
    const mode = url.searchParams.get("hub.mode");
    const token = url.searchParams.get("hub.verify_token");
    const challenge = url.searchParams.get("hub.challenge") ?? "";
    if (mode === "subscribe" && token && token === VERIFY_TOKEN) {
      res.writeHead(200, { "Content-Type": "text/plain" });
      res.end(challenge);
    } else {
      res.writeHead(403);
      res.end();
    }
    return;
  }
  if (req.method === "POST" && url.pathname === "/webhooks/instagram") {
    const raw = await readBody(req);
    if (!validSignature(raw, req.headers["x-hub-signature-256"] as string | undefined)) {
      res.writeHead(401);
      res.end();
      return;
    }
    res.writeHead(200); // ack fast, process async
    res.end();
    try {
      const body = JSON.parse(raw.toString("utf8")) as {
        object: string;
        entry: Array<{ id: string; time: number; changes?: Array<{ field: string; value: { id?: string } }>; messaging?: Array<{ sender?: { id: string }; message?: { mid?: string; text?: string } }> }>;
      };
      for (const entry of body.entry ?? []) {
        for (const change of entry.changes ?? []) {
          const key = `${change.field}:${change.value?.id}`;
          if (dedupe(key)) continue;
          console.log("change:", change.field, JSON.stringify(change.value));
          // TODO: enqueue → hide/comment-reply/mention pipeline
        }
        for (const msg of entry.messaging ?? []) {
          const key = `msg:${msg.message?.mid}`;
          if (!msg.message?.mid || dedupe(key)) continue;
          console.log("message from", msg.sender?.id, ":", msg.message.text);
          // TODO: enqueue → DM bot reply via POST /{ig-user-id}/messages
        }
      }
    } catch (e) {
      console.error("bad webhook body:", e);
    }
    return;
  }
  res.writeHead(404);
  res.end();
});

server.listen(Number(process.env.PORT ?? 3000), () =>
  console.log(`webhook listening on :${process.env.PORT ?? 3000}/webhooks/instagram`),
);
