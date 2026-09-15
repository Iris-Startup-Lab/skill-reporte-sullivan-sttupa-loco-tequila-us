"""
================================================================================
 LOCO TEQUILA USA — MARGEN BRUTO Y CONVERSIONES DE UNIDAD
================================================================================
Hasta esta ronda el reporte declaraba que el margen bruto **no era calculable**
porque los archivos crudos no traen COGS por SKU. Eso era correcto con los insumos
que había: las tasas no estaban en ningún export.

Ahora sí las tenemos, y vienen del cliente — no se inventa nada. Son tasas de
margen **por botella**, en dos bases:

    FOB   ventas de tres niveles: Signature/SGWS, ACS, Favorite Brands
    DTR   directo a retail y DTC: Park Street, Shopify, Memory Bottles

DOS PARTICULARIDADES QUE NO SON OPCIONALES
------------------------------------------
1. **Aureo tiene dos tasas, según el canal**: 614.50 en mayoreo de Park Street y
   864.50 en los canales DTC surtidos por Melrose/BML. Una sola tasa para Aureo
   produce cifras equivocadas en uno de los dos canales, siempre.
2. **La conversión a cajas 9L no es siempre ÷12**: el Blanco de 200 mL va a ÷45
   (9000 mL / 200 mL). La ruta de inventario ya lo hacía bien por volumen; la de
   depletions dividía entre 12 a secas, que hoy es inocuo porque el feed de
   California solo trae SKU de 750 ML, pero deja de serlo el día que se deplete un
   200 mL: la cifra saldría 3.75x inflada.

POR QUÉ EL SKU SIN TASA AVISA EN VOZ ALTA
-----------------------------------------
El propio registro de reglas del cliente documenta que, mientras Aureo no tuvo tasa
definida, **cada orden real de Aureo se descartó en silencio** como SKU sin
coincidencia — durante meses. Un cero silencioso en una cifra de dinero es peor que
un error ruidoso, así que aquí todo SKU sin tasa se acumula y se reporta: va a la
consola y a la pestaña de fuentes del reporte.

Las tasas viven en `Config/loco_tequila_us/gross_margin_rates.csv`, editable por el
cliente sin tocar código, con su fecha de vigencia y su origen.
================================================================================
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional, Tuple

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = PROJECT_ROOT / "Config" / "loco_tequila_us"

ML_PER_9L_CASE = 9000.0
DEFAULT_BOTTLES_PER_9L = 12.0

# Qué base de margen aplica a cada fuente de dato. FOB para tres niveles, DTR para
# directo a retail y DTC.
SOURCE_BASIS = {
    "signature_ca": "FOB",
    "signature_sgws": "FOB",
    "acs": "FOB",
    "fb_tx": "FOB",
    "favorite_brands": "FOB",
    "park_street": "DTR",
    "park_street_salesperson_inventory": "DTR",
    "shopify": "DTR",
    "memory": "DTR",
}

# Qué canal aplica para las tasas que dependen del canal (hoy solo Aureo).
SOURCE_CHANNEL = {
    "park_street": "park_street",
    "park_street_salesperson_inventory": "park_street",
    "shopify": "dtc",
    "memory": "dtc",
}


@dataclass
class MarginRates:
    """Tabla de tasas cargada, más el colector de SKU sin tasa."""
    rates: Dict[Tuple[str, str, str], float] = field(default_factory=dict)
    bottles_per_9l: Dict[str, float] = field(default_factory=dict)
    effective_from: str = ""
    source_label: str = ""
    _unmatched: Dict[str, float] = field(default_factory=lambda: defaultdict(float),
                                        init=False)

    # -- margen ----------------------------------------------------------

    def rate_for(self, sku: str, basis: str, channel: str = "*") -> Optional[float]:
        """Tasa por botella, o `None` si el SKU no tiene tasa en esa base."""
        sku = (sku or "").strip()
        for ch in (channel, "*"):
            hit = self.rates.get((sku, basis, ch))
            if hit is not None:
                return hit
        return None

    def gross_margin(self, sku: str, bottles: float, source: str) -> Tuple[float, Optional[float]]:
        """
        Margen bruto de una línea. Devuelve `(gm, tasa_usada)`.

        Si el SKU no tiene tasa, devuelve `(0.0, None)` **y lo registra** para que
        salga reportado. Nunca finge un cero limpio.
        """
        basis = SOURCE_BASIS.get(source, "DTR")
        channel = SOURCE_CHANNEL.get(source, "*")
        rate = self.rate_for(sku, basis, channel)
        if rate is None:
            self._unmatched[f"{sku or '(sin SKU)'} [{basis}]"] += float(bottles or 0)
            return 0.0, None
        return float(bottles or 0) * rate, rate

    # -- unidades --------------------------------------------------------

    def to_9l(self, sku: str, bottles: float) -> float:
        """Botellas -> cajas 9L, respetando la excepción del 200 mL."""
        per_case = self.bottles_per_9l.get((sku or "").strip(),
                                           self.bottles_per_9l.get("*", DEFAULT_BOTTLES_PER_9L))
        return float(bottles or 0) / per_case if per_case else 0.0

    # -- diagnóstico -----------------------------------------------------

    @property
    def unmatched_skus(self) -> list:
        return [{"sku": k, "bottles": round(v, 2)}
                for k, v in sorted(self._unmatched.items(), key=lambda x: -x[1])]

    @property
    def available(self) -> bool:
        return bool(self.rates)

    def provenance(self) -> str:
        if not self.available:
            return ""
        return (f"Margin rates per bottle as supplied by the client "
                f"({self.source_label}), effective {self.effective_from}. "
                f"FOB applies to three-tier sales (Signature, ACS, Favorite "
                f"Brands); DTR to direct-to-retail and DTC (Park Street, "
                f"Shopify, Memory Bottles). Aureo carries two rates by channel.")


def load_margin_rates(rates_path: Optional[Path] = None,
                      units_path: Optional[Path] = None) -> MarginRates:
    """Carga tasas y conversiones. Si faltan los archivos devuelve una tabla
    vacía: el reporte vuelve a declarar la brecha, en vez de fallar."""
    rates_path = Path(rates_path) if rates_path else CONFIG_DIR / "gross_margin_rates.csv"
    units_path = Path(units_path) if units_path else CONFIG_DIR / "unit_conversions.csv"

    mr = MarginRates()
    mr.bottles_per_9l = {"*": DEFAULT_BOTTLES_PER_9L}

    if units_path.exists():
        u = pd.read_csv(units_path)
        for _, r in u.iterrows():
            if str(r.get("rule_type", "")).strip() == "bottles_per_9l":
                key = str(r.get("key", "")).strip()
                try:
                    mr.bottles_per_9l[key] = float(r.get("value"))
                except (TypeError, ValueError):
                    continue

    if not rates_path.exists():
        return mr

    df = pd.read_csv(rates_path)
    needed = {"sku", "basis", "channel", "usd_per_bottle"}
    missing = needed - set(df.columns)
    if missing:
        raise ValueError(
            f"{rates_path.name} debe tener las columnas {sorted(needed)}; "
            f"faltan {sorted(missing)}"
        )
    eff, src = set(), set()
    for _, r in df.iterrows():
        try:
            rate = float(r["usd_per_bottle"])
        except (TypeError, ValueError):
            continue
        key = (str(r["sku"]).strip(), str(r["basis"]).strip().upper(),
               str(r["channel"]).strip() or "*")
        mr.rates[key] = rate
        if str(r.get("effective_from", "")).strip():
            eff.add(str(r["effective_from"]).strip())
        if str(r.get("source", "")).strip():
            src.add(str(r["source"]).strip())
    mr.effective_from = sorted(eff)[-1] if eff else ""
    mr.source_label = ("client cost file" if src == {"client_cost_file"}
                       else ", ".join(sorted(src)))
    return mr


if __name__ == "__main__":
    mr = load_margin_rates()
    print(f"tasas cargadas: {len(mr.rates)}")
    print(f"vigencia: {mr.effective_from} | origen: {mr.source_label}")
    print(f"botellas por caja 9L: {mr.bottles_per_9l}")
    for sku in ("Blanco", "Ambar", "Puro Corazon", "Aureo", "Blanco 200mL"):
        fob = mr.rate_for(sku, "FOB")
        dtr_ps = mr.rate_for(sku, "DTR", "park_street")
        dtr_dtc = mr.rate_for(sku, "DTR", "dtc")
        print(f"  {sku:16s} FOB={fob!s:>7}  DTR/park_street={dtr_ps!s:>7}  "
              f"DTR/dtc={dtr_dtc!s:>7}  9L={mr.to_9l(sku, 12):.4f} por 12 btl")
