"""
================================================================================
 SULLIVAN RUTHERFORD ESTATE — REPORTE UNIFICADO EN PDF
================================================================================
Contraparte imprimible del dashboard unificado: un solo documento con las dos
cadencias, sin repetir lo que ambos reportes decían igual.

Reutiliza los constructores de datos que ya existen, no los reimplementa:

    dashboard_generator        cascada de clasificación, vista de categorías,
                               Club Deep Dive y reconciliación al centavo
    sullivan_weekly_processor  DTC semanal, cuentas por cobrar, depletions
    dashboard_sullivan_unified homologación de las dos taxonomías de canal y
                               la tabla única de no clasificados
    pdf_common                 toda la maquetación

Qué aparece UNA sola vez (y antes estaba dos):
  * La mezcla de canales, como una tabla de dos columnas —mes y semana— con los
    nombres homologados ("Events"->"Event", "Tock (Net Rec.)"->"Tock"). Las dos
    cadencias usan la MISMA taxonomía de 10 canales; eso era la duplicación.
  * El desglose de Club: el semanal solo tenía Founder's/Estate, que es un
    subconjunto del Club Deep Dive mensual.
  * La tabla de no clasificados, ahora con una columna de cadencia.
  * La portada y la tira de KPIs.

Qué se conserva por ser exclusivo:
  * Mensual: reconciliación al centavo y la cascada de 9 prioridades.
  * Semanal: Tock, cuentas por cobrar con antigüedad y depletions.

El mapa Albers NO va en el PDF: es una figura interactiva cuyo valor está en el
tooltip por estado y por código postal. En papel se sustituye por la tabla de
estados destino, que es la misma información sin la mitad que no funciona
impresa.
================================================================================
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import pdf_common as T  # noqa: E402
from pdf_common import (  # noqa: E402
    BLANK,
    CONTENT_W,
    MARGIN,
    PAGE_H,
    PAGE_W,
    SULLIVAN_THEME,
    auto_row_h,
    blank_if_missing,
    center_block,
    draw_empty_state,
    draw_header_band,
    draw_horizontal_bars,
    draw_kpi_cards,
    draw_note,
    draw_section_title,
    draw_table,
    fit_text,
    fmt_cases,
    fmt_money,
    fmt_money2,
    fmt_num,
    fmt_pct,
    logo_data,
    scale_widths,
    use_theme,
)

# Motores de cálculo ya validados. Se importan, no se copian.
from dashboard_generator import (  # noqa: E402
    CATEGORY_GLOSSARY,
    REASON_CLUB_NO_PROGRAM,
    REASON_UNKNOWN_CHANNEL,
    UNCLASSIFIED,
    build_geo,
    build_reconciliation,
    build_vista_a,
    build_vista_b,
    classify_orders,
    coerce_money,
    load_data_file,
    money_col,
)
from dashboard_sullivan_unified import (  # noqa: E402
    build_unified_channels,
    build_unified_unclassified,
)
from sullivan_weekly_processor import process_sullivan_weekly_series  # noqa: E402

PROJECT_ROOT = _HERE.parent

# Misma paleta que el HTML: un canal conserva su color entre entregables.
CATEGORY_PDF_COLORS = {
    "Telesales": colors.HexColor("#003057"),
    "Event": colors.HexColor("#2C4F73"),
    "Corporate": colors.HexColor("#55698C"),
    "Friends & Family": colors.HexColor("#7E85A5"),
    "Tock": colors.HexColor("#A7A1BE"),
    "Web / Ecommerce": colors.HexColor("#A67C52"),
    "Tasting Room": colors.HexColor("#C79F6C"),
    "Estate Club": colors.HexColor("#8C2F2F"),
    "Founder's Club": colors.HexColor("#451B0F"),
    UNCLASSIFIED: colors.HexColor("#656565"),
}
CLUB_PDF_COLORS = {
    "Estate 4 Bottle": colors.HexColor("#8C2F2F"),
    "Estate 6 Bottle": colors.HexColor("#B24B4B"),
    "Founder's 3 Bottle": colors.HexColor("#451B0F"),
    "Founder's Half Case": colors.HexColor("#6B2C1B"),
    "Founder's Single Case": colors.HexColor("#8C4A2E"),
    "Founder's Double Case": colors.HexColor("#A6673F"),
}
AGING_PDF_COLORS = {
    "0–15 days": colors.HexColor("#1D6B36"),
    "16–30 days": colors.HexColor("#A67C52"),
    "30+ days (overdue)": colors.HexColor("#8C2F2F"),
}


# ==============================================================================
# PÁGINAS
# ==============================================================================
def page_cover(c, payload):
    m, w = payload["monthly"], payload["weekly"]
    c.setFillColor(T.PRIMARY)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

    logo = logo_data("sullivan")
    y = PAGE_H - 2.4 * inch
    drew = False
    if logo:
        try:
            c.drawImage(logo, (PAGE_W - 2.2 * inch) / 2, y, width=2.2 * inch,
                        height=0.9 * inch, mask="auto",
                        preserveAspectRatio=True, anchor="c")
            drew = True
            y -= 0.45 * inch
        except Exception:
            pass
    if not drew:
        c.setFillColor(colors.white)
        c.setFont(T.FONT_BOLD, 30)
        c.drawCentredString(PAGE_W / 2, y, "SULLIVAN")
        c.setFont(T.FONT_REGULAR, 11)
        c.drawCentredString(PAGE_W / 2, y - 24, "R U T H E R F O R D   E S T A T E")
        y -= 0.7 * inch

    c.setStrokeColor(T.ACCENT)
    c.setLineWidth(1.2)
    c.line(PAGE_W / 2 - 1.4 * inch, y, PAGE_W / 2 + 1.4 * inch, y)

    c.setFillColor(colors.white)
    c.setFont(T.FONT_BOLD, 22)
    c.drawCentredString(PAGE_W / 2, y - 0.55 * inch, "Executive Report")
    c.setFont(T.FONT_REGULAR, 11)
    c.drawCentredString(PAGE_W / 2, y - 0.83 * inch,
                        "Monthly close and weekly operations in one document")

    # Los dos periodos, uno por cadencia.
    c.setFillColor(T.ACCENT)
    c.setFont(T.FONT_BOLD, 14)
    c.drawCentredString(PAGE_W / 2, y - 1.35 * inch,
                        blank_if_missing(payload["meta"]["period_label"]))
    if w:
        c.setFillColor(colors.white)
        c.setFont(T.FONT_REGULAR, 10)
        c.drawCentredString(PAGE_W / 2, y - 1.62 * inch,
                            "with " + blank_if_missing(w.get("period_label")))

    rec = m["reconciliation"]
    box_y = 3.0 * inch
    items = [("MONTH · TOTAL DTC", fmt_money(m["vista_a"]["total_dtc"]))]
    if w:
        items.append(("WEEK · TOTAL DTC", fmt_money(w["kpis"]["total_dtc_sales"])))
        items.append(("WEEK · OPEN POs", fmt_money(w["kpis"]["total_open_pos_amount"])))
    else:
        items.append(("UNIQUE ORDERS", fmt_num(m["vista_a"]["total_orders"])))
        items.append(("RECONCILED", "YES" if rec.get("match") else BLANK))

    col_w = CONTENT_W / len(items)
    for i, (label, value) in enumerate(items):
        cx = MARGIN + col_w * i + col_w / 2
        c.setFillColor(T.ACCENT)
        c.setFont(T.FONT_REGULAR, 7.5)
        c.drawCentredString(cx, box_y + 0.32 * inch, label)
        c.setFillColor(colors.white)
        size = 17.0
        while size > 10 and T.pdfmetrics.stringWidth(value, T.FONT_BOLD, size) > col_w - 12:
            size -= 0.5
        c.setFont(T.FONT_BOLD, size)
        c.drawCentredString(cx, box_y, value)

    if rec.get("net_sales_financial") is not None:
        ok = rec.get("match") is True
        c.setFillColor(T.ACCENT if ok else colors.HexColor("#E08A8A"))
        c.setFont(T.FONT_REGULAR, 9)
        c.drawCentredString(
            PAGE_W / 2, 1.3 * inch,
            "RECONCILED · Total DTC matches Net Sales to the cent" if ok
            else f"REVIEW REQUIRED · difference {fmt_money2(rec.get('difference'))}")
    c.showPage()


def page_executive(c, payload, page_num):
    """Las dos cadencias en una página: el mes cierra los libros, la semana opera."""
    m, w = payload["monthly"], payload["weekly"]
    draw_header_band(c, "Executive Summary",
                     blank_if_missing(payload["meta"]["period_label"]), page_num)
    y = PAGE_H - 1.25 * inch

    va, rec, dg = m["vista_a"], m["reconciliation"], m["diagnostics"]

    y = draw_section_title(c, "Month — " +
                           blank_if_missing(payload["meta"]["period_label"]), y)
    y = draw_kpi_cards(c, [
        ("Total DTC Net Sales", fmt_money(va["total_dtc"]), False),
        ("Unique Orders", fmt_num(va["total_orders"]), False),
        ("Leading Channel", fit_text(blank_if_missing(va["categories"][0]),
                                     1.7 * inch, T.FONT_BOLD, 13), False),
        ("Unclassified", fmt_money(dg["unclassified_subtotal"]),
         dg["unclassified_rows"] > 0),
    ], y)

    if w:
        k = w["kpis"]
        y = draw_section_title(c, "Week — " +
                               blank_if_missing(w.get("period_label")), y - 4)
        overdue = k.get("overdue_30_amount") or 0
        y = draw_kpi_cards(c, [
            ("Total DTC Sales", fmt_money(k.get("total_dtc_sales")), False),
            ("Cash Received", fmt_money(k.get("cash_received")), False),
            ("Open PO Balance", fmt_money(k.get("total_open_pos_amount")), False),
            ("Overdue > 30 Days", fmt_money(overdue), overdue > 0),
        ], y)
        y = draw_kpi_cards(c, [
            ("Depletions", fmt_cases(k.get("depletions_9l_cases")), False),
            ("Open Invoices", fmt_num(k.get("open_invoices_count")), False),
            ("Cases in Pipeline", fmt_num(k.get("total_open_cases")), False),
        ], y - 2)

    # Reconciliación: la afirmación central del cierre mensual.
    y = draw_section_title(c, "Financial reconciliation", y - 4)
    if rec.get("net_sales_financial") is None:
        y = draw_empty_state(
            c, "No financial report was supplied, so this month was not reconciled.", y)
    else:
        rows = [
            ["DTC net sales (transactional)", blank_if_missing(rec.get("sales_basis")),
             fmt_money2(rec.get("total_dtc"))],
            ["Net sales (financial report)", blank_if_missing(rec.get("financial_basis")),
             fmt_money2(rec.get("net_sales_financial"))],
            ["Difference",
             "Exact to the cent" if rec.get("match") else "Review required",
             fmt_money2(rec.get("difference"))],
        ]
        widths = scale_widths([3.4, 2.2, 1.7])
        row_h = auto_row_h(4, y, 15, 26, reserve=70)
        y = draw_table(c, ["Measure", "Basis", "Amount"], rows, MARGIN, y,
                       widths, row_h=row_h, total_row_idx=2, align_right={2})
        y = draw_note(
            c, "The comparison uses the item-level amount on each side: "
               f"{blank_if_missing(rec.get('sales_basis'))} in the sales export and "
               f"{blank_if_missing(rec.get('financial_basis'))} in the financial "
               "report. Forcing the same column name on both double-counts orders "
               "with several lines, which is why the two bases differ by design.",
            y - 4)
    c.showPage()


def page_channel_mix(c, payload, page_num):
    """El bloque que los dos reportes repetían, ahora uno."""
    uni = payload["unified_channels"]
    draw_header_band(c, "Channel Mix", "One taxonomy, both cadences", page_num)
    y = PAGE_H - 1.25 * inch

    rows_m = [r for r in uni["rows"] if r["monthly"] is not None]

    y = draw_section_title(c, "Monthly net sales by channel", y)
    reserve = (len(uni["rows"]) + 3) * 15 + 90
    row_h = auto_row_h(max(1, len(rows_m)), y, 14, 24, reserve=reserve)
    if rows_m:
        y = draw_horizontal_bars(
            c, [r["channel"] for r in rows_m], [r["monthly"] for r in rows_m],
            {r["channel"]: CATEGORY_PDF_COLORS.get(r["channel"], T.ACCENT)
             for r in rows_m},
            MARGIN, y, CONTENT_W, row_h=row_h)
    else:
        y = draw_empty_state(c, "No monthly channel detail available.", y)

    y = draw_section_title(c, "Month against week, channel by channel", y - 6)
    tm, tw = uni["monthly_total"], uni["weekly_total"]
    rows = []
    for r in uni["rows"]:
        rows.append([
            r["channel"],
            fmt_money2(r["monthly"]),
            fmt_pct(r["monthly"] / tm * 100) if (r["monthly"] is not None and tm) else BLANK,
            fmt_money2(r["weekly"]),
            fmt_pct(r["weekly"] / tw * 100) if (r["weekly"] is not None and tw) else BLANK,
        ])
    rows.append(["TOTAL", fmt_money2(tm), "100.0%" if tm else BLANK,
                 fmt_money2(tw), "100.0%" if tw else BLANK])

    widths = scale_widths([2.2, 1.5, 0.9, 1.5, 0.9])
    row_h = auto_row_h(len(rows) + 1, y, 12, 20, reserve=74)
    y = draw_table(c, ["Channel", "Month", "Share", "Week", "Share"], rows,
                   MARGIN, y, widths, row_h=row_h,
                   total_row_idx=len(rows) - 1, align_right={1, 2, 3, 4})

    y = draw_note(
        c, "Both cadences classify sales into the same ten channels, so this is one "
           "table instead of two charts. The week is not a twelfth of the month: it "
           "is a different window, and a channel can lead one and trail the other. "
           "A dash means that channel has no figure on that side rather than a zero.",
        y - 4)
    c.showPage()


def page_cascade(c, payload, page_num):
    """Cascada de 9 prioridades y detalle por categoría (exclusivo del mensual)."""
    va = payload["monthly"]["vista_a"]
    draw_header_band(c, "DTC Detail — 9-Priority Cascade",
                     "Every order line lands in exactly one category", page_num)
    y = PAGE_H - 1.25 * inch

    rows = []
    for cat, orders, sub, pct in zip(va["categories"], va["orders"],
                                     va["subtotal"], va["pct"]):
        aov = (sub / orders) if orders else None
        rows.append([cat, fmt_num(orders), fmt_money2(sub), fmt_pct(pct),
                     fmt_money2(aov)])
    rows.append(["TOTAL DTC", fmt_num(va["total_orders"]),
                 fmt_money2(va["total_dtc"]), "100.0%",
                 fmt_money2(va["total_dtc"] / va["total_orders"]
                            if va["total_orders"] else None)])

    y = draw_section_title(c, "Net sales by final category", y)
    widths = scale_widths([2.3, 1.0, 1.6, 0.9, 1.4])
    glossary_h = (len(CATEGORY_GLOSSARY) + 2) * 13 + 44
    row_h = auto_row_h(len(rows) + 1, y, 13, 22, reserve=glossary_h)
    y = draw_table(c, ["Category", "Orders", "Net Sales", "Share", "Avg / Order"],
                   rows, MARGIN, y, widths, row_h=row_h,
                   total_row_idx=len(rows) - 1, align_right={1, 2, 3, 4})

    y = draw_section_title(c, "What each category means", y - 10)
    g_rows = []
    for i, (name, desc) in enumerate(CATEGORY_GLOSSARY):
        is_diag = name == UNCLASSIFIED
        g_rows.append([BLANK if is_diag else str(i + 1), name, desc])
    widths = scale_widths([0.4, 1.7, 5.2])
    row_h = auto_row_h(len(g_rows) + 1, y, 11, 17, reserve=10)
    draw_table(c, ["#", "Category", "Definition"], g_rows, MARGIN, y, widths,
               row_h=row_h)
    c.showPage()


def page_club(c, payload, page_num):
    """Club Deep Dive. El semanal solo tenía Founder's/Estate: subconjunto de esto."""
    vb = payload["monthly"]["vista_b"]
    geo = payload["monthly"]["geo"]
    draw_header_band(c, "Club Deep Dive",
                     "Estate versus Founder's, by package", page_num)
    y = PAGE_H - 1.25 * inch

    est = vb.get("estate_total") or 0
    fdr = vb.get("founders_total") or 0
    tot = est + fdr
    y = draw_kpi_cards(c, [
        ("Total Club Net Sales", fmt_money(tot), False),
        ("Founder's Club", fmt_money(fdr), False),
        ("Estate Club", fmt_money(est), False),
        ("Club Share of DTC",
         fmt_pct(tot / payload["monthly"]["vista_a"]["total_dtc"] * 100
                 if payload["monthly"]["vista_a"]["total_dtc"] else None), False),
    ], y)

    pkgs = [(p, o, s, a) for p, o, s, a in zip(
        vb["packages"], vb["orders"], vb["subtotal"], vb["aov"]) if s]

    y = draw_section_title(c, "Net sales by package", y)
    n_states = min(10, len(geo.get("states", [])))
    reserve = (len(pkgs) + n_states + 6) * 14 + 70
    row_h = auto_row_h(max(1, len(pkgs)), y, 16, 28, reserve=reserve)
    if pkgs:
        y = draw_horizontal_bars(
            c, [p[0] for p in pkgs], [p[2] for p in pkgs],
            {p[0]: CLUB_PDF_COLORS.get(p[0], T.ACCENT) for p in pkgs},
            MARGIN, y, CONTENT_W, row_h=row_h)
        rows = [[p[0], fmt_num(p[1]), fmt_money2(p[2]), fmt_money2(p[3])]
                for p in pkgs]
        rows.append(["TOTAL CLUB", fmt_num(sum(p[1] for p in pkgs)),
                     fmt_money2(tot), ""])
        widths = scale_widths([2.9, 1.2, 1.7, 1.5])
        row_h = auto_row_h(len(rows) + 1, y, 12, 20,
                           reserve=(n_states + 4) * 14 + 44)
        y = draw_table(c, ["Package", "Shipments", "Net Sales", "Avg Order Value"],
                       rows, MARGIN, y, widths, row_h=row_h,
                       total_row_idx=len(rows) - 1, align_right={1, 2, 3})
    else:
        y = draw_empty_state(c, "No club shipments in this period.", y)

    # Sustituto en papel del mapa Albers: la misma información sin el tooltip.
    y = draw_section_title(c, "Where club wine shipped", y - 10)
    states = geo.get("states", [])[:n_states]
    if states:
        rows = [[s, fmt_num(o), fmt_money2(sub)] for s, o, sub in zip(
            states, geo["state_orders"][:n_states], geo["state_subtotal"][:n_states])]
        widths = scale_widths([1.2, 1.5, 2.0])
        row_h = auto_row_h(len(rows) + 1, y, 11, 17, reserve=40)
        y = draw_table(c, ["Destination state", "Shipments", "Net Sales"], rows,
                       MARGIN, y, widths, row_h=row_h, align_right={1, 2})
        if geo.get("unresolved_rows"):
            y = draw_note(
                c, f"{fmt_num(geo['unresolved_rows'])} club line(s) worth "
                   f"{fmt_money2(geo['unresolved_subtotal'])} carry no usable "
                   "destination state, so they are absent from this table. They "
                   "are still included in total club net sales, which is why the "
                   "column does not add up to the figure above.", y - 4)
    else:
        y = draw_empty_state(c, "No club shipment carried a usable destination "
                                "state this period.", y)
    c.showPage()


