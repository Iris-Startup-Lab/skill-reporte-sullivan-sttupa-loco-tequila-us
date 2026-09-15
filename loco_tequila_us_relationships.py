#!/usr/bin/env python3
"""
loco_tequila_us_relationships.py
=================================

Intenta SIMULAR el Weekly Sales Report de Loco Tequila USA
("Sales Report Loco USA <fecha>.xlsx") a partir de los 8 archivos crudos que
llegan de los distribuidores (Favorite Brands en TX, Signature/Southern
Glazer's en CA vía VIPIDIG), de Park Street (wholesale sell-in, venta directa
y salidas de inventario de vendedor) y del ecommerce (Shopify + Memory
event pick-up).

Este script NO pretende ser un reemplazo exacto del proceso manual de Sara:
varias hojas del reporte dependen de una tabla maestra cuenta->vendedor->canal
y de un costo unitario (COGS) por SKU que NO vienen en ninguno de los 8
archivos crudos. Donde eso pasa, el script deja el dato como aproximación
etiquetada ("Unknown (heuristic)", GM=None, etc.) en vez de inventar un
número que parezca exacto sin serlo.

Ver `loco_tequila_us_relationships.md` (mismo repo) para la explicación
completa, tabla por tabla, de qué se validó con números reales y qué quedó
como hipótesis abierta.

Uso:
    python loco_tequila_us_relationships.py \
        --data-dir "Client_Data/Loco_tequila_usa_data" \
        --output-dir "Output/simulacion_loco_usa" \
        [--account-map mi_mapeo_cuentas.csv]

El CSV opcional de --account-map debe tener columnas: account,salesperson,channel
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
from datetime import date, datetime
from typing import Optional

import numpy as np
import openpyxl
import pandas as pd

pd.set_option("mode.chained_assignment", None)

# --------------------------------------------------------------------------
# Constantes de negocio (documentadas y validadas en el .md que acompaña a
# este script)
# --------------------------------------------------------------------------

ML_PER_9L_CASE = 9000.0
DEFAULT_BOTTLE_ML = 750.0

# Palabras clave para clasificar un SKU/nombre de producto en la categoría
# que usa el reporte (orden importa: se evalúa de arriba hacia abajo).
PRODUCT_CATEGORY_RULES = [
    (r"NSS|NOT SELLABLE|SAMPLE", "NOT SELLABLE - SAMPLES ONLY"),
    # OJO orden: varios SKU llevan "BLANCO" en el nombre aunque el producto
    # real sea otro (ej. Signature nombra la Puro Corazon como
    # "BLANCO PURO CORAZON 80 750ML"), así que las reglas mas especificas
    # deben evaluarse ANTES que "BLANCO" o quedan mal clasificadas.
    (r"ANGEL|MXD|ANGELEZ", "Ltd Etn Angeles Puro"),
    (r"PURO ?COYOTE|PURO ?HUMMBIRD|PURO ?SERPENT|PURO ?BAT|ALEBRIJE", "Limited Edition Alebrije"),
    (r"PURO ?CORAZ", "Puro Corazon"),
    (r"AUREO", "Aureo"),
    (r"AMBAR|AMBER|REPOSADO", "Ambar"),
    (r"200\s*ML|200mL|BLANCO-200|BLANCO 200", "Blanco 200mL"),
    (r"BLANCO", "Blanco"),
]

# Prefijo de SKU de Park Street que corresponde a material de empaque, no a
# producto vendible (inserts, shippers, cajas de regalo) -> se excluye del
# resumen de inventario de producto.
PARK_STREET_PACKAGING_PREFIX = "Z-"

KNOWN_SALESPEOPLE = {
    "mark": "Mark Harding (CA)",
    "jacky": "Jacky Gonzalez (CA)",
    "jackquelin": "Jacky Gonzalez (CA)",
    "joe pat": "Joe Pat Clayton (TX)",
    "manuel": "Manuel Leyshon (TX/DTC)",
}

ON_PREMISE_KEYWORDS = [
    "restaurant", "bar", "club", "resort", "hotel", "kitchen", "grill",
    "tavern", "lounge", "bistro", "cafe", "winery", "tequileria", "spa",
]
OFF_PREMISE_KEYWORDS = [
    "liquor", "wine", "spirits", "market", "grocery", "shop", "store",
    "foods",
]


def guess_channel(account_name: str) -> str:
    """Heuristico de canal por nombre de cuenta. Etiquetado como aproximado
    a propósito: no hay tabla maestra de canal en los archivos crudos."""
    name = (account_name or "").lower()
    for kw in ON_PREMISE_KEYWORDS:
        if kw in name:
            return "On Premise (heuristic)"
    for kw in OFF_PREMISE_KEYWORDS:
        if kw in name:
            return "Off Premise (heuristic)"
    return "Unknown (heuristic)"


def categorize_product(name: str) -> str:
    name = (name or "").upper()
    for pattern, category in PRODUCT_CATEGORY_RULES:
        if re.search(pattern, name):
            return category
    return "Other/Unclassified"


def bottles_to_9l(bottles: float, bottle_ml: float = DEFAULT_BOTTLE_ML) -> float:
    """1 caja 9L = 9000 mL. bottles_to_9l(12, 750) == 1.0"""
    return bottles * bottle_ml / ML_PER_9L_CASE


def money_to_float(series: pd.Series) -> pd.Series:
    return (
        series.astype(str)
        .str.replace(r"[\$,]", "", regex=True)
        .replace({"": np.nan, "-": np.nan, "nan": np.nan})
        .astype(float)
    )


# --------------------------------------------------------------------------
# Loaders — un loader por archivo crudo
# --------------------------------------------------------------------------

def load_fb_supplier_inventory(path: str) -> pd.DataFrame:
    """Favorite Brands (TX) — inventario disponible por SKU en botellas
    individuales, con una columna por bodega TX + Total."""
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    header_idx = next(i for i, r in enumerate(rows) if r and "ITEM #" in r)
    header = rows[header_idx]
    col = {h: i for i, h in enumerate(header) if h}
    out = []
    for r in rows[header_idx + 1:]:
        item = r[col.get("ITEM #")] if col.get("ITEM #") is not None else None
        if item is None:
            continue
        product = r[col["Product"]]
        total_bottles = r[col["Total"]]
        out.append(
            {
                "item_id": item,
                "product_name": product,
                "category": categorize_product(product),
                "total_bottles": float(total_bottles or 0),
            }
        )
    df = pd.DataFrame(out)
    df["9L"] = bottles_to_9l(df["total_bottles"], DEFAULT_BOTTLE_ML) if len(df) else df.get("total_bottles")
    return df


_FB_DEPLETION_DATE_PATTERNS = [
    re.compile(r"(\d{4})-(\d{2})-(\d{2})"),  # 2026-08-24
    # 011226 -> MM DD YY. El separador acepta guion o guion bajo además del
    # espacio: si el archivo se renombra a un nombre portable, la fecha debe
    # seguir leyéndose en vez de caer al primer candidato de la carpeta.
    re.compile(r"^(\d{2})(\d{2})(\d{2})[\s_-]"),
]


def _parse_fb_depletion_filename_date(fname: str) -> Optional[date]:
    base = os.path.basename(fname)
    m = _FB_DEPLETION_DATE_PATTERNS[0].search(base)
    if m:
        y, mo, d = map(int, m.groups())
        return date(y, mo, d)
    m = _FB_DEPLETION_DATE_PATTERNS[1].match(base)
    if m:
        mo, d, y = map(int, m.groups())
        return date(2000 + y, mo, d)
    return None


def _find_fb_depletion_folder(data_dir: str) -> Optional[str]:
    """
    Localiza la subcarpeta de depletions de FB sin fijar el año ni la
    puntuación: reconoce `FB Depletion Reports 2026` (nombre real del cliente)
    y `FB-Depletion-Reports-2026` (nombre portable del demo). Si hay varias,
    gana la del año más alto.
    """
    if not os.path.isdir(data_dir):
        return None
    hits = []
    for name in os.listdir(data_dir):
        path = os.path.join(data_dir, name)
        if not os.path.isdir(path):
            continue
        flat = re.sub(r"[^a-z0-9]", "", name.lower())
        if flat.startswith("fbdepletionreports"):
            hits.append(name)
    if not hits:
        return None
    hits.sort()
    return os.path.join(data_dir, hits[-1])


def find_latest_fb_depletion_file(data_dir: str) -> Optional[str]:
    folder = _find_fb_depletion_folder(data_dir)
    if not folder:
        return None
    candidates = glob.glob(os.path.join(folder, "*.xlsx"))
    dated = [(c, _parse_fb_depletion_filename_date(c)) for c in candidates]
    dated = [(c, d) for c, d in dated if d is not None]
    if not dated:
        return candidates[0] if candidates else None
    dated.sort(key=lambda t: t[1])
    return dated[-1][0]


MONTH_COLS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]


def load_fb_depletion(path: str) -> pd.DataFrame:
    """Favorite Brands (TX) — depletions off-premise acumuladas por mes
    calendario, snapshot semanal (sin fecha real de transacción)."""
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    header_idx = next(i for i, r in enumerate(rows) if r and "CUSTOMER" in r and "PRODUCT" in r)
    header = rows[header_idx]
    col = {h: i for i, h in enumerate(header) if h}
    records = []
    for r in rows[header_idx + 1:]:
        if col.get("ITEM ") is None or r[col["ITEM "]] is None:
            continue
        rec = {
            "customer": r[col.get("CUSTOMER")],
            "city": r[col.get("CITY")],
            "state": r[col.get("STATE")],
            "chain": r[col.get("CHAIN")],
            "premise": r[col.get("PREMISE")],
            "sales_rep_fb": r[col.get("SALES REP")],
            "product": r[col.get("PRODUCT")],
            "category": categorize_product(r[col.get("PRODUCT")]),
        }
        for m in MONTH_COLS:
            if m in col:
                v = r[col[m]]
                rec[m] = float(v) if isinstance(v, (int, float)) else 0.0
        records.append(rec)
    df = pd.DataFrame(records)
    present_months = [m for m in MONTH_COLS if m in df.columns]
    df["total_bottles_ytd"] = df[present_months].sum(axis=1) if present_months else 0.0
    return df


def load_signature_inventory_history(path: str) -> pd.DataFrame:
    """Signature/Southern Glazer's (CA) — inventario disponible, jerárquico
    por sitio y producto, en cases decimales de 6 botellas."""
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    header_idx = next(i for i, r in enumerate(rows) if r and r[0] == "Sites")
    header = rows[header_idx]
    col = {h: i for i, h in enumerate(header) if h}
    out = []
    for r in rows[header_idx + 1:]:
        site = r[col.get("Sites")]
        if site is None or site == "":
            continue
        plant = r[col.get("Plants")]
        item = r[col.get("Item Names")]
        on_hand = r[col.get(" On Hand Decimal  Cases")]
        out.append(
            {
                "site": site,
                "plant": plant,
                "item_name": item,
                "category": categorize_product(item) if item != "Total" else "TOTAL_ROW",
                "on_hand_cases_6btl": float(on_hand) if isinstance(on_hand, (int, float)) else 0.0,
                "is_site_total": (plant == "Total" and item == "Total"),
                "is_leaf": (plant != "Total" and item not in (None, "Total")),
            }
        )
    return pd.DataFrame(out)


def load_signature_ytd_by_month(path: str) -> pd.DataFrame:
    """Signature (CA) — depletions por cuenta/producto/factura, con columnas
    mensuales ene..(mes en curso) y un acumulado YTD ya calculado por fila."""
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    header = rows[0]
    month_cols = [h for h in header if isinstance(h, str) and h.startswith("1 Depletion Month")]
    ytd_bottles_col = next(h for h in header if isinstance(h, str) and h.endswith("Bottles") and "Year" in h)
    ytd_9l_col = next(h for h in header if isinstance(h, str) and "9L" in h)
    col = {h: i for i, h in enumerate(header)}
    out = []
    for r in rows[1:]:
        account = r[col["Retail Accounts"]]
        if account is None:
            continue
        rec = {
            "account": account,
            "city": r[col["City"]],
            "item_name": r[col["Item Names"]],
            "category": categorize_product(r[col["Item Names"]]),
            "invoice_date": r[col["Invoice Dates"]],
            "ytd_bottles": r[col[ytd_bottles_col]] or 0,
            "ytd_9l": r[col[ytd_9l_col]] or 0,
        }
        for mc in month_cols:
            month_label = mc.replace("1 Depletion Month ", "").split(" ")[0]
            v = r[col[mc]]
            rec[month_label.upper()] = float(v) if isinstance(v, (int, float)) else 0.0
        out.append(rec)
    return pd.DataFrame(out)


def load_park_street_inventory_by_location(path: str) -> pd.DataFrame:
    """Park Street — inventario disponible por SKU y ubicación (incluye
    bodegas propias y el stock que cada vendedor carga), en cases decimales
    (6 botellas para 750mL, 24 para 200mL)."""
    df = pd.read_csv(path)
    is_packaging = df["product_id"].astype(str).str.startswith(PARK_STREET_PACKAGING_PREFIX) | df[
        "sub_brand_product_name"
    ].astype(str).str.contains(
        "Value Added Packaging|Gift Box|Outer Shipper|Slit Insert", case=False, na=False
    )
    df = df[~is_packaging].copy()
    df["onhand"] = df["onhand"].astype(float)
    # OJO: el sufijo "NSS" (not-sellable-samples) casi siempre vive en
    # product_id (ej. "LCU-BLANCO-750NSS"), no en sub_brand_product_name
    # (que dice "Loco Blanco Tequila 750mL/6" igual que la version vendible)
    # -> hay que clasificar usando ambas columnas juntas o el NSS se pierde.
    df["category"] = (df["product_id"].astype(str) + " " + df["sub_brand_product_name"].astype(str)).map(
        categorize_product
    )
    is_200 = df["product_id"].str.contains("200", na=False) | df["sub_brand_product_name"].str.contains("200", na=False)
    factor = np.where(is_200, 24 * 200.0 / ML_PER_9L_CASE, 6 * DEFAULT_BOTTLE_ML / ML_PER_9L_CASE)
    df["9L"] = df["onhand"] * factor
    df["is_salesperson_stock"] = df["location_grp"].eq("Salesperson Inventory")
    return df


def load_park_street_sales_orders(path: str) -> pd.DataFrame:
    """Park Street — SalesOrdersSummary: 1 fila por línea de producto dentro
    de una orden. OJO: usar la columna `Total` (importe de esa línea), NUNCA
    `Total Value` (importe de la ORDEN completa, repetido en cada línea —
    sumarlo de más cuenta el mismo pedido varias veces)."""
    df = pd.read_csv(path)
    df["date_posted"] = pd.to_datetime(df["Date Posted"], format="%m/%d/%y", errors="coerce")
    df["qty"] = pd.to_numeric(df["Qty"], errors="coerce").fillna(0.0)
    df["line_total_usd"] = money_to_float(df["Total"])
    df["order_total_usd"] = money_to_float(df["Total Value"])  # solo para referencia/diagnóstico
    df["category"] = df["Product Description"].map(categorize_product)
    is_200 = df["Product Code"].astype(str).str.contains("200", na=False)
    case_factor = np.where(is_200, 24 * 200.0 / ML_PER_9L_CASE, 6 * DEFAULT_BOTTLE_ML / ML_PER_9L_CASE)
    bottle_factor = np.where(is_200, 200.0 / ML_PER_9L_CASE, DEFAULT_BOTTLE_ML / ML_PER_9L_CASE)
    is_cases = df["Unit"].eq("Cases")
    df["9L"] = np.where(is_cases, df["qty"] * case_factor, df["qty"] * bottle_factor)
    return df


def load_ecommerce_orders(path: str, source_label: str) -> pd.DataFrame:
    """Shopify o Memory (event pick-up) — export estándar de Shopify."""
    df = pd.read_csv(path, dtype=str)
    df["source"] = source_label
    df["lineitem_qty"] = pd.to_numeric(df["Lineitem quantity"], errors="coerce").fillna(0.0)
    df["lineitem_price"] = pd.to_numeric(df["Lineitem price"], errors="coerce").fillna(0.0)
    df["revenue"] = df["lineitem_qty"] * df["lineitem_price"]
    df["category"] = df["Lineitem name"].map(categorize_product)
    df["created_at"] = pd.to_datetime(df["Created at"], errors="coerce", utc=True)
    df["has_tag"] = df["Tags"].notna() & (df["Tags"].astype(str).str.strip() != "")
    return df


# --------------------------------------------------------------------------
# Builders — una función por tabla del reporte
# --------------------------------------------------------------------------

def build_inventory_table(data_dir: str) -> pd.DataFrame:
    """Hoja `Inventory`. Validada exacta contra el reporte real (ver .md,
    sección 3.1)."""
    fb_inv = load_fb_supplier_inventory(
        _first_match(data_dir, "1 - Supplier - Inventory*.xlsx")
    )
    sig_inv = load_signature_inventory_history(
        _first_match(data_dir, "Inventory History*.xlsx")
    )
    ps_inv = load_park_street_inventory_by_location(
        _first_match(data_dir, "InventoryByLocation*.csv")
    )

    tx_by_cat = fb_inv.groupby("category")["9L"].sum()

    leaf = sig_inv[sig_inv["is_leaf"]].copy()
    leaf["region"] = leaf["site"].apply(
        lambda s: "NOR CAL" if "North" in str(s) else ("SO CAL" if "South" in str(s) else "OTHER")
    )
    sig_by_cat_region = (
        leaf.groupby(["category", "region"])["on_hand_cases_6btl"].sum() * 0.5
    )

    ps_by_cat = ps_inv.groupby("category")["9L"].sum()

    categories = sorted(
        set(tx_by_cat.index)
        | set(sig_by_cat_region.index.get_level_values(0))
        | set(ps_by_cat.index)
    )
    rows = []
    for cat in categories:
        so_cal = sig_by_cat_region.get((cat, "SO CAL"), 0.0)
        nor_cal = sig_by_cat_region.get((cat, "NOR CAL"), 0.0)
        ca_park_st = ps_by_cat.get(cat, 0.0)
        tx_fb = tx_by_cat.get(cat, 0.0)
        total_ca = so_cal + nor_cal + ca_park_st
        total_tx = tx_fb
        rows.append(
            {
                "Product": cat,
                "Grand Total (9L)": round(total_ca + total_tx, 4),
                "Total CA (9L)": round(total_ca, 4),
                "Total TX (9L)": round(total_tx, 4),
                "SO CAL SGWS (On Hand)": round(so_cal, 4),
                "NOR CAL SGWS (On Hand)": round(nor_cal, 4),
                "CA Park St (On Hand)": round(ca_park_st, 4),
                "Texas FB (On Hand)": round(tx_fb, 4),
            }
        )
    out = pd.DataFrame(rows).sort_values("Grand Total (9L)", ascending=False)
    return out


def build_wholesale_and_retail_tables(data_dir: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Tablas "Wholesale" y "Direct to Retail". Wholesale validada exacta;
    Direct to Retail queda como aproximación (ver .md, secciones 3.2-3.3)."""
    orders = load_park_street_sales_orders(_first_match(data_dir, "SalesOrdersSummary*.csv"))

    wholesale = (
        orders[orders["Customer Type"] == "Wholesaler"]
        .groupby("Customer")
        .agg(**{"9L": ("9L", "sum"), "Revenue (USD)": ("line_total_usd", "sum")})
        .reset_index()
        .sort_values("Revenue (USD)", ascending=False)
    )

    retail = (
        orders[orders["Customer Type"] == "Retailer"]
        .groupby("Customer")
        .agg(**{"9L": ("9L", "sum"), "Revenue (USD)": ("line_total_usd", "sum")})
        .reset_index()
        .sort_values("Revenue (USD)", ascending=False)
    )
    return wholesale, retail


