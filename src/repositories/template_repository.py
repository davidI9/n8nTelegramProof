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

    Reglas aplicadas:
    - Si el logo no está en 600x600 (lado mayor), se reescala para que su lado mayor sea 600 px.
    - El logo se inserta en un bloque <defs> con id="logo_actividad".
    - Se clona el logo con 4 etiquetas <use> en posiciones fijas.
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

    bloque_logo = (
        "\n"
        f"    {LOGO_BLOCK_START}\n"
        "    <defs>\n"
        f"        <image id=\"logo_actividad\" xlink:href=\"data:image/png;base64,{logo_base64}\" width=\"650\" height=\"650\" />\n"
        "    </defs>\n"
        f"    <g id=\"logos_actividad\" transform=\"scale({scale_x:.12f} {scale_y:.12f})\">\n"
        "        <use xlink:href=\"#logo_actividad\" x=\"596\" y=\"677\" />\n"
        "        <use xlink:href=\"#logo_actividad\" x=\"598\" y=\"2652\" />\n"
        "        <use xlink:href=\"#logo_actividad\" x=\"3003\" y=\"699\" />\n"
        "        <use xlink:href=\"#logo_actividad\" x=\"2877\" y=\"2282\" />\n"
        "    </g>\n"
        f"    {LOGO_BLOCK_END}\n"
    )

    if LOGO_BLOCK_START in contenido_svg and LOGO_BLOCK_END in contenido_svg:
        patron_bloque = re.compile(
            rf"{re.escape(LOGO_BLOCK_START)}.*?{re.escape(LOGO_BLOCK_END)}\\s*",
            flags=re.DOTALL,
        )
        contenido_svg = re.sub(patron_bloque, "", contenido_svg)

    if "</svg>" not in contenido_svg:
        raise ValueError("El archivo SVG base no contiene la etiqueta de cierre </svg>.")

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
