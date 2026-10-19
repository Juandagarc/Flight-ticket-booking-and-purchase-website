import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { destinosPermitidos } from "@/components/FormularioVuelo";
import { TarjetaVuelo } from "@/components/TarjetaVuelo";
import { generarSvg } from "@/lib/imagenDestino";
import type { Ciudad, Vuelo } from "@/lib/tipos";

const ciudad = (codigo: string, extra: Partial<Ciudad> = {}): Ciudad => ({
  codigo,
  nombre: codigo,
  pais: "Colombia",
  zona_horaria: "America/Bogota",
  es_capital_nacional: true,
  origen_internacional: false,
  destino_internacional: false,
  ...extra,
});

const CIUDADES = [
  ciudad("PEI", { origen_internacional: true }),
  ciudad("BGA"),
  ciudad("LET"),
  ciudad("MAD", { es_capital_nacional: false, destino_internacional: true, pais: "España" }),
];

describe("destinos permitidos al programar (RF-03 a RF-05)", () => {
  it("desde un origen internacional: capitales y destinos internacionales", () => {
    expect(destinosPermitidos(CIUDADES, "PEI").map((c) => c.codigo)).toEqual(["BGA", "LET", "MAD"]);
  });
  it("desde otra capital: solo capitales", () => {
    expect(destinosPermitidos(CIUDADES, "BGA").map((c) => c.codigo)).toEqual(["PEI", "LET"]);
  });
  it("nunca el mismo origen ni orígenes fuera del catálogo", () => {
    expect(destinosPermitidos(CIUDADES, "LET").map((c) => c.codigo)).not.toContain("LET");
    expect(destinosPermitidos(CIUDADES, "XXX")).toEqual([]);
  });
});

const vuelo: Vuelo = {
  codigo: "FL0007",
  tipo: "INTERNACIONAL",
  origen: { codigo: "PEI", nombre: "Pereira", pais: "Colombia" },
  destino: { codigo: "MAD", nombre: "Madrid", pais: "España" },
  salida_local: "2026-12-31T20:00:00",
  salida_utc: "2027-01-01T01:00:00Z",
  duracion_min: 632,
  llegada_local: "2027-01-01T13:32:00",
  estado: "PROGRAMADO",
  imagen_url: "/destinos/MAD.svg",
  tarifas: { primera: "7000000.00", economica: "2900000.00" },
  disponibles: { primera: 50, economica: 200 },
  editable: true,
};

describe("tarjeta de resultado (pantalla 03)", () => {
  it("muestra ruta, horas locales, duración, tarifas y el enlace para reservar", () => {
    render(<TarjetaVuelo vuelo={vuelo} pasajeros={2} />);
    expect(screen.getByText("Pereira")).toBeInTheDocument();
    expect(screen.getByText("Madrid")).toBeInTheDocument();
    expect(screen.getByText("20:00")).toBeInTheDocument();
    expect(screen.getByText("+1")).toBeInTheDocument();
    expect(screen.getByText("10 h 32 min")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Reservar" })).toHaveAttribute("href", "/reservar/FL0007?pasajeros=2");
  });
});

describe("imagen alusiva del destino", () => {
  it("genera un SVG con el nombre y escapa el texto", () => {
    const svg = generarSvg("MAD", "Madrid <&>", "España");
    expect(svg).toContain("<svg");
    expect(svg).toContain("Madrid &#60;&#38;&#62;");
    expect(svg).not.toContain("<&>");
  });
});

describe("imagen sin texto para mosaicos", () => {
  it("omite el nombre cuando se pide", () => {
    expect(generarSvg("MAD", "Madrid", "España", false)).not.toContain("<text");
  });
});
