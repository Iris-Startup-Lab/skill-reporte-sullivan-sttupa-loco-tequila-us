"""
================================================================================
 GENERADOR DE DATOS DEMO — Sullivan (mensual y semanal) y Loco Tequila USA
================================================================================
Construye en `Data_for_demo/` un juego COMPLETO de archivos de entrada
SINTÉTICOS que reproduce la ESTRUCTURA exacta de los insumos reales de cada
cliente: mismos nombres de archivo (patrones de búsqueda), mismos encabezados
—incluidos los irregulares que se leen por posición— y las mismas reglas de
negocio.

¿Por qué existe este script?
----------------------------
Los flujos semanal de Sullivan y de Loco Tequila leían únicamente de
`Client_Data/`, que el empaquetador excluye a propósito (son datos del cliente
y no se distribuyen). Resultado: la habilidad recién instalada NO podía generar
esos dos reportes sin que el usuario aportara sus propios archivos. Con estos
demos, los tres reportes corren "de fábrica" y el usuario puede ver la forma
que deben tener sus datos antes de sustituirlos por los propios.

Nada aquí es dato real: nombres de cuenta, clientes, direcciones e importes son
inventados. Lo que se conserva —y es lo único que importa para probar— es la
ESTRUCTURA y las relaciones entre archivos.

Casos que los demos ejercitan a propósito
-----------------------------------------
Sullivan semanal
  * Club con programa reconocible (Founder's y Estate).
  * Club SIN programa -> cae en "Unclassified" con su motivo (regla nueva).
  * Web con vendor Tock (se excluye de Web/Ecommerce) y Web sin vendor.
  * Una devolución con importe negativo.
  * Open POs en los tres buckets de aging, incluido uno vencido a >30 días.
  * Facturas PAID (efectivo cobrado) junto a las OPEN.
  * iDig con su encabezado de dos pisos y la fila Total/Total.
Loco Tequila USA
  * Un SKU "NOT SELLABLE - SAMPLES ONLY" -> debe quedar FUERA del inventario
    comercial y reportarse aparte.
  * Material de empaque con prefijo "Z-" -> debe excluirse del inventario.
  * Un 200 mL -> factor de conversión a caja 9L distinto (24 botellas, no 6).
  * Inventario de vendedor ("Salesperson Inventory") separado de bodega.
  * Ecommerce con y sin tag -> separa Ecommerce de DTC atribuido.
  * Las tres categorías de cliente de Park Street: Wholesaler / Retailer /
    Salesperson.

Uso
---
    python Scripts/make_demo_data.py                 # los tres juegos
    python Scripts/make_demo_data.py --brand loco
    python Scripts/make_demo_data.py --brand sullivan_weekly
    python Scripts/make_demo_data.py --brand sullivan_monthly
================================================================================
"""

from __future__ import annotations

import csv
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import openpyxl
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEMO_ROOT = PROJECT_ROOT / "Data_for_demo"

SULLIVAN_MONTHLY_DIR = DEMO_ROOT / "Sullivan_data_demo"
SULLIVAN_WEEKLY_DIR = DEMO_ROOT / "Sullivan_weekly_demo"
LOCO_DIR = DEMO_ROOT / "Loco_tequila_demo"

# El nombre de esta subcarpeta NO es libre: `_find_fb_depletion_folder` la
# busca por prefijo normalizado ("fbdepletionreports"). Va con guiones, no con
# espacios, porque TODO lo que viaja en el ZIP distribuible debe tener rutas de
# solo [A-Za-z0-9._/-]: el instalador rechaza el paquete completo con "path with
# invalid characters" si encuentra un espacio, un apóstrofo o un corchete.
LOCO_FB_SUBDIR = "FB-Depletion-Reports-2026"


def _say(msg: str) -> None:
    print(f"  {msg}")