def build_depletions_by_territory(data_dir: str) -> dict:
    """Bloque "Depletions" (California / Texas) de `YTD Summary` /
    `Monthly Summary`. Orden de magnitud correcto, sin cuadrar al 100% con
    el reporte real (ver .md, sección 3.4)."""
    sig_path = _first_match(data_dir, "YTD by Month*.xlsx")
    sig = load_signature_ytd_by_month(sig_path)
    ca_bottles_ytd = float(sig["ytd_bottles"].sum())
    ca_9l_ytd = float(sig["ytd_9l"].sum())
    ca_by_month = {m: float(sig[m].sum()) for m in MONTH_COLS if m in sig.columns}

    fb_path = find_latest_fb_depletion_file(data_dir)
    fb = load_fb_depletion(fb_path) if fb_path else pd.DataFrame()
    tx_bottles_ytd = float(fb["total_bottles_ytd"].sum()) if len(fb) else 0.0
    tx_by_month = {m: float(fb[m].sum()) for m in MONTH_COLS if m in fb.columns} if len(fb) else {}

    return {
        "fb_depletion_snapshot_used": fb_path,
        "california": {
            "bottles_ytd": ca_bottles_ytd,
            "9l_ytd": ca_9l_ytd,
            "9l_ytd_from_bottles": bottles_to_9l(ca_bottles_ytd),
            "by_month_bottles": ca_by_month,
            "n_accounts": int(sig["account"].nunique()),
        },
        "texas": {
            "bottles_ytd": tx_bottles_ytd,
            "9l_ytd_from_bottles": bottles_to_9l(tx_bottles_ytd),
            "by_month_bottles": tx_by_month,
            "n_accounts": int(fb["customer"].nunique()) if len(fb) else 0,
            "premise_breakdown": fb["premise"].value_counts().to_dict() if len(fb) else {},
        },
    }


