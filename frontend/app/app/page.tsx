"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import {
  API_BASE,
  health,
  ingest,
  query,
  type IngestResponse,
  type QueryResponse,
} from "../../lib/api";
import { getEmail, getStats, logout, type Stats } from "../../lib/auth";

const EXAMPLES = [
  "¿Cuántos días de vacaciones tienen los empleados?",
  "¿Cumplió el empleado con RUT 12.345.678-9 y correo ana@empresa.cl sus metas?",
  "¿Cuál es la política de devoluciones?",
];

function uuid(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return "00000000-0000-0000-0000-" + Date.now().toString().padStart(12, "0");
}

export default function DemoApp() {
  const [provider, setProvider] = useState<string | null>(null);
  const [online, setOnline] = useState<boolean>(false);
  const [userEmail, setUserEmail] = useState<string | null>(null);
  const [stats, setStats] = useState<Stats | null>(null);

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
    setUserEmail(getEmail());
    getStats().then(setStats);
  }, []);

  const trialExpired = stats != null && !stats.trial_active;

  function onLogout() {
    logout();
    setUserEmail(null);
  }

  async function handleFile(f: File | null) {
    if (!f) return;
    setFile(f);
    setIngestRes(null);
    setError(null);
    setUploading(true);
    try {
      const r = await ingest(f, sessionId);
      setIngestRes(r);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al subir el archivo");
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
      setError(e instanceof Error ? e.message : "Error en la consulta");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="wrap">
      <div className="appbar">
        <Link href="/" className="brand brand-sm">
          Docu<span className="brand-accent">Seguro</span>
        </Link>
        <div className="sessionbar">
          {userEmail ? (
            <>
              {stats != null &&
                (stats.trial_active ? (
                  <span className="trial-pill">
                    {stats.trial_days_remaining} días de prueba
                  </span>
                ) : (
                  <span className="trial-pill trial-pill-off">Prueba vencida</span>
                ))}
              <Link href="/dashboard" className="chip">
                Mi panel
              </Link>
              <span className="hint">{userEmail}</span>
              <button className="chip" onClick={onLogout}>
                Cerrar sesión
              </button>
            </>
          ) : (
            <>
              <Link href="/login" className="chip">
                Iniciar sesión
              </Link>
              <Link href="/registro" className="chip">
                Crear cuenta
              </Link>
            </>
          )}
        </div>
      </div>
      <section className="hero">
        <span className="badge-live">
          <span className={online ? "dot ok" : "dot"} />
          {online ? `API en línea · ${provider}` : "Conectando con la API…"}
        </span>
        <h1>
          Pregúntale lo que sea a tus documentos.
          <br />
          <span className="grad">Sin filtrar datos sensibles.</span>
        </h1>
        <p>
          DocuSeguro borra los datos privados (RUT, correos, teléfonos){" "}
          <strong>antes</strong> de que cualquier texto llegue a un LLM externo.
          Sube un documento, pregunta en lenguaje natural y mira exactamente qué
          se mantuvo privado.
        </p>
      </section>

      {trialExpired && (
        <div className="trial-banner">
          <strong>Tu período de prueba terminó.</strong> Puedes seguir viendo tu
          historial, pero para subir documentos o hacer consultas escríbenos a{" "}
          <a href="mailto:bast-1996@hotmail.com">bast-1996@hotmail.com</a>.
        </div>
      )}

      {/* Paso 1 — subir */}
      <div className="card">
        <h2>
          <span className="step">1</span>Sube un documento
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
            accept=".pdf,.txt,.docx"
            hidden
            onChange={(e) => handleFile(e.target.files?.[0] ?? null)}
          />
          <div style={{ fontSize: 15, marginBottom: 4 }}>
            {uploading
              ? "Borrando datos privados e indexando…"
              : "Arrastra un PDF, Word (.docx) o .txt aquí, o haz clic para elegir"}
          </div>
          <div className="hint">
            O sáltatelo — la demo ya tiene documentos de RR.HH. de ejemplo
            cargados.
          </div>
        </div>
        <div className="hint" style={{ marginTop: 10, fontSize: 12.5 }}>
          🔒 Demo: lo que subes está aislado por sesión y se elimina solo. No
          subas datos confidenciales de terceros. Ver{" "}
          <Link href="/privacidad" style={{ color: "var(--accent)" }}>
            aviso de privacidad
          </Link>
          .
        </div>
        {file && (
          <div className={ingestRes ? "filechip ok" : "filechip"}>
            {uploading ? <span className="spinner" /> : "📄"} {file.name}
            {ingestRes &&
              ` · ${ingestRes.chunk_count} fragmentos${
                ingestRes.pii_scrubbed ? " · datos privados borrados 🔒" : ""
              }`}
          </div>
        )}
      </div>

      {/* Paso 2 — preguntar */}
      <div className="card">
        <h2>
          <span className="step">2</span>Haz una pregunta
        </h2>
        <div className="qrow">
          <textarea
            rows={2}
            placeholder="ej. ¿Cuántos días de vacaciones tienen los empleados?"
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
            {loading ? <span className="spinner" /> : "Preguntar"}
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

      {/* Paso 3 — respuesta */}
      {res && (
        <div className="card">
          <h2>
            <span className="step">3</span>Respuesta
          </h2>
          <div className="answer">{res.answer}</div>

          <div className="metrics">
            {res.pii_found ? (
              <span className="metric green">
                🔒 Datos privados ocultados: {res.pii_types.join(", ")}
              </span>
            ) : (
              <span className="metric">🔓 Sin datos privados detectados</span>
            )}
            {res.cache_hit ? (
              <span className="metric green">⚡ Respuesta en caché</span>
            ) : (
              <span className="metric">🧠 Consulta nueva al LLM</span>
            )}
            <span className="metric indigo">⏱ {res.latency_ms} ms</span>
            {res.tokens_saved_pct != null && (
              <span className="metric amber">
                ✂ {res.tokens_saved_pct.toFixed(1)}% tokens ahorrados
              </span>
            )}
            <span className="metric">📚 {res.chunk_count} fuentes</span>
            <span className="metric">🤖 {res.llm_provider}</span>
          </div>

          {res.source_chunks.length > 0 && (
            <details className="sources">
              <summary>
                Ver fuentes recuperadas ({res.source_chunks.length})
              </summary>
              {res.source_chunks.map((c) => (
                <div className="source" key={c.chunk_id}>
                  <span className="sim">{(c.similarity * 100).toFixed(1)}%</span>{" "}
                  de coincidencia · {c.text_preview}
                </div>
              ))}
            </details>
          )}
          <div className="hint" style={{ marginTop: 16, fontSize: 12.5 }}>
            ⚠️ Respuesta generada por IA. Puede contener errores; no constituye
            asesoría legal ni profesional.
          </div>
        </div>
      )}

      {/* CTA para visitantes anónimos tras la primera consulta (Escenario 3) */}
      {res && !userEmail && (
        <div className="signup-cta">
          <div>
            <strong>¿Te sirvió?</strong> Crea una cuenta gratis para guardar tus
            documentos y tu historial — 14 días de prueba, sin tarjeta.
          </div>
          <Link href="/registro" className="primary-link">
            Crear cuenta gratis
          </Link>
        </div>
      )}

      <div className="footer">
        Funciona con{" "}
        <a href={`${API_BASE}/docs`} target="_blank" rel="noreferrer">
          la API de DocuSeguro
        </a>{" "}
        · los embeddings corren localmente · el LLM nunca ve tus datos privados
        <br />
        <Link href="/privacidad" className="legal-link">
          Aviso de privacidad
        </Link>{" "}
        ·{" "}
        <Link href="/terminos" className="legal-link">
          Términos y condiciones
        </Link>
      </div>
    </main>
  );
}
