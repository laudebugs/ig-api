/**
 * Fetch account insights and media insights from the Instagram Graph API.
 * Generated: 2026-10-13
 * Env: IG_USER_ID, ACCESS_TOKEN (Page token), GRAPH_VERSION (default v21.0), MEDIA_ID (optional)
 * Run: npx tsx fetch-insights.ts
 */

const VERSION = process.env.GRAPH_VERSION ?? "v21.0";
const BASE = `https://graph.facebook.com/${VERSION}`;
const IG_USER_ID = process.env.IG_USER_ID!;
const TOKEN = process.env.ACCESS_TOKEN!;

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { Authorization: `Bearer ${TOKEN}` },
  });
  const json = (await res.json()) as T & { error?: { message: string } };
  if (!res.ok) throw new Error(json.error?.message ?? `HTTP ${res.status}`);
  return json;
}

async function main() {
  const account = await get<{ data: unknown[] }>(
    `/${IG_USER_ID}/insights?metric=reach,impressions,profile_views&period=day`,
  );
  console.log("Account insights:", JSON.stringify(account.data, null, 2));

  const mediaId = process.env.MEDIA_ID;
  if (mediaId) {
    const media = await get<{ data: unknown[] }>(
      `/${mediaId}/insights?metric=reach,impressions,engagement,saved`,
    );
    console.log("Media insights:", JSON.stringify(media.data, null, 2));
  }
}

main().catch((e) => { console.error(e); process.exit(1); });
