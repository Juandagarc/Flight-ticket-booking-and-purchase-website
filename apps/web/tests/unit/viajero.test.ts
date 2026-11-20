import { describe, expect, it } from "vitest";

import { camposDelFormulario } from "@/lib/viajero";

describe("HU-010 · errores de cada viajero", () => {
  it("lleva los errores de la API al campo del viajero en el formulario", () => {
    expect(camposDelFormulario({ "pasajeros.1.documento": "No válido", clase: "Requerido" })).toEqual({
      p1_documento: "No válido",
      clase: "Requerido",
    });
  });
});
