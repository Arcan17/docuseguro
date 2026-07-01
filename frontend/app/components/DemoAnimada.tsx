"use client";

import { useEffect, useState } from "react";

const QUESTION = "¿Cuál es la renta y cada cuánto se reajusta?";
const ANSWER =
  "La renta mensual es de $650.000 y se reajusta una vez al año según el IPC.";

// Duración de cada fase, en milisegundos.
const T_READ = 1500; // documento con datos visibles
const T_PROTECT = 1700; // datos se ocultan
const T_TYPE = 1800; // se escribe la pregunta
const T_THINK = 900; // pensando
const T_ANSWER = 3200; // respuesta visible
const CYCLE = T_READ + T_PROTECT + T_TYPE + T_THINK + T_ANSWER;

const TICK_MS = 60;

// Estado derivado del tiempo transcurrido dentro del ciclo (determinístico, sin
// bucles asíncronos ni condiciones de carrera con el modo estricto de React).
function frame(elapsed: number) {
  let phase: 0 | 1 | 2 | 3 | 4 = 0;
  let typed = 0;
  if (elapsed < T_READ) {
    phase = 0;
  } else if (elapsed < T_READ + T_PROTECT) {
    phase = 1;
  } else if (elapsed < T_READ + T_PROTECT + T_TYPE) {
    phase = 2;
    const p = (elapsed - T_READ - T_PROTECT) / T_TYPE;
    typed = Math.round(p * QUESTION.length);
  } else if (elapsed < T_READ + T_PROTECT + T_TYPE + T_THINK) {
    phase = 3;
    typed = QUESTION.length;
  } else {
    phase = 4;
    typed = QUESTION.length;
  }
  return { phase, typed };
}

export default function DemoAnimada() {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    const start = Date.now();
    const id = setInterval(() => {
      setElapsed((Date.now() - start) % CYCLE);
    }, TICK_MS);
    return () => clearInterval(id);
  }, []);

  const { phase, typed } = frame(elapsed);
  const hidden = phase >= 1; // datos ocultos desde la fase 1

  return (
    <div className="demo-anim" aria-hidden="true">
      {/* Documento */}
      <div className="lp-doc demo-anim-doc">
        <div className="lp-doc-label">Contrato_arriendo.pdf</div>
        <div className="lp-doc-line">Arrendatario: Juan Pérez Soto</div>
        <div className="lp-doc-line">
          RUT:{" "}
          {hidden ? (
            <span className="lp-redact">██.███.███-█</span>
          ) : (
            <span className="demo-real">12.345.678-9</span>
          )}
        </div>
        <div className="lp-doc-line">
          Correo:{" "}
          {hidden ? (
            <span className="lp-redact">████████@████.cl</span>
          ) : (
            <span className="demo-real">j.perez@correo.cl</span>
          )}
        </div>
        <div className="lp-doc-line">
          Teléfono:{" "}
          {hidden ? (
            <span className="lp-redact">+56 9 ████ ████</span>
          ) : (
            <span className="demo-real">+56 9 6521 4477</span>
          )}
        </div>
        <div className="lp-doc-line lp-doc-dim">
          Renta mensual: $650.000 — reajuste anual IPC…
        </div>
        <div className={`demo-shield ${hidden ? "on" : ""}`}>
          🔒 {hidden ? "Datos privados protegidos" : "Leyendo el documento…"}
        </div>
      </div>

      {/* Conversación */}
      <div className="demo-anim-chat">
        <div className={`lp-chat-q demo-bubble ${phase >= 2 ? "show" : ""}`}>
          {phase >= 2 ? QUESTION.slice(0, typed) : ""}
          {phase === 2 && typed < QUESTION.length && (
            <span className="demo-cursor">|</span>
          )}
        </div>
        {phase >= 3 && (
          <div className="lp-chat-a demo-bubble show">
            {phase === 3 ? (
              <span className="demo-dots">
                <span>·</span>
                <span>·</span>
                <span>·</span>
              </span>
            ) : (
              ANSWER
            )}
          </div>
        )}
      </div>

      <style>{`
        .demo-anim {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 20px;
          max-width: 820px;
          margin: 0 auto;
          align-items: center;
        }
        @media (max-width: 640px) {
          .demo-anim { grid-template-columns: 1fr; }
        }
        .demo-real {
          background: rgba(180, 140, 60, 0.14);
          border-radius: 4px;
          padding: 0 4px;
        }
        .demo-shield {
          margin-top: 12px;
          font-size: 13px;
          opacity: .7;
          transition: opacity .4s ease, color .4s ease;
        }
        .demo-shield.on { opacity: 1; color: #7a5b17; font-weight: 600; }
        .demo-anim-chat {
          display: flex;
          flex-direction: column;
          gap: 12px;
          min-height: 140px;
          justify-content: center;
        }
        .demo-bubble {
          opacity: 0;
          transform: translateY(6px);
          transition: opacity .35s ease, transform .35s ease;
        }
        .demo-bubble.show { opacity: 1; transform: none; }
        .demo-cursor { animation: demoBlink 1s steps(1) infinite; }
        @keyframes demoBlink { 50% { opacity: 0; } }
        .demo-dots span {
          display: inline-block;
          animation: demoPulse 1.2s infinite;
          font-weight: 700;
          font-size: 22px;
          line-height: 1;
        }
        .demo-dots span:nth-child(2) { animation-delay: .2s; }
        .demo-dots span:nth-child(3) { animation-delay: .4s; }
        @keyframes demoPulse { 0%, 60%, 100% { opacity: .25; } 30% { opacity: 1; } }
      `}</style>
    </div>
  );
}
