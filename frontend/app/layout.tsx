import type { Metadata } from "next";
import { Analytics } from "@vercel/analytics/next";
import "./globals.css";

export const metadata: Metadata = {
  title: "PrivRAG — Consulta tus documentos sin filtrar datos privados",
  description:
    "RAG con privacidad. Haz preguntas a tus documentos internos en lenguaje natural — sin que ningún dato sensible llegue a un LLM externo.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es">
      <body>
        {children}
        <Analytics />
      </body>
    </html>
  );
}
