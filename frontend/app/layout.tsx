import type { Metadata } from "next";
import { Inter, Lora } from "next/font/google";
import { Analytics } from "@vercel/analytics/next";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});

const lora = Lora({
  subsets: ["latin"],
  variable: "--font-serif",
  display: "swap",
});

export const metadata: Metadata = {
  title: "DocuSeguro — Consulta tus documentos sin filtrar datos privados",
  description:
    "Haz preguntas a tus documentos internos en lenguaje natural — sin que ningún dato sensible llegue a un LLM externo.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es" className={`${inter.variable} ${lora.variable}`}>
      <body>
        {children}
        <Analytics />
      </body>
    </html>
  );
}
