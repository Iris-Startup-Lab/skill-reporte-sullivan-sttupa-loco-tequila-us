"""
================================================================================
 SULLIVAN RUTHERFORD ESTATE — DASHBOARD UNIFICADO (mensual + semanal)
================================================================================
Un solo HTML con las dos cadencias, sin repetir lo que ambos reportes decían
igual y conservando lo que cada uno tenía de exclusivo.

QUÉ SE DUPLICABA (y aquí aparece UNA sola vez)
----------------------------------------------
Al comparar los dos generadores resultó que usan **la misma taxonomía de 10
canales**, solo con distinta granularidad de tiempo:

    mensual  Telesales · Event  · Corporate · Friends & Family · Tock ·
             Web / Ecommerce · Tasting Room · Estate Club · Founder's Club ·
             Unclassified
    semanal  Telesales · Events · Corporate · Friends & Family · Tock ·
             Web / Ecommerce · Tasting Room · Estate Club · Founder's Club ·
             Unclassified

Por eso la mezcla de canales era el mismo bloque dos veces. Aquí es UN
componente con un selector de cadencia, más una tabla que enfrenta las dos
columnas con los nombres homologados ("Events" -> "Event", "Tock (Net Rec.)"
-> "Tock").

También se eliminaron:
  * El encabezado y la tira de KPIs, que existían por duplicado.
  * El desglose de Club: el semanal solo tenía las filas Founder's/Estate, que
    son un subconjunto de lo que ya muestra el Club Deep Dive mensual.
  * La tabla de "No clasificados", que ambos traían por separado: ahora es una
    sola con una columna de cadencia.
  * El minimapa que el mensual repetía dentro de la pestaña de Club, idéntico
    al de la pestaña Geographic.
  * La capa de gráficas: el mensual usaba Chart.js y el semanal dibujaba SVG a
    mano. Aquí hay una sola (Chart.js, ya embebido).

QUÉ SE CONSERVA POR SER EXCLUSIVO
---------------------------------
  * Mensual: reconciliación al centavo contra el reporte financiero, cascada de
    9 prioridades, y el **mapa Albers con los puntos por código postal** (lo
    que el cliente pidió mantener explícitamente).
  * Semanal: Tock, cuentas por cobrar de distribución con semáforo de aging,
    efectivo cobrado, depletions por estado y por distribuidor.

El archivo resultante es standalone: fuentes, logotipo y Chart.js van embebidos,
así que abre sin red y sin dependencias.
================================================================================
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from dashboard_generator import (  # noqa: E402
    BLANK,
    CATEGORY_COLORS,
    CATEGORY_GLOSSARY,
    REASON_CLUB_NO_PROGRAM,
    REASON_UNKNOWN_CHANNEL,
    TOKENS,
    UNCLASSIFIED,
    build_geo,
    build_reconciliation,
    build_vista_a,
    build_vista_a_by_channel,
    build_vista_b,
    classify_orders,
    coerce_money,
    font_face_css,
    get_chart_js_inline,
    load_data_file,
    logo_white_data_uri,
    money_col,
    render_svg_map_html,
    sanitize_for_json,
    warn,
)
from sullivan_weekly_processor import (process_sullivan_weekly_data,  # noqa: E402,F401
                                      process_sullivan_weekly_series)
import i18n

# Homologación de nombres entre las dos cadencias. Sin esto la tabla comparativa
# mostraría "Event" y "Events" como si fueran canales distintos.
CHANNEL_ALIASES = {
    "events": "Event",
    "event": "Event",
    "tock (net rec.)": "Tock",
    "tock (net sales)": "Tock",
    "tock": "Tock",
    "web / ecommerce": "Web / Ecommerce",
    "tasting room": "Tasting Room",
    "telesales": "Telesales",
    "corporate": "Corporate",
    "friends & family": "Friends & Family",
    "estate club": "Estate Club",
    "founder's club": "Founder's Club",
    UNCLASSIFIED.lower(): UNCLASSIFIED,
}


def canonical_channel(name: str) -> str:
    """Nombre homologado de canal, o el original si no se reconoce (mejor
    mostrarlo tal cual que esconderlo bajo una etiqueta equivocada)."""
    return CHANNEL_ALIASES.get(str(name or "").strip().lower(), str(name or "").strip())


def build_unified_channels(vista_a: dict, weekly: dict | None) -> dict:
    """
    Une las dos mezclas de canales en una sola estructura.

    Devuelve, para cada canal homologado, el importe mensual y el semanal. Los
    canales se ordenan de MAYOR A MENOR por el importe mensual (o por el
    semanal si no hay mensual), cumpliendo la regla de ordenamiento del repo.
    """
    monthly = {}
    for cat, amount in zip(vista_a["categories"], vista_a["subtotal"]):
        monthly[canonical_channel(cat)] = float(amount)

    week = {}
    if weekly:
        for row in weekly.get("channel_mix", []):
            week[canonical_channel(row["channel"])] = float(row["amount"])

    names = list(monthly) + [n for n in week if n not in monthly]
    rows = [{
        "channel": n,
        "monthly": round(monthly.get(n, 0.0), 2) if n in monthly else None,
        "weekly": round(week.get(n, 0.0), 2) if n in week else None,
        "color": CATEGORY_COLORS.get(n, TOKENS["brand_gray"]),
    } for n in names]

    def sort_key(r):
        return (r["monthly"] if r["monthly"] is not None
                else (r["weekly"] if r["weekly"] is not None else 0.0))

    rows.sort(key=sort_key, reverse=True)
    return {
        "rows": rows,
        "monthly_total": round(sum(v for v in monthly.values()), 2),
        "weekly_total": round(sum(v for v in week.values()), 2) if week else None,
    }


def build_unified_unclassified(vista_b: dict, weekly: dict | None) -> list:
    """
    Una sola tabla de "No clasificados" con las dos cadencias.

    Antes cada reporte traía la suya, con columnas distintas para el mismo
    concepto. Aquí se normalizan a un esquema común y se distingue el origen
    con una columna de cadencia, ordenado de mayor a menor por importe.
    """
    rows = []
    for rec in vista_b.get("review_cases", []) or []:
        rows.append({
            "cadence": "Monthly",
            "order": rec.get("Order Number", BLANK),
            "date": rec.get("Date", BLANK),
            "channel": rec.get("Channel", BLANK),
            "package": rec.get("Club Package", BLANK),
            "title": rec.get("Club Title", BLANK),
            "reason": rec.get("Reason", BLANK) or BLANK,
            # `clean_records` ya dejó estos importes formateados como texto; se
            # conserva el texto para pintar y el número para ordenar.
            "amount_text": rec.get("Net Sales", BLANK),
            "amount": _amount_of(rec.get("Net Sales")),
        })
    if weekly:
        for rec in weekly.get("unclassified_detail", []) or []:
            rows.append({
                "cadence": "Weekly",
                "order": rec.get("order", BLANK),
                "date": BLANK,
                "channel": "Club",
                "package": rec.get("package", BLANK),
                "title": rec.get("title", BLANK),
                "reason": rec.get("reason", BLANK),
                "amount_text": f"${float(rec.get('amount') or 0):,.2f}",
                "amount": float(rec.get("amount") or 0),
            })
    rows.sort(key=lambda r: r["amount"], reverse=True)
    return rows


def _amount_of(text) -> float:
    """Importe numérico a partir del texto ya formateado ('$1,234.56')."""
    if text is None:
        return 0.0
    s = str(text).replace("$", "").replace(",", "").strip()
    if s in ("", BLANK):
        return 0.0
    try:
        return float(s)
    except ValueError:
        return 0.0


# ==============================================================================
# PLANTILLA
# ==============================================================================
# Se rellena por REEMPLAZO de marcadores `__NOMBRE__`, no con str.format(): la
# plantilla lleva CSS y JS con cientos de llaves, y con format() habría que
# duplicar todas y cada una, que es una fuente de errores silenciosos.
HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>__PAGE_TITLE__</title>
<style>
__FONT_FACES__

:root {
  --navy: __T_NAVY__;
  --gray: __T_GRAY__;
  --tan: __T_TAN__;
  --cream: __T_CREAM__;
  --rule: __T_RULE__;
  --grid: __T_GRID__;
  --neg: __T_NEG__;
  --map-empty: __T_MAP_EMPTY__;
}

* { box-sizing: border-box; }

body {
  margin: 0;
  background: #F4F5F7;
  color: #24303C;
  font-family: 'Poppins', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  font-size: 14px;
  line-height: 1.55;
}

.wrap { max-width: 1280px; margin: 0 auto; padding: 0 20px 60px; }

/* ---------------------------------------------------------------- encabezado */
header.hero {
  background: linear-gradient(135deg, var(--navy) 0%, #001E36 100%);
  color: #fff;
  padding: 26px 0 0;
}
.hero-inner {
  max-width: 1280px; margin: 0 auto; padding: 0 20px;
  display: flex; align-items: flex-start; justify-content: space-between;
  gap: 24px; flex-wrap: wrap;
}
.hero-logo { height: 54px; width: auto; display: block; }
.hero-title {
  font-family: 'EB Garamond', Georgia, serif;
  font-size: 27px; margin: 10px 0 2px; font-weight: 600; letter-spacing: .2px;
}
.hero-sub { font-size: 12.5px; opacity: .82; margin: 0; }
.hero-meta { text-align: right; font-size: 12px; opacity: .8; }

  .week-pick { margin-top: 8px; display: flex; align-items: center;
               gap: 8px; justify-content: flex-end; }
  .week-pick label { font-size: 10.5px; letter-spacing: .08em;
                     text-transform: uppercase; color: var(--tan); }
  .week-pick select { font: inherit; font-size: 12px; padding: 3px 8px;
                      color: #fff; background: rgba(255,255,255,.10);
                      border: 1px solid var(--tan); border-radius: 4px; }
.hero-meta strong { display: block; font-size: 15px; opacity: 1; font-weight: 600; }

/* --------------------------------------------------------------- pestañas */
nav.tabs {
  max-width: 1280px; margin: 22px auto 0; padding: 0 20px;
  display: flex; gap: 4px; flex-wrap: wrap;
}
nav.tabs button {
  appearance: none; border: 0; cursor: pointer;
  background: rgba(255,255,255,.12); color: rgba(255,255,255,.86);
  font-family: inherit; font-size: 12.5px; font-weight: 500;
  padding: 10px 16px; border-radius: 6px 6px 0 0;
  transition: background .15s, color .15s;
}
nav.tabs button:hover { background: rgba(255,255,255,.22); color: #fff; }
nav.tabs button[aria-selected="true"] {
  background: #F4F5F7; color: var(--navy); font-weight: 600;
}
nav.tabs button .tnum {
  display: inline-block; min-width: 16px; text-align: center;
  opacity: .55; margin-right: 6px; font-variant-numeric: tabular-nums;
}

.panel { display: none; padding-top: 26px; }
.panel.is-active { display: block; }

/* ------------------------------------------------------------------ bloques */
.card {
  background: #fff; border: 1px solid var(--rule); border-radius: 8px;
  padding: 18px 20px; box-shadow: 0 1px 2px rgba(0,0,0,.04);
}
.grid { display: grid; gap: 16px; }
.g2 { grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); }
.g3 { grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); }
.g4 { grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); }
.span2 { grid-column: 1 / -1; }

.sec { margin: 0 0 18px; }
.sec-head { display: flex; align-items: baseline; gap: 10px; margin: 30px 0 4px; }
.sec-head:first-child { margin-top: 0; }
.sec-num {
  background: var(--tan); color: #fff; font-size: 11px; font-weight: 600;
  width: 22px; height: 22px; border-radius: 50%;
  display: inline-flex; align-items: center; justify-content: center; flex: 0 0 auto;
}
h2.sec-title {
  font-family: 'EB Garamond', Georgia, serif;
  color: var(--navy); font-size: 20px; font-weight: 600; margin: 0;
}
p.sec-sub { color: var(--gray); font-size: 12px; margin: 2px 0 14px 32px; }
h3.blk {
  color: var(--navy); font-size: 14px; font-weight: 600;
  margin: 0 0 12px; letter-spacing: .2px;
}

/* --------------------------------------------------------------------- KPIs */
.kpi .kpi-label {
  color: var(--gray); font-size: 10.5px; font-weight: 600;
  text-transform: uppercase; letter-spacing: .7px; margin: 0 0 6px;
}
.kpi .kpi-value {
  color: var(--navy); font-size: 25px; font-weight: 600; margin: 0;
  font-variant-numeric: tabular-nums; line-height: 1.15;
}
.kpi .kpi-note { color: var(--gray); font-size: 11px; margin: 5px 0 0; }
.kpi.accent { border-left: 3px solid var(--tan); }
.kpi.warn { border-left: 3px solid var(--neg); }
.kpi.warn .kpi-value { color: var(--neg); }

.badge {
  display: inline-block; font-size: 10.5px; font-weight: 600;
  padding: 2px 8px; border-radius: 10px; letter-spacing: .3px;
}
.badge.ok { background: #E4F3E8; color: #1D6B36; }
.badge.bad { background: #FBE9E9; color: #8C2F2F; }
.badge.info { background: var(--cream); color: var(--tan); }
.badge.mo { background: #E7EDF3; color: var(--navy); }
.badge.wk { background: #F3ECE3; color: var(--tan); }

/* ------------------------------------------------------------------ tablas */
.tbl-wrap { overflow-x: auto; }
table { border-collapse: collapse; width: 100%; font-size: 12.5px; }
th, td { padding: 7px 10px; text-align: left; border-bottom: 1px solid var(--rule); }
th {
  color: var(--navy); font-size: 10.5px; font-weight: 600;
  text-transform: uppercase; letter-spacing: .55px;
  background: #FAFBFC; white-space: nowrap;
}
td.num, th.num { text-align: right; font-variant-numeric: tabular-nums; }
tbody tr:hover { background: #FCFCFD; }
tr.total-row td { font-weight: 600; color: var(--navy); background: var(--cream); }
.swatch {
  display: inline-block; width: 9px; height: 9px; border-radius: 2px;
  margin-right: 7px; vertical-align: middle;
}
.muted { color: var(--gray); }

/* ---------------------------------------------------------------- gráficas */
.chart-box { position: relative; height: 300px; }
.chart-box.tall { height: 380px; }

/* ------------------------------------------------------------------ toggle */
.seg {
  display: inline-flex; border: 1px solid var(--rule); border-radius: 6px;
  overflow: hidden; background: #fff;
}
.seg button {
  appearance: none; border: 0; background: #fff; cursor: pointer;
  font-family: inherit; font-size: 11.5px; font-weight: 500; color: var(--gray);
  padding: 6px 14px;
}
.seg button[aria-pressed="true"] { background: var(--navy); color: #fff; font-weight: 600; }
.ctl-row {
  display: flex; align-items: center; justify-content: space-between;
  gap: 12px; flex-wrap: wrap; margin-bottom: 14px;
}
select.ctl {
  font-family: inherit; font-size: 12px; padding: 6px 10px;
  border: 1px solid var(--rule); border-radius: 6px; background: #fff; color: var(--navy);
}

/* --------------------------------------------------------------------- mapa */
.map-holder svg { width: 100%; height: auto; display: block; }
#maptip {
  position: fixed; pointer-events: none; opacity: 0; transition: opacity .1s;
  background: rgba(0,30,54,.95); color: #fff; font-size: 11.5px;
  padding: 8px 11px; border-radius: 5px; z-index: 99; max-width: 260px;
}

.note {
  background: var(--cream); border-left: 3px solid var(--tan);
  padding: 11px 14px; font-size: 12px; color: #4A3B2C; border-radius: 0 5px 5px 0;
}
.empty { color: var(--gray); font-size: 12.5px; font-style: italic; padding: 18px 0; }

footer.foot {
  margin-top: 40px; padding-top: 16px; border-top: 1px solid var(--rule);
  color: var(--gray); font-size: 11px; display: flex;
  justify-content: space-between; gap: 16px; flex-wrap: wrap;
}

@media print {
  nav.tabs, .seg, select.ctl { display: none !important; }
  .panel { display: block !important; page-break-before: always; }
  body { background: #fff; }
}
</style>
</head>
<body>

<header class="hero">
  <div class="hero-inner">
    <div>
      __LOGO_TAG__
      <h1 class="hero-title">Executive Dashboard</h1>
      <p class="hero-sub">Direct-to-Consumer &middot; Distribution &middot; Depletions</p>
    </div>
    <div class="hero-meta">
      <strong>__PERIOD_LABEL__</strong>
      __WEEKLY_META__
      <!-- El JS lo llena solo si hay más de una semana cargada: con una sola
           no se muestra un control que no tiene nada que elegir. -->
      <div class="week-pick" id="weekPickWrap" hidden>
        <label for="weekPick">Week ending</label>
        <select id="weekPick"></select>
      </div>
    </div>
  </div>
  <nav class="tabs" role="tablist" id="tabs"></nav>
</header>

<div class="wrap">
  <section class="panel" id="p-exec" role="tabpanel"></section>
  <section class="panel" id="p-dtc" role="tabpanel"></section>
  <section class="panel" id="p-club" role="tabpanel"></section>
  <section class="panel" id="p-dist" role="tabpanel"></section>
  <section class="panel" id="p-geo" role="tabpanel">
    <div class="sec-head"><span class="sec-num">5</span>
      <h2 class="sec-title">Geographic Distribution &mdash; Club Shipments</h2></div>
    <p class="sec-sub">Where club wine physically ships. Shading is net sales by
      destination state; each dot is a ZIP code, sized by net sales.</p>
    <div class="card map-holder" id="map-holder">__SVG_MAP__</div>
    <div class="grid g2" style="margin-top:16px">
      <div class="card">
        <h3 class="blk">Top destination states</h3>
        <div class="tbl-wrap"><table id="tblStates"></table></div>
      </div>
      <div class="card">
        <h3 class="blk">Top 15 ZIP codes</h3>
        <div class="tbl-wrap"><table id="tblZips"></table></div>
      </div>
    </div>
    <div id="geoNote" style="margin-top:16px"></div>
  </section>
  <section class="panel" id="p-recon" role="tabpanel"></section>

  <footer class="foot">
    <span>Sullivan Rutherford Estate &middot; Executive reporting</span>
    <span>Generated __GENERATED_AT__ &middot; Source: __DATA_NOTE__</span>
  </footer>
</div>

<div id="maptip"></div>

<script>
__CHART_JS__
</script>
<script>
(function () {
  'use strict';

  const D = __REPORT_DATA__;
  const BLANK = '—';
  const T = D.tokens;

  /* -------------------------------------------------------- semana activa
     `D.weekly_series` trae TODAS las semanas encontradas, cada una con su
     payload semanal y con la mezcla de canales y los no clasificados ya
     homologados contra el mensual (se precalculan en Python porque la
     homologación de las dos taxonomías vive en un solo lugar).

     El reporte abre en la semana más reciente. Cambiar de semana repinta los
     bloques que dependen de ella —Executive, DTC y Distribution— y deja
     intactos los que no: el mensual, el mapa y la reconciliación no cambian
     porque no son semanales. */
  const SERIES = D.weekly_series || (D.weekly ? [{
    weekly: D.weekly,
    unified_channels: D.unified_channels,
    unified_unclassified: D.unified_unclassified
  }] : []);
  let weekIdx = SERIES.length ? SERIES.length - 1 : -1;

  /* La cadencia elegida en la mezcla de canales se recuerda. Sin esto, al
     cambiar de semana `renderExec` volvía a pintar 'monthly' y el lector que
     estaba viendo la semanal perdía su selección sin haber pedido nada. */
  let mixCadence = 'monthly';

  function curWeek() { return weekIdx >= 0 ? SERIES[weekIdx].weekly : null; }
  function curChannels() {
    return weekIdx >= 0 ? SERIES[weekIdx].unified_channels : D.unified_channels;
  }
  function curUnclassified() {
    return weekIdx >= 0 ? SERIES[weekIdx].unified_unclassified : (D.unified_unclassified || []);
  }

  // --------------------------------------------------------------- formato
  // Regla del repo: nunca imprimir 'nan'/'null'/'undefined'. Cualquier hueco
  // se pinta como la marca de dato ausente.
  function has(v) {
    if (v === null || v === undefined) return false;
    if (typeof v === 'number') return isFinite(v);
    const s = String(v).trim().toLowerCase();
    return !(s === '' || s === 'nan' || s === 'nat' || s === 'none' ||
             s === 'null' || s === 'undefined' || s === '<na>');
  }
  function txt(v) { return has(v) ? String(v) : BLANK; }
  function money(v, dec) {
    if (!has(v)) return BLANK;
    const n = Number(v);
    if (!isFinite(n)) return BLANK;
    return '$' + n.toLocaleString('en-US', {
      minimumFractionDigits: dec === undefined ? 0 : dec,
      maximumFractionDigits: dec === undefined ? 0 : dec
    });
  }
  function money2(v) { return money(v, 2); }
  function num(v, dec) {
    if (!has(v)) return BLANK;
    const n = Number(v);
    if (!isFinite(n)) return BLANK;
    return n.toLocaleString('en-US', {
      minimumFractionDigits: dec === undefined ? 0 : dec,
      maximumFractionDigits: dec === undefined ? 0 : dec
    });
  }
  function pct(v) { return has(v) ? Number(v).toFixed(1) + '%' : BLANK; }
  function esc(s) {
    return String(s).replace(/[&<>"']/g, c => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[c]));
  }

  // -------------------------------------------------------------- Chart.js
  const hasChart = typeof Chart !== 'undefined';
  const charts = {};

  function baseOpts(horizontal) {
    return {
      indexAxis: horizontal ? 'y' : 'x',
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: 'rgba(0,30,54,.95)',
          padding: 10, cornerRadius: 5,
          titleFont: { family: 'Poppins', size: 12 },
          bodyFont: { family: 'Poppins', size: 12 }
        }
      },
      scales: {
        x: {
          grid: { color: T.grid, drawBorder: false },
          ticks: { font: { family: 'Poppins', size: 11 }, color: T.gray }
        },
        y: {
          grid: { color: T.grid, drawBorder: false },
          ticks: { font: { family: 'Poppins', size: 11 }, color: T.gray }
        }
      }
    };
  }

  function drawBars(id, labels, values, colors, horizontal, fmt) {
    if (!hasChart) return;
    const el = document.getElementById(id);
    if (!el) return;
    if (charts[id]) charts[id].destroy();
    const opts = baseOpts(horizontal);
    opts.plugins.tooltip.callbacks = {
      label: c => ' ' + (fmt === 'cases' ? num(c.parsed[horizontal ? 'x' : 'y'], 2) + ' cs'
                                         : money2(c.parsed[horizontal ? 'x' : 'y']))
    };
    const axis = horizontal ? 'x' : 'y';
    opts.scales[axis].ticks.callback = v => (fmt === 'cases' ? num(v, 0) : money(v));
    charts[id] = new Chart(el, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          data: values,
          backgroundColor: colors,
          borderRadius: 3,
          borderSkipped: false,
          maxBarThickness: 34
        }]
      },
      options: opts
    });
  }

  function chartHost(id, tall) {
    return '<div class="chart-box' + (tall ? ' tall' : '') + '"><canvas id="' +
           id + '"></canvas></div>';
  }
  function noChartNote() {
    return '<p class="empty">Charts unavailable: the embedded chart library did ' +
           'not load. All figures remain in the tables below.</p>';
  }

  // ==========================================================================
  // 1. EXECUTIVE
  // ==========================================================================
  // La mezcla de canales vive AQUÍ y solo aquí: era el bloque que los dos
  // reportes repetían. El selector cambia la cadencia, no el componente.
  function renderExec() {
    const M = D.monthly, W = curWeek(), U = curChannels();
    const rec = M.reconciliation || {};
    let h = '';

    h += '<div class="sec-head"><span class="sec-num">1</span>' +
         '<h2 class="sec-title">Executive Summary</h2></div>' +
         '<p class="sec-sub">One page for both cadences: the month closes the books, ' +
         'the week runs operations.</p>';

    // --- KPIs del mes
    h += '<h3 class="blk">Month &mdash; ' + esc(txt(D.meta.period_label)) + '</h3>';
    h += '<div class="grid g4">';
    h += '<div class="card kpi accent"><p class="kpi-label">Total DTC Net Sales</p>' +
         '<p class="kpi-value">' + money(M.vista_a.total_dtc) + '</p>' +
         '<p class="kpi-note">' + num(M.vista_a.total_orders) + ' unique orders</p></div>';
    const topIdx = 0;
    h += '<div class="card kpi"><p class="kpi-label">Leading Channel</p>' +
         '<p class="kpi-value" style="font-size:19px">' +
         esc(txt(M.vista_a.categories[topIdx])) + '</p>' +
         '<p class="kpi-note">' + money(M.vista_a.subtotal[topIdx]) + ' &middot; ' +
         pct(M.vista_a.pct[topIdx]) + ' of net sales</p></div>';

    if (rec.net_sales_financial !== null && rec.net_sales_financial !== undefined) {
      const ok = rec.match === true;
      h += '<div class="card kpi"><p class="kpi-label">Financial Reconciliation</p>' +
           '<p class="kpi-value" style="font-size:19px">' +
           (ok ? 'Balanced' : money2(rec.difference) + ' gap') + '</p>' +
           '<p class="kpi-note"><span class="badge ' + (ok ? 'ok' : 'bad') + '">' +
           (ok ? 'Exact to the cent' : 'Review required') + '</span></p></div>';
    } else {
      h += '<div class="card kpi"><p class="kpi-label">Financial Reconciliation</p>' +
           '<p class="kpi-value" style="font-size:19px">' + BLANK + '</p>' +
           '<p class="kpi-note">No financial report supplied</p></div>';
    }

    const dg = M.diagnostics || {};
    const unclCls = (dg.unclassified_rows > 0) ? ' warn' : '';
    h += '<div class="card kpi' + unclCls + '"><p class="kpi-label">Unclassified</p>' +
         '<p class="kpi-value">' + money(dg.unclassified_subtotal) + '</p>' +
         '<p class="kpi-note">' + num(dg.unclassified_rows) + ' line(s) the cascade ' +
         'could not assign</p></div>';
    h += '</div>';

    // --- KPIs de la semana
    if (W) {
      const K = W.kpis || {};
      h += '<h3 class="blk" style="margin-top:26px">Week &mdash; ' +
           esc(txt(W.period_label)) + '</h3>';
      h += '<div class="grid g4">';
      h += '<div class="card kpi accent"><p class="kpi-label">Total DTC Sales</p>' +
           '<p class="kpi-value">' + money(K.total_dtc_sales) + '</p>' +
           '<p class="kpi-note">' + esc(txt(W.week_label)) + '</p></div>';
      h += '<div class="card kpi"><p class="kpi-label">Cash Received</p>' +
           '<p class="kpi-value">' + money(K.cash_received) + '</p>' +
           '<p class="kpi-note">Paid distribution invoices</p></div>';
      h += '<div class="card kpi"><p class="kpi-label">Open PO Balance</p>' +
           '<p class="kpi-value">' + money(K.total_open_pos_amount) + '</p>' +
           '<p class="kpi-note">' + num(K.open_invoices_count) + ' invoice(s) &middot; ' +
           num(K.total_open_cases, 0) + ' cs</p></div>';
      const od = Number(K.overdue_30_amount) || 0;
      h += '<div class="card kpi' + (od > 0 ? ' warn' : '') +
           '"><p class="kpi-label">Overdue &gt; 30 Days</p>' +
           '<p class="kpi-value">' + money(K.overdue_30_amount) + '</p>' +
           '<p class="kpi-note">' + (od > 0
              ? esc(txt(K.overdue_30_customer)) + ' &middot; ' + num(K.overdue_30_aging) + 'd'
              : 'Nothing past terms') + '</p></div>';
      h += '</div>';
    }

    // --- Mezcla de canales unificada (el bloque deduplicado)
    h += '<div class="sec-head" style="margin-top:34px"><span class="sec-num">1b</span>' +
         '<h2 class="sec-title">Channel Mix</h2></div>' +
         '<p class="sec-sub">Both cadences share one channel taxonomy, so this is a ' +
         'single view with a cadence switch instead of two separate charts.</p>';
    h += '<div class="card">';
    h += '<div class="ctl-row"><h3 class="blk" style="margin:0" id="mixTitle"></h3>' +
         '<div class="seg" id="mixSeg">' +
         '<button data-cad="monthly" aria-pressed="' + (mixCadence !== 'weekly') + '">Monthly</button>' +
         (W ? '<button data-cad="weekly" aria-pressed="' + (mixCadence === 'weekly') + '">Weekly</button>' : '') +
         '</div></div>';
    h += hasChart ? chartHost('chMix', true) : noChartNote();
    h += '<div class="tbl-wrap" style="margin-top:18px"><table id="tblMix"></table></div>';
    h += '</div>';

    document.getElementById('p-exec').innerHTML = h;

    const seg = document.getElementById('mixSeg');
    seg.addEventListener('click', e => {
      const b = e.target.closest('button');
      if (!b) return;
      seg.querySelectorAll('button').forEach(x =>
        x.setAttribute('aria-pressed', String(x === b)));
      mixCadence = b.dataset.cad;
      paintMix(mixCadence);
    });
    // Sin semanal cargado no hay a qué volver: la cadencia cae a mensual.
    if (!W) mixCadence = 'monthly';
    paintMix(mixCadence);
  }

  function paintMix(cadence) {
    const U = curChannels();
    const key = cadence === 'weekly' ? 'weekly' : 'monthly';
    const rows = U.rows.filter(r => r[key] !== null && r[key] !== undefined);
    // Reordenar por la cadencia visible: la regla de barras descendentes
    // aplica a la serie que se está pintando, no a la otra.
    rows.sort((a, b) => b[key] - a[key]);

    document.getElementById('mixTitle').textContent =
      (cadence === 'weekly' ? 'Weekly' : 'Monthly') + ' net sales by channel';

    drawBars('chMix', rows.map(r => r.channel), rows.map(r => r[key]),
             rows.map(r => r.color), true, 'money');

    // La tabla siempre muestra AMBAS columnas: es lo que hace visible que las
    // dos cadencias hablan de los mismos canales.
    const total = { monthly: U.monthly_total, weekly: U.weekly_total };
    let t = '<thead><tr><th>Channel</th><th class="num">Month</th>' +
            '<th class="num">Share</th><th class="num">Week</th>' +
            '<th class="num">Share</th></tr></thead><tbody>';
    U.rows.forEach(r => {
      const mp = (has(r.monthly) && total.monthly) ? (r.monthly / total.monthly * 100) : null;
      const wp = (has(r.weekly) && total.weekly) ? (r.weekly / total.weekly * 100) : null;
      t += '<tr><td><span class="swatch" style="background:' + esc(r.color) + '"></span>' +
           esc(r.channel) + '</td>' +
           '<td class="num">' + money2(r.monthly) + '</td>' +
           '<td class="num muted">' + pct(mp) + '</td>' +
           '<td class="num">' + money2(r.weekly) + '</td>' +
           '<td class="num muted">' + pct(wp) + '</td></tr>';
    });
    t += '<tr class="total-row"><td>Total</td>' +
         '<td class="num">' + money2(total.monthly) + '</td><td class="num"></td>' +
         '<td class="num">' + money2(total.weekly) + '</td><td class="num"></td></tr>';
    t += '</tbody>';
    document.getElementById('tblMix').innerHTML = t;
  }

  // ==========================================================================
  // 2. DTC & CASCADE
  // ==========================================================================
  function renderDtc() {
    const M = D.monthly;
    let h = '';
    h += '<div class="sec-head"><span class="sec-num">2</span>' +
         '<h2 class="sec-title">DTC Detail &mdash; 9-Priority Cascade</h2></div>' +
         '<p class="sec-sub">Every order line lands in exactly one category. ' +
         'The cascade is evaluated in order, so no line can be counted twice.</p>';

    h += '<div class="card">';
    h += '<div class="ctl-row"><h3 class="blk" style="margin:0">Net sales by final category</h3>' +
         '<label style="font-size:12px;color:var(--gray)">Channel ' +
         '<select class="ctl" id="chanSel"></select></label></div>';
    h += hasChart ? chartHost('chCat', true) : noChartNote();
    h += '<div class="tbl-wrap" style="margin-top:18px"><table id="tblCat"></table></div>';
    h += '</div>';

    h += '<div class="sec-head"><span class="sec-num">2b</span>' +
         '<h2 class="sec-title">Category Definitions</h2></div>' +
         '<p class="sec-sub">What each bucket means, in the order the cascade ' +
         'evaluates them.</p>';
    h += '<div class="card"><div class="tbl-wrap"><table><thead><tr>' +
         '<th style="width:34px" class="num">#</th><th>Category</th>' +
         '<th>Definition</th></tr></thead><tbody>';
    (M.glossary || []).forEach((g, i) => {
      const isDiag = (D.diagnostic_categories || []).indexOf(g.name) >= 0;
      h += '<tr><td class="num muted">' + (isDiag ? BLANK : (i + 1)) + '</td>' +
           '<td><span class="swatch" style="background:' +
           esc(M.category_colors[g.name] || T.gray) + '"></span>' + esc(g.name) +
           (isDiag ? ' <span class="badge info">diagnostic</span>' : '') + '</td>' +
           '<td class="muted">' + esc(g.desc) + '</td></tr>';
    });
    h += '</tbody></table></div></div>';

    document.getElementById('p-dtc').innerHTML = h;

    const byCh = M.vista_a_by_channel || {};
    const sel = document.getElementById('chanSel');
    const names = Object.keys(byCh).sort((a, b) =>
      (byCh[b].total_dtc || 0) - (byCh[a].total_dtc || 0));
    sel.innerHTML = '<option value="">All channels</option>' +
      names.map(n => '<option value="' + esc(n) + '">' + esc(n) + '</option>').join('');
    sel.addEventListener('change', () => paintCat(sel.value));
    paintCat('');
  }

  function paintCat(channel) {
    const M = D.monthly;
    const v = channel ? (M.vista_a_by_channel || {})[channel] : M.vista_a;
    if (!v) return;
    // Se filtran los ceros para que el eje no se llene de barras invisibles;
    // el total de la tabla sigue siendo el total completo.
    const idx = v.categories.map((c, i) => i).filter(i => Number(v.subtotal[i]) !== 0);
    drawBars('chCat', idx.map(i => v.categories[i]), idx.map(i => v.subtotal[i]),
             idx.map(i => v.colors[i]), true, 'money');

    let t = '<thead><tr><th>Category</th><th class="num">Orders</th>' +
            '<th class="num">Net Sales</th><th class="num">Share</th>' +
            '<th class="num">Avg / Order</th></tr></thead><tbody>';
    v.categories.forEach((c, i) => {
      const o = Number(v.orders[i]) || 0;
      const s = Number(v.subtotal[i]) || 0;
      t += '<tr><td><span class="swatch" style="background:' + esc(v.colors[i]) +
           '"></span>' + esc(c) + '</td>' +
           '<td class="num">' + num(o) + '</td>' +
           '<td class="num">' + money2(s) + '</td>' +
           '<td class="num muted">' + pct(v.pct[i]) + '</td>' +
           '<td class="num muted">' + (o ? money2(s / o) : BLANK) + '</td></tr>';
    });
    t += '<tr class="total-row"><td>Total</td><td class="num">' +
         num(v.total_orders) + '</td><td class="num">' + money2(v.total_dtc) +
         '</td><td class="num">100.0%</td><td class="num">' +
         (v.total_orders ? money2(v.total_dtc / v.total_orders) : BLANK) +
         '</td></tr></tbody>';
    document.getElementById('tblCat').innerHTML = t;
  }

  // ==========================================================================
  // 3. CLUB
  // ==========================================================================
  // El minimapa que el mensual repetía aquí se quitó: era el mismo de la
  // pestaña Geographic.
  function renderClub() {
    const B = D.monthly.vista_b;
    let h = '';
    h += '<div class="sec-head"><span class="sec-num">3</span>' +
         '<h2 class="sec-title">Club Deep Dive</h2></div>' +
         '<p class="sec-sub">Estate versus Founder’s, broken out by package. ' +
         'Club is where the shipping logistics live, so it drives the geographic view.</p>';

    const est = Number(B.estate_total) || 0;
    const fdr = Number(B.founders_total) || 0;
    const tot = est + fdr;
    h += '<div class="grid g3">';
    h += '<div class="card kpi accent"><p class="kpi-label">Total Club Net Sales</p>' +
         '<p class="kpi-value">' + money(tot) + '</p>' +
         '<p class="kpi-note">' + num((B.orders || []).reduce((a, b) => a + Number(b || 0), 0)) +
         ' shipments across ' + num((B.packages || []).length) + ' packages</p></div>';
    h += '<div class="card kpi"><p class="kpi-label">Founder’s Club</p>' +
         '<p class="kpi-value">' + money(fdr) + '</p>' +
         '<p class="kpi-note">' + (tot ? pct(fdr / tot * 100) : BLANK) + ' of club</p></div>';
    h += '<div class="card kpi"><p class="kpi-label">Estate Club</p>' +
         '<p class="kpi-value">' + money(est) + '</p>' +
         '<p class="kpi-note">' + (tot ? pct(est / tot * 100) : BLANK) + ' of club</p></div>';
    h += '</div>';

    h += '<div class="card" style="margin-top:16px">' +
         '<h3 class="blk">Net sales by package</h3>' +
         (hasChart ? chartHost('chPkg') : noChartNote()) +
         '<div class="tbl-wrap" style="margin-top:18px"><table id="tblPkg"></table></div>' +
         '</div>';

    document.getElementById('p-club').innerHTML = h;

    const idx = (B.packages || []).map((p, i) => i)
      .filter(i => Number(B.subtotal[i]) !== 0);
    drawBars('chPkg', idx.map(i => B.packages[i]), idx.map(i => B.subtotal[i]),
             idx.map(i => B.colors[i]), false, 'money');

    let t = '<thead><tr><th>Package</th><th class="num">Shipments</th>' +
            '<th class="num">Net Sales</th><th class="num">Avg Order Value</th>' +
            '</tr></thead><tbody>';
    (B.packages || []).forEach((p, i) => {
      t += '<tr><td><span class="swatch" style="background:' + esc(B.colors[i]) +
           '"></span>' + esc(p) + '</td>' +
           '<td class="num">' + num(B.orders[i]) + '</td>' +
           '<td class="num">' + money2(B.subtotal[i]) + '</td>' +
           '<td class="num muted">' + money2(B.aov[i]) + '</td></tr>';
    });
    t += '</tbody>';
    document.getElementById('tblPkg').innerHTML = t;
  }

  // ==========================================================================
  // 4. DISTRIBUTION (exclusivo de la cadencia semanal)
  // ==========================================================================
  function renderDist() {
    const W = curWeek();
    const host = document.getElementById('p-dist');
    if (!W) {
      host.innerHTML =
        '<div class="sec-head"><span class="sec-num">4</span>' +
        '<h2 class="sec-title">Distribution &amp; Depletions</h2></div>' +
        '<p class="empty">No weekly data was supplied, so distribution ' +
        'receivables and depletions are not part of this report.</p>';
      return;
    }
    const K = W.kpis || {};
    let h = '';
    h += '<div class="sec-head"><span class="sec-num">4</span>' +
         '<h2 class="sec-title">Distribution Receivables</h2></div>' +
         '<p class="sec-sub">Open invoices by age. Standard terms are net 30 days, ' +
         'so anything past 30 is money that should already be in the bank.</p>';

    h += '<div class="grid g2"><div class="card">' +
         '<h3 class="blk">Open balance by age bracket</h3>' +
         (hasChart ? chartHost('chAge') : noChartNote()) + '</div>';
    h += '<div class="card"><h3 class="blk">Invoices past 30 days</h3>' +
         '<div class="tbl-wrap"><table id="tblOverdue"></table></div></div></div>';

    h += '<div class="sec-head"><span class="sec-num">4b</span>' +
         '<h2 class="sec-title">Depletions</h2></div>' +
         '<p class="sec-sub">Sell-through in 9-litre cases: what distributors ' +
         'actually moved out to accounts, not what was shipped to them. ' +
         'Period: ' + esc(txt(K.depletions_period)) + '.</p>';

    h += '<div class="grid g3">';
    h += '<div class="card kpi accent"><p class="kpi-label">Depletions Volume</p>' +
         '<p class="kpi-value">' + num(K.depletions_9l_cases, 2) + ' cs</p>' +
         '<p class="kpi-note">9L equivalent</p></div>';
    const live = (W.depletions_by_state || []).filter(s => s.live);
    h += '<div class="card kpi"><p class="kpi-label">States Reporting</p>' +
         '<p class="kpi-value">' + num(live.length) + '</p>' +
         '<p class="kpi-note">of ' + num((W.depletions_by_state || []).length) +
         ' markets tracked</p></div>';
    const topState = live.length ? live[0] : null;
    h += '<div class="card kpi"><p class="kpi-label">Leading State</p>' +
         '<p class="kpi-value" style="font-size:19px">' +
         (topState ? esc(topState.state) : BLANK) + '</p>' +
         '<p class="kpi-note">' + (topState ? num(topState.cases, 2) + ' cs' : BLANK) +
         '</p></div>';
    h += '</div>';

    h += '<div class="grid g2" style="margin-top:16px">';
    h += '<div class="card"><h3 class="blk">By state</h3>' +
         (hasChart ? chartHost('chState') : noChartNote()) +
         '<div class="tbl-wrap" style="margin-top:18px"><table id="tblState"></table></div>' +
         '</div>';
    h += '<div class="card"><h3 class="blk">By distributor</h3>' +
         (hasChart ? chartHost('chDist') : noChartNote()) +
         '<div class="tbl-wrap" style="margin-top:18px"><table id="tblDist"></table></div>' +
         '</div>';
    h += '</div>';

    host.innerHTML = h;

    // --- aging
    const ag = W.po_aging || [];
    const agColors = ag.map(b => b.status === 'critical' ? T.neg
                              : (b.status === 'warn' ? T.tan : T.navy));
    drawBars('chAge', ag.map(b => b.bucket), ag.map(b => b.amount),
             agColors, false, 'money');

    // --- vencidos
    const ov = W.overdue_details || [];
    if (!ov.length) {
      document.getElementById('tblOverdue').outerHTML =
        '<p class="empty">Nothing past terms this week.</p>';
    } else {
      let t = '<thead><tr><th>Invoice</th><th>Customer</th><th>Market</th>' +
              '<th class="num">Age</th><th class="num">Balance</th>' +
              '</tr></thead><tbody>';
      ov.forEach(r => {
        t += '<tr><td>' + esc(txt(r.invoice)) + '</td>' +
             '<td>' + esc(txt(r.customer)) + '</td>' +
             '<td class="muted">' + esc(txt(r.market)) + '</td>' +
             '<td class="num">' + num(r.aging) + 'd</td>' +
             '<td class="num" style="color:' + T.neg + ';font-weight:600">' +
             money2(r.balance) + '</td></tr>';
      });
      t += '</tbody>';
      document.getElementById('tblOverdue').innerHTML = t;
    }

    // --- depletions por estado (solo los que reportan entran a la gráfica)
    const st = (W.depletions_by_state || []).filter(s => s.live && Number(s.cases) > 0);
    drawBars('chState', st.map(s => s.state), st.map(s => s.cases),
             st.map(() => T.navy), false, 'cases');
    let ts = '<thead><tr><th>State</th><th class="num">9L Cases</th>' +
             '<th>Feed</th></tr></thead><tbody>';
    (W.depletions_by_state || []).forEach(s => {
      ts += '<tr><td>' + esc(txt(s.state)) + '</td>' +
            '<td class="num">' + num(s.cases, 2) + '</td>' +
            '<td>' + (s.live ? '<span class="badge ok">live</span>'
                             : '<span class="badge info">no feed</span>') +
            '</td></tr>';
    });
    ts += '</tbody>';
    document.getElementById('tblState').innerHTML = ts;

    // --- depletions por distribuidor
    const ds = (W.depletions_by_distributor || []).filter(d => has(d.cases));
    drawBars('chDist', ds.map(d => d.distributor), ds.map(d => d.cases),
             ds.map(d => d.live ? T.navy : T.gray), false, 'cases');
    let td = '<thead><tr><th>Distributor</th><th class="num">9L Cases</th>' +
             '<th>Note</th></tr></thead><tbody>';
    (W.depletions_by_distributor || []).forEach(d => {
      td += '<tr><td>' + esc(txt(d.distributor)) + '</td>' +
            '<td class="num">' + num(d.cases, 2) + '</td>' +
            '<td class="muted">' + esc(txt(d.note)) + '</td></tr>';
    });
    td += '</tbody>';
    document.getElementById('tblDist').innerHTML = td;
  }

  // ==========================================================================
  // 5. GEOGRAPHIC
  // ==========================================================================
  function renderGeo() {
    const G = D.monthly.geo || {};
    let ts = '<thead><tr><th>State</th><th class="num">Shipments</th>' +
             '<th class="num">Net Sales</th></tr></thead><tbody>';
    (G.states || []).slice(0, 15).forEach((s, i) => {
      ts += '<tr><td>' + esc(txt(s)) + '</td>' +
            '<td class="num">' + num(G.state_orders[i]) + '</td>' +
            '<td class="num">' + money2(G.state_subtotal[i]) + '</td></tr>';
    });
    ts += '</tbody>';
    document.getElementById('tblStates').innerHTML = ts;

    const zh = document.getElementById('tblZips');
    if (!(G.zips || []).length) {
      zh.outerHTML = '<p class="empty">' + (G.has_zip_columns
        ? 'No club shipment carried a usable ZIP code this period.'
        : 'This export has no ZIP code column, so the map is drawn at state level only.') +
        '</p>';
    } else {
      let tz = '<thead><tr><th>ZIP</th><th class="num">Shipments</th>' +
               '<th class="num">Net Sales</th><th>On map</th></tr></thead><tbody>';
      const plotted = {};
      (G.zip_points || []).forEach(p => { plotted[p.zip] = true; });
      (G.zips || []).forEach((z, i) => {
        tz += '<tr><td>' + esc(txt(z)) + '</td>' +
              '<td class="num">' + num(G.zip_orders[i]) + '</td>' +
              '<td class="num">' + money2(G.zip_subtotal[i]) + '</td>' +
              '<td>' + (plotted[z] ? '<span class="badge ok">plotted</span>'
                                   : '<span class="badge info">no centroid</span>') +
              '</td></tr>';
      });
      tz += '</tbody>';
      zh.innerHTML = tz;
    }

    let note = '';
    if (Number(G.unresolved_rows) > 0) {
      note += '<div class="note">' + num(G.unresolved_rows) + ' club line(s) worth ' +
              money2(G.unresolved_subtotal) + ' carry no usable destination state, ' +
              'so they are absent from the map. They <strong>are</strong> included in ' +
              'total club net sales of ' + money2(G.club_total) + ', which is why the ' +
              'mapped total (' + money2(G.mapped_subtotal) + ') is lower.</div>';
    }
    if ((G.unresolved_zips || []).length) {
      note += '<div class="note" style="margin-top:10px">' +
              num(G.unresolved_zips.length) + ' ZIP code(s) have no centroid in the ' +
              'reference table, so they appear in the table but not as dots: ' +
              esc(G.unresolved_zips.join(', ')) + '.</div>';
    }
    document.getElementById('geoNote').innerHTML = note;
    wireMap(G);
  }

  function wireMap(G) {
    const tip = document.getElementById('maptip');
    const holder = document.getElementById('map-holder');
    if (!holder || !tip) return;

    function show(e, html) {
      tip.innerHTML = html;
      tip.style.opacity = '1';
      move(e);
    }
    function move(e) {
      const pad = 14;
      let x = e.clientX + pad, y = e.clientY + pad;
      const r = tip.getBoundingClientRect();
      if (x + r.width > window.innerWidth) x = e.clientX - r.width - pad;
      if (y + r.height > window.innerHeight) y = e.clientY - r.height - pad;
      tip.style.left = x + 'px';
      tip.style.top = y + 'px';
    }
    function hide() { tip.style.opacity = '0'; }

    const byState = {};
    (G.states || []).forEach((s, i) => {
      byState[s] = { orders: G.state_orders[i], subtotal: G.state_subtotal[i] };
    });

    holder.querySelectorAll('path[data-code]').forEach(p => {
      const code = p.getAttribute('data-code');
      p.style.cursor = 'pointer';
      p.addEventListener('mouseenter', e => {
        const d = byState[code];
        show(e, '<b>' + esc(code) + '</b><br>' + (d
          ? num(d.orders) + ' shipment(s)<br>' + money2(d.subtotal)
          : 'No club shipments'));
      });
      p.addEventListener('mousemove', move);
      p.addEventListener('mouseleave', hide);
    });

    holder.querySelectorAll('circle[data-zip]').forEach(c => {
      c.style.cursor = 'pointer';
      c.addEventListener('mouseenter', e => {
        show(e, '<b>ZIP ' + esc(c.getAttribute('data-zip')) + '</b><br>' +
             num(c.getAttribute('data-orders')) + ' shipment(s)<br>' +
             money2(c.getAttribute('data-subtotal')));
      });
      c.addEventListener('mousemove', move);
      c.addEventListener('mouseleave', hide);
    });
  }

  // ==========================================================================
  // 6. RECONCILIATION & DIAGNOSTICS
  // ==========================================================================
  function renderRecon() {
    const M = D.monthly;
    const rec = M.reconciliation || {};
    const dg = M.diagnostics || {};
    let h = '';
    h += '<div class="sec-head"><span class="sec-num">6</span>' +
         '<h2 class="sec-title">Reconciliation</h2></div>' +
         '<p class="sec-sub">The month’s DTC total measured against the ' +
         'financial report, to the cent.</p>';

    if (rec.net_sales_financial === null || rec.net_sales_financial === undefined) {
      h += '<div class="card"><p class="empty">No financial report was supplied, ' +
           'so this period was not reconciled.</p></div>';
    } else {
      const ok = rec.match === true;
      h += '<div class="card"><div class="tbl-wrap"><table><thead><tr>' +
           '<th>Measure</th><th>Basis</th><th class="num">Amount</th>' +
           '</tr></thead><tbody>';
      h += '<tr><td>DTC net sales (transactional)</td><td class="muted">' +
           esc(txt(rec.sales_basis)) + '</td><td class="num">' +
           money2(rec.total_dtc) + '</td></tr>';
      h += '<tr><td>Net sales (financial report)</td><td class="muted">' +
           esc(txt(rec.financial_basis)) + '</td><td class="num">' +
           money2(rec.net_sales_financial) + '</td></tr>';
      h += '<tr class="total-row"><td>Difference</td><td>' +
           '<span class="badge ' + (ok ? 'ok' : 'bad') + '">' +
           (ok ? 'Exact to the cent' : 'Review required') + '</span></td>' +
           '<td class="num">' + money2(rec.difference) + '</td></tr>';
      h += '</tbody></table></div></div>';
    }

    h += '<div class="sec-head"><span class="sec-num">6b</span>' +
         '<h2 class="sec-title">Unclassified</h2></div>' +
         '<p class="sec-sub">Lines the cascade could not assign. They are counted in ' +
         'every total so the books still balance — listing them here is what makes ' +
         'them fixable at the source.</p>';

    h += '<div class="grid g3">';
    h += '<div class="card kpi' + (dg.unclassified_rows > 0 ? ' warn' : '') +
         '"><p class="kpi-label">Total Unclassified (Month)</p>' +
         '<p class="kpi-value">' + money2(dg.unclassified_subtotal) + '</p>' +
         '<p class="kpi-note">' + num(dg.unclassified_rows) + ' line(s)</p></div>';
    h += '<div class="card kpi"><p class="kpi-label">Club, No Program Named</p>' +
         '<p class="kpi-value">' + money2(dg.club_no_program_subtotal) + '</p>' +
         '<p class="kpi-note">' + num(dg.club_no_program_rows) +
         ' line(s) &middot; check Club Title / Club Package</p></div>';
    h += '<div class="card kpi"><p class="kpi-label">Channel Not Recognized</p>' +
         '<p class="kpi-value">' + money2(dg.unknown_channel_subtotal) + '</p>' +
         '<p class="kpi-note">' + num(dg.unknown_channel_rows) +
         ' line(s) &middot; check Channel</p></div>';
    h += '</div>';

    const rows = curUnclassified() || [];
    h += '<div class="card" style="margin-top:16px">' +
         '<h3 class="blk">Every unassigned order, both cadences</h3>';
    if (!rows.length) {
      h += '<p class="empty">Nothing unclassified in this period. Every order line ' +
           'matched a category.</p>';
    } else {
      h += '<div class="tbl-wrap"><table><thead><tr><th>Cadence</th><th>Order</th>' +
           '<th>Date</th><th>Channel</th><th>Package</th><th>Title</th>' +
           '<th>Reason</th><th class="num">Net Sales</th></tr></thead><tbody>';
      rows.forEach(r => {
        h += '<tr><td><span class="badge ' + (r.cadence === 'Weekly' ? 'wk' : 'mo') +
             '">' + esc(r.cadence) + '</span></td>' +
             '<td>' + esc(txt(r.order)) + '</td>' +
             '<td class="muted">' + esc(txt(r.date)) + '</td>' +
             '<td class="muted">' + esc(txt(r.channel)) + '</td>' +
             '<td class="muted">' + esc(txt(r.package)) + '</td>' +
             '<td class="muted">' + esc(txt(r.title)) + '</td>' +
             '<td class="muted">' + esc(txt(r.reason)) + '</td>' +
             '<td class="num">' + esc(txt(r.amount_text)) + '</td></tr>';
      });
      h += '</tbody></table></div>';
    }
    h += '</div>';

    document.getElementById('p-recon').innerHTML = h;
  }

  // ==========================================================================
  // PESTAÑAS
  // ==========================================================================
  const TABS = [
    { id: 'p-exec',  label: 'Executive',       num: '1' },
    { id: 'p-dtc',   label: 'DTC & Cascade',   num: '2' },
    { id: 'p-club',  label: 'Club',            num: '3' },
    { id: 'p-dist',  label: 'Distribution',    num: '4' },
    { id: 'p-geo',   label: 'Geographic',      num: '5' },
    { id: 'p-recon', label: 'Reconciliation',  num: '6' }
  ];

  function buildTabs() {
    const nav = document.getElementById('tabs');
    nav.innerHTML = TABS.map((t, i) =>
      '<button role="tab" data-target="' + t.id + '" aria-selected="' +
      (i === 0) + '"><span class="tnum">' + t.num + '</span>' + t.label +
      '</button>').join('');
    nav.addEventListener('click', e => {
      const b = e.target.closest('button');
      if (!b) return;
      show(b.dataset.target);
    });
  }

  function show(id) {
    document.querySelectorAll('.panel').forEach(p =>
      p.classList.toggle('is-active', p.id === id));
    document.querySelectorAll('#tabs button').forEach(b =>
      b.setAttribute('aria-selected', String(b.dataset.target === id)));
    // Chart.js mide el contenedor al crearse; un canvas creado dentro de un
    // panel oculto nace con 0 px de alto. Al mostrar la pestaña se reajusta.
    Object.keys(charts).forEach(k => { try { charts[k].resize(); } catch (e) {} });
  }

  /* Solo estos tres bloques dependen de la semana. El mensual, el mapa y la
     reconciliación no se repintan porque no cambian: repintarlos costaría
     tiempo y podría reordenar el mapa sin motivo. */
  const WEEK_DEPENDENT = [['Executive', renderExec], ['DTC', renderDtc],
                          ['Distribution', renderDist]];

  function paintBlocks(blocks) {
    // Cada bloque se pinta aislado: si uno falla, los demás siguen sirviendo.
    blocks.forEach(([name, fn]) => {
      try { fn(); } catch (err) { console.error('Block failed: ' + name, err); }
    });
  }

  function selectWeek(idx) {
    if (idx < 0 || idx >= SERIES.length) return;
    weekIdx = idx;
    const pick = document.getElementById('weekPick');
    if (pick) pick.selectedIndex = idx;
    paintBlocks(WEEK_DEPENDENT);
  }

  function buildWeekPicker() {
    const wrap = document.getElementById('weekPickWrap');
    const pick = document.getElementById('weekPick');
    if (!wrap || !pick) return;
    // Con una sola semana el control se queda oculto: un desplegable de un
    // solo renglón sugiere que hay algo que elegir cuando no lo hay.
    if (SERIES.length < 2) return;
    wrap.hidden = false;
    SERIES.forEach((entry, i) => {
      const w = entry.weekly || {};
      const opt = document.createElement('option');
      opt.value = String(i);
      opt.textContent = (w.week_label || ('#' + (i + 1))) +
                        (w.date_closing ? ' (' + w.date_closing + ')' : '');
      pick.appendChild(opt);
    });
    pick.selectedIndex = weekIdx;
    pick.addEventListener('change', e => selectWeek(Number(e.target.value)));
  }

  function boot() {
    buildTabs();
    buildWeekPicker();
    paintBlocks([['Executive', renderExec], ['DTC', renderDtc], ['Club', renderClub],
                 ['Distribution', renderDist], ['Geographic', renderGeo],
                 ['Reconciliation', renderRecon]]);
    show('p-exec');
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
</script>
</body>
</html>
"""


