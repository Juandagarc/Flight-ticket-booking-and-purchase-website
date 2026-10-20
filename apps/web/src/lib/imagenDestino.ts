/** Imagen alusiva al destino de un vuelo, generada como SVG (RF-10, RF-65). */

const PALETAS = [
  ["#0f3d91", "#3b82f6", "#f7b267"],
  ["#123c3a", "#2a9d8f", "#e9c46a"],
  ["#3a0f4d", "#9d4edd", "#ffb4a2"],
  ["#5a1e0f", "#e76f51", "#f4d35e"],
  ["#0b2545", "#13315c", "#8da9c4"],
  ["#1b4332", "#40916c", "#d8f3dc"],
];

function hash(texto: string) {
  let h = 0;
  for (const c of texto) h = (h * 31 + c.charCodeAt(0)) >>> 0;
  return h;
}

function escapar(texto: string) {
  return texto.replace(/[&<>"']/g, (c) => `&#${c.charCodeAt(0)};`);
}

export function generarSvg(codigo: string, nombre: string, pais: string, conTexto = true) {
  const h = hash(codigo);
  const [fondo, medio, sol] = PALETAS[h % PALETAS.length];
  const cerros = Array.from({ length: 7 }, (_, i) => {
    const x = i * 140 - 40;
    const alto = 120 + ((h >> (i * 3)) % 90);
    return `M${x} 450 L${x + 110} ${450 - alto} L${x + 220} 450 Z`;
  }).join(" ");
  const sx = 520 + (h % 160);
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 450" role="img" aria-label="${escapar(nombre)}">
  <defs>
    <linearGradient id="cielo" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="${fondo}"/><stop offset="1" stop-color="${medio}"/>
    </linearGradient>
  </defs>
  <rect width="800" height="450" fill="url(#cielo)"/>
  <circle cx="${sx}" cy="150" r="70" fill="${sol}" opacity="0.9"/>
  <path d="${cerros}" fill="#000" opacity="0.22"/>
  <path d="M0 450 C 200 380, 420 420, 800 360 L800 450 Z" fill="#000" opacity="0.25"/>
  <g transform="translate(120 120) rotate(-12)" fill="#fff" opacity="0.95">
    <path d="M0 18 L120 10 L170 -14 L182 -10 L150 14 L210 12 L226 0 L236 2 L224 22 L236 42 L226 44 L210 32 L150 30 L182 54 L170 58 L120 34 L0 26 Z"/>
  </g>
${conTexto ? `  <text x="48" y="360" font-family="Inter, Arial, sans-serif" font-size="64" font-weight="700" fill="#fff">${escapar(nombre)}</text>
  <text x="50" y="400" font-family="Inter, Arial, sans-serif" font-size="24" fill="#fff" opacity="0.85">${escapar(pais)} · ${escapar(codigo)}</text>` : ""}
</svg>`;
}
