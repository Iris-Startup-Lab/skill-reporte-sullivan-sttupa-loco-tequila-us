"""
================================================================================
 LOCO TEQUILA USA — GENERADOR DE DASHBOARD EJECUTIVO (BLUEPRINT DEMO)
================================================================================
 Genera el dashboard directivo interactivo para Loco Tequila USA:
   - Top Strip: KPIs de dirección (Depletions 9L, Revenue, GM%, Cuentas activas, CA 9L, TX 9L).
   - Bloque 1: Tendencia mensual de depletions (Línea) y Crecimiento MoM (Barras divergentes).
   - Bloque 2: Team & Channel Mix (Leaderboard de vendedores y desglose por mercado CA/TX/DTC/Ecom).
   - Bloque 3: Product Mix (Donut por SKU y Margen Bruto por caja 9L).
   - Bloque 4: Top Accounts de por vida y Revenue de distribuidores mayoristas.
   - Bloque 5: Heatmap de cadencia mensual de pedidos de cuentas clave + días sin pedido.
   - Bloque 6: Matriz de cuentas pequeñas con ritmo consistente (Sparklines).
   - Bloque 7: Rendimiento semanal de vendedores (Toggle 12 semanas vs 34 semanas YTD).
   - Bloque 8: Salud de inventario on-hand por SKU en bodegas CA vs TX.
 
 Gobernado estrictamente por Designs/Design_loco_tequila.md:
   - Paleta: Maroon #541424 / #6E1E28, Deep Maroon #3A0D18 / #5A1822, Oro Tequilero #C5A059, Crema #FBF8F2.
   - Paleta de SKUs: Blanco #9B1C31, Corazón #8A8A8A, Ámbar #A96C43, 269 #1F1F1F, Áureo #1F6E6E, 200 #D4AF37.
   - Tipografía: Fraunces (titulares y números) e Inter (tablas y métricas).
   - Logotipo oficial de Loco Tequila en base64.
   - REGLA DIRECTIVA: Todas las gráficas de barras ordenadas estrictamente de mayor a menor.
================================================================================
"""

import base64
import json
from pathlib import Path
from typing import Any, Dict, Optional

from loco_data_processor import (
    BLANK,
    process_loco_data,
    sanitize_for_json,
)
import i18n

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOGO_WHITE_PNG = PROJECT_ROOT / "Imagenes_iconos" / "Loco_Tequila_Logo_white.png"


