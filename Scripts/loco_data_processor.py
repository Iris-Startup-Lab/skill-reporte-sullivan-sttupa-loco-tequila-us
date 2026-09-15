"""
================================================================================
 LOCO TEQUILA USA — PROCESADOR DE DATOS DE PRODUCCIÓN
================================================================================
Convierte los archivos crudos de `Client_Data/Loco_tequila_usa_data/` (o de
cualquier carpeta que el usuario indique) en la estructura que consume
`loco_dashboard_generator.py`.

Antes el dashboard traía TODAS las cifras incrustadas a mano en la plantilla JS:
no leía ningún archivo, así que no era un reporte sino una maqueta. Este módulo
cierra esa brecha (to_do §I.3.1) reutilizando la lógica ya validada
numéricamente en `loco_tequila_us_relationships.py`, que reproduce al centésimo
el libro maestro del cliente (Grand Total 220.65 cajas 9L · CA 198.23 · TX 22.42).

Insumos esperados en la carpeta (los nombres pueden variar en sufijos):
    1 - Supplier - Inventory*.xlsx      Inventario por bodega (FB / Park Street)
    Inventory History*.xlsx             Histórico on-hand de Signature/SGWS
    YTD by Month*.xlsx                  Botellas y órdenes por mes
    InventoryByLocation*.csv            On-hand por ubicación de Park Street
    SalesOrdersSummary*.csv             Órdenes de venta de Park Street
    orders_export*shopify.csv           Ecommerce
    orders_export*memory.csv            DTC
    FB Depletion Reports*/              Depletions mensuales por territorio

REGLAS QUE ESTE MÓDULO GARANTIZA
  * Toda serie de barras sale ordenada de MAYOR A MENOR (regla de storytelling
    declarada en SKILL.md / README.md / AGENTS.md).
  * Ningún NaN/None llega al reporte: se normaliza a la marca de dato ausente.
  * Nada se inventa. Lo que no existe en los archivos se reporta como ausente
    con su motivo, en vez de rellenarse con un número plausible.
================================================================================
"""

import math
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA_DIR = PROJECT_ROOT / "Client_Data" / "Loco_tequila_usa_data"

# Marca de dato ausente (misma convención que los generadores de Sullivan).
BLANK = "—"
_MISSING = {"nan", "nat", "none", "null", "undefined", "<na>", ""}

# Productos que no son venta comercial y no deben contaminar los rankings.
NON_SELLABLE_HINTS = ("not sellable", "sample")


def warn(msg: str) -> None:
    """Aviso visible en consola: un reporte que se arma con supuestos silenciosos
    es peor que uno que falla."""
    print(f"  [AVISO] {msg}", file=sys.stderr)


def blank_if_missing(value, blank: str = BLANK) -> str:
    if value is None:
        return blank
    try:
        if pd.isna(value):
            return blank
    except (TypeError, ValueError):
        pass
    text = str(value).strip()
    return blank if text.lower() in _MISSING else text


def sanitize_for_json(obj):
    """NaN / Infinity -> None en toda la estructura, para poder serializar con
    allow_nan=False y que un NaN nunca se imprima como 'NaN' en el HTML."""
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [sanitize_for_json(v) for v in obj]
    if isinstance(obj, float):
        return None if (math.isnan(obj) or math.isinf(obj)) else obj
    if hasattr(obj, "item") and not isinstance(obj, (str, bytes)):
        try:
            value = obj.item()
        except (AttributeError, ValueError):
            return obj
        if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
            return None
        return value
    return obj


def _load_validated_module():
    """
    Importa la lógica ya validada. Vive en la raíz del proyecto como
    `loco_tequila_us_relationships.py`; se resuelve por ruta desde PROJECT_ROOT
    para que funcione igual en Windows y en Linux, y desde cualquier CWD.
    """
    root = str(PROJECT_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)
    try:
        import loco_tequila_us_relationships as validated
        return validated
    except ImportError as exc:
        raise ImportError(
            "No se encontró 'loco_tequila_us_relationships.py' en la raíz del "
            f"proyecto ({PROJECT_ROOT}). Es la lógica de cálculo validada que "
            "este procesador reutiliza."
        ) from exc


def _desc(rows: list, key: str) -> list:
    """Ordena de mayor a menor. Regla de visualización obligatoria del repo."""
    return sorted(rows, key=lambda r: (r.get(key) or 0), reverse=True)


