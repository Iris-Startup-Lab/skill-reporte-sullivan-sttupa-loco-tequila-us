# Tutorial para el Cliente — Reportes Sullivan Rutherford Estate
# Client Tutorial — Sullivan Rutherford Estate Reports

> **ES:** Esta guía explica, parte por parte, qué contiene cada uno de los entregables del reporte DTC (venta directa al consumidor) de Sullivan Rutherford Estate y cómo leerlos. No necesitas conocimientos técnicos.
>
> **EN:** This guide explains, part by part, what each deliverable of the Sullivan Rutherford Estate DTC (direct-to-consumer) report contains and how to read them. No technical background is required.

---

## 1. Visión general / Overview

**ES:** Sullivan Rutherford Estate es una bodega (viñedo) en Napa Valley. Cada mes, su plataforma Commerce7 exporta 5 reportes distintos de las mismas ventas. Estos reportes toman esos datos y los consolidan en **un solo reporte DTC** con **dos entregables**:

**EN:** Sullivan Rutherford Estate is a winery in Napa Valley. Each month, its Commerce7 platform exports 5 different reports of the same sales. These reports take that data and consolidate it into **a single DTC report** with **two deliverables**:

| Entregable / Deliverable | Archivo / File | Para qué sirve / What it's for |
| --- | --- | --- |
| **Dashboard (HTML)** | `sullivan_dashboard_<periodo>.html` | ES: Tablero interactivo de 3 pestañas que se abre en el navegador. / EN: Interactive 3-tab dashboard that opens in a browser. |
| **Reporte Directivo (PDF)** | `sullivan_report_<periodo>.pdf` | ES: Documento formal de ~9 páginas para imprimir o presentar. / EN: Formal ~9-page document to print or present. |

**ES:** `<periodo>` es el mes del reporte (ejemplo: `sullivan_dashboard_April_2026.html`).
**EN:** `<periodo>` is the report month (example: `sullivan_dashboard_April_2026.html`).

> **ES — Importante:** No existe un archivo Excel. Por decisión de negocio, el PDF y el Dashboard cubren el 100% de lo solicitado.
> **EN — Important:** There is no Excel file. By business decision, the PDF and Dashboard cover 100% of the requirements.

---

## 2. Conceptos clave (glosario) / Key concepts (glossary)

**ES:** Estos términos aparecen en ambos entregables. Entenderlos es suficiente para leer todo el reporte.
**EN:** These terms appear in both deliverables. Understanding them is enough to read the whole report.

| Término / Term | Significado / Meaning |
| --- | --- |
| **DTC** (*Direct-to-Consumer*) | ES: Venta directa al consumidor (sin distribuidor de por medio). / EN: Direct-to-consumer sales (no distributor in between). |
| **Net Sales / Venta Neta** | ES: Ventas después de descuentos, **sin** fletes, impuestos ni propinas. Es la cifra base para reconciliar. / EN: Sales after discounts, **excluding** shipping, tax and tips. The base figure for reconciliation. |
| **SubTotal** | ES: Suma de los ítems de una orden; se compara contra Net Sales. / EN: Sum of an order's items; compared against Net Sales. |
| **Reconciliación / Reconciliation** | ES: Verificar que el total clasificado **cuadra exactamente** con el reporte financiero. / EN: Verifying the classified total **matches exactly** the financial report. |
| **Cascada de clasificación / Classification cascade** | ES: Reglas en orden de prioridad (1 a 9) que asignan cada orden a una sola categoría final. / EN: Priority-ordered rules (1–9) that assign each order to a single final category. |
| **Club** | ES: Membresías de vino recurrentes; hay dos niveles: **Estate** y **Founder's**. / EN: Recurring wine memberships; two tiers: **Estate** and **Founder's**. |
| **AOV** (*Average Order Value*) | ES: Valor promedio por orden. / EN: Average value per order. |
| **Order Tag** | ES: Etiqueta manual de orden. Hoy los exports **no la traen**, por lo que algunas categorías salen en cero por diseño. / EN: A manual order label. Current exports **don't include it**, so some categories are zero by design. |
| **ZIP / ZCTA** | ES: Código postal de EEUU, usado para el mapa geográfico. / EN: US postal code, used for the geographic map. |