def _write_sheet(path: Path, rows: list, sheet_title: str = "Sheet1") -> None:
    """Escribe una hoja fila por fila. Se usa openpyxl y no pandas porque
    varios insumos reales traen filas de título, filas vacías y encabezados
    de dos pisos que pandas no puede reproducir."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = sheet_title
    for row in rows:
        ws.append(list(row))
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)
    wb.close()


def _write_csv(path: Path, header: list, rows: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)


# ==============================================================================
# 1. SULLIVAN — CADENCIA SEMANAL
# ==============================================================================

# Órdenes a nivel ORDEN. El lector semanal deduplica por Order Number y usa el
# SubTotal de la orden, así que este es el nivel donde vive la verdad.
#   (orden, canal, vendor externo, Club Title, Club Package, SubTotal)
WEEKLY_ORDERS = [
    (600101, "POS",     "",     "",                      "",                           1240.00),
    (600102, "POS",     "",     "",                      "",                            385.50),
    (600103, "POS",     "",     "",                      "",                             96.00),
    (600104, "Web",     "",     "",                      "",                            612.00),
    # Vendor Tock: se excluye de Web/Ecommerce porque su dinero entra por el
    # archivo de Tock. Si no se excluyera, se contaría dos veces.
    (600105, "Web",     "Tock", "",                      "",                            150.00),
    (600106, "Inbound", "",     "",                      "",                            268.00),
    (600107, "Inbound", "",     "",                      "",                             74.25),
    (600108, "Club",    "",     "Founder's Half Case",   "Sept26 Founders Half Case",  1795.00),
    (600109, "Club",    "",     "Founder's 3 Bottle",    "Sept26 Founders 3 Bottle",    961.00),
    (600110, "Club",    "",     "Estate 4 Bottle",       "Sept26 Estate 4 Bottle",      519.00),
    (600111, "Club",    "",     "Estate 6 Bottle",       "Sept26 Estate 6 Bottle",      816.00),
    # Club SIN programa nombrado: ni "founder" ni "estate" en paquete/título.
    # Debe caer en "Unclassified" con motivo "Club channel, no program named".
    (600112, "Club",    "",     "",                      "",                            930.00),
    (600113, "Club",    "",     "",                      "",                            412.00),
    # Devolución: importe negativo, para verificar que no se descarta ni se
    # convierte en positivo en ningún punto de la cadena.
    (600114, "POS",     "",     "",                      "",                           -260.00),
]

# Catálogo demo (SKU, título, tipo, precio de lista). Nombres inventados con la
# nomenclatura de una bodega de Napa, sin copiar el catálogo real.
WEEKLY_PRODUCTS = [
    ("DEMO-CAB-750",   "2023 Estate Cabernet Sauvignon", "Wine",                136.00),
    ("DEMO-MER-750",   "2023 Reserve Merlot",            "Wine",                175.00),
    ("DEMO-CHA-750",   "2024 Estate Chardonnay",         "Wine",                 72.00),
    ("DEMO-ROS-750",   "2025 Rosé",                      "Wine",                 60.00),
    ("DEMO-TASTING",   "Estate Tasting Experience",      "General Merchandise", 125.00),
    ("DEMO-FEE",       "Order Fee",                      "General Merchandise",   5.00),
]

WEEKLY_SHIP = [
    ("CA", "94574", "Saint Helena"),
    ("CA", "94558", "Napa"),
    ("NY", "10011", "New York"),
    ("TX", "78701", "Austin"),
    ("FL", "33139", "Miami Beach"),
    ("IL", "60614", "Chicago"),
]

WEEKLY_NAMES = [
    ("Avery", "Lindqvist"), ("Dashiell", "Okonkwo"), ("Marisol", "Tavares"),
    ("Priya", "Raghunathan"), ("Soren", "Blackwood"), ("Ines", "Valdovinos"),
    ("Tobias", "Merriweather"), ("Noor", "Al-Habsi"), ("Camille", "Deschamps"),
    ("Rafael", "Quintanilla"), ("Hattie", "Brennerman"), ("Yusuf", "Adeyemi"),
    ("Solveig", "Nordstrom"), ("Emiliano", "Cifuentes"),
]

# 114 columnas es el ancho del export real de Commerce7. El lector semanal usa
# 6 de ellas; aquí se escriben las que tienen contenido útil y se documenta el
# resto en DATOS_REQUERIDOS.md, para no inflar el demo con 100 columnas vacías.
WEEKLY_ORDER_COLUMNS = [
    "Id", "Order Submitted Date", "Order Paid Date", "Order Fulfilled Date",
    "Order Number", "External Order Vendor", "Order Source", "Payment Status",
    "Fulfillment Status", "Channel", "Sales Attribute", "Order Delivery Method",
    "POS Profile", "SubTotal", "Shipping Total", "Tax Total", "Total",
    "Total After Tip", "Club Title", "Club Package",
    "Customer First Name", "Customer Last Name", "Customer Email",
    "Ship To First Name", "Ship To Last Name", "Ship To Address",
    "Ship To City", "Ship To State Code", "Ship To Zip Code", "Ship To Country Code",
    "Sales Associate", "Product Title", "Type", "SKU", "Quantity",
    "Bottle Quantity", "Price", "Product SubTotal", "Department Code",
]

# Semana de referencia (lunes a domingo). Es la que reproduce las cifras ya
# verificadas; el resto de la serie se deriva desplazando desde aquí.
WEEK_START = date(2026, 8, 17)
WEEK_END = date(2026, 8, 23)

# Serie de semanas del demo: (inicio de semana, escala, etiqueta de archivo).
# La escala mueve todos los importes para que el WoW del dashboard tenga algo
# que comparar y la línea de tendencia deje de ser un punto suelto. La ÚLTIMA
# va en 1.0 a propósito: es la semana verificada y sus números no deben cambiar.
#
# La curva no es monótona a propósito: con una subida constante no se podría
# distinguir un WoW bien calculado de uno que siempre da positivo. La semana
# del 8/16 baja respecto a la del 8/09.
WEEKLY_SERIES = [
    (date(2026, 7, 27), 0.72, "8.02.26"),
    (date(2026, 8,  3), 0.94, "8.09.26"),
    (date(2026, 8, 10), 0.81, "8.16.26"),
    (WEEK_START,        1.00, "8.23.26"),
]


def _weekly_order_lines(order) -> list:
    """Explota una orden en 1..3 líneas de producto cuyos importes suman el
    SubTotal de la orden. Determinista: el reparto depende del número de orden,
    no de un generador aleatorio, para que el demo sea reproducible."""
    num, channel, vendor, title, package, subtotal = order
    n_lines = 1 + (num % 3)
    if abs(subtotal) < 120:
        n_lines = 1

    shares = {1: [1.0], 2: [0.62, 0.38], 3: [0.5, 0.3, 0.2]}[n_lines]
    amounts = [round(subtotal * s, 2) for s in shares]
    # El redondeo de los repartos puede desviar centavos: la última línea
    # absorbe la diferencia para que la suma sea EXACTA.
    amounts[-1] = round(subtotal - sum(amounts[:-1]), 2)

    lines = []
    for i, amount in enumerate(amounts):
        sku, ptitle, ptype, _price = WEEKLY_PRODUCTS[(num + i) % len(WEEKLY_PRODUCTS)]
        qty = 1 if abs(amount) < 200 else 2
        lines.append((sku, ptitle, ptype, qty, round(amount / qty, 2), amount))
    return lines


def build_sullivan_weekly(out_dir: Path = SULLIVAN_WEEKLY_DIR,
                          week_start: date = WEEK_START,
                          scale: float = 1.0,
                          tag: str = "8.23.26") -> dict:
    """
    Genera los 4 insumos de UNA semana.

    `week_start` desplaza todas las fechas y `scale` escala todos los importes,
    para poder emitir una serie de varias semanas sin duplicar el generador.
    Con los valores por omisión reproduce **exactamente** la semana del
    2026-08-23 que ya está verificada ($9,148.13 de Total DTC, $7,840.00 de
    efectivo, 13.4 cajas 9L): así añadir semanas no invalida las cifras de
    referencia.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    written = {}

    shift = week_start - WEEK_START
    week_end = week_start + timedelta(days=6)

    def D(d: date) -> date:
        """Misma fecha, corrida al periodo de esta semana."""
        return d + shift

    def S(x: float) -> float:
        """Importe escalado. Se redondea a centavos aquí y no al final para que
        lo que se escribe en el archivo sea exactamente lo que el lector suma."""
        return round(x * scale, 2)

    # ------------------------------------------------------- 1. OrderReport
    rows = []
    for idx, order in enumerate(WEEKLY_ORDERS):
        num, channel, vendor, title, package, subtotal = order
        subtotal = S(subtotal)
        order = (num, channel, vendor, title, package, subtotal)
        submitted = datetime.combine(
            week_start + timedelta(days=idx % 7), datetime.min.time()
        ) + timedelta(hours=9 + (idx % 8), minutes=(idx * 7) % 60)
        state, zip_code, city = WEEKLY_SHIP[idx % len(WEEKLY_SHIP)]
        first, last = WEEKLY_NAMES[idx % len(WEEKLY_NAMES)]

        # Impuesto y envío se calculan UNA vez por orden y se repiten en cada
        # línea, igual que el export real: si se calcularan por línea, sumar
        # por canal sobrecontaría.
        tax = round(abs(subtotal) * 0.0775, 2) * (1 if subtotal >= 0 else -1)
        ship = round(abs(subtotal) * 0.02, 2) * (1 if subtotal >= 0 else -1)
        total = round(subtotal + tax + ship, 2)

        for sku, ptitle, ptype, qty, price, line_total in _weekly_order_lines(order):
            rows.append([
                f"demo-{num}-{sku.lower()}",
                submitted,
                submitted + timedelta(hours=2),
                submitted + timedelta(days=2),
                num, vendor,
                "External" if vendor else "Internal",
                "Paid", "Fulfilled", channel,
                "Web" if vendor == "Tock" else channel,
                "Ship" if state != "CA" else "Carry Out",
                "Tasting Room" if channel == "POS" else "",
                subtotal, ship, tax, total, total,
                title, package,
                first, last, f"{first.lower()}.{last.lower()}@example-demo.test",
                first, last, f"{100 + idx} Demo Vineyard Rd",
                city, state, zip_code, "US",
                "Demo Associate",
                ptitle, ptype, sku, float(qty), float(qty * 2), price, line_total, "Wine",
            ])

    order_report = out_dir / f"OrderReport_demo_{tag}.xlsx"
    pd.DataFrame(rows, columns=WEEKLY_ORDER_COLUMNS).to_excel(order_report, index=False)
    written["OrderReport"] = order_report
    _say(f"OrderReport         {order_report.name}  ({len(rows)} líneas de {len(WEEKLY_ORDERS)} órdenes)")

    # -------------------------------------------------------------- 2. Tock
    # Reservaciones y catas. El lector puede usar Net receivable (recomendado)
    # o Net sales; el demo trae las dos bases con valores distintos para que la
    # elección se note.
    tock_daily = [
        # fecha, bookings, gross, comps, discounts, net_sales, net_receivable
        (date(2026, 8, 17), 2, 250.00,  0.00,  0.00, 250.00, 236.25),
        (date(2026, 8, 18), 1, 125.00,  0.00,  0.00, 125.00, 118.13),
        (date(2026, 8, 19), 3, 375.00, 125.00,  0.00, 250.00, 236.25),
        (date(2026, 8, 20), 0,   0.00,   0.00,  0.00,   0.00,   0.00),
        (date(2026, 8, 21), 2, 300.00,   0.00, 50.00, 250.00, 236.25),
        (date(2026, 8, 22), 4, 500.00,   0.00,  0.00, 500.00, 472.50),
        (date(2026, 8, 23), 1, 125.00, 125.00,  0.00,   0.00,   0.00),
    ]
    tock_rows = []
    for d, bookings, gross, comps, disc, net_sales, net_rec in tock_daily:
        d = D(d)
        gross, comps, disc = S(gross), S(comps), S(disc)
        net_sales, net_rec = S(net_sales), S(net_rec)
        taxes = round(net_sales * 0.0775, 2)
        tock_rows.append([
            d, bookings, 0.0, 0.0, 0.0, gross, comps, disc, net_sales, 0.0,
            taxes, round(net_sales + taxes, 2), round(net_sales + taxes, 2),
            0.0, 0.0, round(net_rec * 0.02, 2), round(net_sales * 0.03, 2), net_rec,
        ])
    tock_file = out_dir / f"Tock_demo_{tag}.xlsx"
    pd.DataFrame(tock_rows, columns=[
        "Date", "Bookings", "Service charges", "Fees", "Retained payments",
        "Gross sales", "Comps", "Discounts", "Net sales", "Gratuities", "Taxes",
        "Gross receivable", "Credit card", "Third party gift card",
        "Outstanding payments", "Processing fees", "Tock fees", "Net receivable",
    ]).to_excel(tock_file, index=False)
    written["Tock"] = tock_file
    _say(f"Tock                {tock_file.name}  "
         f"(Net receivable ${sum(r[-1] for r in tock_rows):,.2f})")

    # ---------------------------------------------------------- 3. Open PO's
    # Cuentas por cobrar de distribución. El nombre del archivo DEBE contener
    # "open po": así lo busca el lector.
    po_rows = [
        # invoice, fecha, tipo, estado, cliente, id, tipo cliente, mercado,
        # país, vencimiento, aging, po/ref, total, balance, cases, notas
        ("DEM30011", date(2026, 8, 4),  "Invoice", "Open", "Northgate Beverage Co (Dallas)",   50211, "Wholesaler", "TX", "United States", date(2026, 9, 3),   8, 45601,  4200.00, 4200.00, 10, "Aging normal"),
        ("DEM30012", date(2026, 7, 21), "Invoice", "Open", "Coastline Wine & Spirits (Irvine)", 50212, "Wholesaler", "CA", "United States", date(2026, 8, 20), 22, 45602,  6750.00, 6750.00, 18, "Recordatorio enviado"),
        ("DEM30013", date(2026, 7, 2),  "Invoice", "Open", "Sunshine Fine Wine (Tampa)",        50213, "Wholesaler", "FL", "United States", date(2026, 8, 1),  41, 45603,  3900.00, 3900.00,  9, "VENCIDO: escalado a crédito"),
        ("DEM30014", date(2026, 8, 1),  "Invoice", "Open", "Hudson Cellar Room (Brooklyn)",     50214, "Retailer",   "NY", "United States", date(2026, 8, 31), 12, 45604,  1150.00, 1150.00,  3, ""),
        ("DEM30009", date(2026, 6, 15), "Invoice", "Paid", "Northgate Beverage Co (Houston)",   50209, "Wholesaler", "TX", "United States", date(2026, 7, 15),  0, 45599,  5600.00,    0.00, 14, "Pagado por transferencia"),
        ("DEM30010", date(2026, 6, 28), "Invoice", "Paid", "Lakeshore Distributing (Chicago)",  50210, "Wholesaler", "IL", "United States", date(2026, 7, 28),  0, 45600,  2240.00,    0.00,  6, "Pagado por cheque"),
    ]
    po_file = out_dir / f"Open-POs-demo-{tag}.xlsx"
    pd.DataFrame([
        [inv, D(fecha), tipo, estado, cli, cid, ctype, mkt, pais, D(due), aging,
         ref, S(total), S(bal), "--", "--", "No", cases, notas]
        for (inv, fecha, tipo, estado, cli, cid, ctype, mkt, pais, due, aging,
             ref, total, bal, cases, notas) in po_rows
    ], columns=[
        "Invoice #", "Invoice Date", "Type", "Status", "Customer", "Customer ID",
        "Customer Type", "Market", "Country", "Due Date", "Aging", "PO / REF #",
        "Total", "Balance", "Last Payment Date", "Delinquency Reporting Date",
        "On Delinquency List", "Total Cases", "Notes",
    ]).to_excel(po_file, index=False)
    written["Open POs"] = po_file
    _say(f"Open PO's           {po_file.name}  "
         f"({sum(1 for r in po_rows if r[3] == 'Open')} abiertas, "
         f"{sum(1 for r in po_rows if r[3] == 'Paid')} pagadas)")

    # ------------------------------------------------- 4. iDig Depletions
    # Encabezado de DOS pisos: fila 1 = mes (celdas combinadas -> el lector le
    # aplica ffill), fila 2 = medida. El lector arma el nombre de columna
    # concatenando ambas, salvo en las columnas de dimensión.
    months = [
        "Sep 2025", "Oct 2025", "Nov 2025", "Dec 2025", "Jan 2026", "Feb 2026",
        "Mar 2026", "Apr 2026", "May 2026", "Jun 2026", "Jul 2026", "Aug 2026",
    ]
    dims = ["Sites", "OnOff Premises", "Brands", "Item Names", "Item Name ID"]

    row0 = ["Supplier: DEMO WINERY ESTATE/PARK ST (datos sintéticos)"] + [None] * (len(dims) - 1 + len(months) * 2)
    row1 = [None] * len(dims)
    row2 = list(dims)
    for m in months:
        # Solo la primera de las dos celdas trae el mes: eso es una celda
        # combinada en el original y el lector lo resuelve con ffill.
        row1 += [f"1 Depletion Month {m}", None]
        row2 += [" Sales Depletions Decimal Cases", " Sales Depletions 9L Cases"]

    # Cajas 9L del mes más reciente por sitio. El nombre del sitio lleva el
    # estado, como en el archivo real, y un mismo estado viene partido en dos
    # regiones comerciales (CA-North/CA-South, NY-Metro/NY-Upstate) para que se
    # pueda comprobar que se consolidan.
    #
    # Los valores son deliberadamente DISTINTOS de los que antes estaban
    # escritos a mano en el procesador (CA 8.92 · FL 3.08 · IL 1.08 · NV 0.42 ·
    # NY 0.08): si el demo los repitiera, no se podría distinguir un desglose
    # derivado del archivo de uno que sigue viniendo del código.
    sites_aug = [
        ("Demo Distributor - CA-North",   "OFF", 5.10),
        ("Demo Distributor - CA-South",   "ON",  3.40),
        ("Demo Distributor - FL",         "OFF", 2.75),
        ("Demo Distributor - IL",         "ON",  1.20),
        ("Demo Distributor - NY-Metro",   "ON",  0.35),
        ("Demo Distributor - NY-Upstate", "OFF", 0.00),
        ("Demo Distributor - NV",         "OFF", 0.60),
    ]
    sites_aug = [(site, premise, round(v * scale, 2)) for site, premise, v in sites_aug]
    total_aug = round(sum(s[2] for s in sites_aug), 2)

    def measure_cells(aug_9l: float) -> list:
        """Doce meses de historia terminando en el valor de agosto. Los meses
        previos se derivan del mismo valor con una curva suave y determinista;
        cada mes trae cajas decimales (6 botellas) y cajas 9L."""
        cells = []
        for i, _m in enumerate(months):
            factor = 0.55 + 0.045 * i          # tendencia creciente suave
            nine_l = round(aug_9l * factor, 5) if _m != "Aug 2026" else round(aug_9l, 5)
            cells += [round(nine_l * 2, 5), nine_l]   # 1 caja 9L = 2 cajas de 6 botellas de 750 mL
        return cells

    dep_rows = [row0, row1, row2]
    dep_rows.append(["Total", "Total", "Total", "Total", "Total"] + measure_cells(total_aug))
    for site, premise, aug in sites_aug:
        dep_rows.append([site, "Total", "Total", "Total", "Total"] + measure_cells(aug))
        dep_rows.append([site, premise, "Demo Estate", "2023 Estate Cabernet Sauvignon 750ML",
                         "900001"] + measure_cells(aug))
    dep_rows.append([f"Report Created on {week_end.month}/{week_end.day}"])

    dep_file = out_dir / f"Idig-Depletions-demo-{tag}.xlsx"
    _write_sheet(dep_file, dep_rows)
    written["Depletions"] = dep_file
    _say(f"iDig Depletions     {dep_file.name}  "
         f"(Total ago-2026 {total_aug} cajas 9L en {len(sites_aug)} sitios)")

    return written


