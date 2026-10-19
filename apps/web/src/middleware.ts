import { NextResponse, type NextRequest } from "next/server";

import { leerToken } from "@/lib/jwt";
import { decidirAcceso } from "@/lib/rutas";

export function middleware(request: NextRequest) {
  const sesion = leerToken(request.cookies.get("sesion")?.value);
  const ruta = request.nextUrl.pathname + request.nextUrl.search;
  const decision = decidirAcceso(ruta, sesion?.rol ?? null);
  if (decision.tipo === "redirigir") {
    return NextResponse.redirect(new URL(decision.destino, request.url));
  }
  return NextResponse.next();
}

export const config = {
  matcher: ["/login", "/registro", "/reservar/:path*", "/cliente/:path*", "/perfil/:path*", "/admin/:path*"],
};