def get_logo_white_data_uri() -> str:
    if LOGO_WHITE_PNG.exists():
        raw = LOGO_WHITE_PNG.read_bytes()
        return f"data:image/png;base64,{base64.b64encode(raw).decode('ascii')}"
    return ""


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Loco Tequila USA — Executive Sales &amp; Depletions Dashboard</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&family=Inter:wght@400;500;600;700&display=swap');

  :root {{
    color-scheme: light;
    --brand-maroon:      #541424;
    --brand-maroon-light:#6E1E28;
    --brand-maroon-deep: #3A0D18;
    --brand-gold:        #C5A059;
    --brand-cream:       #FBF8F2;
    --brand-gold-soft:   #F7F1E3;
    --ground:            #F9F8F5;
    --surface:           #FFFFFF;
    --surface-2:         #FBF9F5;
    --ink:               #1F1F1F;
    --ink-2:             #5A554E;
    --muted:             #8C857B;
    --hairline:          #E5E0D8;
    --hairline-strong:   #D4CEBF;
    --accent:            #C5A059;
    --accent-soft:       #F7F1E3;
    --good:              #1E7145;
    --bad:               #C0392B;
    --warning:           #D4AC0D;
    --serious:           #D35400;
    --critical:          #922B21;

    /* Series cromáticas corporativas de Loco Tequila */
    --series-1: #6E1E28; /* Maroon */
    --series-2: #C5A059; /* Oro Tequilero */
    --series-3: #2E6E6E; /* Teal Agave */
    --series-4: #A96C43; /* Ámbar */
    --series-5: #3A3A3A; /* Carbón */

    /* Colores Canónicos de Producto (Design_loco_tequila.md) */
    --p-blanco:  #9B1C31;
    --p-corazon: #8A8A8A;
    --p-ambar:   #A96C43;
    --p-269:     #1F1F1F;
    --p-aureo:   #1F6E6E;
    --p-200:     #D4AF37;

    font-family: 'Inter', system-ui, -apple-system, sans-serif;
    background: var(--ground);
    color: var(--ink);
  }}

  * {{ box-sizing: border-box; }}
  body {{ margin: 0; padding: 0; background: var(--ground); color: var(--ink); line-height: 1.5; }}

  /* HERO HEADER */
  .hero {{
    background: linear-gradient(135deg, var(--brand-maroon-deep) 0%, var(--brand-maroon) 55%, #7A1A2F 100%);
    color: #FFFFFF;
    padding: 32px 36px 28px;
    border-bottom: 3px solid var(--brand-gold);
  }}
  .hero-inner {{
    max-width: 1200px;
    margin: 0 auto;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 24px;
  }}
  .hero-brand {{
    display: flex;
    align-items: center;
    gap: 24px;
  }}
  .hero-logo {{
    height: 54px;
    width: auto;
    object-fit: contain;
    filter: drop-shadow(0 2px 6px rgba(0,0,0,0.3));
  }}
  .hero-titles {{
    max-width: 720px;
  }}
  .eyebrow {{
    font-size: 11px;
    letter-spacing: .16em;
    text-transform: uppercase;
    color: var(--brand-gold);
    font-weight: 700;
    margin: 0 0 6px;
  }}
  .hero h1 {{
    font-family: 'Fraunces', Georgia, serif;
    font-size: 30px;
    font-weight: 600;
    margin: 0 0 6px;
    letter-spacing: -0.01em;
    color: #FFFFFF;
  }}
  .hero p {{
    margin: 0;
    font-size: 14px;
    color: #F1ECE6;
    line-height: 1.5;
  }}
  .badge-exec {{
    font-size: 11px;
    font-weight: 600;
    background: rgba(197, 160, 89, 0.16);
    border: 1px solid var(--brand-gold);
    color: #FFFFFF;
    padding: 7px 14px;
    border-radius: 4px;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    white-space: nowrap;
  }}

  /* CONTENEDOR */
  .wrap {{
    max-width: 1200px;
    margin: 0 auto;
    padding: 32px 24px 80px;
  }}

  /* STRIP SUPERIOR KPI */
  .kpi-row {{
    display: grid;
    grid-template-columns: repeat(6, 1fr);
    gap: 12px;
    margin-bottom: 36px;
  }}
  @media (max-width: 1024px) {{
    .kpi-row {{ grid-template-columns: repeat(3, 1fr); }}
  }}
  @media (max-width: 640px) {{
    .kpi-row {{ grid-template-columns: repeat(2, 1fr); }}
  }}
  .kpi {{
    background: var(--surface);
    border: 1px solid var(--hairline);
    border-radius: 8px;
    padding: 16px 16px 14px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    border-top: 3px solid var(--brand-maroon);
  }}
  .kpi .l {{
    font-size: 11px;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: .06em;
    font-weight: 600;
    margin-bottom: 6px;
  }}
  .kpi .v {{
    font-family: 'Fraunces', Georgia, serif;
    font-size: 24px;
    font-weight: 700;
    color: var(--brand-maroon);
    line-height: 1.15;
  }}
  .kpi .d {{
    font-size: 11.5px;
    margin-top: 4px;
    color: var(--ink-2);
  }}
  .kpi .d.up {{ color: var(--good); font-weight: 600; }}

  /* SECCIONES Y BLOQUES */
  section.block {{
    margin-bottom: 40px;
  }}
  .block-head {{
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 16px;
    margin-bottom: 14px;
    border-bottom: 1px solid var(--hairline);
    padding-bottom: 10px;
    flex-wrap: wrap;
  }}
  .block-head-left {{
    display: flex;
    align-items: center;
    gap: 10px;
  }}
  .block-num {{
    width: 26px;
    height: 26px;
    border-radius: 50%;
    background: var(--brand-maroon);
    color: var(--brand-gold);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    font-weight: 700;
    flex: none;
  }}
  .block-head h2 {{
    font-family: 'Fraunces', Georgia, serif;
    font-size: 21px;
    margin: 0;
    font-weight: 600;
    color: var(--brand-maroon);
  }}
  .block-head .source {{
    font-size: 11px;
    color: var(--muted);
    letter-spacing: 0.04em;
    text-transform: uppercase;
  }}
  .block-head .source code {{
    background: var(--surface-2);
    border: 1px solid var(--hairline);
    border-radius: 4px;
    padding: 2px 6px;
    font-family: inherit;
    color: var(--brand-maroon);
    font-weight: 600;
  }}

  .grid2 {{ display: grid; grid-template-columns: 1.15fr 1fr; gap: 20px; }}
  @media (max-width: 920px) {{
    .grid2 {{ grid-template-columns: 1fr; }}
  }}

  .card {{
    background: var(--surface);
    border: 1px solid var(--hairline);
    border-radius: 8px;
    padding: 18px 20px 16px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    display: flex;
    flex-direction: column;
  }}
  .card h3 {{
    font-size: 14px;
    margin: 0 0 2px;
    font-weight: 700;
    color: var(--brand-maroon);
    display: flex;
    align-items: center;
  }}
  .card .card-sub {{
    font-size: 11.5px;
    color: var(--muted);
    margin-bottom: 12px;
  }}
  .chart-wrap {{
    position: relative;
    flex: 1;
    min-height: 0;
  }}

  .chip {{
    display: inline-block;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: .05em;
    text-transform: uppercase;
    padding: 2px 7px;
    border-radius: 4px;
    margin-right: 8px;
    vertical-align: 1px;
  }}
  .chip.bar {{ background: rgba(110, 30, 40, 0.12); color: var(--brand-maroon-light); }}
  .chip.line {{ background: rgba(46, 110, 110, 0.14); color: var(--series-3); }}
  .chip.donut {{ background: rgba(197, 160, 89, 0.18); color: #8A6822; }}
  .chip.voronoi {{ background: rgba(46, 110, 110, 0.18); color: #1F6E6E; }}
  .chip.stack {{ background: rgba(169, 108, 67, 0.14); color: var(--series-4); }}

  /* SVG Dataviz */
  svg text {{ font-family: 'Inter', sans-serif; }}
  .axis-label {{ font-size: 10px; fill: var(--muted); }}
  .val-label {{ font-size: 11px; font-weight: 600; fill: var(--ink); }}
  .val-label-inv {{ font-size: 11px; font-weight: 600; fill: #FFFFFF; }}
  .cat-label {{ font-size: 12px; fill: var(--ink); font-weight: 500; }}
  .grid-line {{ stroke: var(--hairline); stroke-width: 1; }}
  .baseline {{ stroke: var(--hairline-strong); stroke-width: 1.5; }}
  .bar-rect {{ transition: opacity .12s; }}
  .bar-rect:hover {{ opacity: .82; cursor: pointer; }}

  /* TOOLTIP */
  .tooltip {{
    position: fixed;
    pointer-events: none;
    z-index: 999;
    background: var(--brand-maroon-deep);
    color: #FFFFFF;
    font-size: 11.5px;
    padding: 7px 11px;
    border-radius: 5px;
    line-height: 1.45;
    opacity: 0;
    transition: opacity .08s;
    box-shadow: 0 6px 18px rgba(0,0,0,.25);
    border: 1px solid var(--brand-gold);
    max-width: 240px;
    white-space: nowrap;
  }}
  .tooltip b {{ font-weight: 700; color: #FFFFFF; }}
  .tooltip .row {{ display:flex; justify-content: space-between; gap: 12px; }}

  /* HEATMAP */
  .table-scroll {{ overflow-x: auto; }}
  table.cadence-table {{ border-collapse: collapse; width: 100%; min-width: 640px; }}
  table.cadence-table th, table.cadence-table td {{
    padding: 7px 8px; font-size: 12px; text-align: center; border-bottom: 1px solid var(--hairline);
  }}
  table.cadence-table th {{ color: var(--brand-maroon); font-weight: 700; font-size: 10.5px; text-transform: uppercase; }}
  table.cadence-table td.acct {{ text-align: left; font-weight: 600; color: var(--ink); font-size: 12.5px; white-space: nowrap; }}
  table.cadence-table td.cell {{ border-radius: 4px; }}
  table.cadence-table td.status {{ text-align: right; white-space: nowrap; }}
  .status-pill {{
    display: inline-flex; align-items: center; gap: 5px; font-size: 11px; font-weight: 600;
    padding: 3px 8px; border-radius: 20px;
  }}
  .status-pill .dot {{ width: 6px; height: 6px; border-radius: 50%; flex: none; }}

  .legend {{ display: flex; flex-wrap: wrap; gap: 12px 16px; margin-top: 10px; font-size: 11.5px; color: var(--ink-2); }}
  .legend .item {{ display: flex; align-items: center; gap: 6px; }}
  .legend .sw {{ width: 10px; height: 10px; border-radius: 2px; flex: none; }}

  /* SPARKLINES */
  .sparkline-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }}
  @media (max-width: 900px) {{ .sparkline-grid {{ grid-template-columns: repeat(2, 1fr); }} }}
  @media (max-width: 560px) {{ .sparkline-grid {{ grid-template-columns: 1fr; }} }}
  .spark-card {{ border: 1px solid var(--hairline); border-radius: 8px; padding: 14px 15px; background: var(--surface-2); }}
  .spark-card .acct-name {{ font-size: 13.5px; font-weight: 700; color: var(--brand-maroon); line-height: 1.3; }}
  .spark-card .acct-meta {{ font-size: 11px; color: var(--muted); margin-top: 2px; }}
  .spark-card .spark-stat {{ display:flex; align-items:baseline; justify-content:space-between; margin-top:10px; }}
  .spark-card .spark-total {{ font-family: 'Fraunces', Georgia, serif; font-size: 18px; font-weight: 700; color: var(--ink); }}
  .spark-card .spark-total small {{ font-family: 'Inter', sans-serif; font-size: 11px; font-weight: 500; color: var(--muted); }}
  .spark-bars {{ display: flex; align-items: flex-end; gap: 3px; height: 38px; margin-top: 10px; }}
  .spark-bars .bar-col {{ flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: flex-end; height: 100%; cursor: pointer; }}
  .spark-bars .bar {{ width: 100%; border-radius: 2px 2px 0 0; min-height: 2px; }}
  .spark-bars .bar.zero {{ background: var(--hairline); min-height: 2px; }}
  .spark-months {{ display: flex; gap: 3px; margin-top: 4px; }}
  .spark-months span {{ flex: 1; text-align: center; font-size: 8.5px; color: var(--muted); }}
  .trend-tag {{
    display: inline-flex; align-items: center; gap: 5px; font-size: 11px; font-weight: 600;
    padding: 3px 8px; border-radius: 12px; margin-top: 10px;
  }}
  .trend-tag .dot {{ width: 6px; height: 6px; border-radius: 50%; flex: none; }}

  /* CONTROLES DE BOTÓN */
  .seg {{ display: flex; gap: 2px; background: var(--surface-2); border: 1px solid var(--hairline); border-radius: 6px; padding: 2px; }}
  .seg-btn {{
    font: inherit; font-size: 11.5px; font-weight: 600; color: var(--ink-2); background: transparent; border: none;
    border-radius: 4px; padding: 5px 11px; cursor: pointer;
  }}
  .seg-btn:hover {{ color: var(--brand-maroon); }}
  .seg-btn.active {{ background: var(--brand-maroon); color: #FFFFFF; }}

  /* FOOTER */
  footer.notes {{
    margin-top: 48px;
    padding-top: 22px;
    border-top: 1px solid var(--hairline);
    background: var(--brand-cream);
    padding: 20px 24px;
    border-radius: 6px;
    border: 1px solid var(--hairline);
  }}
  footer.notes h4 {{
    font-size: 13px;
    margin: 0 0 8px;
    color: var(--brand-maroon);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }}
  footer.notes ol {{
    margin: 0;
    padding-left: 18px;
    font-size: 12.5px;
    color: var(--ink-2);
    line-height: 1.7;
  }}
  footer.notes li b {{ color: var(--brand-maroon); }}

  /* --- Pestañas. Mismo patrón ya probado en el tablero unificado de Sullivan:
         CSS + JS planos, sin framework, y la navegación se oculta al imprimir. */
  nav.tabs {{
    display: flex; flex-wrap: wrap; gap: 6px;
    border-bottom: 2px solid rgba(110,30,40,.18);
    margin: 0 0 22px; padding: 0;
  }}
  nav.tabs button {{
    appearance: none; border: 0; background: transparent; cursor: pointer;
    font-family: inherit; font-size: 13px; font-weight: 600; letter-spacing: .01em;
    color: #6a6a6a; padding: 10px 14px; border-radius: 8px 8px 0 0;
    border-bottom: 3px solid transparent; transition: color .15s, border-color .15s;
  }}
  nav.tabs button:hover {{ color: var(--brand-maroon); background: rgba(110,30,40,.04); }}
  nav.tabs button[aria-selected="true"] {{
    color: var(--brand-maroon); border-bottom-color: var(--brand-gold);
    background: rgba(197,160,89,.10);
  }}
  nav.tabs button .tnum {{
    display: inline-block; min-width: 17px; height: 17px; line-height: 17px;
    margin-right: 7px; border-radius: 4px; font-size: 10px; text-align: center;
    background: rgba(110,30,40,.10); color: var(--brand-maroon);
  }}
  nav.tabs button[aria-selected="true"] .tnum {{
    background: var(--brand-maroon); color: #fff;
  }}
  .panel {{ display: none; }}
  .panel.is-active {{ display: block; }}

  /* --- Tablas de detalle (rejillas mensuales, cuentas, trazabilidad) */
  table.grid-table {{
    width: 100%; border-collapse: collapse; font-size: 12px;
  }}
  table.grid-table th {{
    text-align: left; font-weight: 700; color: var(--brand-maroon);
    border-bottom: 2px solid rgba(110,30,40,.20);
    padding: 7px 9px; white-space: nowrap; background: rgba(197,160,89,.07);
    position: sticky; top: 0;
  }}
  table.grid-table td {{
    padding: 6px 9px; border-bottom: 1px solid rgba(0,0,0,.055);
    vertical-align: top;
  }}
  table.grid-table tbody tr:nth-child(even) td {{ background: rgba(0,0,0,.016); }}
  table.grid-table td.num, table.grid-table th.num {{
    text-align: right; font-variant-numeric: tabular-nums;
  }}
  table.grid-table td.zero {{ color: #bdbdbd; }}
  table.grid-table tr.total-row td {{
    font-weight: 700; border-top: 2px solid rgba(110,30,40,.25);
    background: rgba(197,160,89,.10) !important;
  }}
  table.grid-table td.reason {{ color: #7a6a4a; max-width: 380px; white-space: normal; }}
  .rule-badge {{
    display: inline-block; padding: 1px 6px; border-radius: 4px; font-size: 10px;
    font-weight: 700; background: rgba(110,30,40,.09); color: var(--brand-maroon);
  }}
  .rule-badge.unres {{ background: rgba(180,110,20,.14); color: #8a5a10; }}
  ul.rules-list {{ margin: 6px 0 0; padding-left: 18px; font-size: 12.5px; color: #4a4a4a; }}
  ul.rules-list li {{ margin-bottom: 6px; line-height: 1.55; }}
  ul.rules-list code {{ background: rgba(110,30,40,.06); padding: 1px 4px; border-radius: 3px; }}
  .block-note {{
    font-size: 12.5px; color: #7a6a4a; background: rgba(197,160,89,.10);
    border-left: 3px solid var(--brand-gold); padding: 10px 14px;
    border-radius: 0 6px 6px 0; margin-bottom: 18px; line-height: 1.55;
  }}

  @media print {{
    nav.tabs, .seg {{ display: none !important; }}
    .panel {{ display: block !important; page-break-before: always; }}
  }}
</style>
</head>
<body>

<div class="hero">
  <div class="hero-inner">
    <div class="hero-brand">
      {logo_img_tag}
      <div class="hero-titles">
        <p class="eyebrow">Executive Sales &amp; Depletions &middot; Loco Tequila USA</p>
        <h1>Executive Summary Blueprint</h1>
        <p>Directivo YTD 2026 consolidado a Semana 34 (24 de agosto de 2026). Datos unificados de distribuidores (SGWS en CA, Favorite Brands en TX), Park Street wholesale y DTC.</p>
      </div>
    </div>
    <div class="badge-exec">
      Official Executive Report &middot; {period_label}
    </div>
  </div>
</div>

<div class="wrap">

  <nav class="tabs" role="tablist" id="tabs"></nav>

  <!-- ===================== 1. OVERVIEW ===================== -->
  <section class="panel" role="tabpanel" id="p-over">
    <div class="kpi-row" id="kpiRow"></div>

    <section class="block">
      <div class="block-head">
        <div class="block-head-left">
          <span class="block-num">1</span>
          <h2>Depletion Trend &amp; Growth</h2>
        </div>
        <span class="source" id="srcTrend"></span>
      </div>
      <div class="grid2">
        <div class="card">
          <h3><span class="chip line">Line</span>Monthly Depletions (9L Cases)</h3>
          <div class="card-sub">Consolidated national volume, California plus Texas</div>
          <div class="chart-wrap"><svg id="chartTrend" width="100%" height="230" preserveAspectRatio="none"></svg></div>
        </div>
        <div class="card">
          <h3><span class="chip bar">Diverging</span>Month-over-Month Growth</h3>
          <div class="card-sub">Percent change against the prior month</div>
          <div class="chart-wrap"><svg id="chartMoM" width="100%" height="230" preserveAspectRatio="none"></svg></div>
        </div>
      </div>
    </section>

    <section class="block">
      <div class="block-head">
        <div class="block-head-left">
          <span class="block-num">2</span>
          <h2>Market &amp; Product Mix</h2>
        </div>
        <span class="source" id="srcMix"></span>
      </div>
      <div class="grid2">
        <div class="card">
          <h3><span class="chip stack">Bar</span>Depletions by Market (9L)</h3>
          <div class="card-sub">California &middot; Texas &middot; Direct-to-consumer</div>
          <div class="chart-wrap"><svg id="chartChannel" width="100%" height="230" preserveAspectRatio="none"></svg></div>
        </div>
        <div class="card">
          <h3><span class="chip donut" id="chipSkuChart">Donut</span>Share of Depletions by SKU</h3>
          <div class="card-sub">Proportional share of total depleted volume</div>
          <div class="chart-wrap" style="display:flex; align-items:center; gap: 20px;">
            <svg id="chartDonut" width="165" height="185" viewBox="0 0 165 185" style="flex:none;"></svg>
            <div id="donutLegend" style="flex:1;"></div>
          </div>
        </div>
      </div>
    </section>
  </section>

  <!-- ===================== 2. SALESPEOPLE ===================== -->
  <section class="panel" role="tabpanel" id="p-reps">
    <div class="block-note" id="repsNote"></div>
    <section class="block">
      <div class="block-head">
        <div class="block-head-left">
          <span class="block-num">1</span>
          <h2>Salesperson Leaderboard</h2>
        </div>
        <span class="source" id="srcReps"></span>
      </div>
      <div class="card">
        <h3><span class="chip bar">Bar</span>Bottles by Salesperson, highest to lowest</h3>
        <div class="card-sub">Bar length is bottles credited year to date</div>
        <div class="chart-wrap"><svg id="chartReps" width="100%" height="260" preserveAspectRatio="none"></svg></div>
      </div>
    </section>

    <section class="block">
      <div class="block-head">
        <div class="block-head-left">
          <span class="block-num">2</span>
          <h2>Bottle Sales by Person by Week</h2>
        </div>
        <span class="source" id="srcWeekly"></span>
      </div>
      <div class="card">
        <div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:10px; margin-bottom:4px;">
          <h3 style="margin-bottom:0;"><span class="chip stack">Bar</span>Weekly Bottle Depletions by Rep</h3>
          <div class="seg" id="weeklyToggle" role="group" aria-label="Date range">
            <button type="button" class="seg-btn active" data-mode="12w">Last 12 weeks</button>
            <button type="button" class="seg-btn" data-mode="ytd">Full year</button>
          </div>
        </div>
        <div class="card-sub" id="weeklySub">Tactical weekly view for operating reviews</div>
        <div class="chart-wrap"><svg id="chartWeekly" width="100%" height="260" preserveAspectRatio="none"></svg></div>
      </div>
      <div class="card">
        <h3>Rep by week &mdash; full grid</h3>
        <div class="card-sub">Every rep, every week, as reported. Reps ordered highest to lowest by total.</div>
        <div class="table-scroll"><table class="grid-table" id="repWeekTable"></table></div>
      </div>
    </section>
  </section>

  <!-- ===================== 3. SIGNATURE ===================== -->
  <section class="panel" role="tabpanel" id="p-sig">
    <section class="block">
      <div class="block-head">
        <div class="block-head-left">
          <span class="block-num">1</span>
          <h2>Signature Depletions &mdash; California</h2>
        </div>
        <span class="source" id="srcSig"></span>
      </div>
      <div class="card">
        <h3>By account and month (bottles)</h3>
        <div class="card-sub" id="sigAccSub"></div>
        <div class="table-scroll"><table class="grid-table" id="sigAccTable"></table></div>
      </div>
      <div class="grid2">
        <div class="card">
          <h3><span class="chip bar">Bar</span>By SKU, highest to lowest</h3>
          <div class="card-sub">Year-to-date bottles</div>
          <div class="chart-wrap"><svg id="chartSigSku" width="100%" height="200" preserveAspectRatio="none"></svg></div>
        </div>
        <div class="card">
          <h3><span class="chip bar">Bar</span>By city, highest to lowest</h3>
          <div class="card-sub">Top cities by year-to-date bottles</div>
          <div class="chart-wrap"><svg id="chartSigCity" width="100%" height="200" preserveAspectRatio="none"></svg></div>
        </div>
      </div>
    </section>
  </section>

  <!-- ===================== 4. FAVORITE BRANDS ===================== -->
  <section class="panel" role="tabpanel" id="p-fb">
    <section class="block">
      <div class="block-head">
        <div class="block-head-left">
          <span class="block-num">1</span>
          <h2>Favorite Brands Depletions &mdash; Texas</h2>
        </div>
        <span class="source" id="srcFb"></span>
      </div>
      <div class="card">
        <h3>By account and month (bottles)</h3>
        <div class="card-sub" id="fbAccSub"></div>
        <div class="table-scroll"><table class="grid-table" id="fbAccTable"></table></div>
      </div>
      <div class="grid2">
        <div class="card">
          <h3><span class="chip bar">Bar</span>By SKU, highest to lowest</h3>
          <div class="card-sub">Year-to-date bottles</div>
          <div class="chart-wrap"><svg id="chartFbSku" width="100%" height="200" preserveAspectRatio="none"></svg></div>
        </div>
        <div class="card">
          <h3><span class="chip bar">Bar</span>By premise</h3>
          <div class="card-sub">From the distributor's own PREMISE column, not inferred from the account name</div>
          <div class="chart-wrap"><svg id="chartFbPremise" width="100%" height="200" preserveAspectRatio="none"></svg></div>
        </div>
      </div>
      <div class="card">
        <h3>Distributor sales reps</h3>
        <div class="card-sub">These are <b>Favorite Brands' own</b> reps, from the SALES REP column of their report. They are not Loco salespeople and are never used to credit Loco volume.</div>
        <div class="table-scroll"><table class="grid-table" id="fbRepTable"></table></div>
      </div>
    </section>
  </section>

  <!-- ===================== 5. INVENTORY ===================== -->
  <section class="panel" role="tabpanel" id="p-inv">
    <section class="block">
      <div class="block-head">
        <div class="block-head-left">
          <span class="block-num">1</span>
          <h2>Inventory by SKU and Warehouse</h2>
        </div>
        <span class="source" id="srcInv"></span>
      </div>
      <div class="card">
        <h3>On-hand 9L cases by SKU across every warehouse</h3>
        <div class="card-sub">Signature SGWS (SoCal and NorCal) &middot; Park Street California &middot; Favorite Brands Texas. Columns sum to the CA and TX totals.</div>
        <div class="table-scroll"><table class="grid-table" id="invTable"></table></div>
      </div>
      <div class="grid2">
        <div class="card">
          <h3><span class="chip stack">Bar</span>On-hand by SKU, CA vs TX</h3>
          <div class="card-sub">Ordered by California holding</div>
          <div class="chart-wrap"><svg id="chartInventory" width="100%" height="230" preserveAspectRatio="none"></svg></div>
        </div>
        <div class="card">
          <h3><span class="chip bar">Bar</span>By warehouse, highest to lowest</h3>
          <div class="card-sub">Total sellable 9L cases held at each location</div>
          <div class="chart-wrap"><svg id="chartWarehouse" width="100%" height="230" preserveAspectRatio="none"></svg></div>
        </div>
      </div>
    </section>
  </section>

  <!-- ===================== 6. POD ===================== -->
  <section class="panel" role="tabpanel" id="p-pod">
    <section class="block">
      <div class="block-head">
        <div class="block-head-left">
          <span class="block-num">1</span>
          <h2>POD &mdash; Accounts On and Off Premise</h2>
        </div>
        <span class="source" id="srcPod"></span>
      </div>
      <div class="kpi-row" id="podRow"></div>
      <div class="grid2">
        <div class="card">
          <h3><span class="chip bar">Bar</span>Top accounts by bottles</h3>
          <div class="card-sub">Highest to lowest, wholesalers excluded</div>
          <div class="chart-wrap"><svg id="chartTopAccounts" width="100%" height="250" preserveAspectRatio="none"></svg></div>
        </div>
        <div class="card">
          <h3><span class="chip bar">Bar</span>Wholesale distributor revenue</h3>
          <div class="card-sub">Year to date, highest to lowest</div>
          <div class="chart-wrap"><svg id="chartWholesale" width="100%" height="250" preserveAspectRatio="none"></svg></div>
        </div>
      </div>
      <div class="card">
        <h3>Accounts with orders year to date</h3>
        <div class="card-sub">Channel comes from the distributor's PREMISE column where it exists, otherwise from the account map. The rule that resolved each row is shown, so an unresolved one can be fixed at the source.</div>
        <div class="table-scroll"><table class="grid-table" id="podTable"></table></div>
      </div>
    </section>
  </section>

  <!-- ===================== 7. DTC ===================== -->
  <section class="panel" role="tabpanel" id="p-dtc">
    <section class="block">
      <div class="block-head">
        <div class="block-head-left">
          <span class="block-num">1</span>
          <h2>DTC &mdash; Shopify and Memory Bottles</h2>
        </div>
        <span class="source" id="srcDtc"></span>
      </div>
      <div class="kpi-row" id="dtcRow"></div>
      <div class="grid2">
        <div class="card">
          <h3><span class="chip line">Line</span>Bottles by month and store</h3>
          <div class="card-sub">Split by the store the order came from</div>
          <div class="chart-wrap"><svg id="chartDtcMonth" width="100%" height="230" preserveAspectRatio="none"></svg></div>
        </div>
        <div class="card">
          <h3><span class="chip bar">Bar</span>Bottles by SKU and store</h3>
          <div class="card-sub">Highest to lowest</div>
          <div class="chart-wrap"><svg id="chartDtcSku" width="100%" height="230" preserveAspectRatio="none"></svg></div>
        </div>
      </div>
      <div class="card">
        <h3>Store detail</h3>
        <div class="table-scroll"><table class="grid-table" id="dtcTable"></table></div>
      </div>
    </section>
  </section>

  <!-- ===================== 8. SOURCES ===================== -->
  <section class="panel" role="tabpanel" id="p-src">
    <section class="block">
      <div class="block-head">
        <div class="block-head-left">
          <span class="block-num">1</span>
          <h2>Where every number comes from</h2>
        </div>
        <span class="source">Methodology &amp; Sources</span>
      </div>
      <div class="card">
        <h3>Measure, source and basis</h3>
        <div class="card-sub">Each figure in this report, the file it is read from, the columns used, and the conversion applied.</div>
        <div class="table-scroll"><table class="grid-table" id="provTable"></table></div>
      </div>
      <div class="card">
        <h3>Unit conversions applied</h3>
        <ul class="rules-list" id="unitRules"></ul>
      </div>
      <div class="card" id="marginCard">
        <h3>Gross margin basis</h3>
        <div class="card-sub" id="marginProv"></div>
        <div class="table-scroll"><table class="grid-table" id="marginTable"></table></div>
      </div>
      <div class="card">
        <h3>How salespeople are credited</h3>
        <div class="card-sub">A ranked ladder. The first rule that resolves a line wins, and each line carries the rule that resolved it.</div>
        <div class="table-scroll"><table class="grid-table" id="ladderTable"></table></div>
      </div>
      <div class="card">
        <h3>Lines not credited to anyone</h3>
        <div class="card-sub" id="unattrSub"></div>
        <div class="table-scroll"><table class="grid-table" id="unattrTable"></table></div>
      </div>
      <div class="card" id="gapsCard">
        <h3>Declared limits of this report</h3>
        <ul class="rules-list" id="gapsList"></ul>
      </div>
    </section>
  </section>

  <footer class="notes">
    <h4>Reporting rules &mdash; Loco Tequila USA</h4>
    <ol>
      <li><b>Descending order:</b> every categorical bar chart is ordered highest to lowest. Time series are ordered by period, because sorting a time series by value destroys its axis.</li>
      <li><b>Order value:</b> wholesale revenue sums the per-line amount, never the order-level total that repeats on every line of the same order.</li>
      <li><b>Nothing is invented:</b> what the source files do not contain is reported as a declared limit, with its reason, instead of being filled in with a plausible number.</li>
      <li><b>Traceability:</b> the Sources tab names the file and columns behind every measure, and lists every line that could not be credited to a salesperson together with why.</li>
    </ol>
  </footer>

</div>

<div class="tooltip" id="tooltip"></div>

<script>
window.LOCO_DATA = {report_data_json};
</script>
<script>
(function(){{
  const COLORS = {{
    maroon: '#6E1E28',
    maroonDeep: '#3A0D18',
    gold: '#C5A059',
    cream: '#FBF8F2',
    teal: '#2E6E6E',
    amber: '#A96C43',
    slate: '#3A3A3A',
    blanco: '#9B1C31',
    corazon: '#8A8A8A',
    aureo: '#1F6E6E',
    p200: '#D4AF37',
    ink: '#1F1F1F',
    muted: '#8C857B',
    hair: '#E5E0D8',
    hairStrong: '#D4CEBF',
    good: '#1E7145',
    bad: '#C0392B',
    surface: '#FFFFFF',
    warning: '#D4AC0D',
    serious: '#D35400',
    critical: '#922B21'
  }};

  const tooltip = document.getElementById('tooltip');
  function showTip(evt, html){{
    tooltip.innerHTML = html;
    tooltip.style.opacity = 1;
    const x = evt.clientX, y = evt.clientY;
    const tw = 220;
    tooltip.style.left = Math.min(x + 14, window.innerWidth - tw - 10) + 'px';
    tooltip.style.top = (y - 14) + 'px';
  }}
  function moveTip(evt){{
    if(tooltip.style.opacity == '1'){{
      tooltip.style.left = Math.min(evt.clientX + 14, window.innerWidth - 230) + 'px';
      tooltip.style.top = (evt.clientY - 14) + 'px';
    }}
  }}
  function hideTip(){{ tooltip.style.opacity = 0; }}

  const NS = 'http://www.w3.org/2000/svg';
  function el(tag, attrs){{
    const e = document.createElementNS(NS, tag);
    for(const k in attrs) e.setAttribute(k, attrs[k]);
    return e;
  }}
  function fmt(n, d){{
    return Number(n).toLocaleString('en-US', {{minimumFractionDigits: d || 0, maximumFractionDigits: d || 0}});
  }}
  function fmtMoney(n){{ return '$' + fmt(Math.round(n)); }}

  // FORMATEO CENTRAL. Antes cada gráfica decidía por su cuenta cuántos decimales
  // usar: la tendencia no redondeaba nada (de ahí "6.833333333333333 9L", la
  // queja del cliente), el inventario usaba 1 decimal, y el MoM usaba 1 en el
  // tooltip y 0 en la etiqueta de la misma barra. Una sola política:
  const DEC = {{ bottles: 0, cases: 2, money: 0, pct: 1, rate: 2 }};
  function nfmt(n, kind){{
    const v = Number(n);
    if(n === null || n === undefined || n === '' || !isFinite(v)) return BLANK;
    if(kind === 'money') return fmtMoney(v);
    return fmt(v, DEC[kind] !== undefined ? DEC[kind] : 2);
  }}
  function cases9l(n){{ return nfmt(n, 'cases') + ' 9L'; }}

  // BLANK marca el dato ausente: nunca debe imprimirse "nan" ni "null".
  const LOCO = window.LOCO_DATA || {{}};
  const K = LOCO.kpis || {{}};
  const BLANK = '\\u2014';

  function cellText(v){{
    if (v === null || v === undefined) return BLANK;
    if (typeof v === 'number' && !isFinite(v)) return BLANK;
    const s = String(v).trim();
    if (/^(nan|nat|none|null|undefined|<na>)$/i.test(s)) return BLANK;
    return s === '' ? BLANK : s;
  }}
  function num(v){{ const n = Number(v); return isFinite(n) ? n : 0; }}

  // Barras horizontales reutilizables. Las gráficas nuevas de las pestañas de
  // detalle son todas de esta forma, así que se dibujan una sola vez aquí en
  // lugar de repetir el mismo bloque SVG siete veces.
  // Ranking categórico -> SIEMPRE descendente (regla del repo).
  function hbars(svgId, data, labelFn, colorFn){{
    const svg = document.getElementById(svgId);
    if(!svg) return;
    svg.innerHTML = '';
    const rows = (data||[]).filter(d => isFinite(Number(d.v)))
                           .sort((a,b) => num(b.v) - num(a.v));
    if(!rows.length){{
      svg.appendChild(el('text', {{x:12, y:24, style:'font-size:11px;fill:#8a8a8a;'}}))
         .textContent = 'No data for this view.';
      return;
    }}
    const W = 560;
    const rowH = Math.max(18, Math.min(30, 200 / rows.length));
    const H = Math.max(80, rows.length * rowH + 16);
    const P = {{t:8, r:86, b:8, l:Math.min(190, Math.max(96,
      8 + 6.1 * Math.max(...rows.map(d => String(d.name||'').length))))}};
    svg.setAttribute('viewBox', `0 0 ${{W}} ${{H}}`);
    svg.setAttribute('height', H);
    const maxV = Math.max(1, ...rows.map(d => num(d.v)));
    const x = v => (v / maxV) * (W - P.l - P.r);
    rows.forEach((d, i) => {{
      const cy = P.t + i * rowH;
      const bh = Math.max(8, rowH - 8);
      svg.appendChild(el('text', {{x:P.l - 8, y:cy + bh/2 + 3.5, 'text-anchor':'end',
        style:'font-size:10.5px;fill:#4a4a4a;'}})).textContent = cellText(d.name);
      const r = el('rect', {{x:P.l, y:cy, width:Math.max(1, x(num(d.v))), height:bh,
        rx:2.5, fill:(colorFn ? colorFn(d, i) : (i === 0 ? COLORS.maroon : COLORS.gold))}});
      r.addEventListener('mouseenter', e => showTip(e,
        `<b>${{cellText(d.name)}}</b><div class="row"><span>Value</span><b>${{labelFn ? labelFn(num(d.v)) : nfmt(d.v,'cases')}}</b></div>`));
      r.addEventListener('mousemove', moveTip);
      r.addEventListener('mouseleave', hideTip);
      svg.appendChild(r);
      svg.appendChild(el('text', {{class:'val-label', x:P.l + x(num(d.v)) + 7,
        y:cy + bh/2 + 3.5}})).textContent = labelFn ? labelFn(num(d.v)) : nfmt(d.v,'cases');
    }});
  }}

  // Crecimiento del último mes contra el anterior, calculado del dato real.
  const MONTHLY = (LOCO.depletions_monthly || []);
  let momLabel = BLANK, momCls = '';
  if (MONTHLY.length >= 2) {{
    const a = num(MONTHLY[MONTHLY.length - 2].bottles);
    const b = num(MONTHLY[MONTHLY.length - 1].bottles);
    if (a > 0) {{
      const pct = (b - a) / a * 100;
      momLabel = (pct >= 0 ? '+' : '') + pct.toFixed(1) + '%';
      momCls = pct >= 0 ? 'up' : 'down';
    }}
  }}
  const lastMonth = MONTHLY.length ? cellText(MONTHLY[MONTHLY.length - 1].month) : BLANK;
  const prevMonth = MONTHLY.length >= 2 ? cellText(MONTHLY[MONTHLY.length - 2].month) : BLANK;

  // ---------- KPI ROW ----------
  const kpis = [
    {{l:'Depletions (9L cases)', v: fmt(num(K.depletions_cases_9l_ytd), 2),
      d: fmt(num(K.depletions_bottles_ytd)) + ' bottles YTD'}},
    {{l:'Wholesale Revenue', v: fmtMoney(num(K.wholesale_revenue)), d:'Sell-in to distributors, YTD'}},
    {{l:'Retail + DTC Revenue', v: fmtMoney(num(K.retail_revenue) + num(K.dtc_revenue)),
      d:'Direct retail and ecommerce, YTD'}},
    {{l:'Active Accounts', v: fmt(num(K.accounts_active)), d:'Across all sources'}},
    {{l:'On-Hand Inventory (9L)', v: fmt(num(K.inventory_total_9l), 2),
      d:'CA ' + fmt(num(K.inventory_ca_9l), 2) + ' · TX ' + fmt(num(K.inventory_tx_9l), 2)}},
    {{l: lastMonth + ' vs. ' + prevMonth, v: momLabel, d:'MoM depletions volume', cls: momCls}}
  ];
  const kpiRow = document.getElementById('kpiRow');
  kpis.forEach(k=>{{
    const d = document.createElement('div');
    d.className = 'kpi';
    d.innerHTML = `<div class="l">${{k.l}}</div><div class="v">${{k.v}}</div><div class="d ${{k.cls||''}}">${{k.d}}</div>`;
    kpiRow.appendChild(d);
  }});

  // ---------- 1. LINE CHART: DEPLETIONS TREND ----------
  (function(){{
    const svg = document.getElementById('chartTrend');
    // Serie de TIEMPO: orden de calendario, no descendente (reordenarla
    // destruiría el eje). La regla de mayor a menor aplica a rankings.
    const months = MONTHLY.map(m => cellText(m.month));
    // Las cajas 9L llegan ya calculadas desde la capa de datos, donde se conoce
    // el SKU y por tanto se puede aplicar la excepcion del formato de 200 mL.
    const vals = MONTHLY.map(m => num(m.cases_9l));
    if (!months.length) {{ return; }}
    const W = 560, H = 230, padL = 34, padR = 16, padT = 16, padB = 28;
    svg.setAttribute('viewBox', `0 0 ${{W}} ${{H}}`);
    const maxV = Math.max(...vals) * 1.18;
    const x = i => padL + (i/(months.length-1)) * (W-padL-padR);
    const y = v => H-padB - (v/maxV) * (H-padT-padB);

    let path = `M ${{x(0)}} ${{y(vals[0])}}`;
    vals.forEach((v,i)=>{{ if(i>0) path += ` L ${{x(i)}} ${{y(v)}}`; }});
    const areaPath = path + ` L ${{x(vals.length-1)}} ${{y(0)}} L ${{x(0)}} ${{y(0)}} Z`;

    const grad = el('linearGradient', {{id:'trendGrad', x1:0, y1:0, x2:0, y2:1}});
    grad.appendChild(el('stop', {{offset:'0%', 'stop-color':COLORS.maroon, 'stop-opacity':0.35}}));
    grad.appendChild(el('stop', {{offset:'100%', 'stop-color':COLORS.maroon, 'stop-opacity':0.02}}));
    const defs = el('defs',{{}}); defs.appendChild(grad); svg.appendChild(defs);

    svg.appendChild(el('path', {{d:areaPath, fill:'url(#trendGrad)'}}));
    svg.appendChild(el('path', {{d:path, fill:'none', stroke:COLORS.maroon, 'stroke-width':2.5, 'stroke-linecap':'round', 'stroke-linejoin':'round'}}));
    svg.appendChild(el('line', {{class:'baseline', x1:padL, x2:W-padR, y1:y(0), y2:y(0)}}));

    months.forEach((m,i)=>{{
      const cx = x(i), cy = y(vals[i]);
      const dot = el('circle', {{cx, cy, r:4.5, fill:COLORS.gold, stroke:COLORS.maroon, 'stroke-width':2, style:'cursor:pointer'}});
      dot.addEventListener('mouseenter', e=>showTip(e, `<b>${{m}} 2026</b><div class="row"><span>Depletions</span><b>${{cases9l(vals[i])}}</b></div><div class="row"><span>Bottles</span><b>${{nfmt(MONTHLY[i].bottles,'bottles')}}</b></div>`));
      dot.addEventListener('mousemove', moveTip);
      dot.addEventListener('mouseleave', hideTip);
      svg.appendChild(dot);
      svg.appendChild(el('text', {{class:'axis-label', x:cx, y:H-8, 'text-anchor':'middle'}})).textContent = m;
      if(i === months.length - 1){{
        svg.appendChild(el('text', {{class:'val-label', x:cx, y:cy-10, 'text-anchor':'end', fill:COLORS.maroon}})).textContent = cases9l(vals[i]);
      }}
    }});
  }})();

  // ---------- 2. DIVERGING BAR: MOM GROWTH ----------
  (function(){{
    const svg = document.getElementById('chartMoM');
    // Variación mes contra mes, derivada de la serie real. También es serie de
    // tiempo: se conserva el orden de calendario.
    const months = [], vals = [];
    for (let i = 1; i < MONTHLY.length; i++) {{
      const prev = num(MONTHLY[i-1].bottles), cur = num(MONTHLY[i].bottles);
      if (prev <= 0) continue;
      months.push(cellText(MONTHLY[i].month));
      vals.push(Number(((cur - prev) / prev * 100).toFixed(2)));
    }}
    if (!months.length) {{ return; }}
    const W = 560, H = 230, padL = 40, padR = 16, padT = 16, padB = 28;
    svg.setAttribute('viewBox', `0 0 ${{W}} ${{H}}`);
    const maxAbs = Math.max(...vals.map(Math.abs)) * 1.15;
    const mid = padT + (H-padT-padB)/2;
    const scale = (H-padT-padB)/2 / maxAbs;
    const slot = (W-padL-padR)/months.length;
    const bw = slot * 0.55;

    svg.appendChild(el('line', {{class:'baseline', x1:padL, x2:W-padR, y1:mid, y2:mid}}));
    months.forEach((m,i)=>{{
      const cx = padL + slot*i + slot/2;
      const v = vals[i];
      const h = Math.abs(v)*scale;
      const y = v>=0 ? mid-h : mid;
      const color = v>=0 ? COLORS.maroon : COLORS.bad;
      const rect = el('rect', {{class:'bar-rect', x:cx-bw/2, y, width:bw, height:h, rx:3, fill:color, style:'cursor:pointer'}});
      rect.addEventListener('mouseenter', e=>showTip(e, `<b>${{m}} 2026</b><div class="row"><span>MoM Growth</span><b>${{v>0?'+':''}}${{nfmt(v,'pct')}}%</b></div>`));
      rect.addEventListener('mousemove', moveTip);
      rect.addEventListener('mouseleave', hideTip);
      svg.appendChild(rect);
      const lbl = el('text', {{class:'axis-label', x:cx, y: v>=0 ? y-6 : y+h+12, 'text-anchor':'middle', style:`fill:${{v>=0?COLORS.good:COLORS.bad}};font-weight:600;font-size:10.5px;`}});
      lbl.textContent = (v>0?'+':'') + nfmt(v,'pct') + '%';
      svg.appendChild(lbl);
      svg.appendChild(el('text', {{class:'axis-label', x:cx, y:H-8, 'text-anchor':'middle'}})).textContent = m;
    }});
  }})();

  // ---------- 3. SALESPERSON LEADERBOARD (MAYOR A MENOR) ----------
  (function(){{
    const svg = document.getElementById('chartReps');
    // Datos reales por vendedor (botellas -> cajas 9L). Sin catálogo de COGS no
    // hay margen bruto, así que el tooltip informa participación de VOLUMEN.
    const repsTotal = (LOCO.reps || []).reduce((a, r) => a + num(r.bottles), 0);
    const data = (LOCO.reps || []).map(r => ({{
      name: cellText(r.rep),
      v: num(r.cases_9l),
      gm: repsTotal > 0 ? (num(r.bottles) / repsTotal * 100).toFixed(1) + '% of volume' : BLANK
    }}));
    if (!data.length) {{ return; }}
    data.sort((a,b)=>b.v - a.v);   // regla: mayor a menor

    const W = 580, H = 230, padL = 178, padR = 50, padT = 10, padB = 10;
    svg.setAttribute('viewBox', `0 0 ${{W}} ${{H}}`);
    const maxV = Math.max(...data.map(d=>d.v)) * 1.15;
    const rowH = (H-padT-padB)/data.length;
    const x = v => padL + (v/maxV)*(W-padL-padR);

    data.forEach((d,i)=>{{
      const cy = padT + rowH*i + rowH/2;
      const barH = rowH*0.52;
      svg.appendChild(el('text', {{class:'cat-label', x:padL-10, y:cy+4, 'text-anchor':'end'}})).textContent = d.name;
      const rect = el('rect', {{class:'bar-rect', x:padL, y:cy-barH/2, width:x(d.v)-padL, height:barH, rx:4, fill:COLORS.maroon, style:'cursor:pointer'}});
      rect.addEventListener('mouseenter', e=>showTip(e, `<b>${{d.name}}</b><div class="row"><span>Volume</span><b>${{d.v}} 9L</b></div><div class="row"><span>Share</span><b>${{d.gm}}</b></div>`));
      rect.addEventListener('mousemove', moveTip);
      rect.addEventListener('mouseleave', hideTip);
      svg.appendChild(rect);
      svg.appendChild(el('text', {{class:'val-label', x:x(d.v)+8, y:cy+4}})).textContent = d.v+' 9L';
    }});
  }})();

  // ---------- 3b. SALES BY MARKET (MAYOR A MENOR) ----------
  (function(){{
    const svg = document.getElementById('chartChannel');
    // Mercados reales: territorios de depletions + los flujos directos.
    const terrColors = {{'California': COLORS.maroon, 'Texas': COLORS.gold}};
    const streamColors = [COLORS.teal, COLORS.amber];
    const data = (LOCO.territories || []).map(t => ({{
      name: cellText(t.territory),
      v: Number(num(t.cases_9l_ytd).toFixed(2)),
      color: terrColors[t.territory] || COLORS.slate
    }})).concat((LOCO.dtc_streams || []).map((s, i) => ({{
      name: cellText(s.stream),
      v: num(s.cases_9l),
      color: streamColors[i % streamColors.length]
    }})));
    if (!data.length) {{ return; }}
    data.sort((a,b)=>b.v - a.v);   // regla: mayor a menor
    const total = data.reduce((a,d)=>a+d.v,0);

    const W = 560, H = 230, padL = 150, padR = 60, padT = 10, padB = 10;
    svg.setAttribute('viewBox', `0 0 ${{W}} ${{H}}`);
    const maxV = Math.max(...data.map(d=>d.v)) * 1.15;
    const rowH = (H-padT-padB)/data.length;
    const x = v => padL + (v/maxV)*(W-padL-padR);

    data.forEach((d,i)=>{{
      const cy = padT + rowH*i + rowH/2;
      const barH = rowH*0.52;
      const pct = (d.v/total*100).toFixed(1);
      svg.appendChild(el('text', {{class:'cat-label', x:padL-10, y:cy+4, 'text-anchor':'end'}})).textContent = d.name;
      const rect = el('rect', {{class:'bar-rect', x:padL, y:cy-barH/2, width:x(d.v)-padL, height:barH, rx:4, fill:d.color, style:'cursor:pointer'}});
      rect.addEventListener('mouseenter', e=>showTip(e, `<b>${{d.name}}</b><div class="row"><span>Depletions</span><b>${{d.v}} 9L</b></div><div class="row"><span>Share</span><b>${{pct}}%</b></div>`));
      rect.addEventListener('mousemove', moveTip);
      rect.addEventListener('mouseleave', hideTip);
      svg.appendChild(rect);
      svg.appendChild(el('text', {{class:'val-label', x:x(d.v)+8, y:cy+4}})).textContent = pct+'%';
    }});
  }})();

  // ---------- 4. SKU PRODUCT MIX: DONUT (<=3) O VORONOI TREEMAP (>3) ----------
  (function(){{
    const svg = document.getElementById('chartDonut');
    const chip = document.getElementById('chipSkuChart');
    const legend = document.getElementById('donutLegend');
    if (!svg) return;

    const skuPalette = [COLORS.blanco, COLORS.amber, COLORS.corazon,
                        COLORS.aureo, COLORS.teal, COLORS.gold, COLORS.slate];
    const data = (LOCO.sku_mix || []).map((s, i) => ({{
      name: cellText(s.sku),
      v: num(s.cases_9l),
      color: skuPalette[i % skuPalette.length]
    }})).filter(d => d.v > 0);

    if (!data.length) return;
    data.sort((a, b) => b.v - a.v); // regla: mayor a menor
    const total = data.reduce((a, d) => a + d.v, 0);

    // Heurística de UI: <=3 dona (total al centro), >3 Voronoi (total arriba)
    if (data.length <= 3) {{
      if (chip) {{ chip.className = 'chip donut'; chip.textContent = 'Donut'; }}
      svg.setAttribute('viewBox', '0 0 160 160');
      svg.setAttribute('width', '160');
      svg.setAttribute('height', '160');
      svg.innerHTML = '';
      if (legend) legend.innerHTML = '';

      const cx = 80, cy = 80, r = 64, rInner = 40;
      let angle = -Math.PI / 2;

      data.forEach(d => {{
        const frac = d.v / total;
        const a0 = angle, a1 = angle + frac * Math.PI * 2;
        angle = a1;
        const large = (a1 - a0) > Math.PI ? 1 : 0;
        const p0 = [cx + r * Math.cos(a0), cy + r * Math.sin(a0)];
        const p1 = [cx + r * Math.cos(a1), cy + r * Math.sin(a1)];
        const p0i = [cx + rInner * Math.cos(a1), cy + rInner * Math.sin(a1)];
        const p1i = [cx + rInner * Math.cos(a0), cy + rInner * Math.sin(a0)];
        const d_attr = `M ${{p0[0]}} ${{p0[1]}} A ${{r}} ${{r}} 0 ${{large}} 1 ${{p1[0]}} ${{p1[1]}} L ${{p0i[0]}} ${{p0i[1]}} A ${{rInner}} ${{rInner}} 0 ${{large}} 0 ${{p1i[0]}} ${{p1i[1]}} Z`;
        const path = el('path', {{d: d_attr, fill: d.color, stroke: '#fff', 'stroke-width': 1.5, style: 'cursor:pointer'}});
        const pct = (frac * 100).toFixed(1);
        path.addEventListener('mouseenter', e => showTip(e, `<b>${{d.name}}</b><div class="row"><span>Volume</span><b>${{d.v}} 9L</b></div><div class="row"><span>Share</span><b>${{pct}}%</b></div>`));
        path.addEventListener('mousemove', moveTip);
        path.addEventListener('mouseleave', hideTip);
        svg.appendChild(path);

        if (legend) {{
          const row = document.createElement('div');
          row.className = 'legend item';
          row.style.marginBottom = '4px';
          row.innerHTML = `<span class="sw" style="background:${{d.color}}"></span><span>${{d.name}} &mdash; <b>${{pct}}%</b></span>`;
          legend.appendChild(row);
        }}
      }});

      svg.appendChild(el('text', {{x: cx, y: cy - 3, 'text-anchor': 'middle', style: 'font-family:Fraunces,serif;font-size:16px;font-weight:700;fill:var(--brand-maroon);'}})).textContent = total.toFixed(0);
      svg.appendChild(el('text', {{x: cx, y: cy + 13, 'text-anchor': 'middle', class: 'axis-label'}})).textContent = '9L total';
    }} else {{
      if (chip) {{ chip.className = 'chip voronoi'; chip.textContent = 'Voronoi Treemap'; }}
      svg.setAttribute('viewBox', '0 0 165 185');
      svg.setAttribute('width', '165');
      svg.setAttribute('height', '185');
      svg.innerHTML = '';
      if (legend) legend.innerHTML = '';

      // Geometría del Voronoi circular (Sutherland-Hodgman + Lloyd)
      function _clip(poly, a, b, c) {{
        if (!poly || !poly.length) return poly;
        const res = [], n = poly.length;
        for (let i = 0; i < n; i++) {{
          const cur = poly[i], nxt = poly[(i + 1) % n];
          const cur_in = (a * cur[0] + b * cur[1]) <= c + 1e-9;
          const nxt_in = (a * nxt[0] + b * nxt[1]) <= c + 1e-9;
          if (cur_in) res.push(cur);
          if (cur_in !== nxt_in) {{
            const dx = nxt[0] - cur[0], dy = nxt[1] - cur[1];
            const denom = a * dx + b * dy;
            if (Math.abs(denom) > 1e-12) {{
              const t = (c - (a * cur[0] + b * cur[1])) / denom;
              res.push([cur[0] + t * dx, cur[1] + t * dy]);
            }}
          }}
        }}
        return res;
      }}

      function _area(poly) {{
        const n = poly.length;
        if (n < 3) return 0;
        let a = 0;
        for (let i = 0; i < n; i++) {{
          const j = (i + 1) % n;
          a += poly[i][0] * poly[j][1] - poly[j][0] * poly[i][1];
        }}
        return Math.abs(a) * 0.5;
      }}

      function _centroid(poly) {{
        const n = poly.length;
        if (n < 3) return [0, 0];
        let A = 0, cx = 0, cy = 0;
        for (let i = 0; i < n; i++) {{
          const j = (i + 1) % n;
          const cross = poly[i][0] * poly[j][1] - poly[j][0] * poly[i][1];
          A += cross;
          cx += (poly[i][0] + poly[j][0]) * cross;
          cy += (poly[i][1] + poly[j][1]) * cross;
        }}
        A *= 0.5;
        return Math.abs(A) > 1e-12 ? [cx / (6 * A), cy / (6 * A)] : [0, 0];
      }}

      const vals = data.map(d => d.v);
      const n = vals.length;
      const boundary = [];
      const NB = 64;
      for (let k = 0; k < NB; k++) {{
        const ang = (2 * Math.PI * k) / NB;
        boundary.push([Math.cos(ang), Math.sin(ang)]);
      }}
      const barea = _area(boundary);
      const target = vals.map(v => (v / total) * barea);
      const ga = Math.PI * (3 - Math.sqrt(5));
      const sites = [];
      for (let i = 0; i < n; i++) {{
        const r = 0.55 * Math.sqrt((i + 0.5) / n);
        sites.push([r * Math.cos(i * ga), r * Math.sin(i * ga)]);
      }}
      let weights = new Array(n).fill(0.0);

      function computeCells(s, w) {{
        const list = [];
        for (let i = 0; i < n; i++) {{
          let poly = boundary.slice();
          for (let j = 0; j < n; j++) {{
            if (j === i) continue;
            const a = 2 * (s[j][0] - s[i][0]);
            const b = 2 * (s[j][1] - s[i][1]);
            const c = (s[j][0]**2 + s[j][1]**2 - w[j]) - (s[i][0]**2 + s[i][1]**2 - w[i]);
            poly = _clip(poly, a, b, c);
            if (!poly.length) break;
          }}
          list.push(poly);
        }}
        return list;
      }}

      let cells = computeCells(sites, weights);
      for (let it = 0; it < 90; it++) {{
        for (let i = 0; i < n; i++) {{
          if (_area(cells[i]) > 1e-8) sites[i] = _centroid(cells[i]);
        }}
        cells = computeCells(sites, weights);
        const areas = cells.map(c => _area(c));
        for (let i = 0; i < n; i++) weights[i] += (target[i] - areas[i]) * 0.45;
        const wmin = Math.min(...weights);
        weights = weights.map(w => w - wmin);
        cells = computeCells(sites, weights);
      }}

      // Encabezado con KPI global arriba (deja el 100% del círculo para celdas)
      const cxCircle = 82.5, cyCircle = 108, rCircle = 72;
      svg.appendChild(el('text', {{x: cxCircle, y: 16, 'text-anchor': 'middle', style: 'font-family:Fraunces,serif;font-size:15px;font-weight:700;fill:var(--brand-maroon);'}})).textContent = `${{total.toFixed(0)}} 9L total`;
      svg.appendChild(el('text', {{x: cxCircle, y: 28, 'text-anchor': 'middle', class: 'axis-label'}})).textContent = 'Product Mix';

      cells.forEach((cell, i) => {{
        if (cell.length < 3) return;
        const d = data[i];
        const frac = d.v / total;
        const pct = (frac * 100).toFixed(1);
        const pts = cell.map(p => `${{(cxCircle + p[0] * rCircle).toFixed(1)}},${{(cyCircle + p[1] * rCircle).toFixed(1)}}`).join(' ');
        const polyEl = el('polygon', {{points: pts, fill: d.color, stroke: '#fff', 'stroke-width': 1.5, style: 'cursor:pointer'}});
        polyEl.addEventListener('mouseenter', e => showTip(e, `<b>${{d.name}}</b><div class="row"><span>Volume</span><b>${{d.v}} 9L</b></div><div class="row"><span>Share</span><b>${{pct}}%</b></div>`));
        polyEl.addEventListener('mousemove', moveTip);
        polyEl.addEventListener('mouseleave', hideTip);
        svg.appendChild(polyEl);

        // Contraste dinámico
        const cHex = d.color.replace('#', '');
        const rC = parseInt(cHex.slice(0, 2), 16) / 255;
        const gC = parseInt(cHex.slice(2, 4), 16) / 255;
        const bC = parseInt(cHex.slice(4, 6), 16) / 255;
        const lum = 0.299 * rC + 0.587 * gC + 0.114 * bC;
        const txtColor = lum < 0.55 ? '#FFFFFF' : '#3A3A3A';

        const cent = _centroid(cell);
        const lx = cxCircle + cent[0] * rCircle;
        const ly = cyCircle + cent[1] * rCircle;

        if (frac >= 0.07) {{
          const shortName = d.name.length > 9 ? d.name.slice(0, 8) + '…' : d.name;
          svg.appendChild(el('text', {{x: lx, y: ly - 2, 'text-anchor': 'middle', style: `font-size:8px;font-weight:700;fill:${{txtColor}};pointer-events:none;`}})).textContent = shortName;
          svg.appendChild(el('text', {{x: lx, y: ly + 9, 'text-anchor': 'middle', style: `font-size:8.5px;font-weight:600;fill:${{txtColor}};pointer-events:none;`}})).textContent = `${{Math.round(frac * 100)}}%`;
        }} else if (frac >= 0.035) {{
          svg.appendChild(el('text', {{x: lx, y: ly + 3, 'text-anchor': 'middle', style: `font-size:7.5px;font-weight:600;fill:${{txtColor}};pointer-events:none;`}})).textContent = `${{Math.round(frac * 100)}}%`;
        }}

        if (legend) {{
          const row = document.createElement('div');
          row.className = 'legend item';
          row.style.marginBottom = '4px';
          row.innerHTML = `<span class="sw" style="background:${{d.color}}"></span><span>${{d.name}} &mdash; <b>${{pct}}%</b></span>`;
          legend.appendChild(row);
        }}
      }});
    }}
  }})();

  // ---------- 5. TOP ACCOUNTS BY LIFETIME BOTTLES (MAYOR A MENOR) ----------
  (function(){{
    const svg = document.getElementById('chartTopAccounts');
    // Cuentas reales, ya ordenadas por el procesador; se recorta al top 8.
    const data = (LOCO.accounts || []).slice(0, 8).map(a => ({{
      name: cellText(a.account),
      v: Math.round(num(a.bottles)),
      last: cellText(a.last_order),
      ch: cellText(a.channel)
    }}));
    if (!data.length) {{ return; }}
    data.sort((a,b)=>b.v - a.v);   // regla: mayor a menor

    const W = 560, H = 250, padL = 150, padR = 50, padT = 8, padB = 8;
    svg.setAttribute('viewBox', `0 0 ${{W}} ${{H}}`);
    const maxV = Math.max(...data.map(d=>d.v)) * 1.15;
    const rowH = (H-padT-padB)/data.length;
    const x = v => padL + (v/maxV)*(W-padL-padR);

    data.forEach((d,i)=>{{
      const cy = padT + rowH*i + rowH/2;
      const barH = rowH*0.55;
      svg.appendChild(el('text', {{class:'cat-label', x:padL-10, y:cy+4, 'text-anchor':'end'}})).textContent = d.name;
      const rect = el('rect', {{class:'bar-rect', x:padL, y:cy-barH/2, width:x(d.v)-padL, height:barH, rx:3, fill:COLORS.maroon, style:'cursor:pointer'}});
      rect.addEventListener('mouseenter', e=>showTip(e, `<b>${{d.name}}</b><div class="row"><span>Bottles (all sources)</span><b>${{d.v}}</b></div><div class="row"><span>Last order</span><b>${{d.last}}</b></div><div class="row"><span>Channel</span><b>${{d.ch}}</b></div>`));
      rect.addEventListener('mousemove', moveTip);
      rect.addEventListener('mouseleave', hideTip);
      svg.appendChild(rect);
      svg.appendChild(el('text', {{class:'val-label', x:x(d.v)+8, y:cy+4}})).textContent = d.v;
    }});
  }})();

  // ---------- 5b. WHOLESALE DISTRIBUTOR REVENUE (MAYOR A MENOR) ----------
  (function(){{
    const svg = document.getElementById('chartWholesale');
    // Distribuidores mayoristas reales (sell-in), ya ordenados por el procesador.
    const data = (LOCO.wholesale || []).map(w => {{
      const full = cellText(w.customer);
      return {{
        name: full.length > 26 ? full.slice(0, 25) + '…' : full,
        full: full,
        v: num(w.revenue),
        cases: num(w.cases_9l)
      }};
    }});
    if (!data.length) {{ return; }}
    data.sort((a,b)=>b.v - a.v);

    const W = 560, H = 250, padL = 165, padR = 60, padT = 20, padB = 20;
    svg.setAttribute('viewBox', `0 0 ${{W}} ${{H}}`);
    const maxV = Math.max(...data.map(d=>d.v)) * 1.15;
    const rowH = (H-padT-padB)/data.length;
    const x = v => padL + (v/maxV)*(W-padL-padR);

    data.forEach((d,i)=>{{
      const cy = padT + rowH*i + rowH/2;
      const barH = rowH*0.5;
      svg.appendChild(el('text', {{class:'cat-label', x:padL-10, y:cy+4, 'text-anchor':'end', style:'font-size:11px;'}})).textContent = d.name;
      const rect = el('rect', {{class:'bar-rect', x:padL, y:cy-barH/2, width:x(d.v)-padL, height:barH, rx:3, fill:COLORS.gold, style:'cursor:pointer'}});
      rect.addEventListener('mouseenter', e=>showTip(e, `<b>${{d.full}}</b><div class="row"><span>Revenue YTD</span><b>${{fmtMoney(d.v)}}</b></div>`));
      rect.addEventListener('mousemove', moveTip);
      rect.addEventListener('mouseleave', hideTip);
      svg.appendChild(rect);
      svg.appendChild(el('text', {{class:'val-label', x:x(d.v)+8, y:cy+4}})).textContent = fmtMoney(d.v);
    }});
  }})();

  // ---------- 7. WEEKLY SALESPERSON PERFORMANCE ----------
  (function(){{
    const svg = document.getElementById('chartWeekly');
    // Series semanales reales por vendedor. Serie de TIEMPO: orden cronológico.
    const repPalette = [COLORS.maroon, COLORS.gold, COLORS.teal,
                        COLORS.amber, COLORS.corazon, COLORS.slate];
    const allWeeks = (LOCO.weekly_weeks || []);
    const allReps = (LOCO.weekly_by_rep || []).map((r, i) => ({{
      name: cellText(r.rep),
      color: repPalette[i % repPalette.length],
      v: (r.values || []).map(num)
    }}));
    if (!allWeeks.length || !allReps.length) {{ return; }}

    function render(mode){{
      svg.innerHTML = '';
      const n = mode === '12w' ? 12 : allWeeks.length;
      const weeks = allWeeks.slice(allWeeks.length - n);
      const reps = allReps.map(r => ({{...r, v: r.v.slice(allWeeks.length - n)}}));

      const W = 900, H = 260, padL = 40, padR = 16, padT = 20, padB = 30;
      svg.setAttribute('viewBox', `0 0 ${{W}} ${{H}}`);
      let maxPos = 0, maxNeg = 0;
      weeks.forEach((w,i)=>{{
        let pos=0, neg=0;
        reps.forEach(r=>{{ const v=r.v[i]; if(v>=0) pos+=v; else neg+=v; }});
        maxPos = Math.max(maxPos,pos); maxNeg = Math.min(maxNeg,neg);
      }});
      const range = maxPos - maxNeg;
      const zeroY = padT + (maxPos/range)*(H-padT-padB);
      const scale = (H-padT-padB)/range;
      const slot = (W-padL-padR)/weeks.length;
      const bw = slot*(n<=12 ? 0.6 : 0.68);
      svg.appendChild(el('line', {{class:'baseline', x1:padL, x2:W-padR, y1:zeroY, y2:zeroY}}));

      weeks.forEach((w,i)=>{{
        const cx = padL + slot*i + slot/2;
        let yPos = zeroY, yNeg = zeroY;
        reps.forEach(r=>{{
          const v = r.v[i];
          if(v===0) return;
          const h = Math.abs(v)*scale;
          let y, color, note='';
          if(v>0){{ y = yPos - h; yPos = y; color = r.color; }}
          else {{ y = yNeg; yNeg = yNeg + h; color = COLORS.bad; note = ' (return/credit adj.)'; }}
          const rect = el('rect', {{class:'bar-rect', x:cx-bw/2, y, width:bw, height:Math.max(h,1), fill:color, style:'cursor:pointer'}});
          rect.addEventListener('mouseenter', e=>showTip(e, `<b>${{w}} &middot; ${{r.name}}</b><div class="row"><span>Bottles</span><b>${{v}}${{note}}</b></div>`));
          rect.addEventListener('mousemove', moveTip);
          rect.addEventListener('mouseleave', hideTip);
          svg.appendChild(rect);
        }});
        if(n <= 12){{
          svg.appendChild(el('text', {{class:'axis-label', x:cx, y:H-10, 'text-anchor':'middle'}})).textContent = w;
        }}
      }});
    }}

    const toggle = document.getElementById('weeklyToggle');
    toggle.addEventListener('click', (e)=>{{
      const btn = e.target.closest('.seg-btn');
      if(!btn) return;
      toggle.querySelectorAll('.seg-btn').forEach(b=>b.classList.remove('active'));
      btn.classList.add('active');
      render(btn.dataset.mode);
    }});

    render('12w');
  }})();

  // ---------- 8. INVENTORY HEALTH (MAYOR A MENOR) ----------
  (function(){{
    const svg = document.getElementById('chartInventory');
    // Inventario real por SKU. Solo líneas VENDIBLES: las muestras
    // ("NOT SELLABLE") se excluyen para cuadrar con el libro del cliente.
    const data = (LOCO.inventory || []).filter(r => r.sellable).map(r => ({{
      name: cellText(r.product),
      ca: num(r.ca_9l),
      tx: num(r.tx_9l)
    }}));
    if (!data.length) {{ return; }}
    // Barras agrupadas CA/TX ordenadas de mayor a menor por el TOTAL de la fila.
    data.sort((a,b)=>(b.ca+b.tx) - (a.ca+a.tx));

    const W = 900, H = 230, padL = 170, padR = 60, padT = 10, padB = 10;
    svg.setAttribute('viewBox', `0 0 ${{W}} ${{H}}`);
    const maxV = Math.max(...data.map(d=>d.ca+d.tx)) * 1.15;
    const rowH = (H-padT-padB)/data.length;
    const x = v => padL + (v/maxV)*(W-padL-padR);

    data.forEach((d,i)=>{{
      const cy = padT + rowH*i + rowH/2;
      const barH = rowH*0.5;
      svg.appendChild(el('text', {{class:'cat-label', x:padL-10, y:cy+4, 'text-anchor':'end'}})).textContent = d.name;
      const rCA = el('rect', {{class:'bar-rect', x:padL, y:cy-barH/2, width:x(d.ca)-padL, height:barH, fill:COLORS.maroon, style:'cursor:pointer'}});
      rCA.addEventListener('mouseenter', e=>showTip(e, `<b>${{d.name}} &mdash; CA</b><div class="row"><span>On Hand</span><b>${{cases9l(d.ca)}}</b></div>`));
      rCA.addEventListener('mousemove', moveTip); rCA.addEventListener('mouseleave', hideTip);
      svg.appendChild(rCA);
      if(d.tx>0){{
        const rTX = el('rect', {{class:'bar-rect', x:x(d.ca)+2, y:cy-barH/2, width:Math.max(x(d.ca+d.tx)-x(d.ca)-2,0), height:barH, fill:COLORS.gold, style:'cursor:pointer'}});
        rTX.addEventListener('mouseenter', e=>showTip(e, `<b>${{d.name}} &mdash; TX</b><div class="row"><span>On Hand</span><b>${{cases9l(d.tx)}}</b></div>`));
        rTX.addEventListener('mousemove', moveTip); rTX.addEventListener('mouseleave', hideTip);
        svg.appendChild(rTX);
      }}
      svg.appendChild(el('text', {{class:'val-label', x:x(d.ca+d.tx)+8, y:cy+4}})).textContent = cases9l(d.ca+d.tx);
    }});
    const legend = document.createElement('div'); legend.className='legend';
    legend.innerHTML = `<span class="item"><span class="sw" style="background:${{COLORS.maroon}}"></span>California (On Hand)</span><span class="item"><span class="sw" style="background:${{COLORS.gold}}"></span>Texas (On Hand)</span>`;
    svg.parentElement.after(legend);
  }})();

  // ======================================================================
  //  TABLAS Y BLOQUES NUEVOS
  //  Sustituyen los dos bloques que antes pintaban datos INVENTADOS
  //  (cadencia de cuentas y rejilla de sparklines eran arreglos literales
  //  dentro de esta plantilla, con nombres de cuenta y de vendedor que no
  //  salían de ningún archivo). Ahora todo viene de LOCO_DATA.
  // ======================================================================

  function tbl(id){{ const t = document.getElementById(id); if(t) t.innerHTML=''; return t; }}
  function row(parent, cells, cls){{
    const tr = document.createElement('tr');
    if(cls) tr.className = cls;
    cells.forEach(c => {{
      const td = document.createElement(c.th ? 'th' : 'td');
      if(c.num) td.className = 'num';
      if(c.cls) td.className = (td.className ? td.className+' ' : '') + c.cls;
      if(c.html !== undefined) td.innerHTML = c.html; else td.textContent = c.text;
      if(c.span) td.colSpan = c.span;
      tr.appendChild(td);
    }});
    parent.appendChild(tr);
    return tr;
  }}
  function head(t, cols){{
    const thead = document.createElement('thead');
    row(thead, cols.map(c => typeof c === 'string'
      ? {{th:true, text:c}} : {{th:true, text:c.t, num:c.num}}));
    t.appendChild(thead);
    const tb = document.createElement('tbody'); t.appendChild(tb); return tb;
  }}
  function zeroCls(v){{ return Number(v) ? '' : 'zero'; }}
  function setText(id, s){{ const e = document.getElementById(id); if(e) e.textContent = s; }}
  function setHtml(id, s){{ const e = document.getElementById(id); if(e) e.innerHTML = s; }}
  function hide(id){{ const e = document.getElementById(id); if(e) e.style.display = 'none'; }}

  // ---------- rejilla mes a mes (Signature y Favorite Brands) ----------
  function monthGrid(tableId, months, rows, unitLabel){{
    const t = tbl(tableId); if(!t) return;
    if(!rows || !rows.length){{ row(t, [{{text:'No data in this feed.', span:2}}]); return; }}
    const tb = head(t, [{{t:'Account'}}, {{t:'YTD', num:true}}, {{t:'9L', num:true}}]
      .concat(months.map(m => ({{t:m, num:true}}))));
    const totals = months.map(()=>0); let tY=0, tC=0;
    rows.forEach(r => {{
      tY += num(r.bottles_ytd); tC += num(r.cases_9l_ytd);
      (r.by_month||[]).forEach((v,i)=> totals[i] += num(v));
      row(tb, [{{text: cellText(r.name)}},
               {{text: nfmt(r.bottles_ytd,'bottles'), num:true}},
               {{text: nfmt(r.cases_9l_ytd,'cases'), num:true}}]
        .concat((r.by_month||[]).map(v => ({{
          text: Number(v) ? nfmt(v,'bottles') : '-', num:true, cls: zeroCls(v)}}))));
    }});
    row(tb, [{{text:'TOTAL'}}, {{text:nfmt(tY,'bottles'), num:true}},
             {{text:nfmt(tC,'cases'), num:true}}]
      .concat(totals.map(v => ({{text:nfmt(v,'bottles'), num:true}}))), 'total-row');
    return {{bottles:tY, cases:tC}};
  }}

  // ---------- 3. SIGNATURE (CA) ----------
  (function(){{
    const S = LOCO.signature || {{}};
    const months = S.months || [];
    const tot = monthGrid('sigAccTable', months, S.by_account, 'bottles');
    setText('sigAccSub', tot
      ? `${{(S.by_account||[]).length}} accounts - ${{nfmt(tot.bottles,'bottles')}} bottles year to date - ${{nfmt(S.orders_ytd,'bottles')}} orders`
      : 'No California feed found.');
    hbars('chartSigSku', (S.by_sku||[]).map(r=>({{
      name: cellText(r.name), v: num(r.bottles_ytd)}})), v=>nfmt(v,'bottles')+' btl');
    hbars('chartSigCity', (S.by_city||[]).slice(0,10).map(r=>({{
      name: cellText(r.name), v: num(r.bottles_ytd)}})), v=>nfmt(v,'bottles')+' btl');
  }})();

  // ---------- 4. FAVORITE BRANDS (TX) ----------
  (function(){{
    const F = LOCO.favorite_brands || {{}};
    const months = F.months || [];
    const tot = monthGrid('fbAccTable', months, F.by_account, 'bottles');
    setText('fbAccSub', tot
      ? `${{(F.by_account||[]).length}} accounts - ${{nfmt(tot.bottles,'bottles')}} bottles year to date`
      : 'No Texas feed found.');
    hbars('chartFbSku', (F.by_sku||[]).map(r=>({{
      name: cellText(r.name), v: num(r.bottles_ytd)}})), v=>nfmt(v,'bottles')+' btl');
    hbars('chartFbPremise', (F.by_premise||[]).map(r=>({{
      name: cellText(r.name), v: num(r.bottles_ytd)}})), v=>nfmt(v,'bottles')+' btl');
    const t = tbl('fbRepTable');
    if(t){{
      const tb = head(t, [{{t:'Favorite Brands rep'}}, {{t:'Bottles YTD', num:true}}]);
      (F.by_distributor_rep||[]).forEach(r => row(tb, [
        {{text: cellText(r.name)}},
        {{text: nfmt(r.bottles_ytd,'bottles'), num:true}}]));
      if(!(F.by_distributor_rep||[]).length)
        row(tb, [{{text:'The depletion report carries no SALES REP column.', span:2}}]);
    }}
  }})();

  // ---------- 5. INVENTARIO POR BODEGA ----------
  (function(){{
    const rows = LOCO.inventory || [];
    const t = tbl('invTable');
    if(t){{
      const tb = head(t, [{{t:'SKU'}}, {{t:'Total 9L', num:true}},
        {{t:'CA total', num:true}}, {{t:'SGWS SoCal', num:true}},
        {{t:'SGWS NorCal', num:true}}, {{t:'Park Street CA', num:true}},
        {{t:'TX total', num:true}}, {{t:'Favorite Brands TX', num:true}}]);
      const ks = ['total_9l','ca_9l','socal_sgws_9l','norcal_sgws_9l',
                  'parkstreet_ca_9l','tx_9l','fb_tx_9l'];
      const tot = ks.map(()=>0);
      rows.filter(r=>r.sellable).forEach(r => {{
        ks.forEach((k,i)=> tot[i] += num(r[k]));
        row(tb, [{{text: cellText(r.product)}}].concat(
          ks.map(k => ({{text: Number(r[k]) ? nfmt(r[k],'cases') : '-',
                        num:true, cls: zeroCls(r[k])}}))));
      }});
      row(tb, [{{text:'TOTAL SELLABLE'}}].concat(
        tot.map(v=>({{text:nfmt(v,'cases'), num:true}}))), 'total-row');
      const smp = rows.filter(r=>!r.sellable);
      smp.forEach(r => row(tb, [{{text: cellText(r.product) + '  (not sellable)'}}].concat(
        ks.map(k => ({{text: Number(r[k]) ? nfmt(r[k],'cases') : '-',
                      num:true, cls: zeroCls(r[k])}})))));
    }}
    hbars('chartWarehouse', (LOCO.inventory_by_warehouse||[]).map(r=>({{
      name: cellText(r.warehouse), v: num(r.cases_9l)}})), v=>cases9l(v));
  }})();

  // ---------- 6. POD ----------
  (function(){{
    const pod = LOCO.pod || [];
    const strip = document.getElementById('podRow');
    if(strip){{
      strip.innerHTML = '';
      pod.forEach(p => {{
        const d = document.createElement('div'); d.className = 'kpi';
        d.innerHTML = `<div class="kpi-label">${{cellText(p.channel)}}</div>`
          + `<div class="kpi-value">${{nfmt(p.accounts,'bottles')}}</div>`
          + `<div class="kpi-sub">${{nfmt(p.bottles,'bottles')}} bottles - ${{nfmt(p.orders_ytd,'bottles')}} orders YTD</div>`;
        strip.appendChild(d);
      }});
    }}
    const t = tbl('podTable');
    if(t){{
      const tb = head(t, [{{t:'Account'}}, {{t:'Channel'}}, {{t:'Salesperson'}},
        {{t:'Bottles', num:true}}, {{t:'Orders YTD', num:true}},
        {{t:'Last order'}}, {{t:'Resolved by'}}]);
      (LOCO.accounts||[]).slice(0,60).forEach(a => row(tb, [
        {{text: cellText(a.account)}},
        {{text: cellText(a.channel)}},
        {{text: cellText(a.salesperson)}},
        {{text: nfmt(a.bottles,'bottles'), num:true}},
        {{text: Number(a.orders_ytd) ? nfmt(a.orders_ytd,'bottles') : '-', num:true,
          cls: zeroCls(a.orders_ytd)}},
        {{text: cellText(a.last_order)}},
        {{html: `<span class="rule-badge${{a.attr_rule==='R6'?' unres':''}}">${{cellText(a.attr_rule)}}</span>`}}]));
    }}
  }})();

  // ---------- 7. DTC POR TIENDA ----------
  (function(){{
    const stores = LOCO.dtc_by_store || [];
    const strip = document.getElementById('dtcRow');
    if(strip){{
      strip.innerHTML = '';
      stores.forEach(s => {{
        const d = document.createElement('div'); d.className = 'kpi';
        d.innerHTML = `<div class="kpi-label">${{cellText(s.stream)}}</div>`
          + `<div class="kpi-value">${{nfmt(s.bottles,'bottles')}}</div>`
          + `<div class="kpi-sub">bottles - ${{nfmt(s.orders,'bottles')}} orders - ${{fmtMoney(s.revenue)}}</div>`;
        strip.appendChild(d);
      }});
    }}
    // Serie mensual por tienda. Serie de TIEMPO: orden por mes, no por valor.
    const MO = ['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC'];
    const present = MO.filter(m => stores.some(s => (s.by_month||{{}})[m] !== undefined));
    const svg = document.getElementById('chartDtcMonth');
    if(svg && present.length){{
      const W=560,H=230,P={{t:16,r:16,b:30,l:42}};
      svg.setAttribute('viewBox', `0 0 ${{W}} ${{H}}`);
      const maxV = Math.max(1, ...stores.flatMap(s => present.map(m => num((s.by_month||{{}})[m]))));
      const x = i => P.l + (i*(W-P.l-P.r)/Math.max(1,present.length-1));
      const y = v => H-P.b - (v/maxV)*(H-P.t-P.b);
      const cols=[COLORS.maroon, COLORS.gold];
      svg.appendChild(el('line', {{x1:P.l, y1:H-P.b, x2:W-P.r, y2:H-P.b, stroke:'rgba(0,0,0,.16)'}}));
      present.forEach((m,i)=> svg.appendChild(el('text', {{x:x(i), y:H-P.b+16,
        'text-anchor':'middle', style:'font-size:9px;fill:#8a8a8a;'}})).textContent = m);
      stores.forEach((s,si)=>{{
        const pts = present.map((m,i)=> `${{x(i)}},${{y(num((s.by_month||{{}})[m]))}}`).join(' ');
        svg.appendChild(el('polyline', {{points:pts, fill:'none',
          stroke:cols[si%cols.length], 'stroke-width':2.2}}));
        present.forEach((m,i)=>{{
          const v = num((s.by_month||{{}})[m]);
          const c = el('circle', {{cx:x(i), cy:y(v), r:3.4, fill:cols[si%cols.length]}});
          c.addEventListener('mouseenter', e=>showTip(e,
            `<b>${{cellText(s.stream)}} - ${{m}}</b><div class="row"><span>Bottles</span><b>${{nfmt(v,'bottles')}}</b></div>`));
          c.addEventListener('mousemove', moveTip);
          c.addEventListener('mouseleave', hideTip);
          svg.appendChild(c);
        }});
      }});
      const lg = document.createElement('div'); lg.className='legend';
      lg.innerHTML = stores.map((s,i)=>`<span class="item"><span class="sw" style="background:${{cols[i%cols.length]}}"></span>${{cellText(s.stream)}}</span>`).join('');
      svg.parentElement.after(lg);
    }}
    const skuAgg = {{}};
    stores.forEach(s => (s.by_sku||[]).forEach(k => {{
      skuAgg[cellText(k.sku)] = (skuAgg[cellText(k.sku)]||0) + num(k.bottles);
    }}));
    hbars('chartDtcSku', Object.entries(skuAgg).map(([n,v])=>({{name:n, v:v}})),
          v=>nfmt(v,'bottles')+' btl');
    const t = tbl('dtcTable');
    if(t){{
      const tb = head(t, [{{t:'Store'}}, {{t:'Bottles', num:true}},
        {{t:'Orders', num:true}}, {{t:'Revenue', num:true}}, {{t:'Top SKU'}}]);
      stores.forEach(s => row(tb, [
        {{text: cellText(s.stream)}},
        {{text: nfmt(s.bottles,'bottles'), num:true}},
        {{text: nfmt(s.orders,'bottles'), num:true}},
        {{text: fmtMoney(s.revenue), num:true}},
        {{text: (s.by_sku&&s.by_sku[0]) ? cellText(s.by_sku[0].sku) : BLANK}}]));
    }}
  }})();

  // ---------- 8. FUENTES Y METODOLOGÍA ----------
  (function(){{
    const t = tbl('provTable');
    if(t){{
      const tb = head(t, [{{t:'Measure'}}, {{t:'Source file'}}, {{t:'Basis'}},
                          {{t:'Conversion applied'}}, {{t:'Amount', num:true}}]);
      (LOCO.provenance||[]).forEach(p => row(tb, [
        {{text: cellText(p.measure)}}, {{text: cellText(p.source)}},
        {{text: cellText(p.basis)}}, {{text: cellText(p.transform)}},
        {{text: cellText(p.amount), num:true}}]));
    }}
    setHtml('unitRules',
      '<li>Signature / SGWS quantities arrive as 4.5L case equivalents: <code>x6</code> to reach 750mL bottles.</li>'
      + '<li>Park Street converts per row from its own <code>Unit</code> column: <code>x6</code> when it reads Cases, <code>x1</code> when it reads Bottles.</li>'
      + '<li>Favorite Brands reports bottles directly. No conversion.</li>'
      + '<li>9L cases = bottles <code>/12</code>, <b>except 200mL Blanco</b>, which is bottles <code>/45</code> (9000mL divided by 200mL). This conversion is computed once, at the data layer, so a rounded figure is never divided again downstream.</li>'
      + '<li>Wholesale revenue sums the per-line amount. The order-level total repeats on every line of the same order and would multiply the same order.</li>');

    const M = LOCO.margin || {{}};
    if(M.available){{
      setText('marginProv', cellText(M.provenance));
      const mt = tbl('marginTable');
      if(mt){{
        const tb = head(mt, [{{t:'SKU'}}, {{t:'Channel'}}, {{t:'Rate / bottle', num:true}},
          {{t:'Bottles', num:true}}, {{t:'9L', num:true}},
          {{t:'Gross margin', num:true}}, {{t:'GM / 9L', num:true}}]);
        (M.rows||[]).forEach(r => row(tb, [
          {{text: cellText(r.sku)}}, {{text: cellText(r.channel)}},
          {{text: r.rate_per_bottle===null||r.rate_per_bottle===undefined
                  ? 'no rate' : fmtMoney(r.rate_per_bottle), num:true,
            cls: (r.rate_per_bottle===null||r.rate_per_bottle===undefined)?'reason':''}},
          {{text: nfmt(r.bottles,'bottles'), num:true}},
          {{text: nfmt(r.cases_9l,'cases'), num:true}},
          {{text: fmtMoney(r.gross_margin), num:true}},
          {{text: fmtMoney(r.gm_per_9l), num:true}}]));
        row(tb, [{{text:'TOTAL'}}, {{text:''}}, {{text:''}},
          {{text:nfmt(M.bottles,'bottles'), num:true}},
          {{text:nfmt(M.cases_9l,'cases'), num:true}},
          {{text:fmtMoney(M.total), num:true}},
          {{text:fmtMoney(M.gm_per_9l), num:true}}], 'total-row');
        (M.unmatched_skus||[]).forEach(u => row(tb, [
          {{html:`<b>No margin rate:</b> ${{cellText(u.sku)}}`, span:5, cls:'reason'}},
          {{text:nfmt(u.bottles,'bottles')+' btl', num:true}}, {{text:''}}]));
      }}
    }} else {{
      hide('marginCard');
    }}

    const A = LOCO.attribution || {{}};
    const lt = tbl('ladderTable');
    if(lt){{
      const tb = head(lt, [{{t:'Rule'}}, {{t:'How the line was resolved'}},
        {{t:'Lines', num:true}}, {{t:'Bottles', num:true}}, {{t:'Share', num:true}}]);
      (A.by_rule||[]).forEach(r => row(tb, [
        {{html:`<span class="rule-badge${{r.rule==='R6'?' unres':''}}">${{cellText(r.rule)}}</span>`}},
        {{text: cellText(r.label)}},
        {{text: nfmt(r.lines,'bottles'), num:true}},
        {{text: nfmt(r.bottles,'bottles'), num:true}},
        {{text: nfmt(r.pct,'pct')+'%', num:true}}]));
      row(tb, [{{text:'TOTAL'}}, {{text:''}}, {{text:''}},
        {{text:nfmt(A.total_bottles,'bottles'), num:true}},
        {{text:'100.0%', num:true}}], 'total-row');
    }}
    setText('unattrSub', `${{nfmt(A.unattributed_bottles,'bottles')}} of ${{nfmt(A.total_bottles,'bottles')}} bottles could not be credited to a salesperson. They are counted in every total so the numbers still balance; listing them here with the reason is what makes them fixable at the source.`);
    const ut = tbl('unattrTable');
    if(ut){{
      const tb = head(ut, [{{t:'Account or order'}}, {{t:'Bottles', num:true}},
        {{t:'Why it could not be credited'}}, {{t:'Closest names in the map'}}]);
      (A.unattributed||[]).forEach(u => row(tb, [
        {{text: cellText(u.account)}},
        {{text: nfmt(u.bottles,'bottles'), num:true}},
        {{text: cellText(u.reason), cls:'reason'}},
        {{text: u.candidates ? cellText(u.candidates) : BLANK, cls:'reason'}}]));
      if(!(A.unattributed||[]).length)
        row(tb, [{{text:'Every line is credited to a salesperson.', span:4}}]);
    }}

    const gaps = Object.values(LOCO.gaps||{{}}).filter(Boolean);
    if(gaps.length) setHtml('gapsList', gaps.map(g=>`<li>${{cellText(g)}}</li>`).join(''));
    else hide('gapsCard');
  }})();

  // ---------- NOTA Y CHIPS DE TRAZABILIDAD ----------
  // Cada chip nombra el insumo real del que sale su bloque.
  (function(){{
    const A = LOCO.attribution || {{}};
    const F = LOCO.favorite_brands || {{}};
    setText('srcTrend', 'Signature YTD by Month + Favorite Brands depletion report');
    setText('srcMix', 'Depletions by territory + ecommerce line items');
    setText('srcReps', 'Account map + order tags - see Sources tab');
    setText('srcWeekly', 'Sources carrying a transaction date only');
    setText('srcSig', 'YTD by Month [Bottles, Orders].xlsx');
    setText('srcFb', cellText(F.snapshot) !== BLANK
      ? `Favorite Brands depletion report - ${{cellText(F.snapshot)}}`
      : 'Favorite Brands depletion report');
    setText('srcInv', 'Supplier Inventory + Inventory History + InventoryByLocation');
    setText('srcPod', 'SalesOrdersSummary + PREMISE column');
    setText('srcDtc', 'orders_export Shopify + orders_export Memory Bottles');
    setHtml('repsNote',
      `<b>${{nfmt(A.attributed_pct,'pct')}}% of bottles are credited to a named salesperson.</b> `
      + `The remaining ${{nfmt(A.unattributed_bottles,'bottles')}} bottles are listed one by one, with the reason, in the Sources tab. `
      + `Texas depletions arrive as a cumulative snapshot with no transaction date, so they appear in the Favorite Brands tab but not in the weekly series below.`);

    // Rejilla rep x semana
    const t = tbl('repWeekTable');
    if(t){{
      const weeks = LOCO.weekly_weeks || [];
      const reps = LOCO.weekly_by_rep || [];
      const tb = head(t, [{{t:'Salesperson'}}, {{t:'Total', num:true}}]
        .concat(weeks.map(w => ({{t:w.slice(5), num:true}}))));
      const colTot = weeks.map(()=>0);
      reps.forEach(r => {{
        const vals = r.values || [];
        const tot = vals.reduce((a,b)=>a+num(b),0);
        vals.forEach((v,i)=> colTot[i] += num(v));
        row(tb, [{{text: cellText(r.rep)}}, {{text: nfmt(tot,'bottles'), num:true}}]
          .concat(vals.map(v => ({{text: Number(v) ? nfmt(v,'bottles') : '-',
                                  num:true, cls: zeroCls(v)}}))));
      }});
      row(tb, [{{text:'TOTAL'}},
        {{text:nfmt(colTot.reduce((a,b)=>a+b,0),'bottles'), num:true}}]
        .concat(colTot.map(v=>({{text:nfmt(v,'bottles'), num:true}}))), 'total-row');
    }}
  }})();

  // ---------- NAVEGACIÓN DE PESTAÑAS ----------
  // Patrón tomado del tablero unificado de Sullivan: array declarativo, click
  // delegado, ARIA, y la navegación oculta al imprimir.
  (function(){{
    const TABS = [
      {{id:'p-over', label:'Overview',        num:'1'}},
      {{id:'p-reps', label:'Salespeople',     num:'2'}},
      {{id:'p-sig',  label:'Signature',       num:'3'}},
      {{id:'p-fb',   label:'Favorite Brands', num:'4'}},
      {{id:'p-inv',  label:'Inventory',       num:'5'}},
      {{id:'p-pod',  label:'POD accounts',    num:'6'}},
      {{id:'p-dtc',  label:'DTC',             num:'7'}},
      {{id:'p-src',  label:'Sources',         num:'8'}}
    ];
    const nav = document.getElementById('tabs');
    if(!nav) return;
    TABS.forEach(t => {{
      const b = document.createElement('button');
      b.type = 'button';
      b.setAttribute('role','tab');
      b.setAttribute('aria-selected','false');
      b.dataset.target = t.id;
      b.innerHTML = `<span class="tnum">${{t.num}}</span>${{t.label}}`;
      nav.appendChild(b);
    }});
    function show(id){{
      TABS.forEach(t => {{
        const p = document.getElementById(t.id);
        if(p) p.classList.toggle('is-active', t.id === id);
      }});
      nav.querySelectorAll('button').forEach(b =>
        b.setAttribute('aria-selected', String(b.dataset.target === id)));
    }}
    nav.addEventListener('click', e => {{
      const b = e.target.closest('button');
      if(b && b.dataset.target) show(b.dataset.target);
    }});
    show(TABS[0].id);
  }})();

}})();
</script>

</body>
</html>
"""


def generate_loco_tequila_dashboard(output_file: Path,
                                    data_dir: Optional[Path] = None,
                                    account_map_path: Optional[str] = None,
                                    data: Optional[Dict[str, Any]] = None,
                                    lang: str = i18n.DEFAULT_LANG) -> Path:
    """
    Genera el dashboard directivo de Loco Tequila USA a partir de datos REALES.

    Antes esta función solo recibía `output_file` y todas las cifras vivían
    incrustadas en la plantilla JS: el archivo era una maqueta, no un reporte.
    Ahora lee la carpeta de datos (por defecto Client_Data/Loco_tequila_usa_data,
    o la que el usuario indique con --data-dir) mediante loco_data_processor.
    """
    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    if data is None:
        data = process_loco_data(data_dir, account_map_path)

    logo_uri = get_logo_white_data_uri()
    logo_tag = f'<img src="{logo_uri}" class="hero-logo" alt="Loco Tequila USA" />' if logo_uri else ""

    html = HTML_TEMPLATE.format(
        logo_img_tag=logo_tag,
        # allow_nan=False tras sanitizar: un NaN nunca puede imprimirse como
        # "NaN" en un reporte para el cliente; si se cuela, el script falla.
        report_data_json=json.dumps(sanitize_for_json(data), allow_nan=False),
        period_label=data.get("period_label", BLANK),
    )
    # Este tablero nació con parte de su texto en español y el resto en
    # inglés. La tabla es bidireccional, así que ahora sale íntegro en el
    # idioma elegido, venga de donde venga cada cadena.
    html = i18n.inject(html, lang)
    output_file.write_text(html, encoding="utf-8")
    return output_file


# Alias retrocompatible: el orquestador y AGENTS.md referían al nombre "_demo".
def generate_loco_tequila_dashboard_demo(output_file: Path, **kwargs) -> Path:
    return generate_loco_tequila_dashboard(output_file, **kwargs)


if __name__ == "__main__":
    import argparse
    import sys

    for _s in (sys.stdout, sys.stderr):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError, OSError):
            pass

    ap = argparse.ArgumentParser(
        description="Genera el dashboard directivo de Loco Tequila USA con datos reales.")
    ap.add_argument("--data-dir", default=None,
                    help="Carpeta con los archivos crudos de Loco Tequila USA.")
    ap.add_argument("--account-map", default=None,
                    help="CSV opcional cuenta → vendedor → canal comercial.")
    ap.add_argument("--output", default=None, help="Ruta del HTML de salida.")
    args = ap.parse_args()

    out = Path(args.output) if args.output else (
        PROJECT_ROOT / "Output" / "loco_tequila_usa_dashboard.html")
    if not out.is_absolute():
        out = PROJECT_ROOT / out
    generate_loco_tequila_dashboard(out, args.data_dir, args.account_map)
    print(f"Dashboard de Loco Tequila USA generado en: {out}")
