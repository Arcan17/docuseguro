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
    "Hazle preguntas a tus documentos con tus propias palabras y recibe respuestas al instante, manteniendo tus datos privados protegidos.",
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
