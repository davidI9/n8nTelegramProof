import base64
import re
from io import BytesIO
from pathlib import Path

from PIL import Image


SVG_BASE_WIDTH = 4316.0
SVG_BASE_HEIGHT = 4301.0
LOGO_BLOCK_START = "<!-- logo_actividad:start -->"
LOGO_BLOCK_END = "<!-- logo_actividad:end -->"


def incrustar_logo_en_svg(ruta_svg_base: str, ruta_logo_png: str, ruta_salida: str) -> str:
    """Incrusta un logo codificado en Base64 en una plantilla SVG y guarda el resultado.

    Parámetros:
    - ruta_svg_base: Ruta del SVG base que contiene los 4 diseños.
    - ruta_logo_png: Ruta de la imagen del logo descargada desde Telegram.
    - ruta_salida: Ruta donde se guardará el SVG final.

    Implementación:
    - Calcula el escalado del viewBox y las posiciones base del diseño.
    - Para cada grupo objetivo (`twitter`, `story`, `post`, `youtube`) busca el <g>
      correspondiente y toma su atributo `transform` (si existe).
    - Convierte las coordenadas globales a locales aplicando la inversa del `transform`
      del propio grupo y genera una etiqueta `<image>` insertada justo antes de `</g>`.
    """
    svg_path = Path(ruta_svg_base)
    logo_path = Path(ruta_logo_png)
    output_path = Path(ruta_salida)

    if not svg_path.is_file():
        raise FileNotFoundError(f"No existe el SVG base: {ruta_svg_base}")

    if not logo_path.is_file():
        raise FileNotFoundError(f"No existe el logo: {ruta_logo_png}")

    logo_base64 = _logo_a_base64_redimensionado(logo_path)

    try:
        contenido_svg = svg_path.read_text(encoding="utf-8")
    except OSError as error:
        raise OSError(f"No se pudo leer el SVG base: {ruta_svg_base}") from error

    viewbox_width, viewbox_height = _extraer_viewbox_dimensiones(contenido_svg)
    scale_x = viewbox_width / SVG_BASE_WIDTH
    scale_y = viewbox_height / SVG_BASE_HEIGHT

    # sólo marcadores para idempotencia; no crear grupo fallback que pueda generar artefactos
    bloque_logo = (
        "\n"
        f"    {LOGO_BLOCK_START}\n"
        f"    {LOGO_BLOCK_END}\n"
    )

    # eliminar bloque previo completo si existe
    if LOGO_BLOCK_START in contenido_svg and LOGO_BLOCK_END in contenido_svg:
        patron_bloque = re.compile(
            rf"{re.escape(LOGO_BLOCK_START)}.*?{re.escape(LOGO_BLOCK_END)}\s*",
            flags=re.DOTALL,
        )
        contenido_svg = re.sub(patron_bloque, "", contenido_svg)

    # eliminar imágenes embebidas previas (data URIs) para evitar duplicados en los grupos
    contenido_svg = re.sub(r'<image[^>]+xlink:href\s*=\s*"data:image/png;base64,[^\"]+"[^>]*>', '', contenido_svg, flags=re.IGNORECASE)

    if "</svg>" not in contenido_svg:
        raise ValueError("El archivo SVG base no contiene la etiqueta de cierre </svg>.")

    # mapeo base (coordenadas en diseño base 4316x4301)
    placements = {
        "twitter": (3003, 699),
        "story": (598, 2652),
        "post": (596, 677),
        "youtube": (2877, 2282),
    }

    base_img_size = 650.0

    def parse_transform(s: str):
        if not s:
            return [[1,0,0],[0,1,0],[0,0,1]]
        s = s.strip()
        m = [[1,0,0],[0,1,0],[0,0,1]]
        for part in re.finditer(r'([a-zA-Z]+)\s*\(([^)]+)\)', s):
            name = part.group(1)
            args = [float(x) for x in re.split(r'[ ,]+', part.group(2).strip()) if x!='']
            if name == 'translate':
                tx = args[0]
                ty = args[1] if len(args)>1 else 0.0
                mat = [[1,0,tx],[0,1,ty],[0,0,1]]
            elif name == 'scale':
                sx = args[0]
                sy = args[1] if len(args)>1 else sx
                mat = [[sx,0,0],[0,sy,0],[0,0,1]]
            elif name == 'matrix':
                a,b,c,d,e,f = args[:6]
                mat = [[a,c,e],[b,d,f],[0,0,1]]
            else:
                mat = [[1,0,0],[0,1,0],[0,0,1]]
            # multiply m @ mat
            m = [
                [m[0][0]*mat[0][0] + m[0][1]*mat[1][0] + m[0][2]*mat[2][0],
                 m[0][0]*mat[0][1] + m[0][1]*mat[1][1] + m[0][2]*mat[2][1],
                 m[0][0]*mat[0][2] + m[0][1]*mat[1][2] + m[0][2]*mat[2][2]],
                [m[1][0]*mat[0][0] + m[1][1]*mat[1][0] + m[1][2]*mat[2][0],
                 m[1][0]*mat[0][1] + m[1][1]*mat[1][1] + m[1][2]*mat[2][1],
                 m[1][0]*mat[0][2] + m[1][1]*mat[1][2] + m[1][2]*mat[2][2]],
                [0,0,1]
            ]
        return m

    def mat_inv(m):
        a,b,c = m[0]
        d,e,f = m[1]
        det = a*e - b*d
        if abs(det) < 1e-9:
            return [[1,0,0],[0,1,0],[0,0,1]]
        inv = [[e/det, -b/det, (b*f - c*e)/det],[ -d/det, a/det, (c*d - a*f)/det],[0,0,1]]
        return inv

    def apply_mat(m, x, y):
        nx = m[0][0]*x + m[0][1]*y + m[0][2]
        ny = m[1][0]*x + m[1][1]*y + m[1][2]
        return nx, ny

    def encontrar_bloque_grupo(nombre: str):
        patron_apertura = re.compile(
            rf'<g\b[^>]*(?:id\s*=\s*"layer-{re.escape(nombre)}"|inkscape:label\s*=\s*"[^"]*{re.escape(nombre)}[^"]*")[^>]*>',
            flags=re.IGNORECASE,
        )
        apertura = patron_apertura.search(contenido_svg)
        if not apertura:
            return None

        patron_tag = re.compile(r'</?g\b[^>]*>', flags=re.IGNORECASE)
        depth = 1
        pos = apertura.end()

        while True:
            tag = patron_tag.search(contenido_svg, pos)
            if not tag:
                return None

            token = tag.group(0)
            if token.startswith('</'):
                depth -= 1
            else:
                # evitar contar grupos autocerrados como apertura adicional
                if not token.rstrip().endswith('/>'):
                    depth += 1

            if depth == 0:
                return apertura, tag

            pos = tag.end()

    # insertar por regex calculando coords locales usando sólo el transform del <g>
    for name, (bx, by) in placements.items():
        x_global = bx * scale_x
        y_global = by * scale_y
        w_global = base_img_size * scale_x
        h_global = base_img_size * scale_y

        bloque = encontrar_bloque_grupo(name)
        if not bloque:
            continue

        apertura, cierre = bloque
        start_tag = apertura.group(0)
        t_m = re.search(r'transform\s*=\s*"([^"]+)"', start_tag)
        t = t_m.group(1) if t_m else ''
        Mt = parse_transform(t)
        Minv = mat_inv(Mt)
        lx, ly = apply_mat(Minv, x_global, y_global)
        rx, ry = apply_mat(Minv, x_global + w_global, y_global + h_global)
        lw = abs(rx - lx)
        lh = abs(ry - ly)

        image_tag = (
            f'<image xlink:href="data:image/png;base64,{logo_base64}" '
            f'x="{lx:.6f}" y="{ly:.6f}" width="{lw:.6f}" height="{lh:.6f}" '
            'preserveAspectRatio="xMidYMid meet" />'
        )

        contenido_svg = f"{contenido_svg[:cierre.start()]}{image_tag}{contenido_svg[cierre.start():]}"

    # finalmente añadimos el bloque defs y el grupo fallback al final del SVG
    contenido_final = contenido_svg.rsplit("</svg>", 1)
    contenido_svg_generado = f"{contenido_final[0]}{bloque_logo}</svg>{contenido_final[1]}"

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(contenido_svg_generado, encoding="utf-8")
    except OSError as error:
        raise OSError(f"No se pudo guardar el SVG de salida: {ruta_salida}") from error

    return str(output_path)