---

## 3. Las 9 categorías finales de venta / The 9 final sales categories

**ES:** Todo el reporte gira en torno a clasificar cada orden en **una** de estas 9 categorías, aplicadas en orden de prioridad (la primera regla que se cumple, gana):
**EN:** The whole report revolves around classifying each order into **one** of these 9 categories, applied in priority order (the first rule that matches, wins):

| # | Categoría / Category | Regla / Rule |
| --- | --- | --- |
| 1 | **Event** | ES: `Inbound` + etiqueta Event. / EN: `Inbound` + Event tag. |
| 2 | **Corporate** | ES: `Inbound` + etiqueta Corporate. / EN: `Inbound` + Corporate tag. |
| 3 | **Friends & Family** | ES: `Inbound` + etiqueta Friends & Family. / EN: `Inbound` + Friends & Family tag. |
| 4 | **Telesales** | ES: `Inbound` restante (sin etiqueta). / EN: remaining `Inbound` (untagged). |
| 5 | **Tock** | ES: `Web` + proveedor = Tock. / EN: `Web` + vendor = Tock. |
| 6 | **Web / Ecommerce** | ES: `Web` restante. / EN: remaining `Web`. |
| 7 | **Tasting Room** | ES: ventas en `POS` (sala de degustación). / EN: `POS` (tasting room) sales. |
| 8 | **Estate Club** | ES: `Club` nivel Estate. / EN: `Club` Estate tier. |
| 9 | **Founder's Club** | ES: `Club` nivel Founder's. / EN: `Club` Founder's tier. |

> **ES — Nota:** Como los exports actuales no traen `Order Tag`, las categorías 1–3 (Event, Corporate, Friends & Family) suelen aparecer en **cero**, y todo el Inbound cae en **Telesales**. Esto es por diseño, no un error.
> **EN — Note:** Since current exports lack `Order Tag`, categories 1–3 (Event, Corporate, Friends & Family) usually show as **zero**, and all Inbound falls into **Telesales**. This is by design, not a bug.

---

## 4. El Dashboard (HTML) — pestaña por pestaña / The Dashboard (HTML) — tab by tab

**ES:** Se abre con doble clic en cualquier navegador (Chrome, Edge). Es un archivo único y autocontenido (no necesita internet). Tiene 3 pestañas:
**EN:** Open it by double-clicking in any browser (Chrome, Edge). It's a single self-contained file (no internet needed). It has 3 tabs:

### Pestaña 1 — DTC Reconciliation (Vista A) / Tab 1 — DTC Reconciliation (View A)
**ES:** La vista de reconciliación general:
- **KPIs ejecutivos:** Total DTC, Net Sales del reporte financiero, **estado de reconciliación** (cuadra / discrepancia) y número de órdenes.
- **Barras horizontales** con las 9 categorías finales, de mayor a menor.
- **Tabla auditada** con una fila TOTAL resaltada, que controla cualquier discrepancia contra Net Sales.

**EN:** The overall reconciliation view:
- **Executive KPIs:** Total DTC, Net Sales from the financial report, **reconciliation status** (matches / discrepancy), and order count.
- **Horizontal bars** for the 9 final categories, largest to smallest.
- **Audited table** with a highlighted TOTAL row, controlling any discrepancy against Net Sales.

### Pestaña 2 — Club Deep Dive (Vista B) / Tab 2 — Club Deep Dive (View B)
**ES:** El análisis profundo del Club (representa ~85% de la venta neta real):
- **Estate vs Founder's:** comparación entre los dos niveles de membresía.
- **Tabla por paquete** (4/6 Bottle, 3 Bottle, Half/Single/Double Case) con órdenes, subtotal y **AOV** (valor promedio por orden).
- **Casos de revisión:** órdenes marcadas manualmente como Club desde el panel administrativo/POS (*Admin/POS Marked as Club*), para auditoría.

