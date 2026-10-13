/**
 * Publish a single photo to Instagram via the Graph API (two-step flow).
 * Generated: 2026-10-13
 * Env: IG_USER_ID, ACCESS_TOKEN (Page token), GRAPH_VERSION (default v21.0), IMAGE_URL, CAPTION
 * Run: npx tsx publish-photo.ts
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

async function main() {
  // Step 1: create the media container
  const container = await post<{ id: string }>(`/${IG_USER_ID}/media`, {
    image_url: process.env.IMAGE_URL ?? "https://example.com/photo.jpg",
    caption: process.env.CAPTION ?? "Hello from the API #launch",
  });
  console.log("Container:", container.id);

  // Step 2: publish it
  const published = await post<{ id: string }>(`/${IG_USER_ID}/media_publish`, {
    creation_id: container.id,
  });
  console.log("Published media ID:", published.id);
}

main().catch((e) => { console.error(e); process.exit(1); });
