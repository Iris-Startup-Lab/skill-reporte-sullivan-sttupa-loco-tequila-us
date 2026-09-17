"""
================================================================================
 i18n — TRADUCCIÓN DE LA INTERFAZ DE LOS REPORTES (ES / EN)
================================================================================

Un solo diccionario para los OCHO entregables (4 dashboards HTML + 4 PDF). La
alternativa —una lista de textos por generador— garantiza que a la tercera
corrección alguna quede desincronizada y el cliente reciba un reporte medio
traducido.

Dos mecanismos, porque hay dos clases de texto:

1. `PAIRS` — coincidencia EXACTA para etiquetas completas ("Total DTC Sales",
   "Mezcla de canales"). Es la mayoría.
2. `FRAGMENTS` — reemplazo de FRAGMENTO para el texto que se compone en tiempo
   de ejecución con datos dentro: `"$2,756 · 30% of weekly DTC volume"` no se
   puede meter en una tabla porque el importe cambia en cada corrida. Se
   aplican de más largo a más corto para que "of weekly DTC volume" no se coma
   parte de una frase mayor que también estaba contemplada.

**Bidireccional a propósito.** El dashboard de Loco Tequila nació con parte de
su texto en español y los tres de Sullivan en inglés: hoy los entregables son
inconsistentes entre sí. Traducir en un solo sentido habría dejado los
párrafos de Loco en español dentro de un reporte en inglés. Con pares
`(en, es)` se traduce hacia cualquiera de los dos lados y el reporte queda
íntegro en el idioma elegido, venga de donde venga la cadena.

**Lo que NO se traduce** (decisión del usuario, 2026-09-04): la taxonomía del
reporte. Las 9 categorías de la cascada, los nombres de SKU, distribuidores y
cuentas se quedan en inglés en los dos idiomas, porque son los nombres con los
que el equipo del cliente cuadra contra Commerce7 y Park Street. Si el reporte
dijera "Sala de Cata" y el sistema dice "Tasting Room", quien audita pierde el
hilo. La forma de garantizarlo es simple: esas cadenas no están en este
archivo. Lo que no está aquí, no se toca.
================================================================================
"""

from __future__ import annotations

import json
import re
from typing import Iterable

LANGS = ("en", "es")
DEFAULT_LANG = "en"


def normalize_lang(value: str | None) -> str:
    """Acepta 'es', 'ES', 'spanish', 'español'... y cae al idioma por omisión."""
    text = str(value or "").strip().lower()
    if text in ("es", "esp", "spa", "spanish", "español", "espanol", "castellano"):
        return "es"
    if text in ("en", "eng", "english", "ingles", "inglés"):
        return "en"
    return DEFAULT_LANG


# ==============================================================================
#  TAXONOMÍA — INTOCABLE
# ==============================================================================
# Se lista explícitamente para poder COMPROBAR que no se traduce, no porque el
# código la consulte para traducir. Las pruebas verifican que ninguna de estas
# cadenas aparezca como clave en `PAIRS` ni dentro de un fragmento.
TAXONOMY_FROZEN = (
    "Tasting Room", "Estate Club", "Founder's Club", "Web / Ecommerce",
    "Inbound Telesales", "Telesales", "Event", "Corporate",
    "Friends & Family", "Unclassified", "Tock", "POS", "Web", "Inbound",
    "Estate 4 Bottle", "Estate 6 Bottle", "Founder's 3 Bottle",
    "Founder's Half Case", "Founder's Single Case", "Founder's Double Case",
    "Southern Glazer's", "Favorite Brands", "Park Street", "Commerce7",
    "Shopify", "Memory", "Blanco", "Reposado", "Ambar", "Aureo",
    "Puro Corazon", "Sullivan Rutherford Estate", "Loco Tequila USA", "Sttupa",
    # Agrupadores y nombres de cuenta que vienen del origen. "Events" y "Club"
    # están aquí y no en las tablas porque son etiquetas de la taxonomía: si se
    # tradujeran, dejarían de coincidir con "Event" y "Estate Club".
    "Events", "Club", "Costco", "Brescome", "Sunshine Fine Wine",
    "Coastline Wine & Spirits", "Northgate Beverage Co", "Hudson Cellar Room",
    "Lakeshore Distributing", "EB Garamond", "Fraunces", "Inter",
)


