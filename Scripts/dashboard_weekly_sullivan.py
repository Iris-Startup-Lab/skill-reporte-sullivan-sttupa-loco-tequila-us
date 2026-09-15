"""
================================================================================
 SULLIVAN RUTHERFORD ESTATE — GENERADOR DE DASHBOARD SEMANAL
================================================================================
 Genera el dashboard semanal standalone de Sullivan Rutherford Estate:
   - DTC Sales by Channel (9 canales + Tock + cascada directiva).
   - Distribution Snapshot (Cash, Open POs, Depletions).
   - Distribution PO Aging (semáforo 0-15d, 16-30d, >30d overdue).
   - Distribution Cash by Region (chips regionales y estado de espera).
   - Depletions by State (cajas 9L Southern Glazer's).
   - Depletions by Distributor (Southern Glazer's vs Favorite Brands).
   - Inventory & Supply status table.
 
 Gobernado estrictamente por Designs/Design_sullivan.md:
   - Paleta: Navy #003057, Deep Navy #001A30, Gold #D9B24E, Tan #A67C52, Cream #FFFBEF.
   - Tipografía: EB Garamond.
   - Logotipo oficial de Sullivan en alta resolución (base64).
================================================================================
"""

import base64
import json
import math
import re
from pathlib import Path
from typing import Any, Dict

from sullivan_weekly_processor import (process_sullivan_weekly_data,
                                      process_sullivan_weekly_series,
                                      weekly_output_name)
import i18n


def sanitize_for_json(obj):
    """
    Reemplaza NaN / Infinity por None en toda la estructura antes de serializar.
    `json.dumps` los emite por defecto como los literales `NaN` / `Infinity`, que
    son JSON inválido pero JS válido: el navegador los pintaba tal cual en las
    celdas. Tras esta pasada se serializa con allow_nan=False, de modo que si
    alguna vez se cuela un NaN el script falla en voz alta en vez de publicar
    "NaN" en un reporte para el cliente.
    """
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

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOGO_BLACK_SVG = PROJECT_ROOT / "Imagenes_iconos" / "Sullivan-Black.svg"
LOGO_WHITE_SVG = PROJECT_ROOT / "Imagenes_iconos" / "Sullivan-White.svg"
LOGO_WHITE_PNG = PROJECT_ROOT / "Imagenes_iconos" / "Sullivan-White.png"


def _recolor_svg_to_white(raw: bytes) -> bytes:
    text = raw.decode("utf-8", errors="ignore")
    text = re.sub(r'fill="#(?:000000|000)"', 'fill="#FFFFFF"', text, flags=re.IGNORECASE)
    text = re.sub(r'stroke="#(?:000000|000)"', 'stroke="#FFFFFF"', text, flags=re.IGNORECASE)
    return text.encode("utf-8")


def get_logo_white_data_uri() -> str:
    if LOGO_WHITE_SVG.exists() and LOGO_WHITE_SVG.stat().st_size > 100:
        raw = LOGO_WHITE_SVG.read_bytes()
        if re.search(rb"<path|<rect|<circle|<polygon|<line|<text", raw):
            return f"data:image/svg+xml;base64,{base64.b64encode(raw).decode('ascii')}"
    if LOGO_BLACK_SVG.exists() and LOGO_BLACK_SVG.stat().st_size > 100:
        raw = LOGO_BLACK_SVG.read_bytes()
        if re.search(rb"<path|<rect|<circle|<polygon|<line|<text", raw):
            white = _recolor_svg_to_white(raw)
            return f"data:image/svg+xml;base64,{base64.b64encode(white).decode('ascii')}"
    if LOGO_WHITE_PNG.exists():
        return f"data:image/png;base64,{base64.b64encode(LOGO_WHITE_PNG.read_bytes()).decode('ascii')}"
    return ""


