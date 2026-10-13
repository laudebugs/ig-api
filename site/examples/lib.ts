/**
 * Minimal typed Graph client shared by examples/ (fetch, no SDK).
 * Env: GRAPH_HOST (default https://graph.facebook.com), GRAPH_VERSION (default v25.0), ACCESS_TOKEN
 */

const BASE = `${process.env.GRAPH_HOST ?? "https://graph.facebook.com"}/${process.env.GRAPH_VERSION ?? "v25.0"}`;
const TOKEN = process.env.ACCESS_TOKEN!;

interface GraphErrorBody {
  error?: { message: string; code: number; error_subcode?: number; fbtrace_id?: string };
}

export async function gget<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { Authorization: `Bearer ${TOKEN}` },
  });
  const json = (await res.json()) as T & GraphErrorBody;
  if (!res.ok) {
    const err = new Error(`GET ${path} → ${json.error?.code}: ${json.error?.message ?? res.status}`) as Error & { code?: number };
    err.code = json.error?.code;
    throw err;
  }
  return json;
}

export async function gpost<T>(path: string, body: Record<string, string> = {}): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({ ...body, access_token: TOKEN }),
  });
  const json = (await res.json()) as T & GraphErrorBody;
  if (!res.ok) {
    const err = new Error(`POST ${path} → ${json.error?.code}: ${json.error?.message ?? res.status}`) as Error & { code?: number };
    err.code = json.error?.code;
    throw err;
  }
  return json;
}

export async function gpostJson<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${TOKEN}` },
    body: JSON.stringify(body),
  });
  const json = (await res.json()) as T & GraphErrorBody;
  if (!res.ok) {
    const err = new Error(`POST ${path} → ${json.error?.code}: ${json.error?.message ?? res.status}`) as Error & { code?: number };
    err.code = json.error?.code;
    throw err;
  }
  return json;
}

const RETRYABLE = new Set([1, 2, 4, 17, 32]);

export async function withRetry<T>(fn: () => Promise<T>, tries = 5): Promise<T> {
  let delay = 1000;
  for (let i = 0; ; i++) {
    try {
      return await fn();
    } catch (e: unknown) {
      const code = (e as { code?: number })?.code;
      if (i >= tries - 1 || (code !== undefined && !RETRYABLE.has(code))) throw e;
      await new Promise((r) => setTimeout(r, delay + Math.random() * 250));
      delay *= 2;
    }
  }
}