# ==============================================================================
#  PARES EXACTOS  (inglés, español)
# ==============================================================================
PAIRS: tuple[tuple[str, str], ...] = (
    # ---------------------------------------------------------- encabezados
    ("Executive Dashboard", "Tablero directivo"),
    ("Weekly Executive Dashboard · Rutherford, Napa Valley",
     "Tablero directivo semanal · Rutherford, Napa Valley"),
    ("DTC & Distribution Sales", "Ventas DTC y de distribución"),
    ("Direct-to-Consumer · Distribution · Depletions",
     "Venta directa · Distribución · Depletions"),
    ("Sullivan Rutherford Estate · Executive reporting",
     "Sullivan Rutherford Estate · Reporteo directivo"),
    ("Executive Sales & Depletions · Loco Tequila USA",
     "Ventas y depletions directivos · Loco Tequila USA"),
    ("Executive Summary Blueprint", "Resumen directivo"),
    ("Official Executive Report · YTD Aug 2026",
     "Reporte directivo oficial · Acumulado a agosto 2026"),
    ("California · Texas · Direct-to-Consumer · Ecommerce",
     "California · Texas · Venta directa · Comercio electrónico"),
    ("Weekly executive scorecard consolidating direct-to-consumer channels "
     "(Commerce7 & Tock), distribution accounts aging (Park Street), and "
     "wholesale depletions (Southern Glazer's).",
     "Tablero directivo semanal que consolida los canales de venta directa "
     "(Commerce7 y Tock), la antigüedad de las cuentas de distribución "
     "(Park Street) y los depletions mayoristas (Southern Glazer's)."),

    # ---------------------------------------------------------- pestañas
    ("Monthly Summary", "Resumen mensual"),
    ("YTD Summary", "Resumen acumulado"),
    ("Club Deep Dive", "Análisis de Club"),
    ("DTC Reconciliation", "Reconciliación DTC"),
    ("Geographic Distribution", "Distribución geográfica"),
    ("Geographic Distribution — Club Shipments",
     "Distribución geográfica — Envíos de Club"),
    ("Geographic Distribution of Club Shipments",
     "Distribución geográfica de los envíos de Club"),
    ("Inventory", "Inventario"),
    ("Distribution", "Distribución"),
    ("Executive", "Directivo"),

    # ---------------------------------------------------------- KPIs
    ("Total DTC Sales", "Ventas DTC totales"),
    ("Total DTC (net sales)", "Total DTC (ventas netas)"),
    ("Total Club net sales", "Ventas netas de Club"),
    ("WoW % Change", "Variación % semanal"),
    ("Top Channel", "Canal principal"),
    ("Cash Received", "Efectivo recibido"),
    ("Cash Received by Region", "Efectivo recibido por región"),
    ("Total Open POs", "Órdenes de compra abiertas"),
    ("Total Outstanding PO Balance", "Saldo total pendiente de órdenes"),
    ("Total Cases in Pipeline", "Cajas comprometidas"),
    ("Balance Overdue (> 30 Days)", "Saldo vencido (más de 30 días)"),
    ("Overdue > 30 Days", "Vencido a más de 30 días"),
    ("Depletions Volume", "Volumen de depletions"),
    ("Depletions (9L cases)", "Depletions (cajas 9L)"),
    ("Active Accounts", "Cuentas activas"),
    ("Wholesale Revenue", "Ingreso mayorista"),
    ("Retail + DTC Revenue", "Ingreso retail + venta directa"),
    ("On-Hand Inventory (9L)", "Inventario disponible (9L)"),
    ("Total Orders", "Órdenes totales"),
    ("Net Sales", "Ventas netas"),
    ("Net Sales ($)", "Ventas netas ($)"),
    ("Net Sales (Financial Report)", "Ventas netas (Reporte financiero)"),
    ("Total", "Total"),
    ("Total Value", "Valor total"),
    ("Orders", "Órdenes"),
    ("Customer", "Cliente"),
    ("Market", "Mercado"),
    ("Invoice", "Factura"),
    ("Balance", "Saldo"),
    ("Age", "Antigüedad"),
    ("Metric", "Métrica"),
    ("Governing Formula", "Fórmula que la gobierna"),
    ("Current Value / Status", "Valor actual / Estado"),
    ("Source channel", "Canal de origen"),
    ("Top state", "Estado principal"),
    ("Top destination states", "Principales estados destino"),
    ("States with shipments", "Estados con envíos"),
    ("Across all sources", "Sumando todas las fuentes"),
    ("Sell-in to distributors, YTD", "Venta a distribuidores, acumulado"),
    ("Direct retail and ecommerce, YTD",
     "Retail directo y comercio electrónico, acumulado"),
    ("MoM depletions volume", "Volumen de depletions mes contra mes"),
    ("Month-over-Month Growth", "Crecimiento mes contra mes"),

    # ---------------------------------------------------------- secciones
    ("DTC Sales by Channel", "Ventas DTC por canal"),
    ("Channel Mix", "Mezcla de canales"),
    ("Channel Mix — Selected Week", "Mezcla de canales — Semana seleccionada"),
    ("Monthly net sales by channel", "Ventas netas mensuales por canal"),
    ("Net sales by channel", "Ventas netas por canal"),
    ("Net Sales by Final Category", "Ventas netas por categoría final"),
    ("Net Sales by State (Choropleth)", "Ventas netas por estado (coroplético)"),
    ("Distribution Snapshot", "Panorama de distribución"),
    ("Distribution POs — Aging Analysis",
     "Órdenes de distribución — Análisis de antigüedad"),
    ("Distribution Cash by Region", "Efectivo de distribución por región"),
    ("Open PO Balance by Age Bracket",
     "Saldo de órdenes abiertas por rango de antigüedad"),
    ("Depletions by State", "Depletions por estado"),
    ("Depletions by Distributor", "Depletions por distribuidor"),
    ("Wholesale Depletions by Territory", "Depletions mayoristas por territorio"),
    ("Distributor Depletions Rollup", "Consolidado de depletions por distribuidor"),
    ("Inventory & Supply Metrics", "Métricas de inventario y abasto"),
    ("Concentration by ZIP Code", "Concentración por código postal"),
    ("Estate vs Founder's — by Package", "Estate contra Founder's — por paquete"),
    ("Review Cases", "Casos por revisar"),
    ("Review Cases (Admin/POS Marked as Club)",
     "Casos por revisar (Admin/POS marcados como Club)"),
    ("Methodology — what each category means",
     "Metodología — qué significa cada categoría"),
    ("Total DTC Sales — Weekly Trend", "Ventas DTC totales — Tendencia semanal"),
    ("Weekly trend", "Tendencia semanal"),
    ("Depletion Trend & Growth", "Tendencia y crecimiento de depletions"),
    ("Team & Channel Mix", "Mezcla de equipo y canal"),
    ("Product Mix & Profitability", "Mezcla de producto y rentabilidad"),
    ("Key Accounts & Wholesale Distributors",
     "Cuentas clave y distribuidores mayoristas"),
    ("Account Ordering Rhythm & Recency",
     "Ritmo de compra y recencia por cuenta"),
    ("Accounts Building Repeat Cadence",
     "Cuentas que consolidan cadencia de recompra"),
    ("Consistent Reorder Patterns (Emerging Accounts)",
     "Patrones de recompra consistentes (cuentas emergentes)"),
    ("Weekly Salesperson Performance", "Desempeño semanal por vendedor"),
    ("Weekly Bottle Depletions by Rep",
     "Depletions semanales en botellas por vendedor"),
    ("Warehouse Inventory Health (CA vs. TX)",
     "Salud del inventario en almacén (CA contra TX)"),
    ("Account Summary Total Business", "Resumen de cuentas — Negocio total"),
    ("Salesperson by Week", "Vendedor por semana"),
    ("Monthly Depletions (9L Cases), YTD 2026",
     "Depletions mensuales (cajas 9L), acumulado 2026"),

    # ---------------------------------------------------------- controles
    ("Report Week Ending", "Semana que cierra"),
    ("Week ending", "Semana que cierra"),
    ("Date range", "Rango de fechas"),
    ("All channels", "Todos los canales"),
    ("Applies to this tab only", "Aplica solo a esta pestaña"),
    ("Monthly", "Mensual"),
    ("Weekly", "Semanal"),
    ("Last 12 weeks", "Últimas 12 semanas"),
    ("Full year (34 wks)", "Año completo (34 sem.)"),
    ("Close (Esc)", "Cerrar (Esc)"),
    ("Enlarge", "Ampliar"),
    ("Enlarge map", "Ampliar mapa"),
    ("Open geographic map →", "Abrir el mapa geográfico →"),
    ("Top 15 ZIP codes", "15 códigos postales principales"),
    ("Top 15 ZIP codes (Club)", "15 códigos postales principales (Club)"),
    ("ZIP", "C.P."),
    ("ZIP code", "Código postal"),
    ("number of orders", "número de órdenes"),
    ("Language", "Idioma"),
    ("Español", "Español"),
    ("English", "English"),

    # ---------------------------------------------------------- estados
    ("Live data", "Datos en vivo"),
    ("Awaiting feed", "En espera del feed"),
    ("Awaiting warehouse feed", "En espera del feed de almacén"),
    ("Awaiting warehouse export", "En espera del export de almacén"),
    ("Awaiting shipment export", "En espera del export de embarques"),
    ("Pending formula feed", "Pendiente del feed de la fórmula"),
    ("Partial — 2 of 3 feeds live", "Parcial — 2 de 3 feeds en vivo"),
    ("no feed", "sin feed"),
    ("n/a — filtered", "n/d — filtrado"),
    ("No sales ($0)", "Sin ventas ($0)"),
    ("Nothing past terms", "Nada fuera de plazo"),
    ("0 bottles YTD", "0 botellas acumuladas"),
    ("Cases Shipped", "Cajas embarcadas"),
    ("Cases Depleted", "Cajas depletadas"),
    ("Warehouse On-Hand", "Existencia en almacén"),
    ("Sell-Through Rate", "Tasa de venta al consumidor"),
    ("Weeks of Supply", "Semanas de abasto"),

    # ---------------------------------------------------------- rangos aging
    ("0–15 days", "0 a 15 días"),
    ("16–30 days", "16 a 30 días"),
    ("30+ days (overdue)", "Más de 30 días (vencido)"),

    # ---------------------------------------------------------- regiones
    ("West", "Oeste"),
    ("Central", "Centro"),
    ("East", "Este"),
    ("Mexico", "México"),
    ("Import/Export", "Importación/Exportación"),
    ("National Direct", "Directo nacional"),
    ("Direct", "Directo"),
    ("Other", "Otro"),

    # ---------------------------------------------------------- tipos gráfica
    ("Bar", "Barras"),
    ("Line", "Línea"),
    ("Donut", "Dona"),
    ("Voronoi Treemap", "Treemap de Voronoi"),
    ("Treemap", "Treemap"),
    ("Total sales", "Total de ventas"),
    ("Total volume", "Volumen total"),
    ("Total bottles", "Total de botellas"),
    ("Heatmap", "Mapa de calor"),
    ("Sparklines", "Minigráficas"),
    ("Diverging", "Divergente"),
    ("High", "Alto"),
    ("Medium", "Medio"),
    ("Low", "Bajo"),

    # ---------------------------------------------------------- etiquetas nota
    ("Note:", "Nota:"),
    ("Aging Rule:", "Regla de antigüedad:"),
    ("Audit Rule:", "Regla de auditoría:"),
    ("Design Spec:", "Especificación de diseño:"),
    ("Footprint:", "Cobertura:"),
    ("Series:", "Serie:"),
    ("Gold circles:", "Círculos dorados:"),
    ("Sullivan Rutherford Estate Brand Governance Notice:",
     "Aviso de gobernanza de marca de Sullivan Rutherford Estate:"),
    ("Design Governance:", "Gobernanza de Diseño:"),
    ("Storytelling with Data rule:", "Regla de Storytelling with Data:"),
    ("Cadence & Traceability:", "Cadencia y Trazabilidad:"),
    ("Park Street Bug Detection:", "Detección de bug de Park Street:"),
    ("Business Rules & Governance — Loco Tequila USA",
     "Reglas de negocio y gobernanza — Loco Tequila USA"),

    # ---------------------------------------------------------- descripciones
    ("Sum of all 9 channels by Report Week Ending",
     "Suma de los 9 canales por semana de cierre"),
    ("SubTotal by channel · Tock displayed at Net Receivable",
     "SubTotal por canal · Tock mostrado como Neto por cobrar"),
    ("Total outstanding distributor balance categorised by invoice age",
     "Saldo total pendiente de distribuidores, clasificado por antigüedad de la factura"),
    ("9L cases depleted in wholesale channels · Latest reporting month",
     "Cajas 9L depletadas en canales mayoristas · Último mes reportado"),
    ("9L cases depleted across national distributors",
     "Cajas 9L depletadas entre los distribuidores nacionales"),
    ("Cash received upon closed and settled distributor invoices",
     "Efectivo recibido por facturas de distribuidor cerradas y liquidadas"),
    ("Cash received · Open PO balance · Monthly depletions summary",
     "Efectivo recibido · Saldo de órdenes abiertas · Resumen mensual de depletions"),
    ("Pipeline velocity, sell-through percentage and warehouse coverage",
     "Velocidad del pipeline, porcentaje de venta al consumidor y cobertura de almacén"),
    ("Southern Glazer's Wine & Spirits vs. Favorite Brands",
     "Southern Glazer's Wine & Spirits contra Favorite Brands"),
    ("Governed weekly closing cycle. All channels reconciled to Sunday cutoff.",
     "Ciclo de cierre semanal gobernado. Todos los canales cuadran al corte del domingo."),
    ("Both cadences share one channel taxonomy, so this is a single view with a "
     "cadence switch instead of two separate charts.",
     "Las dos cadencias comparten una sola taxonomía de canal, así que esto es "
     "una sola vista con selector de cadencia en vez de dos gráficas separadas."),
    ("Every order line is evaluated once against an exclusive cascade of nine priorities,",
     "Cada renglón de la orden se evalúa una sola vez contra una cascada exclusiva de nueve prioridades,"),
    ("Park Street weekly cash receipt feed awaiting client upload",
     "El feed semanal de efectivo de Park Street está en espera de que el cliente lo cargue"),
    ("Open POs tracks committed accounts receivable and aging. Once the cash "
     "settlement feed is configured, this panel populates automatically with "
     "regional breakdown.",
     "Las órdenes abiertas siguen las cuentas por cobrar comprometidas y su "
     "antigüedad. En cuanto se configure el feed de liquidación de efectivo, "
     "este panel se llena solo con el desglose regional."),
    ("California and Florida lead current volume. Texas (Favorite Brands) "
     "reports via independent distribution path.",
     "California y Florida encabezan el volumen actual. Texas (Favorite Brands) "
     "reporta por una ruta de distribución independiente."),
    ("8 Commerce7 channels evaluate pre-tax order SubTotal; Tock reservations "
     "map to verified net remittance.",
     "Los 8 canales de Commerce7 evalúan el SubTotal de la orden antes de "
     "impuestos; las reservaciones de Tock corresponden al neto remitido verificado."),
    ("0–15d Good (Green) · 16–30d Watch (Gold) · >30d Critical Overdue (Wine Red).",
     "0 a 15 días bien (verde) · 16 a 30 días vigilar (oro) · más de 30 días "
     "vencido crítico (vino)."),
    ("Not available for this period: the source file does not include ship-to / "
     "bill-to ZIP code columns. The map is shown at state level only.",
     "No disponible en este periodo: el archivo de origen no trae las columnas "
     "de código postal de envío ni de facturación. El mapa se muestra solo a "
     "nivel estado."),
    ("Explore the interactive map of shipments by state and concentration by ZIP code.",
     "Explora el mapa interactivo de envíos por estado y la concentración por código postal."),
    ("First week in the loaded series · no prior week to compare",
     "Primera semana de la serie cargada · no hay semana previa con la que comparar"),
    ("Baseline week · Trend tracks trailing weeks",
     "Semana base · La tendencia sigue las semanas previas"),
    ("Open PO file has no Total column for settled invoices",
     "El archivo de órdenes abiertas no trae columna Total para las facturas liquidadas"),
    ("This dashboard implements the layout defined in the weekly reporting "
     "specification while enforcing the official Sullivan Rutherford Estate "
     "visual identity (EB Garamond typography, Navy",
     "Este tablero implementa la maquetación definida en la especificación de "
     "reporteo semanal aplicando la identidad visual oficial de Sullivan "
     "Rutherford Estate (tipografía EB Garamond, azul marino"),
    ("All metrics conform to verified transaction data with Sunday cutoff dates.",
     "Todas las métricas corresponden a datos transaccionales verificados con corte en domingo."),
    ("Amounts are item-level net sales (before tax, shipping and tips) and "
     "reconcile to the cent against the Financial Report.",
     "Los importes son ventas netas a nivel renglón (antes de impuestos, envío "
     "y propinas) y cuadran al centavo contra el Reporte Financiero."),
    ("Charts unavailable: the embedded chart library did not load. All figures "
     "remain in the tables below.",
     "Las gráficas no están disponibles: la librería embebida no cargó. Todas "
     "las cifras siguen en las tablas de abajo."),

    # ---------------------------------------------------------- accesibilidad
    ("Line chart of weekly DTC sales trend",
     "Gráfica de línea de la tendencia semanal de ventas DTC"),
    ("Horizontal bar chart of DTC channel mix",
     "Gráfica de barras horizontales de la mezcla de canales DTC"),
    ("Column chart of PO aging brackets",
     "Gráfica de columnas de los rangos de antigüedad de las órdenes"),
    ("Bar chart of depletions by state",
     "Gráfica de barras de depletions por estado"),
    ("Bar chart of distributor volume",
     "Gráfica de barras del volumen por distribuidor"),

    # ---------------------------------------------------------- fórmulas
    ("SUM(Cases Shipped from Park Street)",
     "SUMA(Cajas embarcadas desde Park Street)"),
    ("SUM(iDig 9L Cases, Trailing Period)",
     "SUMA(Cajas 9L del iDig, periodo previo)"),
    ("Park Street Warehouse Physical Count",
     "Conteo físico del almacén de Park Street"),
    ("Cumulative Cases Depleted ÷ Cumulative Cases Shipped",
     "Cajas depletadas acumuladas ÷ Cajas embarcadas acumuladas"),
    ("(Shipped − Depleted) ÷ Trailing 4-Wk Avg Depletions",
     "(Embarcadas − Depletadas) ÷ Promedio de depletions de las 4 semanas previas"),

    # ---------------------------------------------------------- Loco (nace en ES)
    ("Descending order", "Orden Descendente"),
    ("% change versus the prior month", "% variación respecto al mes anterior"),
    ("Days-since-purchase traffic light", "Semáforo de días sin compra"),
    ("Leading on/off-premise accounts (wholesalers excluded)",
     "Cuentas líderes on/off-premise (excluye mayoristas)"),
    ("Accounts with consistent reorders in at least 3 of the last 8 months. "
     "Acceleration or cool-down alerts.",
     "Cuentas con recompra consistente en al menos 3 de los últimos 8 meses. "
     "Alertas de aceleración o enfriamiento."),
    ("Intensity relative to each account's record month · White = no order · "
     "Right column = days since last order",
     "Intensidad relativa al mes récord de cada cuenta · Blanco = sin pedido · "
     "Columna derecha = días desde último pedido"),
    ("Physical stock in Park Street warehouses, California vs Texas",
     "Stock físico en almacenes Park Street California contra Texas"),
    ("Proportional share by SKU over total depleted volume",
     "Participación proporcional por SKU sobre el total depletado"),
    ("Unit profitability per standard case ($ USD)",
     "Rentabilidad unitaria por caja estándar ($ USD)"),
    ("Length = 9L cases · Label = % of total gross margin",
     "Longitud = Cajas 9L · Etiqueta = % del margen bruto total"),
    ("Jan–Aug · Consolidated national volume",
     "ene–ago · Volumen consolidado nacional"),
    ("Weekly tactical view required for operating meetings",
     "Vista táctica semanal requerida para juntas operativas"),
    ("Every bar chart (leaderboard, channels, profitability, top accounts, "
     "distributors and inventory) is sorted strictly from highest to lowest.",
     "Todas las gráficas de barras (leaderboard, canales, rentabilidad, top "
     "accounts, distribuidores e inventario) están ordenadas estrictamente de "
     "mayor a menor."),
    ("Each series and metric carries an interactive tooltip tracing the maths "
     "back to Sara's report.",
     "Cada serie y métrica incluye tooltip interactivo de trazabilidad "
     "matemática contra el reporte de Sara."),
    ("Highest to Lowest", "Mayor a Menor"),
    ("9L cases on hand as of August 24, 2026",
     "Cajas 9L On-Hand al 24 de agosto de 2026"),
    ("Canonical SKU palette", "Paleta Canónica SKU"),
    ("credit/return adjustments", "Ajustes de crédito/retorno"),
    ("The processor sums", "El procesador suma"),
    ("to avoid tripling the value of wholesale sell-in orders.",
     "para prevenir triplicar el valor de las órdenes mayoristas sell-in."),
    ("Consolidated YTD 2026 through week 34 (August 24, 2026). Unified data "
     "from distributors (SGWS in CA, Favorite Brands in TX), Park Street "
     "wholesale and DTC.",
     "Directivo YTD 2026 consolidado a Semana 34 (24 de agosto de 2026). Datos "
     "unificados de distribuidores (SGWS en CA, Favorite Brands en TX), Park "
     "Street wholesale y DTC."),
    ("Visuals governed by the official Loco Tequila USA identity manual. "
     "Fraunces and Inter typefaces only, with the Maroon identity palette (",
     "Visualización normada bajo el manual de identidad oficial de Loco "
     "Tequila USA. Uso exclusivo de tipografías Fraunces e Inter, con la "
     "paleta de identidad guinda ("),
    (") and Tequila Gold (", ") y Oro Tequilero ("),
    ("Sales by Market (9L)", "Ventas por mercado (9L)"),
    ("Salesperson Leaderboard (9L)", "Tabla de vendedores (9L)"),
    ("Share of Depletions (9L) by SKU", "Participación de depletions (9L) por SKU"),
    ("Top Accounts by Lifetime Bottles", "Cuentas top por botellas históricas"),
    ("Wholesale Distributor Revenue (YTD)",
     "Ingreso de distribuidores mayoristas (acumulado)"),
    ("On-Hand Inventory (9L Cases) by SKU",
     "Inventario disponible (cajas 9L) por SKU"),
    ("Gross Margin per 9L by Product", "Margen bruto por caja 9L y producto"),
    ("Monthly Order Cadence — Top 8 Accounts",
     "Cadencia mensual de compra — 8 cuentas principales"),
    ("Accounts H1/H2-2026", "Cuentas S1/S2-2026"),

    # ---------------------------------------------------------- PDF
    ("Executive Report", "Reporte directivo"),
    ("Weekly Report", "Reporte semanal"),
    ("Unified Report", "Reporte unificado"),
    ("Prepared for", "Preparado para"),
    ("Period", "Periodo"),
    ("Page", "Página"),
    ("Channel", "Canal"),
    ("Source", "Fuente"),
    ("Share", "Participación"),
    ("Amount", "Importe"),
    ("Cases", "Cajas"),
    ("State", "Estado"),
    ("Distributor", "Distribuidor"),
    ("Product", "Producto"),
    ("Account", "Cuenta"),
    ("Salesperson", "Vendedor"),
    ("Month", "Mes"),
    ("Order", "Orden"),
    ("Package", "Paquete"),
    ("Club Title", "Programa de Club"),
    ("Days", "Días"),
    ("Days overdue", "Días de vencimiento"),
    ("Leading Channel", "Canal principal"),
    ("Its Share", "Su participación"),
    ("Receivables & Aging", "Cuentas por cobrar y antigüedad"),
    ("Depletions", "Depletions"),
    ("Declared data gaps", "Brechas de dato declaradas"),
    ("Commercial inventory vs samples", "Inventario comercial contra muestras"),
    ("Revenue by route to market", "Ingreso por ruta al mercado"),
    ("Depletions by territory and month", "Depletions por territorio y mes"),
    ("SKU mix and sales reps", "Mezcla de SKU y vendedores"),
    ("Key accounts", "Cuentas clave"),
    ("Reconciliation", "Reconciliación"),
    ("Difference", "Diferencia"),
    ("Reconciled to the cent", "Cuadrado al centavo"),
    ("Week ending", "Semana que cierra"),
    ("Total DTC", "Total DTC"),
    ("9L cases", "Cajas 9L"),
    # Página de tendencia semanal del PDF.
    ("Weekly Trend", "Tendencia semanal"),
    ("Week by week", "Semana por semana"),
    ("Weeks Loaded", "Semanas cargadas"),
    ("Best Week", "Mejor semana"),
    ("Weakest Week", "Semana más débil"),
    ("Weekly Average", "Promedio semanal"),
    ("Open POs", "Órdenes abiertas"),
    ("Cash received", "Efectivo recibido"),
    # "DTC" y "WoW" se conservan sin traducir: son los términos con los que el
    # cliente nombra estas métricas en los dos idiomas, igual que la taxonomía.

    # --------------------------------------------------------------------
    # Etiquetas que la medicion de cobertura sobre los cuatro PDF encontro
    # sin cubrir. Se listan aparte para dejar constancia de que salieron de
    # una medicion y no de una lectura a ojo del codigo.
    # --------------------------------------------------------------------
    ("Executive Summary", "Resumen directivo"),
    ("Avg Order Value", "Ticket promedio"),
    ("Total Club", "Total de Club"),
    ("Open Invoices", "Facturas abiertas"),
    ("Cases in Pipeline", "Cajas comprometidas"),
    ("Open PO Balance", "Saldo de órdenes abiertas"),
    ("Open balance by age bracket", "Saldo abierto por rango de antigüedad"),
    ("Invoices past 30 days", "Facturas con más de 30 días"),
    ("Feed status", "Estado del feed"),
    ("Every unassigned order", "Cada orden sin asignar"),
    ("Shipments", "Envíos"),
    ("Commercial Total", "Total comercial"),
    ("Total 9L", "Total 9L"),
    ("Gross Revenue", "Ingreso bruto"),
    ("Category", "Categoría"),
    ("Reason", "Motivo"),
    ("Bottles", "Botellas"),
    ("Wholesale", "Mayorista"),
    ("Direct to Retail", "Retail directo"),
    ("Direct to retail", "Retail directo"),
    ("Samples", "Muestras"),
    ("Not sellable", "No vendible"),
    ("Territory", "Territorio"),
    ("Route to market", "Ruta al mercado"),
    ("Sales Rep", "Vendedor"),
    ("Data gap", "Brecha de dato"),
    ("Impact", "Impacto"),
    ("What is needed", "Qué se necesita"),

    # Etiquetas del PDF mensual (segunda ronda de medicion de cobertura).
    ("Final Checklist", "Lista de verificación final"),
    ("Classification Logic", "Lógica de clasificación"),
    ("Cascade rules applied top to bottom",
     "Reglas de la cascada, aplicadas de arriba abajo"),
    ("Priority", "Prioridad"),
    ("Identifier", "Identificador"),
    ("Final Category", "Categoría final"),
    ("Glossary — what each category means",
     "Glosario — qué significa cada categoría"),
    ("Detail by Category", "Detalle por categoría"),
    ("Financial Reconciliation", "Reconciliación financiera"),
    ("Value", "Valor"),
    ("Categories", "Categorías"),
    ("Orders, Sub Total, % of Sales", "Órdenes, subtotal, % de ventas"),
    ("Total DTC vs Net Sales (Financial Report)",
     "Total DTC contra ventas netas (Reporte financiero)"),
    ("Estate vs Founder's — by Package",
     "Estate contra Founder's — por paquete"),
    ("Combined Club", "Club combinado"),
    ("Lines the 9-priority cascade could not assign",
     "Renglones que la cascada de 9 prioridades no pudo asignar"),
    ("DTC Reconciliation — 9 final categories + 1 diagnostic row(s)",
     "Reconciliación DTC — 9 categorías finales + 1 renglón de diagnóstico"),
    ("DTC & Ecommerce", "DTC y comercio electrónico"),

    # Tercer lote, de la medicion sobre los cuatro PDF.
    ("Appendix", "Anexo"),
    ("Methodology & Sources", "Metodología y fuentes"),
    ("Date", "Fecha"),
    ("Diagnostic", "Diagnóstico"),
    ("Distribution Receivables", "Cuentas por cobrar de distribución"),
    ("Park Street invoices · standard terms net 30",
     "Facturas de Park Street · plazo estándar 30 días netos"),
    ("Total Overdue", "Total vencido"),
    ("States Reporting", "Estados que reportan"),
    ("Leading State", "Estado principal"),
    ("Its Volume", "Su volumen"),
    ("By state", "Por estado"),
    ("By distributor", "Por distribuidor"),
    ("Note", "Nota"),
    ("Distribution sites whose state could not be identified",
     "Sitios de distribución cuyo estado no se pudo identificar"),
    ("Orders the channel rules could not assign",
     "Órdenes que las reglas de canal no pudieron asignar"),
    ("Unclassified Amount", "Importe no clasificado"),
    ("Orders Affected", "Órdenes afectadas"),
    ("Share of DTC", "Participación del DTC"),
    ("Composite matching key (OrderSales <-> FinancialReport):",
     "Llave compuesta de cruce (OrderSales <-> FinancialReport):"),
    ("Order Number + SKU + Quantity + Price (or Product Title) — resolves the",
     "Número de orden + SKU + cantidad + precio (o título de producto) — resuelve las"),
    ("9 repeated Order Number + SKU combinations observed in the raw export.",
     "9 combinaciones repetidas de número de orden + SKU vistas en el export crudo."),
    ("Note on Order Tag: the OrderSales/FinancialReport exports do not include a",
     "Nota sobre Order Tag: los exports de OrderSales/FinancialReport no traen la"),
    ("populated 'Order Tag' column, so Event / Corporate / Friends & Family only",
     "columna 'Order Tag' con datos, así que Event / Corporate / Friends & Family solo"),
    ("trigger when that column is present in the input file.",
     "se activan cuando esa columna está presente en el archivo de entrada."),
    ("References: Commerce7 Sales Summary Report, Order Channels, Sales",
     "Referencias: Commerce7 Sales Summary Report, Order Channels, Sales"),
    ("Attributes and Reports Overview documentation. Business rules by Maya.",
     "Attributes y Reports Overview. Reglas de negocio definidas por Maya."),

    # Portadas de los cuatro PDF.
    ("Weekly Operating Report", "Reporte semanal de operación"),
    ("DTC Sales · Distribution Receivables · Depletions",
     "Ventas DTC · Cuentas por cobrar de distribución · Depletions"),
    ("DTC Sales & Reconciliation Report",
     "Reporte de ventas DTC y reconciliación"),
    ("Executive Business Report", "Reporte directivo de negocio"),
    ("Monthly close and weekly operations in one document",
     "El cierre mensual y la operación semanal en un solo documento"),
    ("Inventory · Wholesale · Direct to Retail · Depletions · DTC",
     "Inventario · Mayoreo · Retail directo · Depletions · DTC"),
    ("All monetary figures are GROSS REVENUE, not margin.",
     "Todas las cifras monetarias son INGRESO BRUTO, no margen."),
    ("No per-SKU cost of goods exists in the source files.",
     "Los archivos de origen no traen costo de ventas por SKU."),
)


