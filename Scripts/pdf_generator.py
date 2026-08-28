"""
================================================================================
 SULLIVAN RUTHERFORD ESTATE — GENERADOR BASE DE PDF (Vista A + Vista B)
================================================================================
Genera el PDF directivo acordado con la estructura reducida (no la de 25-35
páginas del patrón genérico, pensada para catálogos de muchos SKUs — aquí son
9 categorías + 6 paquetes de club, así que basta con 9 páginas):

    1. Portada (con sello de reconciliación)
    2. Resumen ejecutivo (Vista A) — barras horizontales, 9 categorías
    3. Cascada de clasificación + glosario de las 9 categorías
    4. Detalle por categoría (tabla comparativa)
    5. Reconciliación financiera + diagnósticos + checklist de 10 puntos
    6. Club Deep Dive (Vista B): KPIs, barras por paquete y tabla con AOV
    7. Casos de revisión (Admin/POS Marked as Club)
    8. Apéndice / metodología

El alto de filas, el tamaño de tipografía y los anchos de columna se calculan a
partir del espacio disponible en cada página (ver auto_row_h / scale_widths /
center_block): con medidas fijas, una tabla de 6 filas ocupaba un cuarto de la
hoja y dejaba el resto en blanco.

Reutiliza la MISMA función de clasificación que dashboard_generator.py
(duplicada aquí a propósito para que cada script sea autocontenido, tal
como se pidió: "los 2 archivos" sin módulo compartido).

Uso:
    python pdf_generator.py \
        --order-sales "Client_Data/Sullivan_data/Apr_OrderSales.xlsx" \
        --financial-report "Client_Data/Sullivan_data/Apr_FinancialReport.xlsx" \
        --period-label "April 2026" \
        --output "Data_for_demo/sullivan_report.pdf"

Requiere: reportlab (pip install reportlab)
================================================================================
"""

import argparse
import math
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ==============================================================================
# 0. RUTAS DE MARCA Y TOKENS (idénticos a Design_sullivan.md)
# ==============================================================================
PROJECT_ROOT = Path(__file__).resolve().parent.parent
FONT_DIR = PROJECT_ROOT / "Fonts" / "Font_sullivan" / "EB_Garamond" / "static"

NAVY = colors.HexColor("#003057")
GRAY = colors.HexColor("#656565")
TAN = colors.HexColor("#A67C52")
CREAM = colors.HexColor("#FFFBEF")
RULE_LINE = colors.HexColor("#D9D9D9")
NEG = colors.HexColor("#8C2F2F")
PAGE_W, PAGE_H = letter

CATEGORY_COLORS = {
    "Telesales": colors.HexColor("#003057"), "Event": colors.HexColor("#2C4F73"),
    "Corporate": colors.HexColor("#55698C"), "Friends & Family": colors.HexColor("#7E85A5"),
    "Tock": colors.HexColor("#A7A1BE"), "Web / Ecommerce": colors.HexColor("#A67C52"),
    "Tasting Room": colors.HexColor("#C79F6C"), "Estate Club": colors.HexColor("#8C2F2F"),
    "Founder's Club": colors.HexColor("#451B0F"), "Club - Review (Admin/POS)": colors.HexColor("#656565"),
}
CATEGORY_ORDER = list(CATEGORY_COLORS.keys())

# Filas que NO forman parte de la cascada de 9 prioridades: existen solo para que
# el total cuadre al centavo y para que nada quede fuera del reporte en silencio.
DIAGNOSTIC_CATEGORIES = ("Club - Review (Admin/POS)", "Unassigned")

# Glosario de las 9 categorías finales — un lector directivo no tiene por qué
# adivinar qué distingue "Telesales" de "Tock". Se imprime en el PDF y se
# muestra en el dashboard.
CATEGORY_GLOSSARY = [
    ("Event", "Inbound order tagged as a private/trade event."),
    ("Corporate", "Inbound order tagged as a corporate gifting account."),
    ("Friends & Family", "Inbound order tagged Friends & Family (comped or discounted)."),
    ("Telesales", "Remaining Inbound: phone / concierge sales taken by the team."),
    ("Tock", "Web order booked through the Tock reservation platform."),
    ("Web / Ecommerce", "Remaining Web: self-service purchases on the online store."),
    ("Tasting Room", "Any POS order rung up on site at the estate."),
    ("Estate Club", "Club shipment on an Estate program (4 or 6 bottle)."),
    ("Founder's Club", "Club shipment on a Founder's program (3 bottle to double case)."),
]

CLUB_PACKAGE_COLORS = {
    "Estate 4 Bottle": colors.HexColor("#8C2F2F"), "Estate 6 Bottle": colors.HexColor("#B24B4B"),
    "Founder's 3 Bottle": colors.HexColor("#451B0F"), "Founder's Half Case": colors.HexColor("#6B2C1B"),
    "Founder's Single Case": colors.HexColor("#8C4A2E"), "Founder's Double Case": colors.HexColor("#A6673F"),
}

FONT_REGULAR, FONT_BOLD = "Helvetica", "Helvetica-Bold"  # fallback
try:
    pdfmetrics.registerFont(TTFont("EBGaramond", str(FONT_DIR / "EBGaramond-Regular.ttf")))
    pdfmetrics.registerFont(TTFont("EBGaramond-Bold", str(FONT_DIR / "EBGaramond-Bold.ttf")))
    FONT_REGULAR, FONT_BOLD = "EBGaramond", "EBGaramond-Bold"
except Exception:
    pass  # cae a Helvetica si no están los .ttf en esta máquina


