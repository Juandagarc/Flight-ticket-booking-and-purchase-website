import { describe, expect, it } from "vitest";

import { leerToken } from "@/lib/jwt";

function token(datos: object) {
  const b64 = (o: object) => Buffer.from(JSON.stringify(o)).toString("base64url");
  return `${b64({ alg: "HS256", typ: "JWT" })}.${b64(datos)}.firma`;
}

describe("leerToken", () => {
  const vigente = { sub: "u1", rol: "CLIENTE", usuario: "ána", exp: Math.floor(Date.now() / 1000) + 3600 };

  it("lee rol y usuario de un token vigente (incluye tildes)", () => {
    expect(leerToken(token(vigente))).toMatchObject({ rol: "CLIENTE", usuario: "ána" });
  });

  it("rechaza tokens vencidos, vacíos o mal formados", () => {
    expect(leerToken(token({ ...vigente, exp: 1 }))).toBeNull();
    expect(leerToken(undefined)).toBeNull();
    expect(leerToken("no.es")).toBeNull();
    expect(leerToken("a.b.c")).toBeNull();
    expect(leerToken(token({ usuario: "x" }))).toBeNull();
  });
});