# ==============================================================================
#  FRAGMENTOS  (para texto compuesto con datos dentro)
# ==============================================================================
# Se aplican de MÁS LARGO a MÁS CORTO. El orden importa: "of weekly DTC volume"
# tiene que intentarse antes que "of", o se rompería la frase larga.
FRAGMENTS: tuple[tuple[str, str], ...] = (
    ("% of weekly DTC volume", "% del volumen DTC de la semana"),
    ("% of connected monthly volume", "% del volumen mensual conectado"),
    ("% of total gross margin", "% del margen bruto total"),
    ("% of volume", "% del volumen"),
    ("% of club", "% del Club"),
    ("channels combined · Week of", "canales combinados · Semana del"),
    ("channels combined", "canales combinados"),
    ("Settled Park Street invoices", "Facturas de Park Street liquidadas"),
    ("open invoices", "facturas abiertas"),
    ("invoice(s)", "factura(s)"),
    ("cases committed", "cajas comprometidas"),
    ("weeks loaded · switching the week redraws every panel below.",
     "semanas cargadas · cambiar de semana repinta todos los paneles de abajo."),
    ("One week loaded · drop more week folders alongside it and this selector fills in.",
     "Una sola semana cargada · deja más carpetas de semana junto a ella y este selector se llena."),
    ("weeks loaded,", "semanas cargadas,"),
    ("The gold anchor marks the week selected above.",
     "El punto dorado marca la semana seleccionada arriba."),
    ("one week loaded. Add more week folders and the trend line, the WoW change "
     "and this selector fill in on their own.",
     "una sola semana cargada. Agrega más carpetas de semana y la línea de "
     "tendencia, la variación semanal y este selector se llenan solos."),
    ("accounts for", "representa el"),
    ("cs across", "cs entre"),
    ("distributors).", "distribuidores)."),
    ("reporting states", "estados que reportan"),
    ("distributors", "distribuidores"),
    ("days overdue", "días de vencimiento"),
    ("9L cs (Live)", "cajas 9L (en vivo)"),
    ("9L cases", "cajas 9L"),
    ("9L cs", "cajas 9L"),
    ("bottles YTD", "botellas acumuladas"),
    ("bottles", "botellas"),
    ("orders,", "órdenes,"),
    ("order(s)", "orden(es)"),
    ("line(s) totalling", "renglón(es) por un total de"),
    ("Club line(s) with no program named", "renglón(es) de Club sin programa nombrado"),
    ("line(s)", "renglón(es)"),
    ("Counted in Total DTC so the reconciliation stays exact to the cent; not "
     "one of the 9 categories.",
     "Se cuenta en el Total DTC para que la reconciliación siga exacta al "
     "centavo; no es una de las 9 categorías."),
    ("Monthly feed", "Feed mensual"),
    ("wholesale network", "red mayorista"),
    ("Week of", "Semana del"),
    ("Week:", "Semana:"),
    ("Cutoff:", "Corte:"),
    ("Cutoff", "Corte"),
    ("Official Weekly Cutoff", "Corte semanal oficial"),
    ("Generated automatically", "Generado automáticamente"),
    ("Generated", "Generado"),
    ("real Commerce7 export dataset.", "export real de Commerce7."),
    ("Source: simulated data", "Fuente: datos simulados"),
    ("Source: Commerce7 (order-level SubTotal dedup) + Tock",
     "Fuente: Commerce7 (SubTotal a nivel orden, deduplicado) + Tock"),
    ("Source: Park Street Cash Receipts · Grain: Region rollup",
     "Fuente: Recibos de efectivo de Park Street · Grano: consolidado por región"),
    ("Source: Park Street Invoice Management · Standard terms: Net 30 days",
     "Fuente: Gestión de facturas de Park Street · Plazo estándar: 30 días netos"),
    ("Source: Southern Glazer's iDig Network · Grain: State rollup in 9L cases",
     "Fuente: Red iDig de Southern Glazer's · Grano: consolidado por estado en cajas 9L"),
    ("Net Receivable", "Neto por cobrar"),
    ("Net Sales", "Ventas netas"),
    ("Net sales:", "Ventas netas:"),
    ("Avg order value:", "Ticket promedio:"),
    ("Volume:", "Volumen:"),
    ("Live", "En vivo"),
    ("Ending", "cierra"),
    ("vs", "contra"),
    ("rows", "renglones"),
    ("Applies to this tab only", "Aplica solo a esta pestaña"),
    ("Channel filter active", "Filtro de canal activo"),
    ("Reconciliation against the Financial Report is only meaningful on",
     "La reconciliación contra el Reporte Financiero solo tiene sentido en"),
    ("switch back to verify the close.", "regresa ahí para verificar el cierre."),
    ("ZIP code(s) have no centroid in the", "código(s) postal(es) sin centroide en el"),
    ("carry no usable destination state,", "no traen un estado destino utilizable,"),
    ("shipped there.", "enviado ahí."),
    ("the exact location of each delivery", "la ubicación exacta de cada entrega"),
    ("Circle size is proportional to the", "El tamaño del círculo es proporcional al"),
    ("destination state; each dot is a ZIP code, sized by net sales.",
     "estado destino; cada punto es un código postal, dimensionado por ventas netas."),
    ("before tax, shipping and tips", "antes de impuestos, envío y propinas"),
    ("diagnostic", "diagnóstico"),
    ("No feed configured yet", "Todavía no hay feed configurado"),
    ("Week ending", "Semana que cierra"),
    ("Tock basis:", "Base de Tock:"),
    ("with ", "con "),
    ("Sell-through in 9-litre cases", "Venta al consumidor en cajas de 9 litros"),
    ("Data source for this report:", "Fuente de datos de este reporte:"),
    ("simulated data", "datos simulados"),
    ("real Commerce7 export", "export real de Commerce7"),
    ("any other", "cualquier otro"),
    ("Difference (must be $0.00)", "Diferencia (debe ser $0.00)"),
    ("Total DTC (classified) — basis:", "Total DTC (clasificado) — base:"),
    ("% of Sales", "% de ventas"),
    ("Bottles YTD", "Botellas acumuladas"),
    ("9 + 1 diag.", "9 + 1 diag."),
    ("any other", "cualquier otro"),
    # "Live feed" ANTES que "Live": sin este par, el fragmento corto convertia
    # "Live feed" en "En vivo feed". Los fragmentos se aplican de mas largo a
    # mas corto justamente para que el especifico gane al generico.
    ("Live feed", "Feed en vivo"),
    ("No sell-through feed", "Sin feed de venta al consumidor"),
    ("No feed", "Sin feed"),
    ("9L Cases", "Cajas 9L"),
    ("Off Premise (heuristic)", "Off Premise (por heurística)"),
    ("On Premise (heuristic)", "On Premise (por heurística)"),
    ("heuristic", "heurística"),
    ("remainder", "resto"),
    ("Unknown", "Desconocido"),

    # --- Pestañas y bloques nuevos de Loco (ronda P). Las más largas primero:
    # la sustitución es por fragmento, así que una corta que sea prefijo de otra
    # la cortaría a medias. La TAXONOMÍA no se traduce: Signature, Favorite
    # Brands, Park Street, Shopify, Memory Bottles, SKU, cuentas y vendedores.
    ("Where every number comes from", "De dónde sale cada número"),
    ("Lines not credited to anyone", "Renglones sin vendedor asignado"),
    ("How salespeople are credited", "Cómo se acredita a cada vendedor"),
    ("Declared limits of this report", "Límites declarados de este reporte"),
    ("Why it could not be credited", "Por qué no se pudo acreditar"),
    ("Closest names in the map", "Nombres más cercanos en el mapa"),
    ("Unit conversions applied", "Conversiones de unidad aplicadas"),
    ("Conversion applied", "Conversión aplicada"),
    ("Measure, source and basis", "Medida, fuente y base"),
    ("Gross margin basis", "Base del margen bruto"),
    ("Bottle Sales by Person by Week", "Venta de botellas por persona por semana"),
    ("Salesperson Leaderboard", "Ranking de vendedores"),
    ("Bottles by Salesperson, highest to lowest",
     "Botellas por vendedor, de mayor a menor"),
    ("Rep by week — full grid", "Vendedor por semana — rejilla completa"),
    ("By account and month (bottles)", "Por cuenta y mes (botellas)"),
    ("By SKU, highest to lowest", "Por SKU, de mayor a menor"),
    ("By city, highest to lowest", "Por ciudad, de mayor a menor"),
    ("By warehouse, highest to lowest", "Por bodega, de mayor a menor"),
    ("Inventory by SKU and Warehouse", "Inventario por SKU y bodega"),
    ("On-hand 9L cases by SKU across every warehouse",
     "Cajas 9L disponibles por SKU en cada bodega"),
    ("Accounts On and Off Premise", "Cuentas On y Off Premise"),
    ("Accounts with orders year to date",
     "Cuentas con órdenes en el año a la fecha"),
    ("Top accounts by bottles", "Cuentas principales por botellas"),
    ("Wholesale distributor revenue", "Ingreso por distribuidor mayorista"),
    ("Bottles by month and store", "Botellas por mes y tienda"),
    ("Bottles by SKU and store", "Botellas por SKU y tienda"),
    ("Distributor sales reps", "Vendedores del distribuidor"),
    ("Depletion Trend & Growth", "Tendencia y crecimiento de depletions"),
    ("Monthly Depletions (9L Cases)", "Depletions mensuales (cajas 9L)"),
    ("Month-over-Month Growth", "Crecimiento mes contra mes"),
    ("Depletions by Market (9L)", "Depletions por mercado (cajas 9L)"),
    ("Share of Depletions by SKU", "Participación de depletions por SKU"),
    ("Market & Product Mix", "Mezcla de mercado y producto"),
    ("Weekly Bottle Depletions by Rep",
     "Depletions semanales de botellas por vendedor"),
    ("Reporting rules", "Reglas del reporte"),
    ("Store detail", "Detalle por tienda"),
    ("By premise", "Por premise"),
    ("Salespeople", "Vendedores"),
    ("Overview", "Resumen"),
    ("Inventory", "Inventario"),
    ("Sources", "Fuentes"),
    ("Source file", "Archivo fuente"),
    ("Salesperson", "Vendedor"),
    ("Resolved by", "Resuelto por"),
    ("Orders YTD", "Órdenes YTD"),
    ("Last order", "Última orden"),
    ("Rate / bottle", "Tasa por botella"),
    ("no rate", "sin tasa"),
    ("Gross margin", "Margen bruto"),
    ("Bottles YTD", "Botellas YTD"),
    ("Account", "Cuenta"),
    ("Channel", "Canal"),
    ("Bottles", "Botellas"),
    ("Orders", "Órdenes"),
    ("Revenue", "Ingreso"),
    ("Lines", "Renglones"),
    ("Share", "Participación"),
    ("Basis", "Base"),
    ("Amount", "Importe"),
    ("Measure", "Medida"),

    # Etiquetas que llevan un icono pegado delante ("⛶ Enlarge map",
    # "🗺️ Geographic Distribution"): la coincidencia exacta falla por el
    # prefijo, así que van también como fragmento.
    ("Geographic Distribution — Club Shipments",
     "Distribución geográfica — Envíos de Club"),
    ("Geographic Distribution", "Distribución geográfica"),
    ("Enlarge map", "Ampliar mapa"),
    ("Enlarge", "Ampliar"),

    # Meses. El periodo del reporte se arma con ellos ("April 2026",
    # "Aug 2026 (Monthly feed)"), así que sin esto la portada quedaba en
    # inglés dentro de un reporte en español.
    ("January", "enero"), ("February", "febrero"), ("March", "marzo"),
    ("April", "abril"), ("June", "junio"), ("July", "julio"),
    ("August", "agosto"), ("September", "septiembre"), ("October", "octubre"),
    ("November", "noviembre"), ("December", "diciembre"),
    # "May" completo antes que abreviaturas, y "March"/"May" van después de las
    # formas largas para no cortarlas a medias.
    ("May", "mayo"),
    ("Jan", "ene"), ("Feb", "feb"), ("Mar", "mar"), ("Apr", "abr"),
    ("Jun", "jun"), ("Jul", "jul"), ("Aug", "ago"), ("Sep", "sep"),
    ("Oct", "oct"), ("Nov", "nov"), ("Dec", "dic"),

    # Colores de la identidad, dentro del aviso de gobernanza de marca.
    ("Navy", "azul marino"), ("Gold", "oro"), ("Tan", "canela"),
    ("Cream", "crema"), ("Wine Red", "vino"), ("Maroon", "guinda"),

    # Restos de párrafo del mensual: en el HTML el texto viene partido en
    # varias líneas, y el navegador lo entrega junto. Se cubren los dos casos.
    ("National view of Club sales. Colour intensity per state reflects net revenue; the gold",
     "Vista nacional de las ventas de Club. La intensidad del color por estado "
     "refleja el ingreso neto; los círculos dorados"),
    ("Club-channel orders that name neither the Estate nor the Founder's program. They are",
     "Órdenes del canal Club que no nombran ni el programa Estate ni el Founder's. Están"),
    ("included in Total DTC so the reconciliation stays exact, and listed here because they",
     "incluidas en el Total DTC para que la reconciliación siga exacta, y se listan aquí porque"),
    ("need a business decision before the next close.",
     "requieren una decisión de negocio antes del siguiente cierre."),
    ("circles mark the exact location and volume of the receiving ZIP codes. Only Club shipments",
     "marcan la ubicación y el volumen exactos de los códigos postales que reciben. Solo los envíos de Club"),
    ("are mapped — that is where the physical logistics live.",
     "se mapean: ahí es donde vive la logística física."),
    ("top to bottom, so no revenue is counted twice. Amounts are item-level net sales",
     "de arriba abajo, así que ningún ingreso se cuenta dos veces. Los importes son ventas netas a nivel renglón"),
    ("against the Financial Report.", "contra el Reporte Financiero."),
    ("Executive Sales & Depletions Dashboard",
     "Tablero directivo de ventas y depletions"),
    ("Weekly Dashboard", "Tablero semanal"),
    ("Executive Dashboard", "Tablero directivo"),
    ("All metrics conform to verified transaction data with Sunday cutoff dates.",
     "Todas las métricas corresponden a datos transaccionales verificados con corte en domingo."),
    ("Where club wine physically ships. Shading is net sales by",
     "Dónde se envía físicamente el vino del Club. El sombreado es la venta neta por"),
    ("Canonical SKU palette", "Paleta Canónica SKU"),
    ("Descending order", "Orden Descendente"),
    ("Days-since-purchase traffic light", "Semáforo de días sin compra"),
    ("9L cases on hand as of August 24, 2026",
     "Cajas 9L On-Hand al 24 de agosto de 2026"),
)

