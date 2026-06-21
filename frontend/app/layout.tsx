import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "PrivRAG — Query your documents without leaking PII",
  description:
    "Privacy-preserving RAG. Ask questions over your internal documents in natural language — no sensitive data ever reaches an external LLM.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
