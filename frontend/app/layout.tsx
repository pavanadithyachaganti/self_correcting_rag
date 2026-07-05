import type { Metadata } from "next";
import "./globals.css";
import Header from "@/components/Header";

export const metadata: Metadata = {
  title: "Self-Correcting RAG",
  description: "Agentic RAG with self-correction, evaluation, and full tracing.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-ink font-sans text-fg antialiased">
        <Header />
        <main className="mx-auto max-w-4xl px-5 pb-24 pt-8">{children}</main>
      </body>
    </html>
  );
}