# Índices bidireccionales. Se construyen una vez al importar.
_TO_ES = {en: es for en, es in PAIRS}
_TO_EN = {es: en for en, es in PAIRS if es not in _TO_ES}

# Índices en minúsculas. Varios generadores pasan la etiqueta ya en mayúsculas
# ("CASCADE RULES APPLIED TOP TO BOTTOM") porque el estilo de la tarjeta o del
# encabezado lo pide. Duplicar cada entrada en mayúsculas dentro de las tablas
# sería el doble de diccionario y el doble de sitios donde desincronizarse.
_TO_ES_CI = {en.lower(): es for en, es in PAIRS}
_TO_EN_CI = {es.lower(): en for en, es in PAIRS if es.lower() not in _TO_ES_CI}

# Fragmentos ordenados de más largo a más corto, en los dos sentidos.
_FRAG_ES = sorted(FRAGMENTS, key=lambda p: len(p[0]), reverse=True)
_FRAG_EN = sorted(((es, en) for en, es in FRAGMENTS),
                  key=lambda p: len(p[0]), reverse=True)


def _needs_word_boundary(src: str) -> bool:
    """
    True para los fragmentos de UNA palabra corta.

    Sin frontera de palabra, un fragmento como "vs" -> "contra" destrozaría
    cualquier dato que lo contenga: el apellido "Elvsborg" saldría impreso como
    "Elcontrasborg". Los fragmentos largos y multipalabra no tienen ese riesgo,
    y aplicarles regex costaría de más.
    """
    return " " not in src.strip() and len(src.strip()) < 12


