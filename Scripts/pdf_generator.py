"""
================================================================================
 SULLIVAN RUTHERFORD ESTATE — GENERADOR BASE DE PDF (Vista A + Vista B)
================================================================================
Genera el PDF directivo acordado con la estructura reducida (no la de 25-35
páginas del patrón genérico, pensada para catálogos de muchos SKUs — aquí son
9 categorías + 6 paquetes de club, así que basta con ~10-12 páginas):

    1. Portada
    2. Resumen ejecutivo (Vista A) — barras horizontales, 9 categorías
    3. Cascada de clasificación (reglas de negocio)
    4. Detalle por categoría (tabla comparativa)
    5. Reconciliación financiera + checklist de 10 puntos
    6-9. Club Deep Dive (Vista B): Estate vs Founder's, por paquete, AOV,
         casos de revisión (Admin/POS Marked as Club)
    10. Apéndice / metodología

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
import re
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics.charts.barcharts import HorizontalBarChart

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
    cond_club_review = is_club & (club_title == "") & (club_package == "")
    cond_estate = is_club & ~cond_club_review & (club_title.str.contains("Estate", case=False) | club_package.str.contains("Estate", case=False))
    cond_founders = is_club & ~cond_club_review & ~cond_estate

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


def money_col(d):
    for c in ("Product SubTotal", "SubTotal", "Total"):
        if c in d.columns:
            return c
    raise KeyError("No se encontró columna de monto.")


# ==============================================================================
# 2. HELPERS DE DIBUJO (banda navy, tabla, gráfica de barras horizontales)
# ==============================================================================
def fmt_money(v):
    return f"${v:,.0f}"


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


def draw_kpi_cards(c, cards, y, card_w=1.75 * inch, card_h=0.75 * inch, gap=0.12 * inch):
    x = 0.6 * inch
    for label, value, warn in cards:
        c.setFillColor(CREAM)
        c.setStrokeColor(RULE_LINE)
        c.roundRect(x, y - card_h, card_w, card_h, 3, fill=1, stroke=1)
        c.setFillColor(GRAY)
        c.setFont(FONT_REGULAR, 7.5)
        c.drawString(x + 8, y - 16, label.upper())
        c.setFillColor(NEG if warn else NAVY)
        c.setFont(FONT_BOLD, 14)
        c.drawString(x + 8, y - card_h + 14, value)
        x += card_w + gap
    return y - card_h - 16


def draw_horizontal_bars(c, labels, values, color_map, x, y, width, row_h=16, max_value=None):
    max_value = max_value or max(values) if values else 1
    max_value = max_value or 1
    label_w = 1.9 * inch
    bar_area_w = width - label_w - 0.9 * inch
    c.setFont(FONT_REGULAR, 8)
    for i, (lab, val) in enumerate(zip(labels, values)):
        row_y = y - i * row_h
        c.setFillColor(colors.black)
        c.drawString(x, row_y - 10, lab[:28])
        bw = (val / max_value) * bar_area_w if max_value else 0
        c.setFillColor(color_map.get(lab, TAN))
        c.rect(x + label_w, row_y - row_h + 4, max(bw, 1), row_h - 6, fill=1, stroke=0)
        c.setFillColor(GRAY)
        c.drawString(x + label_w + bar_area_w + 6, row_y - 10, fmt_money(val))
    return y - len(labels) * row_h - 10


def draw_table(c, headers, rows, x, y, col_widths, row_h=16, total_row_idx=None):
    c.setFont(FONT_BOLD, 8.5)
    c.setFillColor(NAVY)
    c.rect(x, y - row_h, sum(col_widths), row_h, fill=1, stroke=0)
    c.setFillColor(colors.white)
    cx = x
    for h, w in zip(headers, col_widths):
        c.drawString(cx + 4, y - row_h + 5, str(h))
        cx += w
    y -= row_h
    c.setFont(FONT_REGULAR, 8.5)
    for ridx, row in enumerate(rows):
        if total_row_idx is not None and ridx == total_row_idx:
            c.setFillColor(CREAM)
            c.rect(x, y - row_h, sum(col_widths), row_h, fill=1, stroke=0)
            c.setFont(FONT_BOLD, 8.5)
        c.setFillColor(colors.black)
        cx = x
        for val, w in zip(row, col_widths):
            c.drawString(cx + 4, y - row_h + 5, str(val))
            cx += w
        c.setStrokeColor(RULE_LINE)
        c.line(x, y - row_h, x + sum(col_widths), y - row_h)
        y -= row_h
        if total_row_idx is not None and ridx == total_row_idx:
            c.setFont(FONT_REGULAR, 8.5)
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
    draw_header_band(c, "Executive Summary", "DTC Reconciliation — 9 Final Categories", page_num)
    y = PAGE_H - 1.15 * inch
    y = draw_kpi_cards(c, [
        ("Total DTC", fmt_money(vista_a["total_dtc"]), False),
        ("Total Orders", f"{sum(vista_a['orders']):,}", False),
        ("Categories", str(len(vista_a["categories"])), False),
    ], y)
    y = draw_section_title(c, "Net Sales by Final Category", y - 10)
    color_map = {k: v for k, v in zip(vista_a["categories"], [CATEGORY_COLORS[c_] for c_ in vista_a["categories"]])}
    draw_horizontal_bars(c, vista_a["categories"], vista_a["subtotal"], color_map,
                          0.6 * inch, y, PAGE_W - 1.2 * inch, row_h=22)
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
        ("8", "Club", "Club contains 'Estate'", "Estate Club"),
        ("9", "Club", "Club contains \"Founder's\"", "Founder's Club"),
    ]
    draw_table(c, ["Priority", "Channel", "Identifier", "Final Category"], rows,
               0.6 * inch, y, [0.8 * inch, 1.3 * inch, 3.2 * inch, 1.7 * inch], row_h=20)
    c.showPage()


def page_category_detail(c, vista_a, page_num):
    draw_header_band(c, "Detail by Category", "Orders, Sub Total, % of Sales", page_num)
    y = PAGE_H - 1.2 * inch
    rows = [
        (cat, f"{o:,}", fmt_money(s), f"{p}%")
        for cat, o, s, p in zip(vista_a["categories"], vista_a["orders"], vista_a["subtotal"], vista_a["pct"])
    ]
    rows.append(("TOTAL DTC", f"{sum(vista_a['orders']):,}", fmt_money(vista_a["total_dtc"]), "100%"))
    draw_table(c, ["Category", "Orders", "Sub Total", "% of Sales"], rows,
               0.6 * inch, y, [2.6 * inch, 1.2 * inch, 1.6 * inch, 1.6 * inch],
               row_h=18, total_row_idx=len(rows) - 1)
    c.showPage()


def page_financial_reconciliation(c, vista_a, reconciliation, page_num):
    draw_header_band(c, "Financial Reconciliation", "Total DTC vs Net Sales (Financial Report)", page_num)
    y = PAGE_H - 1.2 * inch
    net = reconciliation.get("net_sales_financial")
    rows = [
        ("Total DTC (classified)", fmt_money(vista_a["total_dtc"])),
        ("Net Sales — Financial Report", fmt_money(net) if net is not None else "n/a"),
        ("Difference", fmt_money(vista_a["total_dtc"] - net) if net is not None else "n/a"),
    ]
    y = draw_table(c, ["Metric", "Value"], rows, 0.6 * inch, y, [3.5 * inch, 2.5 * inch], row_h=20) - 24

    y = draw_section_title(c, "Final Checklist (Sullivan_data_guide.md)", y)
    checklist = [
        "Same reporting period across all exports", "One Order ID counted once",
        "Inbound split before Telesales", "Tock subtracted from Web/Ecommerce",
        "Every POS order mapped to Tasting Room", "Club orders split Estate/Founder's",
        "No order in more than one final category", "Refunds treated consistently",
        "Net Sales compared like-for-like", "Final sum reconciles to the cent",
    ]
    c.setFont(FONT_REGULAR, 9)
    for i, item in enumerate(checklist):
        c.setFillColor(colors.black)
        c.drawString(0.7 * inch, y - i * 15, f"[ ]  {i + 1}. {item}")
    c.showPage()


def page_club_overview(c, vista_b, page_num):
    draw_header_band(c, "Club Deep Dive", "Estate Club vs Founder's Club", page_num)
    y = PAGE_H - 1.15 * inch
    total = vista_b["estate_total"] + vista_b["founders_total"]
    y = draw_kpi_cards(c, [
        ("Estate Club", fmt_money(vista_b["estate_total"]), False),
        ("Founder's Club", fmt_money(vista_b["founders_total"]), False),
        ("Combined Club", fmt_money(total), False),
    ], y)
    y = draw_section_title(c, "Sub Total by Package", y - 10)
    color_map = {p: CLUB_PACKAGE_COLORS.get(p, TAN) for p in vista_b["packages"]}
    draw_horizontal_bars(c, vista_b["packages"], vista_b["subtotal"], color_map,
                          0.6 * inch, y, PAGE_W - 1.2 * inch, row_h=22)
    c.showPage()


def page_club_package_table(c, vista_b, page_num):
    draw_header_band(c, "Club Deep Dive", "By package — orders, sub total, AOV", page_num)
    y = PAGE_H - 1.2 * inch
    rows = [
        (p, f"{o:,}", fmt_money(s), fmt_money(a))
        for p, o, s, a in zip(vista_b["packages"], vista_b["orders"], vista_b["subtotal"], vista_b["aov"])
    ]
    draw_table(c, ["Package", "Orders", "Sub Total", "Avg Order Value"], rows,
               0.6 * inch, y, [2.4 * inch, 1.2 * inch, 1.7 * inch, 1.7 * inch], row_h=20)
    c.showPage()


def page_club_review_cases(c, vista_b, page_num):
    draw_header_band(c, "Club Deep Dive", "Review cases — Admin/POS marked as Club", page_num)
    y = PAGE_H - 1.2 * inch
    cases = vista_b["review_cases"]
    if not cases:
        c.setFont(FONT_REGULAR, 10)
        c.setFillColor(GRAY)
        c.drawString(0.6 * inch, y - 10, "No review cases detected in this period.")
    else:
        headers = list(cases[0].keys())
        rows = [[str(v) for v in case.values()] for case in cases]
        col_w = (PAGE_W - 1.2 * inch) / len(headers)
        draw_table(c, headers, rows, 0.6 * inch, y, [col_w] * len(headers), row_h=18)
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
    for i, line in enumerate(lines):
        c.drawString(0.6 * inch, y - i * 14, line)
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
    order_col = "Order Number" if "Order Number" in df.columns else "Id"

    g = df.groupby("Final Category").agg(orders=(order_col, "nunique"), subtotal=(amt_col, "sum")) \
        .reindex(CATEGORY_ORDER).fillna(0).reset_index()
    total_dtc = float(g["subtotal"].sum())
    g["pct"] = np.where(total_dtc > 0, (g["subtotal"] / total_dtc * 100).round(2), 0)
    # Ordenar categorías de mayor a menor por venta neta (SubTotal)
    g = g.sort_values(by="subtotal", ascending=False).reset_index(drop=True)
    vista_a = {
        "categories": g["Final Category"].tolist(), "orders": g["orders"].astype(int).tolist(),
        "subtotal": g["subtotal"].round(2).tolist(), "pct": g["pct"].tolist(), "total_dtc": round(total_dtc, 2),
    }

    club_df = df[df["Final Category"].isin(["Estate Club", "Founder's Club"])]
    pkg_order = list(CLUB_PACKAGE_COLORS.keys())
    gp = club_df.groupby("Club Package Group").agg(orders=(order_col, "nunique"), subtotal=(amt_col, "sum")) \
        .reindex(pkg_order).fillna(0).reset_index()
    gp["aov"] = np.where(gp["orders"] > 0, (gp["subtotal"] / gp["orders"]).round(2), 0)
    # Ordenar paquetes de mayor a menor por venta neta (SubTotal)
    gp = gp.sort_values(by="subtotal", ascending=False).reset_index(drop=True)
    review = df[df["Final Category"] == "Club - Review (Admin/POS)"]
    review_cols = [c for c in ("Order Number", "Order Submitted Date", "Channel", amt_col) if c in review.columns]
    review_cases = review[review_cols].astype(str).to_dict(orient="records")
    vista_b = {
        "packages": gp["Club Package Group"].tolist(), "orders": gp["orders"].astype(int).tolist(),
        "subtotal": gp["subtotal"].round(2).tolist(), "aov": gp["aov"].tolist(),
        "estate_total": round(float(club_df[club_df["Final Category"] == "Estate Club"][amt_col].sum()), 2),
        "founders_total": round(float(club_df[club_df["Final Category"] == "Founder's Club"][amt_col].sum()), 2),
        "review_cases": review_cases,
    }

    net_sales_financial = None
    if financial_report_path:
        try:
            fin = load_data_file(financial_report_path)
            for c in ("SubTotal", "Sub Total"):
                if c in fin.columns:
                    net_sales_financial = round(float(fin[c].sum()), 2)
                    break
        except Exception:
            pass
    match = np.isclose(total_dtc, net_sales_financial, atol=1.0) if net_sales_financial is not None else None
    reconciliation = {"net_sales_financial": net_sales_financial, "match": bool(match) if match is not None else None}

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(out), pagesize=letter)

    page_cover(c, period_label, total_dtc, reconciliation)
    page = 2
    page_executive_summary(c, vista_a, page); page += 1
    page_classification_cascade(c, page); page += 1
    page_category_detail(c, vista_a, page); page += 1
    page_financial_reconciliation(c, vista_a, reconciliation, page); page += 1
    page_club_overview(c, vista_b, page); page += 1
    page_club_package_table(c, vista_b, page); page += 1
    page_club_review_cases(c, vista_b, page); page += 1
    data_note = "simulated data (sullivan_c7_simulator.py)" if "sim" in Path(order_sales_path).stem.lower() else "real Commerce7 export"
    page_appendix(c, page, data_note)

    c.save()
    print(f"PDF generado: {out}  ({page} páginas + portada)")
    print(f"  Total DTC: {fmt_money(total_dtc)}")
    print(f"  Reconciliación: {reconciliation['match']}")


def main():
    ap = argparse.ArgumentParser(description="Genera el PDF base Vista A + Vista B de Sullivan.")
    ap.add_argument("--order-sales", required=True)
    ap.add_argument("--financial-report", default=None)
    ap.add_argument("--output", default="Data_for_demo/sullivan_report.pdf")
    ap.add_argument("--period-label", default="April 2026")
    args = ap.parse_args()
    build_pdf(args.order_sales, args.financial_report, args.output, args.period_label)


if __name__ == "__main__":
    main()
