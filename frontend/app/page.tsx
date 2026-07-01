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

  const contactoMsg =
    "Hola, me interesa DocuSeguro y quiero agendar una demo.";
  const MAILTO = `mailto:bast-1996@hotmail.com?subject=${encodeURIComponent(
    "Quiero una demo de DocuSeguro"
  )}&body=${encodeURIComponent(contactoMsg)}`;
  const WHATSAPP = `https://wa.me/56975503354?text=${encodeURIComponent(
    contactoMsg
  )}`;

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
            <Link href="/app" className="lp-btn lp-btn-primary">
              Pruébalo gratis ahora
            </Link>
            <a href="#planes" className="lp-btn lp-btn-ghost">
              Para tu empresa →
            </a>
          </div>
          <div className="lp-hero-note">
            Sin crear cuenta · sin instalar nada · pruébalo en 1 minuto
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
              <li>
                Diseñado pensando en la nueva ley chilena de protección de datos
                personales (Ley 21.719)
              </li>
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

      {/* ---------- PLANES / EMPRESAS ---------- */}
      <section id="planes" className="lp-section">
        <h2 className="lp-h2">Empieza con una prueba. Crece a tu medida.</h2>
        <p className="lp-sub">
          Un modelo simple para equipos que trabajan con documentos de sus
          clientes.
        </p>
        <div className="lp-planes">
          <div className="lp-step-card lp-plan">
            <div className="lp-plan-tag">1 · Demo</div>
            <h3>Demo gratis</h3>
            <div className="lp-plan-price">Ahora · sin cuenta</div>
            <ul className="lp-checklist">
              <li>Pruébala al instante en el navegador</li>
              <li>Con documentos de ejemplo o los tuyos</li>
              <li>Sin instalar nada</li>
            </ul>
          </div>
          <div className="lp-step-card lp-plan lp-plan-featured">
            <div className="lp-plan-tag">2 · A tu medida</div>
            <h3>Piloto a tu medida</h3>
            <div className="lp-plan-price">Consultar</div>
            <ul className="lp-checklist">
              <li>Lo adaptamos a tus tipos de documento</li>
              <li>Un piloto con tu equipo, acompañado</li>
              <li>Opción de instalarlo en tu propio servidor</li>
            </ul>
          </div>
          <div className="lp-step-card lp-plan">
            <div className="lp-plan-tag">3 · Mantención</div>
            <h3>Mantención mensual</h3>
            <div className="lp-plan-price">Consultar</div>
            <ul className="lp-checklist">
              <li>Soporte y actualizaciones</li>
              <li>Nos encargamos de que siempre funcione</li>
              <li>Mejoras según tus necesidades</li>
            </ul>
          </div>
        </div>

        <div className="lp-proximamente">
          <span className="lp-badge">Próximamente</span>
          Guarda tus documentos y consúltalos cuando quieras —
          buscándolos por cliente o por documento— sin volver a subirlos.
        </div>

        <div className="lp-ley">
          ⚖️ Diseñado pensando en la nueva ley chilena de protección de datos
          personales (Ley 21.719).
        </div>

        <div className="lp-contacto">
          <p>
            ¿Lo quieres para tu empresa? Agenda una demo — te la mostramos en
            menos de 10 minutos, sin compromiso.
          </p>
          <div className="lp-hero-cta lp-center">
            <a className="lp-btn lp-btn-primary" href={MAILTO}>
              ✉️ Escríbenos
            </a>
            <a
              className="lp-btn lp-btn-soft"
              href={WHATSAPP}
              target="_blank"
              rel="noreferrer"
            >
              💬 WhatsApp
            </a>
          </div>
        </div>

        <style>{`
          .lp-planes {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            max-width: 960px;
            margin: 0 auto;
          }
          @media (max-width: 760px) {
            .lp-planes { grid-template-columns: 1fr; }
          }
          .lp-plan { text-align: left; }
          .lp-plan h3 { margin: 6px 0 2px; }
          .lp-plan-tag {
            font-size: 12px;
            font-weight: 700;
            letter-spacing: .04em;
            text-transform: uppercase;
            color: #9a7b3a;
          }
          .lp-plan-price {
            font-size: 15px;
            font-weight: 600;
            color: #7a5b17;
            margin-bottom: 10px;
          }
          .lp-plan-featured {
            border: 2px solid #c9a24b;
            box-shadow: 0 6px 24px rgba(160, 130, 60, .15);
          }
          .lp-proximamente {
            max-width: 720px;
            margin: 26px auto 0;
            text-align: center;
            font-size: 15px;
            color: #5b6472;
          }
          .lp-badge {
            display: inline-block;
            background: rgba(201, 162, 75, .18);
            color: #7a5b17;
            font-size: 12px;
            font-weight: 700;
            letter-spacing: .03em;
            text-transform: uppercase;
            padding: 2px 9px;
            border-radius: 999px;
            margin-right: 8px;
          }
          .lp-ley {
            max-width: 720px;
            margin: 10px auto 0;
            text-align: center;
            font-size: 14px;
            color: #5b6472;
          }
          .lp-contacto {
            max-width: 620px;
            margin: 30px auto 0;
            text-align: center;
          }
          .lp-contacto p { margin-bottom: 16px; }
        `}</style>
      </section>

      {/* ---------- CTA FINAL ---------- */}
      <section className="lp-final">
        <h2>¿Listo para verlo con tus propios documentos?</h2>
        <p>
          Pruébalo gratis ahora en la demo, o agenda una demo para tu empresa.
          Sin compromiso.
        </p>
        <div className="lp-hero-cta lp-center">
          <Link href="/app" className="lp-btn lp-btn-primary">
            Pruébalo gratis ahora
          </Link>
          <a href="#planes" className="lp-btn lp-btn-ghost">
            Agenda una demo
          </a>
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