def _logo_a_base64_redimensionado(logo_path: Path) -> str:
    """Abre el logo, ajusta el lado mayor a 600 px y devuelve su contenido en Base64 PNG."""
    try:
        with Image.open(logo_path) as logo:
            logo = logo.convert("RGBA")
            ancho, alto = logo.size
            lado_mayor = max(ancho, alto)

            if lado_mayor != 600:
                factor = 600 / lado_mayor
                nuevo_ancho = max(1, round(ancho * factor))
                nuevo_alto = max(1, round(alto * factor))
                logo = logo.resize((nuevo_ancho, nuevo_alto), Image.Resampling.LANCZOS)

            buffer = BytesIO()
            logo.save(buffer, format="PNG")
            imagen_binaria = buffer.getvalue()
    except OSError as error:
        raise OSError(f"No se pudo procesar la imagen del logo: {logo_path}") from error

    return base64.b64encode(imagen_binaria).decode("utf-8")


def _extraer_viewbox_dimensiones(contenido_svg: str) -> tuple[float, float]:
    """Extrae ancho y alto desde viewBox="minX minY width height"."""
    match = re.search(r'viewBox\s*=\s*"([^"]+)"', contenido_svg)
    if not match:
        raise ValueError("El SVG no contiene atributo viewBox para mapear coordenadas.")

    partes = match.group(1).replace(",", " ").split()
    if len(partes) != 4:
        raise ValueError("El atributo viewBox del SVG no tiene un formato válido.")

    try:
        width = float(partes[2])
        height = float(partes[3])
    except ValueError as error:
        raise ValueError("No se pudieron interpretar las dimensiones del viewBox.") from error

    if width <= 0 or height <= 0:
        raise ValueError("Las dimensiones del viewBox deben ser mayores que cero.")

    return width, height


class TemplateRepository:
    def generate_posts(self, ruta_logo_png: str, ruta_svg_base: str, ruta_salida: str) -> str:
        """Compatibilidad con el flujo actual delegando en la función principal."""
        return incrustar_logo_en_svg(
            ruta_svg_base=ruta_svg_base,
            ruta_logo_png=ruta_logo_png,
            ruta_salida=ruta_salida,
        )
