"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { register } from "../../lib/auth";

export default function Registro() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await register(email, password);
      router.push("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo crear la cuenta");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="wrap" style={{ maxWidth: 420 }}>
      <Link href="/" style={{ color: "var(--accent)", textDecoration: "none", fontSize: 14 }}>
        ← Volver
      </Link>
      <div className="card" style={{ marginTop: 20 }}>
        <h2>Crear cuenta</h2>
        <form onSubmit={onSubmit}>
          <input
            type="email"
            placeholder="tu@correo.cl"
            value={email}
            required
            onChange={(e) => setEmail(e.target.value)}
            style={{ marginBottom: 10 }}
          />
          <input
            type="password"
            placeholder="Contraseña (mín. 8 caracteres)"
            value={password}
            required
            minLength={8}
            onChange={(e) => setPassword(e.target.value)}
            style={{ marginBottom: 14 }}
          />
          <button
            type="submit"
            className="primary"
            disabled={loading}
            style={{ width: "100%", padding: 14 }}
          >
            {loading ? <span className="spinner" /> : "Crear cuenta"}
          </button>
        </form>
        {error && <div className="error">⚠ {error}</div>}
        <div className="hint" style={{ marginTop: 14 }}>
          ¿Ya tienes cuenta?{" "}
          <Link href="/login" style={{ color: "var(--accent)" }}>
            Inicia sesión
          </Link>
        </div>
      </div>
    </main>
  );
}
