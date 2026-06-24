import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Términos y Condiciones — PrivRAG",
  description: "Términos y condiciones de uso de PrivRAG (borrador).",
};

export default function Terminos() {
  return (
    <main className="wrap" style={{ maxWidth: 760 }}>
      <Link href="/" style={{ color: "var(--accent)", textDecoration: "none", fontSize: 14 }}>
        ← Volver
      </Link>

      <h1 style={{ fontSize: 30, marginTop: 20, marginBottom: 6 }}>
        Términos y Condiciones de Uso
      </h1>
      <p style={{ color: "var(--muted)", marginTop: 0 }}>Última actualización: junio 2026</p>

      <div
        style={{
          border: "1px solid var(--amber)",
          background: "rgba(251,191,36,0.08)",
          borderRadius: 10,
          padding: "12px 14px",
          color: "var(--amber)",
          fontSize: 13.5,
          margin: "14px 0 20px",
        }}
      >
        Borrador. Estos términos no han sido revisados por un abogado. Antes de usarlos
        para un servicio comercial o con clientes reales, deben ser validados por un
        profesional.
      </div>

      <div className="legal">
        <h2>1. Qué es PrivRAG</h2>
        <p>
          PrivRAG es una herramienta de demostración que permite consultar documentos en
          lenguaje natural, eliminando datos personales antes de procesarlos con un modelo
          de inteligencia artificial. Al usar la aplicación aceptas estos términos.
        </p>

        <h2>2. Uso permitido</h2>
        <ul>
          <li>Usa la aplicación solo con documentos sobre los que tengas derecho.</li>
          <li>
            No subas datos personales de terceros sin autorización, información sensible
            real, ni contenido ilegal.
          </li>
          <li>No intentes vulnerar, sobrecargar ni hacer un uso abusivo del servicio.</li>
        </ul>

        <h2>3. Respuestas generadas por IA</h2>
        <p>
          Las respuestas las genera un modelo de inteligencia artificial a partir de los
          documentos cargados. <strong>Pueden contener errores o imprecisiones</strong> y
          no constituyen asesoría legal, médica, financiera ni profesional. Las decisiones
          que tomes en base a ellas son de tu responsabilidad.
        </p>

        <h2>4. Sin garantías y límite de responsabilidad</h2>
        <p>
          El servicio se entrega "tal cual", sin garantías de disponibilidad, exactitud o
          adecuación a un fin específico. En la medida que la ley lo permita, no nos
          hacemos responsables por daños derivados del uso o la imposibilidad de uso de la
          aplicación.
        </p>

        <h2>5. Propiedad intelectual</h2>
        <p>
          El software y la marca PrivRAG pertenecen a su autor. El contenido que subes
          sigue siendo tuyo; solo lo procesamos para responder tus consultas durante tu
          sesión, según el{" "}
          <Link href="/privacidad" style={{ color: "var(--accent)" }}>
            aviso de privacidad
          </Link>
          .
        </p>

        <h2>6. Naturaleza de demostración</h2>
        <p>
          Esta es una versión de demostración. Puede cambiar, pausarse o discontinuarse en
          cualquier momento. Para uso empresarial con datos reales existe una versión
          instalable en tu propia infraestructura.
        </p>

        <h2>7. Legislación aplicable</h2>
        <p>
          Estos términos se rigen por las leyes de Chile. (Punto a confirmar con un
          abogado.)
        </p>

        <h2>8. Contacto</h2>
        <p>
          Consultas:{" "}
          <a href="mailto:bast-1996@hotmail.com" style={{ color: "var(--accent)" }}>
            bast-1996@hotmail.com
          </a>
          .
        </p>
      </div>
    </main>
  );
}