def _is_sellable(product: str) -> bool:
    p = str(product).lower()
    return not any(h in p for h in NON_SELLABLE_HINTS)


def _month_series(by_month: dict) -> list:
    """
    Convierte {'JAN': 50, 'FEB': 83, ...} en una lista ordenada por CALENDARIO.
    Ojo: esta serie es de tiempo, así que NO se ordena de mayor a menor —
    reordenarla destruiría el eje. La regla descendente aplica a rankings
    categóricos, no a series temporales.
    """
    order = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
             "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
    return [{"month": m, "value": float(by_month.get(m, 0) or 0)}
            for m in order if m in by_month]


def process_loco_data(data_dir: Optional[Path] = None,
                      account_map_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Lee la carpeta de datos de Loco Tequila USA y devuelve la estructura del
    reporte. `account_map_path` es opcional: sin él, vendedor y canal comercial
    se resuelven por heurística y se marca así en el reporte (to_do §I.3.2).
    """
    data_dir = Path(data_dir) if data_dir else DEFAULT_DATA_DIR
    if not data_dir.exists():
        raise FileNotFoundError(
            f"No se encontró la carpeta de datos de Loco Tequila: {data_dir}"
        )
    validated = _load_validated_module()
    data_dir_str = str(data_dir)

    import loco_attribution
    import loco_margin

    # Tasas de margen y conversiones de unidad, declarativas y editables por el
    # cliente. Si el archivo no está, `available` queda en False y el reporte
    # vuelve a declarar la brecha en lugar de fallar.
    _margin = loco_margin.load_margin_rates()

    # El mapa de cuentas por omisión es el derivado del libro del cliente. La
    # bandera `--account-map` existía desde septiembre y NUNCA se le pasó un
    # archivo: por eso el leaderboard salía dominado por una barra "Unknown".
    # No era un bug de cálculo, era un insumo ausente.
    account_map = None
    if account_map_path:
        account_map = validated.load_account_map(account_map_path)
    else:
        default_map = loco_attribution.default_account_map_path()
        if default_map:
            account_map = validated.load_account_map(str(default_map))
            print(f"  [INFO] Mapa de cuentas por omisión: {default_map.name} "
                  f"({len(account_map)} cuentas)", file=sys.stderr)
        else:
            warn("Sin mapa de cuentas: el vendedor no se puede resolver a nivel "
                 "cuenta. Cada línea sin atribuir se lista con su motivo en la "
                 "sección de fuentes del reporte.")

    # ---------------------------------------------------------------- inventario
    inv = validated.build_inventory_table(data_dir_str)
    inv = inv.copy()
    inv["_sellable"] = inv["Product"].map(lambda p: _is_sellable(blank_if_missing(p)))

    # El desglose por BODEGA ya lo calculaba `build_inventory_table` y aquí se
    # tiraba: solo pasaban total/CA/TX. El cliente pidió exactamente esto —
    # "inventory sku breakdown across Signature / Favorite Brands / Park Street" —
    # así que es reexposición, no cálculo nuevo.
    inventory_rows = _desc([
        {
            "product": blank_if_missing(r["Product"]),
            "total_9l": round(float(r["Grand Total (9L)"]), 2),
            "ca_9l": round(float(r["Total CA (9L)"]), 2),
            "tx_9l": round(float(r["Total TX (9L)"]), 2),
            "socal_sgws_9l": round(float(r["SO CAL SGWS (On Hand)"]), 2),
            "norcal_sgws_9l": round(float(r["NOR CAL SGWS (On Hand)"]), 2),
            "parkstreet_ca_9l": round(float(r["CA Park St (On Hand)"]), 2),
            "fb_tx_9l": round(float(r["Texas FB (On Hand)"]), 2),
            "sellable": bool(r["_sellable"]),
        }
        for _, r in inv.iterrows()
    ], "total_9l")

    # El inventario COMERCIAL excluye las líneas no vendibles (muestras). No es
    # cosmético: sumando todo dan 226.73 cajas 9L, y el libro maestro del cliente
    # reporta 220.65 (CA 198.23 · TX 22.42). La diferencia son exactamente las
    # 6.08 cajas de "NOT SELLABLE - SAMPLES ONLY", que se reportan aparte para
    # cuadrar con el cliente sin ocultar existencias.
    #
    # Se suma en CRUDO y se redondea al final: redondear cada fila a 2 decimales
    # antes de sumar desviaba el total un centavo (220.64 en vez de 220.65),
    # porque estas cajas 9L son fracciones periódicas (x/12).
    sell = inv[inv["_sellable"]]
    smp = inv[~inv["_sellable"]]
    inv_total = round(float(sell["Grand Total (9L)"].sum()), 2)
    inv_ca = round(float(sell["Total CA (9L)"].sum()), 2)
    inv_tx = round(float(sell["Total TX (9L)"].sum()), 2)
    inv_samples = round(float(smp["Grand Total (9L)"].sum()), 2)
    if not smp.empty:
        warn(f"{len(smp)} línea(s) de inventario no vendible ({inv_samples:,.2f} cajas 9L) "
             "se excluyen del inventario comercial y se reportan aparte.")

    # Totales por bodega, para que la pestaña cuadre columna por columna contra
    # el total de CA y el de TX.
    inv_by_warehouse = [
        {"warehouse": "Signature SGWS — SO CAL", "cases_9l": round(float(sell["SO CAL SGWS (On Hand)"].sum()), 2), "region": "CA"},
        {"warehouse": "Signature SGWS — NOR CAL", "cases_9l": round(float(sell["NOR CAL SGWS (On Hand)"].sum()), 2), "region": "CA"},
        {"warehouse": "Park Street — CA", "cases_9l": round(float(sell["CA Park St (On Hand)"].sum()), 2), "region": "CA"},
        {"warehouse": "Favorite Brands — TX", "cases_9l": round(float(sell["Texas FB (On Hand)"].sum()), 2), "region": "TX"},
    ]
    inv_by_warehouse = _desc(inv_by_warehouse, "cases_9l")

    # ------------------------------------------------- mayoristas y retail directo
    wholesale_df, retail_df = validated.build_wholesale_and_retail_tables(data_dir_str)

    def _customer_rows(df):
        rows = []
        for _, r in df.iterrows():
            rows.append({
                "customer": blank_if_missing(r["Customer"]),
                "cases_9l": round(float(r["9L"]), 2),
                "revenue": round(float(r["Revenue (USD)"]), 2),
            })
        return _desc(rows, "revenue")

    wholesale_rows = _customer_rows(wholesale_df)
    retail_rows = _customer_rows(retail_df)
    # Totales sumados en crudo y redondeados una sola vez (ver nota de inventario).
    wholesale_revenue = round(float(wholesale_df["Revenue (USD)"].sum()), 2)
    retail_revenue = round(float(retail_df["Revenue (USD)"].sum()), 2)

    # ------------------------------------------------------------- depletions
    dep = validated.build_depletions_by_territory(data_dir_str)
    ca, tx = dep.get("california", {}), dep.get("texas", {})
    ca_months = _month_series(ca.get("by_month_bottles", {}))
    tx_months = _month_series(tx.get("by_month_bottles", {}))

    # Serie nacional mes a mes (suma de territorios), en orden de calendario.
    all_months = [m["month"] for m in ca_months] or [m["month"] for m in tx_months]
    ca_by = {m["month"]: m["value"] for m in ca_months}
    tx_by = {m["month"]: m["value"] for m in tx_months}
    # LA CONVERSIÓN A CAJAS 9L SE HACE AQUÍ, NO EN JAVASCRIPT.
    #
    # El tablero hacía `m.bottles / 12` en JS y pintaba el resultado en crudo, así
    # que 82 botellas salían como "6.833333333333333 9L" — la queja literal del
    # cliente. Redondear en JS habría tapado el síntoma y dejado dos problemas:
    #
    #  1. La división correcta NO siempre es entre 12: el Blanco de 200 mL va
    #     entre 45. JavaScript recibe un agregado ya sumado, así que no puede
    #     aplicar una excepción por SKU ni sabiendo la regla.
    #  2. Dos capas calculando la misma cifra se desincronizan a la tercera
    #     corrección.
    #
    # Con `cases_9l` calculado aquí, el JS solo formatea.
    national_months = [
        {"month": m,
         "bottles": round(ca_by.get(m, 0.0) + tx_by.get(m, 0.0), 2),
         "cases_9l": round(_margin.to_9l("*", ca_by.get(m, 0.0) + tx_by.get(m, 0.0)), 2),
         "ca": round(ca_by.get(m, 0.0), 2),
         "tx": round(tx_by.get(m, 0.0), 2),
         "ca_cases_9l": round(_margin.to_9l("*", ca_by.get(m, 0.0)), 2),
         "tx_cases_9l": round(_margin.to_9l("*", tx_by.get(m, 0.0)), 2)}
        for m in all_months
    ]

    # Territorios como ranking categórico -> descendente. Los totales se calculan
    # sobre los valores crudos antes de redondear cada fila.
    _ca_bottles = float(ca.get("bottles_ytd", 0) or 0)
    _tx_bottles = float(tx.get("bottles_ytd", 0) or 0)
    _ca_cases = float(ca.get("9l_ytd") or ca.get("9l_ytd_from_bottles") or 0)
    _tx_cases = float(tx.get("9l_ytd") or tx.get("9l_ytd_from_bottles") or 0)
    territory_rows = _desc([
        {"territory": "California", "bottles_ytd": round(_ca_bottles, 2),
         "cases_9l_ytd": round(_ca_cases, 2),
         "accounts": int(ca.get("n_accounts", 0) or 0)},
        {"territory": "Texas", "bottles_ytd": round(_tx_bottles, 2),
         "cases_9l_ytd": round(_tx_cases, 2),
         "accounts": int(tx.get("n_accounts", 0) or 0)},
    ], "cases_9l_ytd")
    dep_bottles_total = round(_ca_bottles + _tx_bottles, 2)
    dep_cases_total = round(_ca_cases + _tx_cases, 2)

    # ----------------------------------------------------------- DTC / ecommerce
    split = validated.build_dtc_ecommerce_split(data_dir_str)
    ecom = split.get("ecommerce_untagged_shopify", {})
    dtc = split.get("dtc_tagged_or_memory", {})
    _dtc_rev = float(dtc.get("revenue_usd_no_gm", 0) or 0)
    _ecom_rev = float(ecom.get("revenue_usd_no_gm", 0) or 0)
    dtc_rows = _desc([
        {"stream": "DTC (tagged / Memory)",
         "bottles": round(float(dtc.get("bottles", 0) or 0), 2),
         "cases_9l": round(_margin.to_9l("*", dtc.get("bottles", 0) or 0), 2),
         "revenue": round(_dtc_rev, 2)},
        {"stream": "Ecommerce (Shopify)",
         "bottles": round(float(ecom.get("bottles", 0) or 0), 2),
         "cases_9l": round(_margin.to_9l("*", ecom.get("bottles", 0) or 0), 2),
         "revenue": round(_ecom_rev, 2)},
    ], "revenue")
    dtc_revenue_total = round(_dtc_rev + _ecom_rev, 2)

    # Mezcla por SKU sumando ambos flujos (ranking -> descendente).
    sku_mix: Dict[str, float] = {}
    for bucket in (ecom.get("by_category", {}), dtc.get("by_category", {})):
        for cat, bottles in bucket.items():
            sku_mix[cat] = sku_mix.get(cat, 0.0) + float(bottles or 0)
    # OJO: aquí la conversión es POR SKU, no global. El Blanco de 200 mL va
    # entre 45 y no entre 12, y eso solo se puede aplicar donde se conoce el SKU.
    sku_rows = _desc([{"sku": blank_if_missing(k), "bottles": round(v, 2),
                       "cases_9l": round(_margin.to_9l(blank_if_missing(k), v), 2)}
                      for k, v in sku_mix.items()], "bottles")

    # -------------------------------------------- split DTC por tienda (cliente)
    store_rows = []
    for name, blob in (split.get("by_store") or {}).items():
        store_rows.append({
            "stream": name,
            "bottles": round(float(blob.get("bottles", 0) or 0), 2),
            "revenue": round(float(blob.get("revenue_usd_no_gm", 0) or 0), 2),
            "orders": int(blob.get("orders", 0) or 0),
            "by_month": {k: round(float(v or 0), 2)
                         for k, v in (blob.get("by_month") or {}).items()},
            "by_sku": _desc([{"sku": blank_if_missing(k), "bottles": round(float(v or 0), 2)}
                             for k, v in (blob.get("by_category") or {}).items()], "bottles"),
        })
    store_rows = _desc(store_rows, "bottles")

    # ------------------------------------------------------------------ cuentas
    accounts = validated.build_accounts_summary(data_dir_str, account_map)
    account_rows = []
    for _, r in accounts.iterrows():
        account_rows.append({
            "account": blank_if_missing(r["account_name"]),
            "bottles": round(float(r["bottles_all_sources"]), 2),
            "last_order": blank_if_missing(r["last_order_date"])[:10],
            "orders_ytd": int(r.get("orders_ytd", 0) or 0),
            "salesperson": blank_if_missing(r["salesperson"]),
            "channel": blank_if_missing(r["channel"]),
            "attr_rule": blank_if_missing(r.get("attr_rule")),
            "attr_source": blank_if_missing(r.get("attr_source")),
            "attr_reason": blank_if_missing(r.get("attr_reason")),
        })
    account_rows = _desc(account_rows, "bottles")

    # Resumen POD (on / off premise), que es lo que el cliente llama POD. El
    # canal autoritativo viene de la columna PREMISE del distribuidor cuando
    # existe, y del mapa de cuentas cuando no; ya no de adivinar por el nombre.
    pod: Dict[str, Dict[str, float]] = {}
    for a in account_rows:
        slot = pod.setdefault(a["channel"], {"channel": a["channel"], "accounts": 0,
                                             "bottles": 0.0, "orders_ytd": 0})
        slot["accounts"] += 1
        slot["bottles"] += a["bottles"]
        slot["orders_ytd"] += a["orders_ytd"]
    pod_rows = _desc([{**v, "bottles": round(v["bottles"], 2)} for v in pod.values()],
                     "bottles")

    # ------------------------------------------ detalle Signature (CA) y FB (TX)
    signature_detail = validated.build_signature_detail(data_dir_str)
    fb_detail = validated.build_fb_detail(data_dir_str)

    def _grid(rows, months, limit=40):
        return [{"name": blank_if_missing(r["name"]),
                 "bottles_ytd": round(float(r["bottles_ytd"] or 0), 2),
                 "cases_9l_ytd": round(_margin.to_9l("*", r["bottles_ytd"] or 0), 2),
                 "by_month": [round(float((r.get("by_month") or {}).get(m, 0) or 0), 2)
                              for m in months]}
                for r in rows[:limit]]

    sig_months = signature_detail.get("months", [])
    fb_months = fb_detail.get("months", [])
    signature_block = {
        "months": sig_months,
        "by_account": _grid(signature_detail.get("by_account", []), sig_months),
        "by_sku": _grid(signature_detail.get("by_sku", []), sig_months),
        "by_city": _grid(signature_detail.get("by_city", []), sig_months, 25),
        "orders_ytd": int(signature_detail.get("orders_ytd", 0) or 0),
    } if signature_detail else {}
    fb_block = {
        "months": fb_months,
        "by_account": _grid(fb_detail.get("by_account", []), fb_months),
        "by_sku": _grid(fb_detail.get("by_sku", []), fb_months),
        "by_premise": _grid(fb_detail.get("by_premise", []), fb_months, 10),
        "by_distributor_rep": _grid(fb_detail.get("by_distributor_rep", []), fb_months, 25),
        "snapshot": blank_if_missing(fb_detail.get("snapshot")),
    } if fb_detail else {}

    # -------------------------------------------------------------- vendedores
    by_week, attr_lines = validated.build_salesperson_by_week_detailed(
        data_dir_str, account_map)
    attribution = loco_attribution.summarize(attr_lines)
    # Invariante: mejorar la atribución no puede perder volumen por el camino.
    _rung_sum = round(sum(r["bottles"] for r in attribution["by_rule"]), 2)
    if abs(_rung_sum - attribution["total_bottles"]) > 0.01:
        warn(f"Descuadre de atribución: la suma por regla ({_rung_sum}) no iguala "
             f"el total ({attribution['total_bottles']}). Hay volumen perdido.")
    rep_totals = []
    weekly_series = []
    weekly_weeks = []
    weekly_by_rep = []
    if isinstance(by_week, pd.DataFrame) and not by_week.empty:
        cols = [c for c in by_week.columns if c != "TOTAL"]
        for c in cols:
            _b = float(by_week[c].sum())
            rep_totals.append({"rep": blank_if_missing(c),
                               "bottles": round(_b, 2),
                               "cases_9l": round(_margin.to_9l("*", _b), 2)})
        rep_totals = _desc(rep_totals, "bottles")

        # Serie temporal: orden cronológico, NO descendente.
        weekly_weeks = [blank_if_missing(wk)[:10] for wk in by_week.index]
        for wk, row in by_week.iterrows():
            weekly_series.append({
                "week": blank_if_missing(wk)[:10],
                "bottles": round(float(row.get("TOTAL", 0) or 0), 2),
            })
        # Una serie semanal por vendedor, en el MISMO orden que weekly_weeks, y
        # los vendedores ordenados de mayor a menor por volumen total.
        for rt in rep_totals:
            col = next((c for c in cols if blank_if_missing(c) == rt["rep"]), None)
            if col is None:
                continue
            weekly_by_rep.append({
                "rep": rt["rep"],
                "values": [round(float(v or 0), 2) for v in by_week[col].tolist()],
            })

    # ------------------------------------------------------------- margen bruto
    # Ya NO es una brecha. Las tasas por botella las suministró el cliente (FOB
    # para tres niveles, DTR para directo a retail y DTC, con Aureo a dos tasas
    # según canal). Se aplican por SKU y por fuente; todo SKU sin tasa se acumula
    # y se reporta, porque el registro del propio cliente documenta que mientras
    # Aureo no tuvo tasa, cada orden real de Aureo se descartó EN SILENCIO
    # durante meses. Un cero callado en una cifra de dinero es lo peor que puede
    # pasar aquí.
    margin_rows = []
    if _margin.available:
        for src_label, rows, src_key in (
            ("Signature (CA)", signature_detail.get("by_sku", []), "signature_ca"),
            ("Favorite Brands (TX)", fb_detail.get("by_sku", []), "fb_tx"),
        ):
            for r in rows:
                sku = blank_if_missing(r["name"])
                btl = float(r["bottles_ytd"] or 0)
                gm, rate = _margin.gross_margin(sku, btl, src_key)
                margin_rows.append({
                    "sku": sku, "channel": src_label,
                    "bottles": round(btl, 2),
                    "cases_9l": round(_margin.to_9l(sku, btl), 2),
                    "gross_margin": round(gm, 2),
                    "rate_per_bottle": rate,
                    "gm_per_9l": round(gm / _margin.to_9l(sku, btl), 2)
                    if _margin.to_9l(sku, btl) else 0.0,
                })
        for st in store_rows:
            src_key = "shopify" if st["stream"].lower().startswith("shopify") else "memory"
            for s in st["by_sku"]:
                sku, btl = s["sku"], float(s["bottles"] or 0)
                gm, rate = _margin.gross_margin(sku, btl, src_key)
                margin_rows.append({
                    "sku": sku, "channel": st["stream"],
                    "bottles": round(btl, 2),
                    "cases_9l": round(_margin.to_9l(sku, btl), 2),
                    "gross_margin": round(gm, 2),
                    "rate_per_bottle": rate,
                    "gm_per_9l": round(gm / _margin.to_9l(sku, btl), 2)
                    if _margin.to_9l(sku, btl) else 0.0,
                })
    margin_rows = _desc(margin_rows, "gross_margin")
    gm_total = round(sum(r["gross_margin"] for r in margin_rows), 2)
    gm_bottles = round(sum(r["bottles"] for r in margin_rows), 2)
    gm_cases = round(sum(r["cases_9l"] for r in margin_rows), 2)
    unmatched_skus = _margin.unmatched_skus
    if unmatched_skus:
        warn("SKU sin tasa de margen (se reportan en la sección de fuentes): "
             + ", ".join(u["sku"] for u in unmatched_skus[:6]))

    # ------------------------------------------------------------ trazabilidad
    # Qué archivo y qué columna alimenta cada bloque. Los chips del tablero
    # citaban rangos de celda del libro MANUAL del cliente
    # (`Monthly Summary rows 3 & 9`), no los archivos que este procesador lee —
    # de ahí la pregunta del cliente sobre de dónde salen los números. Se nombran
    # SUS archivos y SUS columnas: la regla del repo prohíbe exponer rutas
    # internas y nombres de script, no el origen del dato.
    provenance = [
        {"measure": "Depletions — California (Signature)",
         "source": "YTD by Month [Bottles, Orders].xlsx",
         "basis": "Monthly bottle columns JAN..DEC per account and item",
         "transform": "bottles / 12 -> 9L cases (200mL Blanco / 45)",
         "amount": f"{_ca_bottles:,.0f} bottles"},
        {"measure": "Depletions — Texas (Favorite Brands)",
         "source": blank_if_missing(fb_detail.get("snapshot")) or "Favorite Brands depletion report",
         "basis": "Monthly bottle columns; PREMISE and SALES REP columns",
         "transform": "already in bottles; no conversion",
         "amount": f"{_tx_bottles:,.0f} bottles"},
        {"measure": "Inventory on hand",
         "source": "1 - Supplier - Inventory.xlsx · Inventory History.xlsx · InventoryByLocation.csv",
         "basis": "Per-warehouse on-hand: SGWS SoCal / SGWS NorCal / Park Street CA / Favorite Brands TX",
         "transform": "SGWS decimal cases x 0.5; Park Street 6 bottles per case (24 for 200mL)",
         "amount": f"{inv_total:,.2f} 9L cases"},
        {"measure": "Wholesale and direct-to-retail revenue",
         "source": "SalesOrdersSummary.csv",
         "basis": "Line-level Total column, by Customer Type",
         "transform": "line Total summed; never the order-level Total Value, which repeats per line",
         "amount": f"${wholesale_revenue + retail_revenue:,.2f}"},
        {"measure": "DTC — Shopify and Memory Bottles",
         "source": "orders_export (Shopify).csv · orders_export (Memory Bottles).csv",
         "basis": "Line items, order tags, distinct order IDs",
         "transform": "split by originating store",
         "amount": f"{sum(s['bottles'] for s in store_rows):,.0f} bottles"},
        {"measure": "Salesperson attribution",
         "source": "Account map derived from the client Accounts sheets",
         "basis": "Account name -> salesperson -> channel",
         "transform": "ranked ladder: exact name, name prefix, alias, order tag",
         "amount": f"{attribution['attributed_pct']}% of bottles attributed"},
    ]
    if _margin.available:
        provenance.append({
            "measure": "Gross margin",
            "source": "Client per-bottle margin rate table",
            "basis": "FOB for three-tier; DTR for direct-to-retail and DTC",
            "transform": "bottles x rate per bottle; Aureo carries two rates by channel",
            "amount": f"${gm_total:,.2f}",
        })

    period_label = f"YTD {national_months[-1]['month'].title()} 2026" if national_months else "YTD"

    # NADA de rutas del sistema de archivos en la estructura que va al reporte.
    # `data_dir` completo y la ruta del snapshot se serializaban al HTML y ahi
    # quedaban visibles para el cliente, lo que rompe la regla de presentacion
    # ejecutiva limpia (cero rutas internas en la UI final). Del snapshot si
    # interesa CUAL se uso, asi que se conserva solo el nombre del archivo.
    _snapshot = dep.get("fb_depletion_snapshot_used") or ""
    _snapshot_name = Path(str(_snapshot)).name if _snapshot else ""

    return {
        "brand": "Loco Tequila USA",
        # Solo el nombre de la carpeta: el usuario reconoce su juego de datos
        # sin que se exponga donde vive en el disco.
        "data_source": Path(str(data_dir)).name,
        "period_label": period_label,
        "account_map_used": bool(account_map_path),
        "depletion_snapshot": blank_if_missing(_snapshot_name),
        "kpis": {
            "inventory_total_9l": inv_total,
            "inventory_ca_9l": inv_ca,
            "inventory_tx_9l": inv_tx,
            "inventory_samples_9l": inv_samples,
            "wholesale_revenue": wholesale_revenue,
            "retail_revenue": retail_revenue,
            "dtc_revenue": dtc_revenue_total,
            "depletions_bottles_ytd": dep_bottles_total,
            "depletions_cases_9l_ytd": dep_cases_total,
            "accounts_active": len(accounts),
            "gross_margin_total": gm_total if _margin.available else None,
            "attributed_pct": attribution["attributed_pct"],
            "orders_ytd": int(signature_detail.get("orders_ytd", 0) or 0)
            + sum(s["orders"] for s in store_rows),
        },
        "inventory": inventory_rows,
        "inventory_by_warehouse": inv_by_warehouse,
        "wholesale": wholesale_rows,
        "retail": retail_rows,
        "territories": territory_rows,
        "depletions_monthly": national_months,
        "dtc_streams": dtc_rows,
        "dtc_by_store": store_rows,
        "sku_mix": sku_rows,
        "accounts": account_rows,
        "pod": pod_rows,
        "signature": signature_block,
        "favorite_brands": fb_block,
        "reps": rep_totals,
        "weekly": weekly_series,
        "weekly_weeks": weekly_weeks,
        "weekly_by_rep": weekly_by_rep,
        "attribution": attribution,
        "margin": {
            "available": _margin.available,
            "rows": margin_rows,
            "total": gm_total,
            "bottles": gm_bottles,
            "cases_9l": gm_cases,
            "gm_per_9l": round(gm_total / gm_cases, 2) if gm_cases else 0.0,
            "provenance": _margin.provenance(),
            "unmatched_skus": unmatched_skus,
        },
        "provenance": provenance,
        # Brechas declaradas, no rellenadas con supuestos. La de margen bruto
        # queda CERRADA cuando la tabla de tasas del cliente está presente: ya no
        # se afirma que no es calculable (to_do §O.8).
        "gaps": {
            "gross_margin": None if _margin.available else (
                "No disponible: no se encontró la tabla de tasas de margen por "
                "botella. Todas las cifras monetarias son INGRESO BRUTO, no margen."
            ),
            "account_mapping": None if account_map is not None else (
                "Sin mapa de cuentas: el vendedor no se puede resolver a nivel "
                "cuenta. Cada línea sin atribuir se lista con su motivo."
            ),
            "weekly_texas": (
                "The weekly salesperson series covers only sources that carry a "
                "transaction date (Signature, Park Street, Shopify, Memory "
                "Bottles). The Favorite Brands feed is a cumulative snapshot with "
                "no transaction date, so Texas depletions appear in the Favorite "
                "Brands tab but not in the weekly rep series."
            ),
        },
    }


if __name__ == "__main__":
    import argparse

    for _s in (sys.stdout, sys.stderr):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError, OSError):
            pass

    ap = argparse.ArgumentParser(
        description="Procesa los datos de Loco Tequila USA y muestra un resumen.")
    ap.add_argument("--data-dir", default=None,
                    help="Carpeta con los archivos crudos (por defecto Client_Data/Loco_tequila_usa_data).")
    ap.add_argument("--account-map", default=None,
                    help="CSV opcional cuenta → vendedor → canal.")
    args = ap.parse_args()

    res = process_loco_data(args.data_dir, args.account_map)
    k = res["kpis"]
    print("\nPROCESAMIENTO LOCO TEQUILA USA COMPLETADO")
    # La ruta completa se imprime en consola (herramienta de desarrollo),
    # pero NO viaja en la estructura del reporte: ver nota en el return.
    print(f"  Carpeta:            {args.data_dir or DEFAULT_DATA_DIR}")
    print(f"  Periodo:            {res['period_label']}")
    print(f"  Inventario 9L:      {k['inventory_total_9l']:,.2f} "
          f"(CA {k['inventory_ca_9l']:,.2f} · TX {k['inventory_tx_9l']:,.2f})"
          f"  [+{k['inventory_samples_9l']:,.2f} no vendible]")
    print(f"  Depletions YTD:     {k['depletions_bottles_ytd']:,.0f} botellas "
          f"= {k['depletions_cases_9l_ytd']:,.2f} cajas 9L")
    print(f"  Ingreso mayorista:  ${k['wholesale_revenue']:,.2f}")
    print(f"  Ingreso retail:     ${k['retail_revenue']:,.2f}")
    print(f"  Ingreso DTC:        ${k['dtc_revenue']:,.2f}")
    print(f"  Cuentas activas:    {k['accounts_active']}")
    print(f"  Top producto:       {res['inventory'][0]['product']} "
          f"({res['inventory'][0]['total_9l']:,.2f} cajas 9L)")
    print(f"  Top mayorista:      {res['wholesale'][0]['customer']} "
          f"(${res['wholesale'][0]['revenue']:,.2f})")
