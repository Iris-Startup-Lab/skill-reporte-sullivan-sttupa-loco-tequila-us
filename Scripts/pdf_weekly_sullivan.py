"""
================================================================================
 SULLIVAN RUTHERFORD ESTATE — REPORTE SEMANAL EN PDF  (to_do §I.2.4)
================================================================================
Contraparte imprimible del dashboard semanal. Cubre las tres piezas de la
cadencia semanal: la venta DTC consolidada, las cuentas por cobrar de
distribución con su semáforo de antigüedad, y las depletions de sell-through.

Toda la maquetación sale de `pdf_common`, así que este archivo solo decide QUÉ
va en cada página; el CÓMO (alturas que se adaptan, texto que se ajusta, dato
ausente que se vuelve "—") es compartido con los otros tres PDF.

Dos decisiones que conviene tener presentes al leerlo:

* **El periodo no se escribe a mano.** Sale del dato (`Order Paid Date`), igual
  que el nombre del archivo. Un reporte cuyo título contradice su contenido es
  peor que no tener reporte.
* **Las series temporales no se reordenan.** La regla de "barras de mayor a
  menor" aplica a rankings categóricos. Reordenar un eje de tiempo lo destruye,
  así que aquí los meses de depletions van como tabla en orden de calendario.
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
    BOTTOM_LIMIT,
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
from sullivan_weekly_processor import (  # noqa: E402
    UNCLASSIFIED,
    process_sullivan_weekly_series,
    weekly_output_name,
)

PROJECT_ROOT = _HERE.parent

# Paleta por categoría de canal, consistente con el dashboard: el mismo canal
# lleva el mismo color en HTML y en PDF.
CHANNEL_COLORS = {
    "Tasting Room": colors.HexColor("#C79F6C"),
    "Telesales": colors.HexColor("#003057"),
    "Founder's Club": colors.HexColor("#451B0F"),
    "Estate Club": colors.HexColor("#8C2F2F"),
    "Web / Ecommerce": colors.HexColor("#A67C52"),
    "Events": colors.HexColor("#2C4F73"),
    "Corporate": colors.HexColor("#55698C"),
    "Friends & Family": colors.HexColor("#7E85A5"),
    UNCLASSIFIED: colors.HexColor("#656565"),
}
AGING_COLORS = {
    "0–15 days": colors.HexColor("#1D6B36"),
    "16–30 days": colors.HexColor("#A67C52"),
    "30+ days (overdue)": colors.HexColor("#8C2F2F"),
}


def _channel_color(name: str):
    """Color del canal. Tock llega con la base entre paréntesis
    ('Tock (Net Rec.)'), así que se busca por prefijo."""
    if name in CHANNEL_COLORS:
        return CHANNEL_COLORS[name]
    if str(name).startswith("Tock"):
        return colors.HexColor("#A7A1BE")
    return T.ACCENT


# ==============================================================================
# PÁGINAS
# ==============================================================================
def page_cover(c, data):
    k = data["kpis"]
    c.setFillColor(T.PRIMARY)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

    logo = logo_data("sullivan")
    y = PAGE_H - 2.5 * inch
    if logo:
        try:
            c.drawImage(logo, (PAGE_W - 2.2 * inch) / 2, y, width=2.2 * inch,
                        height=0.9 * inch, mask="auto",
                        preserveAspectRatio=True, anchor="c")
            y -= 0.5 * inch
        except Exception:
            pass
    if not logo:
        c.setFillColor(colors.white)
        c.setFont(T.FONT_BOLD, 30)
        c.drawCentredString(PAGE_W / 2, y, "SULLIVAN")
        c.setFont(T.FONT_REGULAR, 11)
        c.drawCentredString(PAGE_W / 2, y - 24, "R U T H E R F O R D   E S T A T E")
        y -= 0.75 * inch

    c.setFillColor(T.ACCENT)
    c.setLineWidth(1.2)
    c.setStrokeColor(T.ACCENT)
    c.line(PAGE_W / 2 - 1.4 * inch, y, PAGE_W / 2 + 1.4 * inch, y)

    c.setFillColor(colors.white)
    c.setFont(T.FONT_BOLD, 22)
    c.drawCentredString(PAGE_W / 2, y - 0.55 * inch, "Weekly Operating Report")
    c.setFont(T.FONT_REGULAR, 12)
    c.drawCentredString(PAGE_W / 2, y - 0.85 * inch,
                        "DTC Sales · Distribution Receivables · Depletions")

    c.setFillColor(T.ACCENT)
    c.setFont(T.FONT_BOLD, 15)
    c.drawCentredString(PAGE_W / 2, y - 1.4 * inch,
                        blank_if_missing(data.get("period_label")))
    c.setFillColor(colors.white)
    c.setFont(T.FONT_REGULAR, 10)
    c.drawCentredString(PAGE_W / 2, y - 1.68 * inch,
                        blank_if_missing(data.get("week_label")))

    # Tres cifras de portada, una por cada bloque del reporte.
    box_y = 3.0 * inch
    items = [
        ("TOTAL DTC SALES", fmt_money(k.get("total_dtc_sales"))),
        ("OPEN PO BALANCE", fmt_money(k.get("total_open_pos_amount"))),
        ("DEPLETIONS", fmt_cases(k.get("depletions_9l_cases"))),
    ]
    w = CONTENT_W / 3
    for i, (label, value) in enumerate(items):
        cx = MARGIN + w * i + w / 2
        c.setFillColor(T.ACCENT)
        c.setFont(T.FONT_REGULAR, 8)
        c.drawCentredString(cx, box_y + 0.32 * inch, label)
        c.setFillColor(colors.white)
        size = 18.0
        while size > 10 and T.pdfmetrics.stringWidth(value, T.FONT_BOLD, size) > w - 12:
            size -= 0.5
        c.setFont(T.FONT_BOLD, size)
        c.drawCentredString(cx, box_y, value)

    c.setFillColor(colors.HexColor("#7F93A5"))
    c.setFont(T.FONT_REGULAR, 8)
    c.drawCentredString(PAGE_W / 2, 1.15 * inch,
                        "Cutoff " + blank_if_missing(data.get("date_closing")) +
                        "  ·  Tock basis: " +
                        ("Net Receivable" if data.get("tock_basis_used") == "net_receivable"
                         else "Net Sales"))
    c.showPage()


def page_dtc(c, data, page_num):
    """Mezcla de canales DTC. Barras de mayor a menor y tabla con participación."""
    k = data["kpis"]
    draw_header_band(c, "DTC Sales by Channel",
                     blank_if_missing(data.get("period_label")), page_num)
    y = PAGE_H - 1.25 * inch

    y = draw_kpi_cards(c, [
        ("Total DTC Sales", fmt_money(k.get("total_dtc_sales")), False),
        ("Leading Channel", fit_text(blank_if_missing(k.get("top_channel_name")),
                                     1.9 * inch, T.FONT_BOLD, 13), False),
        ("Its Share", fmt_pct(k.get("top_channel_pct")), False),
        ("Cash Received", fmt_money(k.get("cash_received")), False),
    ], y)

    mix = [m for m in data.get("channel_mix", []) if m.get("amount") is not None]
    total = k.get("total_dtc_sales") or 0

    y = draw_section_title(c, "Net sales by channel", y)

    # La gráfica ocupa como máximo media hoja para que la tabla quepa entera
    # debajo; row_h se adapta al número de canales.
    chart_rows = len(mix)
    reserve_for_table = (chart_rows + 2) * 15 + 30
    row_h = auto_row_h(chart_rows, y, 15, 26, reserve=reserve_for_table)
    y = draw_horizontal_bars(c, [m["channel"] for m in mix],
                             [m["amount"] for m in mix],
                             {m["channel"]: _channel_color(m["channel"]) for m in mix},
                             MARGIN, y, CONTENT_W, row_h=row_h)

    y -= 6
    rows = []
    for m in mix:
        share = (m["amount"] / total * 100) if total else None
        rows.append([m["channel"], m.get("category", BLANK),
                     fmt_money2(m["amount"]), fmt_pct(share)])
    rows.append(["TOTAL DTC", "", fmt_money2(total), "100.0%"])

    widths = scale_widths([2.7, 1.5, 1.7, 1.0])
    row_h = auto_row_h(len(rows) + 1, y, 13, 20, reserve=8)
    y = draw_table(c, ["Channel", "Source", "Net Sales", "Share"], rows,
                   MARGIN, y, widths, row_h=row_h,
                   total_row_idx=len(rows) - 1, align_right={2, 3})

    unc = k.get("unclassified_amount") or 0
    if unc:
        y = draw_note(
            c,
            f"{fmt_money2(unc)} across {fmt_num(k.get('unclassified_orders'))} order(s) "
            f"sits in {UNCLASSIFIED}: Club-channel orders that name neither the Estate nor "
            "the Founder's program. The amount is included in the DTC total so the week "
            "still balances; the detail page lists every order so it can be fixed at the "
            "source in Commerce7.", y)
    c.showPage()


def page_trend(c, series, page_num):
    """
    La serie de semanas cargadas, en orden de CALENDARIO.

    No es un ranking: reordenar de mayor a menor destruiría el eje temporal,
    que es exactamente lo que aquí se quiere leer. La regla de barras
    descendentes del repo aplica a categorías, no a series de tiempo, y por eso
    este bloque es una tabla y no una gráfica de barras.
    """
    draw_header_band(c, "Weekly Trend",
                     f"{len(series)} weeks loaded · "
                     f"{blank_if_missing(series[0].get('date_closing'))} to "
                     f"{blank_if_missing(series[-1].get('date_closing'))}", page_num)
    y = PAGE_H - 1.25 * inch

    totals = [w["kpis"].get("total_dtc_sales") for w in series]
    live = [t for t in totals if t is not None]
    best = max(series, key=lambda w: w["kpis"].get("total_dtc_sales") or 0)
    worst = min(series, key=lambda w: w["kpis"].get("total_dtc_sales") or 0)
    avg = (sum(live) / len(live)) if live else None

    y = draw_kpi_cards(c, [
        ("Weeks Loaded", fmt_num(len(series)), False),
        ("Best Week", fmt_money(best["kpis"].get("total_dtc_sales")), False),
        ("Weakest Week", fmt_money(worst["kpis"].get("total_dtc_sales")), False),
        ("Weekly Average", fmt_money(avg), False),
    ], y)

    y = draw_section_title(c, "Week by week", y)

    rows = []
    for wk in series:
        k = wk.get("kpis", {})
        wow = k.get("wow_pct_change")
        rows.append([
            blank_if_missing(wk.get("date_closing")),
            fmt_money2(k.get("total_dtc_sales")),
            (("+" if wow >= 0 else "") + f"{wow:.1f}%") if wow is not None else BLANK,
            fmt_money2(k.get("cash_received")),
            fmt_money2(k.get("total_open_pos_amount")),
            fmt_num(k.get("depletions_9l_cases"), 2),
        ])

    widths = scale_widths([1.15, 1.35, 0.85, 1.25, 1.3, 0.95])
    row_h = auto_row_h(len(rows) + 1, y, 14, 22, reserve=150)
    y = draw_table(c, ["Week ending", "Total DTC", "WoW", "Cash received",
                       "Open POs", "9L cases"],
                   rows, MARGIN, y, widths, row_h=row_h,
                   align_right={1, 2, 3, 4, 5})

    y = draw_note(
        c,
        f"These are every week folder found in the source directory. WoW compares "
        f"each week with the one immediately before it in this series; the first "
        f"week has no prior week, so it reports no change rather than 0%, which "
        f"would claim it did not move. The interactive dashboard carries the same "
        f"series with a week selector.", y)
    c.showPage()


def page_receivables(c, data, page_num):
    """Antigüedad de las cuentas por cobrar y el detalle de lo vencido."""
    k = data["kpis"]
    draw_header_band(c, "Distribution Receivables",
                     "Park Street invoices · standard terms net 30", page_num)
    y = PAGE_H - 1.25 * inch

    overdue_amt = k.get("overdue_30_amount") or 0
    y = draw_kpi_cards(c, [
        ("Open PO Balance", fmt_money(k.get("total_open_pos_amount")), False),
        ("Open Invoices", fmt_num(k.get("open_invoices_count")), False),
        ("Cases in Pipeline", fmt_num(k.get("total_open_cases")), False),
        ("Overdue > 30 Days", fmt_money(overdue_amt), overdue_amt > 0),
    ], y)

    aging = data.get("po_aging", [])
    y = draw_section_title(c, "Open balance by age bracket", y)
    overdue = data.get("overdue_details", [])
    reserve = (len(overdue) + 3) * 16 + 60 if overdue else 90
    row_h = auto_row_h(len(aging), y, 20, 40, reserve=reserve)
    y = draw_horizontal_bars(c, [b["bucket"] for b in aging],
                             [b["amount"] for b in aging],
                             {b["bucket"]: AGING_COLORS.get(b["bucket"], T.ACCENT)
                              for b in aging},
                             MARGIN, y, CONTENT_W, row_h=row_h)

    y -= 10
    y = draw_section_title(c, "Invoices past 30 days", y)
    if not overdue:
        y = draw_empty_state(c, "Nothing past terms this week. Every open invoice "
                                "is inside the 30-day window.", y)
    else:
        rows = [[blank_if_missing(r.get("invoice")),
                 blank_if_missing(r.get("customer")),
                 blank_if_missing(r.get("market")),
                 f"{fmt_num(r.get('aging'))} d",
                 fmt_money2(r.get("balance"))] for r in overdue]
        rows.append(["", "TOTAL OVERDUE", "", "", fmt_money2(overdue_amt)])
        widths = scale_widths([1.2, 2.9, 0.8, 0.8, 1.2])
        row_h = auto_row_h(len(rows) + 1, y, 14, 24, reserve=54)
        y = draw_table(c, ["Invoice", "Customer", "Market", "Age", "Balance"],
                       rows, MARGIN, y, widths, row_h=row_h,
                       total_row_idx=len(rows) - 1, align_right={3, 4})
        y = draw_note(
            c, "Anything in this table is cash that should already be collected. "
               "The 30-day mark is the standard term with Park Street, not a "
               "target: past it, the balance is late.", y - 6)
    c.showPage()


def page_depletions(c, data, page_num):
    """Sell-through: lo que los distribuidores movieron a las cuentas."""
    k = data["kpis"]
    draw_header_band(c, "Depletions",
                     "Sell-through in 9-litre cases · " +
                     blank_if_missing(k.get("depletions_period")), page_num)
    y = PAGE_H - 1.25 * inch

    by_state = data.get("depletions_by_state", [])
    live = [s for s in by_state if s.get("live")]
    top = live[0] if live else None
    y = draw_kpi_cards(c, [
        ("Depletions Volume", fmt_cases(k.get("depletions_9l_cases")), False),
        ("States Reporting", f"{fmt_num(len(live))} of {fmt_num(len(by_state))}", False),
        ("Leading State", blank_if_missing(top.get("state")) if top else BLANK, False),
        ("Its Volume", fmt_cases(top.get("cases")) if top else BLANK, False),
    ], y)

    plotted = [s for s in live if (s.get("cases") or 0) > 0]
    y = draw_section_title(c, "By state", y)
    reserve = (len(by_state) + 4) * 14 + 130
    row_h = auto_row_h(max(1, len(plotted)), y, 16, 30, reserve=reserve)
    if plotted:
        y = draw_horizontal_bars(c, [s["state"] for s in plotted],
                                 [s["cases"] for s in plotted],
                                 T.PRIMARY, MARGIN, y, CONTENT_W,
                                 row_h=row_h, value_fmt=fmt_cases)
    else:
        y = draw_empty_state(c, "No state reported depletions in this period.", y)

    y -= 6
    rows = [[blank_if_missing(s.get("state")), fmt_cases(s.get("cases")),
             "Live feed" if s.get("live") else "No sell-through feed"]
            for s in by_state]
    widths = scale_widths([1.0, 1.4, 2.6])
    row_h = auto_row_h(len(rows) + 1, y, 12, 18, reserve=120)
    y = draw_table(c, ["State", "9L Cases", "Feed status"], rows,
                   MARGIN, y, widths, row_h=row_h, align_right={1})

    y = draw_section_title(c, "By distributor", y - 10)
    dist = data.get("depletions_by_distributor", [])
    rows = [[blank_if_missing(d.get("distributor")), fmt_cases(d.get("cases")),
             blank_if_missing(d.get("note"))] for d in dist]
    widths = scale_widths([1.6, 1.1, 3.6])
    row_h = auto_row_h(len(rows) + 1, y, 13, 22, reserve=52)
    y = draw_table(c, ["Distributor", "9L Cases", "Note"], rows,
                   MARGIN, y, widths, row_h=row_h, align_right={1})

    y = draw_note(
        c, "Depletions measure what left the distributor toward accounts, not what "
           "was shipped to the distributor. Markets marked without a feed are real "
           "markets whose distributor does not report sell-through, so their volume "
           "is unknown rather than zero.", y - 4)
    c.showPage()


def page_unclassified(c, data, page_num):
    """Auditoría de lo que la cascada no pudo asignar."""
    k = data["kpis"]
    draw_header_band(c, UNCLASSIFIED,
                     "Orders the channel rules could not assign", page_num)
    y = PAGE_H - 1.25 * inch

    detail = data.get("unclassified_detail", [])
    total = k.get("unclassified_amount") or 0
    dtc = k.get("total_dtc_sales") or 0

    y = draw_kpi_cards(c, [
        ("Unclassified Amount", fmt_money2(total), total > 0),
        ("Orders Affected", fmt_num(len(detail)), False),
        ("Share of DTC", fmt_pct(total / dtc * 100 if dtc else None), False),
    ], y)

    if not detail:
        draw_empty_state(
            c, "Nothing unclassified this week. Every order matched a channel "
               "rule, so the DTC total needs no diagnostic row.", y)
        c.showPage()
        return

    rows = [[blank_if_missing(r.get("order")),
             blank_if_missing(r.get("package")),
             blank_if_missing(r.get("title")),
             blank_if_missing(r.get("reason")),
             fmt_money2(r.get("amount"))] for r in detail]
    rows.append(["", "", "", "TOTAL", fmt_money2(total)])

    widths = scale_widths([1.0, 1.7, 1.7, 2.1, 1.1])
    # Se centra el bloque completo (nota + tabla) en el espacio libre: antes una
    # tabla de pocas filas quedaba pegada arriba con ~250 pt de hueco debajo.
    note_h = 62
    block_h = (len(rows) + 1) * 20 + note_h + 34
    y = center_block(y, block_h)
    y = draw_section_title(c, "Every unassigned order", y)
    row_h = auto_row_h(len(rows) + 1, y, 14, 24, reserve=note_h + 16)
    y = draw_table(c, ["Order", "Club Package", "Club Title", "Reason", "Net Sales"],
                   rows, MARGIN, y, widths, row_h=row_h,
                   total_row_idx=len(rows) - 1, align_right={4})
    draw_note(
        c, "Action required: these are Club-channel orders with no program named in "
           "either Club Package or Club Title, usually marked as Club by hand from "
           "the POS panel. They are counted in the DTC total so the week balances, "
           "and listed here so the source records can be corrected. Fixing them in "
           "Commerce7 removes this page.", y - 8)
    c.showPage()


# ==============================================================================
# ENTRADA
# ==============================================================================
def build_weekly_pdf(data_dir: str | Path, output_path: str | Path,
                     tock_basis: str = "net_receivable",
                     data: dict | None = None,
                     weeks: list | None = None,
                     lang: str = T.DEFAULT_LANG_PDF) -> Path:
    """
    Un PDF no puede llevar selector de semana, así que documenta la MÁS
    RECIENTE. `weeks` permite pasar la serie completa: de ahí sale la tabla de
    tendencia y el WoW, que antes no existían porque solo había una semana.
    """
    T.set_lang(lang)
    use_theme(SULLIVAN_THEME)
    if weeks:
        series = list(weeks)
        data = series[-1]
    elif data is not None:
        series = [data]
    else:
        series = process_sullivan_weekly_series(Path(data_dir), tock_basis=tock_basis)
        data = series[-1]

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(out), pagesize=letter)
    # Envolver el canvas cubre los `drawString` directos de portadas y pies,
    # que no pasan por los ayudantes de maquetación.
    T.localize_canvas(c)
    c.setTitle(f"Sullivan Rutherford Estate — Weekly Report "
               f"({blank_if_missing(data.get('period_label'))})")

    page_cover(c, data)
    page_dtc(c, data, 2)
    # La tendencia solo tiene sentido con más de una semana; con una sola el
    # reporte sale con las mismas 5 páginas de siempre.
    n = 3
    if len(series) > 1:
        page_trend(c, series, n)
        n += 1
    page_receivables(c, data, n)
    page_depletions(c, data, n + 1)
    page_unclassified(c, data, n + 2)
    c.save()

    k = data["kpis"]
    print(f"PDF semanal generado: {out}")
    print(f"  Periodo:      {blank_if_missing(data.get('period_label'))}")
    if len(series) > 1:
        print(f"  Semanas:      {len(series)} en la serie "
              f"({series[0]['date_closing']} .. {series[-1]['date_closing']})")
    print(f"  Total DTC:    ${k['total_dtc_sales']:,.2f}")
    print(f"  Open POs:     ${k['total_open_pos_amount']:,.2f}")
    print(f"  Depletions:   {k['depletions_9l_cases']} cajas 9L")
    print(f"  {UNCLASSIFIED}: ${k['unclassified_amount']:,.2f} "
          f"({k['unclassified_orders']} orden/es)")
    return out


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError, OSError):
            pass

    ap = argparse.ArgumentParser(
        description="Genera el reporte semanal de Sullivan en PDF.")
    ap.add_argument("--data-dir", default=None,
                    help="Carpeta con los 4 archivos de la semana. Por defecto usa "
                         "los datos del cliente si existen, y si no, el demo.")
    ap.add_argument("--tock-basis", choices=["net_receivable", "net_sales"],
                    default="net_receivable")
    ap.add_argument("--output", default=None)
    args = ap.parse_args(argv)

    if args.data_dir:
        data_dir = Path(args.data_dir)
    else:
        data_dir = PROJECT_ROOT / "Client_Data" / "Sullivan_data" / "Weekly"
        if not data_dir.exists():
            data_dir = PROJECT_ROOT / "Data_for_demo" / "Sullivan_weekly_demo"

    series = process_sullivan_weekly_series(data_dir, tock_basis=args.tock_basis)
    out = args.output or str(
        PROJECT_ROOT / "Output" /
        weekly_output_name(series[-1], prefix="sullivan_weekly_report", suffix=".pdf"))
    build_weekly_pdf(data_dir, out, tock_basis=args.tock_basis, weeks=series)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
