"""
================================================================================
 TOOLKIT COMPARTIDO DE PDF — maquetación adaptativa y primitivas de dibujo
================================================================================
Capa de dibujo común a los cuatro reportes en PDF (Sullivan mensual, Sullivan
semanal, Sullivan unificado y Loco Tequila USA).

¿Por qué existe?
----------------
Toda esta lógica vivía dentro de `pdf_generator.py`. Al añadir tres reportes más
había dos caminos: copiarla tres veces, o extraerla. Copiarla significa que la
siguiente corrección de maquetación (y ya hubo varias: desbordes de ~20 pt,
huecos de ~250 pt, textos truncados que perdían la petición) habría que
aplicarla cuatro veces y en algún momento se olvidaría una.

Qué resuelve cada pieza
-----------------------
* `auto_row_h` / `center_block` / `scale_widths`: el problema de "las tablas y
  las imágenes a veces se ven muy pequeñas y dejan muchos espacios". Las alturas
  y anchos se derivan del espacio disponible en vez de ser constantes.
* `fit_text` / `wrap_text`: `drawString` no hace ajuste de línea. Sin esto, una
  etiqueta larga se dibuja encima de la columna siguiente, y un párrafo se
  recorta con '...' perdiendo justamente lo que hay que leer.
* `blank_if_missing`: última barrera antes de dibujar. `str(np.nan)` da "nan" y
  `str(pd.NaT)` da "NaT"; sin este filtro esas cadenas llegan a la tabla.

Temas de marca
--------------
Las primitivas leen los colores y las fuentes de variables de módulo, y
`use_theme()` las cambia. Así el mismo `draw_table` sirve para el navy de
Sullivan y el guinda de Loco sin duplicar la función ni arrastrar un parámetro
de tema por cada llamada.
================================================================================
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

PROJECT_ROOT = Path(__file__).resolve().parent.parent

PAGE_W, PAGE_H = letter
MARGIN = 0.6 * inch
CONTENT_W = PAGE_W - 2 * MARGIN      # 7.3 in — ancho útil entre márgenes
BOTTOM_LIMIT = 0.85 * inch           # nada de contenido por debajo de aquí
                                     # (la línea de pie va en 0.5 in)

# Marca visual para un dato ausente. Nunca debe imprimirse "nan", "NaT", "None"
# ni "null": son artefactos de pandas, no información para el lector.
BLANK = "—"
_MISSING_TOKENS = {"nan", "nat", "none", "null", "undefined", "<na>", ""}


# ==============================================================================
# 1. TEMAS DE MARCA
# ==============================================================================
def _register(name: str, path: Path) -> bool:
    """Registra una fuente TTF. Devuelve si se pudo."""
    try:
        if not path.exists():
            return False
        pdfmetrics.registerFont(TTFont(name, str(path)))
        return True
    except Exception:
        return False


_SULLIVAN_FONTS = PROJECT_ROOT / "Fonts" / "Font_sullivan" / "EB_Garamond" / "static"
_LOCO_FONTS = PROJECT_ROOT / "Fonts" / "Font_loco_tequila" / "Poppins"

SULLIVAN_THEME = {
    "primary": colors.HexColor("#003057"),      # navy
    "muted": colors.HexColor("#656565"),
    "accent": colors.HexColor("#A67C52"),       # tan
    "soft": colors.HexColor("#FFFBEF"),         # cream
    "rule": colors.HexColor("#D9D9D9"),
    "negative": colors.HexColor("#8C2F2F"),
    "zebra": colors.HexColor("#FAF8F3"),
    "brand_mark": "SULLIVAN · RUTHERFORD ESTATE",
    "fonts": [("EBGaramond", _SULLIVAN_FONTS / "EBGaramond-Regular.ttf"),
              ("EBGaramond-Bold", _SULLIVAN_FONTS / "EBGaramond-Bold.ttf")],
}

# Tokens de `Designs/Design_loco_tequila.md` (los mismos que usa el dashboard).
LOCO_THEME = {
    "primary": colors.HexColor("#541424"),      # guinda
    "muted": colors.HexColor("#8C857B"),
    "accent": colors.HexColor("#C5A059"),       # oro
    "soft": colors.HexColor("#FBF8F2"),         # crema
    "rule": colors.HexColor("#E5E0D8"),
    "negative": colors.HexColor("#C0392B"),
    "zebra": colors.HexColor("#FBF8F2"),
    "brand_mark": "LOCO TEQUILA · USA",
    "fonts": [("Poppins", _LOCO_FONTS / "Poppins-Regular.ttf"),
              ("Poppins-Bold", _LOCO_FONTS / "Poppins-SemiBold.ttf")],
}

# Estado activo. Las primitivas de dibujo lo leen en cada llamada.
PRIMARY = SULLIVAN_THEME["primary"]
MUTED = SULLIVAN_THEME["muted"]
ACCENT = SULLIVAN_THEME["accent"]
SOFT = SULLIVAN_THEME["soft"]
RULE = SULLIVAN_THEME["rule"]
NEGATIVE = SULLIVAN_THEME["negative"]
ZEBRA = SULLIVAN_THEME["zebra"]
BRAND_MARK = SULLIVAN_THEME["brand_mark"]
FONT_REGULAR, FONT_BOLD = "Helvetica", "Helvetica-Bold"


def use_theme(theme: dict) -> None:
    """
    Activa un tema de marca. Si las fuentes de la marca no están en la máquina,
    cae a Helvetica en vez de fallar: un PDF con la tipografía sustituta sigue
    siendo utilizable, y el aviso queda en el log del generador.
    """
    global PRIMARY, MUTED, ACCENT, SOFT, RULE, NEGATIVE, ZEBRA, BRAND_MARK
    global FONT_REGULAR, FONT_BOLD

    PRIMARY = theme["primary"]
    MUTED = theme["muted"]
    ACCENT = theme["accent"]
    SOFT = theme["soft"]
    RULE = theme["rule"]
    NEGATIVE = theme["negative"]
    ZEBRA = theme.get("zebra", theme["soft"])
    BRAND_MARK = theme["brand_mark"]

    (reg_name, reg_path), (bold_name, bold_path) = theme["fonts"]
    if _register(reg_name, reg_path) and _register(bold_name, bold_path):
        FONT_REGULAR, FONT_BOLD = reg_name, bold_name
    else:
        FONT_REGULAR, FONT_BOLD = "Helvetica", "Helvetica-Bold"


# Compatibilidad con los nombres que ya usaba `pdf_generator.py`.
NAVY = SULLIVAN_THEME["primary"]
GRAY = SULLIVAN_THEME["muted"]
TAN = SULLIVAN_THEME["accent"]
CREAM = SULLIVAN_THEME["soft"]
RULE_LINE = SULLIVAN_THEME["rule"]
NEG = SULLIVAN_THEME["negative"]

use_theme(SULLIVAN_THEME)


# ==============================================================================
# 2. DATO AUSENTE Y FORMATO
# ==============================================================================
# ==============================================================================
#  IDIOMA
# ==============================================================================
# Un PDF no puede llevar selector como el HTML, así que se genera en UN idioma
# y `--lang` decide cuál.
#
# La traducción se aplica en DOS lugares, y no es redundancia:
#
#   * En `fit_text` / `wrap_text`, ANTES de medir. El español es entre 15% y 25%
#     más largo que el inglés; si se tradujera después de calcular el recorte,
#     la etiqueta se desbordaría sobre la columna siguiente. Midiendo el texto
#     ya traducido, el recorte y el ajuste de línea son correctos.
#   * En el propio canvas, para los `drawString` que los generadores hacen
#     directo (portadas, avisos al pie) y que no pasan por los ayudantes.
#
# Que un texto pase por los dos caminos es inofensivo porque traducir es
# idempotente: la salida en español no contiene la entrada en inglés, así que
# una segunda pasada no encuentra nada que cambiar. Hay una prueba que lo
# comprueba sobre el inventario completo de cadenas.

_HERE_I18N = Path(__file__).resolve().parent
if str(_HERE_I18N) not in sys.path:
    sys.path.insert(0, str(_HERE_I18N))
import i18n  # noqa: E402

# Alias para que los generadores no tengan que importar i18n solo por esto.
DEFAULT_LANG_PDF = i18n.DEFAULT_LANG
LANG = i18n.DEFAULT_LANG


def set_lang(lang: str) -> str:
    """Fija el idioma de toda la capa de dibujo. Devuelve el idioma normalizado."""
    global LANG
    LANG = i18n.normalize_lang(lang)
    return LANG


def _L(text):
    """
    Traduce si hay algo que traducir; deja intacto lo que no es texto.

    No se corta en `LANG == "en"`: el reporte de Loco Tequila nació con parte
    de su texto en español, así que generarlo en inglés también requiere
    traducir, en el sentido contrario.
    """
    if not isinstance(text, str) or not text:
        return text
    return i18n.t(text, LANG)


def localize_canvas(c):
    """
    Envuelve el canvas para que TODO lo que se dibuje pase por la traducción.

    Existe porque los cuatro generadores hacen 52 llamadas directas a
    `drawString` en portadas y pies. Instrumentar cada una a mano dejaría
    huecos; envolver el canvas cubre incluso las que se añadan después.
    """
    if getattr(c, "_i18n_wrapped", False):
        return c
    for name in ("drawString", "drawCentredString", "drawRightString"):
        original = getattr(c, name)

        def wrapper(x, y, text, _orig=original):
            return _orig(x, y, _L(text))

        setattr(c, name, wrapper)

    original_title = c.setTitle

    def set_title(text, _orig=original_title):
        return _orig(_L(text))

    c.setTitle = set_title
    c._i18n_wrapped = True
    return c


def blank_if_missing(value, blank: str = BLANK) -> str:
    """
    Convierte un valor a texto listo para imprimir, sustituyendo cualquier forma
    de "ausente" por `blank`. `str(np.nan)` da "nan" y `str(pd.NaT)` da "NaT":
    hacer `.astype(str)` sobre una columna con huecos mete esas cadenas en la
    tabla, que es exactamente lo que el lector no debe ver.
    """
    if value is None:
        return blank
    try:
        if isinstance(value, float) and math.isnan(value):
            return blank
        if pd.isna(value):
            return blank
    except (TypeError, ValueError):
        pass
    text = str(value).strip()
    return blank if text.lower() in _MISSING_TOKENS else text


def fmt_money(v):
    """Importe con formato. Un NaN/None devuelve BLANK, no '$nan'."""
    try:
        if v is None or pd.isna(v):
            return BLANK
        return f"${float(v):,.0f}"
    except (TypeError, ValueError):
        return BLANK


def fmt_money2(v):
    """Importe al centavo, para tablas de conciliación y de auditoría."""
    try:
        if v is None or pd.isna(v):
            return BLANK
        return f"${float(v):,.2f}"
    except (TypeError, ValueError):
        return BLANK


def fmt_num(v, dec: int = 0):
    """Número con separador de miles. Ausente -> BLANK, nunca '0' silencioso."""
    try:
        if v is None or pd.isna(v):
            return BLANK
        return f"{float(v):,.{dec}f}"
    except (TypeError, ValueError):
        return BLANK


def fmt_cases(v):
    """Cajas de 9 litros, la unidad de volumen de distribución."""
    n = fmt_num(v, 2)
    return BLANK if n == BLANK else f"{n} cs"


def fmt_pct(v, dec: int = 1):
    try:
        if v is None or pd.isna(v):
            return BLANK
        return f"{float(v):,.{dec}f}%"
    except (TypeError, ValueError):
        return BLANK


# ==============================================================================
# 3. AJUSTE DE TEXTO
# ==============================================================================
def fit_text(text, max_w, font=None, size=9):
    """
    Recorta un texto a `max_w` puntos agregando '...'. drawString no hace wrap:
    sin esto, un nombre de categoría o paquete largo se desborda encima de la
    columna siguiente.
    """
    font = font or FONT_REGULAR
    # Se traduce ANTES de medir: el español es más largo y el recorte tiene que
    # calcularse sobre el texto que realmente se va a dibujar.
    text = _L(str(text))
    if pdfmetrics.stringWidth(text, font, size) <= max_w:
        return text
    while text and pdfmetrics.stringWidth(text + "...", font, size) > max_w:
        text = text[:-1]
    return text + "..."


def wrap_text(text, max_w, font=None, size=9):
    """
    Parte un texto en líneas que caben en `max_w`. Para párrafos (no etiquetas de
    tabla) recortar con '...' pierde el mensaje: aquí se necesita ajuste de línea
    de verdad. Devuelve una lista de líneas.

    Igual que `fit_text`, traduce ANTES de partir: un párrafo en español ocupa
    más líneas que el mismo en inglés, y calcular el corte sobre el original
    dejaría la última línea fuera de la caja.
    """
    text = _L(text)
    font = font or FONT_REGULAR
    words = str(text).split()
    if not words:
        return [""]
    lines, current = [], words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if pdfmetrics.stringWidth(candidate, font, size) <= max_w:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def draw_paragraph(c, text, x, y, max_w, size=9, leading=None, font=None,
                   color=None):
    """Párrafo con ajuste de línea real. Devuelve la `y` final."""
    font = font or FONT_REGULAR
    leading = leading or size * 1.45
    c.setFont(font, size)
    c.setFillColor(color or MUTED)
    for line in wrap_text(text, max_w, font, size):
        c.drawString(x, y, line)
        y -= leading
    return y


# ==============================================================================
# 4. MAQUETACIÓN ADAPTATIVA
# ==============================================================================
def scale_widths(widths, total=None):
    """
    Escala un juego de anchos de columna para ocupar TODO el ancho útil. Las
    tablas se definían con anchos fijos que sumaban ~7.0 in contra 7.3 in
    disponibles: quedaban angostas y se leían "chicas" respecto al margen.
    """
    total = CONTENT_W if total is None else total
    s = float(sum(widths))
    if s <= 0:
        return list(widths)
    return [w * total / s for w in widths]


def auto_row_h(n_rows, top_y, min_h, max_h, reserve=0.0):
    """
    Reparte el espacio vertical disponible entre `n_rows`, acotado a
    [min_h, max_h]. Antes todo usaba alturas fijas (row_h=18/20/22), así que una
    tabla de 6 filas ocupaba 1/4 de la hoja y dejaba media página en blanco.
    `reserve` es el espacio que hay que dejar libre debajo para lo que siga
    (notas, otra sección) y así el crecimiento nunca invade el pie.
    """
    if n_rows <= 0:
        return max_h
    available = top_y - BOTTOM_LIMIT - reserve
    return max(min_h, min(max_h, available / n_rows))


def center_block(top_y, block_h):
    """
    Devuelve la `y` superior para centrar verticalmente un bloque en el espacio
    libre. Estirar filas sin límite para llenar la hoja se ve absurdo (una tabla
    de 5 filas con renglones de 100 pt), pero dejarla pegada arriba con media
    página en blanco debajo se lee como un error de maquetación. Centrarla —un
    poco por encima del centro geométrico, que es donde el ojo lo espera— se lee
    como una decisión de diseño.
    """
    free = top_y - BOTTOM_LIMIT
    if block_h >= free:
        return top_y
    return top_y - (free - block_h) * 0.38


# ==============================================================================
# 5. PRIMITIVAS DE DIBUJO
# ==============================================================================
def draw_header_band(c, title, subtitle, page_num, brand_mark=None):
    c.setFillColor(PRIMARY)
    c.rect(0, PAGE_H - 0.85 * inch, PAGE_W, 0.85 * inch, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont(FONT_BOLD, 15)
    c.drawString(MARGIN, PAGE_H - 0.5 * inch,
                 fit_text(title, CONTENT_W * 0.62, FONT_BOLD, 15))
    c.setFont(FONT_REGULAR, 9)
    c.drawString(MARGIN, PAGE_H - 0.72 * inch,
                 # Se traduce ANTES de subir a mayúsculas, igual que la
                 # etiqueta de las tarjetas: "WEEK ENDING AUG 23, 2026" no
                 # coincide con ninguna clave del diccionario.
                 fit_text(_L(str(subtitle)).upper(), CONTENT_W * 0.62,
                          FONT_REGULAR, 9))
    c.setFont(FONT_REGULAR, 9)
    c.drawRightString(PAGE_W - MARGIN, PAGE_H - 0.6 * inch,
                      brand_mark or BRAND_MARK)

    c.setStrokeColor(RULE)
    c.line(MARGIN, 0.5 * inch, PAGE_W - MARGIN, 0.5 * inch)
    c.setFillColor(MUTED)
    c.setFont(FONT_REGULAR, 8)
    c.drawRightString(PAGE_W - MARGIN, 0.32 * inch, str(page_num))


def draw_section_title(c, text, y):
    c.setFillColor(PRIMARY)
    c.setFont(FONT_BOLD, 13)
    c.drawString(MARGIN, y, fit_text(text, CONTENT_W, FONT_BOLD, 13))
    c.setStrokeColor(ACCENT)
    c.setLineWidth(1.4)
    c.line(MARGIN, y - 6, PAGE_W - MARGIN, y - 6)
    return y - 26


def draw_kpi_cards(c, cards, y, card_h=0.85 * inch, gap=0.12 * inch):
    """
    Fila de tarjetas KPI que ocupa todo el ancho útil. Antes el ancho era fijo
    (1.75 in): con 3 tarjetas quedaban 1.8 in de hueco a la derecha, y el valor
    se desbordaba si el importe era largo.

    `cards` es una lista de (etiqueta, valor, resaltar_en_rojo).
    """
    n = max(1, len(cards))
    card_w = (CONTENT_W - gap * (n - 1)) / n
    x = MARGIN
    for label, value, warn in cards:
        c.setFillColor(SOFT)
        c.setStrokeColor(RULE)
        c.roundRect(x, y - card_h, card_w, card_h, 3, fill=1, stroke=1)
        c.setFillColor(MUTED)
        c.setFont(FONT_REGULAR, 7.5)
        c.drawString(x + 9, y - 17,
                     # Se traduce ANTES de subir a mayúsculas: "TOTAL DTC SALES"
                     # no coincide con ninguna clave del diccionario.
                     fit_text(_L(str(label)).upper(), card_w - 18, FONT_REGULAR, 7.5))
        c.setFillColor(NEGATIVE if warn else PRIMARY)
        # El tamaño baja solo si el valor no cabe, en vez de desbordarse.
        size = 17.0
        while size > 9.5 and pdfmetrics.stringWidth(str(value), FONT_BOLD, size) > card_w - 18:
            size -= 0.5
        c.setFont(FONT_BOLD, size)
        c.drawString(x + 9, y - card_h + 15,
                     fit_text(str(value), card_w - 18, FONT_BOLD, size))
        x += card_w + gap
    return y - card_h - 18


def draw_horizontal_bars(c, labels, values, color_map, x, y, width, row_h=16,
                         max_value=None, value_fmt=None):
    """
    Barras horizontales. La tipografía, el grosor de la barra y el ancho de la
    columna de etiquetas se derivan de `row_h`, de modo que cuando la gráfica
    crece para llenar la página no queden barras gruesas con texto diminuto.

    `value_fmt` permite rotular en cajas 9L o en unidades en vez de en dinero;
    por omisión es dinero, que es el caso más común.

    NOTA: esta función NO reordena. El orden descendente es responsabilidad de
    quien construye los datos, porque hay series (temporales) donde reordenar
    destruiría el eje.
    """
    value_fmt = value_fmt or fmt_money
    numeric = [float(v) for v in values if v is not None and not pd.isna(v)]
    max_value = max_value or (max(numeric) if numeric else 1) or 1

    # Tipografía proporcional a la altura de fila (acotada para seguir siendo
    # legible en gráficas densas y no volverse titular en las de pocas filas).
    font_size = max(7.5, min(12.0, row_h * 0.42))
    label_w = max(1.7 * inch, min(2.4 * inch, width * 0.28))
    value_w = max(0.75 * inch, min(1.15 * inch, width * 0.14))
    bar_area_w = width - label_w - value_w
    bar_h = max(4.0, row_h * 0.62)          # deja aire entre barras
    baseline = (row_h - font_size) / 2 + font_size * 0.22

    c.setFont(FONT_REGULAR, font_size)
    for i, (lab, val) in enumerate(zip(labels, values)):
        row_y = y - i * row_h
        c.setFillColor(colors.black)
        c.drawString(x, row_y - row_h + baseline,
                     fit_text(blank_if_missing(lab), label_w - 8, FONT_REGULAR, font_size))
        try:
            num = float(val)
        except (TypeError, ValueError):
            num = 0.0
        bw = (num / max_value) * bar_area_w if max_value else 0
        c.setFillColor(color_map.get(lab, ACCENT) if isinstance(color_map, dict) else color_map)
        c.rect(x + label_w, row_y - row_h + (row_h - bar_h) / 2,
               max(bw, 1), bar_h, fill=1, stroke=0)
        c.setFillColor(MUTED)
        c.drawString(x + label_w + bar_area_w + 6, row_y - row_h + baseline,
                     value_fmt(val))
    return y - len(labels) * row_h - 10


def draw_table(c, headers, rows, x, y, col_widths, row_h=16, total_row_idx=None,
               align_right=None, zebra=True):
    """
    Tabla simple. `row_h` puede venir de auto_row_h() para llenar la página: la
    tipografía y la línea base se calculan a partir de él para que el texto no
    quede flotando diminuto dentro de filas altas.

    `align_right` es un conjunto de índices de columna a alinear a la derecha
    (las columnas de importes se leían mal pegadas a la izquierda).
    """
    align_right = align_right or set()
    total_w = sum(col_widths)
    font_size = max(7.5, min(11.0, row_h * 0.46))
    baseline = (row_h - font_size) / 2 + font_size * 0.24

    def cell(text, cx, cy, w, font, size, right):
        # blank_if_missing es la última barrera antes de dibujar: aplica a TODAS
        # las tablas del PDF, incluidas las que se agreguen después.
        txt = fit_text(blank_if_missing(text), w - 8, font, size)
        if right:
            c.drawRightString(cx + w - 4, cy, txt)
        else:
            c.drawString(cx + 4, cy, txt)

    c.setFont(FONT_BOLD, font_size)
    c.setFillColor(PRIMARY)
    c.rect(x, y - row_h, total_w, row_h, fill=1, stroke=0)
    c.setFillColor(colors.white)
    cx = x
    for i, (h, w) in enumerate(zip(headers, col_widths)):
        cell(h, cx, y - row_h + baseline, w, FONT_BOLD, font_size, i in align_right)
        cx += w
    y -= row_h

    for ridx, row in enumerate(rows):
        is_total = total_row_idx is not None and ridx == total_row_idx
        font = FONT_BOLD if is_total else FONT_REGULAR
        if is_total:
            c.setFillColor(SOFT)
            c.rect(x, y - row_h, total_w, row_h, fill=1, stroke=0)
        elif zebra and ridx % 2 == 1:
            # Bandas muy tenues: con filas altas, seguir la línea a lo ancho de
            # 7.3 in a ojo es incómodo.
            c.setFillColor(ZEBRA)
            c.rect(x, y - row_h, total_w, row_h, fill=1, stroke=0)
        c.setFont(font, font_size)
        c.setFillColor(colors.black)
        cx = x
        for i, (val, w) in enumerate(zip(row, col_widths)):
            cell(val, cx, y - row_h + baseline, w, font, font_size, i in align_right)
            cx += w
        c.setStrokeColor(RULE)
        c.line(x, y - row_h, x + total_w, y - row_h)
        y -= row_h
    return y


def draw_note(c, text, y, size=8.5, pad=9):
    """
    Nota al pie de una sección, con ajuste de línea y una barra de acento.
    Antes estos párrafos se dibujaban con drawString y se recortaban con '...',
    perdiendo justo la parte que pedía una acción.
    """
    lines = wrap_text(text, CONTENT_W - 2 * pad - 6, FONT_REGULAR, size)
    leading = size * 1.42
    box_h = len(lines) * leading + pad * 1.4
    c.setFillColor(SOFT)
    c.rect(MARGIN, y - box_h, CONTENT_W, box_h, fill=1, stroke=0)
    c.setFillColor(ACCENT)
    c.rect(MARGIN, y - box_h, 3, box_h, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#4A3B2C"))
    c.setFont(FONT_REGULAR, size)
    ty = y - pad - size * 0.9
    for line in lines:
        c.drawString(MARGIN + pad + 6, ty, line)
        ty -= leading
    return y - box_h - 10


def draw_empty_state(c, message, y):
    """Estado vacío explícito. Una página en blanco parece un error; una que
    dice por qué está vacía es información."""
    c.setFillColor(MUTED)
    c.setFont(FONT_REGULAR, 11)
    lines = wrap_text(message, CONTENT_W * 0.7, FONT_REGULAR, 11)
    ty = center_block(y, len(lines) * 16)
    for line in lines:
        c.drawCentredString(PAGE_W / 2, ty, line)
        ty -= 16
    return ty - 10


def logo_data(brand: str = "sullivan"):
    """
    Logotipo en PNG para embeber. Devuelve `None` si no se puede rasterizar
    (falta cairosvg o el archivo): el PDF sale sin logo, no falla.
    """
    icons = PROJECT_ROOT / "Imagenes_iconos"
    candidates = {
        "sullivan": [icons / "Sullivan-White.png", icons / "Sullivan-Black.png"],
        "loco": [icons / "Loco_Tequila_Logo_white.png"],
        "sttupa": [icons / "Stupa-White.png", icons / "Stupa-Black.png"],
    }
    for p in candidates.get(brand, []):
        if p.exists():
            return str(p)
    return None