**EN:** The deep dive into Club (represents ~85% of true net sales):
- **Estate vs Founder's:** comparison between the two membership tiers.
- **Per-package table** (4/6 Bottle, 3 Bottle, Half/Single/Double Case) with orders, subtotal and **AOV** (average order value).
- **Review cases:** orders manually flagged as Club from the admin/POS panel (*Admin/POS Marked as Club*), for auditing.

### Pestaña 3 — Geographic Distribution / Tab 3 — Geographic Distribution
**ES:** El mapa de los envíos del Club:
- **Mapa coroplético de EEUU** (estados coloreados según volumen; los estados sin órdenes de club van en gris neutro).
- **Puntos por código postal (ZIP)** encima del mapa; el tamaño del punto indica el número de órdenes.
- Las coordenadas de cada ZIP se resuelven automáticamente, así que meses futuros con ZIPs nuevos funcionan sin ajustes manuales.

**EN:** The Club shipments map:
- **US choropleth map** (states colored by volume; states with no club orders shown in neutral gray).
- **Points per ZIP code** over the map; point size indicates the number of orders.
- Each ZIP's coordinates resolve automatically, so future months with new ZIPs work without manual edits.

---

## 5. El Reporte Directivo (PDF) — página por página / The Executive Report (PDF) — page by page

**ES:** Documento formal de ~9 páginas. Se lee de arriba hacia abajo; pensado para imprimir o presentar. Sus páginas, en orden:
**EN:** A formal ~9-page document. Reads top-to-bottom; meant to print or present. Its pages, in order:

### 5.1 Portada / Cover
**ES:** Banda color navy con el sello de la marca y un **banner de reconciliación** que indica si todo cuadra (OK) o si hay discrepancia.
**EN:** A navy band with the brand seal and a **reconciliation banner** showing whether everything matches (OK) or there's a discrepancy.

### 5.2 Executive Summary / Resumen Ejecutivo
**ES:** KPIs principales + barras horizontales de las 9 categorías. Es el panorama de una sola mirada.
**EN:** Key KPIs + horizontal bars of the 9 categories. The at-a-glance picture.

### 5.3 Classification Logic / Lógica de Clasificación
**ES:** La tabla de la **cascada de prioridades 1–9** (ver sección 3), con un glosario de cada categoría.
**EN:** The **priority cascade 1–9** table (see section 3), with a glossary of each category.

### 5.4 Detail by Category / Detalle por Categoría
**ES:** Tabla con categorías × número de órdenes × subtotal × participación (%).
**EN:** Table of categories × number of orders × subtotal × share (%).

### 5.5 Financial Reconciliation / Reconciliación Financiera
**ES:** Compara el **Total DTC clasificado** contra el **Net Sales** del reporte financiero, con diagnósticos, más un **checklist de 10 puntos de control** (por ejemplo: comparar siempre Net Sales contra Net Sales, separar fletes/impuestos/propinas, revisar blancos inesperados, etc.).
**EN:** Compares the **classified Total DTC** against the financial report's **Net Sales**, with diagnostics, plus a **10-point control checklist** (e.g. always compare Net Sales to Net Sales, separate shipping/tax/tips, review unexpected blanks, etc.).

### 5.6 Club Deep Dive — Overview / Panorama del Club
**ES:** Resumen Estate vs Founder's (versión impresa de la Pestaña 2 del dashboard).
**EN:** Estate vs Founder's overview (print version of dashboard Tab 2).

### 5.7 Club Deep Dive — Tabla por Paquete / Per-Package Table
**ES:** Órdenes, subtotal y AOV por cada tipo de paquete de vino.
**EN:** Orders, subtotal and AOV for each wine package type.