def build_sullivan_weekly_series(root: Path = SULLIVAN_WEEKLY_DIR,
                                 series: list | None = None) -> dict:
    """
    Genera VARIAS semanas, una por subcarpeta `Week_YYYY_MM_DD`.

    Es la forma que el reporte necesita para que el selector de semana del
    dashboard tenga algo que seleccionar. `discover_week_dirs` acepta las dos
    disposiciones —una carpeta que ES una semana, o una que las CONTIENE—, así
    que apuntar `--weekly-data-dir` a esta raíz o a una de sus subcarpetas
    funciona igual.
    """
    series = series or WEEKLY_SERIES
    written = {}
    for week_start, scale, tag in series:
        week_end = week_start + timedelta(days=6)
        sub = root / f"Week_{week_end:%Y_%m_%d}"
        _say(f"--- semana que cierra {week_end:%Y-%m-%d}  (escala {scale:.2f}) ---")
        written[sub.name] = build_sullivan_weekly(sub, week_start=week_start,
                                                 scale=scale, tag=tag)
    _say(f"{len(series)} semanas en {root.name}/ -> el dashboard trae selector de semana y WoW real.")
    return written


# ==============================================================================
# 2. LOCO TEQUILA USA
# ==============================================================================

# Catálogo demo. La categoría es la que `categorize_product()` deduce del
# nombre; se documenta aquí para que el demo sea legible.
#   (item_id, nombre, categoría esperada, botellas por caja)
LOCO_PRODUCTS = [
    ("900101", "DEMO BLANCO TEQUILA 750ML",              "Blanco",                       6),
    ("900102", "DEMO REPOSADO AMBAR 80 750ML",           "Ambar",                        6),
    ("900103", "DEMO BLANCO PURO CORAZON 80 750ML",      "Puro Corazon",                 6),
    ("900104", "DEMO AUREO ANEJO 750ML",                 "Aureo",                        6),
    ("900105", "DEMO BLANCO TEQUILA 200ML",              "Blanco 200mL",                24),
    ("900106", "DEMO LTD ETN ALEBRIJE PURO COYOTE 750ML", "Limited Edition Alebrije",     6),
    # Muestras: NO son inventario comercial. Deben salir del total y
    # reportarse aparte (por esto el total del libro no cuadraba antes).
    ("900107", "DEMO BLANCO 750ML NSS NOT SELLABLE - SAMPLES ONLY",
     "NOT SELLABLE - SAMPLES ONLY", 6),
]

