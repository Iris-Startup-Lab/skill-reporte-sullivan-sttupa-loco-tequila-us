# Sullivan DTC Reports — resumen para otro agente/persona

Este documento describe qué hacen `Scripts/dashboard_generator.py` y
`Scripts/pdf_generator.py` (más sus dependencias), para que cualquier agente
o persona que retome el proyecto entienda el estado actual sin releer todo el
historial de la conversación.

## Contexto de negocio

Sullivan Rutherford Estate (bodega, Napa Valley) exporta 5 reportes de
Commerce7 al mes. El cliente pidió **un único reporte consolidado de venta
DTC** con 9 categorías finales (Telesales, Event, Corporate, Friends &
Family, Tock, Web/Ecommerce, Tasting Room, Estate Club, Founder's Club),
clasificadas con una lógica en cascada documentada en
`Sullivan_data_guide.md`. Se decidió combinar esa propuesta ("Vista A") con
un desglose profundo de Club ("Vista B", ~85% de la venta neta real).

Hallazgo importante: el export real `Apr_OrderSales.xlsx` **no trae columna
de Order Tag**, aunque la guía del cliente la menciona como campo clave. Por
eso Event/Corporate/Friends & Family solo se activan si el archivo de
entrada sí trae esa columna; si no, todo Inbound cae en Telesales (que es
justo lo observado en abril real).

## Archivos y qué generan

| Archivo | Genera | Depende de |
|---|---|---|
| `Scripts/sullivan_c7_simulator.py` | Datos sintéticos de los 5 exports (para Colab) | pandas, openpyxl |
| `Scripts/dashboard_generator.py` | 1 HTML standalone (2 pestañas) | pandas, openpyxl; internet solo la 1ª vez (cachea ZIPs) |
| `Scripts/pdf_generator.py` | 1 PDF (~10 páginas) | pandas, reportlab |
| `Scripts/zcta_centroids.csv` | Caché de lat/lon por ZIP (Census Gazetteer) | se regenera solo si falta |

Los tres scripts de generación son **autocontenidos a propósito** (misma
lógica de clasificación duplicada en cada uno, sin módulo compartido) para
que se puedan editar de forma independiente al construir la skill.

## `dashboard_generator.py` — Dashboard HTML

Uso:
```
python dashboard_generator.py \
  --order-sales "Client_Data/Sullivan_data/Apr_OrderSales.xlsx" \
  --financial-report "Client_Data/Sullivan_data/Apr_FinancialReport.xlsx" \
  --period-label "April 2026" \
  --output "Data_for_demo/sullivan_dashboard.html"
```

**Tab 1 — DTC Reconciliation (Vista A):** KPIs (Total DTC, Net Sales del
Financial Report, estado de reconciliación, # órdenes) + barras horizontales
de las 9 categorías + tabla con fila TOTAL resaltada.

**Tab 2 — Club Deep Dive (Vista B):** Estate vs Founder's, desglose por
paquete (4/6 Bottle, 3 Bottle, Half/Single/Double Case) con AOV, tabla de
"casos de revisión" (Admin/POS Marked as Club), y **Geographic Distribution**:
- Choropleth real por estado (fronteras de EEUU embebidas como paths SVG
  estáticos — no depende de ningún CDN en tiempo de ejecución).
- Puntos tan por ZIP encima del choropleth (tamaño = # órdenes), proyectados
  con la misma Albers que las fronteras para que queden alineados.
- Lat/lon de cada ZIP se resuelven automáticamente contra el ZCTA Gazetteer
  del Census Bureau (`load_zip_centroids()`); se cachean en
  `zcta_centroids.csv` la primera vez. Si aparecen ZIPs nuevos en meses
  futuros, se resuelven solos — no hay que tocar coordenadas a mano.

Diseño: tokens de `Designs/Design_sullivan.md` (navy `#003057`, tan
`#A67C52`, cream `#FFFBEF`), fuente EB Garamond embebida en base64, logo
blanco de Sullivan embebido. Estados sin órdenes de club se pintan gris
neutro (nunca en blanco). Validado contra datos reales: Total DTC
$433,380.05, reconcilia exacto contra el Financial Report; desglose de club
cuadra al centavo con la auditoría de la guía.

## `pdf_generator.py` — Reporte PDF

Uso:
```
python pdf_generator.py \
  --order-sales "Client_Data/Sullivan_data/Apr_OrderSales.xlsx" \
  --financial-report "Client_Data/Sullivan_data/Apr_FinancialReport.xlsx" \
  --period-label "April 2026" \
  --output "Data_for_demo/sullivan_report.pdf"
```

Estructura (~10 páginas, más corta que el patrón genérico de 25-35 porque
aquí son 9+7 categorías, no docenas de SKUs):

1. Portada (banda navy, banner de reconciliación OK/discrepancia).
2. Executive Summary — KPIs + barras horizontales de las 9 categorías.
3. Classification Logic — tabla de la cascada de prioridades 1-9.
4. Detail by Category — tabla categorías × orders × sub total × %.
5. Financial Reconciliation — Total DTC vs Net Sales + checklist de 10
   puntos de `Sullivan_data_guide.md`.
6. Club Deep Dive — overview Estate vs Founder's.
7. Club Deep Dive — tabla por paquete (orders, sub total, AOV).
8. Club Deep Dive — casos de revisión (Admin/POS Marked as Club).
9. Appendix — clave compuesta de matching, nota sobre Order Tag, fuentes.

El PDF **no** trae el mapa geográfico todavía (solo el dashboard HTML lo
tiene); si se quiere, el mismo `US_STATES_GEO_JSON` se puede reutilizar
dibujando los paths directamente en el canvas de ReportLab.

## Pendientes / decisiones abiertas para quien retome esto

- Confirmar con el cliente si algún día exportará el campo real de `Order
  Tag` desde Commerce7 (hoy no viene en los exports, así que Event/Corporate/
  Friends & Family quedan en 0 por diseño, no por bug).
- El choropleth de ZIP/condado a nivel nacional **no se implementó** — con
  solo 15 ZIPs con órdenes de club (casi todo concentrado en 94574,
  Rutherford), un relleno de polígonos se vería casi vacío. Se usó overlay de
  puntos en su lugar, que es lo que sí quedó construido.
- `Scripts/sullivan_c7_simulator.py` sirve para generar datos de otros meses
  en Colab y así probar tendencias (`growth_trend_pct`) antes de tener datos
  reales de mayo en adelante.
