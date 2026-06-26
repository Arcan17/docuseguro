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

export interface StreamHandlers {
  onDelta: (text: string) => void;
  onDone: (meta: Partial<QueryResponse>) => void;
}

// Streams the answer token-by-token over SSE. Falls back to the caller's
// onError via a thrown error.
export async function queryStream(
  q: string,
  sessionId: string,
  handlers: StreamHandlers
): Promise<void> {
  const res = await fetch(`${API_BASE}/query/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ query: q, session_id: sessionId }),
  });
  if (!res.ok || !res.body) throw new Error(await parseError(res));

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const events = buffer.split("\n\n");
    buffer = events.pop() ?? "";
    for (const evt of events) {
      const line = evt.trim();
      if (!line.startsWith("data:")) continue;
      const payload = JSON.parse(line.slice(5).trim());
      if (payload.type === "delta") {
        handlers.onDelta(payload.text);
      } else if (payload.type === "done") {
        handlers.onDone({
          cache_hit: payload.cache_hit,
          latency_ms: payload.latency_ms,
          chunk_count: payload.chunk_count,
          pii_found: payload.pii_found,
          pii_types: payload.pii_types,
          llm_provider: payload.provider,
          source_chunks: payload.source_chunks,
          tokens_saved_pct: null,
        });
      }
    }
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