def page_distribution(c, payload, page_num):
    """Cuentas por cobrar y depletions (exclusivo de la cadencia semanal)."""
    w = payload["weekly"]
    draw_header_band(c, "Distribution & Depletions",
                     "Park Street receivables · wholesale sell-through", page_num)
    y = PAGE_H - 1.25 * inch

    if not w:
        draw_empty_state(
            c, "No weekly data was supplied, so distribution receivables and "
               "depletions are not part of this report. Add the weekly folder to "
               "include them.", y)
        c.showPage()
        return

    k = w["kpis"]
    overdue_amt = k.get("overdue_30_amount") or 0
    y = draw_kpi_cards(c, [
        ("Open PO Balance", fmt_money(k.get("total_open_pos_amount")), False),
        ("Cash Received", fmt_money(k.get("cash_received")), False),
        ("Overdue > 30 Days", fmt_money(overdue_amt), overdue_amt > 0),
        ("Depletions", fmt_cases(k.get("depletions_9l_cases")), False),
    ], y)

    aging = w.get("po_aging", [])
    overdue = w.get("overdue_details", [])
    by_state = w.get("depletions_by_state", [])

    y = draw_section_title(c, "Open balance by age bracket", y)
    reserve = (len(overdue) + len(by_state) + 8) * 13 + 90
    row_h = auto_row_h(max(1, len(aging)), y, 16, 28, reserve=reserve)
    if aging:
        y = draw_horizontal_bars(
            c, [b["bucket"] for b in aging], [b["amount"] for b in aging],
            {b["bucket"]: AGING_PDF_COLORS.get(b["bucket"], T.ACCENT) for b in aging},
            MARGIN, y, CONTENT_W, row_h=row_h)

    if overdue:
        y = draw_section_title(c, "Invoices past 30 days", y - 6)
        rows = [[blank_if_missing(r.get("invoice")),
                 blank_if_missing(r.get("customer")),
                 blank_if_missing(r.get("market")),
                 f"{fmt_num(r.get('aging'))} d",
                 fmt_money2(r.get("balance"))] for r in overdue]
        widths = scale_widths([1.2, 2.9, 0.8, 0.8, 1.2])
        row_h = auto_row_h(len(rows) + 1, y, 12, 19,
                           reserve=(len(by_state) + 4) * 13 + 40)
        y = draw_table(c, ["Invoice", "Customer", "Market", "Age", "Balance"],
                       rows, MARGIN, y, widths, row_h=row_h, align_right={3, 4})

    y = draw_section_title(c, "Depletions by state — " +
                           blank_if_missing(k.get("depletions_period")), y - 8)
    if by_state:
        rows = [[blank_if_missing(s.get("state")), fmt_num(s.get("cases"), 2),
                 "Live feed" if s.get("live") else "No sell-through feed"]
                for s in by_state]
        widths = scale_widths([1.1, 1.3, 2.6])
        row_h = auto_row_h(len(rows) + 1, y, 11, 17, reserve=14)
        y = draw_table(c, ["State", "9L Cases", "Feed status"], rows, MARGIN, y,
                       widths, row_h=row_h, align_right={1})
    else:
        y = draw_empty_state(c, "No state reported depletions in this period.", y)
    c.showPage()