# ==============================================================================
# 1. CLASIFICACIÓN (idéntica a dashboard_generator.py — ver ese archivo para
#    el detalle de por qué Event/Corporate/F&F dependen de una columna de
#    Order Tag que el export real no trae)
# ==============================================================================
def classify_orders(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    channel = d.get("Channel", pd.Series("", index=d.index)).fillna("").str.strip().str.lower()
    vendor = d.get("External Order Vendor", pd.Series("", index=d.index)).fillna("").str.strip().str.lower()
    club_title = d.get("Club Title", pd.Series("", index=d.index)).fillna("").astype(str).str.strip()
    club_package = d.get("Club Package", pd.Series("", index=d.index)).fillna("").astype(str)

    tag_col = next((c for c in ("Order Tag", "Order Tags") if c in d.columns), None)
    tags = d[tag_col].fillna("").astype(str) if tag_col else pd.Series("", index=d.index)

    cond_event = (channel == "inbound") & tags.str.contains("Event", case=False)
    cond_corp = (channel == "inbound") & tags.str.contains("Corporate", case=False)
    cond_ff = (channel == "inbound") & tags.str.contains("Friends & Family|Friends and Family", case=False)
    cond_tele = (channel == "inbound")
    cond_tock = (channel == "web") & (vendor == "tock")
    cond_web = (channel == "web")
    cond_pos = (channel == "pos")
    is_club = channel == "club"
    # Prioridades 8 y 9: se exige coincidencia EXPLÍCITA por nombre de programa
    # (no residual), tal como está especificado en Sullivan_data_guide.md. Todo
    # renglón de Club que no nombre ni "Estate" ni "Founder" cae en la fila
    # diagnóstica de revisión en vez de inflar Founder's Club en silencio.
    club_name = (club_title + " " + club_package)
    cond_estate = is_club & club_name.str.contains("Estate", case=False, regex=False)
    cond_founders = is_club & ~cond_estate & club_name.str.contains("Founder", case=False, regex=False)
    cond_club_review = is_club & ~cond_estate & ~cond_founders

    conditions = [cond_event, cond_corp, cond_ff, cond_tele, cond_tock, cond_web,
                  cond_pos, cond_estate, cond_founders, cond_club_review]
    choices = ["Event", "Corporate", "Friends & Family", "Telesales", "Tock",
               "Web / Ecommerce", "Tasting Room", "Estate Club", "Founder's Club",
               "Club - Review (Admin/POS)"]
    d["Final Category"] = np.select(conditions, choices, default="Unassigned")

    def package_group(pkg):
        p = pkg.lower()
        if "estate" in p:
            # Ojo: el nombre incluye el año (ej. "April 2026 Estate 4"); no basta
            # con buscar "6" en todo el string (2026 ya tiene un 6).
            m = re.search(r"estate\s*(\d+)", p)
            return "Estate 6 Bottle" if (m and m.group(1) == "6") else "Estate 4 Bottle"
        if "3 bottle" in p: return "Founder's 3 Bottle"
        if "half" in p: return "Founder's Half Case"
        if "single" in p: return "Founder's Single Case"
        if "double" in p: return "Founder's Double Case"
        return ""
    d["Club Package Group"] = club_package.map(package_group)
    return d


def warn(msg: str):
    """Aviso visible en consola (stderr) — los descuadres silenciosos son el
    riesgo #1 de este reporte, así que todo supuesto se anuncia."""
    print(f"  [AVISO] {msg}", file=sys.stderr)


def coerce_money(s: pd.Series) -> pd.Series:
    """
    Normaliza una columna de montos a float. Un export .csv de Commerce7 trae
    los importes como TEXTO ("$1,234.00", "(45.00)" para negativos); sin esta
    normalización `.sum()` concatena strings o devuelve NaN en silencio y el
    cuadre financiero se cae sin diagnóstico.
    """
    if pd.api.types.is_numeric_dtype(s):
        return pd.to_numeric(s, errors="coerce").fillna(0.0).astype(float)
    t = s.astype(str).str.strip()
    negative = t.str.startswith("(") & t.str.endswith(")")
    t = t.str.replace(r"[^0-9.\-]", "", regex=True)
    out = pd.to_numeric(t, errors="coerce").fillna(0.0)
    return out.where(~negative, -out.abs())


# Base económica canónica del reporte: venta neta a NIVEL ÍTEM, sin impuestos ni
# flete. En el export de OrderSales esa columna es 'Product SubTotal'; 'SubTotal'
# ahí es un total de ORDEN repetido en cada renglón de ítem (sumarlo duplica) y
# 'Total' incluye impuestos y envío. En el FinancialReport, en cambio, 'SubTotal'
# ya es de nivel ítem — por eso cada lado tiene su propio resolvedor y ambos se
# etiquetan en el reporte para que el lector sepa qué se comparó.
SALES_MONEY_COLS = ("Product SubTotal", "SubTotal", "Sub Total")
FINANCIAL_MONEY_COLS = ("SubTotal", "Sub Total", "Product SubTotal")


def money_col(d):
    if "Product SubTotal" in d.columns:
        return "Product SubTotal"
    for c in ("Sub Total", "SubTotal"):
        if c in d.columns:
            warn(f"'Product SubTotal' no está en el archivo de ventas; se usa '{c}'. "
                 "Si ese campo es un total por ORDEN repetido por ítem, el total DTC "
                 "quedará inflado y el cuadre fallará. Verifica la base antes de publicar.")
            return c
    raise KeyError(
        "No se encontró columna de monto a nivel ítem. Se esperaba una de: "
        + ", ".join(SALES_MONEY_COLS)
    )


def financial_money_col(fin):
    for c in FINANCIAL_MONEY_COLS:
        if c in fin.columns:
            return c
    return None


def fit_text(text, max_w, font, size):
    """
    Recorta un texto a `max_w` puntos agregando '...'. drawString no hace wrap:
    sin esto, un nombre de categoría o paquete largo se desborda encima de la
    columna siguiente.
    """
    text = str(text)
    if pdfmetrics.stringWidth(text, font, size) <= max_w:
        return text
    while text and pdfmetrics.stringWidth(text + "...", font, size) > max_w:
        text = text[:-1]
    return text + "..."


def wrap_text(text, max_w, font, size):
    """
    Parte un texto en líneas que caben en `max_w`. Para párrafos (no etiquetas de
    tabla) recortar con '...' pierde el mensaje: aquí se necesita ajuste de línea
    de verdad. Devuelve una lista de líneas.
    """
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


# ==============================================================================
# 2. HELPERS DE DIBUJO (banda navy, tabla, gráfica de barras horizontales)
# ==============================================================================
MARGIN = 0.6 * inch
CONTENT_W = PAGE_W - 2 * MARGIN      # 7.3 in — ancho útil entre márgenes
BOTTOM_LIMIT = 0.85 * inch           # nada de contenido por debajo de aquí
                                     # (la línea de pie va en 0.5 in)


# Marca visual para un dato ausente. Nunca debe imprimirse "nan", "NaT", "None"
# ni "null": son artefactos de pandas, no información para el lector.
BLANK = "—"

_MISSING_TOKENS = {"nan", "nat", "none", "null", "undefined", "<na>", ""}


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


def draw_header_band(c, title, subtitle, page_num):
    c.setFillColor(NAVY)
    c.rect(0, PAGE_H - 0.85 * inch, PAGE_W, 0.85 * inch, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont(FONT_BOLD, 15)
    c.drawString(0.6 * inch, PAGE_H - 0.5 * inch, title)
    c.setFont(FONT_REGULAR, 9)
    c.drawString(0.6 * inch, PAGE_H - 0.72 * inch, subtitle.upper())
    c.setFont(FONT_REGULAR, 9)
    c.drawRightString(PAGE_W - 0.6 * inch, PAGE_H - 0.6 * inch, "SULLIVAN · RUTHERFORD ESTATE")

    c.setStrokeColor(RULE_LINE)
    c.line(0.6 * inch, 0.5 * inch, PAGE_W - 0.6 * inch, 0.5 * inch)
    c.setFillColor(GRAY)
    c.setFont(FONT_REGULAR, 8)
    c.drawRightString(PAGE_W - 0.6 * inch, 0.32 * inch, str(page_num))


def draw_section_title(c, text, y):
    c.setFillColor(NAVY)
    c.setFont(FONT_BOLD, 13)
    c.drawString(0.6 * inch, y, text)
    c.setStrokeColor(TAN)
    c.setLineWidth(1.4)
    c.line(0.6 * inch, y - 6, PAGE_W - 0.6 * inch, y - 6)
    return y - 26


def draw_kpi_cards(c, cards, y, card_h=0.85 * inch, gap=0.12 * inch):
    """
    Fila de tarjetas KPI que ocupa todo el ancho útil. Antes el ancho era fijo
    (1.75 in): con 3 tarjetas quedaban 1.8 in de hueco a la derecha, y el valor
    se desbordaba si el importe era largo.
    """
    n = max(1, len(cards))
    card_w = (CONTENT_W - gap * (n - 1)) / n
    x = MARGIN
    for label, value, warn in cards:
        c.setFillColor(CREAM)
        c.setStrokeColor(RULE_LINE)
        c.roundRect(x, y - card_h, card_w, card_h, 3, fill=1, stroke=1)
        c.setFillColor(GRAY)
        c.setFont(FONT_REGULAR, 7.5)
        c.drawString(x + 9, y - 17, fit_text(label.upper(), card_w - 18, FONT_REGULAR, 7.5))
        c.setFillColor(NEG if warn else NAVY)
        # El tamaño baja solo si el valor no cabe, en vez de desbordarse.
        size = 17.0
        while size > 9.5 and pdfmetrics.stringWidth(str(value), FONT_BOLD, size) > card_w - 18:
            size -= 0.5
        c.setFont(FONT_BOLD, size)
        c.drawString(x + 9, y - card_h + 15, fit_text(value, card_w - 18, FONT_BOLD, size))
        x += card_w + gap
    return y - card_h - 18


def draw_horizontal_bars(c, labels, values, color_map, x, y, width, row_h=16, max_value=None):
    """
    Barras horizontales. La tipografía, el grosor de la barra y el ancho de la
    columna de etiquetas se derivan de `row_h`, de modo que cuando la gráfica
    crece para llenar la página no queden barras gruesas con texto diminuto.
    """
    max_value = max_value or (max(values) if values else 1)
    max_value = max_value or 1

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
        bw = (val / max_value) * bar_area_w if max_value else 0
        c.setFillColor(color_map.get(lab, TAN))
        c.rect(x + label_w, row_y - row_h + (row_h - bar_h) / 2, max(bw, 1), bar_h, fill=1, stroke=0)
        c.setFillColor(GRAY)
        c.drawString(x + label_w + bar_area_w + 6, row_y - row_h + baseline, fmt_money(val))
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
    c.setFillColor(NAVY)
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
            c.setFillColor(CREAM)
            c.rect(x, y - row_h, total_w, row_h, fill=1, stroke=0)
        elif zebra and ridx % 2 == 1:
            # Bandas muy tenues: con filas altas, seguir la línea a lo ancho de
            # 7.3 in a ojo es incómodo.
            c.setFillColor(colors.HexColor("#FAF8F3"))
            c.rect(x, y - row_h, total_w, row_h, fill=1, stroke=0)
        c.setFont(font, font_size)
        c.setFillColor(colors.black)
        cx = x
        for i, (val, w) in enumerate(zip(row, col_widths)):
            cell(val, cx, y - row_h + baseline, w, font, font_size, i in align_right)
            cx += w
        c.setStrokeColor(RULE_LINE)
        c.line(x, y - row_h, x + total_w, y - row_h)
        y -= row_h
    return y


# ==============================================================================
# 3. PÁGINAS
# ==============================================================================
def page_cover(c, period_label, total_dtc, reconciliation):
    c.setFillColor(NAVY)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont(FONT_BOLD, 30)
    c.drawCentredString(PAGE_W / 2, PAGE_H - 3 * inch, "SULLIVAN")
    c.setFont(FONT_REGULAR, 13)
    c.drawCentredString(PAGE_W / 2, PAGE_H - 3.35 * inch, "R U T H E R F O R D   E S T A T E")
    c.setFont(FONT_BOLD, 18)
    c.drawCentredString(PAGE_W / 2, PAGE_H - 4.3 * inch, "DTC Sales & Reconciliation Report")
    c.setFont(FONT_REGULAR, 12)
    c.drawCentredString(PAGE_W / 2, PAGE_H - 4.65 * inch, period_label)

    match = reconciliation.get("match")
    banner_color = colors.HexColor("#1E4E2E") if match else (NEG if match is False else GRAY)
    c.setFillColor(banner_color)
    c.roundRect(PAGE_W / 2 - 2.2 * inch, PAGE_H - 5.7 * inch, 4.4 * inch, 0.7 * inch, 4, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont(FONT_BOLD, 11)
    status = "RECONCILED — Total DTC matches Net Sales" if match else \
             ("DISCREPANCY DETECTED — review classification" if match is False else "Net Sales reference not provided")
    c.drawCentredString(PAGE_W / 2, PAGE_H - 5.32 * inch, status)
    c.setFont(FONT_REGULAR, 9)
    c.drawCentredString(PAGE_W / 2, PAGE_H - 5.52 * inch, f"Total DTC: {fmt_money(total_dtc)}")
    c.showPage()


def page_executive_summary(c, vista_a, page_num):
    diag = [cat for cat in vista_a["categories"] if cat in DIAGNOSTIC_CATEGORIES]
    subtitle = "DTC Reconciliation — 9 final categories" + (
        f" + {len(diag)} diagnostic row(s)" if diag else "")
    draw_header_band(c, "Executive Summary", subtitle, page_num)
    y = PAGE_H - 1.15 * inch
    y = draw_kpi_cards(c, [
        ("Total DTC", fmt_money(vista_a["total_dtc"]), False),
        # Órdenes ÚNICAS del periodo: sumar el nunique por categoría contaría
        # dos veces una orden con ítems en categorías distintas.
        ("Total Orders", f"{vista_a['total_orders']:,}", False),
        ("Categories", f"{len(vista_a['categories']) - len(diag)} + {len(diag)} diag." if diag
         else str(len(vista_a["categories"])), False),
    ], y)
    y = draw_section_title(c, "Net Sales by Final Category", y - 10)
    color_map = {k: CATEGORY_COLORS.get(k, TAN) for k in vista_a["categories"]}
    # La gráfica se estira para ocupar el alto libre: con row_h fijo en 22 las
    # 10 categorías usaban 220 de ~570 pt y dejaban media hoja en blanco.
    row_h = auto_row_h(len(vista_a["categories"]), y, 22, 46,
                       reserve=30 if diag else 0)
    y = draw_horizontal_bars(c, vista_a["categories"], vista_a["subtotal"], color_map,
                             MARGIN, y, CONTENT_W, row_h=row_h)
    if diag:
        c.setFillColor(GRAY)
        c.setFont(FONT_REGULAR, 8)
        c.drawString(MARGIN, y - 6,
                     "Diagnostic rows (" + ", ".join(diag) + ") are not part of the 9-priority "
                     "cascade; they are shown so the total reconciles to the cent.")
    c.showPage()


def page_classification_cascade(c, page_num):
    draw_header_band(c, "Classification Logic", "Cascade rules applied top to bottom", page_num)
    y = PAGE_H - 1.2 * inch
    rows = [
        ("1", "Inbound", "Tag = Event", "Event"),
        ("2", "Inbound", "Tag = Corporate", "Corporate"),
        ("3", "Inbound", "Tag = Friends & Family", "Friends & Family"),
        ("4", "Inbound", "remainder", "Telesales"),
        ("5", "Web", "Vendor = Tock", "Tock"),
        ("6", "Web", "remainder", "Web / Ecommerce"),
        ("7", "POS", "any", "Tasting Room"),
        ("8", "Club", "Club name contains 'Estate'", "Estate Club"),
        ("9", "Club", "Club name contains \"Founder\"", "Founder's Club"),
        ("—", "Club", "names neither program (diagnostic)", "Club - Review (Admin/POS)"),
    ]
    # El glosario va debajo, así que la tabla solo puede crecer hasta dejarle
    # espacio: 2 notas + título de sección + una fila de glosario por categoría.
    glossary_h = 26 + len(CATEGORY_GLOSSARY) * 17 + 10
    row_h = auto_row_h(len(rows) + 1, y, 20, 30, reserve=glossary_h + 44)
    y = draw_table(c, ["Priority", "Channel", "Identifier", "Final Category"], rows,
                   MARGIN, y, scale_widths([0.8 * inch, 1.3 * inch, 3.2 * inch, 1.7 * inch]),
                   row_h=row_h)
    c.setFillColor(GRAY)
    c.setFont(FONT_REGULAR, 8)
    c.drawString(MARGIN, y - 14,
                 "The cascade is exclusive and evaluated top to bottom: one order line lands in "
                 "exactly one category, so no revenue is double counted.")
    c.drawString(MARGIN, y - 26,
                 "The last row is a diagnostic bucket, not a 10th sales category.")

    y = draw_section_title(c, "Glossary — what each category means", y - 48)
    for i, (name, desc) in enumerate(CATEGORY_GLOSSARY):
        row_y = y - i * 17
        c.setFillColor(CATEGORY_COLORS.get(name, TAN))
        c.rect(MARGIN, row_y - 2, 8, 8, fill=1, stroke=0)
        c.setFillColor(colors.black)
        c.setFont(FONT_BOLD, 8.5)
        c.drawString(MARGIN + 14, row_y, name)
        c.setFillColor(GRAY)
        c.setFont(FONT_REGULAR, 8.5)
        desc_x = MARGIN + 1.6 * inch
        c.drawString(desc_x, row_y, fit_text(desc, PAGE_W - MARGIN - desc_x, FONT_REGULAR, 8.5))
    c.showPage()


def page_category_detail(c, vista_a, page_num):
    draw_header_band(c, "Detail by Category", "Orders, Sub Total, % of Sales", page_num)
    y = PAGE_H - 1.2 * inch
    rows = [
        (cat, f"{o:,}", fmt_money(s), f"{p}%")
        for cat, o, s, p in zip(vista_a["categories"], vista_a["orders"], vista_a["subtotal"], vista_a["pct"])
    ]
    rows.append(("TOTAL DTC", f"{vista_a['total_orders']:,}", fmt_money(vista_a["total_dtc"]), "100%"))
    row_h = auto_row_h(len(rows) + 1, y, 18, 34, reserve=30)
    y = draw_table(c, ["Category", "Orders", "Net Sales", "% of Sales"], rows,
                   MARGIN, y, scale_widths([2.9 * inch, 1.2 * inch, 1.6 * inch, 1.6 * inch]),
                   row_h=row_h, total_row_idx=len(rows) - 1, align_right={1, 2, 3})
    c.setFillColor(GRAY)
    c.setFont(FONT_REGULAR, 8)
    c.drawString(MARGIN, y - 14,
                 "Orders are unique order counts. The TOTAL row counts each order once, so it can "
                 "be lower than the sum of the rows when an order spans several categories.")
    c.showPage()


def page_financial_reconciliation(c, vista_a, reconciliation, diagnostics, page_num):
    draw_header_band(c, "Financial Reconciliation", "Total DTC vs Net Sales (Financial Report)", page_num)
    y = PAGE_H - 1.2 * inch
    net = reconciliation.get("net_sales_financial")
    diff = round(vista_a["total_dtc"] - net, 2) if net is not None else None
    rows = [
        (f"Total DTC (classified) — basis: OrderSales.{reconciliation.get('sales_basis', 'n/a')}",
         f"${vista_a['total_dtc']:,.2f}"),
        (f"Net Sales — Financial Report — basis: {reconciliation.get('financial_basis') or 'n/a'}",
         f"${net:,.2f}" if net is not None else "n/a"),
        ("Difference (must be $0.00)", f"${diff:,.2f}" if diff is not None else "n/a"),
    ]
    y = draw_table(c, ["Metric", "Value"], rows, MARGIN, y,
                   scale_widths([4.6 * inch, 1.7 * inch]), row_h=26,
                   align_right={1}, zebra=False) - 16
    c.setFillColor(GRAY)
    c.setFont(FONT_REGULAR, 8)
    c.drawString(MARGIN, y,
                 "Both sides are compared on the same economic basis: item-level net sales, "
                 "excluding tax, shipping and tips. Match is evaluated to the cent (zero tolerance).")
    y -= 22

    if diagnostics.get("unassigned_rows") or diagnostics.get("review_rows"):
        y = draw_section_title(c, "Diagnostics — lines outside the 9 categories", y)
        c.setFont(FONT_REGULAR, 9)
        c.setFillColor(colors.black)
        c.drawString(0.7 * inch, y,
                     f"Unclassified lines (Unassigned): {diagnostics.get('unassigned_rows', 0):,}  ·  "
                     f"{fmt_money(diagnostics.get('unassigned_subtotal', 0.0))}")
        c.drawString(0.7 * inch, y - 14,
                     f"Club lines flagged for review: {diagnostics.get('review_rows', 0):,}  ·  "
                     f"{fmt_money(diagnostics.get('review_subtotal', 0.0))}")
        c.setFillColor(GRAY)
        c.setFont(FONT_REGULAR, 8)
        c.drawString(0.7 * inch, y - 28,
                     "These lines are included in Total DTC so the reconciliation stays exact; "
                     "they still need a business decision before the next close.")
        y -= 48

    y = draw_section_title(c, "Final Checklist (Sullivan_data_guide.md)", y)
    checklist = [
        "Same reporting period across all exports", "One Order ID counted once",
        "Inbound split before Telesales", "Tock subtracted from Web/Ecommerce",
        "Every POS order mapped to Tasting Room", "Club orders split Estate/Founder's",
        "No order in more than one final category", "Refunds treated consistently",
        "Net Sales compared like-for-like", "Final sum reconciles to the cent",
    ]
    # El checklist reparte el alto restante en vez de quedar apelotonado arriba
    # con 15 pt fijos y media hoja vacía debajo.
    lead = auto_row_h(len(checklist), y, 15, 26)
    c.setFont(FONT_REGULAR, max(9.0, min(11.0, lead * 0.46)))
    for i, item in enumerate(checklist):
        c.setFillColor(colors.black)
        c.drawString(MARGIN + 0.1 * inch, y - i * lead, f"[ ]  {i + 1}. {item}")
    c.showPage()


def page_club_deep_dive(c, vista_b, page_num):
    """
    Gráfica de barras y tabla por paquete EN LA MISMA PÁGINA. Antes eran dos
    páginas: la de barras usaba ~1/4 de la hoja y la de la tabla ~2/5, cada una
    con medio pliego en blanco. Son el mismo dato (una es la lectura visual y la
    otra la numérica), así que juntas llenan la página y se leen mejor.
    """
    draw_header_band(c, "Club Deep Dive", "Estate vs Founder's — by package", page_num)
    y = PAGE_H - 1.15 * inch
    total = vista_b["estate_total"] + vista_b["founders_total"]
    y = draw_kpi_cards(c, [
        ("Estate Club", fmt_money(vista_b["estate_total"]), False),
        ("Founder's Club", fmt_money(vista_b["founders_total"]), False),
        ("Combined Club", fmt_money(total), False),
    ], y)

    packages = vista_b["packages"]
    rows = [
        (p, f"{o:,}", fmt_money(s), fmt_money(a))
        for p, o, s, a in zip(packages, vista_b["orders"], vista_b["subtotal"], vista_b["aov"])
    ]
    total_orders = sum(vista_b["orders"])
    total_sub = sum(vista_b["subtotal"])
    rows.append(("TOTAL CLUB", f"{total_orders:,}", fmt_money(total_sub),
                 fmt_money(total_sub / total_orders if total_orders else 0)))

    # El alto libre se reparte entre las dos piezas: ~52 % para las barras y el
    # resto para la tabla. El "overhead" descuenta EXACTAMENTE lo que consumen
    # los dos títulos de sección (26 pt cada uno más su separación) y los 10 pt
    # de cierre que devuelve draw_horizontal_bars, para que la suma nunca invada
    # el pie de página.
    TITLE_H = 26
    overhead = (10 + TITLE_H) + 10 + (14 + TITLE_H)
    free = y - BOTTOM_LIMIT - overhead
    bars_h = free * 0.52
    table_h = free - bars_h
    bar_row_h = max(20.0, min(44.0, bars_h / max(1, len(packages))))
    tab_row_h = max(17.0, min(28.0, table_h / max(1, len(rows) + 1)))

    y = draw_section_title(c, "Net Sales by Package", y - 10)
    color_map = {p: CLUB_PACKAGE_COLORS.get(p, TAN) for p in packages}
    y = draw_horizontal_bars(c, packages, vista_b["subtotal"], color_map,
                             MARGIN, y, CONTENT_W, row_h=bar_row_h)

    y = draw_section_title(c, "Detail by Package — orders, net sales, AOV", y - 14)
    draw_table(c, ["Package", "Orders", "Net Sales", "Avg Order Value"], rows,
               MARGIN, y, scale_widths([2.6 * inch, 1.2 * inch, 1.7 * inch, 1.8 * inch]),
               row_h=tab_row_h, total_row_idx=len(rows) - 1, align_right={1, 2, 3})
    c.showPage()


def page_club_review_cases(c, vista_b, total_dtc, page_num):
    """
    Órdenes de canal Club que no nombran ni el programa Estate ni el Founder's.
    La página se conserva a propósito: es venta REAL incluida en el Total DTC pero
    sin programa asignado, así que alguien tiene que decidir a dónde va. Sin esta
    página nadie sabría que esas órdenes existen.

    La nota, la tabla y el total se maquetan como UN SOLO bloque centrado. Antes
    la nota quedaba pegada arriba y la tabla se centraba por separado, dejando un
    hueco enorme entre ambas que se leía como un error de maquetación.
    """
    draw_header_band(c, "Club Deep Dive",
                     "Review cases — Club orders with no program assigned", page_num)
    top = PAGE_H - 1.2 * inch
    cases = vista_b["review_cases"]

    if not cases:
        c.setFont(FONT_REGULAR, 10.5)
        c.setFillColor(GRAY)
        c.drawString(MARGIN, top - 10,
                     "No review cases detected in this period — every Club order maps to the "
                     "Estate or Founder's program.")
        c.showPage()
        return

    headers = list(cases[0].keys())
    rows = [[str(v) for v in case.values()] for case in cases]
    review_total = vista_b.get("review_total", 0.0)
    share = (review_total / total_dtc * 100) if total_dtc else 0.0
    rows.append(["TOTAL"] + [""] * (len(headers) - 2) + [fmt_money(review_total)])

    # Anchos proporcionales al contenido real de cada columna (antes todas
    # iguales: la de importes sobraba y la de fecha se quedaba corta).
    weights = []
    for i in range(len(headers)):
        longest = max([len(str(headers[i]))] + [len(r[i]) for r in rows])
        weights.append(max(6, min(26, longest)))
    money_cols = {i for i, h in enumerate(headers) if h in ("Net Sales", "SubTotal")}

    intro = ("Club-channel orders whose Club Title and Club Package name neither the Estate nor "
             "the Founder's program.")
    action = (f"These {len(cases)} orders total {fmt_money(review_total)} ({share:.2f}% of Total "
              "DTC). They are counted in Total DTC so the reconciliation stays exact to the cent, "
              "but still need a decision on which program they belong to.")

    # Ambos párrafos se ajustan a línea (no se recortan): el de acción mide ~180
    # caracteres y con fit_text se perdía justo la parte que pide la decisión.
    intro_lines = wrap_text(intro, CONTENT_W, FONT_REGULAR, 8.5)
    action_w = CONTENT_W - 1.05 * inch
    action_lines = wrap_text(action, action_w, FONT_REGULAR, 8.5)

    # Alto real del bloque completo (nota + tabla + bloque de acción) para poder
    # centrarlo como una sola pieza.
    reserve = 24 + len(action_lines) * 12 + len(intro_lines) * 12
    row_h = auto_row_h(len(rows) + 1, top, 20, 30, reserve=reserve)
    block_h = (len(intro_lines) * 12 + 4
               + (len(rows) + 1) * row_h
               + 18 + len(action_lines) * 12)
    y = center_block(top, block_h)

    c.setFillColor(GRAY)
    c.setFont(FONT_REGULAR, 8.5)
    for line in intro_lines:
        c.drawString(MARGIN, y, line)
        y -= 12
    y -= 4

    y = draw_table(c, headers, rows, MARGIN, y, scale_widths(weights),
                   row_h=row_h, total_row_idx=len(rows) - 1, align_right=money_cols)

    y -= 18
    c.setFillColor(NAVY)
    c.setFont(FONT_BOLD, 8.5)
    c.drawString(MARGIN, y, "Action required")
    c.setFillColor(GRAY)
    c.setFont(FONT_REGULAR, 8.5)
    for line in action_lines:
        c.drawString(MARGIN + 1.05 * inch, y, line)
        y -= 12
    c.showPage()


def page_appendix(c, page_num, data_note):
    draw_header_band(c, "Appendix", "Methodology & sources", page_num)
    y = PAGE_H - 1.2 * inch
    c.setFont(FONT_REGULAR, 9.5)
    lines = [
        "Composite matching key (OrderSales <-> FinancialReport):",
        "  Order Number + SKU + Quantity + Price (or Product Title) — resolves the",
        "  9 repeated Order Number + SKU combinations observed in the raw export.",
        "",
        f"Data source for this report: {data_note}.",
        "",
        "Note on Order Tag: the OrderSales/FinancialReport exports do not include a",
        "populated 'Order Tag' column, so Event / Corporate / Friends & Family only",
        "trigger if that column exists in the input file. See sullivan_c7_simulator.py",
        "for the documented finding and the simulated tag model.",
        "",
        "References: Commerce7 Sales Summary Report, Order Channels, Sales",
        "Attributes and Reports Overview documentation. Business rules by Maya.",
    ]
    lead = auto_row_h(len(lines), y, 14, 20)
    y = center_block(y, len(lines) * lead)
    c.setFont(FONT_REGULAR, max(9.5, min(11.0, lead * 0.5)))
    for i, line in enumerate(lines):
        c.drawString(MARGIN, y - i * lead, fit_text(line, CONTENT_W, FONT_REGULAR, 11.0))
    c.showPage()


def load_data_file(path_str: str | Path) -> pd.DataFrame:
    """Carga un archivo de datos en formato Excel (.xlsx/.xls) o CSV (.csv)."""
    p = Path(path_str)
    if not p.exists():
        raise FileNotFoundError(f"No se encontró el archivo de datos: {p}")
    if p.suffix.lower() == ".csv":
        try:
            return pd.read_csv(p, encoding="utf-8")
        except UnicodeDecodeError:
            return pd.read_csv(p, encoding="latin1")
    return pd.read_excel(p)


# ==============================================================================
# 4. MAIN
# ==============================================================================
def build_pdf(order_sales_path, financial_report_path, output_path, period_label):
    df = load_data_file(order_sales_path)
    df = classify_orders(df)
    amt_col = money_col(df)
    df[amt_col] = coerce_money(df[amt_col])
    order_col = "Order Number" if "Order Number" in df.columns else "Id"

    # Las filas 'Unassigned' se incluyen explícitamente cuando existen: si se
    # descartan (reindex solo sobre CATEGORY_ORDER) el total subcuenta y el
    # cuadre falla sin diagnóstico.
    diagnostics = {
        "unassigned_rows": int((df["Final Category"] == "Unassigned").sum()),
        "unassigned_subtotal": round(float(df.loc[df["Final Category"] == "Unassigned", amt_col].sum()), 2),
        "review_rows": int((df["Final Category"] == "Club - Review (Admin/POS)").sum()),
        "review_subtotal": round(float(df.loc[df["Final Category"] == "Club - Review (Admin/POS)", amt_col].sum()), 2),
    }
    if diagnostics["unassigned_rows"]:
        warn(f"{diagnostics['unassigned_rows']} renglones quedaron sin clasificar "
             f"(${diagnostics['unassigned_subtotal']:,.2f}). Se incluyen como 'Unassigned' para "
             "que el total cuadre; revisa Channel / Club Title en el origen.")
    cat_order = CATEGORY_ORDER + (["Unassigned"] if diagnostics["unassigned_rows"] else [])

    g = df.groupby("Final Category").agg(orders=(order_col, "nunique"), subtotal=(amt_col, "sum")) \
        .reindex(cat_order).fillna(0).reset_index()
    total_dtc = float(g["subtotal"].sum())
    g["pct"] = np.where(total_dtc > 0, (g["subtotal"] / total_dtc * 100).round(2), 0)
    # Ordenar categorías de mayor a menor por venta neta (SubTotal)
    g = g.sort_values(by="subtotal", ascending=False).reset_index(drop=True)
    vista_a = {
        "categories": g["Final Category"].tolist(), "orders": g["orders"].astype(int).tolist(),
        "subtotal": g["subtotal"].round(2).tolist(), "pct": g["pct"].tolist(), "total_dtc": round(total_dtc, 2),
        # Órdenes únicas del periodo (no la suma de nunique por categoría).
        "total_orders": int(df[order_col].nunique()),
    }

    club_df = df[df["Final Category"].isin(["Estate Club", "Founder's Club"])]
    pkg_order = list(CLUB_PACKAGE_COLORS.keys())
    gp = club_df.groupby("Club Package Group").agg(orders=(order_col, "nunique"), subtotal=(amt_col, "sum")) \
        .reindex(pkg_order).fillna(0).reset_index()
    gp["aov"] = np.where(gp["orders"] > 0, (gp["subtotal"] / gp["orders"]).round(2), 0)
    # Ordenar paquetes de mayor a menor por venta neta (SubTotal)
    gp = gp.sort_values(by="subtotal", ascending=False).reset_index(drop=True)
    # Casos de revisión (Admin/POS Marked as Club): una fila POR ORDEN, con el
    # SubTotal agregado a nivel orden (antes salía una fila por línea de ítem).
    review = df[df["Final Category"] == "Club - Review (Admin/POS)"]
    review_cases = []
    review_total = 0.0
    if not review.empty:
        order_col = "Order Number" if "Order Number" in review.columns else "Id"
        agg = {amt_col: "sum"}
        if "Order Submitted Date" in review.columns:
            agg["Order Submitted Date"] = "first"
        if "Channel" in review.columns:
            agg["Channel"] = "first"
        for extra in ("Club Title", "Club Package"):
            if extra in review.columns:
                agg[extra] = "first"
        review_cases = review.groupby(order_col, as_index=False).agg(agg).rename(
            columns={order_col: "Order Number", amt_col: "SubTotal"}
        )
        review_cases = review_cases[
            [c for c in ("Order Number", "Order Submitted Date", "Channel",
                         "Club Title", "Club Package", "SubTotal") if c in review_cases.columns]
        ]
        review_cases = review_cases.sort_values("SubTotal", ascending=False)
        review_total = round(float(review_cases["SubTotal"].sum()), 2)
        # Formato listo para imprimir: sin `astype(str)` a secas, que convertía los
        # NaN de Club Title / Club Package en la cadena literal "None", y con los
        # importes en la misma notación de moneda que el resto del reporte.
        review_cases["SubTotal"] = review_cases["SubTotal"].map(lambda v: fmt_money(round(v, 2)))
        if "Order Submitted Date" in review_cases.columns:
            # Solo la fecha: la hora exacta no aporta a una decisión directiva.
            review_cases["Order Submitted Date"] = (
                review_cases["Order Submitted Date"].astype(str).str.slice(0, 10)
            )
        review_cases = review_cases.rename(columns={"Order Submitted Date": "Date",
                                                    "SubTotal": "Net Sales"})
        for col in review_cases.columns:
            review_cases[col] = review_cases[col].map(blank_if_missing)
        review_cases = review_cases.to_dict(orient="records")
    vista_b = {
        "packages": gp["Club Package Group"].tolist(), "orders": gp["orders"].astype(int).tolist(),
        "subtotal": gp["subtotal"].round(2).tolist(), "aov": gp["aov"].tolist(),
        "estate_total": round(float(club_df[club_df["Final Category"] == "Estate Club"][amt_col].sum()), 2),
        "founders_total": round(float(club_df[club_df["Final Category"] == "Founder's Club"][amt_col].sum()), 2),
        "review_cases": review_cases,
        "review_total": review_total,
    }

    net_sales_financial = None
    financial_basis = None
    if financial_report_path:
        try:
            fin = load_data_file(financial_report_path)
            financial_basis = financial_money_col(fin)
            if financial_basis is None:
                warn(f"El reporte financiero no trae ninguna de {FINANCIAL_MONEY_COLS}; "
                     "no se puede reconciliar.")
            else:
                net_sales_financial = round(float(coerce_money(fin[financial_basis]).sum()), 2)
        except Exception as e:
            warn(f"No se pudo leer el reporte financiero ({e}); se omite la reconciliación.")
    # Cuadre EXACTO al centavo: comparación sobre importes redondeados a 2 decimales.
    # Antes se usaba np.isclose(atol=0.005), que conserva rtol=1e-5 por defecto y
    # sobre $433k tolera ~$4.34 de diferencia — justo lo que la guía prohíbe.
    match = None
    if net_sales_financial is not None:
        match = bool(round(total_dtc, 2) == round(net_sales_financial, 2))
    reconciliation = {
        "net_sales_financial": net_sales_financial,
        "match": match,
        "sales_basis": amt_col,
        "financial_basis": financial_basis,
    }

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(out), pagesize=letter)

    page_cover(c, period_label, total_dtc, reconciliation)
    page = 2
    page_executive_summary(c, vista_a, page); page += 1
    page_classification_cascade(c, page); page += 1
    page_category_detail(c, vista_a, page); page += 1
    page_financial_reconciliation(c, vista_a, reconciliation, diagnostics, page); page += 1
    page_club_deep_dive(c, vista_b, page); page += 1
    page_club_review_cases(c, vista_b, total_dtc, page); page += 1
    data_note = "simulated data (sullivan_c7_simulator.py)" if "sim" in Path(order_sales_path).stem.lower() else "real Commerce7 export"
    page_appendix(c, page, data_note)

    c.save()
    print(f"PDF generado: {out}  ({page} páginas + portada)")
    print(f"  Total DTC ({amt_col}): ${total_dtc:,.2f}")
    if net_sales_financial is not None:
        print(f"  Net Sales ({financial_basis}): ${net_sales_financial:,.2f}  "
              f"diferencia: ${total_dtc - net_sales_financial:,.2f}")
    print(f"  Reconciliación al centavo: {reconciliation['match']}")


def main():
    # Forzar UTF-8 en stdout/stderr (evita corrupción o UnicodeEncodeError en consolas Windows legacy).
    for _stream in (sys.stdout, sys.stderr):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError, OSError):
            pass

    ap = argparse.ArgumentParser(description="Genera el PDF base Vista A + Vista B de Sullivan.")
    ap.add_argument("--order-sales", required=True)
    ap.add_argument("--financial-report", default=None)
    ap.add_argument("--output", default="Data_for_demo/sullivan_report.pdf")
    ap.add_argument("--period-label", default="April 2026")
    args = ap.parse_args()
    # Rutas relativas se resuelven contra la raíz del proyecto (igual que en el
    # orquestador), no contra el directorio desde el que se invocó el script.
    out_path = Path(args.output)
    if not out_path.is_absolute():
        out_path = PROJECT_ROOT / out_path
    build_pdf(args.order_sales, args.financial_report, out_path, args.period_label)


if __name__ == "__main__":
    main()
