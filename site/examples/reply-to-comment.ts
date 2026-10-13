/**
 * Reply to an Instagram comment via the Graph API.
 * Generated: 2026-10-13
 * Env: ACCESS_TOKEN (Page token), GRAPH_VERSION (default v21.0), COMMENT_ID, MESSAGE
 * Run: npx tsx reply-to-comment.ts
 */

const VERSION = process.env.GRAPH_VERSION ?? "v21.0";
const BASE = `https://graph.facebook.com/${VERSION}`;
const TOKEN = process.env.ACCESS_TOKEN!;
const COMMENT_ID = process.env.COMMENT_ID ?? "178700001";

async function main() {
  const res = await fetch(`${BASE}/${COMMENT_ID}/replies`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      message: process.env.MESSAGE ?? "Thanks! More coming Friday.",
      access_token: TOKEN,
    }),
  });
  const json = (await res.json()) as { id?: string; error?: { message: string } };
  if (!res.ok) throw new Error(json.error?.message ?? `HTTP ${res.status}`);
  console.log("Reply comment ID:", json.id);
}

main().catch((e) => { console.error(e); process.exit(1); });
