import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Aviso de Privacidad — PrivRAG",
  description:
    "Cómo PrivRAG trata la información, en línea con los principios de la Ley N° 21.719 de protección de datos personales de Chile.",
};

export default function Privacidad() {
  return (
    <main className="wrap" style={{ maxWidth: 760 }}>
      <Link href="/" style={{ color: "var(--accent)", textDecoration: "none", fontSize: 14 }}>
        ← Volver
      </Link>

      <h1 style={{ fontSize: 30, marginTop: 20, marginBottom: 6 }}>
        Aviso de Privacidad y Términos de Uso
      </h1>
      <p style={{ color: "var(--muted)", marginTop: 0 }}>Última actualización: junio 2026</p>

      <div className="legal">
        <p>
          PrivRAG es una herramienta de demostración que permite consultar documentos
          en lenguaje natural protegiendo los datos personales. Este aviso explica cómo
          tratamos la información, siguiendo los principios de la Ley N° 21.719 sobre
          protección de datos personales de Chile.
        </p>

        <h2>1. Qué información tratamos</h2>
        <ul>
          <li>
            <strong>Documentos que subes:</strong> pueden contener datos personales.
            Antes de procesarlos, eliminamos automáticamente identificadores como RUT,
            correos electrónicos y teléfonos.
          </li>
          <li><strong>Las preguntas</strong> que escribes durante tu sesión.</li>
          <li><strong>Datos de uso agregados y anónimos</strong> (estadísticas de visitas).</li>
        </ul>

        <h2>2. Para qué la usamos</h2>
        <p>
          Únicamente para responder tus preguntas sobre los documentos que subes durante
          tu sesión. No usamos tu información para ningún otro fin.
        </p>

        <h2>3. Eliminación automática y aislamiento</h2>
        <ul>
          <li>
            Lo que subes está <strong>aislado por sesión</strong>: ningún otro usuario
            puede consultarlo.
          </li>
          <li>
            Se <strong>elimina automáticamente</strong> del sistema. No conservamos copias
            permanentes de tus documentos.
          </li>
        </ul>

        <h2>4. Inteligencia artificial y terceros</h2>
        <p>
          Para generar las respuestas, el texto —ya <strong>sin los datos personales
          identificables</strong>— se envía a un proveedor de modelos de lenguaje (Groq,
          con servidores en Estados Unidos). Los datos sensibles (RUT, correos, teléfonos)
          se eliminan <strong>antes</strong> de este paso, por lo que el proveedor no los
          recibe.
        </p>

        <h2>5. Tus derechos</h2>
        <p>
          Puedes solicitar acceso, rectificación o supresión de tus datos. Como los
          documentos se eliminan automáticamente, no mantenemos registros permanentes que
          deban suprimirse.
        </p>

        <h2>6. Seguridad</h2>
        <p>
          La comunicación está cifrada (HTTPS) y el acceso a los datos está restringido
          por sesión.
        </p>

        <h2>7. Uso de demostración</h2>
        <p>
          Esta es una <strong>versión de demostración</strong>. Te pedimos no subir datos
          confidenciales de terceros ni información sensible real. Para uso empresarial con
          datos reales, ofrecemos una <strong>versión instalable en tu propio servidor</strong>,
          donde nada sale de tu infraestructura.
        </p>

        <h2>8. Contacto</h2>
        <p>
          Para consultas sobre privacidad, escribe a{" "}
          <strong>[tu correo de contacto]</strong>.
        </p>
      </div>
    </main>
  );
}