def build_dtc_ecommerce_split(data_dir: str) -> dict:
    """Hojas `DTC Sales by Month/Year`. Hipótesis documentada, no verificada
    con exactitud numérica (ver .md, sección 3.6). GM no se calcula: ningún
    archivo crudo trae costo unitario (COGS)."""
    shopify = load_ecommerce_orders(_first_match(data_dir, "orders_export_1*shopify.csv"), "shopify")
    memory = load_ecommerce_orders(_first_match(data_dir, "orders_export_1*memory.csv"), "memory")
    combined = pd.concat([shopify, memory], ignore_index=True)

    ecommerce = combined[(combined["source"] == "shopify") & (~combined["has_tag"])]
    dtc_attributed = combined[combined["has_tag"] | (combined["source"] == "memory")]

    def summarize(df: pd.DataFrame) -> dict:
        return {
            "bottles": float(df["lineitem_qty"].sum()),
            "revenue_usd_no_gm": float(df["revenue"].sum()),
            "by_category": df.groupby("category")["lineitem_qty"].sum().to_dict(),
        }

    orders = load_park_street_sales_orders(_first_match(data_dir, "SalesOrdersSummary*.csv"))
    melrose = orders[orders["Customer"].astype(str).str.contains("Melrose Gas", na=False)]

    # SPLIT POR TIENDA DE ORIGEN — lo que el cliente pidió de verdad.
    # Los dos buckets de arriba están partidos por "tiene etiqueta o no", así que
    # una orden de Shopify ETIQUETADA cae en el bucket de Memory. El cliente pidió
    # "DTC (shopify and memory bottles)": eso es por tienda, y la columna `source`
    # ya venía etiquetada desde el loader — solo no se estaba usando para agrupar.
    by_store = {}
    for label, pretty in (("shopify", "Shopify"), ("memory", "Memory Bottles")):
        part = combined[combined["source"] == label]
        by_store[pretty] = summarize(part) | {
            "orders": int(part["Name"].nunique()) if "Name" in part.columns else 0,
            "by_month": _bottles_by_month(part, "created_at", "lineitem_qty"),
        }

    return {
        "ecommerce_untagged_shopify": summarize(ecommerce),
        "dtc_tagged_or_memory": summarize(dtc_attributed),
        "by_store": by_store,
        "melrose_gas_park_street_reference": {
            "9L": float(melrose["9L"].sum()),
            "revenue_usd": float(melrose["line_total_usd"].sum()),
        },
        "note": (
            "Revenue is gross sales. Gross margin is applied separately from the "
            "client-supplied per-bottle rate table."
        ),
    }