def _apply_fragment(text: str, src: str, dst: str) -> str:
    if _needs_word_boundary(src):
        return re.sub(rf"(?<![\w]){re.escape(src)}(?![\w])", dst.replace("\\", "\\\\"), text)
    return text.replace(src, dst)


def t(text: str, lang: str = DEFAULT_LANG) -> str:
    """
    Traduce una cadena de interfaz al idioma pedido.

    Primero intenta la coincidencia exacta y, si no la hay, aplica los
    fragmentos. Si nada coincide devuelve el texto TAL CUAL: una etiqueta sin
    traducir se ve en el reporte y se corrige; una etiqueta inventada aquí
    pasaría desapercibida.
    """
    if not text:
        return text
    lang = normalize_lang(lang)
    raw = str(text)
    stripped = raw.strip()
    if not stripped:
        return raw

    exact = _TO_ES if lang == "es" else _TO_EN
    if stripped in exact:
        return raw.replace(stripped, exact[stripped], 1)

    # El navegador colapsa saltos de línea y sangrías, así que el mismo
    # párrafo llega aquí con espacios distintos según de dónde venga. Se
    # reintenta con los espacios normalizados antes de pasar a fragmentos.
    collapsed = re.sub(r"\s+", " ", stripped)
    if collapsed != stripped and collapsed in exact:
        return exact[collapsed]

    # Reintento sin distinguir mayúsculas, conservando el estilo del original:
    # una etiqueta que llegó en MAYÚSCULAS se devuelve en MAYÚSCULAS.
    ci = _TO_ES_CI if lang == "es" else _TO_EN_CI
    hit = ci.get(collapsed.lower())
    if hit:
        return hit.upper() if collapsed.isupper() else hit

    out = raw
    for src, dst in (_FRAG_ES if lang == "es" else _FRAG_EN):
        if src in out:
            out = _apply_fragment(out, src, dst)
    return out


