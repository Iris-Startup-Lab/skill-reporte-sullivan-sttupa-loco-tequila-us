"""
================================================================================
 LOCO TEQUILA USA — LIBRO DE EXCEL DE REFERENCIA (segunda validación)
================================================================================
Entregable nuevo, solicitado por el cliente además del tablero HTML: un libro
de Excel con un dataset principal y, en cada hoja siguiente, una tabla cruzada
y una gráfica NATIVA de Excel que referencian ese dataset por fórmula.

POR QUÉ FÓRMULAS Y NO SOLO VALORES
-----------------------------------
Si cada hoja de vista solo llevara números ya calculados en Python, el libro
sería una foto: correcta hoy, pero sin manera de que alguien en Excel verifique
de dónde salió un total. Aquí cada total de vista es una fórmula `SUMIFS` que
apunta a la hoja `Dataset` — así que el propio Excel vuelve a sumar la tabla de
hechos al abrir el archivo. Eso es la segunda validación real: si algún día el
número de una vista no coincide con lo que el tablero HTML reporta, hay un
descuadre genuino que investigar, no una posibilidad de que dos cálculos
independientes coincidan por casualidad.

QUÉ SÍ ES ESTO Y QUÉ NO
------------------------
Openpyxl no puede crear tablas dinámicas de Excel desde cero (su propia
documentación lo dice: "it is not intended that client code should be able to
create pivot tables"). Lo que SÍ puede, y es lo que se usa aquí, es:
  - Excel Tables (`ListObject`) con nombre, que es la estructura que una tabla
    dinámica normalmente consume como origen — el dataset queda listo para que
    alguien inserte su propia dinámica en Excel con un clic (Insertar > Tabla
    dinámica > FactLoco), sin tener que seleccionar el rango a mano.
  - Gráficas NATIVAS de Excel (`BarChart`, `LineChart`) ligadas por referencia
    de celda, que es lo que el cliente pidió como "gráficas replicadas".
  - Fórmulas `SUMIFS`/`SUMPRODUCT` que reconstruyen cada total de vista a
    partir del dataset, en vez de escribir el número ya calculado.

Una plantilla con tablas dinámicas de verdad, autorizadas una sola vez en Excel
vía COM y luego solo rellenadas por este mismo módulo, es el paso siguiente
(§P.6/Fase 3b de to_do.md) y queda pendiente ahí, no aquí.
================================================================================
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import openpyxl
import pandas as pd
from openpyxl.chart import BarChart, LineChart, Reference
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import loco_tequila_us_relationships as R  # noqa: E402
import loco_attribution  # noqa: E402
import loco_data_processor as P  # noqa: E402
import loco_margin  # noqa: E402

MAROON = "6E1E28"
GOLD = "C5A059"
CREAM = "FBF8F2"

MONTH_COLS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
             "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]


# --------------------------------------------------------------------------
# Datasets
# --------------------------------------------------------------------------

def build_inventory_dataset(payload: dict) -> pd.DataFrame:
    """
    Hoja `InventoryDataset`: SKU x bodega, en formato largo.

    Deliberadamente SEPARADA de la tabla de hechos de depletions: el inventario
    es un SALDO en un punto del tiempo, las depletions son un FLUJO acumulado.
    Mezclarlas en una sola tabla de hechos arriesgaría que alguien las sume
    juntas sin darse cuenta de que son magnitudes distintas.
    """
    rows = []
    warehouse_cols = [
        ("socal_sgws_9l", "Signature SGWS — SO CAL", "CA"),
        ("norcal_sgws_9l", "Signature SGWS — NOR CAL", "CA"),
        ("parkstreet_ca_9l", "Park Street — CA", "CA"),
        ("fb_tx_9l", "Favorite Brands — TX", "TX"),
    ]
    for r in payload.get("inventory", []):
        if not r.get("sellable", True):
            continue
        for key, label, region in warehouse_cols:
            v = float(r.get(key) or 0)
            if v:
                rows.append({"SKU": r["product"], "Warehouse": label,
                            "Region": region, "Cases9L": round(v, 2)})
    cols = ["SKU", "Warehouse", "Region", "Cases9L"]
    return pd.DataFrame(rows, columns=cols) if rows else pd.DataFrame(columns=cols)


# --------------------------------------------------------------------------
# Helpers de escritura
# --------------------------------------------------------------------------

def _write_table(ws, df: pd.DataFrame, table_name: str, header_fill: str = MAROON):
    """Escribe un DataFrame como Excel Table (ListObject) nombrada. Devuelve el
    rango A1 y el número de filas de datos."""
    ws.append(list(df.columns))
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor=header_fill)
    for row in df.itertuples(index=False):
        ws.append([("" if pd.isna(v) else v) for v in row])
    n = len(df)
    if n == 0:
        return None, 0
    last_col = get_column_letter(len(df.columns))
    ref = f"A1:{last_col}{n + 1}"
    tab = Table(displayName=table_name, ref=ref)
    tab.tableStyleInfo = TableStyleInfo(
        name="TableStyleMedium9", showRowStripes=True, showFirstColumn=False)
    ws.add_table(tab)
    for i, col in enumerate(df.columns, start=1):
        width = max(10, min(38, int(df[col].astype(str).str.len().max() or 8) + 2))
        ws.column_dimensions[get_column_letter(i)].width = width
    ws.freeze_panes = "A2"
    return ref, n


def _bar_chart(ws, anchor: str, title: str, cats_ref: Reference, data_ref: Reference,
              y_title: str = ""):
    chart = BarChart()
    chart.type = "bar"  # horizontal: más legible con nombres largos de cuenta
    chart.title = title
    chart.y_axis.title = ""
    chart.x_axis.title = y_title
    chart.style = 11
    chart.add_data(data_ref, titles_from_data=True)
    chart.set_categories(cats_ref)
    chart.height = 8
    chart.width = 18
    ws.add_chart(chart, anchor)
    return chart


def _line_chart(ws, anchor: str, title: str, cats_ref: Reference, data_ref: Reference):
    chart = LineChart()
    chart.title = title
    chart.style = 12
    chart.add_data(data_ref, titles_from_data=True)
    chart.set_categories(cats_ref)
    chart.height = 8
    chart.width = 18
    ws.add_chart(chart, anchor)
    return chart


def _section_title(ws, cell: str, text: str):
    c = ws[cell]
    c.value = text
    c.font = Font(bold=True, size=13, color=MAROON)


def _note(ws, cell: str, text: str):
    ws[cell].value = text
    ws[cell].font = Font(italic=True, size=9, color="7A6A4A")


# --------------------------------------------------------------------------
# Libro completo
# --------------------------------------------------------------------------

def generate_loco_excel_reference(output_file: Path, data_dir: Optional[str] = None,
                                  account_map_path: Optional[str] = None) -> Path:
    output_file = Path(output_file)
    data_dir_resolved = str(data_dir) if data_dir else str(P.DEFAULT_DATA_DIR)

    account_map = None
    if account_map_path:
        account_map = R.load_account_map(account_map_path)
    else:
        default_map = loco_attribution.default_account_map_path()
        if default_map:
            account_map = R.load_account_map(str(default_map))

    payload = P.process_loco_data(data_dir, account_map_path)
    fact_df = R.build_fact_table(data_dir_resolved, account_map)
    inv_df = build_inventory_dataset(payload)

    wb = openpyxl.Workbook()
    wb.remove(wb.active)

    # ---------------------------------------------------------------- Dataset
    ws = wb.create_sheet("Dataset")
    fact_ref, fact_n = _write_table(ws, fact_df, "FactLoco")
    if fact_n:
        ws["K1"] = "Reference workbook — Loco Tequila USA"
        ws["K1"].font = Font(bold=True, size=12, color=MAROON)
        ws["K2"] = (f"{fact_n} rows — one per atomic depletion or DTC order "
                   "line, with month, SKU, salesperson and channel already "
                   "resolved by the attribution ladder.")
        ws["K3"] = ("Every view sheet in this workbook sums FROM this table by "
                   "formula. To add a pivot table of your own: Insert > "
                   "PivotTable > choose table 'FactLoco'.")
        for r in ("K2", "K3"):
            ws[r].font = Font(size=9, italic=True, color="4A4A4A")
            ws[r].alignment = openpyxl.styles.Alignment(wrap_text=True)
        ws.column_dimensions["K"].width = 52

    # ---------------------------------------------------------- InventoryDataset
    ws = wb.create_sheet("InventoryDataset")
    inv_ref, inv_n = _write_table(ws, inv_df, "InventoryLoco", header_fill=GOLD)
    if inv_n:
        ws["G1"] = "Inventory is a POINT-IN-TIME BALANCE, not a flow."
        ws["G1"].font = Font(bold=True, size=10, color=MAROON)
        ws["G2"] = ("Kept in a separate table from FactLoco on purpose: summing "
                   "a balance together with a flow produces a meaningless "
                   "number.")
        ws["G2"].font = Font(size=9, italic=True, color="4A4A4A")
        ws["G2"].alignment = openpyxl.styles.Alignment(wrap_text=True)
        ws.column_dimensions["G"].width = 46

    def month_cols_in(df):
        return [m for m in MONTH_COLS if m in set(df["Month"])] if len(df) else []

    fact_months = month_cols_in(fact_df)

    # ---------------------------------------------------------------- Overview
    ws = wb.create_sheet("Overview")
    _section_title(ws, "A1", "Monthly depletions — re-derived from Dataset")
    _note(ws, "A2", "Every cell below is a SUMIFS formula against FactLoco. "
                    "If this table ever disagrees with the HTML dashboard, "
                    "that disagreement is real and needs investigating.")
    ws.append([])
    ws.append(["Month", "Total bottles", "California", "Texas", "DTC"])
    for c in ws[4]:
        c.font = Font(bold=True)
    header_row = 4
    for i, m in enumerate(fact_months):
        r = header_row + 1 + i
        ws.cell(r, 1, m.title())
        ws.cell(r, 2, f"=SUMIFS(FactLoco[Bottles],FactLoco[Month],\"{m}\")")
        ws.cell(r, 3, f"=SUMIFS(FactLoco[Bottles],FactLoco[Month],\"{m}\","
                     "FactLoco[Territory],\"California\")")
        ws.cell(r, 4, f"=SUMIFS(FactLoco[Bottles],FactLoco[Month],\"{m}\","
                     "FactLoco[Territory],\"Texas\")")
        ws.cell(r, 5, f"=SUMIFS(FactLoco[Bottles],FactLoco[Month],\"{m}\","
                     "FactLoco[Territory],\"DTC\")")
    last_row = header_row + len(fact_months)
    if fact_months:
        cats = Reference(ws, min_col=1, min_row=header_row + 1, max_row=last_row)
        data = Reference(ws, min_col=2, max_col=2, min_row=header_row, max_row=last_row)
        _line_chart(ws, "G4", "Total bottles by month", cats, data)
        data3 = Reference(ws, min_col=3, max_col=4, min_row=header_row, max_row=last_row)
        _bar_chart(ws, "G20", "California vs Texas by month", cats, data3)

    # -------------------------------------------------------------- Salespeople
    ws = wb.create_sheet("Salespeople")
    _section_title(ws, "A1", "Bottles by salesperson — re-derived from Dataset")
    _note(ws, "A2", "SUMIF against FactLoco's Salesperson column. Reps ordered "
                    "highest to lowest.")
    reps = sorted({r for r in fact_df["Salesperson"].unique()} if len(fact_df) else set(),
                 key=lambda s: -float(fact_df.loc[fact_df["Salesperson"] == s, "Bottles"].sum())
                 if len(fact_df) else 0)
    ws.append([])
    ws.append(["Salesperson", "Bottles"])
    ws[4][0].font = ws[4][1].font = Font(bold=True)
    for i, rep in enumerate(reps):
        r = 5 + i
        ws.cell(r, 1, rep)
        ws.cell(r, 2, f'=SUMIF(FactLoco[Salesperson],A{r},FactLoco[Bottles])')
    if reps:
        last = 4 + len(reps)
        cats = Reference(ws, min_col=1, min_row=5, max_row=last)
        data = Reference(ws, min_col=2, max_col=2, min_row=4, max_row=last)
        _bar_chart(ws, "D4", "Bottles by salesperson", cats, data)

    # --------------------------------------------------------------- Signature
    ws = wb.create_sheet("Signature")
    _section_title(ws, "A1", "Signature depletions — California, by SKU")
    _note(ws, "A2", "SUMIFS against FactLoco filtered to Source = Signature.")
    skus_ca = sorted(
        {s for s in fact_df.loc[fact_df["Source"] == "Signature", "SKU"].unique()},
        key=lambda s: -float(fact_df.loc[(fact_df.Source == "Signature") & (fact_df.SKU == s), "Bottles"].sum())
    ) if len(fact_df) else []
    ws.append([])
    ws.append(["SKU", "Bottles YTD"])
    ws[4][0].font = ws[4][1].font = Font(bold=True)
    for i, sku in enumerate(skus_ca):
        r = 5 + i
        ws.cell(r, 1, sku)
        ws.cell(r, 2, f'=SUMIFS(FactLoco[Bottles],FactLoco[Source],"Signature",FactLoco[SKU],A{r})')
    if skus_ca:
        last = 4 + len(skus_ca)
        cats = Reference(ws, min_col=1, min_row=5, max_row=last)
        data = Reference(ws, min_col=2, max_col=2, min_row=4, max_row=last)
        _bar_chart(ws, "D4", "Signature bottles by SKU", cats, data)

    # ---------------------------------------------------------- FavoriteBrands
    ws = wb.create_sheet("FavoriteBrands")
    _section_title(ws, "A1", "Favorite Brands depletions — Texas, by premise")
    _note(ws, "A2", "Channel here comes from Favorite Brands' own PREMISE "
                    "column, not from guessing at the account name.")
    prem = sorted(
        {c for c in fact_df.loc[fact_df["Source"] == "Favorite Brands", "Channel"].unique()}
    ) if len(fact_df) else []
    ws.append([])
    ws.append(["Premise", "Bottles YTD"])
    ws[4][0].font = ws[4][1].font = Font(bold=True)
    for i, pr in enumerate(prem):
        r = 5 + i
        ws.cell(r, 1, pr)
        ws.cell(r, 2, f'=SUMIFS(FactLoco[Bottles],FactLoco[Source],"Favorite Brands",FactLoco[Channel],A{r})')
    if prem:
        last = 4 + len(prem)
        cats = Reference(ws, min_col=1, min_row=5, max_row=last)
        data = Reference(ws, min_col=2, max_col=2, min_row=4, max_row=last)
        _bar_chart(ws, "D4", "Texas bottles by premise", cats, data)

    # -------------------------------------------------------------- Inventory
    ws = wb.create_sheet("Inventory")
    _section_title(ws, "A1", "On-hand 9L cases by warehouse")
    _note(ws, "A2", "SUMIF against InventoryLoco. This is a balance: never "
                    "combined with FactLoco's flow.")
    whs = sorted({w for w in inv_df["Warehouse"].unique()},
                key=lambda w: -float(inv_df.loc[inv_df.Warehouse == w, "Cases9L"].sum())
                ) if len(inv_df) else []
    ws.append([])
    ws.append(["Warehouse", "Cases 9L"])
    ws[4][0].font = ws[4][1].font = Font(bold=True)
    for i, w in enumerate(whs):
        r = 5 + i
        ws.cell(r, 1, w)
        ws.cell(r, 2, f'=SUMIF(InventoryLoco[Warehouse],A{r},InventoryLoco[Cases9L])')
    if whs:
        last = 4 + len(whs)
        cats = Reference(ws, min_col=1, min_row=5, max_row=last)
        data = Reference(ws, min_col=2, max_col=2, min_row=4, max_row=last)
        _bar_chart(ws, "D4", "9L cases by warehouse", cats, data)

    # -------------------------------------------------------------- Attribution
    ws = wb.create_sheet("Attribution")
    _section_title(ws, "A1", "How every bottle was credited")
    _note(ws, "A2", "COUNTIFS/SUMIFS against FactLoco's AttrRule column. "
                    "Insert a PivotTable on FactLoco with AttrRule as rows to "
                    "drill into any single rule.")
    ladder = payload.get("attribution", {}).get("by_rule", [])
    ws.append([])
    ws.append(["Rule", "Label", "Bottles (formula)"])
    for c in ws[4]:
        c.font = Font(bold=True)
    for i, rule in enumerate(sorted({r["rule"] for r in ladder} or set())):
        r = 5 + i
        label = next((x["label"] for x in ladder if x["rule"] == rule), rule)
        ws.cell(r, 1, rule)
        ws.cell(r, 2, label)
        ws.cell(r, 3, f'=SUMIF(FactLoco[AttrRule],A{r},FactLoco[Bottles])')
    if ladder:
        last = 4 + len({r["rule"] for r in ladder})
        cats = Reference(ws, min_col=1, min_row=5, max_row=last)
        data = Reference(ws, min_col=3, max_col=3, min_row=4, max_row=last)
        _bar_chart(ws, "E4", "Bottles by attribution rule", cats, data)
    ws2r = 5 + len({r["rule"] for r in ladder}) + 2
    ws.cell(ws2r, 1, "Unattributed lines").font = Font(bold=True, color=MAROON)
    ws.cell(ws2r + 1, 1, "Account/order").font = Font(bold=True)
    ws.cell(ws2r + 1, 2, "Bottles").font = Font(bold=True)
    ws.cell(ws2r + 1, 3, "Reason").font = Font(bold=True)
    for i, u in enumerate(payload.get("attribution", {}).get("unattributed", [])):
        r = ws2r + 2 + i
        ws.cell(r, 1, u["account"])
        ws.cell(r, 2, u["bottles"])
        ws.cell(r, 3, u["reason"])
    ws.column_dimensions["A"].width = 30
    ws.column_dimensions["C"].width = 60

    # -------------------------------------------------------------- Validation
    ws = wb.create_sheet("Validation")
    ws.sheet_properties.tabColor = GOLD
    _section_title(ws, "A1", "Second validation — Excel re-derives every KPI")
    _note(ws, "A2", "Each 'Difference' cell must read 0. If it does not, the "
                    "HTML dashboard and this workbook disagree on a real "
                    "number and it needs investigating before either is sent "
                    "to anyone.")
    ws.append([])
    ws.append(["Measure", "Dashboard value", "Excel formula (from Dataset)", "Difference"])
    for c in ws[4]:
        c.font = Font(bold=True)
        c.fill = PatternFill("solid", fgColor=CREAM)
    k = payload["kpis"]
    checks = [
        # California + Texas es la cifra "depletions" del tablero — DELIBERADAMENTE
        # no incluye DTC, porque las depletions son venta a distribuidor/cuenta
        # (Signature + Favorite Brands) y el DTC es un canal aparte. Sumar los
        # dos SUMIF por separado en vez de contra el total evita mezclar dos
        # magnitudes que el propio tablero mantiene distintas.
        ("California + Texas depletions (bottles)",
         float(k.get("depletions_bottles_ytd") or 0),
         '=SUMIF(FactLoco[Territory],"California",FactLoco[Bottles])'
         '+SUMIF(FactLoco[Territory],"Texas",FactLoco[Bottles])'),
        ("California (bottles)", float(next((t["bottles_ytd"] for t in payload["territories"]
                                            if t["territory"] == "California"), 0)),
         '=SUMIF(FactLoco[Territory],"California",FactLoco[Bottles])'),
        ("Texas (bottles)", float(next((t["bottles_ytd"] for t in payload["territories"]
                                       if t["territory"] == "Texas"), 0)),
         '=SUMIF(FactLoco[Territory],"Texas",FactLoco[Bottles])'),
        ("DTC total (bottles)", float(sum(s["bottles"] for s in payload.get("dtc_by_store", []))),
         '=SUMIF(FactLoco[Territory],"DTC",FactLoco[Bottles])'),
        # Volumen atribuible = depletions + DTC. NO incluye el stock de
        # vendedor de Park Street (retiro a su maletero, todavía no depletado
        # a una cuenta) — ese movimiento es real pero es una magnitud distinta,
        # y por eso tampoco entra a `FactLoco`. Ver el comentario de `add()` en
        # `build_salesperson_by_week_detailed`.
        ("Total attributable volume (bottles)",
         float(payload.get("attribution", {}).get("total_bottles") or 0),
         "=SUM(FactLoco[Bottles])"),
        ("Attributed bottles", float(payload.get("attribution", {}).get("attributed_bottles") or 0),
         '=SUM(FactLoco[Bottles])-SUMIF(FactLoco[AttrRule],"R6",FactLoco[Bottles])'),
    ]
    for i, (label, dash_val, formula) in enumerate(checks):
        r = 5 + i
        ws.cell(r, 1, label)
        ws.cell(r, 2, round(dash_val, 2))
        ws.cell(r, 3, formula)
        ws.cell(r, 4, f"=ROUND(B{r}-C{r},2)")
    for row in ws.iter_rows(min_row=5, max_row=4 + len(checks), min_col=4, max_col=4):
        row[0].font = Font(bold=True)
    ws.column_dimensions["A"].width = 30
    ws.column_dimensions["C"].width = 46

    for name in ("Overview", "Salespeople", "Signature", "FavoriteBrands",
                "Inventory", "Attribution"):
        wb[name].column_dimensions["A"].width = 26

    output_file.parent.mkdir(parents=True, exist_ok=True)
    wb.save(output_file)
    return output_file


if __name__ == "__main__":
    import argparse

    for _s in (sys.stdout, sys.stderr):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError, OSError):
            pass

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data-dir", default=None)
    ap.add_argument("--account-map", default=None)
    ap.add_argument("--output", default=str(PROJECT_ROOT / "Output" / "loco_tequila_usa_reference.xlsx"))
    args = ap.parse_args()

    out = generate_loco_excel_reference(Path(args.output), args.data_dir, args.account_map)
    print(f"Libro de referencia generado: {out}")
