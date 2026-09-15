"""
================================================================================
 SULLIVAN RUTHERFORD ESTATE — PROCESADOR DE DATOS SEMANALES
================================================================================
 Ingesta y normaliza los 7 reportes de la cadencia semanal:
   1. OrderReport: Ventas transaccionales C7 (8 canales no-Tock).
   2. Tock: Ventas de reservaciones y catas (Net Receivable / Net Sales).
   3. SalesbyChannel: Validación cruzada de canales C7.
   4. SalesbyClub: Desglose de membresías (Estate vs Founder's vs Review).
   5. SalesbyTag: Desglose de eventos, corporativo y Friends & Family.
   6. Open PO's: Cuentas por cobrar y antigüedad de órdenes de distribución (Park Street).
   7. Idig Depletions: Cajas de 9L agotadas en distribución (Southern Glazer's).
================================================================================
"""

import re
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

# Mismo nombre de categoría que el reporte mensual, para que el lector vea la
# misma etiqueta en las dos cadencias (decisión de negocio del cliente,
# 2026-09-02): todo lo que la cascada no puede asignar va aquí, visible y sumado.
UNCLASSIFIED = "Unclassified"

# Marca de dato ausente, igual que en los generadores mensuales. Nunca debe
# imprimirse "nan"/"NaT"/"None": son artefactos de pandas, no información.
BLANK = "—"
_MISSING = {"nan", "nat", "none", "null", "undefined", "<na>", ""}


def blank_if_missing(value, blank: str = BLANK) -> str:
    """Texto listo para imprimir; cualquier forma de 'ausente' se vuelve `blank`."""
    if value is None:
        return blank
    try:
        if pd.isna(value):
            return blank
    except (TypeError, ValueError):
        pass
    text = str(value).strip()
    return blank if text.lower() in _MISSING else text


def warn(msg: str) -> None:
    """Aviso visible: un reporte armado con supuestos silenciosos es peor que
    uno que falla."""
    print(f"  [AVISO] {msg}", file=sys.stderr)


# Códigos USPS válidos, para reconocer el estado dentro del nombre del sitio de
# distribución (ej. "Southern Glazer's - CA-North" -> "CA").
US_STATE_CODES = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "DC", "FL", "GA", "HI",
    "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN",
    "MS", "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH",
    "OK", "OR", "PA", "PR", "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA",
    "WA", "WV", "WI", "WY",
}

# Mercados en los que el cliente vende pero cuyo distribuidor NO manda feed de
# sell-through, así que nunca aparecerán en el iDig de Southern Glazer's. Se
# listan explícitamente (con 0 y marcados como "no live") para que no se lean
# como mercados inexistentes: TX lo atiende Favorite Brands, que hoy no reporta
# depletions. Es la única parte de este bloque que NO sale del archivo.
MARKETS_WITHOUT_SELL_THROUGH_FEED = ("TX", "PR")


def weekly_output_name(result: Dict[str, Any], prefix: str = "sullivan_weekly_dashboard",
                       suffix: str = ".html") -> str:
    """
    Nombre de archivo derivado de la semana que se procesó.

    ANTES el orquestador escribía siempre `sullivan_weekly_dashboard_aug_23_2026
    .html`: procesar dos semanas distintas sobreescribía el mismo archivo y el
    usuario se quedaba con un reporte cuyo nombre contradecía su contenido.
    """
    closing = result.get("date_closing")
    if closing:
        return f"{prefix}_{str(closing).replace('-', '_')}{suffix}"
    return f"{prefix}_sin_fecha{suffix}"


def state_from_site(site_name: str) -> str:
    """
    Extrae el código de estado del nombre del sitio de distribución.

    El iDig nombra los sitios como "<Distribuidor> - <ESTADO>[-<Región>]", y un
    mismo estado puede venir partido en varias regiones comerciales
    ("CA-North" y "CA-South", "NY-Metro" y "NY-Upstate"). Consolidarlas por
    estado es lo que espera el mapa del reporte: el cliente razona por estado,
    no por región interna del distribuidor.

    Devuelve "" si no se reconoce ningún estado, para que la fila se pueda
    reportar como no atribuida en vez de asignarse a un estado equivocado.
    """
    text = str(site_name or "")
    tail = text.split(" - ")[-1] if " - " in text else text
    for token in re.split(r"[^A-Za-z]+", tail):
        code = token.upper()
        if code in US_STATE_CODES:
            return code
    return ""