### 5.8 Club Deep Dive — Casos de Revisión / Review Cases
**ES:** Las órdenes marcadas manualmente como Club (Admin/POS), señaladas para auditoría.
**EN:** Orders manually flagged as Club (Admin/POS), flagged for audit.

### 5.9 Appendix / Apéndice
**ES:** Nota técnica: la clave compuesta usada para cruzar los reportes, la aclaración sobre el `Order Tag` faltante, y las fuentes de datos.
**EN:** Technical note: the composite key used to join the reports, the note about the missing `Order Tag`, and the data sources.

> **ES — Nota:** El PDF **aún no incluye** el mapa geográfico; ese solo está en el dashboard HTML.
> **EN — Note:** The PDF **does not yet include** the geographic map; that lives only in the HTML dashboard.

---

## 6. Reglas de negocio que conviene recordar / Business rules worth remembering

**ES:**
- **No sumar los 5 reportes de Commerce7.** Son perspectivas distintas de las mismas ventas; sumarlos duplica los ingresos.
- **La reconciliación es de tolerancia cero:** el total DTC clasificado debe cuadrar exactamente con el Net Sales del reporte financiero.
- **Comparar siempre "lo mismo contra lo mismo":** Net Sales contra Net Sales (nunca Net Sales contra Total Revenue).

**EN:**
- **Don't sum the 5 Commerce7 reports.** They are different perspectives of the same sales; summing them double-counts revenue.
- **Reconciliation is zero-tolerance:** the classified DTC total must match the financial report's Net Sales exactly.
- **Always compare like-for-like:** Net Sales against Net Sales (never Net Sales against Total Revenue).

---

## 7. Cómo usar cada archivo / How to use each file

| Si necesitas… / If you need to… | Usa / Use |
| --- | --- |
| ES: Presentar o imprimir para una junta directiva. / EN: Present or print for a board meeting. | **PDF** |
| ES: Explorar de forma interactiva por categoría, club y geografía. / EN: Explore interactively by category, club and geography. | **Dashboard (HTML)** |
| ES: Ver el mapa de envíos del Club por estado/ZIP. / EN: See the Club shipments map by state/ZIP. | **Dashboard (HTML), Pestaña 3** |
| ES: Auditar que las cifras cuadran con finanzas. / EN: Audit that figures reconcile with finance. | **Ambos / Both** (PDF §5.5, Dashboard Pestaña 1) |

---

## 8. Preguntas frecuentes / FAQ

**ES — ¿Por qué Event, Corporate o Friends & Family aparecen en cero?**
Porque el export actual de Commerce7 no trae la columna `Order Tag`. En cuanto el cliente la exporte, esas categorías se activan solas.
**EN — Why do Event, Corporate or Friends & Family show as zero?**
Because the current Commerce7 export lacks the `Order Tag` column. Once the client exports it, those categories activate automatically.

**ES — ¿Qué significa "reconciliación OK"?**
Que el total de las 9 categorías coincide al centavo con el Net Sales del reporte financiero.
**EN — What does "reconciliation OK" mean?**
That the total of the 9 categories matches the financial report's Net Sales to the cent.

**ES — ¿Los dos archivos tienen la misma información?**
Casi: los números base son los mismos. El dashboard añade interactividad y el mapa geográfico; el PDF es el documento formal para presentar.
**EN — Do both files have the same information?**
Almost: the base numbers are the same. The dashboard adds interactivity and the geographic map; the PDF is the formal document for presenting.

**ES — ¿Puedo generar el reporte de otro mes?**
Sí. Se indica la etiqueta de periodo (ej. "May 2026") y se proveen los archivos de ventas (`order_sales`) y, opcionalmente, el financiero (`financial_report`).
**EN — Can I generate the report for another month?**
Yes. Provide the period label (e.g. "May 2026") and the sales file (`order_sales`) plus, optionally, the financial file (`financial_report`).
