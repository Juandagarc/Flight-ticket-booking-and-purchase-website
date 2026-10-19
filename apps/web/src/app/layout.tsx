import type { Metadata } from "next";

import { EncabezadoSitio } from "@/components/EncabezadoSitio";

import "./globals.css";

export const metadata: Metadata = {
  title: { default: "Flight · Tiquetes aéreos", template: "%s · Flight" },
  description: "Compra y reserva de tiquetes aéreos en línea: vuelos nacionales e internacionales directos.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="es">
      <body className="min-h-screen">
        <EncabezadoSitio />
        <main className="mx-auto w-full max-w-6xl px-4 pb-16 pt-6 sm:px-6">{children}</main>
        <footer className="border-t border-linea py-6 text-center text-xs text-tinta-suave">
          Flight · Laboratorio de Software 2026-02 · Universidad Tecnológica de Pereira
        </footer>
      </body>
    </html>
  );
}