def js_tables(lang: str = DEFAULT_LANG) -> str:
    """
    Tablas de traducción listas para embeber en el HTML.

    El navegador recibe las DOS direcciones y el idioma inicial, de modo que el
    selector ES/EN del reporte alterna sin volver a generar nada: es un solo
    archivo que sirve a los dos públicos, que es lo que se pidió.
    """
    payload = {
        "initial": normalize_lang(lang),
        # `ci` NO viaja: es `exact` con las claves en minúsculas y el
        # navegador lo deriva al cargar. Mandarlo duplicaba la tabla más
        # grande del payload y engordaba cada HTML sin aportar nada.
        "exact": {"es": _TO_ES, "en": _TO_EN},
        # Las listas se emiten YA ordenadas de más largo a más corto: el JS las
        # aplica en ese orden sin tener que reordenarlas.
        "frag": {"es": [list(p) for p in _FRAG_ES],
                 "en": [list(p) for p in _FRAG_EN]},
    }
    return json.dumps(payload, ensure_ascii=False, allow_nan=False)


def coverage(strings: Iterable[str], lang: str = "es") -> tuple[list[str], list[str]]:
    """
    Separa las cadenas que este módulo SÍ traduce de las que no.

    Es la herramienta honesta contra el punto débil del enfoque: una etiqueta
    que no esté en las tablas se queda en inglés sin avisar. Con esto el hueco
    es un número medible en vez de una sorpresa para el cliente.
    """
    lang = normalize_lang(lang)
    # Lado destino: si la cadena YA está en el idioma pedido, no hay nada que
    # traducir y contarla como hueco sería un falso negativo. Es el caso real
    # del dashboard de Loco, que nació con parte de su texto en español.
    ya_destino = set(_TO_ES.values()) if lang == "es" else set(_TO_EN.values())
    frags_destino = {dst for _, dst in (_FRAG_ES if lang == "es" else _FRAG_EN)}

    cubiertas, sin_cubrir = [], []
    for s in strings:
        base = re.sub(r"\s+", " ", str(s).strip())
        if not base or not re.search(r"[A-Za-zÀ-ÿ]{3}", base):
            continue
        if any(frozen in base for frozen in TAXONOMY_FROZEN) and len(base) < 60:
            continue
        if (base in ya_destino
                or any(f in base for f in frags_destino if len(f) > 6)
                or any(v in base for v in ya_destino if len(v) > 10)):
            cubiertas.append(base)
            continue
        cubiertas.append(base) if t(base, lang) != base else sin_cubrir.append(base)
    return cubiertas, sin_cubrir