def _bottles_by_month(df: pd.DataFrame, date_col: str, qty_col: str) -> dict:
    """{'JAN': 12.0, ...} en orden de calendario, para las rejillas mensuales."""
    if df.empty or date_col not in df.columns:
        return {}
    d = df.dropna(subset=[date_col]).copy()
    if d.empty:
        return {}
    d["_m"] = pd.to_datetime(d[date_col], errors="coerce", utc=True).dt.month
    out = {}
    for m, grp in d.dropna(subset=["_m"]).groupby("_m"):
        idx = int(m) - 1
        if 0 <= idx < 12:
            out[MONTH_COLS[idx]] = float(grp[qty_col].sum())
    return {m: out[m] for m in MONTH_COLS if m in out}


def build_signature_detail(data_dir: str) -> dict:
    """
    Detalle del feed de California (Signature / Southern Glazer's) por cuenta,
    por SKU y por ciudad, con su rejilla mensual.

    El loader ya traía `account`, `city`, `item_name`, `category` y una columna
    por mes; el procesador solo agregaba el total nacional y descartaba todo lo
    demás. Esto es lo que necesita la pestaña "Signature depletions" del cliente,
    sin parseo nuevo.
    """
    sig = load_signature_ytd_by_month(_first_match(data_dir, "YTD by Month*.xlsx"))
    months = [m for m in MONTH_COLS if m in sig.columns]

    def grid(group_col):
        rows = []
        for key, g in sig.groupby(group_col):
            if not str(key).strip():
                continue
            row = {"name": str(key).strip(),
                   "bottles_ytd": float(g["ytd_bottles"].sum())}
            row["by_month"] = {m: float(g[m].sum()) for m in months}
            rows.append(row)
        return sorted(rows, key=lambda r: -r["bottles_ytd"])

    orders_by_account = (
        sig.dropna(subset=["invoice_date"])
        .assign(_d=lambda d: pd.to_datetime(d["invoice_date"], errors="coerce").dt.date)
        .groupby("account")["_d"].nunique().to_dict()
    )
    return {
        "months": months,
        "by_account": grid("account"),
        "by_sku": grid("category"),
        "by_city": grid("city"),
        "orders_by_account": {str(k).strip(): int(v)
                              for k, v in orders_by_account.items()},
        # Definición del cliente: en California una orden es un par distinto
        # (cuenta, fecha de factura).
        "orders_ytd": int(sum(orders_by_account.values())),
        "source_file": "YTD by Month [Bottles, Orders].xlsx",
    }


def build_fb_detail(data_dir: str) -> dict:
    """
    Detalle del feed de Texas (Favorite Brands) por cuenta, SKU, premise y
    vendedor del distribuidor, con rejilla mensual.

    Nota importante sobre `SALES REP`: esa columna trae los vendedores **de
    Favorite Brands** (`AUSTIN FB WAREHOUSE`, `BLAKE SCHNEIDER`...), no los de
    Loco. Se expone como metadato del distribuidor y NO se usa para atribuir
    nuestros vendedores — sería inventar, por el mismo motivo por el que la regla
    del cliente ordena ignorar el campo equivalente de ACS.
    """
    path = find_latest_fb_depletion_file(data_dir)
    if not path:
        return {}
    fb = load_fb_depletion(path)
    months = [m for m in MONTH_COLS if m in fb.columns]

    def grid(col, label_fix=None):
        rows = []
        for key, g in fb.groupby(col):
            name = str(key).strip()
            if not name:
                continue
            if label_fix:
                name = label_fix(name)
            rows.append({"name": name,
                         "bottles_ytd": float(g["total_bottles_ytd"].sum()),
                         "by_month": {m: float(g[m].sum()) for m in months}})
        return sorted(rows, key=lambda r: -r["bottles_ytd"])

    def premise_label(p):
        u = p.upper()
        return ("On Premise" if u.startswith("ON")
                else "Off Premise" if u.startswith("OFF") else p.title())

    return {
        "months": months,
        "by_account": grid("customer"),
        "by_sku": grid("category"),
        "by_premise": grid("premise", premise_label),
        "by_distributor_rep": grid("sales_rep_fb"),
        "snapshot": os.path.basename(path),
        "source_file": "Favorite Brands depletion report (weekly snapshot)",
    }