#  Varias semanas
#  ---------------------------------------------------------------------------
#  El reporte semanal nació atado a UNA carpeta, y el dashboard traía un
#  `<select>` con una sola opción fija y sin comportamiento: el filtro se veía,
#  pero no filtraba nada porque no había nada más que mostrar. En cuanto el
#  cliente entrega más semanas, lo que hace falta es descubrirlas todas y poder
#  cambiar entre ellas. De paso el WoW y la línea de tendencia dejan de ser
#  marcadores de posición.

# Los 4 insumos que definen una carpeta como "una semana". Se buscan por
# palabra clave, igual que en `find_file`, y sin puntuación para que valgan
# tanto `Open PO's 8.23.26.xlsx` como `Open-POs-demo-8.23.26.xlsx`.
WEEKLY_REQUIRED_KEYWORDS = ("orderreport", "tock", "open po", "depletion")


def _looks_like_week_dir(path: Path) -> bool:
    """True si la carpeta contiene los 4 insumos de una semana."""
    if not path.is_dir():
        return False
    flat = [re.sub(r"[^a-z0-9]", "", f.name.lower())
            for f in path.iterdir()
            if f.is_file() and f.suffix.lower() in (".xlsx", ".xls", ".csv")]
    if not flat:
        return False
    for kw in WEEKLY_REQUIRED_KEYWORDS:
        needle = re.sub(r"[^a-z0-9]", "", kw.lower())
        if not any(needle in name for name in flat):
            return False
    return True


def discover_week_dirs(root: Path) -> List[Path]:
    """
    Devuelve las carpetas de semana que hay bajo `root`, ordenadas por nombre.

    Acepta las dos formas sin que el usuario tenga que declarar cuál usa:

    * `root` ES una semana (contiene los 4 archivos). Es el caso de
      `Data_for_demo/Sullivan_weekly_demo` y el de quien apunta `--weekly-data-dir`
      directamente a una semana. Devuelve `[root]`.
    * `root` es el CONTENEDOR de semanas (`Client_Data/Sullivan_data/Weekly/`,
      con `Week_2026_08_23/`, `Week_2026_08_16/`, ...). Devuelve las subcarpetas
      que califican.

    Si no encuentra ninguna, devuelve lista vacía y deja que el llamador decida
    el mensaje: aquí no se adivina.
    """
    root = Path(root)
    if not root.exists():
        return []
    if _looks_like_week_dir(root):
        return [root]
    subs = sorted((p for p in root.iterdir() if _looks_like_week_dir(p)),
                  key=lambda p: p.name)
    return subs