def page_unclassified(c, payload, page_num):
    """Una sola tabla de no clasificados para las dos cadencias."""
    dg = payload["monthly"]["diagnostics"]
    rows_data = payload["unified_unclassified"]
    draw_header_band(c, UNCLASSIFIED,
                     "Lines the cascade could not assign, both cadences", page_num)
    y = PAGE_H - 1.25 * inch

    y = draw_kpi_cards(c, [
        ("Month · Unclassified", fmt_money2(dg["unclassified_subtotal"]),
         dg["unclassified_rows"] > 0),
        ("Club, No Program", fmt_money2(dg["club_no_program_subtotal"]), False),
        ("Channel Not Recognized", fmt_money2(dg["unknown_channel_subtotal"]), False),
    ], y)

    if not rows_data:
        draw_empty_state(
            c, "Nothing unclassified in either cadence. Every order line matched a "
               "category, so no diagnostic row was needed to make the totals balance.",
            y)
        c.showPage()
        return

    rows = [[r["cadence"], blank_if_missing(r["order"]),
             blank_if_missing(r["channel"]),
             blank_if_missing(r["package"]),
             blank_if_missing(r["reason"]),
             blank_if_missing(r["amount_text"])] for r in rows_data]
    total = sum(r["amount"] for r in rows_data)
    rows.append(["", "", "", "", "TOTAL", fmt_money2(total)])

    note = ("These lines are counted in every total, which is why the books still "
            "balance to the cent. Listing them is what makes them fixable: "
            f"'{REASON_CLUB_NO_PROGRAM}' means a Club order names neither program in "
            f"Club Package or Club Title, and '{REASON_UNKNOWN_CHANNEL}' means the "
            "Channel value is not one the cascade knows. Both are corrected at the "
            "source in Commerce7.")
    note_h = 80
    block_h = (len(rows) + 2) * 18 + note_h + 30
    y = center_block(y, block_h)

    y = draw_section_title(c, "Every unassigned order", y)
    widths = scale_widths([0.9, 1.0, 0.9, 1.9, 2.3, 1.2])
    row_h = auto_row_h(len(rows) + 1, y, 12, 22, reserve=note_h + 12)
    y = draw_table(c, ["Cadence", "Order", "Channel", "Club Package", "Reason",
                       "Net Sales"], rows, MARGIN, y, widths, row_h=row_h,
                   total_row_idx=len(rows) - 1, align_right={5})
    draw_note(c, note, y - 6)
    c.showPage()


