"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { API_BASE } from "../../lib/api";
import {
  clearSession,
  getStats,
  getToken,
  logout,
  type Stats,
} from "../../lib/auth";

export default function Dashboard() {
  const router = useRouter();
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    getStats()
      .then((s) => {
        if (s == null) {
          // token invalid/expired
          clearSession();
          router.replace("/login");
          return;
        }
        setStats(s);
      })
      .finally(() => setLoading(false));
  }, [router]);

  function onLogout() {
    logout();
    router.replace("/");
  }

  async function onDelete() {
    if (
      !confirm(
        "¿Eliminar tu cuenta? Se borrarán tus documentos y tu historial. Esta acción no se puede deshacer."
      )
    )
      return;
    setDeleting(true);
    try {
      await fetch(`${API_BASE}/auth/account`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${getToken()}` },
      });
    } finally {
      clearSession();
      router.replace("/");
    }
  }

  if (loading) {
    return (
      <main className="wrap">
        <div className="hint" style={{ textAlign: "center", marginTop: 60 }}>
          Cargando tu panel…
        </div>
      </main>
    );
  }
  if (!stats) return null;

  return (
    <main className="wrap">
      <div className="appbar">
        <Link href="/" className="brand brand-sm">
          Docu<span className="brand-accent">Seguro</span>
        </Link>
        <div className="sessionbar">
          <Link href="/app" className="chip">
            Ir a la app
          </Link>
          <button className="chip" onClick={onLogout}>
            Cerrar sesión
          </button>
        </div>
      </div>

      <section className="hero" style={{ paddingBottom: 0 }}>
        <h1 style={{ fontSize: 30 }}>Tu panel</h1>
        <p style={{ fontSize: 15 }}>{stats.email}</p>
      </section>

      {/* Estado del trial */}
      <div className={stats.trial_active ? "trial-card" : "trial-card off"}>
        {stats.trial_active ? (
          <>
            <div className="trial-card-big">{stats.trial_days_remaining}</div>
            <div>
              <strong>días de prueba restantes</strong>
              <div className="hint">
                Vence el{" "}
                {new Date(stats.trial_expires_at).toLocaleDateString("es-CL", {
                  day: "2-digit",
                  month: "long",
                  year: "numeric",
                })}
              </div>
            </div>
          </>
        ) : (
          <>
            <div className="trial-card-big">⏳</div>
            <div>
              <strong>Tu período de prueba terminó</strong>
              <div className="hint">
                Para seguir usando DocuSeguro, escríbenos a{" "}
                <a
                  href="mailto:bast-1996@hotmail.com"
                  style={{ color: "var(--accent)" }}
                >
                  bast-1996@hotmail.com
                </a>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Métricas */}
      <div className="stat-grid">
        <div className="stat-card">
          <div className="stat-num">{stats.documents_count}</div>
          <div className="stat-label">Documentos subidos</div>
        </div>
        <div className="stat-card">
          <div className="stat-num">{stats.queries_count}</div>
          <div className="stat-label">Consultas realizadas</div>
        </div>
        <div className="stat-card">
          <div className="stat-num accent">{stats.pii_events_count}</div>
          <div className="stat-label">Veces que protegimos datos privados</div>
        </div>
      </div>

      <div style={{ marginTop: 28, textAlign: "center" }}>
        <Link href="/app" className="lp-btn lp-btn-primary">
          Ir a la app →
        </Link>
      </div>

      {/* Zona peligrosa */}
      <div className="danger-zone">
        <div>
          <strong>Eliminar cuenta</strong>
          <div className="hint">
            Borra tu cuenta, tus documentos y tu historial de forma permanente.
          </div>
        </div>
        <button className="btn-danger" onClick={onDelete} disabled={deleting}>
          {deleting ? "Eliminando…" : "Eliminar cuenta"}
        </button>
      </div>

      <div className="footer">
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