def attach_wow(weeks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Ordena las semanas por fecha de corte y calcula el cambio porcentual de
    cada una contra la INMEDIATA ANTERIOR de la serie.

    La primera semana se queda en `None`, no en 0.0: no tiene contra qué
    compararse, y un 0% afirmaría que no cambió. Si la semana previa cerró en
    $0.00 también queda `None`, porque el porcentaje no está definido.
    """
    ordered = sorted(weeks, key=lambda w: str(w.get("date_closing") or ""))
    for i, wk in enumerate(ordered):
        if i == 0:
            wk["kpis"]["wow_pct_change"] = None
            wk["prev_week_label"] = None
            wk["prev_total_dtc"] = None
            continue
        prev = ordered[i - 1]
        prev_total = prev["kpis"].get("total_dtc_sales")
        cur_total = wk["kpis"].get("total_dtc_sales")
        wk["prev_week_label"] = prev.get("week_label")
        wk["prev_total_dtc"] = prev_total
        if prev_total in (None, 0) or cur_total is None:
            wk["kpis"]["wow_pct_change"] = None
        else:
            wk["kpis"]["wow_pct_change"] = round(
                (cur_total - prev_total) / prev_total * 100.0, 1)
    return ordered


def process_sullivan_weekly_series(root: Path,
                                   tock_basis: str = "net_receivable"
                                   ) -> List[Dict[str, Any]]:
    """
    Procesa TODAS las semanas que haya bajo `root` y devuelve la serie ordenada
    de la más antigua a la más reciente, con el WoW ya calculado.

    Una semana que truene no tumba las demás: se avisa y se sigue. Perder una
    carpeta mal formada es preferible a no entregar el reporte.
    """
    dirs = discover_week_dirs(root)
    if not dirs:
        raise FileNotFoundError(
            f"No se encontró ninguna semana en {root}. Una carpeta de semana "
            f"debe contener los 4 insumos ({', '.join(WEEKLY_REQUIRED_KEYWORDS)}).")
    results = []
    for d in dirs:
        try:
            res = process_sullivan_weekly_data(d, tock_basis=tock_basis)
            res["source_dir"] = d.name
            results.append(res)
        except Exception as exc:  # noqa: BLE001 - se reporta y se continúa
            warn(f"La semana '{d.name}' no se pudo procesar y se omite: {exc}")
    if not results:
        raise FileNotFoundError(
            f"Ninguna de las {len(dirs)} carpetas de semana en {root} se pudo procesar.")
    return attach_wow(results)


def process_sullivan_weekly_data(data_dir: Path, tock_basis: str = "net_receivable") -> Dict[str, Any]:
    """
    Procesa todos los insumos de una semana de Sullivan Rutherford Estate.
    
    Args:
        data_dir: Directorio que contiene los archivos .xlsx de la semana.
        tock_basis: 'net_receivable' (recomendado / $804) o 'net_sales' ($3,200).
    
    Returns:
        Diccionario estructurado con KPIs, tablas y series para renderizado.
    """
    data_dir = Path(data_dir)
    if not data_dir.exists():
        raise FileNotFoundError(f"Directorio de datos no encontrado: {data_dir}")

    # Identificar archivos (soporta nombres con variaciones de fecha)
    files = {f.name.lower(): f for f in data_dir.iterdir() if f.is_file() and f.suffix.lower() in (".xlsx", ".xls", ".csv")}

    def _flat(text: str) -> str:
        """Deja solo alfanuméricos en minúscula."""
        return re.sub(r"[^a-z0-9]", "", str(text).lower())

    def find_file(keyword: str) -> Path:
        # Se compara sin puntuación: el archivo del cliente se llama
        # `Open PO's 8.23.26.xlsx`, pero el demo que viaja en el paquete tiene
        # que llamarse `Open-POs-demo-8.23.26.xlsx` (el instalador rechaza
        # apóstrofos y espacios en las rutas del ZIP). Un solo criterio,
        # "open po", debe reconocer los dos.
        flat_kw = _flat(keyword)
        for fname, fpath in files.items():
            if keyword in fname or flat_kw in _flat(fname):
                return fpath
        raise FileNotFoundError(f"No se encontró archivo con palabra clave '{keyword}' en {data_dir}")

    order_report_file = find_file("orderreport")
    tock_file = find_file("tock")
    open_pos_file = find_file("open po")
    depletions_file = find_file("depletion")
    
    # -------------------------------------------------------------------------
    # 1. Procesamiento de Open POs (Park Street Distribution)
    # -------------------------------------------------------------------------
    pos_df = pd.read_excel(open_pos_file)
    pos_cols = {c: c.strip() for c in pos_df.columns}
    pos_df.rename(columns=pos_cols, inplace=True)
    
    status_col = "Status" if "Status" in pos_df.columns else [c for c in pos_df.columns if "status" in c.lower()][0]
    balance_col = "Balance" if "Balance" in pos_df.columns else [c for c in pos_df.columns if "balance" in c.lower()][0]
    aging_col = "Aging" if "Aging" in pos_df.columns else [c for c in pos_df.columns if "aging" in c.lower()][0]
    cases_col = "Total Cases" if "Total Cases" in pos_df.columns else [c for c in pos_df.columns if "case" in c.lower()][0]
    # `Total` es el importe facturado; `Balance` es lo que queda por cobrar.
    # Para una factura PAGADA el balance es 0 por definición, así que el
    # efectivo cobrado se lee del Total, no del Balance.
    total_col = next(
        (c for c in pos_df.columns if c.strip().lower() == "total"), None)

    pos_df[balance_col] = pd.to_numeric(pos_df[balance_col], errors="coerce").fillna(0.0)
    pos_df[aging_col] = pd.to_numeric(pos_df[aging_col], errors="coerce").fillna(0)
    pos_df[cases_col] = pd.to_numeric(pos_df[cases_col], errors="coerce").fillna(0)
    if total_col:
        pos_df[total_col] = pd.to_numeric(pos_df[total_col], errors="coerce").fillna(0.0)

    open_pos = pos_df[pos_df[status_col].astype(str).str.upper() == "OPEN"].copy()
    paid_pos = pos_df[pos_df[status_col].astype(str).str.upper() == "PAID"].copy()

    total_open_po_dollars = float(open_pos[balance_col].sum())
    # round, no int: truncar escondería cajas fraccionarias en vez de reportarlas.
    total_open_cases = round(float(open_pos[cases_col].sum()), 2)
    open_invoices_count = len(open_pos)
    # ANTES: sum(Balance) de las PAID, que es 0 por definición -> el KPI de
    # efectivo cobrado siempre salía en $0.00. Ahora se suma el importe facturado.
    if total_col:
        cash_received = round(float(paid_pos[total_col].sum()), 2)
    else:
        cash_received = None
        warn("El archivo de Open PO's no trae columna 'Total'; el efectivo "
             "cobrado se reporta como dato ausente en vez de como $0.00.")

    # Buckets de envejecimiento (Aging)
    b_0_15 = float(open_pos.loc[open_pos[aging_col] <= 15, balance_col].sum())
    b_16_30 = float(open_pos.loc[(open_pos[aging_col] > 15) & (open_pos[aging_col] <= 30), balance_col].sum())
    b_overdue = float(open_pos.loc[open_pos[aging_col] > 30, balance_col].sum())

    overdue_rows = []
    for _, r in open_pos[open_pos[aging_col] > 30].iterrows():
        overdue_rows.append({
            "invoice": str(r.get("Invoice #", "")),
            "customer": str(r.get("Customer", "")),
            "market": str(r.get("Market", "")),
            "aging": int(r[aging_col]),
            "balance": float(r[balance_col]),
        })
    overdue_rows.sort(key=lambda x: x["balance"], reverse=True)

    po_aging_data = [
        {"bucket": "0–15 days", "amount": b_0_15, "status": "good"},
        {"bucket": "16–30 days", "amount": b_16_30, "status": "warn"},
        {"bucket": "30+ days (overdue)", "amount": b_overdue, "status": "critical"},
    ]
    # Regla de visualización: todas las gráficas de barras ordenadas siempre de mayor a menor
    po_aging_data.sort(key=lambda x: x["amount"], reverse=True)

    # -------------------------------------------------------------------------
    # 2. Procesamiento de Tock
    # -------------------------------------------------------------------------
    tock_df = pd.read_excel(tock_file)
    tock_clean_cols = {c.strip().lower(): c for c in tock_df.columns}
    
    def get_tock_sum(col_key: str) -> float:
        for k, orig in tock_clean_cols.items():
            if col_key in k:
                return float(pd.to_numeric(tock_df[orig], errors="coerce").fillna(0.0).sum())
        return 0.0

    tock_gross = get_tock_sum("gross sales")
    tock_net_sales = get_tock_sum("net sales")
    tock_net_receivable = get_tock_sum("net receivable")

    tock_chosen = tock_net_receivable if tock_basis == "net_receivable" else tock_net_sales

    # -------------------------------------------------------------------------
    # 3. Procesamiento de DTC (OrderReport deduplicado por Order Number)
    # -------------------------------------------------------------------------
    orders_df = pd.read_excel(order_report_file)
    ord_cols = {c: c.strip() for c in orders_df.columns}
    orders_df.rename(columns=ord_cols, inplace=True)

    order_num_col = "Order Number"
    channel_col = "Channel"
    subtotal_col = "SubTotal"
    vendor_col = "External Order Vendor"
    package_col = "Club Package"
    club_title_col = "Club Title"

    # Deduplicar por número de orden para obtener SubTotal a nivel orden.
    # (Verificado: esta suma coincide EXACTO con el Sub Total de SalesbyChannel.)
    dedup_orders = orders_df.drop_duplicates(subset=[order_num_col]).copy()
    dedup_orders[subtotal_col] = pd.to_numeric(dedup_orders[subtotal_col], errors="coerce").fillna(0.0)
    for _col in (package_col, club_title_col):
        if _col not in dedup_orders.columns:
            dedup_orders[_col] = ""

    # ------------------------------------------------------- Periodo del reporte
    # ANTES estas tres etiquetas estaban escritas a mano ("Week ending Aug 23,
    # 2026"), así que CUALQUIER semana que se procesara se rotulaba —y se
    # guardaba— como la del 23-ago-2026: dos semanas distintas se sobreescribían
    # en el mismo archivo de salida. Ahora se derivan de la fecha de pago más
    # reciente que traiga el propio export.
    paid_dates = pd.to_datetime(orders_df.get("Order Paid Date"), errors="coerce").dropna()
    if paid_dates.empty:
        paid_dates = pd.to_datetime(orders_df.get("Order Submitted Date"), errors="coerce").dropna()
    if paid_dates.empty:
        paid_dates = pd.to_datetime(tock_df.get("Date"), errors="coerce").dropna()

    if len(paid_dates):
        anchor = paid_dates.max().date()
        # Semana comercial de lunes a domingo (la que usa el cliente en sus
        # propios archivos: "Week of 8/17-8/23/26").
        iso = anchor.isocalendar()
        week_start = date.fromisocalendar(iso[0], iso[1], 1)
        week_end = week_start + timedelta(days=6)
    else:
        week_start = week_end = None
        warn("El export no trae ninguna fecha utilizable (Order Paid Date / "
             "Order Submitted Date / Date de Tock): el periodo se reporta como "
             "dato ausente en vez de inventar una semana.")

    if week_end is not None:
        period_label = f"Week ending {week_end:%b %d, %Y}"
        week_label = (f"Week of {week_start.month}/{week_start.day}"
                      f"–{week_end.month}/{week_end.day}/{week_end:%y}")
        date_closing = week_end.isoformat()
    else:
        period_label = week_label = BLANK
        date_closing = None

    is_web = dedup_orders[channel_col].astype(str).str.lower() == "web"
    is_tock_vendor = dedup_orders[vendor_col].astype(str).str.lower().str.contains("tock", na=False)

    web_ecomm_subtotal = float(dedup_orders[is_web & ~is_tock_vendor][subtotal_col].sum())
    pos_tasting_room = float(dedup_orders[dedup_orders[channel_col].astype(str).str.lower() == "pos"][subtotal_col].sum())
    inbound_telesales = float(dedup_orders[dedup_orders[channel_col].astype(str).str.lower() == "inbound"][subtotal_col].sum())
    
    # Canal Club
    is_club = dedup_orders[channel_col].astype(str).str.lower() == "club"
    club_orders = dedup_orders[is_club]
    
    founders_subtotal = 0.0
    estate_subtotal = 0.0
    unclassified_subtotal = 0.0
    unclassified_orders = []

    # Coincidencia EXPLÍCITA por nombre de programa, igual que el mensual. Se mira
    # el paquete Y el título: en el export real el paquete puede venir vacío y el
    # título traer el nombre del programa (o al revés).
    for _, r in club_orders.iterrows():
        name = f"{r.get(package_col, '')} {r.get(club_title_col, '')}".lower()
        sub = float(r[subtotal_col])
        if "founder" in name:
            founders_subtotal += sub
        elif "estate" in name:
            estate_subtotal += sub
        else:
            # Club sin programa reconocible -> "No clasificados" (decisión de
            # negocio del cliente, 2026-09-02). ANTES esto se reportaba como
            # Founder's Club cuando Founder's daba 0, y se PERDÍA por completo
            # cuando Founder's era > 0. Ahora es su propia fila visible y siempre
            # entra al total.
            unclassified_subtotal += sub
            unclassified_orders.append({
                "order": blank_if_missing(r.get(order_num_col)),
                "package": blank_if_missing(r.get(package_col)),
                "title": blank_if_missing(r.get(club_title_col)),
                "amount": round(sub, 2),
                "reason": "Club channel, no program named",
            })
    unclassified_orders.sort(key=lambda x: x["amount"], reverse=True)

    # Los 9 canales directivos de DTC + la fila diagnóstica de No clasificados.
    channel_mix = [
        {"channel": "Tasting Room", "amount": pos_tasting_room, "category": "POS"},
        {"channel": "Telesales", "amount": inbound_telesales, "category": "Inbound"},
        {"channel": "Founder's Club", "amount": founders_subtotal, "category": "Club"},
        {"channel": "Web / Ecommerce", "amount": web_ecomm_subtotal, "category": "Web"},
        {"channel": f"Tock ({'Net Rec.' if tock_basis=='net_receivable' else 'Net Sales'})", "amount": tock_chosen, "category": "Tock"},
        {"channel": "Events", "amount": 0.0, "category": "Tag/Inbound"},
        {"channel": "Corporate", "amount": 0.0, "category": "Tag/Inbound"},
        {"channel": "Friends & Family", "amount": 0.0, "category": "Tag/Inbound"},
        {"channel": "Estate Club", "amount": estate_subtotal, "category": "Club"},
    ]
    # La fila diagnóstica solo aparece cuando hay algo que reportar, pero su
    # importe SIEMPRE entra al total (por eso se suma después del if).
    if abs(unclassified_subtotal) > 0.005 or unclassified_orders:
        channel_mix.append({
            "channel": UNCLASSIFIED,
            "amount": unclassified_subtotal,
            "category": "Diagnostic",
        })

    channel_mix.sort(key=lambda x: x["amount"], reverse=True)

    total_dtc_sales = sum(item["amount"] for item in channel_mix)
    top_channel = channel_mix[0] if channel_mix else {"channel": "—", "amount": 0.0}
    top_channel_pct = (top_channel["amount"] / total_dtc_sales * 100) if total_dtc_sales > 0 else 0.0

    # -------------------------------------------------------------------------
    # 4. Procesamiento de Depletions (iDig Southern Glazer's)
    # -------------------------------------------------------------------------
    dep_raw = pd.read_excel(depletions_file, header=None)
    row1 = dep_raw.iloc[1].ffill()
    row2 = dep_raw.iloc[2]

    col_names = []
    for m, sub in zip(row1, row2):
        m_s = str(m).strip()
        sub_s = str(sub).strip()
        if any(h in sub_s for h in ["Sites", "OnOff", "Brands", "Item"]):
            col_names.append(sub_s)
        else:
            col_names.append(f"{m_s} - {sub_s}")

    dep_data = dep_raw.iloc[3:].copy()
    dep_data.columns = col_names

    # Columna del mes más reciente. ANTES se buscaba "Aug 2026" literal, así
    # que en septiembre el reporte seguiría leyendo agosto sin avisar. Ahora se
    # parsea el mes de cada columna mensual de 9L y se toma la más reciente.
    _MONTHS = {m: i for i, m in enumerate(
        ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
         "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], start=1)}

    def _month_key(col_name: str):
        m = re.search(r"1 Depletion Month ([A-Z][a-z]{2}) (\d{4})", str(col_name))
        if not m:
            return None
        return (int(m.group(2)), _MONTHS.get(m.group(1), 0))

    nine_l_cols = [c for c in col_names if "9L Cases" in c]
    monthly_9l = [(c, _month_key(c)) for c in nine_l_cols]
    monthly_9l = [(c, k) for c, k in monthly_9l if k]
    if monthly_9l:
        monthly_9l.sort(key=lambda t: t[1])
        latest_col, latest_key = monthly_9l[-1]
        depletions_period = (f"{[k for k, v in _MONTHS.items() if v == latest_key[1]][0]} "
                             f"{latest_key[0]} (Monthly feed)")
    elif nine_l_cols:
        latest_col = nine_l_cols[-1]
        depletions_period = BLANK
        warn("No se pudo identificar el mes de las columnas de depletions; se "
             "usa la última columna de 9L Cases del archivo.")
    else:
        raise ValueError(
            f"El archivo de depletions {depletions_file.name} no trae ninguna "
            "columna de '9L Cases'. Revisa que sea el export de iDig.")

    dep_data[latest_col] = pd.to_numeric(dep_data[latest_col], errors="coerce").fillna(0.0)

    total_dep_row = dep_data[(dep_data["OnOff Premises"] == "Total") & (dep_data["Sites"] == "Total")]
    if not total_dep_row.empty:
        total_depletions_9l = float(total_dep_row[latest_col].values[0])
    else:
        total_depletions_9l = None
        warn("El iDig no trae la fila Total/Total; el total de depletions se "
             "reporta como dato ausente en vez de un número inventado.")

    # ------------------------------------------------- Depletions por estado
    # ANTES este desglose estaba escrito a mano (CA 8.92, FL 3.08, ...): eran
    # cifras copiadas del archivo de una semana concreta, así que cualquier otra
    # semana mostraba los números de agosto de 2026. Ahora se derivan.
    #
    # Se usa el nivel de SUBTOTAL POR SITIO (Sites != Total y los tres niveles
    # inferiores en "Total"): verificado contra el archivo real, esos subtotales
    # suman EXACTO la fila Total/Total (13.58331), mientras que mezclar niveles
    # duplicaría. Varias regiones comerciales del mismo estado ("CA-North" y
    # "CA-South") se consolidan en un solo estado, que es como razona el cliente.
    site_totals = dep_data[
        (dep_data["Sites"].notna())
        & (dep_data["Sites"] != "Total")
        & (dep_data["OnOff Premises"] == "Total")
        & (dep_data["Brands"] == "Total")
        & (dep_data["Item Names"] == "Total")
    ]

    by_state: Dict[str, float] = {}
    unattributed = 0.0
    for _, r in site_totals.iterrows():
        cases = float(r[latest_col])
        code = state_from_site(r["Sites"])
        if code:
            by_state[code] = by_state.get(code, 0.0) + cases
        else:
            unattributed += cases
            warn(f"Sitio de distribución sin estado reconocible: "
                 f"{blank_if_missing(r['Sites'])} ({cases:,.2f} cajas 9L).")

    # Cuadre contra la fila Total/Total del propio archivo: si no cuadra, el
    # nivel de agregación elegido está mal y hay que avisarlo, no taparlo.
    derived_total = round(sum(by_state.values()) + unattributed, 2)
    if total_depletions_9l is not None and derived_total != round(total_depletions_9l, 2):
        warn(f"El desglose por estado suma {derived_total:,.2f} cajas 9L pero la "
             f"fila Total del iDig dice {total_depletions_9l:,.2f}. Se reporta el "
             "desglose tal cual; revisa la jerarquía del export.")

    state_depletions = {k: round(v, 2) for k, v in by_state.items()}
    # Mercados declarados sin feed de sell-through: se muestran en 0 y marcados
    # como no live para que no se lean como mercados inexistentes.
    for code in MARKETS_WITHOUT_SELL_THROUGH_FEED:
        state_depletions.setdefault(code, 0.0)

    distributor_depletions = [
        {"distributor": "Southern Glazer's",
         "cases": round(total_depletions_9l, 2) if total_depletions_9l is not None else None,
         "live": True},
        {"distributor": "Favorite Brands", "cases": 0.0, "live": False,
         "note": "No sell-through feed for TX yet"},
        {"distributor": "Other", "cases": round(unattributed, 2), "live": True,
         "note": "Distribution sites whose state could not be identified"},
    ]

    # -------------------------------------------------------------------------
    # Estructurar resultado consolidado
    # -------------------------------------------------------------------------
    return {
        "period_label": period_label,
        "week_label": week_label,
        "date_closing": date_closing,
        "tock_basis_used": tock_basis,
        "kpis": {
            "total_dtc_sales": round(total_dtc_sales, 2),
            "wow_pct_change": None,
            "top_channel_name": top_channel["channel"],
            "top_channel_amount": round(top_channel["amount"], 2),
            "top_channel_pct": round(top_channel_pct, 1),
            "cash_received": cash_received,
            "total_open_pos_amount": round(total_open_po_dollars, 2),
            "total_open_cases": total_open_cases,
            "open_invoices_count": open_invoices_count,
            "overdue_30_amount": round(b_overdue, 2),
            "overdue_30_customer": overdue_rows[0]["customer"] if overdue_rows else "None",
            "overdue_30_aging": overdue_rows[0]["aging"] if overdue_rows else 0,
            "depletions_9l_cases": (round(total_depletions_9l, 2)
                                    if total_depletions_9l is not None else None),
            "depletions_period": depletions_period,
            "unclassified_amount": round(unclassified_subtotal, 2),
            "unclassified_orders": len(unclassified_orders),
        },
        # Detalle auditable de lo que la cascada no pudo asignar. Se expone
        # siempre para que ninguna venta quede sin explicación.
        "unclassified_detail": unclassified_orders,
        "channel_mix": channel_mix,
        "po_aging": po_aging_data,
        "overdue_details": overdue_rows,
        # `live` = el estado sí llega en el feed del distribuidor. Ordenado de
        # mayor a menor, como todas las gráficas de barras del repo.
        "depletions_by_state": sorted(
            [{"state": s, "cases": v, "live": s in by_state}
             for s, v in state_depletions.items()],
            key=lambda d: d["cases"], reverse=True,
        ),
        "depletions_by_distributor": distributor_depletions,
        "inventory_supply_status": {
            "cases_shipped": None,
            "cases_depleted": (round(total_depletions_9l, 2)
                               if total_depletions_9l is not None else None),
            "on_hand": None,
            "sell_through_pct": None,
            "weeks_of_supply": None,
        },
    }


if __name__ == "__main__":
    import argparse

    for _s in (sys.stdout, sys.stderr):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError, OSError):
            pass

    _root = Path(__file__).resolve().parent.parent
    ap = argparse.ArgumentParser(
        description="Procesa una semana de Sullivan y muestra el resumen.")
    ap.add_argument("--data-dir", default=None,
                    help="Carpeta con los archivos de la semana. Por defecto usa "
                         "los datos del cliente si existen, y si no, el demo.")
    _args = ap.parse_args()

    if _args.data_dir:
        weekly_dir = Path(_args.data_dir)
    else:
        weekly_dir = _root / "Client_Data" / "Sullivan_data" / "Weekly" / "Week_2026_08_23"
        if not weekly_dir.exists():
            weekly_dir = _root / "Data_for_demo" / "Sullivan_weekly_demo"

    res = process_sullivan_weekly_data(weekly_dir)
    print("\nPROCESAMIENTO SEMANAL COMPLETADO:")
    print(f"  Carpeta:        {weekly_dir}")
    print(f"  Periodo:        {res['period_label']}  ({res['week_label']})")
    print(f"  Total DTC:      ${res['kpis']['total_dtc_sales']:,.2f}")
    print(f"  Top Channel:    {res['kpis']['top_channel_name']} (${res['kpis']['top_channel_amount']:,.2f})")
    print(f"  Open POs:       ${res['kpis']['total_open_pos_amount']:,.2f} ({res['kpis']['total_open_cases']} cs)")
    print(f"  Overdue > 30d:  ${res['kpis']['overdue_30_amount']:,.2f}")
    print(f"  Efectivo:       ${res['kpis']['cash_received']:,.2f}"
          if res['kpis']['cash_received'] is not None else f"  Efectivo:       {BLANK}")
    print(f"  Depletions 9L:  {res['kpis']['depletions_9l_cases']} cs "
          f"({res['kpis']['depletions_period']})")
    print("  Por estado:     " + ", ".join(
        f"{d['state']} {d['cases']}{'' if d['live'] else ' (sin feed)'}"
        for d in res["depletions_by_state"]))
    print(f"  {UNCLASSIFIED}:   ${res['kpis']['unclassified_amount']:,.2f} "
          f"({res['kpis']['unclassified_orders']} orden/es)")
    for u in res["unclassified_detail"]:
        print(f"      orden {u['order']}  ${u['amount']:,.2f}  pkg={u['package']!r} title={u['title']!r}")
