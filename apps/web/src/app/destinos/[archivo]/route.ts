import { obtenerCiudades } from "@/lib/datos";
import { generarSvg } from "@/lib/imagenDestino";

/**
 * Imagen alusiva al destino de cada vuelo (RF-10, RF-65). Se genera como SVG para que el sistema
 * no dependa de imágenes externas; el administrador puede reemplazarla con su propia URL.
 */

export async function GET(request: Request, { params }: { params: Promise<{ archivo: string }> }) {
  const { archivo } = await params;
  const codigo = archivo.replace(/\.svg$/i, "").toUpperCase().slice(0, 5);
  const ciudad = (await obtenerCiudades()).find((c) => c.codigo === codigo);
  const conTexto = new URL(request.url).searchParams.get("texto") !== "0";
  const svg = generarSvg(codigo, ciudad?.nombre ?? codigo, ciudad?.pais ?? "", conTexto);
  return new Response(svg, {
    headers: {
      "Content-Type": "image/svg+xml; charset=utf-8",
      "Cache-Control": ciudad ? "public, max-age=86400" : "no-store",
    },
  });
}