def generate_unified_dashboard(order_sales_path: str | Path,
                               financial_report_path: str | Path | None,
                               weekly_data_dir: str | Path | None,
                               output_path: str | Path,
                               period_label: str,
                               tock_basis: str = "net_receivable",
                               lang: str = i18n.DEFAULT_LANG) -> Path:
    """
    Construye el dashboard unificado.

    `weekly_data_dir` es opcional: sin él el reporte sale completo en su parte
    mensual y la pestaña de distribución explica que no hubo datos semanales,
    en vez de mostrar ceros que parecerían reales.
    """
    # ------------------------------------------------------------- mensual
    df = load_data_file(order_sales_path)
    df = classify_orders(df)
    amt_col = money_col(df)
    df[amt_col] = coerce_money(df[amt_col])

    unc = df["Final Category"] == UNCLASSIFIED
    reason = df.get("Unclassified Reason")
    if reason is None:
        import pandas as pd
        reason = pd.Series("", index=df.index)
    reason = reason.fillna("")
    club_no_prog = unc & (reason == REASON_CLUB_NO_PROGRAM)
    bad_channel = unc & (reason == REASON_UNKNOWN_CHANNEL)
    diagnostics = {
        "unclassified_rows": int(unc.sum()),
        "unclassified_subtotal": round(float(df.loc[unc, amt_col].sum()), 2),
        "club_no_program_rows": int(club_no_prog.sum()),
        "club_no_program_subtotal": round(float(df.loc[club_no_prog, amt_col].sum()), 2),
        "unknown_channel_rows": int(bad_channel.sum()),
        "unknown_channel_subtotal": round(float(df.loc[bad_channel, amt_col].sum()), 2),
    }
    if diagnostics["unclassified_rows"]:
        warn(f"{diagnostics['unclassified_rows']} renglones en '{UNCLASSIFIED}' "
             f"(${diagnostics['unclassified_subtotal']:,.2f}): "
             f"{diagnostics['club_no_program_rows']} de Club sin programa, "
             f"{diagnostics['unknown_channel_rows']} con canal no reconocido.")

    vista_a = build_vista_a(df)
    vista_b = build_vista_b(df)
    geo = build_geo(df)
    reconciliation = build_reconciliation(
        vista_a, str(financial_report_path) if financial_report_path else None, amt_col)

    # -------------------------------------------------------------- semanal
    # Se procesan TODAS las semanas que haya bajo la carpeta. La parte semanal
    # del reporte abre en la más reciente y el selector del encabezado permite
    # moverse por la serie.
    weekly = None
    weekly_series = None
    if weekly_data_dir:
        weekly_dir = Path(weekly_data_dir)
        if weekly_dir.exists():
            try:
                weekly_series = process_sullivan_weekly_series(
                    weekly_dir, tock_basis=tock_basis)
                weekly = weekly_series[-1]
            except FileNotFoundError as exc:
                warn(f"No se pudo leer ninguna semana en {weekly_dir}: {exc} "
                     "El reporte sale solo con la parte mensual y lo declara.")
        else:
            warn(f"No existe la carpeta semanal {weekly_dir}: el reporte sale solo "
                 "con la parte mensual y lo declara en la pestaña de distribución.")

    # La homologación de las dos taxonomías de canal se precalcula POR SEMANA
    # aquí, y no en el navegador, para que siga viviendo en un solo lugar: el
    # HTML y el PDF consumen exactamente la misma función.
    series_payload = None
    if weekly_series:
        series_payload = [
            {
                "weekly": wk,
                "unified_channels": build_unified_channels(vista_a, wk),
                "unified_unclassified": build_unified_unclassified(vista_b, wk),
            }
            for wk in weekly_series
        ]

    payload = {
        "meta": {
            "period_label": period_label,
            "weekly_period_label": weekly["period_label"] if weekly else None,
            "generated_at": datetime.now().isoformat(),
        },
        "tokens": {
            "navy": TOKENS["brand_navy"], "gray": TOKENS["brand_gray"],
            "tan": TOKENS["brand_tan"], "cream": TOKENS["brand_cream"],
            "grid": TOKENS["chart_grid"], "neg": TOKENS["neg_value"],
        },
        "monthly": {
            "vista_a": vista_a,
            "vista_a_by_channel": build_vista_a_by_channel(df),
            "vista_b": vista_b,
            "geo": geo,
            "reconciliation": reconciliation,
            "diagnostics": diagnostics,
            "glossary": [{"name": n, "desc": t} for n, t in CATEGORY_GLOSSARY],
            "category_colors": CATEGORY_COLORS,
        },
        "weekly": weekly,
        "weekly_series": series_payload,
        "unified_channels": build_unified_channels(vista_a, weekly),
        "unified_unclassified": build_unified_unclassified(vista_b, weekly),
        "diagnostic_categories": [UNCLASSIFIED],
    }

    logo_uri = logo_white_data_uri()
    logo_tag = (f'<img src="{logo_uri}" class="hero-logo" '
                f'alt="Sullivan Rutherford Estate" />') if logo_uri else ""

    weekly_meta = ""
    if weekly:
        weekly_meta = (f"Week: {weekly['period_label']}<br>"
                       f"Cutoff {weekly.get('date_closing') or BLANK}")
    else:
        weekly_meta = "Monthly cadence only"

    replacements = {
        "__PAGE_TITLE__": f"Sullivan Rutherford Estate — Executive Dashboard ({period_label})",
        "__FONT_FACES__": font_face_css(),
        "__LOGO_TAG__": logo_tag,
        "__PERIOD_LABEL__": period_label,
        "__WEEKLY_META__": weekly_meta,
        "__SVG_MAP__": render_svg_map_html(geo),
        "__CHART_JS__": get_chart_js_inline(),
        # allow_nan=False tras sanitizar: si se colara un NaN, el script falla
        # en voz alta en vez de emitir el literal `NaN` (JSON inválido pero JS
        # válido) que el dashboard acabaría pintando en una celda.
        "__REPORT_DATA__": json.dumps(sanitize_for_json(payload), allow_nan=False),
        "__GENERATED_AT__": datetime.now().strftime("%b %d, %Y %H:%M"),
        "__DATA_NOTE__": ("simulated data" if "sim" in Path(order_sales_path).stem.lower()
                          or "demo" in str(order_sales_path).lower()
                          else "Commerce7 export"),
        "__T_NAVY__": TOKENS["brand_navy"],
        "__T_GRAY__": TOKENS["brand_gray"],
        "__T_TAN__": TOKENS["brand_tan"],
        "__T_CREAM__": TOKENS["brand_cream"],
        "__T_RULE__": TOKENS["rule_line"],
        "__T_GRID__": TOKENS["chart_grid"],
        "__T_NEG__": TOKENS["neg_value"],
        "__T_MAP_EMPTY__": TOKENS["map_empty"],
    }

    html = HTML_TEMPLATE
    for marker, value in replacements.items():
        html = html.replace(marker, value)

    leftover = [m for m in replacements if m in html]
    if leftover:
        raise RuntimeError(f"Marcadores sin sustituir en la plantilla: {leftover}")

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    # Los dos idiomas viajan en el archivo; `lang` fija el inicial.
    html = i18n.inject(html, lang)
    out.write_text(html, encoding="utf-8")

    print(f"Dashboard unificado generado: {out}")
    print(f"  Mensual  ({period_label}): ${vista_a['total_dtc']:,.2f} "
          f"en {vista_a['total_orders']} órdenes")
    if reconciliation["net_sales_financial"] is not None:
        print(f"  Reconciliación al centavo: {reconciliation['match']} "
              f"(diferencia ${reconciliation['difference']:,.2f})")
    if weekly:
        print(f"  Semanal  ({weekly['period_label']}): "
              f"${weekly['kpis']['total_dtc_sales']:,.2f}")
    else:
        print("  Semanal: no incluido (sin carpeta de datos semanales)")
    print(f"  Canales homologados: {len(payload['unified_channels']['rows'])} "
          f"· No clasificados listados: {len(payload['unified_unclassified'])}")
    return out


def main(argv=None) -> int:
    import argparse

    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError, OSError):
            pass

    ap = argparse.ArgumentParser(
        description="Genera el dashboard unificado (mensual + semanal) de Sullivan.")
    ap.add_argument("--order-sales", required=True)
    ap.add_argument("--financial-report", default=None)
    ap.add_argument("--weekly-data-dir", default=None)
    ap.add_argument("--period-label", default="April 2026")
    ap.add_argument("--tock-basis", choices=["net_receivable", "net_sales"],
                    default="net_receivable")
    ap.add_argument("--output", default=None)
    args = ap.parse_args(argv)

    out = args.output or str(PROJECT_ROOT / "Output" / "sullivan_dashboard_unified.html")
    generate_unified_dashboard(
        order_sales_path=args.order_sales,
        financial_report_path=args.financial_report,
        weekly_data_dir=args.weekly_data_dir,
        output_path=out,
        period_label=args.period_label,
        tock_basis=args.tock_basis,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