# ==============================================================================
#  LADO NAVEGADOR
# ==============================================================================
# El HTML lleva LOS DOS idiomas y un selector ES/EN: un solo archivo sirve a los
# dos públicos y no hay riesgo de mandar la versión equivocada.
#
# La traducción se aplica sobre el DOM YA RENDERIZADO en vez de meter una clave
# `data-i18n` en cada nodo de las cuatro plantillas. Dos razones:
#
#   1. Buena parte de las etiquetas las concatena el JS en tiempo de ejecución
#      (tablas, tooltips, notas con cifras dentro). Un atributo en la plantilla
#      no las alcanza; el DOM final sí.
#   2. Cuatro plantillas de entre 900 y 2000 líneas, con más de 300 etiquetas,
#      se habrían tenido que instrumentar a mano una por una. Cada nodo omitido
#      sería un texto que se queda en inglés sin que nadie lo note.
#
# El texto ORIGINAL de cada nodo se guarda antes de tocarlo, así que alternar
# de idioma es reversible y repetirlo no degrada nada. Un `MutationObserver`
# traduce lo que se pinte después, de modo que los repintados (cambiar de
# semana, de cadencia, de pestaña) salen ya en el idioma elegido sin que los
# generadores tengan que llamar a nada.

_BROWSER_JS = r"""
<style>
  .i18n-switch {
    position: fixed; top: 10px; right: 12px; z-index: 9999;
    display: flex; gap: 0; font-family: system-ui, -apple-system, sans-serif;
    border-radius: 5px; overflow: hidden;
    box-shadow: 0 1px 4px rgba(0,0,0,.28);
  }
  .i18n-switch button {
    font: inherit; font-size: 11px; font-weight: 600; letter-spacing: .06em;
    padding: 5px 10px; border: 0; cursor: pointer;
    background: rgba(255,255,255,.92); color: #333;
  }
  .i18n-switch button[aria-pressed="true"] { background: #003057; color: #fff; }
  @media print { .i18n-switch { display: none; } }
</style>
<script>
(function () {
  'use strict';
  var I18N = __I18N_TABLES__;
  var lang = I18N.initial || 'en';

  /* Indice en minusculas, derivado aqui en vez de viajar en el archivo: es
     `exact` con las claves en minusculas, asi que enviarlo duplicaba la tabla
     mas grande del payload. Construirlo cuesta un recorrido de unos cientos de
     claves, una sola vez. */
  I18N.ci = {};
  ['es', 'en'].forEach(function (l) {
    var origen = I18N.exact[l] || {};
    var destino = {};
    for (var k in origen) {
      if (Object.prototype.hasOwnProperty.call(origen, k)) {
        destino[k.toLowerCase()] = origen[k];
      }
    }
    I18N.ci[l] = destino;
  });

  /* Texto original de cada nodo, guardado ANTES de traducir. Sin esto,
     alternar dos veces traduciría sobre lo ya traducido y el texto se
     degradaría en cada cambio. */
  var origText = new WeakMap();
  var origAttr = new WeakMap();
  var ATTRS = ['title', 'aria-label', 'placeholder', 'alt'];
  var SKIP = { SCRIPT: 1, STYLE: 1, NOSCRIPT: 1, CANVAS: 1 };
  var busy = false;

  function translate(text, target) {
    if (!text) return text;
    var raw = String(text);
    var s = raw.trim();
    if (!s) return raw;

    var exact = I18N.exact[target] || {};
    if (Object.prototype.hasOwnProperty.call(exact, s)) {
      return raw.replace(s, exact[s]);
    }
    /* El navegador conserva saltos de línea y sangrías del markup; la tabla
       guarda la frase con espacios simples. Se reintenta normalizado. */
    var flat = s.replace(/\s+/g, ' ');
    if (flat !== s && Object.prototype.hasOwnProperty.call(exact, flat)) {
      return exact[flat];
    }

    /* Reintento sin distinguir mayusculas, conservando el estilo: una etiqueta
       que llego en MAYUSCULAS se devuelve en MAYUSCULAS. */
    var ci = I18N.ci[target] || {};
    var low = flat.toLowerCase();
    if (Object.prototype.hasOwnProperty.call(ci, low)) {
      var hit = ci[low];
      return (flat === flat.toUpperCase() && /[A-Z]/.test(flat)) ? hit.toUpperCase() : hit;
    }

    var frags = I18N.frag[target] || [];
    var out = raw;
    for (var i = 0; i < frags.length; i++) {
      var from = frags[i][0], to = frags[i][1];
      if (out.indexOf(from) === -1) continue;
      /* Un fragmento de UNA palabra corta se reemplaza solo si va suelto: sin
         esto, "vs" -> "contra" convertiria el apellido "Elvsborg" en
         "Elcontrasborg" dentro de una celda de datos. */
      if (from.trim().indexOf(' ') === -1 && from.trim().length < 12) {
        var esc = from.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        out = out.replace(new RegExp('(?<![\\w])' + esc + '(?![\\w])', 'g'), to);
      } else {
        out = out.split(from).join(to);
      }
    }
    return out;
  }

  /* Un nodo de texto sirve si tiene letras, no esta dentro de <script>/<style>
     y no pertenece al propio selector de idioma (traducir sus botones seria
     absurdo). */
  function sirve(n) {
    if (!n.nodeValue || !/[A-Za-zÀ-ÿ]{2}/.test(n.nodeValue)) return false;
    var p = n.parentNode;
    if (p && SKIP[p.nodeName]) return false;
    if (p && p.closest && p.closest('.i18n-switch')) return false;
    return true;
  }

  /* Recorrido propio, usado cuando no hay TreeWalker. Sin este respaldo, un
     entorno sin `NodeFilter` dejaria el selector de idioma inerte y en
     silencio: el tablero se veria bien y el boton no haria nada. */
  function recolectarTextos(root, acc) {
    acc = acc || [];
    var hijos = root.childNodes || [];
    for (var i = 0; i < hijos.length; i++) {
      var n = hijos[i];
      if (n.nodeType === 3) {
        if (sirve(n)) acc.push(n);
      } else if (n.nodeType === 1 && !SKIP[n.nodeName]) {
        recolectarTextos(n, acc);
      }
    }
    return acc;
  }

  function walk(root, target) {
    var nodes = [];
    var puedeWalker = (typeof document.createTreeWalker === 'function' &&
                       typeof NodeFilter !== 'undefined');
    if (puedeWalker) {
      var it = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
        acceptNode: function (n) {
          return sirve(n) ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT;
        }
      });
      var n;
      while ((n = it.nextNode())) nodes.push(n);
    } else {
      nodes = recolectarTextos(root);
      if (root.nodeType === 3 && sirve(root)) nodes.push(root);
    }
    nodes.forEach(function (node) {
      if (!origText.has(node)) origText.set(node, node.nodeValue);
      var base = origText.get(node);
      var next = translate(base, target);
      if (node.nodeValue !== next) node.nodeValue = next;
    });

    /* Atributos visibles (tooltips nativos, etiquetas de accesibilidad) */
    var els = root.querySelectorAll ? root.querySelectorAll('*') : [];
    Array.prototype.forEach.call(els, function (el) {
      ATTRS.forEach(function (a) {
        if (!el.hasAttribute || !el.hasAttribute(a)) return;
        var store = origAttr.get(el) || {};
        if (!(a in store)) { store[a] = el.getAttribute(a); origAttr.set(el, store); }
        var next = translate(store[a], target);
        if (el.getAttribute(a) !== next) el.setAttribute(a, next);
      });
    });
  }

  function apply(target) {
    busy = true;
    try {
      lang = target;
      document.documentElement.setAttribute('lang', target);
      walk(document.body, target);
      var btns = document.querySelectorAll('.i18n-switch button');
      Array.prototype.forEach.call(btns, function (b) {
        b.setAttribute('aria-pressed', String(b.getAttribute('data-lang') === target));
      });
    } finally {
      busy = false;
    }
  }

  function mountSwitch() {
    if (document.querySelector('.i18n-switch')) return;
    var wrap = document.createElement('div');
    wrap.className = 'i18n-switch';
    /* El rótulo de cada botón va en SU propio idioma: quien busca español ve
       "ES" sin tener que entender la etiqueta en inglés primero. */
    [['en', 'EN'], ['es', 'ES']].forEach(function (pair) {
      var b = document.createElement('button');
      b.type = 'button';
      b.setAttribute('data-lang', pair[0]);
      b.setAttribute('aria-pressed', String(pair[0] === lang));
      b.setAttribute('title', pair[0] === 'es' ? 'Ver en español' : 'View in English');
      b.textContent = pair[1];
      b.addEventListener('click', function () { apply(pair[0]); });
      wrap.appendChild(b);
    });
    document.body.appendChild(wrap);
  }

  /* Lo que se pinte después (cambiar de semana, de cadencia, de pestaña) se
     traduce solo. Así ningún generador tiene que acordarse de llamar aquí. */
  function observe() {
    if (typeof MutationObserver !== 'function') return;
    var obs = new MutationObserver(function (muts) {
      if (busy) return;
      busy = true;
      try {
        muts.forEach(function (m) {
          Array.prototype.forEach.call(m.addedNodes || [], function (node) {
            if (node.nodeType === 1) walk(node, lang);
            else if (node.nodeType === 3) {
              if (!origText.has(node)) origText.set(node, node.nodeValue);
              var next = translate(origText.get(node), lang);
              if (node.nodeValue !== next) node.nodeValue = next;
            }
          });
        });
      } finally {
        busy = false;
      }
    });
    obs.observe(document.body, { childList: true, subtree: true });
  }

  function start() {
    mountSwitch();
    apply(lang);
    observe();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', start);
  } else {
    start();
  }
})();
</script>
"""


def browser_snippet(lang: str = DEFAULT_LANG) -> str:
    """Bloque `<style>` + `<script>` con las tablas y el selector ES/EN."""
    return _BROWSER_JS.replace("__I18N_TABLES__", js_tables(lang))


def inject(html: str, lang: str = DEFAULT_LANG) -> str:
    """
    Mete el selector y la traducción en un HTML YA generado.

    Se aplica DESPUÉS del `.format()` de la plantilla a propósito: el snippet
    lleva cientos de llaves de CSS y JS, y meterlo antes obligaría a duplicar
    cada una. Insertarlo al final también garantiza que corre después de los
    scripts propios del dashboard.
    """
    lang = normalize_lang(lang)
    snippet = browser_snippet(lang)

    out = re.sub(r'(<html\b[^>]*?)\slang="[^"]*"', r"\1", html, count=1)
    out = re.sub(r"<html\b", f'<html lang="{lang}"', out, count=1)

    if "</body>" in out:
        return out.replace("</body>", snippet + "\n</body>", 1)
    # Sin </body> (no debería pasar) se añade al final antes que perder el
    # selector en silencio.
    return out + snippet
