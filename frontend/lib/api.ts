// Thin client for the PrivRAG FastAPI backend.

export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE?.replace(/\/$/, "") ||
  "https://privrag-production.up.railway.app";

const API_KEY = process.env.NEXT_PUBLIC_API_KEY || "";

function authHeaders(): Record<string, string> {
  const headers: Record<string, string> = {};
  if (API_KEY) headers["X-API-Key"] = API_KEY;
  // Send the bearer token if the user is logged in (read directly from storage
  // to avoid an import cycle with auth.ts).
  if (typeof window !== "undefined") {
    const token = window.localStorage.getItem("privrag_token");
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
}

export interface SourceChunk {
  chunk_id: string;
  doc_id: string;
  similarity: number;
  text_preview: string;
}

export interface QueryResponse {
  answer: string;
  session_id: string;
  cache_hit: boolean;
  latency_ms: number;
  chunk_count: number;
  pii_found: boolean;
  pii_types: string[];
  llm_provider: string;
  source_chunks: SourceChunk[];
  tokens_saved_pct: number | null;
}

export interface IngestResponse {
  doc_id: number;
  filename: string;
  chunk_count: number;
  status: string;
  pii_scrubbed: boolean;
}

async function parseError(res: Response): Promise<string> {
  try {
    const body = await res.json();
    return body?.detail ? String(body.detail) : `Error ${res.status}`;
  } catch {
    return `Error ${res.status}`;
  }
}

export async function query(
  q: string,
  sessionId: string
): Promise<QueryResponse> {
  const res = await fetch(`${API_BASE}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ query: q, session_id: sessionId }),
  });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function ingest(
  file: File,
  sessionId: string
): Promise<IngestResponse> {
  const form = new FormData();
  form.append("file", file);
  form.append("session_id", sessionId);
  const res = await fetch(`${API_BASE}/ingest`, {
    method: "POST",
    headers: { ...authHeaders() },
    body: form,
  });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function health(): Promise<{ status: string; provider: string }> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}
