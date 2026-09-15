"""
================================================================================
 LOCO TEQUILA USA — ESCALERA DE ATRIBUCIÓN
================================================================================
Resuelve VENDEDOR y CANAL para cada línea, con una cascada explícita, ordenada y
auditable. Sustituye las cuatro cadenas "Unknown" ad hoc que había repartidas por
`loco_tequila_us_relationships.py`, cada una con su propio criterio y una de ellas
con un mensaje engañoso ("no map match" cuando la causa real era "no se suministró
mapa").

POR QUÉ UNA ESCALERA Y NO UN EMPAREJADOR MÁS LISTO
--------------------------------------------------
El cliente preguntó literalmente: *"unknown/unattributed, how can I ensure these
are assigned to someone, where is it grabbing these from?"*. Las dos mitades de la
pregunta necesitan la misma cosa: que cada línea cargue **la regla que la resolvió**
y, si no se resolvió, **el motivo concreto**. Sin eso, subir la tasa de atribución
solo cambia un número opaco por otro.

Cada resultado (`Attribution`) trae `rule`, `source` y `reason`, de modo que la
pestaña de fuentes pueda listar renglón por renglón lo que quedó sin asignar y por
qué — el mismo patrón que ya resolvió bien esto en el tablero unificado de Sullivan
(`build_diagnostics`).

LOS RUNGS
---------
    R0  exclusión   El campo "Sales Rep" del distribuidor NO se lee nunca.
    R1  mapa exacto  Nombre normalizado idéntico en el mapa de cuentas.
    R2  prefijo      El nombre corto es PREFIJO del largo, en frontera de palabra.
    R3  alias        Tabla de alias y consolidaciones aprobadas por el cliente.
    R4  etiqueta     Nombre de persona en la etiqueta de la orden DTC.
    R5  default TX   Sin match y territorio Texas -> único rep de Texas.
    R6  desconocido  Con el motivo nombrando la causa.

DOS FALSOS POSITIVOS QUE ESTA IMPLEMENTACIÓN EVITA A PROPÓSITO
--------------------------------------------------------------
Los dos se encontraron midiendo contra los datos reales, no razonando:

1. **Subconjunto de tokens.** Exigir que los tokens distintivos del nombre corto
   estén contenidos en el largo parece razonable y es inseguro: `"A Restaurant"`
   normaliza a `"a restaurant"`, cuyo único token propio es `"a"`, así que empataba
   con `"BRASSERIE CAPITALE,CAFE A COTE"`. Es exactamente la clase de error que el
   cliente ya había documentado con `"A Restaurant"` contra `"BOTTEGA RESTAURANT"`.
   -> Por eso NO hay rama de subconjunto de tokens.

2. **Subcadena a media frase.** Buscar el nombre corto en cualquier posición hace
   que `"The Mexican"` -> `"mexican"` empate con `"RED O REST MEXICAN CUISINE"`.
   Los nombres comerciales crecen por la DERECHA (`Lahontan` -> `Lahontan Golf
   Club`), no por el centro.
   -> Por eso el empate exige **prefijo**, no contención.

Medido sobre el feed real de California: la regla de prefijo atribuye **68.3%** del
volumen contra **31%** del emparejamiento exacto, y cede solo 2 botellas frente a la
regla insegura. Ese es el canje: eliminar toda una clase de colisiones a cambio de
nada.

LO QUE NO SE HACE, Y POR QUÉ
----------------------------
* **No hay emparejamiento difuso.** Medido con Jaccard sobre los datos reales,
  `"VENDOME WINE & SPIRITS"` proponía `"Moraga Wine & Spirits"` con 0.50 de
  similitud: empató por `"wine spirits"`. Un difuso aquí no produce una atribución
  incierta, produce una **atribución falsa** con apariencia de certeza. Los
  candidatos cercanos se ofrecen como sugerencias para revisión humana
  (`candidates`), nunca como resultado.
* **No se usa el campo de vendedor del distribuidor.** La columna `SALES REP` del
  reporte de Favorite Brands trae `AUSTIN FB WAREHOUSE`, `BLAKE SCHNEIDER`,
  `BRANDON SHELTON`: son los vendedores **de Favorite Brands**, no los de Loco.
  Atribuirlos sería inventar. Es la misma razón por la que el cliente ordena ignorar
  el campo equivalente de ACS.
* **La ambigüedad no se resuelve adivinando.** Si dos entradas del mapa empatan
  (típico de `Vendome`, que existe como tienda individual y como cadena
  consolidada), la línea va a R6 con los candidatos nombrados, porque elegir una es
  una decisión de negocio del cliente.
================================================================================
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = PROJECT_ROOT / "Config" / "loco_tequila_us"

UNKNOWN = "Unknown"
UNKNOWN_CHANNEL = "Unknown"

# --------------------------------------------------------------------------
# Normalización de nombres de cuenta
# --------------------------------------------------------------------------

_STATES = (r"(?:AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|ID|IL|IN|IA|KS|KY|LA|ME|MD|MA"
           r"|MI|MN|MS|MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|OH|OK|OR|PA|RI|SC|SD|TN"
           r"|TX|UT|VT|VA|WA|WV|WI|WY)")
# "Melrose Gas - CA", "Brescome & Barton - CT (North Haven)" -> el sufijo de
# territorio es del export, no parte del nombre de la cuenta.
_TERRITORY_SUFFIX = re.compile(r"\s*[-–]\s*" + _STATES + r"\b\s*(?:\(.*?\))?\s*$", re.I)
_TRAILING_PAREN = re.compile(r"\s*\(.*?\)\s*$")
_PUNCT = re.compile(r"[.,'’\"#]")
_DASH = re.compile(r"\s*[-–]\s*")
_LEGAL_SUFFIX = re.compile(r"\b(?:inc|llc|ltd|co|corp|the)\b")
_WS = re.compile(r"\s+")

# Tokens que por sí solos no identifican un negocio. Sin esta lista, un nombre
# de una sola palabra genérica ancla empates con cualquier cosa.
GENERIC_TOKENS = frozenset({
    "a", "an", "and", "of", "on", "the", "sale", "wine", "wines", "spirits",
    "liquor", "liquors", "market", "bar", "restaurant", "grill", "kitchen",
    "club", "hotel", "cellars", "shop", "store", "foods", "company", "house",
    "fine", "warehouse", "golf", "center", "cafe", "lounge", "tavern", "rest",
    "s", "deli", "spa", "inn", "bistro", "resort",
})
MIN_ANCHOR_LEN = 4


def normalize_account(name) -> str:
    """Clave canónica de una cuenta. Idempotente."""
    s = unicodedata.normalize("NFKD", str(name or "")).casefold().strip()
    s = _TERRITORY_SUFFIX.sub("", s)
    s = _TRAILING_PAREN.sub("", s)
    s = s.replace("&", " and ")
    s = _PUNCT.sub(" ", s)
    s = _DASH.sub(" ", s)
    s = _LEGAL_SUFFIX.sub(" ", s)
    return _WS.sub(" ", s).strip()


def has_anchor(key: str) -> bool:
    """¿La clave tiene un token propio y suficientemente largo para sostener un
    empate por prefijo? Ver el falso positivo 1 del encabezado."""
    return any(len(t) >= MIN_ANCHOR_LEN
               for t in key.split() if t not in GENERIC_TOKENS)


def _is_prefix(long_key: str, short_key: str) -> bool:
    """`short_key` es prefijo de `long_key` en frontera de palabra."""
    return long_key == short_key or long_key.startswith(short_key + " ")


# --------------------------------------------------------------------------
# Resultado
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class Attribution:
    """Resultado de resolver una línea. `rule` es el rung que la resolvió."""
    salesperson: str
    channel: str
    rule: str
    source: str
    reason: str = ""
    matched_account: str = ""
    candidates: Tuple[str, ...] = ()

    @property
    def attributed(self) -> bool:
        return self.salesperson != UNKNOWN


# --------------------------------------------------------------------------
# Resolvedor
# --------------------------------------------------------------------------

@dataclass
class AttributionResolver:
    """
    Carga las tablas declarativas una vez y resuelve línea por línea.

    `account_map`: DataFrame con columnas `account`, `salesperson`, `channel`
    (y opcionalmente `source_sheet`). Si es `None`, los rungs R1-R3 se saltan y
    los motivos de R6 lo dicen explícitamente, en vez de afirmar que la cuenta no
    empató — que es lo que hacía el mensaje anterior.
    """
    account_map: Optional[pd.DataFrame] = None
    roster: Dict[str, str] = field(default_factory=dict)
    aliases: Dict[str, str] = field(default_factory=dict)
    tx_default_rep: Optional[str] = "Joe Pat Clayton"
    tx_default_channel: str = "Off Premise"
    enable_tx_default: bool = False

    _map: Dict[str, Tuple[str, str]] = field(default_factory=dict, init=False)
    _raw: Dict[str, str] = field(default_factory=dict, init=False)
    _anchored: List[str] = field(default_factory=list, init=False)
    _map_sheet: Dict[str, str] = field(default_factory=dict, init=False)

    def __post_init__(self):
        if self.account_map is not None and len(self.account_map):
            for _, r in self.account_map.iterrows():
                key = normalize_account(r.get("account"))
                if not key or key in self._map:
                    continue
                sp = self.canonical_person(_clean(r.get("salesperson")))
                ch = _clean(r.get("channel"))
                self._map[key] = (sp or UNKNOWN, ch or UNKNOWN_CHANNEL)
                self._raw[key] = str(r.get("account") or "").strip()
                self._map_sheet[key] = _clean(r.get("source_sheet")) or "account map"
            self._anchored = [k for k in self._map if has_anchor(k)]

    # -- canonicalización de nombres de persona --------------------------

    def canonical_person(self, name: str) -> str:
        """
        Un vendedor, un nombre.

        El mapa del cliente usa formas cortas (`Mark`, `Jacky`, `Joe Pat`,
        `Sara`) mientras las fuentes transaccionales traen el nombre completo
        (`Mark Harding - CA`, `Jackquelin Gonzalez - CA`). Sin canonizar, el
        leaderboard saca DOS barras para la misma persona y ninguna de las dos
        tiene su volumen real — un error más engañoso que la barra "Unknown",
        porque parece un dato correcto.
        """
        n = _clean(name)
        if not n:
            return ""
        hit = self.roster.get(n.casefold())
        if hit:
            return hit
        # "Mark Harding - CA" -> prueba también sin el sufijo de territorio
        stripped = _TERRITORY_SUFFIX.sub("", n).strip()
        return self.roster.get(stripped.casefold(), n)

    # -- rungs -----------------------------------------------------------

    def resolve_account(self, account_name, territory: str = "") -> Attribution:
        """Vendedor y canal para una línea con nombre de cuenta."""
        key = normalize_account(account_name)

        if not self._map:
            return self._tx_default_or_unknown(
                territory,
                "no account map is loaded, so account-level attribution is "
                "unavailable for this line",
            )

        # R1 — empate exacto normalizado
        if key in self._map:
            return self._from_map(key, "R1")

        # R3 — alias y consolidaciones aprobadas (antes del prefijo: es una
        # decisión explícita del cliente y debe ganar a cualquier inferencia)
        if key in self.aliases:
            target = normalize_account(self.aliases[key])
            if target in self._map:
                return self._from_map(target, "R3", "client alias table")

        # R2 — prefijo en frontera de palabra, sin ambigüedad
        if not has_anchor(key):
            return self._tx_default_or_unknown(
                territory,
                "account name has no distinctive word long enough to match "
                "safely; matching it would risk a false attribution",
            )
        cands = [ck for ck in self._anchored
                 if _is_prefix(key, ck) or _is_prefix(ck, key)]
        if len(cands) == 1:
            return self._from_map(cands[0], "R2")
        if len(cands) > 1:
            names = tuple(self._raw[c] for c in cands[:4])
            return self._tx_default_or_unknown(
                territory,
                "account name matches more than one entry in the account map, "
                "so it needs a human decision",
                candidates=names,
            )

        near = self._near_candidates(key)
        return self._tx_default_or_unknown(
            territory,
            "account does not appear in the account map",
            candidates=near,
        )

    def resolve_tag(self, tag_text) -> Attribution:
        """R4 — vendedor desde la etiqueta de una orden DTC."""
        text = str(tag_text or "").casefold()
        if text.strip():
            # el alias más largo primero: "joe pat clayton" antes que "joe pat"
            for alias in sorted(self.roster, key=len, reverse=True):
                if alias and alias in text:
                    return Attribution(self.roster[alias], "DTC", "R4",
                                       "DTC order tag")
        return Attribution(
            UNKNOWN, "DTC", "R6", "DTC order tag",
            reason=("order carries no tag naming a known person, so the sale "
                    "cannot be credited to anyone"),
        )

    def resolve_person(self, person_name) -> Attribution:
        """R4 — cuando el propio campo es el nombre de la persona (retiros de
        inventario de vendedor en Park Street)."""
        text = str(person_name or "").casefold()
        for alias in sorted(self.roster, key=len, reverse=True):
            if alias and alias in text:
                return Attribution(self.roster[alias], "Salesperson stock",
                                   "R4", "Park Street customer name")
        return Attribution(
            UNKNOWN, UNKNOWN_CHANNEL, "R6", "Park Street customer name",
            reason=(f"{str(person_name or '').strip() or 'this name'} is not in "
                    "the salespeople roster"),
        )

    # -- helpers ---------------------------------------------------------

    def _from_map(self, key: str, rule: str, source: str = "") -> Attribution:
        """
        Resultado a partir de una entrada del mapa.

        Caso que hay que nombrar bien: la cuenta **sí** está en el mapa, pero el
        mapa del cliente la lista con vendedor `Unknown`. Sin este motivo, esas
        líneas salían sin atribuir y sin explicación, lo que las hace parecer un
        fallo de emparejamiento cuando en realidad el dato de origen es el que
        está incompleto — y son dos acciones distintas para quien lo va a
        corregir.
        """
        sp, ch = self._map[key]
        reason = ""
        if sp == UNKNOWN:
            reason = ("the account map lists this account but leaves its "
                      "salesperson as Unknown at the source")
        return Attribution(sp, ch, rule, source or self._map_sheet[key],
                           reason=reason, matched_account=self._raw[key])

    def _tx_default_or_unknown(self, territory, reason, candidates=()) -> Attribution:
        """R5 — regla del cliente: en Texas, lo no atribuido va al único rep de
        Texas. Desactivado por omisión: cambia el leaderboard de forma material,
        así que es una decisión del cliente y no un supuesto nuestro."""
        if (self.enable_tx_default and self.tx_default_rep
                and str(territory).upper().startswith("TX")):
            return Attribution(
                self.tx_default_rep, self.tx_default_channel, "R5",
                "client rule: sole Texas rep",
                reason="assigned by the Texas default, not by an account match",
                candidates=tuple(candidates),
            )
        return Attribution(UNKNOWN, UNKNOWN_CHANNEL, "R6", "account map",
                           reason=reason, candidates=tuple(candidates))

    def _near_candidates(self, key: str, limit: int = 3) -> Tuple[str, ...]:
        """Sugerencias para revisión humana. NO se usan para atribuir: medido
        sobre datos reales, el traslape de tokens propone empates falsos con
        apariencia de certeza (ver encabezado)."""
        mine = {t for t in key.split() if t not in GENERIC_TOKENS}
        if not mine:
            return ()
        scored = []
        for ck in self._map:
            theirs = {t for t in ck.split() if t not in GENERIC_TOKENS}
            if not theirs:
                continue
            j = len(mine & theirs) / len(mine | theirs)
            if j >= 0.34:
                scored.append((j, self._raw[ck]))
        scored.sort(reverse=True)
        return tuple(n for _, n in scored[:limit])


def _clean(v) -> str:
    if v is None:
        return ""
    try:
        if pd.isna(v):
            return ""
    except (TypeError, ValueError):
        pass
    s = str(v).strip()
    return "" if s.lower() in {"nan", "nat", "none", "null", "<na>", ""} else s


# --------------------------------------------------------------------------
# Carga de las tablas declarativas
# --------------------------------------------------------------------------

def load_roster(path: Optional[Path] = None) -> Dict[str, str]:
    """`alias -> display_name`. Reemplaza el diccionario incrustado de cinco
    nombres de pila, al que además le faltaba Sara."""
    path = Path(path) if path else CONFIG_DIR / "salespeople.csv"
    if not path.exists():
        return {}
    df = pd.read_csv(path)
    return {str(r["alias"]).casefold().strip(): str(r["display_name"]).strip()
            for _, r in df.iterrows()
            if _clean(r.get("alias")) and _clean(r.get("display_name"))}


def load_aliases(path: Optional[Path] = None) -> Dict[str, str]:
    """`cuenta_cruda_normalizada -> cuenta_canónica`."""
    path = Path(path) if path else CONFIG_DIR / "account_aliases.csv"
    if not path.exists():
        return {}
    df = pd.read_csv(path)
    out = {}
    for _, r in df.iterrows():
        raw, canon = _clean(r.get("raw_account")), _clean(r.get("canonical_account"))
        if raw and canon:
            out[normalize_account(raw)] = canon
    return out


def default_account_map_path() -> Optional[Path]:
    p = CONFIG_DIR / "account_mapping.csv"
    return p if p.exists() else None


def build_resolver(account_map: Optional[pd.DataFrame] = None,
                   enable_tx_default: bool = False) -> AttributionResolver:
    return AttributionResolver(
        account_map=account_map,
        roster=load_roster(),
        aliases=load_aliases(),
        enable_tx_default=enable_tx_default,
    )


# --------------------------------------------------------------------------
# Diagnósticos — el insumo de la pestaña de fuentes
# --------------------------------------------------------------------------

RULE_LABELS = {
    "R1": "Account map, exact name",
    "R2": "Account map, name prefix",
    "R3": "Client alias / chain consolidation",
    "R4": "Order tag or salesperson name",
    "R5": "Texas default (sole TX rep)",
    "R6": "Not attributed",
}


def summarize(lines: List[dict]) -> dict:
    """
    `lines`: dicts con `bottles`, `attr` (Attribution), `account`, `territory`,
    `source_file`.

    Devuelve el desglose por rung más el listado renglón a renglón de lo no
    atribuido. El invariante que se assertan aguas arriba: la suma de botellas por
    rung es igual al total, de modo que la mejora de atribución no pueda esconder
    volumen perdido.
    """
    by_rule: Dict[str, dict] = {}
    unattributed: List[dict] = []
    total = 0.0
    for ln in lines:
        a: Attribution = ln["attr"]
        b = float(ln.get("bottles") or 0)
        total += b
        slot = by_rule.setdefault(a.rule, {
            "rule": a.rule, "label": RULE_LABELS.get(a.rule, a.rule),
            "lines": 0, "bottles": 0.0,
        })
        slot["lines"] += 1
        slot["bottles"] += b
        if not a.attributed:
            unattributed.append({
                "account": ln.get("account") or "",
                "territory": ln.get("territory") or "",
                "bottles": round(b, 2),
                "reason": a.reason,
                "source": ln.get("source_file") or a.source,
                "candidates": ", ".join(a.candidates),
            })

    rows = sorted(by_rule.values(), key=lambda r: -r["bottles"])
    for r in rows:
        r["bottles"] = round(r["bottles"], 2)
        r["pct"] = round(100.0 * r["bottles"] / total, 1) if total else 0.0

    unattributed.sort(key=lambda r: -r["bottles"])
    agg: Dict[str, dict] = {}
    for u in unattributed:
        slot = agg.setdefault(u["account"] or "(unnamed)", dict(u, bottles=0.0))
        slot["bottles"] += u["bottles"]
    merged = sorted(agg.values(), key=lambda r: -r["bottles"])
    for m in merged:
        m["bottles"] = round(m["bottles"], 2)

    attributed = round(sum(r["bottles"] for r in rows if r["rule"] != "R6"), 2)
    return {
        "by_rule": rows,
        "unattributed": merged,
        "total_bottles": round(total, 2),
        "attributed_bottles": attributed,
        "attributed_pct": round(100.0 * attributed / total, 1) if total else 0.0,
        "unattributed_bottles": round(total - attributed, 2),
    }
