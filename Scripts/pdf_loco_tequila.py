"""
================================================================================
 LOCO TEQUILA USA — REPORTE EJECUTIVO EN PDF  (to_do §I.3.4)
================================================================================
Contraparte imprimible del dashboard de Loco Tequila USA, alimentada por los
mismos datos reales: `loco_data_processor.process_loco_data()` lee los 7
insumos crudos de los distribuidores más la carpeta de depletions.

Bajo los tokens de `Designs/Design_loco_tequila.md` (guinda, oro, crema y
Poppins), aplicados a través del tema de marca de `pdf_common`, de modo que la
maquetación es la misma que la de los PDF de Sullivan pero la identidad no.

Tres cosas que este reporte NO hace, a propósito:

* **No calcula margen bruto.** Ningún archivo crudo trae COGS por SKU. Todas
  las cifras monetarias son ingreso bruto, y la última página lo declara con
  su nombre en vez de dejar al lector suponer que vio margen.
* **No mete las muestras en el inventario comercial.** Las líneas
  "NOT SELLABLE - SAMPLES ONLY" se reportan aparte. Sumarlas daba 226.73 cajas
  9L contra las 220.65 del libro del cliente.
* **No reordena las series temporales.** La regla de barras descendentes aplica
  a rankings; los meses de depletions van en orden de calendario, como tabla.
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
    LOCO_THEME,
    MARGIN,
    PAGE_H,
    PAGE_W,
    auto_row_h,
    blank_if_missing,
    center_block,
    draw_empty_state,
    draw_header_band,
    draw_horizontal_bars,
    draw_kpi_cards,
    draw_note,
    draw_paragraph,
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
from loco_data_processor import process_loco_data  # noqa: E402

PROJECT_ROOT = _HERE.parent

# Paleta por producto, la misma del dashboard: el mismo SKU lleva el mismo color
# en HTML y en PDF.
PRODUCT_COLORS = {
    "Blanco": colors.HexColor("#9B1C31"),
    "Blanco 200mL": colors.HexColor("#C0524A"),
    "Ambar": colors.HexColor("#A96C43"),
    "Puro Corazon": colors.HexColor("#6E1E28"),
    "Aureo": colors.HexColor("#C5A059"),
    "Limited Edition Alebrije": colors.HexColor("#1F6E6E"),
    "NOT SELLABLE - SAMPLES ONLY": colors.HexColor("#8C857B"),
    "Other/Unclassified": colors.HexColor("#8C857B"),
}


def _product_color(name):
    return PRODUCT_COLORS.get(name, T.ACCENT)


# ==============================================================================
# PÁGINAS
# ==============================================================================
def page_cover(c, data):
    k = data["kpis"]
    c.setFillColor(T.PRIMARY)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

    logo = logo_data("loco")
    y = PAGE_H - 2.6 * inch
    drew_logo = False
    if logo:
        try:
            c.drawImage(logo, (PAGE_W - 2.0 * inch) / 2, y, width=2.0 * inch,
                        height=1.1 * inch, mask="auto",
                        preserveAspectRatio=True, anchor="c")
            drew_logo = True
            y -= 0.4 * inch
        except Exception:
            pass
    if not drew_logo:
        c.setFillColor(colors.white)
        c.setFont(T.FONT_BOLD, 30)
        c.drawCentredString(PAGE_W / 2, y, "LOCO TEQUILA")
        c.setFillColor(T.ACCENT)
        c.setFont(T.FONT_REGULAR, 11)
        c.drawCentredString(PAGE_W / 2, y - 24, "U S A")
        y -= 0.7 * inch

    c.setStrokeColor(T.ACCENT)
    c.setLineWidth(1.2)
    c.line(PAGE_W / 2 - 1.4 * inch, y, PAGE_W / 2 + 1.4 * inch, y)

    c.setFillColor(colors.white)
    c.setFont(T.FONT_BOLD, 21)
    c.drawCentredString(PAGE_W / 2, y - 0.55 * inch, "Executive Business Report")
    c.setFont(T.FONT_REGULAR, 11)
    c.drawCentredString(PAGE_W / 2, y - 0.83 * inch,
                        "Inventory · Wholesale · Direct to Retail · Depletions · DTC")

    c.setFillColor(T.ACCENT)
    c.setFont(T.FONT_BOLD, 15)
    c.drawCentredString(PAGE_W / 2, y - 1.35 * inch,
                        blank_if_missing(data.get("period_label")))

    box_y = 3.0 * inch
    items = [
        ("COMMERCIAL INVENTORY", fmt_cases(k.get("inventory_total_9l"))),
        ("WHOLESALE REVENUE", fmt_money(k.get("wholesale_revenue"))),
        ("DEPLETIONS YTD", fmt_cases(k.get("depletions_cases_9l_ytd"))),
    ]
    w = CONTENT_W / 3
    for i, (label, value) in enumerate(items):
        cx = MARGIN + w * i + w / 2
        c.setFillColor(T.ACCENT)
        c.setFont(T.FONT_REGULAR, 7.5)
        c.drawCentredString(cx, box_y + 0.32 * inch, label)
        c.setFillColor(colors.white)
        size = 17.0
        while size > 10 and T.pdfmetrics.stringWidth(value, T.FONT_BOLD, size) > w - 12:
            size -= 0.5
        c.setFont(T.FONT_BOLD, size)
        c.drawCentredString(cx, box_y, value)

    # Advertencia de portada: es la afirmación más importante del reporte.
    c.setFillColor(colors.HexColor("#B9AFA0"))
    c.setFont(T.FONT_REGULAR, 8.5)
    c.drawCentredString(PAGE_W / 2, 1.45 * inch,
                        "All monetary figures are GROSS REVENUE, not margin.")
    c.drawCentredString(PAGE_W / 2, 1.28 * inch,
                        "No per-SKU cost of goods exists in the source files.")
    c.setFont(T.FONT_REGULAR, 8)
    c.drawCentredString(PAGE_W / 2, 1.0 * inch,
                        "Data set: " + blank_if_missing(data.get("data_source")))
    c.showPage()


def page_inventory(c, data, page_num):
    k = data["kpis"]
    draw_header_band(c, "Inventory on Hand",
                     "9-litre case equivalent by product and market", page_num)
    y = PAGE_H - 1.25 * inch

    y = draw_kpi_cards(c, [
        ("Commercial Total", fmt_cases(k.get("inventory_total_9l")), False),
        ("California", fmt_cases(k.get("inventory_ca_9l")), False),
        ("Texas", fmt_cases(k.get("inventory_tx_9l")), False),
        ("Samples (excluded)", fmt_cases(k.get("inventory_samples_9l")), False),
    ], y)

    rows_all = data.get("inventory", [])
    sellable = [r for r in rows_all if r.get("sellable")]
    samples = [r for r in rows_all if not r.get("sellable")]

    y = draw_section_title(c, "Commercial inventory by product", y)
    table_rows = len(sellable) + 2 + (len(samples) + 2 if samples else 0)
    reserve = table_rows * 14 + 80
    row_h = auto_row_h(max(1, len(sellable)), y, 16, 30, reserve=reserve)
    if sellable:
        y = draw_horizontal_bars(c, [r["product"] for r in sellable],
                                 [r["total_9l"] for r in sellable],
                                 {r["product"]: _product_color(r["product"])
                                  for r in sellable},
                                 MARGIN, y, CONTENT_W, row_h=row_h,
                                 value_fmt=fmt_cases)
    else:
        y = draw_empty_state(c, "No sellable inventory in this data set.", y)

    y -= 6
    rows = [[r["product"], fmt_num(r["total_9l"], 2), fmt_num(r["ca_9l"], 2),
             fmt_num(r["tx_9l"], 2)] for r in sellable]
    rows.append(["COMMERCIAL TOTAL", fmt_num(k.get("inventory_total_9l"), 2),
                 fmt_num(k.get("inventory_ca_9l"), 2),
                 fmt_num(k.get("inventory_tx_9l"), 2)])
    widths = scale_widths([3.0, 1.5, 1.4, 1.4])
    row_h = auto_row_h(len(rows) + 1, y, 12, 20,
                       reserve=(len(samples) + 3) * 14 + 66 if samples else 66)
    y = draw_table(c, ["Product", "Total 9L", "CA 9L", "TX 9L"], rows,
                   MARGIN, y, widths, row_h=row_h,
                   total_row_idx=len(rows) - 1, align_right={1, 2, 3})

    if samples:
        y = draw_section_title(c, "Reported separately — not sellable", y - 12)
        rows = [[r["product"], fmt_num(r["total_9l"], 2), fmt_num(r["ca_9l"], 2),
                 fmt_num(r["tx_9l"], 2)] for r in samples]
        row_h = auto_row_h(len(rows) + 1, y, 12, 18, reserve=62)
        y = draw_table(c, ["Product", "Total 9L", "CA 9L", "TX 9L"], rows,
                       MARGIN, y, widths, row_h=row_h, align_right={1, 2, 3})
        y = draw_note(
            c, "Samples are stock on hand but not stock that can be sold, so they "
               "are outside the commercial total. Including them overstated inventory "
               "by " + fmt_cases(k.get("inventory_samples_9l")) + " against the "
               "reference book, which is exactly the gap this split closes.", y - 4)
    c.showPage()


def page_revenue(c, data, page_num):
    k = data["kpis"]
    draw_header_band(c, "Revenue by Route to Market",
                     "Gross revenue — wholesale, direct to retail and DTC", page_num)
    y = PAGE_H - 1.25 * inch

    wholesale = data.get("wholesale", [])
    retail = data.get("retail", [])
    streams = data.get("dtc_streams", [])
    total = sum(v or 0 for v in (k.get("wholesale_revenue"),
                                 k.get("retail_revenue"), k.get("dtc_revenue")))

    y = draw_kpi_cards(c, [
        ("Wholesale", fmt_money(k.get("wholesale_revenue")), False),
        ("Direct to Retail", fmt_money(k.get("retail_revenue")), False),
        ("DTC & Ecommerce", fmt_money(k.get("dtc_revenue")), False),
        ("Total Gross", fmt_money(total), False),
    ], y)

    # Ranking de rutas: categórico, así que descendente.
    routes = sorted([
        ("Wholesale", k.get("wholesale_revenue") or 0),
        ("Direct to Retail", k.get("retail_revenue") or 0),
        ("DTC & Ecommerce", k.get("dtc_revenue") or 0),
    ], key=lambda t: t[1], reverse=True)

    y = draw_section_title(c, "Gross revenue by route", y)
    reserve = (len(wholesale) + len(retail) + len(streams) + 8) * 13 + 70
    row_h = auto_row_h(len(routes), y, 18, 30, reserve=reserve)
    y = draw_horizontal_bars(c, [r[0] for r in routes], [r[1] for r in routes],
                             {"Wholesale": T.PRIMARY,
                              "Direct to Retail": T.ACCENT,
                              "DTC & Ecommerce": colors.HexColor("#1F6E6E")},
                             MARGIN, y, CONTENT_W, row_h=row_h)

    y = draw_section_title(c, "Top wholesale customers", y - 6)
    rows = [[r["customer"], fmt_num(r["cases_9l"], 2), fmt_money2(r["revenue"])]
            for r in wholesale[:8]]
    if rows:
        rows.append(["TOTAL WHOLESALE", "", fmt_money2(k.get("wholesale_revenue"))])
    widths = scale_widths([4.0, 1.3, 1.8])
    row_h = auto_row_h(len(rows) + 1, y, 12, 19,
                       reserve=(len(retail) + len(streams) + 6) * 13 + 40)
    if rows:
        y = draw_table(c, ["Customer", "9L Cases", "Gross Revenue"], rows,
                       MARGIN, y, widths, row_h=row_h,
                       total_row_idx=len(rows) - 1, align_right={1, 2})
    else:
        y = draw_empty_state(c, "No wholesale orders in this data set.", y)

    y = draw_section_title(c, "Direct to retail and DTC streams", y - 10)
    rows = [[r["customer"], "Direct to retail", fmt_num(r["cases_9l"], 2),
             fmt_money2(r["revenue"])] for r in retail[:6]]
    rows += [[r["stream"], "DTC", fmt_num(r["bottles"], 0) + " btl",
              fmt_money2(r["revenue"])] for r in streams]
    widths = scale_widths([3.2, 1.5, 1.3, 1.6])
    row_h = auto_row_h(len(rows) + 1, y, 12, 19, reserve=20)
    if rows:
        y = draw_table(c, ["Account / Stream", "Route", "Volume", "Gross Revenue"],
                       rows, MARGIN, y, widths, row_h=row_h, align_right={2, 3})
    else:
        y = draw_empty_state(c, "No direct-to-retail or DTC activity recorded.", y)
    c.showPage()


def page_depletions(c, data, page_num):
    k = data["kpis"]
    draw_header_band(c, "Depletions",
                     "Sell-through by territory · " +
                     blank_if_missing(data.get("period_label")), page_num)
    y = PAGE_H - 1.25 * inch

    terr = data.get("territories", [])
    monthly = data.get("depletions_monthly", [])

    y = draw_kpi_cards(c, [
        ("Bottles YTD", fmt_num(k.get("depletions_bottles_ytd")), False),
        ("9L Cases YTD", fmt_cases(k.get("depletions_cases_9l_ytd")), False),
        ("Active Accounts", fmt_num(k.get("accounts_active")), False),
    ], y)

    y = draw_section_title(c, "By territory", y)
    reserve = (len(monthly) + len(terr) + 6) * 14 + 90
    row_h = auto_row_h(max(1, len(terr)), y, 18, 34, reserve=reserve)
    if terr:
        y = draw_horizontal_bars(c, [t["territory"] for t in terr],
                                 [t["cases_9l_ytd"] for t in terr],
                                 {"California": T.PRIMARY, "Texas": T.ACCENT},
                                 MARGIN, y, CONTENT_W, row_h=row_h,
                                 value_fmt=fmt_cases)
        rows = [[t["territory"], fmt_num(t["bottles_ytd"]),
                 fmt_num(t["cases_9l_ytd"], 2), fmt_num(t["accounts"])]
                for t in terr]
        rows.append(["TOTAL", fmt_num(k.get("depletions_bottles_ytd")),
                     fmt_num(k.get("depletions_cases_9l_ytd"), 2), ""])
        widths = scale_widths([2.2, 1.6, 1.5, 1.4])
        row_h = auto_row_h(len(rows) + 1, y, 13, 20,
                           reserve=(len(monthly) + 4) * 14 + 60)
        y = draw_table(c, ["Territory", "Bottles YTD", "9L Cases YTD", "Accounts"],
                       rows, MARGIN, y, widths, row_h=row_h,
                       total_row_idx=len(rows) - 1, align_right={1, 2, 3})
    else:
        y = draw_empty_state(c, "No territory reported depletions.", y)

    y = draw_section_title(c, "Month by month", y - 10)
    if monthly:
        # Serie de TIEMPO: orden de calendario. Reordenarla de mayor a menor
        # destruiría el eje, así que va como tabla y no como ranking.
        rows = [[m["month"], fmt_num(m.get("bottles")), fmt_num(m.get("ca")),
                 fmt_num(m.get("tx"))] for m in monthly]
        widths = scale_widths([1.4, 1.8, 1.6, 1.6])
        row_h = auto_row_h(len(rows) + 1, y, 12, 19, reserve=56)
        y = draw_table(c, ["Month", "Bottles", "California", "Texas"], rows,
                       MARGIN, y, widths, row_h=row_h, align_right={1, 2, 3})
        y = draw_note(
            c, "Calendar order, not ranked: this is a time series. The Texas feed is "
               "a weekly snapshot with no transaction date, so its months are "
               "cumulative as reported by the distributor rather than reconstructed.",
            y - 4)
    else:
        y = draw_empty_state(c, "No monthly depletion detail available.", y)
    c.showPage()


def page_mix_and_reps(c, data, page_num):
    draw_header_band(c, "Product Mix and Sales Team",
                     "Bottles depleted by SKU and by salesperson", page_num)
    y = PAGE_H - 1.25 * inch

    sku = data.get("sku_mix", [])
    reps = data.get("reps", [])

    y = draw_section_title(c, "Bottles by SKU", y)
    reserve = (len(reps) + 4) * 15 + 120
    row_h = auto_row_h(max(1, len(sku)), y, 15, 26, reserve=reserve)
    if sku:
        y = draw_horizontal_bars(c, [s["sku"] for s in sku],
                                 [s["bottles"] for s in sku],
                                 {s["sku"]: _product_color(s["sku"]) for s in sku},
                                 MARGIN, y, CONTENT_W, row_h=row_h,
                                 value_fmt=lambda v: fmt_num(v) + " btl")
    else:
        y = draw_empty_state(c, "No SKU-level volume in this data set.", y)

    y = draw_section_title(c, "Volume by salesperson", y - 8)
    if reps:
        total_rep = sum(r["bottles"] or 0 for r in reps)
        rows = [[r["rep"], fmt_num(r["bottles"]),
                 fmt_pct(r["bottles"] / total_rep * 100 if total_rep else None)]
                for r in reps]
        rows.append(["TOTAL", fmt_num(total_rep), "100.0%"])
        widths = scale_widths([3.6, 1.7, 1.4])
        row_h = auto_row_h(len(rows) + 1, y, 13, 22, reserve=64)
        y = draw_table(c, ["Salesperson", "Bottles", "Share"], rows,
                       MARGIN, y, widths, row_h=row_h,
                       total_row_idx=len(rows) - 1, align_right={1, 2})
        if not data.get("account_map_used"):
            y = draw_note(
                c, "Salesperson attribution is an estimate: it is inferred from the "
                   "account name, because no account-to-salesperson table exists in "
                   "the source files. Supplying one (account, salesperson, channel) "
                   "turns this page from estimated into exact.", y - 4)
    else:
        y = draw_empty_state(c, "No salesperson attribution available.", y)
    c.showPage()


def page_accounts(c, data, page_num):
    draw_header_band(c, "Key Accounts",
                     "Ranked by bottles across every source", page_num)
    y = PAGE_H - 1.25 * inch

    accounts = data.get("accounts", [])
    if not accounts:
        draw_empty_state(c, "No account-level detail in this data set.", y)
        c.showPage()
        return

    top = accounts[:22]
    y = draw_section_title(c, f"Top {len(top)} accounts", y)
    rows = [[a["account"], fmt_num(a["bottles"]), a["last_order"],
             a["salesperson"], a["channel"]] for a in top]
    widths = scale_widths([2.7, 1.0, 1.1, 1.5, 1.4])
    row_h = auto_row_h(len(rows) + 1, y, 12, 22, reserve=70)
    y = draw_table(c, ["Account", "Bottles", "Last Order", "Salesperson", "Channel"],
                   rows, MARGIN, y, widths, row_h=row_h, align_right={1})
    y = draw_note(
        c, f"{fmt_num(len(accounts))} accounts appear across the distributor and "
           "Park Street files; the strongest are listed here. Channel is inferred "
           "from the account name, so an account whose name gives no clue reads as "
           "unknown rather than being guessed into a bucket.", y - 6)
    c.showPage()


def page_gaps(c, data, page_num):
    """Lo que este reporte NO puede afirmar, con su motivo."""
    draw_header_band(c, "Scope and Data Gaps",
                     "What this report does not claim, and why", page_num)
    y = PAGE_H - 1.3 * inch

    gaps = data.get("gaps", {}) or {}
    entries = [
        ("Gross margin is not reported",
         gaps.get("gross_margin") or
         "No per-SKU cost of goods exists in the source files, so margin cannot be "
         "computed. Every monetary figure in this report is gross revenue."),
    ]
    if gaps.get("account_mapping"):
        entries.append(("Salesperson and channel are estimated",
                        gaps["account_mapping"]))
    entries.append((
        "Texas depletions have no transaction date",
        "The Favorite Brands feed is a weekly cumulative snapshot per month, not a "
        "transaction log. Texas volume is therefore accurate as a total but cannot "
        "be split into weeks the way California can."))
    entries.append((
        "Sample stock is excluded from the commercial total",
        "Lines flagged as not sellable are real stock on hand but cannot be sold, so "
        "they are reported separately. This is what reconciles the inventory total "
        "against the reference book."))

    block_h = sum(30 + 3 * 13 for _ in entries) + 40
    y = center_block(y, block_h)

    y = draw_paragraph(
        c, "A report is only useful if its limits are as visible as its numbers. "
           "Each item below is a question this data cannot answer yet, and what it "
           "would take to answer it.",
        MARGIN, y, CONTENT_W, size=10, color=T.PRIMARY)
    y -= 12

    for title, body in entries:
        c.setFillColor(T.PRIMARY)
        c.setFont(T.FONT_BOLD, 11)
        c.drawString(MARGIN, y, fit_text(title, CONTENT_W, T.FONT_BOLD, 11))
        c.setStrokeColor(T.ACCENT)
        c.setLineWidth(1.0)
        c.line(MARGIN, y - 5, MARGIN + 1.1 * inch, y - 5)
        y -= 20
        y = draw_paragraph(c, body, MARGIN, y, CONTENT_W, size=9.5)
        y -= 12
    c.showPage()


# ==============================================================================
# ENTRADA
# ==============================================================================
def build_loco_pdf(output_path: str | Path, data_dir=None, account_map=None,
                   data: dict | None = None,
                   lang: str = T.DEFAULT_LANG_PDF) -> Path:
    # Este reporte nace con parte de su texto en español: generarlo en
    # inglés también requiere traducir, en el sentido contrario.
    T.set_lang(lang)
    use_theme(LOCO_THEME)
    if data is None:
        data = process_loco_data(data_dir, account_map)

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(out), pagesize=letter)
    # Envolver el canvas cubre los `drawString` directos de portadas y pies,
    # que no pasan por los ayudantes de maquetación.
    T.localize_canvas(c)
    c.setTitle("Loco Tequila USA — Executive Business Report "
               f"({blank_if_missing(data.get('period_label'))})")

    page_cover(c, data)
    page_inventory(c, data, 2)
    page_revenue(c, data, 3)
    page_depletions(c, data, 4)
    page_mix_and_reps(c, data, 5)
    page_accounts(c, data, 6)
    page_gaps(c, data, 7)
    c.save()

    k = data["kpis"]
    print(f"PDF de Loco Tequila generado: {out}")
    print(f"  Periodo:            {blank_if_missing(data.get('period_label'))}")
    print(f"  Inventario 9L:      {k['inventory_total_9l']:,.2f} "
          f"(CA {k['inventory_ca_9l']:,.2f} · TX {k['inventory_tx_9l']:,.2f})"
          f"  [+{k['inventory_samples_9l']:,.2f} no vendible]")
    print(f"  Ingreso mayorista:  ${k['wholesale_revenue']:,.2f}")
    print(f"  Depletions YTD:     {k['depletions_cases_9l_ytd']:,.2f} cajas 9L")
    return out


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError, OSError):
            pass

    ap = argparse.ArgumentParser(
        description="Genera el reporte ejecutivo de Loco Tequila USA en PDF.")
    ap.add_argument("--data-dir", default=None)
    ap.add_argument("--account-map", default=None)
    ap.add_argument("--output", default=None)
    args = ap.parse_args(argv)

    out = args.output or str(PROJECT_ROOT / "Output" / "loco_tequila_usa_report.pdf")
    build_loco_pdf(out, args.data_dir, args.account_map)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