LOCO_ACCOUNTS_CA = [
    ("MERIDIAN CHEESE SHOP",   "OCEAN & 5TH AVE",        "CARMEL",        "270101"),
    ("BOTTEGA TRATTORIA",      "6525 VINE ST STE A9",    "YOUNTVILLE",    "270102"),
    ("HOLLISTER FINE LIQUORS", "310 FIRST ST",           "HOLLISTER",     "270103"),
    ("EMBARCADERO WINE BAR",   "88 PIER WALK",           "SAN FRANCISCO", "270104"),
    ("PALISADE MARKET",        "1420 SUNSET BLVD",       "SANTA MONICA",  "270105"),
]

LOCO_ACCOUNTS_TX = [
    ("LONE STAR SPIRITS #091", "8830 CLAY ROAD",         "HOUSTON",  "TX", "77080", "LONE STAR WHSE", "OFF", "DEMO REP NORTE"),
    ("TWIN OAKS LIQUORS #108", "148 EL DORADO BLVD",     "WEBSTER",  "TX", "77598", "TWIN OAKS",      "OFF", "DEMO REP SUR"),
    ("BAYOU CANTINA & GRILL",  "2200 RIVER OAKS LN",     "HOUSTON",  "TX", "77019", "INDEPENDIENTE",  "ON",  "DEMO REP NORTE"),
    ("HILL COUNTRY TAVERN",    "915 CONGRESS AVE",       "AUSTIN",   "TX", "78701", "INDEPENDIENTE",  "ON",  "DEMO REP SUR"),
]

