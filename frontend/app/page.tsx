"use client";

import { useEffect, useRef, useState } from "react";
import {
  API_BASE,
  health,
  ingest,
  query,
  type IngestResponse,
  type QueryResponse,
} from "../lib/api";

const EXAMPLES = [
  "¿Cuántos días de vacaciones tienen los empleados?",
  "¿Cumplió el empleado con RUT 12.345.678-9 y correo ana@empresa.cl sus metas?",
  "What is the refund policy?",
];

function uuid(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return "00000000-0000-0000-0000-" + Date.now().toString().padStart(12, "0");
}

export default function Home() {
  const [provider, setProvider] = useState<string | null>(null);
  const [online, setOnline] = useState<boolean>(false);

  const [sessionId] = useState<string>(uuid);
  const [file, setFile] = useState<File | null>(null);
  const [ingestRes, setIngestRes] = useState<IngestResponse | null>(null);
  const [uploading, setUploading] = useState(false);
  const [dragging, setDragging] = useState(false);

  const [q, setQ] = useState("");
  const [loading, setLoading] = useState(false);
  const [res, setRes] = useState<QueryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fileInput = useRef<HTMLInputElement>(null);

  useEffect(() => {
    health()
      .then((h) => {
        setOnline(h.status === "ok");
        setProvider(h.provider);
      })
      .catch(() => setOnline(false));
  }, []);

  async function handleFile(f: File | null) {
    if (!f) return;
    setFile(f);
    setIngestRes(null);
    setError(null);
    setUploading(true);
    try {
      const r = await ingest(f);
      setIngestRes(r);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed");
      setFile(null);
    } finally {
      setUploading(false);
    }
  }

  async function runQuery(text?: string) {
    const value = (text ?? q).trim();
    if (!value) return;
    if (text) setQ(text);
    setLoading(true);
    setError(null);
    setRes(null);
    try {
      const r = await query(value, sessionId);
      setRes(r);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Query failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="wrap">
      <section className="hero">
        <span className="badge-live">
          <span className={online ? "dot ok" : "dot"} />
          {online ? `API live · ${provider}` : "Connecting to API…"}
        </span>
        <h1>
          Ask your documents anything.
          <br />
          <span className="grad">Without leaking sensitive data.</span>
        </h1>
        <p>
          PrivRAG strips PII (RUTs, emails, phones) <strong>before</strong> any
          text reaches an external LLM. Upload a document, ask in plain language,
          and see exactly what stayed private.
        </p>
      </section>

      {/* Step 1 — upload */}
      <div className="card">
        <h2>
          <span className="step">1</span>Upload a document
        </h2>
        <div
          className={dragging ? "drop drag" : "drop"}
          onClick={() => fileInput.current?.click()}
          onDragOver={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragging(false);
            handleFile(e.dataTransfer.files?.[0] ?? null);
          }}
        >
          <input
            ref={fileInput}
            type="file"
            accept=".pdf,.txt"
            hidden
            onChange={(e) => handleFile(e.target.files?.[0] ?? null)}
          />
          <div style={{ fontSize: 15, marginBottom: 4 }}>
            {uploading
              ? "Scrubbing PII & indexing…"
              : "Drop a PDF or .txt here, or click to choose"}
          </div>
          <div className="hint">
            Or skip this — the live demo already has sample HR docs loaded.
          </div>
        </div>
        {file && (
          <div className={ingestRes ? "filechip ok" : "filechip"}>
            {uploading ? <span className="spinner" /> : "📄"} {file.name}
            {ingestRes &&
              ` · ${ingestRes.chunk_count} chunks${
                ingestRes.pii_scrubbed ? " · PII scrubbed 🔒" : ""
              }`}
          </div>
        )}
      </div>

      {/* Step 2 — ask */}
      <div className="card">
        <h2>
          <span className="step">2</span>Ask a question
        </h2>
        <div className="qrow">
          <textarea
            rows={2}
            placeholder="e.g. How many vacation days do employees get?"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) runQuery();
            }}
          />
          <button
            className="primary"
            disabled={loading || !q.trim()}
            onClick={() => runQuery()}
          >
            {loading ? <span className="spinner" /> : "Ask"}
          </button>
        </div>
        <div className="examples">
          {EXAMPLES.map((ex) => (
            <button key={ex} className="chip" onClick={() => runQuery(ex)}>
              {ex}
            </button>
          ))}
        </div>
        {error && <div className="error">⚠ {error}</div>}
      </div>

      {/* Step 3 — answer */}
      {res && (
        <div className="card">
          <h2>
            <span className="step">3</span>Answer
          </h2>
          <div className="answer">{res.answer}</div>

          <div className="metrics">
            {res.pii_found ? (
              <span className="metric green">
                🔒 PII masked: {res.pii_types.join(", ")}
              </span>
            ) : (
              <span className="metric">🔓 No PII detected</span>
            )}
            {res.cache_hit ? (
              <span className="metric green">⚡ Cache hit</span>
            ) : (
              <span className="metric">🧠 Fresh LLM call</span>
            )}
            <span className="metric indigo">⏱ {res.latency_ms} ms</span>
            {res.tokens_saved_pct != null && (
              <span className="metric amber">
                ✂ {res.tokens_saved_pct.toFixed(1)}% tokens saved
              </span>
            )}
            <span className="metric">📚 {res.chunk_count} sources</span>
            <span className="metric">🤖 {res.llm_provider}</span>
          </div>

          {res.source_chunks.length > 0 && (
            <details className="sources">
              <summary>Show retrieved sources ({res.source_chunks.length})</summary>
              {res.source_chunks.map((c) => (
                <div className="source" key={c.chunk_id}>
                  <span className="sim">{(c.similarity * 100).toFixed(1)}%</span>{" "}
                  match · {c.text_preview}
                </div>
              ))}
            </details>
          )}
        </div>
      )}

      <div className="footer">
        Powered by{" "}
        <a href={`${API_BASE}/docs`} target="_blank" rel="noreferrer">
          the PrivRAG API
        </a>{" "}
        · embeddings run locally · the LLM never sees your raw PII
      </div>
    </main>
  );
}