def build_fact_table(data_dir: str, account_map: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """
    La tabla de hechos que alimenta la hoja `Dataset` del libro de Excel.

    Una fila por hecho atómico: territorio, fuente, cuenta, SKU, mes, botellas,
    y vendedor/canal resuelto por la escalera de atribución. Es EL MISMO insumo
    que necesitan las tablas dinámicas de Excel y que necesita la pestaña de
    trazabilidad del tablero — se construye una vez y sirve para las dos cosas.

    Deliberadamente en formato LARGO (una fila por hecho), no ancho: así es como
    espera los datos una tabla dinámica, y así se puede sumar por cualquier
    combinación de dimensiones sin escribir una agregación por vista.

    Solo filas con botellas != 0: incluir los ceros multiplicaría el tamaño del
    libro sin aportar nada que una tabla dinámica no pueda mostrar filtrando.
    """
    resolver = _get_resolver(account_map)
    rows = []

    # -- Signature (California) --------------------------------------------
    sig = load_signature_ytd_by_month(_first_match(data_dir, "YTD by Month*.xlsx"))
    sig_months = [m for m in MONTH_COLS if m in sig.columns]
    for _, r in sig.iterrows():
        account = str(r.get("account") or "").strip()
        if not account:
            continue
        attr = resolver.resolve_account(account, "CA")
        for m in sig_months:
            b = float(r.get(m) or 0)
            if b:
                rows.append({
                    "Territory": "California", "Source": "Signature",
                    "Account": account, "SKU": str(r.get("category") or "").strip(),
                    "Month": m, "Bottles": b,
                    "Salesperson": attr.salesperson, "Channel": attr.channel,
                    "AttrRule": attr.rule,
                })

    # -- Favorite Brands (Texas) -------------------------------------------
    fb_path = find_latest_fb_depletion_file(data_dir)
    if fb_path:
        fb = load_fb_depletion(fb_path)
        fb_months = [m for m in MONTH_COLS if m in fb.columns]
        for _, r in fb.iterrows():
            account = str(r.get("customer") or "").strip()
            if not account:
                continue
            premise_raw = str(r.get("premise") or "").strip().upper()
            channel = ("On Premise" if premise_raw.startswith("ON")
                      else "Off Premise" if premise_raw.startswith("OFF") else "")
            attr = resolver.resolve_account(account, "TX")
            for m in fb_months:
                b = float(r.get(m) or 0)
                if b:
                    rows.append({
                        "Territory": "Texas", "Source": "Favorite Brands",
                        "Account": account, "SKU": str(r.get("category") or "").strip(),
                        "Month": m, "Bottles": b,
                        # PREMISE del distribuidor es autoritativo y gana al mapa.
                        "Salesperson": attr.salesperson,
                        "Channel": channel or attr.channel,
                        "AttrRule": attr.rule,
                    })

    # -- DTC: Shopify y Memory Bottles, por línea de orden -----------------
    for fname, label in [("orders_export_1*shopify.csv", "Shopify"),
                         ("orders_export_1*memory.csv", "Memory Bottles")]:
        path = _first_match(data_dir, fname, required=False)
        if not path:
            continue
        df = load_ecommerce_orders(path, label.lower().split()[0])
        df = df.dropna(subset=["created_at"])
        for _, r in df.iterrows():
            b = float(r.get("lineitem_qty") or 0)
            if not b:
                continue
            attr = resolver.resolve_tag(r.get("Tags") or r.get("Employee") or "")
            month = MONTH_COLS[r["created_at"].month - 1]
            rows.append({
                "Territory": "DTC", "Source": label,
                "Account": str(r.get("Name") or "").strip(),
                "SKU": str(r.get("category") or "").strip(),
                "Month": month, "Bottles": b,
                "Salesperson": attr.salesperson, "Channel": "DTC",
                "AttrRule": attr.rule,
            })

    cols = ["Territory", "Source", "Account", "SKU", "Month", "Bottles",
            "Salesperson", "Channel", "AttrRule"]
    if not rows:
        return pd.DataFrame(columns=cols)
    df = pd.DataFrame(rows, columns=cols)
    # Orden de calendario, NO descendente por valor: es la dimensión temporal.
    df["Month"] = pd.Categorical(df["Month"], categories=MONTH_COLS, ordered=True)
    return df.sort_values(["Territory", "Month", "Account"]).reset_index(drop=True)


def build_salesperson_by_week_detailed(data_dir: str,
                                       account_map: Optional[pd.DataFrame]):
    """
    Igual que `build_salesperson_by_week`, pero devuelve además la lista de
    líneas con su atribución resuelta: `(pivot, lines)`.

    `lines` es lo que alimenta la pestaña de fuentes, y por eso cubre TODO el
    volumen de depletion (CA + TX + DTC) — no solo lo que entra al pivote
    semanal. Son dos alcances distintos a propósito: Favorite Brands (Texas) no
    trae fecha de transacción, así que no puede aparecer en una serie *semanal*,
    pero sí tiene que contar para "¿qué porcentaje del volumen está atribuido a
    un vendedor?", que es la pregunta que el cliente hizo. Mezclar los dos
    alcances fue justo el bug que la hoja `Validation` del libro de Excel
    encontró: la atribución declarada en el tablero (solo fuentes con fecha)
    no cuadraba contra la de la tabla de hechos completa (`build_fact_table`,
    que sí incluye Texas) — 84 botellas de diferencia, exactamente el volumen
    de Texas que la escalera de atribución nunca llegaba a ver.
    """
    resolver = _get_resolver(account_map)
    records, lines = [], []

    def add(week, attr, bottles, account, source_file, territory="",
            to_weekly=True, to_lines=True):
        """
        `to_weekly` y `to_lines` son alcances INDEPENDIENTES a propósito:

        - `to_weekly` -> entra al pivote "Salesperson by Week" (necesita una
          fecha real).
        - `to_lines` -> entra al audit de atribución (`lines`), que es lo que
          responde "¿qué % del volumen de DEPLETION está atribuido?" — y por
          eso deliberadamente NO incluye el stock que un vendedor tiene en el
          maletero sin haber depletado todavía (ver Park Street más abajo):
          es movimiento de inventario, no una venta a una cuenta.
        """
        if to_weekly:
            records.append({"week": week, "salesperson": attr.salesperson,
                            "bottles": bottles, "source": source_file})
        if to_lines:
            lines.append({"attr": attr, "bottles": bottles, "account": account,
                          "territory": territory, "source_file": source_file})

    sig = load_signature_ytd_by_month(_first_match(data_dir, "YTD by Month*.xlsx"))
    sig = sig.dropna(subset=["invoice_date"])
    for _, r in sig.iterrows():
        dt = r["invoice_date"]
        if not isinstance(dt, (datetime, date)):
            continue
        add(_iso_week_start(dt), resolver.resolve_account(r["account"], "CA"),
            float(r["ytd_bottles"] or 0), r["account"],
            "YTD by Month [Bottles, Orders].xlsx", "CA")

    # Retiros de inventario de vendedor en Park Street (`Customer Type ==
    # "Salesperson"`, el `Customer` es literalmente el nombre del rep). Esto es
    # stock que salió a su maletero, NO una venta depletada a una cuenta — por
    # eso sí entra al pivote semanal (`to_weekly=True`, es la vista operativa
    # de qué tiene cada rep) pero NO al audit de atribución de depletions
    # (`to_lines=False`): mezclarlo ahí inflaría "% de depletions atribuidas"
    # con una magnitud que no es depletion.
    orders = load_park_street_sales_orders(_first_match(data_dir, "SalesOrdersSummary*.csv"))
    sp_orders = orders[orders["Customer Type"] == "Salesperson"].dropna(subset=["date_posted"])
    for _, r in sp_orders.iterrows():
        add(_iso_week_start(r["date_posted"]), resolver.resolve_person(r["Customer"]),
            float(r["qty"] if r["Unit"] == "Bottles" else r["qty"] * 6),
            r["Customer"], "SalesOrdersSummary.csv", to_lines=False)

    for fname, label, pretty in [
        ("orders_export_1*shopify.csv", "shopify", "orders_export (Shopify).csv"),
        ("orders_export_1*memory.csv", "memory", "orders_export (Memory Bottles).csv"),
    ]:
        path = _first_match(data_dir, fname, required=False)
        if not path:
            continue
        df = load_ecommerce_orders(path, label)
        df = df.dropna(subset=["created_at"])
        for _, r in df.iterrows():
            # Los exports de Shopify no traen columna `Employee`, así que la
            # atribución descansa en el texto libre de `Tags`. Se declara.
            add(_iso_week_start(r["created_at"]),
                resolver.resolve_tag(r.get("Tags") or r.get("Employee") or ""),
                float(r["lineitem_qty"] or 0), r.get("Name") or "", pretty)

    # Favorite Brands (Texas). NO entra al pivote semanal (to_weekly=False):
    # el feed es un snapshot acumulado sin fecha de transacción real, así que
    # no hay una semana verdadera a la que asignarlo. Pero SÍ entra a `lines`,
    # porque para "qué porcentaje de las botellas está atribuido a alguien" el
    # territorio de Texas cuenta igual que California o el DTC.
    fb_path = find_latest_fb_depletion_file(data_dir)
    if fb_path:
        Attribution = _loco_attribution().Attribution
        fb = load_fb_depletion(fb_path)
        for _, r in fb.iterrows():
            b = float(r.get("total_bottles_ytd") or 0)
            if not b:
                continue
            premise_raw = str(r.get("premise") or "").strip().upper()
            attr = resolver.resolve_account(r["customer"], "TX")
            # PREMISE de Favorite Brands es autoritativo y gana al canal que
            # la escalera hubiera resuelto por mapa/heurística.
            channel = ("On Premise" if premise_raw.startswith("ON")
                      else "Off Premise" if premise_raw.startswith("OFF") else None)
            if channel:
                attr = Attribution(attr.salesperson, channel, attr.rule,
                                   attr.source, attr.reason, attr.matched_account,
                                   attr.candidates)
            add(None, attr, b, r["customer"],
                "Favorite Brands depletion report (weekly snapshot)", "TX",
                to_weekly=False)

    if not records:
        return pd.DataFrame(columns=["week", "salesperson", "bottles"]), lines
    df = pd.DataFrame(records)
    pivot = df.pivot_table(index="week", columns="salesperson", values="bottles",
                           aggfunc="sum", fill_value=0.0)
    pivot["TOTAL"] = pivot.sum(axis=1)
    return pivot.sort_index(), lines


def build_salesperson_by_week(data_dir: str, account_map: Optional[pd.DataFrame]) -> pd.DataFrame:
    """Hoja `Salesperson by Week`. Cubre las fuentes con fecha real
    (Signature, Park Street, Shopify/Memory); FB Depletion no tiene fecha de
    transacción así que no se semanaliza (ver .md, sección 3.5)."""
    return build_salesperson_by_week_detailed(data_dir, account_map)[0]


def build_accounts_summary(data_dir: str, account_map: Optional[pd.DataFrame]) -> pd.DataFrame:
    """Esqueleto de `Accounts H1/H2-2026` y `Account Summary Total Business`:
    botellas por cuenta y última fecha de orden, unidas desde las 3 fuentes
    con nivel de cuenta. Salesperson/Channel quedan como heurístico salvo que
    se pase --account-map (ver .md, sección 3.7)."""
    pieces = []

    sig = load_signature_ytd_by_month(_first_match(data_dir, "YTD by Month*.xlsx"))
    sig_g = sig.groupby("account").agg(
        bottles=("ytd_bottles", "sum"), last_order=("invoice_date", "max")
    ).reset_index().rename(columns={"account": "account_name"})
    sig_g["source"] = "signature_ca"
    pieces.append(sig_g)

    fb_path = find_latest_fb_depletion_file(data_dir)
    if fb_path:
        fb = load_fb_depletion(fb_path)
        fb_g = fb.groupby("customer").agg(bottles=("total_bottles_ytd", "sum")).reset_index()
        fb_g = fb_g.rename(columns={"customer": "account_name"})
        fb_g["last_order"] = pd.NaT
        fb_g["source"] = "fb_tx"
        pieces.append(fb_g)

    orders = load_park_street_sales_orders(_first_match(data_dir, "SalesOrdersSummary*.csv"))
    ps_rows = orders[orders["Customer Type"].isin(["Retailer", "Salesperson"])]
    # Conteo de ORDENES por cuenta, no solo botellas. La definición del cliente
    # para California es un par (cuenta, fecha) distinto: dos líneas del mismo
    # pedido no son dos órdenes. Antes esto no se contaba en ninguna parte,
    # aunque el cliente lo reporta en su libro y lo pidió explícitamente.
    ps_g = (
        ps_rows
        .groupby("Customer")
        .agg(bottles=("9L", lambda s: s.sum() * 12.0),
             last_order=("date_posted", "max"))
        .reset_index()
        .rename(columns={"Customer": "account_name"})
    )
    ps_g["source"] = "park_street"
    pieces.append(ps_g)

    orders_ytd = (
        ps_rows.dropna(subset=["date_posted"])
        .assign(_d=lambda d: d["date_posted"].dt.date)
        .groupby("Customer")["_d"].nunique()
    )

    # PREMISE de Favorite Brands: es el campo AUTORITATIVO de on/off premise y
    # hasta ahora se parseaba, se agregaba y se tiraba, mientras el canal se
    # adivinaba por palabras en el nombre de la cuenta.
    fb_premise: dict = {}
    if fb_path:
        for _, r in fb.iterrows():
            p = str(r.get("premise") or "").strip().upper()
            if not p:
                continue
            fb_premise[str(r["customer"]).strip()] = (
                "On Premise" if p.startswith("ON") else
                "Off Premise" if p.startswith("OFF") else p.title()
            )

    all_accounts = pd.concat(pieces, ignore_index=True)
    agg = all_accounts.groupby("account_name").agg(
        bottles_all_sources=("bottles", "sum"),
        last_order_date=("last_order", "max"),
        n_sources=("source", "nunique"),
    ).reset_index()
    agg["orders_ytd"] = agg["account_name"].map(orders_ytd).fillna(0).astype(int)

    # Escalera de atribución explícita. Sustituye los tres desenlaces ad hoc que
    # había aquí: un `fillna("Unknown (no map match)")` que mentía sobre la causa
    # cuando el problema era que no se había suministrado mapa, un literal
    # distinto para ese caso, y el heurístico de canal por nombre.
    resolver = _get_resolver(account_map)
    sp_col, ch_col, rule_col, why_col, src_col = [], [], [], [], []
    for name in agg["account_name"]:
        terr = "TX" if str(name).strip() in fb_premise else ""
        a = resolver.resolve_account(name, territory=terr)
        sp_col.append(a.salesperson)
        # El campo PREMISE del distribuidor gana al canal del mapa: es el dato,
        # no una inferencia.
        ch_col.append(fb_premise.get(str(name).strip()) or a.channel)
        rule_col.append(a.rule)
        why_col.append(a.reason)
        src_col.append("Favorite Brands PREMISE column"
                       if str(name).strip() in fb_premise else a.source)
    agg["salesperson"] = sp_col
    agg["channel"] = ch_col
    agg["attr_rule"] = rule_col
    agg["attr_reason"] = why_col
    agg["attr_source"] = src_col

    return agg.sort_values("bottles_all_sources", ascending=False)


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def _flexible_pattern(pattern: str) -> "re.Pattern":
    """
    Traduce un patrón glob a una regex INSENSIBLE a la puntuación separadora.

    Los nombres que entrega el cliente traen espacios, comas, apóstrofos y
    corchetes (`YTD by Month [Bottles, Orders] 8.24.26.xlsx`). Esos caracteres
    no pueden viajar en el ZIP distribuible —el instalador rechaza el paquete
    con "path with invalid characters"—, así que los archivos demo van con
    guiones. Un patrón literal no puede servir a los dos nombres a la vez.

    Cada tramo no alfanumérico del patrón se vuelve `[^A-Za-z0-9]*`, de modo que
    `1 - Supplier - Inventory*.xlsx` reconoce tanto el nombre real del cliente
    como `1-Supplier-Inventory-demo.xlsx`. `*` sigue siendo comodín.
    """
    out = []
    for ch in pattern:
        if ch == "*":
            out.append(".*")
        elif ch.isalnum():
            out.append(re.escape(ch))
        else:
            out.append(r"[^A-Za-z0-9]*")
    return re.compile("".join(out), re.IGNORECASE)


def _first_match(data_dir: str, pattern: str, required: bool = True) -> Optional[str]:
    matches = glob.glob(os.path.join(data_dir, pattern))
    if not matches and os.path.isdir(data_dir):
        # Segunda pasada tolerante a la puntuación (ver _flexible_pattern).
        rx = _flexible_pattern(pattern)
        matches = [
            os.path.join(data_dir, n)
            for n in os.listdir(data_dir)
            if rx.fullmatch(n) and os.path.isfile(os.path.join(data_dir, n))
        ]
    if not matches:
        if required:
            raise FileNotFoundError(f"No se encontró ningún archivo que haga match con '{pattern}' en {data_dir}")
        return None
    matches.sort(key=os.path.getmtime, reverse=True)
    return matches[0]


def _iso_week_start(dt) -> date:
    if isinstance(dt, pd.Timestamp):
        dt = dt.to_pydatetime()
    iso = dt.isocalendar()
    return date.fromisocalendar(iso[0], iso[1], 1)


_RESOLVER_CACHE: dict = {}


def _get_resolver(account_map: Optional[pd.DataFrame]):
    """
    Resolvedor de atribución, memorizado por identidad del mapa (construirlo
    indexa 259 cuentas y se llama por línea).

    `Scripts/loco_attribution.py` concentra la cascada. Antes la atribución vivía
    repartida en cuatro funciones con cuatro criterios distintos y cuatro cadenas
    "Unknown" diferentes, una de ellas con un motivo equivocado.
    """
    key = id(account_map) if account_map is not None else 0
    if key not in _RESOLVER_CACHE:
        _RESOLVER_CACHE.clear()
        _RESOLVER_CACHE[key] = _loco_attribution().build_resolver(account_map)
    return _RESOLVER_CACHE[key]


def _loco_attribution():
    """Import perezoso de `Scripts/loco_attribution.py`, memorizado."""
    scripts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    import loco_attribution
    return loco_attribution


def _match_known_salesperson(text, account_map: Optional[pd.DataFrame] = None) -> str:
    """Compatibilidad: delega en el rung R4 de la escalera. El roster ya no es un
    diccionario de cinco nombres de pila incrustado — vive en
    `Config/loco_tequila_us/salespeople.csv` e incluye a Sara y a Neeraj, que
    faltaban y caían a "Unknown" aunque sí estuvieran identificables."""
    return _get_resolver(account_map).resolve_person(text).salesperson


def _lookup_salesperson(account_name: str, account_map: Optional[pd.DataFrame]) -> str:
    """Compatibilidad: delega en los rungs R1-R3."""
    return _get_resolver(account_map).resolve_account(account_name).salesperson


def load_account_map(path: Optional[str]) -> Optional[pd.DataFrame]:
    if not path:
        return None
    df = pd.read_csv(path)
    required = {"account", "salesperson", "channel"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"--account-map debe tener columnas {required}; faltan {missing}")
    return df


# --------------------------------------------------------------------------
# Reconciliación contra el reporte real del 24-ago-2026
# (valores extraídos y verificados manualmente de
#  "Sales Report Loco USA August 24, 2026.xlsx"; solo tienen sentido si
#  --data-dir contiene el mismo corte de datos que se usó para ese reporte)
# --------------------------------------------------------------------------

REFERENCE_VALUES_2026_08_24 = {
    "inventory_grand_total_9l": 220.6483,
    "inventory_total_ca_9l": 198.2317,
    "inventory_total_tx_9l": 22.4167,
    "wholesale_9l_southern_glazers_union_city": 20.0,
    "wholesale_9l_southern_glazers_santa_fe": 36.0,
    "wholesale_9l_favorite_brands_houston": 23.0,
    "wholesale_9l_brescome_barton": 2.0,
    "wholesale_revenue_southern_glazers_union_city": 25625.0,
    "wholesale_revenue_southern_glazers_santa_fe": 58000.0,
    "wholesale_revenue_favorite_brands_houston": 28419.8,
    "wholesale_revenue_brescome_barton": 2805.0,
    "depletions_california_bottles_ytd": 545.0,
    "depletions_texas_bottles_ytd": 319.0,
    "depletions_dtc_bottles_ytd": 146.0,
    "depletions_ecommerce_bottles_ytd": 59.0,
}


def print_reconciliation(inventory_df: pd.DataFrame, wholesale_df: pd.DataFrame, depletions: dict) -> None:
    print("\n" + "=" * 78)
    print("RECONCILIACIÓN vs. valores reales del reporte del 24-ago-2026")
    print("(solo es representativa si --data-dir tiene el mismo corte de datos)")
    print("=" * 78)

    def row(label, computed, reference):
        diff = computed - reference if reference else None
        pct = (diff / reference * 100) if reference else None
        flag = "OK (validado)" if reference and abs(diff) < 0.01 else "revisar"
        print(f"{label:52s} calc={computed:>12.2f}  ref={reference:>12.2f}  diff={diff:>10.2f} ({pct:>6.1f}%)  [{flag}]")

    # El renglon "TOTAL" del reporte real EXCLUYE la categoria
    # "NOT SELLABLE - SAMPLES ONLY" (aparece como bloque aparte, sin sumar
    # al total principal) -> hay que excluirla aqui tambien o el total
    # calculado queda inflado por esa cantidad exacta.
    sellable = inventory_df[inventory_df["Product"] != "NOT SELLABLE - SAMPLES ONLY"]
    inv_total = sellable["Grand Total (9L)"].sum()
    inv_ca = sellable["Total CA (9L)"].sum()
    inv_tx = sellable["Total TX (9L)"].sum()
    row("Inventory: Grand Total 9L", inv_total, REFERENCE_VALUES_2026_08_24["inventory_grand_total_9l"])
    row("Inventory: Total CA 9L", inv_ca, REFERENCE_VALUES_2026_08_24["inventory_total_ca_9l"])
    row("Inventory: Total TX 9L", inv_tx, REFERENCE_VALUES_2026_08_24["inventory_total_tx_9l"])

    for cust, key_9l, key_rev in [
        ("Southern Glazer's - CA (Union City)", "wholesale_9l_southern_glazers_union_city", "wholesale_revenue_southern_glazers_union_city"),
        ("Southern Glazer's - CA (Santa Fe)", "wholesale_9l_southern_glazers_santa_fe", "wholesale_revenue_southern_glazers_santa_fe"),
        ("Favorite Brands - TX (Houston Ltl York)", "wholesale_9l_favorite_brands_houston", "wholesale_revenue_favorite_brands_houston"),
        ("Brescome & Barton - CT (North Haven)", "wholesale_9l_brescome_barton", "wholesale_revenue_brescome_barton"),
    ]:
        match = wholesale_df[wholesale_df["Customer"] == cust]
        computed_9l = float(match["9L"].sum()) if len(match) else 0.0
        computed_rev = float(match["Revenue (USD)"].sum()) if len(match) else 0.0
        row(f"Wholesale 9L: {cust}", computed_9l, REFERENCE_VALUES_2026_08_24[key_9l])
        row(f"Wholesale $: {cust}", computed_rev, REFERENCE_VALUES_2026_08_24[key_rev])

    row("Depletions California (bottles YTD)", depletions["california"]["bottles_ytd"], REFERENCE_VALUES_2026_08_24["depletions_california_bottles_ytd"])
    row("Depletions Texas (bottles YTD, solo FB)", depletions["texas"]["bottles_ytd"], REFERENCE_VALUES_2026_08_24["depletions_texas_bottles_ytd"])
    print(
        "\nNota: Texas 'solo FB' no incluye las cuentas on-premise atendidas "
        "directo por vendedor (Park Street, Customer Type='Salesperson'), que "
        "el reporte real sí cuenta dentro de 'Texas'. Ver .md sección 3.4."
    )


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data-dir", default="Client_Data/Loco_tequila_usa_data", help="Carpeta con los 8 archivos crudos")
    parser.add_argument("--output-dir", default="Output/simulacion_loco_usa", help="Carpeta donde se guardan los CSV calculados")
    parser.add_argument("--account-map", default=None, help="CSV opcional con columnas account,salesperson,channel")
    parser.add_argument("--skip-reconciliation", action="store_true", help="No imprimir la comparación contra el reporte del 24-ago-2026")
    args = parser.parse_args()

    if not os.path.isdir(args.data_dir):
        print(f"ERROR: no existe la carpeta de datos: {args.data_dir}", file=sys.stderr)
        return 1
    os.makedirs(args.output_dir, exist_ok=True)

    account_map = load_account_map(args.account_map)

    print(f"Cargando fuentes desde: {args.data_dir}")

    inventory_df = build_inventory_table(args.data_dir)
    inventory_df.to_csv(os.path.join(args.output_dir, "inventory.csv"), index=False)
    print(f"\n[Inventory] {len(inventory_df)} categorías de producto -> inventory.csv")
    print(inventory_df.to_string(index=False))

    wholesale_df, retail_df = build_wholesale_and_retail_tables(args.data_dir)
    wholesale_df.to_csv(os.path.join(args.output_dir, "wholesale.csv"), index=False)
    retail_df.to_csv(os.path.join(args.output_dir, "direct_to_retail.csv"), index=False)
    print(f"\n[Wholesale] {len(wholesale_df)} cuentas distribuidor -> wholesale.csv")
    print(wholesale_df.to_string(index=False))
    print(f"\n[Direct to Retail] {len(retail_df)} cuentas retail directo (APROXIMADO, ver .md 3.3) -> direct_to_retail.csv")
    print(retail_df.to_string(index=False))

    depletions = build_depletions_by_territory(args.data_dir)
    with open(os.path.join(args.output_dir, "depletions_by_territory.json"), "w", encoding="utf-8") as f:
        json.dump(depletions, f, indent=2, default=str)
    print(f"\n[Depletions] California YTD bottles={depletions['california']['bottles_ytd']:.1f}  "
          f"Texas YTD bottles (solo FB)={depletions['texas']['bottles_ytd']:.1f} -> depletions_by_territory.json")

    dtc = build_dtc_ecommerce_split(args.data_dir)
    with open(os.path.join(args.output_dir, "dtc_ecommerce_split.json"), "w", encoding="utf-8") as f:
        json.dump(dtc, f, indent=2, default=str)
    print(f"\n[DTC/Ecommerce] (HIPÓTESIS, ver .md 3.6) -> dtc_ecommerce_split.json")
    print(json.dumps(dtc, indent=2, default=str))

    salesperson_week_df = build_salesperson_by_week(args.data_dir, account_map)
    salesperson_week_df.to_csv(os.path.join(args.output_dir, "salesperson_by_week.csv"))
    print(f"\n[Salesperson by Week] {len(salesperson_week_df)} semanas -> salesperson_by_week.csv")

    accounts_df = build_accounts_summary(args.data_dir, account_map)
    accounts_df.to_csv(os.path.join(args.output_dir, "accounts_summary.csv"), index=False)
    print(f"\n[Accounts Summary] {len(accounts_df)} cuentas (Salesperson/Channel {'con' if account_map is not None else 'SIN'} mapeo manual) -> accounts_summary.csv")

    if not args.skip_reconciliation:
        print_reconciliation(inventory_df, wholesale_df, depletions)

    print(f"\nListo. Archivos calculados guardados en: {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