MONTHS_YTD = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug"]


def build_loco(out_dir: Path = LOCO_DIR) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    written = {}

    # ------------------------------------- 1. Supplier Inventory (Texas / FB)
    # Layout disperso real: título en r0, tres filas vacías, encabezado en r4
    # con las columnas en posiciones no contiguas. El lector localiza el
    # encabezado buscando la celda "ITEM #", así que las posiciones exactas no
    # importan, pero se respetan para que el demo sirva de referencia visual.
    warehouses = ["MCA", "HAR", "LAR", "CC", "EP", "ROS", "ABQ", "AUS", "HOU", "DAL"]
    hdr = [None] * 21
    hdr[1], hdr[4], hdr[7], hdr[9] = "ITEM #", "Product", "Supplier", "Pack"
    for i, w in enumerate(warehouses):
        hdr[10 + i] = w
    hdr[20] = "Total"

    # Botellas por bodega TX. Se reparte a mano para que el total sea legible.
    tx_bottles = {
        "900101": [0, 0, 0, 0, 28, 0, 0, 42, 42, 14],
        "900102": [0, 0, 0, 0, 12, 0, 0, 18, 24, 6],
        "900103": [0, 0, 0, 0, 6, 0, 0, 12, 12, 6],
        "900104": [0, 0, 0, 0, 0, 0, 0, 6, 6, 0],
        "900105": [0, 0, 0, 0, 0, 0, 0, 24, 0, 0],
        "900106": [0, 0, 0, 0, 0, 0, 0, 0, 6, 0],
        "900107": [0, 0, 0, 0, 0, 0, 0, 6, 6, 0],
    }
    inv_rows = [
        [None, None, None, "FB - Inventory (datos sintéticos)"],
        [], [], [],
        hdr,
    ]
    for item_id, name, _cat, pack in LOCO_PRODUCTS:
        per_wh = tx_bottles[item_id]
        row = [None] * 21
        row[1], row[4], row[7], row[9] = item_id, name, "PARK ST / DEMO USA LLC", pack
        for i, v in enumerate(per_wh):
            row[10 + i] = v
        row[20] = sum(per_wh)
        inv_rows.append(row)

    supplier_inv = out_dir / "1-Supplier-Inventory-demo.xlsx"
    _write_sheet(supplier_inv, inv_rows)
    written["Supplier Inventory (TX)"] = supplier_inv
    _say(f"Supplier Inventory  {supplier_inv.name}  "
         f"({sum(sum(v) for v in tx_bottles.values())} botellas en TX)")

    # ---------------------------- 2. Inventory History (California / SGWS)
    # Jerarquía por sitio -> planta -> producto, en cajas decimales de 6
    # botellas. Solo las hojas (leaf) se suman: las filas 'Total' son
    # subtotales del propio archivo y sumarlas duplicaría el inventario.
    sig_hdr = ["Sites", "Plants", "Item Names", "Item Name ID",
               " On Hand Decimal  Cases", " Receipts Decimal Cases",
               " On Order Decimal Cases"]
    # (sitio, planta, item_id, cajas de 6 botellas)
    sig_leaves = [
        ("Demo Distributor - CA-North", "NCA", "900101", 15.33333),
        ("Demo Distributor - CA-North", "NCA", "900102", 14.66667),
        ("Demo Distributor - CA-North", "NCA", "900103", 11.83333),
        ("Demo Distributor - CA-South", "SCA", "900101", 22.50000),
        ("Demo Distributor - CA-South", "SCA", "900103",  9.16667),
        ("Demo Distributor - CA-South", "SCA", "900104",  6.33333),
        ("Demo Distributor - CA-South", "SCA", "900106",  3.50000),
    ]
    name_by_id = {p[0]: p[1] for p in LOCO_PRODUCTS}

    sig_rows = [
        ["Supplier: DEMO USA LLC/PARK ST (datos sintéticos)"],
        ["", "", "", "", "1 Depletion Month Aug 2026", "1 Depletion Month Aug 2026",
         "1 Depletion Month Aug 2026"],
        ["", "", "", "", "No Filters Selected", "No Filters Selected", "No Filters Selected"],
        sig_hdr,
    ]
    grand = round(sum(l[3] for l in sig_leaves), 5)
    sig_rows.append(["Total", "Total", "Total", "Total", grand, 0, 0])
    for site in ("Demo Distributor - CA-North", "Demo Distributor - CA-South"):
        site_leaves = [l for l in sig_leaves if l[0] == site]
        site_total = round(sum(l[3] for l in site_leaves), 5)
        plant = site_leaves[0][1]
        sig_rows.append([site, "Total", "Total", "Total", site_total, 0, 0])
        sig_rows.append([site, plant, "Total", "Total", site_total, 0, 0])
        for _s, pl, item_id, cases in site_leaves:
            sig_rows.append([site, pl, name_by_id[item_id], item_id, cases, 0, 0])

    inv_hist = out_dir / "Inventory-History-demo.xlsx"
    _write_sheet(inv_hist, sig_rows)
    written["Inventory History (CA)"] = inv_hist
    _say(f"Inventory History   {inv_hist.name}  "
         f"({grand} cajas de 6 botellas = {round(grand * 0.5, 2)} cajas 9L)")

    # -------------------------- 3. YTD by Month (depletions California, SGWS)
    ytd_hdr = ["Retail Accounts", "Address", "City", "Account #", "Item Names",
               "Item Name ID", "Invoice Dates"]
    ytd_hdr += [f"1 Depletion Month {m} 2026  Bottles" for m in MONTHS_YTD]
    ytd_hdr += ["1 Depletion Year Jan 2026 thru Aug 2026  Bottles",
                "1 Depletion Year Jan 2026 thru Aug 2026  Sales Depletions 9L Cases",
                "1 Depletion Year Jan 2026 thru Aug 2026  # Purchases"]

    ytd_rows = [ytd_hdr]
    # Cada cuenta compra 1-2 SKU. Las botellas por mes suben suavemente; el
    # acumulado y las cajas 9L se DERIVAN de esos meses, nunca se teclean
    # aparte: si se teclearan, el archivo demo podría no cuadrar consigo mismo.
    for a_i, (acct, addr, city, acct_no) in enumerate(LOCO_ACCOUNTS_CA):
        for s_i in range(1 + (a_i % 2)):
            item_id, item_name, _c, _p = LOCO_PRODUCTS[(a_i + s_i) % 4]
            per_month = [float(max(0, 2 + a_i + s_i * 3 + m_i - 4) * 6)
                         for m_i in range(len(MONTHS_YTD))]
            ytd_bottles = round(sum(per_month), 2)
            ytd_9l = round(ytd_bottles * 750.0 / 9000.0, 5)
            invoice = date(2026, 8, 20 - a_i)
            ytd_rows.append(
                [acct, addr, city, float(acct_no), item_name, float(item_id), invoice]
                + per_month + [ytd_bottles, ytd_9l, float(len([p for p in per_month if p]))]
            )

    ytd_file = out_dir / "YTD-by-Month-Bottles-Orders-demo.xlsx"
    _write_sheet(ytd_file, ytd_rows)
    ca_bottles = sum(r[-3] for r in ytd_rows[1:])
    written["YTD by Month (CA)"] = ytd_file
    _say(f"YTD by Month        {ytd_file.name}  "
         f"({len(ytd_rows) - 1} filas, {ca_bottles:,.0f} botellas YTD en CA)")

    # --------------------------- 4. InventoryByLocation (Park Street, CSV)
    ps_inv_header = ["location_grp", "product_id", "brand", "sub_brand",
                     "sub_brand_product_name", "description", "client_name",
                     "location", "supplier_name", "onhand"]
    ps_inv_rows = [
        ["Warehouse", "DEMO-BLANCO-750", "Demo Tequila", "Blanco",
         "Demo Blanco Tequila 750mL/6", "Blanco 750", "DEMO USA LLC",
         "CA-Benicia", "Park Street", "96"],
        ["Warehouse", "DEMO-AMBAR-750", "Demo Tequila", "Ambar",
         "Demo Reposado Ambar 750mL/6", "Ambar 750", "DEMO USA LLC",
         "CA-Benicia", "Park Street", "48"],
        ["Warehouse", "DEMO-CORAZON-750", "Demo Tequila", "Puro Corazon",
         "Demo Blanco Puro Corazon 750mL/6", "Corazon 750", "DEMO USA LLC",
         "CA-Benicia", "Park Street", "30"],
        # 200 mL: 24 botellas por caja, no 6 -> el factor a caja 9L es distinto.
        ["Warehouse", "DEMO-BLANCO-200", "Demo Tequila", "Blanco 200",
         "Demo Blanco Tequila 200mL/24", "Blanco 200", "DEMO USA LLC",
         "CA-Benicia", "Park Street", "18"],
        # Muestras: el sufijo NSS vive en product_id, NO en el nombre comercial
        # (el nombre es idéntico al de la versión vendible). Si se clasificara
        # solo por nombre, estas cajas se colarían al inventario comercial.
        ["Warehouse", "DEMO-BLANCO-750NSS", "Demo Tequila", "Blanco",
         "Demo Blanco Tequila 750mL/6", "Muestras", "DEMO USA LLC",
         "CA-Benicia", "Park Street", "12"],
        # Empaque con prefijo Z-: no es producto, se excluye.
        ["Warehouse", "Z-GIFTBOX-750", "Demo Tequila", "Packaging",
         "Value Added Packaging Gift Box", "Caja de regalo", "DEMO USA LLC",
         "CA-Benicia", "Park Street", "240"],
        # Inventario que carga un vendedor en su vehículo.
        ["Salesperson Inventory", "DEMO-BLANCO-750", "Demo Tequila", "Blanco",
         "Demo Blanco Tequila 750mL/6", "Blanco 750", "DEMO USA LLC",
         "CA-Mark", "Park Street", "12"],
        ["Salesperson Inventory", "DEMO-AMBAR-750", "Demo Tequila", "Ambar",
         "Demo Reposado Ambar 750mL/6", "Ambar 750", "DEMO USA LLC",
         "CA-Jacky", "Park Street", "6"],
    ]
    ps_inv_file = out_dir / "InventoryByLocation-demo.csv"
    _write_csv(ps_inv_file, ps_inv_header, ps_inv_rows)
    written["InventoryByLocation (Park St)"] = ps_inv_file
    _say(f"InventoryByLocation {ps_inv_file.name}  ({len(ps_inv_rows)} filas)")

    # ------------------------- 5. SalesOrdersSummary (Park Street, CSV)
    # OJO: `Total` es el importe de la LÍNEA y `Total Value` el de la ORDEN
    # completa repetido en cada línea. El lector suma `Total`; sumar
    # `Total Value` contaría el mismo pedido varias veces. El demo trae órdenes
    # de varias líneas precisamente para que ese error se pueda detectar.
    ps_ord_header = ["Unique Order ID", "Order #", "Order Status", "Date Posted",
                     "PO / REF #", "Customer", "Customer ID", "Customer Type",
                     "Market", "Total Cases", "Total Value", "Shipment Status",
                     "Shipment Date", "Brand", "Product Code", "Product Description",
                     "Supplier Reference ID", "Location Group", "Location", "Qty",
                     "Unit", "Unit Price", "Total", "Notes"]

    # (orden, fecha, cliente, tipo, mercado, [(product_code, desc, qty, unit, unit_price)])
    ps_orders = [
        (7001, date(2026, 7, 8), "Coastline Wine & Spirits", "Wholesaler", "CA", [
            ("DEMO-BLANCO-750", "Demo Blanco Tequila 750mL/6", 40, "Cases", 132.00),
            ("DEMO-AMBAR-750", "Demo Reposado Ambar 750mL/6", 15, "Cases", 156.00),
        ]),
        (7002, date(2026, 7, 22), "Northgate Beverage Co", "Wholesaler", "TX", [
            ("DEMO-BLANCO-750", "Demo Blanco Tequila 750mL/6", 25, "Cases", 132.00),
            ("DEMO-CORAZON-750", "Demo Blanco Puro Corazon 750mL/6", 10, "Cases", 198.00),
        ]),
        (7003, date(2026, 8, 5), "Lakeshore Distributing", "Wholesaler", "IL", [
            ("DEMO-BLANCO-750", "Demo Blanco Tequila 750mL/6", 18, "Cases", 132.00),
        ]),
        (7004, date(2026, 8, 12), "Meridian Cheese Shop", "Retailer", "CA", [
            ("DEMO-BLANCO-750", "Demo Blanco Tequila 750mL/6", 12, "Bottles", 27.00),
            ("DEMO-CORAZON-750", "Demo Blanco Puro Corazon 750mL/6", 6, "Bottles", 39.00),
        ]),
        (7005, date(2026, 8, 14), "Embarcadero Wine Bar", "Retailer", "CA", [
            ("DEMO-AMBAR-750", "Demo Reposado Ambar 750mL/6", 6, "Bottles", 32.00),
        ]),
        (7006, date(2026, 8, 18), "Palisade Market", "Retailer", "CA", [
            ("DEMO-BLANCO-200", "Demo Blanco Tequila 200mL/24", 24, "Bottles", 9.50),
        ]),
        # Cliente tipo "Salesperson": salidas de inventario de vendedor. Se usan
        # para la serie semanal por vendedor, no como venta a cuenta.
        (7007, date(2026, 8, 3), "Mark Demo - Salesperson Inventory", "Salesperson", "CA", [
            ("DEMO-BLANCO-750", "Demo Blanco Tequila 750mL/6", 3, "Cases", 0.00),
        ]),
        (7008, date(2026, 8, 10), "Jacky Demo - Salesperson Inventory", "Salesperson", "CA", [
            ("DEMO-AMBAR-750", "Demo Reposado Ambar 750mL/6", 12, "Bottles", 0.00),
        ]),
        (7009, date(2026, 8, 17), "Joe Pat Demo - Salesperson Inventory", "Salesperson", "TX", [
            ("DEMO-CORAZON-750", "Demo Blanco Puro Corazon 750mL/6", 2, "Cases", 0.00),
        ]),
    ]
    ps_ord_rows = []
    for onum, posted, cust, ctype, market, lines in ps_orders:
        order_value = round(sum(q * p for _c, _d, q, _u, p in lines), 2)
        total_cases = sum(q for _c, _d, q, u, _p in lines if u == "Cases")
        for code, desc, qty, unit, unit_price in lines:
            ps_ord_rows.append([
                f"DEMO-{onum}", onum, "Posted", posted.strftime("%m/%d/%y"),
                f"REF{onum}", cust, 50000 + onum, ctype, market, total_cases,
                f"${order_value:,.2f}", "Shipped",
                (posted + timedelta(days=3)).strftime("%m/%d/%y"), "Demo Tequila",
                code, desc, f"SUP{onum}", "Warehouse", f"{market}-Benicia",
                qty, unit, f"${unit_price:,.2f}", f"${qty * unit_price:,.2f}", "",
            ])
    ps_ord_file = out_dir / "SalesOrdersSummary-demo.csv"
    _write_csv(ps_ord_file, ps_ord_header, ps_ord_rows)
    written["SalesOrdersSummary (Park St)"] = ps_ord_file
    _say(f"SalesOrdersSummary  {ps_ord_file.name}  "
         f"({len(ps_ord_rows)} líneas en {len(ps_orders)} órdenes)")

    # ------------------------------ 6/7. Ecommerce (Shopify y Memory, CSV)
    # Se escribe el ancho completo del export de Shopify (79 columnas) para que
    # el demo sirva también de referencia de formato; solo se llenan las que
    # el lector usa más algunas de contexto.
    shopify_cols = [
        "Name", "Email", "Financial Status", "Paid at", "Fulfillment Status",
        "Fulfilled at", "Accepts Marketing", "Currency", "Subtotal", "Shipping",
        "Taxes", "Total", "Discount Code", "Discount Amount", "Shipping Method",
        "Created at", "Lineitem quantity", "Lineitem name", "Lineitem price",
        "Lineitem compare at price", "Lineitem sku", "Lineitem requires shipping",
        "Lineitem taxable", "Lineitem fulfillment status", "Billing Name",
        "Billing Street", "Billing Address1", "Billing Address2", "Billing Company",
        "Billing City", "Billing Zip", "Billing Province", "Billing Country",
        "Billing Phone", "Shipping Name", "Shipping Street", "Shipping Address1",
        "Shipping Address2", "Shipping Company", "Shipping City", "Shipping Zip",
        "Shipping Province", "Shipping Country", "Shipping Phone", "Notes",
        "Note Attributes", "Cancelled at", "Payment Method", "Payment Reference",
        "Refunded Amount", "Vendor", "Outstanding Balance", "Employee", "Location",
        "Device ID", "Id", "Tags", "Risk Level", "Source", "Lineitem discount",
        "Tax 1 Name", "Tax 1 Value", "Tax 2 Name", "Tax 2 Value", "Tax 3 Name",
        "Tax 3 Value", "Tax 4 Name", "Tax 4 Value", "Tax 5 Name", "Tax 5 Value",
        "Phone", "Receipt Number", "Duties", "Billing Province Name",
        "Shipping Province Name", "Payment ID", "Payment Terms Name",
        "Next Payment Due At", "Payment References",
    ]
    idx = {c: i for i, c in enumerate(shopify_cols)}

    def ecom_rows(spec: list) -> list:
        """spec: (orden, fecha, nombre_producto, qty, precio, tag, empleado)."""
        out = []
        for order_name, created, item, qty, price, tag, employee in spec:
            row = [""] * len(shopify_cols)
            row[idx["Name"]] = order_name
            row[idx["Email"]] = f"{order_name.lower().strip('#')}@example-demo.test"
            row[idx["Financial Status"]] = "paid"
            row[idx["Currency"]] = "USD"
            row[idx["Created at"]] = f"{created:%Y-%m-%d} 12:00:00 -0700"
            row[idx["Lineitem quantity"]] = str(qty)
            row[idx["Lineitem name"]] = item
            row[idx["Lineitem price"]] = f"{price:.2f}"
            row[idx["Lineitem sku"]] = item.split()[1][:6].upper()
            row[idx["Subtotal"]] = f"{qty * price:.2f}"
            row[idx["Total"]] = f"{qty * price:.2f}"
            row[idx["Tags"]] = tag
            row[idx["Employee"]] = employee
            row[idx["Source"]] = "web"
            out.append(row)
        return out

    # Shopify SIN tag = Ecommerce puro; CON tag = DTC atribuido a un vendedor.
    shopify_spec = [
        ("#D1001", date(2026, 7, 6),  "Demo Blanco Tequila 750mL", 2, 44.00, "",             ""),
        ("#D1002", date(2026, 7, 14), "Demo Reposado Ambar 750mL", 1, 52.00, "",             ""),
        ("#D1003", date(2026, 7, 28), "Demo Blanco Puro Corazon 750mL", 3, 64.00, "",        ""),
        ("#D1004", date(2026, 8, 4),  "Demo Blanco Tequila 750mL", 6, 44.00, "mark-demo",    "Mark Demo"),
        ("#D1005", date(2026, 8, 11), "Demo Aureo Anejo 750mL",    2, 88.00, "jacky-demo",   "Jacky Demo"),
        ("#D1006", date(2026, 8, 19), "Demo Blanco Tequila 200mL", 12, 12.00, "",            ""),
    ]
    # Memory = venta en evento con recolección en sitio: se atribuye a DTC
    # completa, con tag o sin él.
    memory_spec = [
        ("#M2001", date(2026, 7, 18), "Demo Blanco Tequila 750mL", 12, 40.00, "manuel-demo", "Manuel Demo"),
        ("#M2002", date(2026, 8, 8),  "Demo Reposado Ambar 750mL",  6, 48.00, "",            "Manuel Demo"),
        ("#M2003", date(2026, 8, 22), "Demo Ltd Etn Alebrije Puro Coyote 750mL", 3, 120.00, "joe pat-demo", "Joe Pat Demo"),
    ]
    shop_file = out_dir / "orders_export_1-demo-shopify.csv"
    mem_file = out_dir / "orders_export_1-demo-memory.csv"
    _write_csv(shop_file, shopify_cols, ecom_rows(shopify_spec))
    _write_csv(mem_file, shopify_cols, ecom_rows(memory_spec))
    written["Ecommerce (Shopify)"] = shop_file
    written["Ecommerce (Memory)"] = mem_file
    _say(f"Ecommerce           {shop_file.name} ({len(shopify_spec)}) + "
         f"{mem_file.name} ({len(memory_spec)})")

    # -------------------------- 8. FB Depletion Reports (Texas, subcarpeta)
    # El nombre de la subcarpeta y el patrón de fecha del archivo NO son
    # libres: el lector busca la carpeta por nombre literal y elige el archivo
    # más reciente parseando la fecha del nombre.
    fb_dir = out_dir / LOCO_FB_SUBDIR
    fb_dir.mkdir(parents=True, exist_ok=True)

    fb_hdr = [None] * 38
    for pos, label in [(2, "COMPANY"), (3, "LOCATION"), (6, "CUST ID"),
                       (7, "CUSTOMER"), (11, "ADDRESS"), (12, "CITY"),
                       (13, "STATE"), (14, "ZIP"), (15, "CHAIN"), (16, "PREMISE"),
                       (17, "SALES REP"), (18, "ITEM "), (19, "PRODUCT"),
                       (20, "VENDOR"), (21, "SUBITEM"), (22, "TYPE"), (23, "PACK")]:
        fb_hdr[pos] = label
    month_names = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
                   "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
    for i, m in enumerate(month_names):
        fb_hdr[24 + i] = m
    fb_hdr[36] = "TOTAL"
    fb_hdr[37] = ""

    fb_rows = [
        [None] * 5 + ["FB - Depletions (datos sintéticos)"],
        [],
        fb_hdr,
    ]
    for a_i, (cust, addr, city, st, zc, chain, premise, rep) in enumerate(LOCO_ACCOUNTS_TX):
        for s_i in range(1 + (a_i % 2)):
            item_id, item_name, _c, pack = LOCO_PRODUCTS[(a_i + s_i) % 4]
            row = [None] * 38
            for pos, val in [(2, "demo"), (3, city.title()), (6, 840000 + a_i * 10 + s_i),
                             (7, cust), (11, addr), (12, city), (13, st), (14, zc),
                             (15, chain), (16, premise), (17, rep), (18, item_id),
                             (19, item_name), (20, "PARK ST"), (21, item_id),
                             (22, "TEQUILA"), (23, pack)]:
                row[pos] = val
            # Solo ene..ago tienen movimiento (el año va a la mitad); sep..dic en
            # cero, igual que el snapshot real de agosto.
            per_month = [float(max(0, 6 + a_i * 3 + s_i * 6 + m_i * 3 - 6))
                         for m_i in range(len(MONTHS_YTD))]
            for i, v in enumerate(per_month):
                row[24 + i] = v
            for i in range(len(MONTHS_YTD), 12):
                row[24 + i] = 0.0
            row[36] = round(sum(per_month), 2)
            fb_rows.append(row)

    fb_file = fb_dir / "1-Depletion-By-Month-2026-08-24.xlsx"
    _write_sheet(fb_file, fb_rows)
    tx_bottles_ytd = sum(r[36] for r in fb_rows[3:])
    written["FB Depletions (TX)"] = fb_file
    _say(f"FB Depletions       {LOCO_FB_SUBDIR}/{fb_file.name}  "
         f"({len(fb_rows) - 3} filas, {tx_bottles_ytd:,.0f} botellas YTD en TX)")

    return written


