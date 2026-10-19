import type { Rol } from "./tipos";

/** Página de inicio de cada rol después de iniciar sesión (HU-002). */
export function inicioDeRol(rol: Rol): string {
  return rol === "CLIENTE" ? "/cliente" : "/admin";
}

export type Decision = { tipo: "permitir" } | { tipo: "redirigir"; destino: string };

const permitir: Decision = { tipo: "permitir" };
const redirigir = (destino: string): Decision => ({ tipo: "redirigir", destino });

function alLogin(ruta: string): Decision {
  return redirigir(`/login?next=${encodeURIComponent(ruta)}`);
}

/**
 * Control de acceso por rol en la interfaz (RNF-05). La API aplica las mismas reglas;
 * esto solo evita mostrar pantallas que el rol no puede usar.
 */
export function decidirAcceso(rutaCompleta: string, rol: Rol | null): Decision {
  const ruta = rutaCompleta.split(/[?#]/)[0];
  const empieza = (prefijo: string) => ruta === prefijo || ruta.startsWith(`${prefijo}/`);
  const alLoginDesdeAqui = () => alLogin(rutaCompleta);

  if (empieza("/login") || empieza("/registro")) {
    return rol ? redirigir(inicioDeRol(rol)) : permitir;
  }

  // RF-33, RF-34: reservar y comprar exige ser cliente.
  if (empieza("/reservar")) {
    if (!rol) return alLoginDesdeAqui();
    return rol === "CLIENTE" ? permitir : redirigir("/admin?aviso=sin-compras");
  }

  if (empieza("/cliente")) {
    if (!rol) return alLoginDesdeAqui();
    return rol === "CLIENTE" ? permitir : redirigir(inicioDeRol(rol));
  }

  if (empieza("/perfil")) {
    return rol ? permitir : alLoginDesdeAqui();
  }

  if (empieza("/admin/administradores")) {
    if (!rol) return alLoginDesdeAqui();
    return rol === "ROOT" ? permitir : redirigir(inicioDeRol(rol));
  }

  if (empieza("/admin/vuelos")) {
    if (!rol) return alLoginDesdeAqui();
    return rol === "ADMINISTRADOR" ? permitir : redirigir(inicioDeRol(rol));
  }

  if (empieza("/admin")) {
    if (!rol) return alLoginDesdeAqui();
    return rol === "CLIENTE" ? redirigir("/cliente") : permitir;
  }

  return permitir;
}

/** Solo se aceptan destinos internos tras el inicio de sesión. */
export function destinoSeguro(next: string | null | undefined, rol: Rol): string {
  if (next && next.startsWith("/") && !next.startsWith("//")) {
    const d = decidirAcceso(next, rol);
    if (d.tipo === "permitir") return next;
  }
  return inicioDeRol(rol);
}