HTML_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>{page_title}</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=EB+Garamond:ital,wght@0,400..800;1,400..800&family=Inter:wght@400;500;600;700&display=swap');

  :root {{
    color-scheme: light;
    --navy:        #003057;
    --navy-2:      #001A30;
    --gold:        #D9B24E;
    --tan:         #A67C52;
    --gold-soft:   #FFFBEF;
    --page:        #F8F7F4;
    --card:        #FFFFFF;
    --ink:         #1C2430;
    --ink-2:       #5C5548;
    --ink-muted:   #8C8476;
    --hair:        #E5DFC9;
    --good:        #1E4E2E;
    --good-bg:     #E8F2EA;
    --warn:        #A9791F;
    --warn-bg:     #FCF6E8;
    --critical:    #8C2F2F;
    --critical-bg: #FBEAEA;
    --seq-primary: #003057;
    --seq-hover:   #00447C;
    --shadow: 0 1px 3px rgba(0,48,87,0.06), 0 8px 24px -8px rgba(0,48,87,0.12);
  }}

  * {{ box-sizing: border-box; }}
  body {{
    background: var(--page);
    color: var(--ink);
    font-family: 'EB Garamond', Georgia, serif;
    margin: 0;
    line-height: 1.5;
  }}

  .sans {{ font-family: 'Inter', system-ui, -apple-system, sans-serif; }}

  .hero {{
    background: var(--navy);
    color: #FFFFFF;
    padding: 28px 32px 24px;
    border-bottom: 3px solid var(--gold);
  }}
  .hero-inner {{
    max-width: 1180px;
    margin: 0 auto;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 20px;
  }}
  .hero-brand {{
    display: flex;
    align-items: center;
    gap: 24px;
  }}
  .hero-logo {{
    height: 48px;
    filter: brightness(0) invert(1);
  }}
  .eyebrow {{
    font-family: 'Inter', sans-serif;
    font-size: 11px;
    letter-spacing: .18em;
    text-transform: uppercase;
    color: var(--gold);
    font-weight: 600;
    margin: 0 0 6px;
  }}
  .hero h1 {{
    font-size: 28px;
    font-weight: 700;
    margin: 0 0 4px;
    letter-spacing: 0.01em;
  }}
  .hero p {{
    margin: 0;
    font-size: 14.5px;
    color: #E2E8F0;
    max-width: 680px;
    line-height: 1.45;
  }}
  .badge-governance {{
    font-family: 'Inter', sans-serif;
    font-size: 11px;
    background: rgba(217, 178, 78, 0.15);
    border: 1px solid var(--gold);
    color: #FFFFFF;
    padding: 6px 12px;
    border-radius: 4px;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    white-space: nowrap;
  }}

  .filterbar {{
    background: var(--navy-2);
    color: #FFFFFF;
    padding: 12px 32px;
    font-family: 'Inter', sans-serif;
  }}
  .filterbar-inner {{
    max-width: 1180px;
    margin: 0 auto;
    display: flex;
    align-items: center;
    gap: 16px;
    flex-wrap: wrap;
  }}
  .filterbar label {{
    font-size: 12px;
    letter-spacing: .06em;
    text-transform: uppercase;
    color: var(--gold);
    font-weight: 600;
  }}
  .filterbar select {{
    background: #002240;
    color: #FFFFFF;
    border: 1px solid var(--tan);
    border-radius: 4px;
    padding: 6px 12px;
    font-size: 13px;
    font-family: inherit;
  }}
  .filterbar .hint {{
    font-size: 12px;
    color: #A0AEC0;
  }}

  .wrap {{
    max-width: 1180px;
    margin: 0 auto;
    padding: 32px 24px 80px;
  }}

  .section {{
    margin-bottom: 36px;
  }}
  .section-head {{
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 16px;
    margin-bottom: 14px;
    border-bottom: 1px solid var(--hair);
    padding-bottom: 10px;
    flex-wrap: wrap;
  }}
  .section-title-wrap {{
    display: flex;
    align-items: center;
    gap: 10px;
  }}
  .section-num {{
    width: 26px;
    height: 26px;
    border-radius: 50%;
    background: var(--navy);
    color: var(--gold);
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: 'Inter', sans-serif;
    font-size: 12px;
    font-weight: 700;
    flex: none;
  }}
  .section-title {{
    font-size: 22px;
    font-weight: 700;
    color: var(--navy);
    margin: 0;
    letter-spacing: 0.01em;
  }}
  .section-sub {{
    font-size: 13.5px;
    color: var(--ink-2);
    margin: 4px 0 0 36px;
  }}

  .status-pill {{
    font-family: 'Inter', sans-serif;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 11px;
    font-weight: 600;
    padding: 4px 10px;
    border-radius: 999px;
    white-space: nowrap;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }}
  .status-pill .dot {{ width: 7px; height: 7px; border-radius: 50%; }}
  .status-pill.live {{ background: var(--good-bg); color: var(--good); border: 1px solid #B8DCBD; }}
  .status-pill.live .dot {{ background: var(--good); }}
  .status-pill.wait {{ background: var(--warn-bg); color: var(--warn); border: 1px solid #E8D39E; }}
  .status-pill.wait .dot {{ background: var(--warn); }}

  .card {{
    background: var(--card);
    border: 1px solid var(--hair);
    border-radius: 8px;
    box-shadow: var(--shadow);
  }}

  /* KPI rows */
  .kpi-row {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
  }}
  .kpi-row.k4 {{
    grid-template-columns: repeat(4, 1fr);
  }}
  @media (max-width: 860px) {{
    .kpi-row, .kpi-row.k4 {{ grid-template-columns: repeat(2, 1fr); }}
  }}
  @media (max-width: 540px) {{
    .kpi-row, .kpi-row.k4 {{ grid-template-columns: 1fr; }}
  }}

  .kpi {{
    padding: 18px 20px 16px;
  }}
  .kpi-label {{
    font-family: 'Inter', sans-serif;
    font-size: 11.5px;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--ink-muted);
    margin: 0 0 6px;
    font-weight: 600;
  }}
  .kpi-value {{
    font-size: 32px;
    font-weight: 700;
    color: var(--navy);
    line-height: 1.1;
    margin: 0;
  }}
  .kpi-note {{
    font-family: 'Inter', sans-serif;
    font-size: 11.5px;
    color: var(--ink-2);
    margin-top: 8px;
    line-height: 1.4;
  }}
  .kpi-note.flag {{
    color: var(--critical);
    font-weight: 600;
  }}

  .grid2 {{
    display: grid;
    grid-template-columns: 1.25fr 1fr;
    gap: 20px;
  }}
  @media (max-width: 900px) {{
    .grid2 {{ grid-template-columns: 1fr; }}
  }}

  .chart-card {{
    padding: 20px 22px 18px;
  }}
  .chart-card h3 {{
    font-size: 18px;
    font-weight: 700;
    color: var(--navy);
    margin: 0 0 2px;
  }}
  .chart-card .sub {{
    font-family: 'Inter', sans-serif;
    font-size: 12px;
    color: var(--ink-muted);
    margin: 0 0 14px;
  }}
  .chart-surface {{
    background: var(--page);
    border: 1px solid var(--hair);
    border-radius: 6px;
    padding: 16px 14px 10px;
  }}
  .foot {{
    font-family: 'Inter', sans-serif;
    font-size: 11px;
    color: var(--ink-muted);
    margin-top: 12px;
    line-height: 1.5;
  }}
  .foot b {{ color: var(--ink-2); }}

  svg {{
    display: block;
    width: 100%;
    height: auto;
    overflow: visible;
  }}
  .axis-label {{
    font-family: 'Inter', sans-serif;
    fill: var(--ink-muted);
    font-size: 10px;
  }}
  .value-label {{
    font-family: 'Inter', sans-serif;
    fill: var(--navy);
    font-size: 11px;
    font-weight: 600;
  }}
  .cat-label {{
    font-family: 'EB Garamond', Georgia, serif;
    fill: var(--ink);
    font-size: 13.5px;
    font-weight: 600;
  }}
  .baseline {{
    stroke: var(--hair);
    stroke-width: 1.5;
  }}
  .bar {{
    fill: var(--navy);
    transition: fill .15s ease;
  }}
  .bar:hover {{
    fill: var(--gold);
  }}
  .bar.zero {{
    fill: #EAE6DC;
  }}

  .empty-state {{
    border: 1.5px dashed var(--tan);
    border-radius: 6px;
    background: var(--gold-soft);
    padding: 24px 20px;
    text-align: center;
    color: var(--ink-2);
    font-size: 13.5px;
    line-height: 1.6;
  }}
  .empty-state b {{
    display: block;
    color: var(--navy);
    font-size: 15px;
    margin-bottom: 4px;
    font-weight: 700;
  }}

  .region-chips {{
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
  }}
  .region-chip {{
    background: var(--card);
    border: 1px solid var(--hair);
    border-radius: 6px;
    padding: 10px 14px;
    font-family: 'Inter', sans-serif;
    font-size: 12px;
    color: var(--ink-muted);
    flex: 1 1 140px;
    text-align: center;
  }}
  .region-chip b {{
    display: block;
    color: var(--navy);
    font-size: 13px;
    margin-bottom: 2px;
  }}

  table.spectbl {{
    width: 100%;
    border-collapse: collapse;
    margin-top: 10px;
    font-size: 13.5px;
  }}
  table.spectbl th {{
    font-family: 'Inter', sans-serif;
    text-align: left;
    color: var(--navy);
    background: var(--gold-soft);
    font-weight: 700;
    padding: 9px 12px;
    border-bottom: 2px solid var(--tan);
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }}
  table.spectbl td {{
    padding: 9px 12px;
    border-bottom: 1px solid var(--hair);
    color: var(--ink);
  }}
  table.spectbl td.formula {{
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    font-size: 12px;
    color: var(--navy);
  }}

  .banner {{
    background: var(--gold-soft);
    border-left: 4px solid var(--gold);
    border-radius: 4px;
    padding: 16px 20px;
    font-size: 13.5px;
    color: var(--ink-2);
    line-height: 1.6;
    margin-top: 36px;
  }}
  .banner b {{
    color: var(--navy);
  }}

  .tip {{
    position: fixed;
    pointer-events: none;
    background: var(--navy-2);
    color: #FFFFFF;
    font-family: 'Inter', sans-serif;
    font-size: 11.5px;
    padding: 7px 11px;
    border-radius: 4px;
    border: 1px solid var(--gold);
    line-height: 1.4;
    box-shadow: 0 8px 24px rgba(0,0,0,.25);
    z-index: 999;
    opacity: 0;
    transform: translate(-50%,-100%);
    transition: opacity .08s ease;
    white-space: nowrap;
  }}
</style>
</head>
<body>

<div class="hero">
  <div class="hero-inner">
    <div class="hero-brand">
      {logo_img_tag}
      <div>
        <p class="eyebrow">Weekly Executive Dashboard &middot; Rutherford, Napa Valley</p>
        <h1>DTC &amp; Distribution Sales</h1>
        <p>Weekly executive scorecard consolidating direct-to-consumer channels (Commerce7 &amp; Tock), distribution accounts aging (Park Street), and wholesale depletions (Southern Glazer's).</p>
      </div>
    </div>
    <div class="badge-governance">
      Official Weekly Cutoff &middot; <span id="badgeCutoff">{date_closing}</span>
    </div>
  </div>
</div>

<div class="filterbar">
  <div class="filterbar-inner">
    <label for="weekPick">Report Week Ending</label>
    <!-- Las opciones las llena el JS a partir de WEEKS: con una sola semana
         cargada queda un solo renglón, y con varias el selector cambia TODO el
         tablero (KPIs, gráficas y notas), no solo el rótulo. -->
    <select id="weekPick"></select>
    <span class="hint" id="weekHint">Governed weekly closing cycle. All channels reconciled to Sunday cutoff.</span>
  </div>
</div>

<div class="wrap">

  <!-- 1. DTC SALES BY CHANNEL -->
  <div class="section">
    <div class="section-head">
      <div>
        <div class="section-title-wrap"><span class="section-num">1</span><h2 class="section-title">DTC Sales by Channel</h2></div>
        <p class="section-sub">Source: Commerce7 (order-level SubTotal dedup) + Tock ({tock_basis_label}) &middot; Cutoff: <span id="subCutoff">{date_closing}</span></p>
      </div>
      <span class="status-pill live"><span class="dot"></span>Live data</span>
    </div>

    <div class="kpi-row" style="margin-bottom:18px;">
      <div class="card kpi">
        <p class="kpi-label">Total DTC Sales</p>
        <p class="kpi-value" id="kpiTotalDtc">${total_dtc_sales:,.0f}</p>
        <p class="kpi-note" id="kpiTotalDtcNote">9 channels combined &middot; Week of {week_label}</p>
      </div>
      <div class="card kpi">
        <p class="kpi-label">WoW % Change</p>
        <p class="kpi-value" id="kpiWow" style="color:var(--ink-muted);">&mdash;</p>
        <p class="kpi-note" id="kpiWowNote">Baseline week &middot; Trend tracks trailing weeks</p>
      </div>
      <div class="card kpi">
        <p class="kpi-label">Top Channel</p>
        <p class="kpi-value" id="kpiTopChannel" style="font-size:24px;">{top_channel_name}</p>
        <p class="kpi-note" id="kpiTopChannelNote">${top_channel_amount:,.0f} &middot; {top_channel_pct:.0f}% of weekly DTC volume</p>
      </div>
    </div>

    <div class="grid2">
      <div class="card chart-card">
        <h3>Total DTC Sales &mdash; Weekly Trend</h3>
        <p class="sub">Sum of all 9 channels by Report Week Ending</p>
        <div class="chart-surface"><svg id="chartTrend" viewBox="0 0 620 190" role="img" aria-label="Line chart of weekly DTC sales trend"></svg></div>
        <p class="foot" id="footTrend"><b>Design Spec:</b> &mdash;</p>
      </div>
      <div class="card chart-card">
        <h3>Channel Mix &mdash; Selected Week</h3>
        <p class="sub">SubTotal by channel &middot; Tock displayed at {tock_basis_label}</p>
        <div class="chart-surface"><svg id="chartMix" viewBox="0 0 340 260" role="img" aria-label="Horizontal bar chart of DTC channel mix"></svg></div>
        <p class="foot"><b>Audit Rule:</b> 8 Commerce7 channels evaluate pre-tax order SubTotal; Tock reservations map to verified net remittance.</p>
      </div>
    </div>
  </div>

  <!-- 2. DISTRIBUTION SNAPSHOT -->
  <div class="section">
    <div class="section-head">
      <div>
        <div class="section-title-wrap"><span class="section-num">2</span><h2 class="section-title">Distribution Snapshot</h2></div>
        <p class="section-sub">Cash received &middot; Open PO balance &middot; Monthly depletions summary</p>
      </div>
      <span class="status-pill wait"><span class="dot"></span>Partial &mdash; 2 of 3 feeds live</span>
    </div>
    <div class="kpi-row">
      <div class="card kpi">
        <p class="kpi-label">Cash Received</p>
        <p class="kpi-value" id="kpiCash">&mdash;</p>
        <p class="kpi-note" id="kpiCashNote">&mdash;</p>
      </div>
      <div class="card kpi">
        <p class="kpi-label">Total Open POs</p>
        <p class="kpi-value" id="kpiOpenPos">${total_open_pos:,.0f}</p>
        <p class="kpi-note" id="kpiOpenPosNote">{open_invoices_count} open invoices &middot; {total_open_cases} cases committed</p>
      </div>
      <div class="card kpi">
        <p class="kpi-label">Depletions Volume</p>
        <p class="kpi-value"><span id="kpiDepletions">{depletions_cases:.1f}</span> <span class="sans" style="font-size:16px;font-weight:600;color:var(--tan);">9L cs</span></p>
        <p class="kpi-note" id="kpiDepletionsNote">{depletions_period} &middot; Southern Glazer's wholesale network</p>
      </div>
    </div>
  </div>

  <!-- 2b. DISTRIBUTION POs AGING -->
  <div class="section">
    <div class="section-head">
      <div>
        <div class="section-title-wrap"><span class="section-num">2b</span><h2 class="section-title">Distribution POs &mdash; Aging Analysis</h2></div>
        <p class="section-sub">Source: Park Street Invoice Management &middot; Standard terms: Net 30 days</p>
      </div>
      <span class="status-pill live"><span class="dot"></span>Live data</span>
    </div>
    <div class="grid2">
      <div class="card chart-card">
        <h3>Open PO Balance by Age Bracket</h3>
        <p class="sub">Total outstanding distributor balance categorised by invoice age</p>
        <div class="chart-surface"><svg id="chartAging" viewBox="0 0 400 210" role="img" aria-label="Column chart of PO aging brackets"></svg></div>
        <p class="foot"><b>Aging Rule:</b> 0–15d Good (Green) &middot; 16–30d Watch (Gold) &middot; &gt;30d Critical Overdue (Wine Red).</p>
      </div>
      <div class="card kpi-row" style="grid-template-columns:1fr; display:grid; gap:12px; padding:0; background:none; border:none; box-shadow:none;">
        <div class="card kpi"><p class="kpi-label">Total Outstanding PO Balance</p><p class="kpi-value" id="kpiPoBalance">${total_open_pos:,.0f}</p></div>
        <div class="card kpi"><p class="kpi-label">Total Cases in Pipeline</p><p class="kpi-value" id="kpiPoCases">{total_open_cases} cs</p></div>
        <div class="card kpi">
          <p class="kpi-label">Balance Overdue (&gt; 30 Days)</p>
          <p class="kpi-value" id="kpiOverdue" style="color:var(--critical);">${overdue_amount:,.0f}</p>
          <p class="kpi-note flag" id="kpiOverdueNote">{overdue_customer} &middot; {overdue_aging} days overdue</p>
        </div>
      </div>
    </div>
  </div>

  <!-- 3. DISTRIBUTION CASH BY REGION -->
  <div class="section">
    <div class="section-head">
      <div>
        <div class="section-title-wrap"><span class="section-num">3</span><h2 class="section-title">Distribution Cash by Region</h2></div>
        <p class="section-sub">Source: Park Street Cash Receipts &middot; Grain: Region rollup</p>
      </div>
      <span class="status-pill wait"><span class="dot"></span>Awaiting feed</span>
    </div>
    <div class="card chart-card">
      <h3>Cash Received by Region</h3>
      <p class="sub">Cash received upon closed and settled distributor invoices</p>
      <div class="empty-state">
        <b>Park Street weekly cash receipt feed awaiting client upload</b>
        Open POs tracks committed accounts receivable and aging. Once the cash settlement feed is configured, this panel populates automatically with regional breakdown.
      </div>
      <div class="region-chips" style="margin-top:16px;">
        <div class="region-chip"><b>West</b>CA</div>
        <div class="region-chip"><b>Central</b>NV, IL, TX</div>
        <div class="region-chip"><b>East</b>FL, NY</div>
        <div class="region-chip"><b>Mexico</b>Direct</div>
        <div class="region-chip"><b>Import/Export</b>PR</div>
        <div class="region-chip"><b>National Direct</b>Costco</div>
      </div>
    </div>
  </div>

  <!-- 4. DEPLETIONS BY STATE -->
  <div class="section">
    <div class="section-head">
      <div>
        <div class="section-title-wrap"><span class="section-num">4</span><h2 class="section-title">Depletions by State</h2></div>
        <p class="section-sub">Source: Southern Glazer's iDig Network &middot; Grain: State rollup in 9L cases</p>
      </div>
      <span class="status-pill live" id="pillStates"><span class="dot"></span>&mdash;</span>
    </div>
    <div class="card chart-card">
      <h3>Wholesale Depletions by Territory</h3>
      <p class="sub">9L cases depleted in wholesale channels &middot; Latest reporting month</p>
      <div class="chart-surface"><svg id="chartState" viewBox="0 0 620 200" role="img" aria-label="Bar chart of depletions by state"></svg></div>
      <p class="foot"><b>Footprint:</b> California and Florida lead current volume. Texas (Favorite Brands) reports via independent distribution path.</p>
    </div>
  </div>

  <!-- 5. DEPLETIONS BY DISTRIBUTOR -->
  <div class="section">
    <div class="section-head">
      <div>
        <div class="section-title-wrap"><span class="section-num">5</span><h2 class="section-title">Depletions by Distributor</h2></div>
        <p class="section-sub">Southern Glazer's Wine &amp; Spirits vs. Favorite Brands</p>
      </div>
      <span class="status-pill wait" id="pillDist"><span class="dot"></span>&mdash;</span>
    </div>
    <div class="card chart-card">
      <h3>Distributor Depletions Rollup</h3>
      <p class="sub">9L cases depleted across national distributors</p>
      <div class="chart-surface"><svg id="chartDist" viewBox="0 0 400 220" role="img" aria-label="Bar chart of distributor volume"></svg></div>
      <p class="foot" id="footDist"><b>Note:</b> &mdash;</p>
    </div>
  </div>

  <!-- 6. INVENTORY & SUPPLY -->
  <div class="section">
    <div class="section-head">
      <div>
        <div class="section-title-wrap"><span class="section-num">6</span><h2 class="section-title">Inventory &amp; Supply Metrics</h2></div>
        <p class="section-sub">Pipeline velocity, sell-through percentage and warehouse coverage</p>
      </div>
      <span class="status-pill wait"><span class="dot"></span>Awaiting warehouse feed</span>
    </div>
    <div class="card chart-card">
      <table class="spectbl">
        <thead>
          <tr><th>Metric</th><th>Governing Formula</th><th>Current Value / Status</th></tr>
        </thead>
        <tbody>
          <tr><td>Cases Shipped</td><td class="formula">SUM(Cases Shipped from Park Street)</td><td style="color:var(--ink-muted);">Awaiting shipment export</td></tr>
          <tr><td>Cases Depleted</td><td class="formula">SUM(iDig 9L Cases, Trailing Period)</td><td style="color:var(--good);font-weight:700;" id="cellDepleted">{depletions_cases:.1f} 9L cs (Live)</td></tr>
          <tr><td>Warehouse On-Hand</td><td class="formula">Park Street Warehouse Physical Count</td><td style="color:var(--ink-muted);">Awaiting warehouse export</td></tr>
          <tr><td>Sell-Through Rate</td><td class="formula">Cumulative Cases Depleted &divide; Cumulative Cases Shipped</td><td style="color:var(--ink-muted);">Pending formula feed</td></tr>
          <tr><td>Weeks of Supply</td><td class="formula">(Shipped &minus; Depleted) &divide; Trailing 4-Wk Avg Depletions</td><td style="color:var(--ink-muted);">Pending formula feed</td></tr>
        </tbody>
      </table>
    </div>
  </div>

  <div class="banner">
    <b>Sullivan Rutherford Estate Brand Governance Notice:</b> This dashboard implements the layout defined in the weekly reporting specification while enforcing the official Sullivan Rutherford Estate visual identity (EB Garamond typography, Navy <code>#003057</code>, Gold <code>#D9B24E</code>, Tan <code>#A67C52</code>). All metrics conform to verified transaction data with Sunday cutoff dates.
  </div>

</div>

<div class="tip" id="tip"></div>

<script>
/* ---------------------------------------------------------------------------
   Serie de semanas. `WEEKS` viene ordenada de la más antigua a la más
   reciente y cada elemento es el payload COMPLETO de esa semana. El tablero
   arranca en la más reciente; el selector cambia `REPORT_DATA` y vuelve a
   dibujar todo. Antes esto era un `<select>` con una sola opción fija y sin
   comportamiento: el filtro se veía pero no filtraba.
   --------------------------------------------------------------------------- */
const WEEKS = {weeks_json};
let activeIdx = WEEKS.length - 1;
let REPORT_DATA = WEEKS[activeIdx];

const tip = document.getElementById('tip');
function showTip(evt, html){{ tip.innerHTML = html; tip.style.opacity = '1'; positionTip(evt); }}
function positionTip(evt){{ tip.style.left = evt.clientX + 'px'; tip.style.top = (evt.clientY - 14) + 'px'; }}
function hideTip(){{ tip.style.opacity = '0'; }}
document.addEventListener('mousemove', (e)=>{{ if (tip.style.opacity === '1') positionTip(e); }});

const SVGNS = 'http://www.w3.org/2000/svg';
function el(tag, attrs){{ const e = document.createElementNS(SVGNS, tag); for (const k in attrs) e.setAttribute(k, attrs[k]); return e; }}
function money(n){{ return '$' + Math.round(n).toLocaleString('en-US'); }}
function fmt(n, d){{ return Number(n).toLocaleString('en-US', {{minimumFractionDigits:d||0, maximumFractionDigits:d||0}}); }}

/* Nunca imprimir 'null'/'undefined'/'NaN' en una celda: un guion em dice
   "no hay dato" y es verdad; un cero afirmaría un valor que nadie midió. */
const BLANK = '—';
function has(v){{ return v !== null && v !== undefined && !(typeof v === 'number' && !isFinite(v)); }}
function moneyOr(v){{ return has(v) ? money(v) : BLANK; }}

function clear(svg){{ while (svg.firstChild) svg.removeChild(svg.firstChild); }}
function setText(id, txt){{ const n = document.getElementById(id); if (n) n.textContent = txt; }}
function setHtml(id, html){{ const n = document.getElementById(id); if (n) n.innerHTML = html; }}

/* "2026-08-23" -> "8/23". Se parte la cadena en vez de usar new Date(), que
   interpretaría la fecha en UTC y en husos negativos mostraría el día previo. */
function shortDay(iso){{
  const m = String(iso || '').match(/^(\\d{{4}})-(\\d{{2}})-(\\d{{2}})$/);
  return m ? (Number(m[2]) + '/' + Number(m[3])) : String(iso || BLANK);
}}

/* ------------------------------------------------------- 0. Tira de KPIs */
function renderKpis(){{
  const d = REPORT_DATA, k = d.kpis;

  setText('badgeCutoff', d.date_closing);
  setText('subCutoff', d.date_closing);
  setText('kpiTotalDtc', money(k.total_dtc_sales));
  setText('kpiTotalDtcNote', '9 channels combined · ' + d.week_label);

  /* WoW: si no hay semana previa en la serie queda en blanco. Un 0.0%
     afirmaría que no cambió, y lo cierto es que no hay con qué comparar. */
  const wowNode = document.getElementById('kpiWow');
  if (has(k.wow_pct_change)) {{
    const up = k.wow_pct_change >= 0;
    wowNode.textContent = (up ? '+' : '') + fmt(k.wow_pct_change, 1) + '%';
    wowNode.style.color = up ? 'var(--good)' : 'var(--critical)';
    setText('kpiWowNote', 'vs ' + (d.prev_week_label || BLANK) + ' · ' + moneyOr(d.prev_total_dtc));
  }} else {{
    wowNode.textContent = BLANK;
    wowNode.style.color = 'var(--ink-muted)';
    setText('kpiWowNote', 'First week in the loaded series · no prior week to compare');
  }}

  setText('kpiTopChannel', k.top_channel_name);
  setText('kpiTopChannelNote', money(k.top_channel_amount) + ' · ' + fmt(k.top_channel_pct, 0) + '% of weekly DTC volume');

  /* Cash Received: es la suma del Total de las facturas PAID de Park Street.
     Este panel lo declaraba ausente aunque el valor ya se calculaba. */
  const cashNode = document.getElementById('kpiCash');
  if (has(k.cash_received)) {{
    cashNode.textContent = money(k.cash_received);
    cashNode.style.color = 'var(--ink)';
    setText('kpiCashNote', 'Settled Park Street invoices · ' + d.date_closing);
  }} else {{
    cashNode.textContent = BLANK;
    cashNode.style.color = 'var(--ink-muted)';
    setText('kpiCashNote', 'Open PO file has no Total column for settled invoices');
  }}

  setText('kpiOpenPos', money(k.total_open_pos_amount));
  setText('kpiOpenPosNote', k.open_invoices_count + ' open invoices · ' + fmt(k.total_open_cases, 1) + ' cases committed');
  setText('kpiDepletions', fmt(k.depletions_9l_cases, 1));
  setText('kpiDepletionsNote', k.depletions_period + " · Southern Glazer's wholesale network");

  setText('kpiPoBalance', money(k.total_open_pos_amount));
  setText('kpiPoCases', fmt(k.total_open_cases, 1) + ' cs');
  setText('kpiOverdue', money(k.overdue_30_amount));
  setText('kpiOverdueNote', k.overdue_30_customer + ' · ' + k.overdue_30_aging + ' days overdue');
  setText('cellDepleted', fmt(k.depletions_9l_cases, 1) + ' 9L cs (Live)');

  /* Pastillas y notas derivadas: antes decían "5 of 7" y "1 of 2" escritos a
     mano, que dejarían de ser verdad en cuanto cambiara un feed. */
  const st = REPORT_DATA.depletions_by_state || [];
  const stLive = st.filter(x=>x.live).length;
  setHtml('pillStates', '<span class="dot"></span>Live (' + stLive + ' of ' + st.length + ' reporting states)');

  const di = REPORT_DATA.depletions_by_distributor || [];
  const diLive = di.filter(x=>x.live).length;
  setHtml('pillDist', '<span class="dot"></span>Live (' + diLive + ' of ' + di.length + ' distributors)');

  const diTotal = di.reduce((a,x)=>a + (x.cases||0), 0);
  const top = di.slice().sort((a,b)=>(b.cases||0)-(a.cases||0))[0];
  setHtml('footDist', top && diTotal > 0
    ? '<b>Note:</b> ' + top.distributor + ' accounts for ' + fmt(top.cases/diTotal*100, 0)
      + '% of connected monthly volume (' + fmt(diTotal, 1) + ' cs across ' + di.length + ' distributors).'
    : '<b>Note:</b> ' + BLANK);

  setHtml('footTrend', WEEKS.length > 1
    ? '<b>Series:</b> ' + WEEKS.length + ' weeks loaded, ' + shortDay(WEEKS[0].date_closing)
      + ' through ' + shortDay(WEEKS[WEEKS.length-1].date_closing)
      + '. The gold anchor marks the week selected above.'
    : '<b>Series:</b> one week loaded. Add more week folders and the trend line, '
      + 'the WoW change and this selector fill in on their own.');
}}

/* --------------------------------------------------- 1. Tendencia semanal */
function drawTrend(){{
  const svg = document.getElementById('chartTrend');
  if (!svg) return;
  clear(svg);
  const W=620, H=190, left=62, right=26, top=22, bottom=34;
  const plotW=W-left-right, plotH=H-top-bottom;
  const vals = WEEKS.map(w=>w.kpis.total_dtc_sales || 0);

  /* Escala derivada de la serie, no un techo fijo: con `max = 20000` escrito a
     mano una semana mejor que ese techo se habría dibujado fuera del panel. */
  const peak = Math.max.apply(null, vals) || 1;
  const max = peak * 1.18;

  svg.appendChild(el('line', {{x1:left, x2:W-right, y1:top+plotH, y2:top+plotH, class:'baseline'}}));
  [0, 0.5, 1].forEach(f=>{{
    const y = top+plotH - f*plotH;
    svg.appendChild(el('text', {{x:left-10, y:y+4, 'text-anchor':'end', class:'axis-label'}})).textContent = money(max*f);
  }});

  const n = WEEKS.length;
  const xOf = i => n === 1 ? left + plotW/2 : left + plotW * (i/(n-1));
  const yOf = v => top + plotH - (v/max*plotH);

  if (n > 1) {{
    const pts = WEEKS.map((w,i)=>xOf(i) + ',' + yOf(vals[i])).join(' ');
    svg.appendChild(el('polyline', {{points:pts, fill:'none', stroke:'var(--navy)', 'stroke-width':'2.5'}}));
  }}

  WEEKS.forEach((w, i)=>{{
    const x = xOf(i), y = yOf(vals[i]), isActive = (i === activeIdx);
    const dot = el('circle', {{
      cx:x, cy:y, r:isActive ? 6.5 : 4.5,
      fill:isActive ? 'var(--gold)' : 'var(--navy)',
      stroke:'var(--navy)', 'stroke-width':isActive ? '2.5' : '1.5',
      style:'cursor:pointer'
    }});
    const wow = has(w.kpis.wow_pct_change)
      ? '<br>' + (w.kpis.wow_pct_change >= 0 ? '+' : '') + fmt(w.kpis.wow_pct_change,1) + '% WoW'
      : '';
    dot.addEventListener('mousemove', e=>showTip(e, '<b>' + w.week_label + '</b><br>' + money(vals[i]) + ' Total DTC' + wow));
    dot.addEventListener('mouseleave', hideTip);
    dot.addEventListener('click', ()=>selectWeek(i));
    svg.appendChild(dot);

    if (isActive) {{
      svg.appendChild(el('text', {{x:x, y:y-13, 'text-anchor':'middle', class:'value-label', fill:'var(--navy)', 'font-weight':'700'}})).textContent = money(vals[i]);
    }}
    svg.appendChild(el('text', {{
      x:x, y:top+plotH+18, 'text-anchor':'middle', class:'axis-label',
      'font-weight': isActive ? '700' : '400'
    }})).textContent = shortDay(w.date_closing);
  }});
}}

/* ------------------------------------------------------ 2. Mezcla de canales */
function drawMix(){{
  const svg = document.getElementById('chartMix');
  if (!svg) return;
  clear(svg);
  const data = REPORT_DATA.channel_mix;
  const W=340, H=260, left=120, right=48, top=6, rowH=27, gap=5;
  const max = Math.max.apply(null, data.map(d=>d.amount)) || 1;
  const plotW = W - left - right;
  data.forEach((d, i)=>{{
    const y = top + i*rowH;
    svg.appendChild(el('text', {{x:left-8, y:y+rowH/2-gap+4, 'text-anchor':'end', class:'cat-label'}})).textContent = d.channel;
    const bw = Math.max(d.amount/max * plotW, d.amount>0 ? 4 : 0);
    const bar = el('rect', {{x:left, y:y, width:bw, height:rowH-gap*2, rx:3, class:d.amount>0?'bar':'bar zero'}});
    bar.addEventListener('mousemove', e=>showTip(e, '<b>' + d.channel + '</b><br>' + money(d.amount)));
    bar.addEventListener('mouseleave', hideTip);
    svg.appendChild(bar);
    svg.appendChild(el('text', {{x:left+bw+6, y:y+rowH/2-gap+4, class:'value-label'}})).textContent = d.amount>0 ? money(d.amount) : BLANK;
  }});
}}

/* --------------------------------------------------------- 3. Aging de POs */
function drawAging(){{
  const svg = document.getElementById('chartAging');
  if (!svg) return;
  clear(svg);
  const data = REPORT_DATA.po_aging;
  const colors = {{'good':'var(--good)', 'warn':'var(--warn)', 'critical':'var(--critical)'}};
  const W=400, H=210, left=50, right=14, top=16, bottom=36;
  const max = Math.max.apply(null, data.map(d=>d.amount)) || 1;
  const plotW = W - left - right, plotH = H - top - bottom;
  const bw = plotW / data.length;
  data.forEach((d, i)=>{{
    const barW = 68, x = left + i*bw + (bw-barW)/2;
    const h = d.amount>0 ? Math.max(d.amount/max * plotH, 4) : 2;
    const y = top + plotH - h;
    const bar = el('rect', {{x:x, y:y, width:barW, height:h, rx:4, fill:colors[d.status]||'var(--navy)'}});
    bar.addEventListener('mousemove', e=>showTip(e, '<b>' + d.bucket + '</b><br>' + money(d.amount)));
    bar.addEventListener('mouseleave', hideTip);
    svg.appendChild(bar);
    svg.appendChild(el('text', {{x:x+barW/2, y:y-6, 'text-anchor':'middle', class:'value-label'}})).textContent = money(d.amount);
    svg.appendChild(el('text', {{x:x+barW/2, y:top+plotH+16, 'text-anchor':'middle', class:'axis-label'}})).textContent = d.bucket;
  }});
  svg.appendChild(el('line', {{x1:left, x2:W-right, y1:top+plotH, y2:top+plotH, class:'baseline'}}));
}}

/* ------------------------------------------------- 4. Depletions por estado */
function drawStates(){{
  const svg = document.getElementById('chartState');
  if (!svg) return;
  clear(svg);
  const data = REPORT_DATA.depletions_by_state;
  const W=620, H=200, left=42, right=14, top=16, bottom=34;
  const max = Math.max.apply(null, data.map(d=>d.cases)) || 1;
  const plotW = W - left - right, plotH = H - top - bottom;
  const bw = plotW / data.length;
  data.forEach((d, i)=>{{
    const barW = Math.min(50, bw - 6), x = left + i*bw + (bw-barW)/2;
    const h = d.cases>0 ? Math.max(d.cases/max * plotH, 4) : 2;
    const y = top + plotH - h;
    const bar = el('rect', {{x:x, y:y, width:barW, height:h, rx:3, class:d.live && d.cases>0 ? 'bar' : 'bar zero'}});
    bar.addEventListener('mousemove', e=>showTip(e, '<b>' + d.state + '</b><br>' + (d.live ? fmt(d.cases,2)+' 9L cases' : 'No feed configured yet')));
    bar.addEventListener('mouseleave', hideTip);
    svg.appendChild(bar);
    svg.appendChild(el('text', {{x:x+barW/2, y:y-6, 'text-anchor':'middle', class:'value-label'}})).textContent = d.live && d.cases>0 ? fmt(d.cases,1) : BLANK;
    svg.appendChild(el('text', {{x:x+barW/2, y:top+plotH+18, 'text-anchor':'middle', class:'axis-label'}})).textContent = d.state;
  }});
  svg.appendChild(el('line', {{x1:left, x2:W-right, y1:top+plotH, y2:top+plotH, class:'baseline'}}));
}}

/* -------------------------------------------- 5. Depletions por distribuidor */
function drawDistributors(){{
  const svg = document.getElementById('chartDist');
  if (!svg) return;
  clear(svg);
  const data = REPORT_DATA.depletions_by_distributor;
  const left=130, top=10, rowH=46, gap=10;
  const max = Math.max.apply(null, data.map(d=>d.cases)) || 1;
  const plotW = 400 - left - 50;
  data.forEach((d, i)=>{{
    const y = top + i*rowH;
    svg.appendChild(el('text', {{x:left-8, y:y+18, 'text-anchor':'end', class:'cat-label'}})).textContent = d.distributor;
    const bw = d.cases>0 ? Math.max(d.cases/max * plotW, 5) : 3;
    const bar = el('rect', {{x:left, y:y, width:bw, height:rowH-gap*2, rx:3, class:d.live && d.cases>0 ? 'bar' : 'bar zero'}});
    bar.addEventListener('mousemove', e=>showTip(e, '<b>' + d.distributor + '</b><br>' + (d.live ? fmt(d.cases,2)+' 9L cases' : d.note)));
    bar.addEventListener('mouseleave', hideTip);
    svg.appendChild(bar);
    svg.appendChild(el('text', {{x:left+bw+8, y:y+18, class:'value-label'}})).textContent = d.live && d.cases>0 ? fmt(d.cases,1)+' cs' : 'no feed';
  }});
}}

/* ------------------------------------------------------------ Orquestación */
function renderAll(){{
  renderKpis();
  drawTrend();
  drawMix();
  drawAging();
  drawStates();
  drawDistributors();
}}

function selectWeek(idx){{
  if (idx < 0 || idx >= WEEKS.length) return;
  activeIdx = idx;
  REPORT_DATA = WEEKS[idx];
  const pick = document.getElementById('weekPick');
  if (pick) pick.selectedIndex = idx;
  hideTip();
  renderAll();
}}

(function initWeekPicker(){{
  const pick = document.getElementById('weekPick');
  if (!pick) return;
  WEEKS.forEach((w, i)=>{{
    const opt = document.createElement('option');
    opt.value = String(i);
    opt.textContent = w.week_label + ' (Ending ' + w.date_closing + ')';
    pick.appendChild(opt);
  }});
  pick.selectedIndex = activeIdx;
  pick.addEventListener('change', e=>selectWeek(Number(e.target.value)));

  const hint = document.getElementById('weekHint');
  if (hint) {{
    hint.textContent = WEEKS.length > 1
      ? WEEKS.length + ' weeks loaded · switching the week redraws every panel below.'
      : 'One week loaded · drop more week folders alongside it and this selector fills in.';
  }}
}})();

renderAll();
</script>

</body>
</html>
"""


def generate_sullivan_weekly_dashboard(data_dir: Path, output_file: Path,
                                       tock_basis: str = "net_receivable",
                                       data: dict | None = None,
                                       weeks: list | None = None,
                                       lang: str = i18n.DEFAULT_LANG) -> Path:
    """
    Genera el archivo HTML standalone para el dashboard semanal de Sullivan.

    `weeks` es la serie completa de semanas ya procesadas, ordenada de la más
    antigua a la más reciente. El HTML las embebe TODAS y el selector cambia
    entre ellas sin volver a generar nada; la que se pinta al abrir es la
    última. Con una sola semana el reporte sale idéntico a como salía antes.

    `data` sigue aceptándose para una sola semana: el orquestador necesita
    conocer el periodo ANTES de nombrar el archivo de salida, y sin esto
    tendría que procesar la carpeta dos veces.
    """
    if weeks:
        series = list(weeks)
    elif data is not None:
        series = [data]
    else:
        series = process_sullivan_weekly_series(data_dir, tock_basis=tock_basis)

    # La semana ACTIVA es la más reciente. Las sustituciones estáticas de la
    # plantilla la usan para que el HTML ya venga pintado correctamente antes
    # de que corra el JS (importa al imprimir y si el script no se ejecuta).
    data = series[-1]
    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    logo_uri = get_logo_white_data_uri()
    logo_tag = f'<img src="{logo_uri}" class="hero-logo" alt="Sullivan Rutherford Estate" />' if logo_uri else ""

    tock_label = "Net Receivable" if tock_basis == "net_receivable" else "Net Sales"

    html = HTML_TEMPLATE.format(
        page_title=f"Sullivan Rutherford Estate &mdash; Weekly Dashboard ({data['week_label']})",
        logo_img_tag=logo_tag,
        week_label=data["week_label"],
        date_closing=data["date_closing"],
        tock_basis_label=tock_label,
        total_dtc_sales=data["kpis"]["total_dtc_sales"],
        top_channel_name=data["kpis"]["top_channel_name"],
        top_channel_amount=data["kpis"]["top_channel_amount"],
        top_channel_pct=data["kpis"]["top_channel_pct"],
        total_open_pos=data["kpis"]["total_open_pos_amount"],
        open_invoices_count=data["kpis"]["open_invoices_count"],
        total_open_cases=data["kpis"]["total_open_cases"],
        overdue_amount=data["kpis"]["overdue_30_amount"],
        overdue_customer=data["kpis"]["overdue_30_customer"],
        overdue_aging=data["kpis"]["overdue_30_aging"],
        depletions_cases=data["kpis"]["depletions_9l_cases"],
        depletions_period=data["kpis"]["depletions_period"],
        weeks_json=json.dumps(sanitize_for_json(series), allow_nan=False),
    )

    # Los dos idiomas viajan en el archivo; `lang` fija el inicial.
    html = i18n.inject(html, lang)
    output_file.write_text(html, encoding="utf-8")
    return output_file


if __name__ == "__main__":
    # Raíz de semanas, no una semana fija: `discover_week_dirs` acepta que la
    # carpeta SEA una semana o que las CONTENGA.
    weekly_data = PROJECT_ROOT / "Client_Data" / "Sullivan_data" / "Weekly"
    if not weekly_data.exists():
        weekly_data = PROJECT_ROOT / "Data_for_demo" / "Sullivan_weekly_demo"
    _series = process_sullivan_weekly_series(weekly_data)
    out = PROJECT_ROOT / "Output" / weekly_output_name(_series[-1])
    generate_sullivan_weekly_dashboard(weekly_data, out, weeks=_series)
    print(f"Dashboard semanal generado exitosamente en: {out}")
    print(f"  Semanas embebidas: {len(_series)} "
          f"({_series[0]['date_closing']} .. {_series[-1]['date_closing']})")