# ==============================================================================
# 3. SULLIVAN — CADENCIA MENSUAL (delega en el simulador que ya existía)
# ==============================================================================

def build_sullivan_monthly(out_dir: Path = SULLIVAN_MONTHLY_DIR) -> dict:
    """El mensual ya tenía su propio simulador (`sullivan_c7_simulator.py`),
    con las proporciones de canal/club ancladas a los agregados reales. Aquí
    solo se le indica dónde escribir, para no duplicar esa lógica."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import sullivan_c7_simulator as sim

    cfg = dict(sim.CONFIG)
    cfg["output_dir"] = str(out_dir)
    files = sim.run(cfg)
    return {name: out_dir / name for name in files}


# ==============================================================================
# 4. MAIN
# ==============================================================================

BUILDERS = {
    "sullivan_monthly": ("Sullivan — mensual (Commerce7)", build_sullivan_monthly),
    "sullivan_weekly": ("Sullivan — semanal, serie de 4 semanas (C7 + Tock + Park St + iDig)",
                        build_sullivan_weekly_series),
    "loco": ("Loco Tequila USA (FB + SGWS + Park St + ecommerce)", build_loco),
}


def main(argv=None) -> int:
    import argparse

    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError, OSError):
            pass

    ap = argparse.ArgumentParser(
        description="Genera los datos demo sintéticos de cada reporte.")
    ap.add_argument("--brand", choices=["all", *BUILDERS], default="all",
                    help="Juego de datos a generar (por defecto: todos).")
    args = ap.parse_args(argv)

    selected = list(BUILDERS) if args.brand == "all" else [args.brand]
    for key in selected:
        label, builder = BUILDERS[key]
        print(f"\n{label}")
        print("-" * len(label))
        builder()

    print("\nDatos demo listos en Data_for_demo/.")
    print("Sttupa no tiene demo: todavía no hay ningún archivo real del cliente "
          "en el que basar la estructura, y un demo inventado de punta a punta "
          "enseñaría un formato que después no coincidiría con el real.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
