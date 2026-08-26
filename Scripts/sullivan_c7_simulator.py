"""
================================================================================
 SULLIVAN RUTHERFORD ESTATE — SIMULADOR DE EXPORTS COMMERCE7
================================================================================
Genera datos SINTÉTICOS (no reales) que respetan la estructura, las reglas de
negocio y las proporciones observadas en los 5 exports reales de abril 2026:

    Apr_OrderSales.xlsx        (583 renglones ítem, base transaccional)
    Apr_FinancialReport.xlsx   (583 renglones, espejo financiero)
    Apr_SalesbyChannel.xlsx    (agregado por canal)
    Apr_SalesbyClub.xlsx       (agregado por club)
    Apr_SalesbyTag.xlsx        (agregado por Order Tag)

DISEÑADO PARA GOOGLE COLABORATORY
----------------------------------
1. Sube este archivo o pega su contenido en una celda de Colab.
2. Ajusta los parámetros en `CONFIG` (mes, año, # de órdenes base, tendencia).
3. Ejecuta. Al final se generan los 5 .xlsx y (si corres en Colab) se ofrecen
   para descarga automática.

--------------------------------------------------------------------------------
NOTA IMPORTANTE — Apr_SalesbyTag no es derivable de OrderSales/FinancialReport
--------------------------------------------------------------------------------
Al auditar los archivos reales se confirmó que ninguno de los 114/44 columnas
exportadas de `Apr_OrderSales` / `Apr_FinancialReport` contiene una columna de
"Order Tag" o "Order Tags" (a pesar de que la guía interna del cliente la
menciona como campo clave). Los tags reales de abril observados fueron:

  - "J.O. Sullivan Library Collection - 2026"  -> 430 órdenes (95.3% de ventas)
      (tag de campaña/colección aplicado casi universalmente en el periodo)
  - "R - <Nombre Referente>"                    -> 8 órdenes de referidos (1 c/u)
  - "Founder's Club"                             -> 1 orden (caso mixto/anómalo)

Es decir, el tag vive en Commerce7 como una dimensión INDEPENDIENTE (campaña de
marketing / atribución de referido) que no se puede reconstruir con Channel,
Club o SKU. Por eso este simulador la trata como su propio generador aleatorio
("motor de tags"), documentado en `simulate_order_tags()`, en vez de derivarla
de las otras columnas — así se preserva fielmente el comportamiento real y se
deja evidencia para que el cliente confirme si quiere seguir así o exportar el
campo real de tags en el futuro.
================================================================================
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# ==============================================================================
# 0. CONFIGURACIÓN — ajustar aquí para simular otros meses / volúmenes
# ==============================================================================
CONFIG = {
    "year": 2026,
    "month": 4,                 # 1-12
    "seed": 42,                 # cambia la semilla para otra corrida
    "n_orders_base": 430,       # abril real = 430 órdenes; escala con growth_trend
    "growth_trend_pct": 0.0,    # +5.0 = crecer 5% vs línea base (para simular meses futuros)
    "output_prefix": "Apr",     # prefijo de archivo (cambiar por mes, ej. "May")
}

rng = np.random.default_rng(CONFIG["seed"])

# ==============================================================================
# 1. CATÁLOGO DE PRODUCTOS — tomado del catálogo real observado en OrderSales
#    (SKU, Título, Tipo, Precio de lista, peso de frecuencia de venta)
# ==============================================================================
PRODUCT_CATALOG = [
    # SKU              Título                                     Tipo                   Precio   Peso
    ("23ML712JB",  "2023 J.O. Merlot, 3 Bottles",              "Bundle",              750.00,  17.0),
    ("23NVC712",   "2023 Napa Valley Cabernet",                "Wine",                136.00,  10.5),
    ("FounderTasting125", "Founder's Reserve Tasting",         "General Merchandise", 150.00,   3.7),
    ("23ML712J",   "2023 J.O. Sullivan Merlot",                "Wine",                350.00,   3.1),
    ("OrderFee",   "Order Fee",                                "General Merchandise",   5.00,   2.2),
    ("CompDisc",   "Complimentary Discount",                   "General Merchandise",    0.00,   1.9),
    ("21CS712J",   "2021 J.O. Sullivan Cabernet Sauvignon",    "Wine",                390.00,   1.7),
    ("22ML712J",   "2022 J.O. Sullivan Merlot",                "Wine",                370.00,   1.6),
    ("22CS712J",   "2022 J.O. Sullivan Cabernet Sauvignon",    "Wine",                370.00,   1.3),
    ("24RO712",    "2024 Rosé",                                "Wine",                 60.00,   1.2),
    ("22CH712",    "2022 Chardonnay",                          "Wine",                 72.25,   1.0),
    ("21ME712J",   "2021 J.O. Sullivan Merlot",                "Wine",                390.00,   0.9),
    ("22CH7123pk", "2022 Chardonnay 3pk",                      "Bundle",              216.75,   0.9),
    ("20CS712J",   "2020 J.O. Sullivan Cabernet Sauvignon",    "Wine",                410.00,   0.7),
    ("22HV712",    "2022 Heart of the Vineyard",               "Wine",                152.00,   0.7),
    ("24RO7123pk", "2024 Rosé 3pk",                            "Bundle",              180.00,   0.6),
    ("POETRYINNFT","Sttupa Estate Founder's Experience",       "General Merchandise", 350.00,   0.5),
    ("Membership", "Membership",                               "General Merchandise",   0.00,   0.5),
    ("PartnershipSRE","Partnership  - SRE",                    "Rebate",              -50.00,   0.5),
    ("TASTINGFEE", "Estate Tasting",                            "General Merchandise", 125.00,   0.4),
    ("21CF712J",   "2021 J.O. Sullivan Cabernet Franc",        "Wine",                390.00,   0.4),
    ("19PA712",    "2019 PA Vinea",                             "Wine",                830.00,   0.4),
    ("20ML712J",   "2020 J.O. Sullivan Merlot",                "Wine",                410.00,   0.4),
    ("21ME106J",   "2021 J.O. Sullivan Merlot 1.5L",           "Wine",                760.00,   0.3),
    ("21PA712",    "2021 PA Vinea",                             "Wine",                790.00,   0.3),
    ("22ML712JB",  "2022 J.O. Merlot, 3 Bottles",              "Bundle",             1110.00,   0.3),
    ("CS13712",    "2013 Cabernet Sauvignon",                   "Wine",                212.50,   0.3),
    ("23CH712",    "2023 Chardonnay",                           "Wine",                 72.25,   0.3),
    ("21CS712JB",  "2021 J.O. Cabernet Sauvignon, 3 Bottles in Box","Bundle",         1170.00,   0.3),
    ("22CS712",    "2022 Estate Cabernet Sauvignon",            "Wine",                136.00,   0.3),
    ("HeartoftheValley","Lunch Experience",                     "General Merchandise", 350.00,   0.3),
    ("ACOM",       "A Conversation on Merlot",                  "General Merchandise", 200.00,   0.3),
]
SKU, TITLE, TYPE, PRICE, WEIGHT = 0, 1, 2, 3, 4
_cat_weights = np.array([p[WEIGHT] for p in PRODUCT_CATALOG], dtype=float)
_cat_weights = _cat_weights / _cat_weights.sum()

# ==============================================================================
# 2. DISTRIBUCIONES REALES OBSERVADAS (abril 2026, `Apr_SalesbyChannel/Club`)
#    Se usan como ancla estadística; el simulador NO copia los datos, genera
#    nuevas órdenes que respetan estas proporciones +/- ruido natural.
# ==============================================================================
CHANNEL_SHARE = {          # % de órdenes por canal (no % de $, eso se deriva)
    "POS": 61 / 430,
    "Web": 56 / 430,
    "Club": 295 / 430,
    "Inbound": 18 / 430,
}

CLUB_PACKAGE_SHARE = {     # dentro de Club: (paquete, share de órdenes de Club, avg order value, std)
    "Estate 4 Bottle":        dict(club="Estate",     share=87 / 295, avg=519.90,  std=60),
    "Estate 6 Bottle":        dict(club="Estate",     share=8 / 295,  avg=816.00,  std=90),
    "Founder's 3 Bottle":     dict(club="Founder's",  share=101 / 295, avg=961.47, std=110),
    "Founder's Half Case":    dict(club="Founder's",  share=77 / 295, avg=1795.97, std=180),
    "Founder's Single Case":  dict(club="Founder's",  share=17 / 295, avg=3746.47, std=350),
    "Founder's Double Case":  dict(club="Founder's",  share=2 / 295,  avg=8400.00, std=400),
    "Admin/POS Marked as Club": dict(club="Review",   share=3 / 295,  avg=932.67, std=200),
}

INBOUND_TAG_SHARE = {      # dentro de Inbound: casi todo Telesales en abril real
    "Telesales": 1.0, "Event": 0.0, "Corporate": 0.0, "Friends & Family": 0.0,
}

CHANNEL_ORDER_VALUE = {     # (avg, std) de SubTotal por orden, canal no-Club
    "POS": (839.28, 260.0),
    "Web": (155.45, 60.0),      # 100% Tock en abril real
    "Inbound": (168.53, 90.0),
}

STATE_TAX_RATE_BAND = (0.055, 0.0925)   # rango realista de sales tax por estado destino US
SHIP_RATE_BY_CHANNEL = {"Club": 0.0196, "POS": 0.0157, "Web": 0.0, "Inbound": 0.072}

US_STATES = ["CA", "NY", "TX", "WA", "FL", "IL", "CO", "OR", "NV", "AZ", "MA", "NJ"]

FIRST_NAMES = ["James", "Maria", "Robert", "Linda", "Michael", "Susan", "David",
               "Karen", "William", "Patricia", "Charles", "Nancy", "Thomas", "Betty"]
LAST_NAMES = ["Sullivan", "Chernick", "Newberry", "Scholl", "White", "Pour", "Day",
              "Kapscandy", "Bennett", "Foster", "Reyes", "Coleman", "Ortiz", "Bishop"]

# ==============================================================================
# 3. MOTOR DE TAGS (Order Tags) — dimensión independiente, ver nota al inicio
# ==============================================================================
def simulate_order_tags(n_orders, year, month):
    """
    Devuelve una lista de tags (uno por orden) que reproduce el patrón real:
      - ~95% de las órdenes llevan el tag de campaña/colección del periodo.
      - un puñado (~2%) lleva un tag de referido "R - Nombre Apellido".
      - 0-3 órdenes (anomalías) llevan un tag de club aunque su canal real
        no sea Club (mismo patrón que "Admin/POS Order Marked as Club").
    """
    collection_tag = f"J.O. Sullivan Library Collection - {year}"
    tags = np.full(n_orders, collection_tag, dtype=object)

    n_referrals = max(1, round(n_orders * 0.018))
    referral_idx = rng.choice(n_orders, size=min(n_referrals, n_orders), replace=False)
    for i in referral_idx:
        name = f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"
        tags[i] = f"R - {name}"

    return tags, collection_tag


# ==============================================================================
# 4. GENERACIÓN DE ÓRDENES (nivel orden)
# ==============================================================================
def month_date_range(year, month):
    start = datetime(year, month, 1)
    if month == 12:
        end = datetime(year + 1, 1, 1) - timedelta(seconds=1)
    else:
        end = datetime(year, month + 1, 1) - timedelta(seconds=1)
    return start, end


def simulate_orders(cfg):
    n_orders = round(cfg["n_orders_base"] * (1 + cfg["growth_trend_pct"] / 100))
    year, month = cfg["year"], cfg["month"]
    start, end = month_date_range(year, month)
    total_seconds = int((end - start).total_seconds())

    # -- 4.1 Canal asignado por orden, respetando proporciones reales --------
    channels = rng.choice(
        list(CHANNEL_SHARE.keys()), size=n_orders, p=list(CHANNEL_SHARE.values())
    )

    order_numbers = np.arange(517502, 517502 + n_orders)
    submitted = [start + timedelta(seconds=int(rng.uniform(0, total_seconds))) for _ in range(n_orders)]
    submitted.sort()

    club_titles = np.full(n_orders, "", dtype=object)
    club_packages = np.full(n_orders, "", dtype=object)
    order_subtotal = np.zeros(n_orders)
    external_vendor = np.full(n_orders, "", dtype=object)
    sales_attribute = channels.copy()

    club_idx = np.where(channels == "Club")[0]
    pkg_names = list(CLUB_PACKAGE_SHARE.keys())
    pkg_probs = [v["share"] for v in CLUB_PACKAGE_SHARE.values()]
    pkg_probs = np.array(pkg_probs) / np.sum(pkg_probs)
    pkgs_assigned = rng.choice(pkg_names, size=len(club_idx), p=pkg_probs)
    for i, pkg in zip(club_idx, pkgs_assigned):
        info = CLUB_PACKAGE_SHARE[pkg]
        club_packages[i] = pkg
        if info["club"] == "Review":
            # Caso anómalo: marcado como Club desde POS/Admin -> Sales Attribute distinto
            club_titles[i] = "Founder's" if rng.random() < 0.5 else "Estate"
            sales_attribute[i] = "POS"
        else:
            club_titles[i] = info["club"]
        order_subtotal[i] = max(50, rng.normal(info["avg"], info["std"]))

    for chan in ("POS", "Web", "Inbound"):
        idx = np.where(channels == chan)[0]
        if chan == "Web":
            external_vendor[idx] = "Tock"
        if len(idx):
            avg, std = CHANNEL_ORDER_VALUE[chan]
            order_subtotal[idx] = np.clip(rng.normal(avg, std, size=len(idx)), 15, None)

    tags, collection_tag = simulate_order_tags(n_orders, year, month)

    orders = pd.DataFrame({
        "Order Number": order_numbers,
        "Order Submitted Date": submitted,
        "Order Paid Date": submitted,
        "Channel": channels,
        "Sales Attribute": sales_attribute,
        "Club Title": club_titles,
        "Club Package": club_packages,
        "External Order Vendor": external_vendor,
        "Order Source": np.where(external_vendor == "Tock", "External", "Internal"),
        "Order Tag": tags,
        "State Code": rng.choice(US_STATES, size=n_orders),
        "SubTotal_target": order_subtotal,
    })
    return orders, collection_tag


# ==============================================================================
# 5. EXPLOSIÓN A NIVEL ÍTEM (Apr_OrderSales) — 1..N renglones por orden
# ==============================================================================
def explode_to_items(orders):
    rows = []
    for _, o in orders.iterrows():
        target = o["SubTotal_target"]
        n_lines = int(rng.choice([1, 1, 2, 2, 3, 4], p=[0.30, 0.25, 0.20, 0.13, 0.08, 0.04]))
        remaining = target
        for line_i in range(n_lines):
            is_last = line_i == n_lines - 1
            prod = PRODUCT_CATALOG[rng.choice(len(PRODUCT_CATALOG), p=_cat_weights)]
            qty = max(1, int(round(rng.gamma(2.0, 1.2))))
            if is_last:
                line_total = max(5.0, remaining)
            else:
                line_total = max(5.0, remaining * rng.uniform(0.3, 0.7))
            remaining -= line_total
            price = round(line_total / qty, 2) if qty else round(line_total, 2)

            rows.append({
                "Order Number": o["Order Number"],
                "Order Submitted Date": o["Order Submitted Date"],
                "Order Paid Date": o["Order Paid Date"],
                "Channel": o["Channel"],
                "Sales Attribute": o["Sales Attribute"],
                "Club Title": o["Club Title"],
                "Club Package": o["Club Package"],
                "External Order Vendor": o["External Order Vendor"],
                "Order Source": o["Order Source"],
                "Order Tag": o["Order Tag"],
                "Bill To State Code": o["State Code"],
                "Ship To State Code": o["State Code"],
                "Product Title": prod[TITLE],
                "SKU": prod[SKU],
                "Type": prod[TYPE],
                "Quantity": float(qty),
                "Price": price,
                "Product SubTotal": round(price * qty, 2),
            })

    items = pd.DataFrame(rows)

    # -- Fees / impuestos / envío a nivel orden, distribuidos a última línea de cada orden
    items["SubTotal"] = items.groupby("Order Number")["Product SubTotal"].transform("sum")
    tax_rate = rng.uniform(*STATE_TAX_RATE_BAND, size=len(items))
    ship_rate = items["Channel"].map(SHIP_RATE_BY_CHANNEL).fillna(0.02).to_numpy()
    items["Tax Total"] = (items["SubTotal"] * tax_rate).round(2)
    items["Shipping Total"] = (items["SubTotal"] * ship_rate).round(2)
    items["Cost of Good"] = (items["Product SubTotal"] * rng.uniform(0.18, 0.28, size=len(items))).round(2)
    items["Total"] = (items["SubTotal"] + items["Tax Total"] + items["Shipping Total"]).round(2)
    items["Tip"] = 0.0
    items["Total After Tip"] = items["Total"]

    # -- Regla crítica de desambiguación: duplicar (Order Number + SKU) en ~2% de casos
    #    para simular fielmente los "9 casos" de renglones repetidos del dataset real
    dup_candidates = items.groupby(["Order Number", "SKU"]).size()
    dup_candidates = dup_candidates[dup_candidates == 1].reset_index()
    n_dup = max(1, round(len(items) * 0.015))
    if len(dup_candidates) > n_dup:
        chosen = dup_candidates.sample(n=n_dup, random_state=CONFIG["seed"])
        extra_rows = []
        for _, c in chosen.iterrows():
            base = items[(items["Order Number"] == c["Order Number"]) & (items["SKU"] == c["SKU"])].iloc[0].copy()
            base["Quantity"] = max(1.0, base["Quantity"] + rng.integers(1, 3))
            base["Price"] = round(base["Price"] * rng.uniform(0.9, 1.1), 2)
            extra_rows.append(base)
        items = pd.concat([items, pd.DataFrame(extra_rows)], ignore_index=True)

    return items


# ==============================================================================
# 6. CONSTRUCCIÓN DE LOS 5 REPORTES DE SALIDA
# ==============================================================================
def build_order_sales(items):
    df = items.copy()
    df.insert(0, "Id", [f"sim-{i:06d}" for i in range(len(df))])
    df["Total Volume in ML"] = df["Quantity"] * 750
    return df


def build_financial_report(items):
    df = items[[
        "Order Number", "Order Submitted Date", "Order Paid Date", "Channel",
        "Sales Attribute", "Club Title", "Product Title", "Type", "SKU",
        "Quantity", "Price", "Cost of Good", "SubTotal", "Shipping Total",
        "Tax Total", "Total",
    ]].copy()
    df = df.rename(columns={"Club Title": "Club Name"})
    df["Total Discount"] = 0.0
    df["Tip Total"] = 0.0
    df["Total After Tip"] = df["Total"]
    return df


def _aggregate_control(items, group_col, rename_to):
    g = items.groupby(group_col, dropna=False).agg(
        **{
            "Order Count": ("Order Number", "nunique"),
            "Sub Total": ("Product SubTotal", "sum"),
            "Cost of Good Total": ("Cost of Good", "sum"),
            "Ship Total": ("Shipping Total", "sum"),
            "Tax Total": ("Tax Total", "sum"),
        }
    ).reset_index().rename(columns={group_col: rename_to})
    g["Bottle Deposit Total"] = 0.0
    g["Duty Total"] = 0.0
    g["Total"] = (g["Sub Total"] + g["Ship Total"] + g["Tax Total"]).round(2)
    g["Tip Total"] = 0.0
    g["Total After Tip"] = g["Total"]
    total_sub = g["Sub Total"].sum()
    g["Percentage of Sales"] = (g["Sub Total"] / total_sub * 100).round(2)
    ordered_cols = [rename_to, "Order Count", "Percentage of Sales", "Sub Total",
                    "Cost of Good Total", "Ship Total", "Tax Total", "Bottle Deposit Total",
                    "Duty Total", "Total", "Tip Total", "Total After Tip"]
    return g[ordered_cols].sort_values("Sub Total", ascending=False).reset_index(drop=True)


def build_sales_by_channel(items):
    return _aggregate_control(items, "Channel", "Channel")


def build_sales_by_club(items):
    club_items = items[items["Club Title"] != ""]
    out = _aggregate_control(club_items, "Club Package", "Club")
    return out


def build_sales_by_tag(items):
    # Nota: agrega por orden única (un tag por orden), no por línea, para que
    # Order Count / Sub Total cuadren con la lógica real de Commerce7.
    per_order = items.drop_duplicates("Order Number")[["Order Number", "Order Tag"]]
    merged = items.merge(per_order, on="Order Number", suffixes=("", "_orderlevel"))
    return _aggregate_control(items.assign(**{"Order Tag": items["Order Tag"]}), "Order Tag", "Order Tag")


# ==============================================================================
# 7. VALIDACIÓN DE RECONCILIACIÓN (regla de oro de la guía: tolerancia cero)
# ==============================================================================
def validate(items, by_channel, by_club, by_tag):
    total_items = items["Product SubTotal"].sum()
    checks = {
        "OrderSales SubTotal == SalesbyChannel SubTotal": np.isclose(total_items, by_channel["Sub Total"].sum(), atol=1.0),
        "OrderSales SubTotal == SalesbyTag SubTotal": np.isclose(total_items, by_tag["Sub Total"].sum(), atol=1.0),
        "N° órdenes únicas == Order Count total (channel)": items["Order Number"].nunique() == by_channel["Order Count"].sum(),
    }
    print("\n--- VALIDACIÓN DE RECONCILIACIÓN ---")
    for k, v in checks.items():
        print(f"  [{'OK' if v else 'FALLÓ'}] {k}")
    return all(checks.values())


# ==============================================================================
# 8. MAIN
# ==============================================================================
def run(cfg=CONFIG):
    orders, collection_tag = simulate_orders(cfg)
    items = explode_to_items(orders)

    order_sales = build_order_sales(items)
    financial_report = build_financial_report(items)
    by_channel = build_sales_by_channel(items)
    by_club = build_sales_by_club(items)
    by_tag = build_sales_by_tag(items)

    validate(items, by_channel, by_club, by_tag)

    prefix = cfg["output_prefix"]
    files = {
        f"{prefix}_OrderSales.xlsx": order_sales,
        f"{prefix}_FinancialReport.xlsx": financial_report,
        f"{prefix}_SalesbyChannel.xlsx": by_channel,
        f"{prefix}_SalesbyClub.xlsx": by_club,
        f"{prefix}_SalesbyTag.xlsx": by_tag,
    }
    for fname, df in files.items():
        df.to_excel(fname, index=False)
        print(f"Generado: {fname}  ({len(df)} filas)")

    # Descarga automática si corre en Google Colab
    try:
        from google.colab import files as colab_files  # type: ignore
        for fname in files:
            colab_files.download(fname)
    except ImportError:
        pass

    return files


if __name__ == "__main__":
    run(CONFIG)