# ==============================================================================
# ENTRADA
# ==============================================================================
def build_unified_pdf(order_sales_path, financial_report_path, weekly_data_dir,
                      output_path, period_label: str,
                      tock_basis: str = "net_receivable",
                      lang: str = T.DEFAULT_LANG_PDF) -> Path:
    T.set_lang(lang)
    use_theme(SULLIVAN_THEME)

    df = load_data_file(order_sales_path)
    df = classify_orders(df)
    amt_col = money_col(df)
    df[amt_col] = coerce_money(df[amt_col])

    unc = df["Final Category"] == UNCLASSIFIED
    reason = df.get("Unclassified Reason")
    if reason is None:
        import pandas as pd
        reason = pd.Series("", index=df.index)
    reason = reason.fillna("")
    club_no_prog = unc & (reason == REASON_CLUB_NO_PROGRAM)
    bad_channel = unc & (reason == REASON_UNKNOWN_CHANNEL)
    diagnostics = {
        "unclassified_rows": int(unc.sum()),
        "unclassified_subtotal": round(float(df.loc[unc, amt_col].sum()), 2),
        "club_no_program_rows": int(club_no_prog.sum()),
        "club_no_program_subtotal": round(float(df.loc[club_no_prog, amt_col].sum()), 2),
        "unknown_channel_rows": int(bad_channel.sum()),
        "unknown_channel_subtotal": round(float(df.loc[bad_channel, amt_col].sum()), 2),
    }

    vista_a = build_vista_a(df)
    vista_b = build_vista_b(df)
    geo = build_geo(df)
    reconciliation = build_reconciliation(
        vista_a, str(financial_report_path) if financial_report_path else None, amt_col)

    # Un PDF no puede llevar selector, así que documenta la semana MÁS
    # RECIENTE de las que haya. El WoW que aparece en la portada sí es real
    # ahora: sale de comparar contra la semana anterior de la serie.
    weekly = None
    weekly_series = None
    if weekly_data_dir and Path(weekly_data_dir).exists():
        try:
            weekly_series = process_sullivan_weekly_series(
                Path(weekly_data_dir), tock_basis=tock_basis)
            weekly = weekly_series[-1]
        except FileNotFoundError:
            weekly = None

    payload = {
        "meta": {"period_label": period_label},
        "monthly": {"vista_a": vista_a, "vista_b": vista_b, "geo": geo,
                    "reconciliation": reconciliation, "diagnostics": diagnostics},
        "weekly": weekly,
        "unified_channels": build_unified_channels(vista_a, weekly),
        "unified_unclassified": build_unified_unclassified(vista_b, weekly),
    }

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(out), pagesize=letter)
    # Envolver el canvas cubre los `drawString` directos de portadas y pies,
    # que no pasan por los ayudantes de maquetación.
    T.localize_canvas(c)
    c.setTitle(f"Sullivan Rutherford Estate — Executive Report ({period_label})")

    page_cover(c, payload)
    page_executive(c, payload, 2)
    page_channel_mix(c, payload, 3)
    page_cascade(c, payload, 4)
    page_club(c, payload, 5)
    page_distribution(c, payload, 6)
    page_unclassified(c, payload, 7)
    c.save()

    print(f"PDF unificado generado: {out}")
    print(f"  Mensual  ({period_label}): ${vista_a['total_dtc']:,.2f} "
          f"en {vista_a['total_orders']} órdenes")
    if reconciliation["net_sales_financial"] is not None:
        print(f"  Reconciliación al centavo: {reconciliation['match']} "
              f"(diferencia ${reconciliation['difference']:,.2f})")
    if weekly:
        print(f"  Semanal  ({weekly['period_label']}): "
              f"${weekly['kpis']['total_dtc_sales']:,.2f}")
    else:
        print("  Semanal: no incluido (sin carpeta de datos semanales)")
    print(f"  Canales homologados: {len(payload['unified_channels']['rows'])} "
          f"· No clasificados listados: {len(payload['unified_unclassified'])}")
    return out


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError, OSError):
            pass

    ap = argparse.ArgumentParser(
        description="Genera el reporte unificado de Sullivan en PDF.")
    ap.add_argument("--order-sales", required=True)
    ap.add_argument("--financial-report", default=None)
    ap.add_argument("--weekly-data-dir", default=None)
    ap.add_argument("--period-label", default="April 2026")
    ap.add_argument("--tock-basis", choices=["net_receivable", "net_sales"],
                    default="net_receivable")
    ap.add_argument("--output", default=None)
    args = ap.parse_args(argv)

    out = args.output or str(PROJECT_ROOT / "Output" / "sullivan_report_unified.pdf")
    build_unified_pdf(args.order_sales, args.financial_report,
                      args.weekly_data_dir, out, args.period_label,
                      args.tock_basis)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
