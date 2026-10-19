import { describe, expect, it } from "vitest";

import { decidirAcceso, destinoSeguro, inicioDeRol } from "@/lib/rutas";

const redirige = (ruta: string, rol: Parameters<typeof decidirAcceso>[1]) => {
  const d = decidirAcceso(ruta, rol);
  return d.tipo === "redirigir" ? d.destino : null;
};

describe("HU-002 · cada rol llega a su página", () => {
  it("cliente al dashboard; administrador y root al panel", () => {
    expect(inicioDeRol("CLIENTE")).toBe("/cliente");
    expect(inicioDeRol("ADMINISTRADOR")).toBe("/admin");
    expect(inicioDeRol("ROOT")).toBe("/admin");
  });

  it("con sesión iniciada, login y registro llevan a la página del rol", () => {
    expect(redirige("/login", "CLIENTE")).toBe("/cliente");
    expect(redirige("/registro?x=1", "ROOT")).toBe("/admin");
    expect(redirige("/login?next=%2Fvuelos", null)).toBeNull();
  });
});

describe("RF-33 y RF-34 · barrera de reserva y compra", () => {
  it("el visitante que intenta reservar va al inicio de sesión conservando el vuelo", () => {
    expect(redirige("/reservar/FL0001?pasajeros=2", null)).toBe(
      `/login?next=${encodeURIComponent("/reservar/FL0001?pasajeros=2")}`,
    );
  });

  it("root y administrador nunca entran a reservar", () => {
    expect(redirige("/reservar/FL0001", "ROOT")).toBe("/admin?aviso=sin-compras");
    expect(redirige("/reservar/FL0001", "ADMINISTRADOR")).toBe("/admin?aviso=sin-compras");
  });

  it("el cliente sí entra", () => {
    expect(redirige("/reservar/FL0001", "CLIENTE")).toBeNull();
  });
});

describe("RNF-05 · pantallas por rol", () => {
  it.each([
    ["/admin/administradores", "ROOT", null],
    ["/admin/administradores", "ADMINISTRADOR", "/admin"],
    ["/admin/administradores", "CLIENTE", "/cliente"],
    ["/admin/vuelos/nuevo", "ADMINISTRADOR", null],
    ["/admin/vuelos", "ROOT", "/admin"],
    ["/admin/vuelos/FL0001", "CLIENTE", "/cliente"],
    ["/admin", "CLIENTE", "/cliente"],
    ["/admin", "ROOT", null],
    ["/cliente", "ADMINISTRADOR", "/admin"],
    ["/perfil", "ROOT", null],
    ["/vuelos", null, null],
    ["/noticias", null, null],
  ] as const)("%s con rol %s → %s", (ruta, rol, destino) => {
    expect(redirige(ruta, rol)).toBe(destino);
  });

  it("las pantallas privadas piden sesión", () => {
    for (const ruta of ["/cliente", "/perfil", "/admin", "/admin/vuelos", "/admin/administradores"]) {
      expect(redirige(ruta, null)).toBe(`/login?next=${encodeURIComponent(ruta)}`);
    }
  });
});

describe("destino seguro tras iniciar sesión", () => {
  it("respeta rutas internas permitidas para el rol", () => {
    expect(destinoSeguro("/reservar/FL0002", "CLIENTE")).toBe("/reservar/FL0002");
  });
  it("ignora destinos externos o no permitidos", () => {
    expect(destinoSeguro("https://malicioso.example", "CLIENTE")).toBe("/cliente");
    expect(destinoSeguro("//malicioso.example", "CLIENTE")).toBe("/cliente");
    expect(destinoSeguro("/reservar/FL0002", "ADMINISTRADOR")).toBe("/admin");
    expect(destinoSeguro(undefined, "ROOT")).toBe("/admin");
  });
});
