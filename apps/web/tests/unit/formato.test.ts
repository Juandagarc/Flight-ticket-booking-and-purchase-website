import { describe, expect, it } from "vitest";

import * as f from "@/lib/formato";

describe("formato", () => {
  it("precios en pesos colombianos sin decimales", () => {
    expect(f.precio("280000.00")).toMatch(/^\$\s?280\.000$/);
    expect(f.precio(1250000)).toMatch(/^\$\s?1\.250\.000$/);
  });

  it("duración en horas y minutos", () => {
    expect(f.duracion(18)).toBe("18 min");
    expect(f.duracion(120)).toBe("2 h");
    expect(f.duracion(632)).toBe("10 h 32 min");
  });

  it("fechas locales sin conversión de zona", () => {
    expect(f.fechaCorta("2026-11-03T23:15:00")).toBe("3 nov 2026");
    expect(f.hora("2026-11-03T23:15:00")).toBe("23:15");
    expect(f.fechaHora("2026-11-03T08:05:00")).toBe("3 nov 2026 · 08:05");
  });

  it("días de diferencia para mostrar la llegada al día siguiente", () => {
    expect(f.diasDeDiferencia("2026-12-31T20:00:00", "2027-01-01T13:00:00")).toBe(1);
    expect(f.diasDeDiferencia("2026-11-03T08:00:00", "2026-11-03T09:00:00")).toBe(0);
  });
});
