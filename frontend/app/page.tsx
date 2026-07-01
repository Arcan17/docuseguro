"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { getEmail } from "../lib/auth";
import DemoAnimada from "./components/DemoAnimada";

export default function Landing() {
  const [userEmail, setUserEmail] = useState<string | null>(null);

  useEffect(() => {
    setUserEmail(getEmail());
  }, []);

  return (
    <div className="lp">
      {/* ---------- NAV ---------- */}
      <nav className="lp-nav">
        <Link href="/" className="brand">
          Docu<span className="brand-accent">Seguro</span>
        </Link>
        <div className="lp-nav-links">
          <a href="#como-funciona">Cómo funciona</a>
          <a href="#rubros">Para quién</a>
          <a href="#privacidad">Privacidad</a>
          {userEmail ? (
            <Link href="/dashboard" className="lp-btn lp-btn-soft">
              Mi panel
            </Link>
          ) : (
            <>
              <Link href="/login" className="lp-nav-login">
                Iniciar sesión
              </Link>
              <Link href="/registro" className="lp-btn lp-btn-soft">
                Crear cuenta
              </Link>
            </>
          )}
        </div>
      </nav>

      {/* ---------- HERO ---------- */}
      <header className="lp-hero">
        <div className="lp-hero-text">
          <span className="lp-eyebrow">
            Tus documentos, con tus datos protegidos
          </span>
          <h1>
            Hazle preguntas a tus documentos.
            <br />
            <span className="grad">Tus datos privados quedan protegidos.</span>
          </h1>
          <p>
            Sube un documento —un contrato, una boleta, un informe— y pregúntale
            lo que quieras saber, como si le hablaras a una persona. Te responde
            al instante, y los datos privados que aparecen en él (como el RUT o el
            teléfono) quedan <strong>ocultos y protegidos</strong>.
          </p>
          <div className="lp-hero-cta">
            <Link href="/registro" className="lp-btn lp-btn-primary">
              Empieza gratis — 14 días
            </Link>
            <Link href="/app" className="lp-btn lp-btn-ghost">
              Probar la demo →
            </Link>
          </div>
          <div className="lp-hero-note">
            Sin tarjeta de crédito · sin instalar nada · pruébalo en 1 minuto
          </div>
        </div>

        {/* Visual: antes / después del borrado de datos */}
        <div className="lp-hero-visual" aria-hidden="true">
          <div className="lp-doc">
            <div className="lp-doc-label">Contrato_arriendo.pdf</div>
            <div className="lp-doc-line">
              Arrendatario: Juan Pérez Soto
            </div>
            <div className="lp-doc-line">
              RUT: <span className="lp-redact">██.███.███-█</span>
            </div>
            <div className="lp-doc-line">
              Correo: <span className="lp-redact">████████@████.cl</span>
            </div>
            <div className="lp-doc-line">
              Teléfono: <span className="lp-redact">+56 9 ████ ████</span>
            </div>
            <div className="lp-doc-line lp-doc-dim">
              Renta mensual: $650.000 — reajuste anual IPC…
            </div>
            <div className="lp-doc-shield">🔒 Datos privados ocultados</div>
          </div>
          <div className="lp-chat">
            <div className="lp-chat-q">
              ¿Cuál es la renta y cada cuánto se reajusta?
            </div>
            <div className="lp-chat-a">
              La renta mensual es de $650.000 y se reajusta una vez al año según
              el IPC.
            </div>
          </div>
        </div>
      </header>

      {/* ---------- CÓMO FUNCIONA ---------- */}
      <section id="como-funciona" className="lp-section">
        <h2 className="lp-h2">Así de fácil. Y tus datos, protegidos.</h2>
        <div className="lp-steps">
          <div className="lp-step-card">
            <div className="lp-step-num">1</div>
            <h3>Subes tu documento</h3>
            <p>
              Un contrato, una boleta, un informe… lo subes y listo. No necesitas
              instalar nada.
            </p>
          </div>
          <div className="lp-step-card">
            <div className="lp-step-num">2</div>
            <h3>Haces tu pregunta</h3>
            <p>
              Escribes lo que quieres saber con tus propias palabras, como si le
              preguntaras a alguien.
            </p>
          </div>
          <div className="lp-step-card">
            <div className="lp-step-num">3</div>
            <h3>Recibes la respuesta</h3>
            <p>
              Clara y al instante, tomada solo de tu documento. Y tus datos
              privados quedan siempre protegidos.
            </p>
          </div>
        </div>
      </section>

      {/* ---------- DEMOSTRACIÓN ---------- */}
      <section id="demo" className="lp-section">
        <h2 className="lp-h2">Míralo funcionando</h2>
        <p className="lp-sub">Un ejemplo real, en segundos.</p>
        <DemoAnimada />
      </section>

      {/* ---------- POR RUBRO ---------- */}
      <section id="rubros" className="lp-section">
        <h2 className="lp-h2">Pensado para quien maneja información delicada</h2>
        <p className="lp-sub">
          Si tu trabajo es leer documentos con datos de clientes, esto es para ti.
        </p>
        <div className="lp-rubros">
          <div className="lp-rubro-card">
            <div className="lp-rubro-ico">⚖️</div>
            <h3>Estudios jurídicos</h3>
            <p>Contratos, escrituras, poderes, demandas.</p>
            <span className="lp-rubro-ex">
              “¿Qué cláusula regula el término anticipado?”
            </span>
          </div>
          <div className="lp-rubro-card">
            <div className="lp-rubro-ico">📊</div>
            <h3>Oficinas contables</h3>
            <p>Balances, declaraciones de renta, facturas.</p>
            <span className="lp-rubro-ex">
              “¿Cuánto fue el IVA del período?”
            </span>
          </div>
          <div className="lp-rubro-card">
            <div className="lp-rubro-ico">🛡️</div>
            <h3>Corredoras de seguros</h3>
            <p>Pólizas, informes de siniestro, liquidaciones.</p>
            <span className="lp-rubro-ex">
              “¿Qué coberturas excluye esta póliza?”
            </span>
          </div>
        </div>
      </section>

      {/* ---------- PRIVACIDAD ---------- */}
      <section id="privacidad" className="lp-section lp-privacy">
        <div className="lp-privacy-grid">
          <div>
            <span className="lp-eyebrow">La diferencia</span>
            <h2 className="lp-h2 lp-h2-left">
              Tus clientes nunca llegan a la IA
            </h2>
            <p className="lp-privacy-p">
              La mayoría de las herramientas envían tu documento entero a un
              modelo externo. DocuSeguro no. Primero detecta los datos personales
              —RUT, correos, teléfonos— y los reemplaza por etiquetas. Solo
              entonces consulta a la inteligencia artificial.
            </p>
            <ul className="lp-checklist">
              <li>El proveedor de IA jamás ve un RUT real</li>
              <li>Lo que subes en la demo se elimina solo</li>
              <li>Pensado para la Ley 21.719 de datos personales</li>
            </ul>
          </div>
          <div className="lp-flow">
            <div className="lp-flow-step">📄 Documento con datos reales</div>
            <div className="lp-flow-arrow">↓</div>
            <div className="lp-flow-step lp-flow-scrub">
              🔒 Se borran RUT, correos, teléfonos
            </div>
            <div className="lp-flow-arrow">↓</div>
            <div className="lp-flow-step lp-flow-ai">
              🤖 La IA responde — sin datos privados
            </div>
          </div>
        </div>
      </section>

      {/* ---------- CTA FINAL ---------- */}
      <section className="lp-final">
        <h2>¿Listo para usarlo con tus propios documentos?</h2>
        <p>
          Crea tu cuenta y prueba DocuSeguro gratis durante 14 días. Sin tarjeta,
          sin compromiso.
        </p>
        <div className="lp-hero-cta lp-center">
          <Link href="/registro" className="lp-btn lp-btn-primary">
            Empieza gratis ahora
          </Link>
          <Link href="/app" className="lp-btn lp-btn-ghost">
            Ver la demo primero
          </Link>
        </div>
      </section>

      {/* ---------- FOOTER ---------- */}
      <footer className="lp-footer">
        <div className="brand brand-sm">
          Docu<span className="brand-accent">Seguro</span>
        </div>
        <div className="lp-footer-links">
          <Link href="/privacidad">Aviso de privacidad</Link>
          <Link href="/terminos">Términos y condiciones</Link>
          <a href="mailto:bast-1996@hotmail.com">Contacto</a>
        </div>
        <div className="lp-footer-fine">
          DocuSeguro · Herramienta de consulta de documentos con IA · Chile
        </div>
      </footer>
    </div>
  );
}
