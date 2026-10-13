/**
 * Publish a Reel: create a REELS container, poll until FINISHED, then publish.
 * Generated: 2026-10-13
 * Env: IG_USER_ID, ACCESS_TOKEN (Page token), GRAPH_VERSION (default v21.0), VIDEO_URL, CAPTION
 * Run: npx tsx publish-reel.ts
 */

const VERSION = process.env.GRAPH_VERSION ?? "v21.0";
const BASE = `https://graph.facebook.com/${VERSION}`;
const IG_USER_ID = process.env.IG_USER_ID!;
const TOKEN = process.env.ACCESS_TOKEN!;

async function post<T>(path: string, body: Record<string, string>): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({ ...body, access_token: TOKEN }),
  });
  const json = (await res.json()) as T & { error?: { message: string } };
  if (!res.ok) throw new Error(json.error?.message ?? `HTTP ${res.status}`);
  return json;
}

async function containerStatus(id: string) {
  const res = await fetch(`${BASE}/${id}?fields=status_code,status&access_token=${TOKEN}`);
  const json = (await res.json()) as { status_code: string; status?: string; error?: { message: string } };
  if (!res.ok) throw new Error(json.error?.message ?? `HTTP ${res.status}`);
  return json;
}

async function main() {
  const container = await post<{ id: string }>(`/${IG_USER_ID}/media`, {
    media_type: "REELS",
    video_url: process.env.VIDEO_URL ?? "https://example.com/reel.mp4",
    caption: process.env.CAPTION ?? "New reel",
    share_to_feed: "true",
  });
  console.log("Container:", container.id);

  // Poll every 5s until processed (videos are async)
  for (;;) {
    const s = await containerStatus(container.id);
    console.log("Status:", s.status_code);
    if (s.status_code === "FINISHED") break;
    if (s.status_code === "ERROR" || s.status_code === "EXPIRED") {
      throw new Error(`Container ${s.status_code}: ${s.status ?? "unknown"}`);
    }
    await new Promise((r) => setTimeout(r, 5000));
  }

  const published = await post<{ id: string }>(`/${IG_USER_ID}/media_publish`, {
    creation_id: container.id,
  });
  console.log("Published Reel media ID:", published.id);
}

main().catch((e) => { console.error(e); process.exit(1); });
