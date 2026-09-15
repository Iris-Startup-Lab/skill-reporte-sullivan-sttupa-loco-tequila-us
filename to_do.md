# TO-DO — Revisión de la skill Sullivan

> Revisión original: 2026-08-26 · Rondas de debuggeo: **2026-08-27** (§B–§F y §H) ·
> **2026-09-02** (§J — auditoría de los entregables nuevos) · **2026-09-03** (§K — regla de
> No clasificados y Loco con datos reales) · **2026-09-04** (§L — datos demo, fusión de
> dashboards y cierre de los bloqueantes del semanal · §M — los tres PDF faltantes y el
> tutorial de datos para el cliente)
> Alcance: `dashboard_generator.py`, `pdf_generator.py`, `pdf_common.py`,
> `pdf_weekly_sullivan.py`, `pdf_sullivan_unified.py`, `pdf_loco_tequila.py`,
> `generate_report.py`,
> `sullivan_weekly_processor.py`, `dashboard_weekly_sullivan.py`, `loco_dashboard_generator.py`,
> `loco_data_processor.py`, `dashboard_sullivan_unified.py`, `make_demo_data.py`,
> entregables en `Output/` y el paquete distribuible.
>
> **Estado por entregable (actualizado 2026-09-04 — ver §L):**
>
> - **Sullivan Mensual — LISTO.** Cuadre al centavo ($0.00 en demo y en real), verificado
>   también desde el paquete extraído.
> - **Sullivan Semanal — LISTO.** Los 3 bloqueantes de §J.2 están cerrados: el periodo, el
>   nombre del archivo de salida y el mes de depletions se **derivan** del dato; el desglose
>   por estado se **deriva** del nombre del sitio del iDig (y reproduce exacto los valores que
>   antes estaban a mano); el Club sin programa va a *Unclassified* y ya no pierde dinero.
>   Quedan mejoras no bloqueantes (§L.5) y el PDF semanal (§I.2.4).
> - **Loco Tequila — LISTO como reporte con datos reales.** Ya NO es una maqueta: lee los 7
>   insumos crudos + la carpeta de depletions vía `loco_data_processor.py` y cuadra exacto con
>   el libro del cliente (220.65 cajas 9L · CA 198.23 · TX 22.42). Acepta datos propios con
>   `--data-dir` / `--account-map`. Falta su PDF (§I.3.4). **Sin margen bruto**: no hay COGS por
>   SKU en el origen, así que todo es ingreso bruto y el reporte lo declara.
> - **Sullivan Unificado — NUEVO y recomendado.** Las dos cadencias en un solo entregable,
>   sin los bloques que se duplicaban y conservando lo exclusivo de cada una (§L.2).
> - **Los 4 reportes entregan HTML y PDF** (§M). Toda la maquetación de los PDF sale de una
>   sola capa compartida, `Scripts/pdf_common.py`.
> - **Sttupa — no iniciado.** Sin datos del cliente, así que tampoco tiene demo (§L.1).
>
> **Los 4 reportes corren desde el paquete extraído sin ningún dato de cliente**, gracias a los
> datos demo sintéticos de `Data_for_demo/` (§L.1). Qué pide cada uno: `DATOS_REQUERIDOS.md`.
>
> Queda 1 decisión de negocio (§A) que necesita al cliente, no código: la primera ya la resolvió
> (Club sin programa → No clasificados, §K.1).

---

## A. PENDIENTE — requiere decisión del cliente (no es deuda técnica) esto lo hace el usuario final no el agente

- [ ] **8 órdenes de Club en la fila de revisión** (`Club - Review (Admin/POS)`, $4,681.53 en el demo;
      5 órdenes en los datos reales). Son órdenes de canal `Club` que no nombran ni Estate ni
      Founder's — marcadas manualmente como club desde el panel de POS. Hoy se **incluyen** en el
      Total DTC (por eso el cuadre es exacto) y se listan aparte en el dashboard y el PDF.
      *Falta que el cliente diga a qué categoría deben ir.*
- [ ] **El dataset demo no trae columnas de código postal** (`Data_for_demo/Sullivan_data_demo/Apr_OrderSales.xlsx`
      tiene 27 columnas; el export real tiene 114 e incluye `Ship To Zip Code`). Con datos demo el mapa
      se dibuja solo a nivel estado y el dashboard ahora lo explica en la leyenda en vez de mostrar una
      leyenda de círculos que no existen. *Si se quiere que el demo también muestre ZIPs, hay que
      regenerar ese archivo con las columnas de envío.*

---

## B. CERRADO — bugs críticos de cuadre

### B.1 Tolerancia de la reconciliación (era ~$4.34, ahora al centavo) ✅

`np.isclose(a, b, atol=0.005)` conservaba su `rtol=1e-5` por defecto: sobre $433,380 toleraba
≈ $4.34 de diferencia. Reemplazado por `round(a, 2) == round(b, 2)` en ambos generadores.
Probado: diferencias de $0.01, $1.00, $4.00 y $4.33 ahora reportan **DISCREPANCIA**.

### B.2 Base de comparación ventas vs financiero ✅ (el diagnóstico original estaba invertido)

El to-do pedía *"forzar `SubTotal` en ambos lados"*. **Eso habría roto el cuadre.** Medición real:

| Archivo | Columna | Suma (datos reales) | Nivel |
| :--- | :--- | ---: | :--- |
| OrderSales | `Product SubTotal` | **433,380.05** | ítem ✅ |
| OrderSales | `SubTotal` | 576,727.80 | **orden, repetida en cada ítem → duplica** |
| OrderSales | `Total` | 627,608.85 | incluye impuestos y flete |
| FinancialReport | `SubTotal` | **433,380.05** | ítem ✅ |

La base canónica correcta es `OrderSales.Product SubTotal` ↔ `FinancialReport.SubTotal`.
Implementado: dos resolvedores separados (`money_col` / `financial_money_col`), `Total` eliminado
del fallback, aviso a stderr si hay que caer a un fallback, y **ambas bases se imprimen en el
dashboard y en el PDF** para que el lector sepa qué se comparó.

### B.3 `pdf_generator.py` no corría en modo directo ✅ (bug nuevo, no estaba en la revisión)

`main()` usaba `sys.stdout` sin `import sys` → `NameError` al invocar el script solo.
Solo funcionaba a través del orquestador. Corregido.

---

## C. CERRADO — filtro de canal y features del dashboard

### C.1 Filtro de canal engañoso ✅ (opción A, por semántica de los datos)

Se movió el `<select>` **dentro** de la pestaña DTC, con la nota *"Applies to this tab only"*.
Se descartó la opción B (hacer reactivas las 3 pestañas) porque Club Deep Dive y Geographic son
vistas **exclusivas del canal Club**: filtrar por POS/Web/Inbound las dejaría vacías, que es
correcto pero inútil.

Además: el KPI *Net Sales (Financial Report)* muestra **"n/a — filtered"** al filtrar (el reporte
financiero no viene desglosado por canal, así que compararlo contra un DTC filtrado se leía como
un descuadre), y la nota de reconciliación explica el estado en cada caso.

### C.2 Features del Bloque E.3 ✅ implementadas

- **Export CSV con BOM UTF-8** en las 4 tablas (categorías, paquetes, casos de revisión, estados y ZIPs).
- **Descarga PNG** por gráfica: las instancias de `Chart` ahora se guardan en `CHARTS` (antes eran
  `new Chart(...)` anónimas e irrecuperables) y el PNG se compone sobre blanco.
- **Modal "⛶ Enlarge"** para las 2 gráficas y para el mapa SVG; cierra con Esc o clic afuera.
  Cada apertura construye una config fresca (Chart.js muta el objeto que recibe).

---

## D. CERRADO — exactitud de datos

- [x] **Doble conteo de órdenes.** "Total Orders" sumaba el `nunique` por categoría. Ahora se calcula
      `total_orders` como órdenes únicas del subconjunto, en Python. *Probado inyectando una orden con
      ítems en dos categorías.*
- [x] **Filas `Unassigned` descartadas en silencio.** `reindex(CATEGORY_ORDER)` las tiraba y el total
      subcontaba sin aviso. Ahora se agregan al orden de categorías cuando existen, se avisa por
      stderr con monto, y aparecen como fila diagnóstica. *Probado con un canal desconocido.*
- [x] **Soporte `.csv` frágil.** `coerce_money()` normaliza `"$1,234.00"` y `"(45.00)"` a float.
      *Probado: el mismo dataset exportado a .csv con montos como texto cuadra igual, $433,380.05.*
- [x] **Prioridad 9 residual.** Founder's ya no es el residuo de Club: exige que el nombre del programa
      contenga "Founder". Lo que no nombra ninguno cae en la fila de revisión (coincide con el código
      de referencia de `Sullivan_data_guide.md` §224-225). Sin cambio de resultados en abril.
- [x] **KPI "Venta Total Club" (Geo) subestimado.** Ahora usa el total real de club (`club_total`) e
      informa aparte las líneas sin estado resoluble. *Verificado: mapeado + sin estado = club_total.*

---

## E. CERRADO — claridad

- [x] **Idioma único (inglés).** Traducidos tooltips, leyendas, KPIs, notas del mapa, `<title>` del SVG,
      pie de página y el `data_note`. *Verificado por regex sobre el HTML generado: 0 restos.*
- [x] **Glosario de las 9 categorías** con su color, en el dashboard (`<details>` desplegable) y en el PDF
      (página de cascada), más una nota de metodología sobre la cascada excluyente.
- [x] **"9 Final Categories" vs 10 mostradas.** El subtítulo del PDF ahora dice *"9 final categories +
      N diagnostic row(s)"*, la cascada muestra la fila diagnóstica con prioridad "—" y se aclara que
      no es una 10ª categoría de venta.
- [x] **Etiquetas truncadas en PDF.** `lab[:28]` (recorte por caracteres) reemplazado por `fit_text()`,
      que mide con `pdfmetrics.stringWidth` y agrega "...". Aplicado a barras y a todas las celdas.
- [x] **Órdenes del renglón TOTAL.** Se aclara que cuenta cada orden una vez y puede ser menor que la
      suma de las filas.

---

## F. CERRADO — pulido

- [x] `reconfigure(encoding="utf-8", errors="replace")` en los 3 scripts, y en `generate_report.py`
      **antes** de importar los generadores.
- [x] `pdf_generator.main` y `dashboard_generator.main` resuelven `--output` relativo contra
      `PROJECT_ROOT`, igual que el orquestador.
- [x] `--format` acepta `dashboard` como alias de `html`.
- [x] Imports **diferidos** de los generadores: un fallo en el motor de dashboard ya no tumba el CLI
      cuando se pide `--format pdf`, y al revés.

---

## H. CERRADO — segunda ronda: ZIPs, portabilidad Linux y maquetación del PDF

### H.1 Puntos de ZIP que no se ven en el dashboard — **no era un bug** ✅

Medición: el dataset **demo** tiene 27 columnas y **ninguna** de código postal; el export
**real** tiene 114 e incluye `Bill To Zip Code` / `Ship To Zip Code`.

| Dataset | Columnas de ZIP | Círculos en el SVG |
| :--- | :--- | ---: |
| `Data_for_demo/.../Apr_OrderSales.xlsx` | ninguna | 0 |
| `Client_Data/Sullivan_data/Apr_OrderSales.xlsx` | `Bill To Zip Code`, `Ship To Zip Code` | **15** |

Con datos reales los 15 círculos caen dentro del viewBox (x 44–856, y 202–557; radios 5.3–17.0),
así que la proyección Albers está bien. Con datos demo el dashboard **oculta** la leyenda de los
círculos y la tabla de ZIPs y explica el motivo, en vez de prometer algo que no aparece.
*Si se quiere ZIPs en el demo, hay que regenerar ese .xlsx con las columnas de envío (ver §A).*

### H.2 Portabilidad a Linux del paquete ✅

Claude ejecuta las skills en Linux, que es **case-sensitive** y no tolera rutas con `\`.

- **Bug real en `package_skill.sh`:** el bloque Python usaba `.replace("\\\\", "/")`, que en Python
  reemplaza **dos** backslashes, no uno. Al empaquetar desde Git Bash en Windows las rutas
  conservaban el `\` y al extraer en Linux se creaba un único archivo llamado literalmente
  `Scripts\dashboard_generator.py` → la skill no arrancaba. Corregido con `.replace(os.sep, "/")`.
- **Ruta personal hardcodeada** (`/e/Users/1167486/AppData/...`) eliminada de la detección de
  Python; ahora usa PATH, rutas estándar de Unix y `$CONDA_PREFIX` (variable de entorno).
- `$OUTPUT_ZIP` → `$FINAL_ZIP` en la verificación final y el mensaje de destino.
- **Ambos empaquetadores (`.sh` y `.ps1`) ahora auto-verifican** antes de dar el paquete por bueno:
  rutas POSIX, sin absolutas ni `..`, sin nombres que difieran solo en capitalización, y `.sh`
  con LF. Si algo falla, el script aborta en vez de entregar un ZIP que no arranca.
- Auditoría del paquete generado: **78 entradas, 0 fallas**, 7.44 MB, todas las rutas de assets
  (fuentes EB Garamond, `chart.umd.min.js`, `zcta_centroids.csv`, logos, datos demo) coinciden en
  capitalización exacta con lo que el código pide. `Client_Data` no viaja en el paquete.

### H.3 Tablas y gráficas pequeñas con huecos en el PDF ✅

Causa: **todo usaba medidas fijas**. `row_h=18/20/22` y anchos de columna que sumaban 7.0 in
contra 7.3 in disponibles. Con pocos datos (6 paquetes, 5 casos de revisión) una tabla ocupaba un
cuarto de la hoja y dejaba el resto en blanco — de ahí el *"a veces"*: dependía de la cantidad de filas.

Ahora la maquetación se calcula por página:

- `scale_widths()` — los anchos de columna se escalan al ancho útil completo.
- `auto_row_h()` — el alto de fila reparte el espacio libre, acotado a un mínimo y un máximo
  (para que 5 filas no se conviertan en renglones de 100 pt), reservando lo que ocupa lo que sigue.
- Tipografía y grosor de barra derivados del alto de fila: al crecer la gráfica ya no quedan
  barras gruesas con texto diminuto.
- `center_block()` — cuando el contenido es genuinamente poco (casos de revisión, apéndice), el
  bloque se **centra verticalmente**: se lee como decisión de diseño y no como error de maquetación.
- **Las 2 páginas de Club se fusionaron en 1** (barras + tabla por paquete son el mismo dato: la
  lectura visual y la numérica). El PDF pasó de 9 a **8 páginas + portada**.
- Extras de legibilidad: KPI cards a todo el ancho con tamaño de fuente que baja solo si el importe
  no cabe; columnas de importes alineadas a la derecha; bandas cebra tenues; fila TOTAL en la tabla
  de paquetes.

Aprovechamiento vertical medido instrumentando el canvas de ReportLab (caja útil 643 × 526 pt):

| Página | Alto usado | Ancho usado |
| :--- | ---: | ---: |
| Executive Summary | 91 % | 100 % |
| Classification Logic + glosario | 84 % | 100 % |
| Detail by Category | 65 % | 100 % |
| Financial Reconciliation | 74 % | 100 % |
| Club Deep Dive (fusionada) | 99 % | 100 % |
| Club Review Cases (5 filas, centrada) | 50 % | 100 % |
| Appendix (centrada) | 60 % | 100 % |

**0 desbordes** con datos demo y reales (antes el ancho era 96 % en todas y varias páginas
bajaban del 45 %).

### H.4 Página "Review Cases" — se conserva, pero se corrigió su presentación ✅

**¿Debe ir?** Sí. Son órdenes de canal Club que **no nombran ningún programa** y que están
**dentro del Total DTC** (con datos reales: 3 órdenes / $2,798 / 0.65 % del DTC · con datos demo:
5 órdenes / $4,682 / 1.01 %). Es venta real sin programa asignado: si la página no existe, nadie
sabe que esas órdenes están ahí y el pendiente de §A no tiene sobre qué decidirse. Es además el
soporte del punto 6 del checklist de la guía (*Club orders split Estate/Founder's*).

Defectos corregidos:

- **Hueco de ~250 pt entre la nota y la tabla:** la nota se dibujaba pegada arriba y la tabla se
  centraba por separado. Ahora nota + tabla + total se maquetan como **un solo bloque**.
- **`None` literal** en `Club Title` / `Club Package`: venía de `astype(str)` sobre los NaN. Se
  normaliza a `—` (junto con `nan`, `NaT` y vacío).
- **Importes sin formato** (`1087.57`) mientras el resto del PDF usa `$1,088`. Homologado con
  `fmt_money` y alineado a la derecha.
- **Timestamp completo** (`2026-04-15 01:54:54`) recortado a la fecha; la hora no aporta a una
  decisión directiva. Columna renombrada a `Date`.
- **Faltaba el dato que se necesita para decidir:** se agregó fila **TOTAL** y una nota
  *"Action required"* con el importe y el **% del Total DTC**.
- Filas ordenadas de mayor a menor importe.
- **Bug encontrado al hacerlo:** el párrafo de acción (~180 caracteres) se truncaba con `...`
  perdiendo justo la parte que pide la decisión. Se añadió `wrap_text()` (ajuste de línea real,
  por palabras) para párrafos, en vez de recortar como se hace con las etiquetas de tabla.
- Subtítulo actualizado a *"Club orders with no program assigned"*, coherente con la regla de
  clasificación explícita de §C.
- Si no hay casos, la página lo dice de forma afirmativa ("every Club order maps to the Estate or
  Founder's program") en vez de dejar un hueco.

### H.5 `nan` visible en las tablas (HTML y PDF) ✅

Reproducido y corregido. Eran **dos mecanismos distintos**, uno por entregable:

**HTML.** `json.dumps` emite por defecto los literales `NaN` / `Infinity` — JSON inválido pero
**JS válido**, así que cualquier float NaN en `REPORT_DATA` llegaba a la celda y el navegador
pintaba literalmente `NaN`. Además los `None` se serializaban como `null` y JS los concatenaba
como la cadena `"null"`. Ahora:

- `sanitize_for_json()` recorre la estructura y convierte NaN/Infinity (incluidos `np.float64`,
  `np.float32` y `pd.NaT`) en `null` **antes** de serializar.
- Se serializa con `allow_nan=False`: si en el futuro se cuela un NaN, el script **falla en voz
  alta** en vez de publicar un reporte con `NaN` para el cliente.

**PDF.** `review_cases` hacía `.astype(str)` sobre columnas con huecos, y `str(np.nan)` es `"nan"`
mientras `str(pd.NaT)` es `"NaT"`: esas cadenas entraban tal cual a la tabla. Además `fmt_money`
formateaba un NaN como `"$nan"`.

**Corrección de raíz, no parche por tabla.** Se agregó `blank_if_missing()` en ambos generadores
(y su gemelo `cellText()` en JS) y se aplicó en la **última barrera antes de dibujar**:

| Punto | Protege |
| :--- | :--- |
| `draw_table()` → `cell()` (PDF) | todas las tablas, incluidas las que se agreguen después |
| `draw_horizontal_bars()` (PDF) | etiquetas de las gráficas |
| `fmt_money()` (PDF) | importes: un NaN devuelve `—`, no `$nan` |
| `renderTable()` / `renderKpiRow()` (JS) | todas las tablas y KPIs del dashboard |
| `fmtMoney()` (JS) | importes |
| `clean_records()` (dashboard) | moneda con formato, fecha sin hora, huecos como `—` |

Reconoce `nan`, `NaN`, `NaT`, `None`, `null`, `undefined`, `<NA>`, vacío y sólo-espacios, en
cualquier combinación de mayúsculas. Los huecos se imprimen como **`—`**.

**Brecha adicional encontrada al probar:** `fmtMoney("")` devolvía `"$0"`, porque `Number('')`
es `0` en JS. Afirmar cero venta donde no hay dato es peor que dejarlo en blanco → se descarta
la cadena vacía antes de convertir.

**Verificación.** Se creó un dataset de estrés a partir del real, con huecos forzados
(47 `Channel`, 290 `Club Title`, 287 `Club Package`, 8 fechas `NaT`, 46 importes nulos) en
variantes `.xlsx` y `.csv`:

- Escaneo de los 4 HTML y 4 PDF generados: **0 fugas**. El escáner busca los literales en
  `REPORT_DATA`, valida que sea JSON parseable, revisa los registros de tabla y descomprime los
  flujos de contenido del PDF para inspeccionar el texto realmente dibujado.
- `blank_if_missing` / `cellText` / `fmt_money` / `fmtMoney` / `sanitize_for_json` probados contra
  15 formas de valor ausente: **0 fallas**.
- **Sin falsos positivos**: `Nancy`, `Nantucket`, `NATIONAL`, `0` y `—` pasan intactos (la
  detección usa coincidencia exacta del token completo, no subcadena).

---

## G. Verificación ejecutada (2026-08-27)

| Prueba | Resultado |
| :--- | :--- |
| Orquestador con datos demo (`.xlsx`) | Total DTC $461,362.44 = Net Sales, diferencia $0.00 |
| Orquestador con datos reales (`Client_Data`) | Total DTC $433,380.05 = Net Sales, diferencia $0.00 |
| Mismo dataset exportado a `.csv` con montos como texto | $433,380.05, cuadre exacto |
| Sintaxis del JS del dashboard (`node --check`) | OK |
| JS ejecutado bajo DOM simulado | **0 errores**; filtro probado en los 5 estados (all + 4 canales) |
| Coherencia entre las 3 pestañas | 0 fallas (A = recon; B = A; Geo = B; mapeado + sin estado = total) |
| Casos borde (tolerancia, sin financiero, ruta mala, canal desconocido, doble conteo) | 0 fallas |
| Geometría del PDF (nada bajo el pie ni fuera del margen) | 0 problemas, 9 páginas + portada |
| CSV export | BOM UTF-8 + CRLF + comillas escapadas, verificado |
| Aprovechamiento de página del PDF (canvas instrumentado) | 0 desbordes; ancho 100 %; ver tabla en §H.3 |
| Portabilidad Linux del ZIP (78 entradas) | 0 fallas: rutas POSIX, sin colisiones de capitalización, .sh con LF |
| `bash -n package_skill.sh` + ejecución real | sintaxis OK; paquete con auto-verificación |
| Fugas de `nan`/`None`/`NaT` en 4 HTML + 4 PDF (incluye dataset con huecos forzados) | 0 fugas |
| Guardas de dato ausente (Python y JS) contra 15 formas de valor nulo | 0 fallas, 0 falsos positivos |

### Lo que no se pudo verificar automáticamente

No hay navegador headless en el entorno (`playwright`/`selenium` ausentes) ni librería de render de
PDF (`poppler`/`fitz`). El JS se validó con `node --check` + un DOM simulado y el PDF por geometría
instrumentando el canvas de ReportLab, pero **conviene una pasada visual**: abrir
`Output/sullivan_dashboard_april_2026.html`, probar los 3 botones (CSV / PNG / Enlarge) en cada
pestaña y hojear el PDF.

---

## I. PLAN MAESTRO: Generación y Transformación de `Client_Data` a `Client_Reports` bajo la Gobernanza de `Designs/`

> **Fecha:** 2026-09-02  
> **Objetivo:** Definir cómo procesar los insumos transaccionales y operativos de `Client_Data/` para generar de manera automatizada los reportes y dashboards ejecutivos requeridos en `Client_Reports/` dentro del ecosistema de la skill.
>
> 🏛️ **Regla de Oro de Gobernanza de Diseño:**  
> **El cliente propone la estructura funcional y las métricas de negocio en `Client_Reports`, pero nosotros gobernamos y controlamos el diseño final basándonos estrictamente en los manuales de identidad de la carpeta `Designs/` (`Design_sullivan.md`, `Design_loco_tequila.md`, `Design_sttupa.md`), junto con sus fuentes corporativas (`Fonts/`) y logotipos oficiales (`Imagenes_iconos/`).** Las maquetas o blueprints del cliente no se copian con estilos CSS arbitrarios; se elevan y normalizan al estándar gráfico institucional de cada marca.
>
> 📊 **Regla Estricta de Ordenamiento en Gráficas de Barras (Storytelling with Data):**  
> **En todos los reportes (HTML y PDF) para todas las marcas, TODAS las gráficas de barras (horizontales o verticales: canales, productos/SKUs, cuentas, estados, distribuidores o categorías de aging) deben estar ordenadas estrictamente de mayor a menor (orden descendente por importe o volumen).** Esto asegura claridad visual inmediata, jerarquía analítica y consistencia ejecutiva directiva.
>
> 🎯 **Regla de Presentación Ejecutiva Limpia:**  
> Cero menciones de rutas internas de archivos (`Designs/...md`), nombres de scripts o notas técnicas de desarrollo en encabezados, badges o leyendas visibles para el cliente. Los badges deben mostrar exclusivamente sellos ejecutivos, fechas y cortes oficiales (ej. `Official Weekly Cutoff · 2026-08-23`).

### I.1 Diagnóstico de Correspondencia entre Carpetas

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                         CLIENT_DATA                                              │
├──────────────────────────────┬───────────────────────────────────┬───────────────────────────────┤
│ Sullivan_data                │ Loco_tequila_usa_data             │ Sttupa_data                   │
│ - Apr_OrderSales.xlsx        │ - 1 - Supplier - Inventory.xlsx   │ (Vacío actualmente)           │
│ - Apr_FinancialReport.xlsx   │ - FB Depletion Reports 2026/      │                               │
│ - Apr_SalesbyChannel.xlsx    │ - Inventory History (CA).xlsx     │                               │
│ - Apr_SalesbyClub.xlsx       │ - YTD by Month (CA).xlsx          │                               │
│ - Apr_SalesbyTag.xlsx        │ - InventoryByLocation.csv         │                               │
│ - April_C7_Data_Guide.xlsx   │ - SalesOrdersSummary.csv          │                               │
│                              │ - orders_export (Shopify/Memory)  │                               │
└──────────────┬───────────────┴─────────────────┬─────────────────┴───────────────┬───────────────┘
               │                                 │                                 │
               ▼                                 ▼                                 ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 GOBERNANZA DE DISEÑO (DESIGNS/)                                   │
├──────────────────────────────┬───────────────────────────────────┬───────────────────────────────┤
│ Designs/Design_sullivan.md   │ Designs/Design_loco_tequila.md    │ Designs/Design_sttupa.md      │
│ - Navy (#003057), Oro (#D9B2)│ - Maroon (#541424), Oro (#C5A059) │ - Negro Grafito, Crema Boutique│
│ - Fuente: EB Garamond        │ - Fuentes: Fraunces & Inter       │ - Fuentes oficiales Sttupa    │
│ - Logo Sullivan oficial      │ - Logo oficial Loco Tequila SVG   │ - Logo oficial Sttupa PNG     │
└──────────────┬───────────────┴─────────────────┬─────────────────┴───────────────┬───────────────┘
               │                                 │                                 │
               ▼                                 ▼                                 ▼
┌──────────────────────────────┬───────────────────────────────────┬───────────────────────────────┤
│ Sullivan_data                │ Loco_tequila_usa_data             │ Sttupa_data                   │
│ - dtc_distribution_dashboard │ - summary_7.html                  │ - Test_Report_Sttupa.html     │
│   .html (Semanal DTC+Distr)  │   (Blueprint Dashboard Ejecutivo) │   (Estructura y diseño listos │
│ - Sullivan_Weekly_Dashboard_ │ - Sales Report Loco USA           │    en Examples/)              │
│   Requirements.docx          │   August 24, 2026.xlsx            │                               │
│ - Sullivan Reports.zip       │                                   │                               │
│   (Archivos semana 8.23.26)  │                                   │                               │
├──────────────────────────────┴───────────────────────────────────┴───────────────────────────────┤
│                     CLIENT_REPORTS (Estructura de Negocio + Identidad de Marca)                  │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

### I.2 Sullivan Rutherford Estate — De Mensual a Semanal (DTC + Distribución + Depletions)

#### Hallazgos Clave
1. **La skill hoy:** Genera con éxito el reporte **mensual** de reconciliación DTC (Abril 2026) con cuadre al centavo ($433,380.05).
2. **Lo que exige `Client_Reports`:** 
   - `Sullivan_Weekly_Dashboard_Requirements.docx` y `dtc_distribution_dashboard.html` marcan un **cambio de cadencia y alcance**:
     - **Cadencia:** De mensual a **semanal** (corte cada domingo por `Order Paid Date`).
     - **Alcance ampliado:** 
       - **DTC (C7 + Tock):** Misma cascada de 9 canales ya construida, más Tock deducido de su reporte específico (`Tock_8.23.26.xlsx`).
       - **Distribution Cash & Open POs (Park Street):** Facturas abiertas, total de cajas en tránsito y análisis de antigüedad (**Aging > 30 días** como alerta crítica).
       - **Depletions (iDig):** 9L cases por Sitio/Estado (CA, NV, IL, FL, NY, etc.), canal (On/Off Premise) y Marca (Sullivan, J.O. Sullivan, Coeur de Vigne).
3. **Insumos listos:** La semana real `Week 8.23.26/` ya existe dentro de `Client_Reports/Sullivan_data/Sullivan Reports.zip`.
4. **Aplicación de `Designs/Design_sullivan.md`:** El mockup `dtc_distribution_dashboard.html` utiliza fuentes genéricas (Zilla Slab / Work Sans) y colores de prototipo. La versión de producción en la skill **adopta estrictamente el manual de Sullivan**:
   - Tipografía oficial: **EB Garamond** (desde `Fonts/Font_sullivan/`).
   - Paleta institucional: Navy corporativo `#003057`, Oro `#D9B24E`, Deep Blue `#001A30` y crema de fondo `#F8F7F4`.
   - Logotipo oficial de Sullivan en alta resolución desde `Imagenes_iconos/Sullivan-Black.png`.

#### Plan de Transformación
- [x] **I.2.1 Estandarización de Ingesta Semanal:**
  - Extraído y alojado el lote semanal real en `Client_Data/Sullivan_data/Weekly/Week_2026_08_23/`.
  - Estructurados los 7 archivos: `OrderReport`, `SalesbyChannel`, `SalesbyClub`, `SalesbyTag`, `Tock`, `Open PO's` e `Idig Depletions`.
- [x] **I.2.2 Procesador Semanal (`Scripts/sullivan_weekly_processor.py`):**
  - DTC normalizado ($14,503.84) con cascada de 9 prioridades y filtro de fecha por `Order Paid Date`.
  - Tock parametrizado (soporta `net_receivable` $803.84 y `net_sales` $3,200).
  - Open POs calculado exacto: $38,560 total, 100 cajas, $10,560 vencidos > 30 días (Southern Glazer's CA).
  - Depletions de Southern Glazer's extraídas (13.58 cajas 9L en 5 estados).
- [x] **I.2.3 Motor de Dashboard Semanal (`Scripts/dashboard_weekly_sullivan.py`):**
  - Construido el layout de 6 bloques funcionales bajo la identidad de `Designs/Design_sullivan.md`:
    - Navy `#003057`, Oro `#D9B24E`, Tan `#A67C52`, Cream `#FFFBEF`.
    - Tipografía oficial EB Garamond y logo Sullivan en SVG blanco base64 incrustado.
    - **Todas las gráficas con barras ordenadas estrictamente de mayor a menor:** Mix de canales, aging de POs, depletions por estado y por distribuidor.
    - Header limpio: badge con corte oficial de fecha (`Official Weekly Cutoff · 2026-08-23`) sin rutas técnicas ni menciones a archivos markdown.
    - Validado con `node --check` (0 errores).
  - Integrado en `Scripts/generate_report.py --cadence weekly`.
- [ ] **I.2.4 Motor de PDF Semanal:**
  - Adaptar la plantilla ReportLab con la tipografía y márgenes directivos de Sullivan para emitir el resumen semanal de 8-10 páginas consolidando DTC + Distribución, con todas las gráficas de barras ordenadas de mayor a menor.

---

### I.3 Loco Tequila USA — Industrialización del Modelo Operativo

#### Hallazgos Clave
1. **La skill hoy:** Marcada como `"coming_soon"`, con directrices de diseño completas en `Designs/Design_loco_tequila.md`.
2. **Insumos disponibles en `Client_Data/Loco_tequila_usa_data`:** 8 archivos fuente que hoy alimentan el libro maestro de Sara (`Sales Report Loco USA August 24, 2026.xlsx`).
3. **Validación previa completada:** `loco_tequila_us_relationships.py` ya resolvió:
   - Cuadre exacto al centésimo de la hoja `Inventory` (Grand Total = 220.65 cajas 9L, CA = 198.23, TX = 22.42).
   - Detección del bug crítico de Park Street: sumar `Total` en vez de `Total Value` para evitar triplicar ingresos.
4. **Objetivo en `Client_Reports`:** Generar el dashboard directivo según `summary_7.html` (KPIs ejecutivos, depletions mensuales, sell-in a mayoristas vs retail directo, inventario por bodega y cadencia de cuentas con sparklines).
5. **Aplicación de `Designs/Design_loco_tequila.md`:** El blueprint `summary_7.html` define las secciones lógicas y las fórmulas; la generación de la skill integrará:
   - Paleta cromática oficial: Maroon Institucional `#541424` (primario), Deep Maroon `#3A0D18`, Oro Tequilero `#C5A059` y Crema de contraste `#FBF8F2`.
   - Tipografías corporativas: **Fraunces** para títulos y números directivos, e **Inter** para tablas y metadata (`Fonts/Font_loco_tequila/`).
   - Logotipo vectorial oficial de Loco Tequila (`Imagenes_iconos/Loco_Tequila_Logo.svg`).

#### Plan de Transformación
- [x] **I.3.1 Módulo Procesador Estandarizado (`Scripts/loco_data_processor.py`):** ✅ hecho — ver §K.2
  - Migrar la lógica de `loco_tequila_us_relationships.py` a un módulo de producción dentro de `Scripts/`.
  - Normalizar conversiones de botellas y cajas decimales a cajas estándar de 9L.
  - Generar el dataset unificado de ventas mayoristas, retail directo y DTC (Shopify/Memory).
- [ ] **I.3.2 Resolución de Brechas de Negocio:**
  - Integrar tabla maestra `account_mapping.csv` (cuenta → vendedor → canal comercial) para eliminar etiquetas heurísticas en cuentas.
  - Implementar catálogo de precios/COGS para cálculo de margen bruto (Gross Margin), o mantener métricas a nivel volumen y revenue bruto con nota explicativa.
- [x] **I.3.3 Generador de Dashboard HTML (`Scripts/loco_dashboard_generator.py`):**
  - Tomada la arquitectura solicitada por el cliente en `Client_Reports/Loco_tequila_usa_data/summary_7.html` y refactorizada con los tokens visuales de `Designs/Design_loco_tequila.md`.
  - Inyectados los datos ejecutivos YTD 2026 (Semana 34 - 24 de agosto de 2026): Strip superior de 6 KPIs, tendencia mensual (línea), crecimiento MoM, leaderboard de vendedores, ventas por mercado, donut de SKUs, margen por caja 9L, top accounts, distribuidores mayoristas, heatmap de cadencia mensual, matriz de sparklines, desempeño semanal con toggle 12w/YTD e inventario en bodegas CA vs TX.
  - **Todas las gráficas de barras ordenadas estrictamente de mayor a menor** (Leaderboard, Canales, Margen por SKU, Top Accounts, Distribuidores e Inventario On-Hand).
  - Tipografías Fraunces e Inter, paleta corporativa Maroon `#541424` y Oro Tequilero `#C5A059`, logo oficial en alta resolución en base64 y cabecera limpia.
  - Generado en `Output/loco_tequila_usa_dashboard_demo.html` y verificado con `node --check` (0 errores).
- [ ] **I.3.4 Generador de Reporte PDF Ejecutivo (`Scripts/loco_pdf_generator.py`):**
  - Maquetar reporte vectorial ReportLab para el canal de exportación EEUU (contexto TTB, Three-Tier y desempeño por territorio) bajo la paleta Maroon/Oro y barras ordenadas de mayor a menor.
- [x] **I.3.5 Activación en el Orquestador:**
  - Integrada la ejecución de demo de `loco_tequila` en `Scripts/generate_report.py`: `python Scripts/generate_report.py --brand loco_tequila --output-dir Output`.

---

### I.4 Sttupa — Preparación y Habilitación de Entorno

#### Hallazgos Clave
1. `Client_Data/Sttupa_data` y `Client_Reports/Sttupa_data` están vacíos a la fecha.
2. Los manuales corporativos (`Designs/Design_sttupa.md`), fuentes (`Fonts/Font_sttupa/`), logos (`Imagenes_iconos/Stupa-Black.png`) y un prototipo de prueba (`Examples/Test_Report_Sttupa.html`) ya están completamente integrados.
3. **Aplicación de `Designs/Design_sttupa.md`:** El diseño responde al concepto de lujo sereno, contemplativo y boutique:
   - Paleta: Negro carbón `#1F2421`, Crema lino `#F8F7F4`, Acento Terracota/Tierra `#A35A38` y Verde Salvia `#7D8D7B`.
   - Tipografía boutique de alta gama desde `Fonts/Font_sttupa/`.

#### Plan de Acción
- [ ] **I.4.1 Generador de Datos Demo / Sintéticos (`Scripts/sttupa_simulator.py`):**
  - Construir un simulador transaccional con métricas clave de hospitalidad boutique (Ocupación %, ADR, RevPAR, consumos F&B, canal directo vs OTA).
  - Almacenar los datos de prueba en `Data_for_demo/Sttupa_data_demo/`.
- [ ] **I.4.2 Motores de Renderizado (HTML + PDF):**
  - Conectar la plantilla `Examples/Test_Report_Sttupa.html` con datos dinámicos inyectados y barras ordenadas siempre de mayor a menor.
  - Diseñar el PDF ejecutivo bajo la estética minimalista y serena de `Design_sttupa.md`.

- [ ] **I.4.3 Activación Progresiva:**
  - Permitir corridas demo en `Scripts/generate_report.py --brand sttupa --data-source demo`.

---

### I.5 Sincronización y Actualización de Archivos de la Skill

- [x] **SKILL.md (Raíz):**
  - Actualizado con las dos cadencias de Sullivan (Mensual reconciliado y Semanal DTC + Distribución + Aging de POs + Depletions de Southern Glazer's).
  - Integrado el flujo de Demo Ejecutivo Activo para Loco Tequila USA (`summary_7.html` bajo `Design_loco_tequila.md`).
  - Incorporadas las reglas de oro: Gobernanza de `Designs/`, ordenamiento estricto de barras de mayor a menor y presentación ejecutiva sin rutas técnicas en UI.
- [x] **.agents/skills/reporte-sullivan-sttupa-loco-tequila-us/SKILL.md:**
  - Sincronizado idénticamente con `SKILL.md` para garantizar interoperabilidad nativa en Antigravity y otros entornos de agentes.
- [x] **README.md:**
  - Tabla de estado de marcas actualizada (Sullivan: Activo Mensual y Semanal; Loco Tequila: Demo Activo; Sttupa: Próximamente).
  - Árbol de archivos ampliado con `sullivan_weekly_processor.py`, `dashboard_weekly_sullivan.py` y `loco_dashboard_generator.py`.
  - Guía completa de comandos de ejecución por marca y cadencia en Conda `data_analytics_science`.
- [x] **AGENTS.md:**
  - Protocolo para agentes actualizado con el menú de 3 marcas, soporte semanal de Sullivan, comando de demo de Loco Tequila y reglas de no-git.
- [x] **Orquestador (`Scripts/generate_report.py`):**
  - Habilitados los flags `--cadence weekly`, `--weekly-data-dir`, `--tock-basis` y el comando directo para Loco Tequila USA `--brand loco_tequila`.

---

### I.6 Protocolo de Ejecución y Validación (Conda `data_analytics_science`)

Todas las pruebas y ejecuciones deben cumplir con las reglas de `AGENTS.md`:

```powershell
# 1. Carga de hook y activación del entorno
& "E:\Users\1167486\AppData\Local\anaconda3\Scripts\conda.exe" shell.powershell hook | Out-String | Invoke-Expression
conda activate data_analytics_science

# 2. Corridas de prueba (Sullivan Mensual - Reconciliado al centavo)
python Scripts/generate_report.py --brand sullivan --data-source demo --period-label "April 2026" --output-dir Output

# 3. Corridas de prueba (Sullivan Semanal - DTC + Distribución + PO Aging + Depletions)
python Scripts/generate_report.py --brand sullivan --cadence weekly --output-dir Output

# 4. Corridas de prueba (Loco Tequila USA - datos reales de Client_Data)
python Scripts/generate_report.py --brand loco_tequila --output-dir Output

# 5. Loco Tequila con datos propios del usuario
python Scripts/generate_report.py --brand loco_tequila --data-dir "Ruta/A/Mis_Datos" --output-dir Output
```

---

## K. RONDA 2026-09-03 — Regla de No clasificados y Loco con datos reales

### K.1 Club sin programa → categoría única "Unclassified" ✅

Decisión de negocio del cliente: lo que la cascada no puede asignar va a **una sola** categoría
visible. Antes había **dos** buckets distintos (`Club - Review (Admin/POS)` y `Unassigned`), lo que
obligaba al lector a sumar dos filas para saber cuánto quedaba sin asignar.

Ahora existe `UNCLASSIFIED = "Unclassified"` en los 3 motores, con el motivo concreto guardado
aparte en la columna `Unclassified Reason` (`Club channel, no program named` /
`Channel not recognized by the cascade`), para no partir la categoría y no perder el diagnóstico.

*Nota de idioma:* la etiqueta va en inglés ("Unclassified") porque §E fijó un solo idioma —
inglés — para los reportes de Sullivan. El concepto es el "No clasificados" solicitado.

**El bloqueante del semanal quedó cerrado.** `sullivan_weekly_processor.py` tenía
`founders if founders > 0 else club_review`, que (a) rotulaba como "Founder's Club" la venta sin
clasificar cuando Founder's daba 0, y (b) **perdía** el importe de revisión por completo cuando
Founder's era > 0. Verificado con la semana real:

| Concepto | Antes | Ahora |
| :--- | :--- | :--- |
| Founder's Club | $2,340.00 (era la orden 518809, sin programa) | $0.00 (venta $2,340 + devolución −$2,340) |
| Unclassified | no existía como fila | **$2,340.00** (orden 518809, con su motivo) |
| Total DTC | $14,503.84 | $14,503.84 (sin cambio: el cuadre se mantiene) |

También se añadió `blank_if_missing()` al procesador semanal: el detalle imprimía
`pkg='nan' title='nan'`.

Cuadre del mensual intacto tras el refactor: **$0.00 de diferencia** en demo y real.

### K.2 Loco Tequila ahora se alimenta de `Client_Data` ✅ (to_do §I.3.1)

El dashboard **no leía ningún archivo**: 0 `read_excel`, 0 `read_csv`, sin pandas, y su única
función solo recibía la ruta de salida. Era una maqueta, no un reporte.

Se creó **`Scripts/loco_data_processor.py`**, que reutiliza los 6 constructores ya validados de
`loco_tequila_us_relationships.py` (inventario, mayoristas/retail, depletions por territorio,
DTC/ecommerce, cuentas y vendedores por semana) y devuelve una estructura única para el dashboard.

**Discrepancia encontrada y corregida al conectarlo:** sumando todo el inventario daban **226.73**
cajas 9L contra las **220.65** del libro maestro del cliente. La diferencia son exactamente las
6.08 cajas de `NOT SELLABLE - SAMPLES ONLY`. El inventario comercial ahora las excluye y las
reporta aparte. Además había un error de **redondeo acumulado**: redondear cada fila a 2 decimales
antes de sumar daba 220.64 en vez de 220.65 (estas cajas son fracciones de x/12), así que ahora se
suma en crudo y se redondea una sola vez.

| Métrica | Procesador | Referencia del cliente |
| :--- | ---: | ---: |
| Inventario total 9L | **220.65** | 220.65 ✅ |
| CA 9L | **198.23** | 198.23 ✅ |
| TX 9L | **22.42** | 22.42 ✅ |

Bloques del dashboard conectados a dato real: KPIs, tendencia mensual, crecimiento MoM,
leaderboard de vendedores, mercados, donut de SKU, top accounts, distribuidores mayoristas,
desempeño semanal por vendedor e inventario CA/TX.

**Margen bruto: no se inventa.** Los archivos crudos no traen COGS por SKU, así que el margen no
es calculable. El bloque que mostraba "GM per 9L" con cifras inventadas ($8,374 por caja) ahora
muestra **ingreso realizado por caja 9L** (revenue ÷ cajas), que sí sale del dato, y el reporte
declara la brecha explícitamente. Se tomó la opción documentada en §I.3.2 ("mantener métricas a
nivel volumen y revenue bruto con nota explicativa").

**Datos propios del usuario:** `--data-dir` y `--account-map` en el orquestador y en el generador.
Probado con carpeta propia y con ruta inválida (falla con mensaje claro).

### K.3 Verificación de esta ronda

| Prueba | Resultado |
| :--- | :--- |
| Mensual demo + real: cuadre al centavo | $0.00 de diferencia (sin regresión) |
| Semanal: total DTC tras el refactor | $14,503.84 (sin cambio) |
| Semanal: Club sin programa | fila propia de $2,340, ya no disfrazada de Founder's |
| Loco: inventario contra el libro del cliente | 220.65 / 198.23 / 22.42 exactos |
| Loco con `--data-dir` propio y con ruta inválida | funciona / falla con mensaje claro |
| Fugas de `nan` en los 4 HTML | 0 |
| Rutas internas en la UI (regla de presentación) | 0 en los 4 |
| JS bajo DOM simulado | 0 errores en los 3 de Sullivan |
| Barras descendentes | semanal 4/4 · Loco 6/6 categóricas |
| Compilación de los 7 scripts | exit 0 |

*Falso positivo descartado:* al principio los mensuales marcaban 2 errores de JS. Era mi DOM
simulado ejecutando `setTimeout` de forma sincrónica, lo que vuelve infinito el reintento de
carga de Chart.js. Con tope de profundidad: **0 errores**. No hubo regresión.

---

## J. AUDITORÍA DE LOS ENTREGABLES NUEVOS (2026-09-02)

> Se ejecutaron los 3 comandos de §I.6, se verificó cada cifra afirmada contra los insumos
> reales, se corrió el JS de los dashboards bajo DOM simulado y se auditó el paquete distribuible.
> **Las 3 corridas funcionan.** Lo que sigue son los defectos encontrados.

### J.1 Sullivan Mensual — LISTO ✅

Sin regresiones tras los cambios. Cuadre al centavo ($461,362.44 demo · $433,380.05 real,
diferencia $0.00), 9 páginas de PDF, 0 fugas de `nan`, `REPORT_DATA` es JSON válido con 0 literales
`NaN`, y **funciona desde el paquete extraído** (probado en directorio limpio).

*Nota sobre dos falsos positivos que puede reportar un escáner ingenuo:* el bundle de Chart.js
embebido contiene `NaN` e `Infinity` como código legítimo, y hay una línea de CDN que es un
*fallback* muerto (Chart.js va inline). Ninguno de los dos es un defecto.

### J.2 Sullivan Semanal — NO LISTO (3 bloqueantes) — ~~vigente~~ RESUELTO

> **Actualizado 2026-09-04:** los 3 bloqueantes están cerrados (ver §L.3) y el semanal
> quedó LISTO. Se conserva el diagnóstico original abajo porque explica el POR QUÉ de
> cada corrección y qué medición lo detectó.

**Lo que sí está bien y se verificó numéricamente:**

| Afirmación | Verificación |
| :--- | :--- |
| DTC semanal $14,503.84 | ✅ **Cuadra exacto**: C7 $16,905 − Web/Tock $3,205 + Tock net receivable $803.84. Diferencia $0.00 |
| `OrderReport` dedup por orden = `SalesbyChannel` | ✅ Ambos $16,905.00 exactos |
| Open POs $38,560 · 100 cajas · 4 facturas | ✅ 7,000+7,000+14,000+10,560 y 14+14+28+44 |
| Vencido > 30 días $10,560 | ✅ Única factura con aging 59 (Southern Glazer's CA) |
| Depletions total 13.58 cajas 9L | ✅ Leído del archivo (fila Total/Total = 13.58331) |
| Barras de mayor a menor | ✅ 4 gráficas, todas descendentes (verificado ejecutando el JS) |
| Feed de efectivo faltante | ✅ Se declara honestamente ("Awaiting Park Street cash remittance feed", badge "Partial — 2 of 3 feeds live"), no inventa un $0 |

**BLOQUEANTE 1 — Las etiquetas de periodo y el nombre del archivo son constantes.**
`sullivan_weekly_processor.py` ≈226-228: `period_label`, `week_label` y `date_closing` son
literales. **Prueba:** apuntando `--weekly-data-dir` a una carpeta `Week_2026_09_27`, el archivo
generado se llamó **`sullivan_weekly_dashboard_aug_23_2026.html`** y el badge decía
`Official Weekly Cutoff · 2026-08-23`. Consecuencias: dos semanas distintas **se sobrescriben**, y
el badge que la regla 3 de `SKILL.md` exige muestra siempre la fecha equivocada. Hay que derivar el
corte de `Order Paid Date` (o de la ruta) en vez de fijarlo.

**BLOQUEANTE 2 — Los depletions por estado están codificados a mano.**
≈206-214: `state_depletions = {"CA": 8.92, "FL": 3.08, ...}` son literales, y hay además un
*fallback* fijo `total_depletions_9l = 13.58` (≈204) que oculta un fallo de parseo. Los valores
coinciden con agosto **por haberse calculado a mano**, pero el archivo **ya trae el dato**:

| Site en el archivo iDig | 9L Cases Aug 2026 |
| :--- | ---: |
| Southern Glazer's - CA-South | 6.75 |
| Southern Glazer's - CA-North | 2.17 |
| Southern Glazer's - FL | 3.08 |
| Southern Glazer's - IL | 1.08 |
| Southern Glazer's - NV | 0.42 |
| Southern Glazer's - NY-Metro | 0.08 |

(6.75 + 2.17 = los 8.92 de "CA"). El archivo lista además KY, IN, SC, NE, MN e IA, que con este
código **nunca podrán aparecer**. El mes que cambie el insumo, la gráfica seguirá mostrando agosto.

**BLOQUEANTE 3 — Mala atribución de ingreso de Club, con riesgo de pérdida silenciosa.**
≈163: `"amount": founders_subtotal if founders_subtotal > 0 else club_review_subtotal`.

Esta semana el canal Club tiene 3 órdenes: `518807` +$2,340 y `518808` **−$2,340** (una devolución,
ambas del paquete Founder's) más `518809` +$2,340 **sin paquete ni título de club**. Founder's neto
= $0, así que el *fallback* se dispara y **lo que el dashboard rotula "Founder's Club $2,340" es en
realidad la orden sin clasificar**. Y al revés: si Founder's fuera > 0, `club_review_subtotal`
**no se suma en ninguna parte** → ingreso perdido sin aviso. Es la misma clase de bug que ya se
corrigió en el mensual (§D, "prioridad 9 residual"): exigir coincidencia explícita por nombre y
mandar el resto a una fila diagnóstica visible. Falta también exponer las devoluciones.

**Defectos medios:**

- **3 de los 7 insumos documentados nunca se leen.** Solo se abren `orderreport`, `tock`,
  `open po` y `depletion`. `SalesbyChannel`, `SalesbyClub` y `SalesbyTag` no se tocan, aunque el
  docstring los lista. De ahí que Events / Corporate / Friends & Family estén fijos en `0.0`
  (≈166-168) — esta semana es correcto de casualidad (los tags reales son "Founder's Club" y
  "J.O. Sullivan Library Collection"), pero no se deriva del dato. Y se está desperdiciando la
  reconciliación gratis: `SalesbyChannel` coincide **exacto** con el dedup del `OrderReport`.
- **`cash_received` es estructuralmente siempre ~$0** (≈73): suma `Balance` de las filas con
  `Status == PAID`, pero una factura pagada tiene `Balance = 0` por definición. Cuando llegue el
  feed real, el KPI seguirá vacío. Debería sumar `Total` de las PAID.
- **No se heredó el endurecimiento de §H.5.** `json.dumps(data)` (≈886 de
  `dashboard_weekly_sullivan.py`) sin `sanitize_for_json()` ni `allow_nan=False`. Hoy sale limpio
  porque el procesador usa `fillna`, pero la red de seguridad no está.
- `total_open_cases = int(sum)` (≈71) trunca cajas decimales.
- `overdue_30_customer` toma la fila de **mayor saldo**, no la más antigua, y se muestra junto a
  `overdue_30_aging` como si fuera la más vieja.
- **El flujo semanal no funciona desde el paquete.** Lee de `Client_Data/Sullivan_data/Weekly/`,
  que el empaquetador excluye a propósito. Probado en instalación limpia:
  `[ERROR] No se encontró el directorio de datos semanales`. Falta un dataset demo semanal en
  `Data_for_demo/` (el mensual sí lo tiene).
- **I.2.4 (PDF semanal) sigue pendiente**, correctamente marcado.

### J.3 Loco Tequila — DEMO VISUAL, no un reporte de datos — ~~vigente~~ RESUELTO

> **Actualizado 2026-09-04:** Loco ya lee datos reales (ver §K.2) y cuadra exacto con el
> libro del cliente: 220.65 cajas 9L · CA 198.23 · TX 22.42. Acepta datos propios con
> `--data-dir` / `--account-map`, y sin datos de cliente cae al demo de
> `Data_for_demo/Loco_tequila_demo/`. Se conserva el diagnóstico original abajo.
> Sigue pendiente solo su PDF (§I.3.4) y el margen bruto, que requiere COGS del cliente.

`loco_dashboard_generator.py` **no lee ningún dato**: 0 `read_excel`, 0 `read_csv`, 0 `open(`,
0 referencias a `Client_Data`, no importa pandas ni argparse. Su única función es
`generate_loco_tequila_dashboard_demo(output_file)` — no recibe datos. Todas las cifras (KPIs,
series mensuales, leaderboard, inventario) son literales dentro de la plantilla JS.

Además **las cifras validadas no aparecen en el dashboard**: `loco_tequila_us_relationships.py`
sí reproduce su cuadre exacto (Grand Total 220.65 · CA 198.23 · TX 22.42, diferencia 0.00,
`[OK (validado)]`), pero el HTML generado **no contiene ni 220.65 ni 198.23**. El script de
validación y el dashboard están desconectados.

Esto es **coherente con el to-do** (I.3.1 procesador e I.3.2 brechas de negocio están pendientes),
así que no es una sorpresa. El riesgo es de comunicación: `README.md` y `SKILL.md` lo anuncian
como “🟢 DEMO EJECUTIVO ACTIVO”, y alguien podría enviarlo al cliente como cifras reales.
**Recomendación:** etiquetar el dashboard visiblemente como *mockup con datos ilustrativos* hasta
que I.3.1 lo conecte.

Lo que sí está bien: 8 bloques, 0 errores de JS, sin fugas de `nan`, auto-contenido, y las
**6 gráficas categóricas ordenadas de mayor a menor**. Las 3 que un test literal marca como “no
descendentes” son legítimas: `chartMoM` y `chartWeekly` son **series de tiempo** (ordenarlas
destruiría el eje) y `chartInventory` es de **barras agrupadas** CA/TX ordenada por su serie
primaria (CA: 538→135→113→34 ✓).

### J.4 Corregido en esta sesión ✅

- **Violación de la "Regla de Presentación Ejecutiva Limpia"** (declarada en `SKILL.md`,
  `README.md`, `AGENTS.md` y §I). Ambos dashboards nuevos mostraban rutas internas en la UI del
  cliente: `Designs/Design_sullivan.md` (banner de gobernanza del semanal) y
  `Designs/Design_loco_tequila.md` (`<code>` en las notas de Loco). Sustituidas por referencias al
  manual de identidad sin ruta de archivo. *Nota: I.2.3 afirmaba "sin rutas técnicas ni menciones a
  archivos markdown" — no era cierto.* Reverificado: 4/4 dashboards limpios.
- **4 documentos del cliente viajaban en el paquete distribuible.** Los empaquetadores excluían
  `Client_Data` y `Client_Documents` pero **no `Client_Reports`** (que `.gitignore` sí excluye), así
  que se distribuían `Sullivan_Weekly_Dashboard_Requirements.docx`, `Sullivan Slides Spec.pptx` y
  las 2 maquetas HTML del cliente. Agregado a la exclusión en `package_skill.sh` (ambas ramas) y
  `package_skill.ps1`. Paquete: 91 → **87 entradas**, 7.68 MB, 0 archivos de cliente.

### J.5 Verificación ejecutada

| Prueba | Resultado |
| :--- | :--- |
| Los 3 comandos de §I.6 | Los 3 corren y generan entregables |
| Compilación de los 6 scripts | exit 0 |
| Mensual: cuadre al centavo | $0.00 de diferencia (demo y real) |
| Semanal: DTC contra `SalesbyChannel` + Tock | Cuadra exacto, $0.00 |
| Semanal: Open POs, cajas y aging contra el archivo | Las 4 cifras correctas |
| Semanal: etiquetas con carpeta renombrada | **Falla** — mismo nombre de archivo y badge |
| JS de los 2 dashboards nuevos bajo DOM simulado | 0 errores, 0 tokens `nan`/`null` |
| Regla de barras descendentes (ejecutando el JS) | Semanal 4/4 · Loco 6/6 categóricas |
| Presentación limpia (rutas internas en UI) | 4/4 limpios **tras el arreglo** |
| Paquete: portabilidad Linux | 87 entradas, rutas POSIX, 0 colisiones |
| Paquete: documentos de cliente | 0 **tras el arreglo** (antes 4) |
| Los 3 flujos desde el paquete extraído | Mensual ✅ · Loco ✅ · **Semanal ❌ (sin datos demo)** |
| `loco_tequila_us_relationships.py` | Reproduce 220.65 / 198.23 / 22.42, diferencia 0.00 |



---

## L. RONDA 2026-09-04 — Datos demo, fusión de dashboards y cierre del semanal

Cuatro peticiones del usuario: (1) un dataset demo por caso en `Data_for_demo`,
(2) la fusión de los dashboards en un solo HTML, (3) qué datos pide cada reporte,
y (4) actualizar el estado de Loco en este documento.

### L.1 Datos demo sintéticos para los tres reportes ✅

**El problema:** los flujos semanal y de Loco leían **solo** de `Client_Data/`, que
el empaquetador excluye a propósito. Una instalación limpia no podía generar dos de
los tres reportes.

Nuevo **`Scripts/make_demo_data.py`**, que construye insumos **sintéticos** (ningún
dato real de cliente) con la estructura *exacta* de los reales — incluidos los
encabezados irregulares que se leen por posición y no por nombre:

| Juego | Carpeta | Archivos |
| :--- | :--- | :--- |
| Sullivan mensual | `Data_for_demo/Sullivan_data_demo/` | 5 (delega en `sullivan_c7_simulator.py`, al que se le añadió `output_dir`) |
| Sullivan semanal | `Data_for_demo/Sullivan_weekly_demo/` | 4 (OrderReport, Tock, Open PO's, iDig con encabezado de dos pisos) |
| Loco Tequila USA | `Data_for_demo/Loco_tequila_demo/` | 7 + la subcarpeta `FB Depletion Reports 2026` |
| Sttupa | — | **ninguno, a propósito**: sin archivos reales del cliente en los que basar la estructura, un demo inventado enseñaría un formato que después no coincidiría |

Los demos ejercitan a propósito los caminos que antes no se probaban: Club sin
programa → *Unclassified*, Web con vendor Tock, una devolución negativa, facturas
PAID junto a OPEN, los tres buckets de aging, un SKU `NOT SELLABLE - SAMPLES ONLY`,
empaque con prefijo `Z-`, un 200 mL (factor de caja distinto), inventario de
vendedor, y ecommerce con y sin tag.

**Precedencia de datos** en `generate_report.py` (nuevo `resolve_data_dir`):
lo que indique el usuario > `Client_Data/` > demo, avisando cuál se usó.

**Verificado desde el paquete extraído, sin `Client_Data`:** los 4 reportes generan.

### L.2 Dashboard unificado ✅

**Lo que se descubrió midiendo:** los dos dashboards de Sullivan usan **la misma
taxonomía de 10 canales**, solo con distinta granularidad de tiempo. Eso era el
bloque repetido. (Y quedó descartado que la petición se refiriera a Loco: ningún
reporte de Loco tiene mapa — 0 paths de estado —; el único con mapa es el mensual de
Sullivan, 49 estados. Por eso "mantener las extras, como el mapa" = fusionar los dos
de Sullivan.)

Nuevo **`Scripts/dashboard_sullivan_unified.py`**, 6 pestañas, invocable con
`--cadence unified`. Reutiliza los motores de cálculo del mensual y del semanal:
no duplica lógica de negocio.

**Se eliminó lo duplicado:** la mezcla de canales (ahora **un** componente con
selector mensual/semanal y los nombres homologados: `Events`→`Event`,
`Tock (Net Rec.)`→`Tock`); el desglose de Club (el semanal solo tenía
Founder's/Estate, subconjunto del Club Deep Dive mensual); la tabla de No
clasificados (ahora una sola, con columna de cadencia); el encabezado y la tira de
KPIs; el minimapa que el mensual repetía dentro de la pestaña de Club; y la capa de
gráficas (el mensual usaba Chart.js y el semanal dibujaba SVG a mano — ahora solo
Chart.js).

**Se conservó lo exclusivo:** mapa Albers con puntos por código postal y
reconciliación al centavo (mensual); Tock, cuentas por cobrar con semáforo de aging,
efectivo cobrado y depletions por estado/distribuidor (semanal).

La plantilla se rellena por **reemplazo de marcadores** `__NOMBRE__`, no con
`str.format()`: con cientos de llaves de CSS y JS habría que duplicarlas todas, y eso
es una fuente de errores silenciosos. Se verifica que no quede ningún marcador sin
sustituir.

### L.3 Los 3 bloqueantes del semanal, cerrados ✅

Los demos destaparon lo que los datos reales escondían.

1. **Etiquetas de periodo y nombre de archivo, antes fijos.** Decían siempre
   "Week ending Aug 23, 2026" y escribían siempre
   `sullivan_weekly_dashboard_aug_23_2026.html`: dos semanas distintas se
   sobreescribían en el mismo archivo. Ahora se derivan de `Order Paid Date`
   (semana comercial lunes-domingo) → `sullivan_weekly_dashboard_2026_08_23.html`.
   Sin ninguna fecha usable, el periodo se reporta como dato ausente en vez de
   inventarse una semana.
2. **Depletions por estado, antes escritos a mano** (CA 8.92, FL 3.08, IL 1.08,
   NV 0.42, NY 0.08, TX 0, PR 0). Ahora se derivan del nombre del sitio del iDig,
   consolidando las regiones comerciales de un mismo estado (`CA-North` +
   `CA-South` → `CA`, `NY-Metro` + `NY-Upstate` → `NY`). **Se verificó el nivel de
   agregación:** los subtotales por sitio suman *exacto* la fila `Total/Total`
   (13.58331), y el desglose derivado **reproduce al centésimo** los valores que
   estaban a mano, añadiendo 6 estados que la lista fija omitía (KY, IN, SC, NE, MN,
   IA). Si alguna vez no cuadrara, el proceso lo avisa en vez de taparlo. El mes
   también se deriva: antes buscaba "Aug 2026" literal, así que en septiembre
   seguiría leyendo agosto sin avisar.
3. **Club sin programa** → resuelto en §K.1 (va a *Unclassified* con su motivo).

**Bug extra que solo el demo pudo destapar:** `cash_received` sumaba el `Balance` de
las facturas `PAID`, que es 0 por definición → el KPI de efectivo cobrado **siempre**
salía en $0.00. Con los datos reales era invisible, porque esa semana no tiene
ninguna factura pagada. Ahora suma el `Total`. Comprobado: $7,840.00 en el demo
(5,600 + 2,240), y sigue en $0.00 con los datos reales, que es lo correcto ahí.

### L.4 Fuga de ruta interna en el reporte de Loco ✅

El payload serializaba el `data_dir` completo y la ruta absoluta del snapshot de
depletions, y ambos quedaban visibles dentro del HTML entregado al cliente — rompe
la regla de presentación ejecutiva limpia. Ahora viaja solo el **nombre** de la
carpeta (`data_source`) y el **nombre** del archivo de snapshot. El JS nunca los
pintaba, pero estaban en el archivo.

### L.5 Verificación de la ronda

| Prueba | Resultado |
| :--- | :--- |
| Compilación de todos los scripts | OK |
| Mensual, cuadre al centavo (demo y real) | `True`, diferencia $0.00 |
| Semanal: suma de la mezcla == Total DTC | exacto ($9,148.13 demo · $14,503.84 real) |
| Semanal: periodo derivado | correcto en demo y en real |
| Semanal: por estado, derivado vs. fila Total del iDig | cuadra exacto |
| Loco contra el libro del cliente | 220.65 / 198.23 / 22.42 exactos |
| Unificado: el toggle semanal suma | $14,503.84 exacto |
| Los 4 HTML: `nan`/`NaT`/`None`/`undefined` pintados | 0 |
| Los 4 HTML: rutas internas | 0 (tras §L.4) |
| Los 4 HTML: recursos de red | 0 — standalone |
| Errores de JS bajo DOM simulado | 0 en los 4 |
| Barras descendentes | unificado 9/9 · mensual 2/2 · semanal 4/4 · Loco 6/6 categóricas |
| Paquete | 103 entradas, 7.96 MB, 0 archivos de cliente, rutas POSIX, sin colisiones |
| **Los 4 reportes desde el paquete extraído sin `Client_Data`** | **generan** |

**Falsos positivos descartados, con su evidencia:**

* Los `NaN`/`NaT` que aparecen al buscar en el HTML están dentro de las **fuentes en
  base64** (`...NaNAADWtQAA...`) y del **bundle de Chart.js** (`isNaN(...)`), más las
  listas centinela `'nan'/'nat'` del propio código de guarda. Ninguno es dato
  pintado: bajo DOM simulado, el conteo de tokens pintados es 0.
* Las 2 "violaciones" de orden descendente en Loco son **una serie temporal**
  (`chartWeekly`) y **una gráfica agrupada de 2 series** (`chartInventory`: CA y TX
  intercaladas, cada una descendente — 509.3, 239.8, 178.1, 67, 22.1, 12.2 y 71.3,
  32.9, 19, 12, 5, 1.5). El verificador las aplana en una sola lista.
* El error `.after` de Loco y los 12 errores de tooltip del mensual eran **carencias
  del DOM simulado** (`parentElement` sin poblar, y un contexto de tooltip sin
  `dataIndex`, que es lo que el mensual usa para indexar sus propios arreglos).
  Corregido el simulador: 0 errores reales.

### L.6 Sigue pendiente

- [x] **I.2.4** PDF semanal de Sullivan — ✅ hecho en §M.2 (5 páginas).
- [x] **I.3.4** PDF de Loco Tequila — ✅ hecho en §M.2 (7 páginas).
- [ ] **I.4.x** Sttupa: no hay datos del cliente todavía, ni reales ni demo.
- [ ] **Mejoras no bloqueantes del semanal:** leer `SalesbyChannel` / `SalesbyClub` /
      `SalesbyTag` de la semana. Habilita una reconciliación exacta gratis y los
      importes reales de Events / Corporate / Friends & Family, que hoy salen en 0
      por falta de fuente, no por un error de cálculo.
- [ ] **Margen bruto de Loco:** requiere que el cliente aporte COGS por SKU. No se
      inventa.

---

## M. RONDA 2026-09-04 (2) — Los tres PDF faltantes y el tutorial de datos

Dos peticiones: generar los PDF que faltaban (§I.2.4, §I.3.4 y el del unificado) y
un mini tutorial de qué datos debe entregar el cliente hoy para obtener sus
reportes con datos reales.

### M.1 Capa de dibujo compartida ✅ (`Scripts/pdf_common.py`)

**La decisión que había que tomar primero.** Toda la maquetación adaptativa vivía
dentro de `pdf_generator.py`. Al añadir tres PDF más, copiarla significaba que la
siguiente corrección de layout habría que aplicarla cuatro veces — y en algún
momento se olvidaría una. Ya hubo varias de esas correcciones: desbordes de ~20 pt,
huecos de ~250 pt, párrafos truncados que perdían justo la petición.

Se extrajo a `pdf_common.py`: tokens y **temas de marca** (navy de Sullivan / guinda
y oro de Loco, con sus tipografías), `blank_if_missing` y los formateadores,
`fit_text` / `wrap_text` / `draw_paragraph`, `scale_widths` / `auto_row_h` /
`center_block`, y las primitivas `draw_header_band`, `draw_section_title`,
`draw_kpi_cards`, `draw_horizontal_bars`, `draw_table`, `draw_note` y
`draw_empty_state`.

`pdf_generator.py` pasó de **1046 a 799 líneas** y ahora importa de ahí.

**Verificación de no-regresión.** Antes de tocar nada se tomó una línea base del PDF
mensual con una sonda propia (páginas, fragmentos de texto, rectángulos, rango
vertical, desbordes, dato ausente impreso). Después del refactor:

| Métrica | Antes | Después |
| :--- | :--- | :--- |
| Páginas | 8 | 8 |
| Fragmentos de texto | 323 | 323 |
| Rectángulos | 57 | 57 |
| Rango vertical | 23 .. 756 | 23 .. 756 |
| Desbordes de margen | 0 | 0 |
| Dato ausente impreso | ninguno | ninguno |

Idéntico en todo lo medible: el refactor no cambió una sola coordenada.

### M.2 Los tres PDF nuevos ✅

| Archivo | Páginas | Contenido |
| :--- | :---: | :--- |
| `Scripts/pdf_weekly_sullivan.py` (§I.2.4) | 5 | Portada · DTC por canal · Cuentas por cobrar con antigüedad y detalle de vencidos · Depletions por estado y distribuidor · Auditoría de no clasificados |
| `Scripts/pdf_sullivan_unified.py` | 7 | Portada con los dos periodos · Resumen ejecutivo de ambas cadencias + reconciliación · Mezcla de canales homologada · Cascada de 9 prioridades + glosario · Club Deep Dive + estados destino · Distribución y depletions · No clasificados de ambas cadencias |
| `Scripts/pdf_loco_tequila.py` (§I.3.4) | 7 | Portada · Inventario comercial vs. muestras · Ingreso por ruta al mercado · Depletions por territorio y mes · Mezcla de SKU y vendedores · Cuentas clave · **Brechas de dato declaradas** |

Decisiones de contenido que conviene tener presentes:

* **El unificado reutiliza, no reimplementa.** Importa `classify_orders`,
  `build_vista_a/b`, `build_geo` y `build_reconciliation` del mensual;
  `process_sullivan_weekly_data` del semanal; y `build_unified_channels` /
  `build_unified_unclassified` del dashboard unificado. La homologación de las dos
  taxonomías de canal vive en UN solo lugar y la usan el HTML y el PDF.
* **El mapa Albers no va en el PDF.** Su valor está en el tooltip por estado y por
  código postal, que en papel no existe. Se sustituye por la tabla de estados
  destino: la misma información sin la mitad que no funciona impresa.
* **Las series temporales no se reordenan.** La regla de barras descendentes aplica a
  rankings categóricos. Los meses de depletions de Loco van como tabla en orden de
  calendario, porque reordenarlos destruiría el eje.
* **El PDF de Loco dedica su última página a lo que NO puede afirmar**: margen bruto
  (no hay COGS por SKU), vendedor y canal estimados sin tabla de cuentas, Texas sin
  fecha de transacción, y las muestras fuera del inventario comercial. Un reporte es
  útil si sus límites son tan visibles como sus números.

**Conectados al orquestador:** los cuatro reportes responden a `--format all | html |
pdf`. En Loco y en el semanal los insumos se procesan **una vez** y se comparten entre
los dos entregables, en vez de leer los archivos crudos dos veces.

### M.3 Mini tutorial de datos para el cliente ✅

Nuevo `tutorial_datos_para_cliente.md`, bilingüe ES/EN, corto y accionable: qué
archivos entregar para cada reporte, cómo se llaman, dónde ponerlos, el comando
exacto, cómo saber que salió bien, y qué **no** se puede todavía con lo que falta
para desbloquearlo. Cierra con un resumen de una hoja.

Queda un cuerpo de documentación de datos en tres niveles, sin solaparse:

| Documento | Para quién | Qué responde |
| :--- | :--- | :--- |
| `tutorial_datos_para_cliente.md` | Cliente | Qué entrego y qué comando corro |
| `DATOS_REQUERIDOS.md` | Técnico / agente | Qué columna lee cada motor y por qué |
| `tutorial_para_cliente.md` | Cliente | Cómo leo el reporte ya generado |

### M.4 Verificación de la ronda

| Prueba | Resultado |
| :--- | :--- |
| PDF mensual antes/después del refactor | idéntico en páginas, texto, rectángulos y rango vertical |
| Los 4 PDF: desbordes de margen | 0 |
| Los 4 PDF: `nan`/`NaT`/`None` impreso | 0 |
| Páginas | mensual 8 · semanal 5 · unificado 7 · Loco 7 |
| Los 4 PDF con datos DEMO | generan |
| Los 4 PDF con datos REALES | generan |
| Loco real contra el libro del cliente | 220.65 / 198.23 / 22.42 exactos |
| Unificado real: reconciliación | `True`, diferencia $0.00 |
| Semanal real: Total DTC | $14,503.84 |
| Compilación de todos los scripts | OK |

**Nota metodológica sobre la sonda de PDF.** Extraer el texto de estos PDF tiene dos
trampas que costaron dos intentos fallidos:

1. La cadena `stream` aparece también dentro de `endstream`. Sin excluirla, los
   offsets se desalinean y se extraen **0 fragmentos de texto de un PDF que sí tiene
   texto** — un falso "todo limpio" que habría dado por buena cualquier fuga.
2. ReportLab **encadena** `/ASCII85Decode` + `/FlateDecode`, y las fuentes van
   embebidas como subset con un CMap propio, así que el texto no es ASCII: cada byte
   se traduce con el `beginbfchar` de su fuente.

Con las dos cosas resueltas la sonda extrae los 323 fragmentos del mensual y puede
afirmar de verdad que no se imprime ningún dato ausente.

### M.5 Sigue pendiente

- [ ] **I.4.x** Sttupa: no hay datos del cliente todavía, ni reales ni demo.
- [ ] **Mejoras no bloqueantes del semanal:** leer `SalesbyChannel` / `SalesbyClub` /
      `SalesbyTag` de la semana. Habilita una reconciliación exacta gratis y los
      importes reales de Events / Corporate / Friends & Family, que hoy salen en 0
      por falta de fuente, no por un error de cálculo.
- [ ] **Margen bruto de Loco:** requiere que el cliente aporte COGS por SKU. No se
      inventa.

---

## N. RONDA 2026-09-04 (3) — El paquete era rechazado al instalarse

**Síntoma reportado:** `Zip file contains path with invalid characters`.

**Causa.** El instalador de skills solo admite rutas de `[A-Za-z0-9._/-]`, y basta
UNA entrada fuera de ese juego para que rechace el paquete completo. El ZIP traía
10, todas de `Data_for_demo/`, heredadas de los nombres que entrega el cliente:
espacios en los 8 archivos de Loco y del semanal, más un apóstrofo
(`Open PO's demo 8.23.26.xlsx`) y corchetes y coma
(`YTD by Month [Bottles, Orders] demo.xlsx`).

Las verificaciones del empaquetador cubrían backslashes, rutas absolutas, `..`,
colisiones de capitalización y CRLF en `.sh` — pero no el juego de caracteres.

### N.1 Por qué no bastaba renombrar los archivos ✅

Los lectores localizaban sus insumos con patrones que **contienen los espacios
literalmente**: `_first_match(data_dir, "1 - Supplier - Inventory*.xlsx")`,
`"YTD by Month*.xlsx"`, la carpeta fija `"FB Depletion Reports 2026"`, y
`find_file("open po")` en el semanal. Renombrar solo el demo rompía el demo;
renombrar el patrón rompía los **datos reales del cliente**, que siguen llegando
con espacios y apóstrofos y no están bajo nuestro control.

La solución es que un mismo criterio reconozca los dos nombres:

* `_flexible_pattern` (`loco_tequila_us_relationships.py`): traduce el glob a una
  regex donde cada tramo no alfanumérico vale `[^A-Za-z0-9]*`. Así
  `1 - Supplier - Inventory*.xlsx` reconoce el nombre real y
  `1-Supplier-Inventory-demo.xlsx`. Se aplica como **segunda pasada**: el glob
  literal sigue teniendo prioridad, así que el comportamiento con datos reales no
  cambia.
* `_find_fb_depletion_folder`: busca la subcarpeta por prefijo normalizado
  (`fbdepletionreports`) y no por nombre exacto. De paso deja de fijar el año
  2026, que en 2027 habría devuelto `None` en silencio.
* `find_file` (`Scripts/sullivan_weekly_processor.py`): compara también la forma
  sin puntuación, de modo que `open po` reconoce `Open PO's 8.23.26.xlsx` y
  `Open-POs-demo-8.23.26.xlsx`.
* `_parse_fb_depletion_filename_date`: el separador del patrón `MMDDYY` acepta
  `[\s_-]`. Sin esto, un nombre portable perdía la fecha y caía al primer
  candidato de la carpeta **sin avisar**.

### N.2 Nombres portables del demo ✅

`Scripts/make_demo_data.py` los emite ya con guiones:

| Antes | Ahora |
| :--- | :--- |
| `Open PO's demo 8.23.26.xlsx` | `Open-POs-demo-8.23.26.xlsx` |
| `Idig Depletions demo 8.26.xlsx` | `Idig-Depletions-demo-8.26.xlsx` |
| `1 - Supplier - Inventory demo.xlsx` | `1-Supplier-Inventory-demo.xlsx` |
| `Inventory History demo.xlsx` | `Inventory-History-demo.xlsx` |
| `YTD by Month [Bottles, Orders] demo.xlsx` | `YTD-by-Month-Bottles-Orders-demo.xlsx` |
| `InventoryByLocation demo.csv` | `InventoryByLocation-demo.csv` |
| `SalesOrdersSummary demo.csv` | `SalesOrdersSummary-demo.csv` |
| `orders_export_1 demo shopify.csv` | `orders_export_1-demo-shopify.csv` |
| `orders_export_1 demo memory.csv` | `orders_export_1-demo-memory.csv` |
| `FB Depletion Reports 2026/1 - Depletion - By Month - 2026-08-24.xlsx` | `FB-Depletion-Reports-2026/1-Depletion-By-Month-2026-08-24.xlsx` |

Los datos del cliente en `Client_Data/` **no se tocaron**: no viajan en el paquete
y sus nombres son los que el cliente exporta.

### N.3 La barrera, para que no vuelva a salir de aquí ✅

`package_skill.ps1` y `package_skill.sh` revientan si alguna entrada del ZIP tiene
un carácter fuera de `[A-Za-z0-9._/-]`, con la lista de las culpables. Se probó
con nombres sintéticos que el guardia **sí falla** cuando debe: rechaza
`Open PO's demo.xlsx` y `YTD [Bottles, Orders].xlsx`, y acepta
`ok_file-1.py` y `EBGaramond-Regular.ttf`. Un guardia que nunca falla no prueba
nada.

### N.4 Verificación de la ronda

| Prueba | Resultado |
| :--- | :--- |
| Rutas del ZIP con caracteres inválidos | **0** (antes 10) |
| El guardia rechaza nombres malos / acepta buenos | 2 de 2 · 2 de 2, en ambos empaquetadores |
| Loco con datos **reales** (nombres con espacios) | `220.65` · CA `198.23` · TX `22.42` exactos |
| Semanal con datos **reales** (`Open PO's ...`) | Total DTC `$14,503.84`, depletions `13.58` cs |
| Loco con datos demo renombrados | `169.27` (CA `147.27` · TX `22.00`) + `7.00` no vendible |
| Semanal con datos demo renombrados | `$9,148.13`, efectivo `$7,840.00`, `13.4` cs |
| Compilación de todos los scripts | OK |
| Los 8 entregables desde el paquete extraído sin datos de cliente | generan, mismos tamaños que la ronda anterior |
| Paquete | 108 entradas · 7.99 MB · 0 archivos de cliente |

**Nota de proceso.** Al probar generé en `Output_check`, y el paquete saltó de 108
a 116 entradas: la exclusión va por nombre **exacto** de carpeta, así que solo
`Output` está excluida y mis 8 entregables se empaquetaron. Quedó anotado en
`AGENTS.md`; al probar hay que generar en `Output`.

---

## O. RONDA 2026-09-04 (4) — Reportes bilingües y selector de semana

Dos peticiones: que la skill y sus reportes funcionen en español o inglés, y que
el filtro de semana del semanal sirva cuando haya más datos.

### O.1 Decisiones del usuario

| Pregunta | Decisión |
| :--- | :--- |
| Forma del HTML bilingüe | **Un solo archivo con selector ES/EN**. Los dos idiomas viajan dentro; no hay riesgo de mandar la versión equivocada. |
| ¿Se traduce la taxonomía? | **No.** Interfaz en el idioma elegido, taxonomía en inglés. |
| Prioridad | **Primero** que la skill misma opere en el idioma del usuario. |

### O.2 Protocolo de primer turno ✅ (`SKILL.md` §0, `AGENTS.md` §0)

Regla inmutable: **nunca** preguntar solo la marca. Si el usuario escribió en
inglés, se fija `en` y se pregunta la marca en inglés; si escribió en español,
saludó o solo invocó la skill, el primer mensaje pregunta **idioma y marca a la
vez**, en formato bilingüe. La redacción literal de las dos bifurcaciones queda
en `SKILL.md` §0 para que no se improvise.

El idioma gobierna **dos cosas distintas**: la conversación y los entregables
(vía `--lang es|en`).

### O.3 El filtro de semana no estaba limitado por falta de datos ✅

El diagnóstico real es peor que "falta información":

* `generate_report.py` tenía la ruta semanal **fija** en
  `Client_Data/Sullivan_data/Weekly/Week_2026_08_23`. Con diez semanas en la
  carpeta, el reporte solo habría leído esa.
* El dashboard traía `<select><option>{week_label}</option></select>`: **una
  opción fija y ningún manejador**. El filtro se veía pero no filtraba.
* La línea de tendencia dibujaba **un punto real y tres puntos gris de relleno**
  rotulados "Wk 2/3/4", con el eje fijo en `max = 20000`.
* El KPI "WoW % Change" estaba escrito a mano como `—`.
* El KPI "Cash Received" mostraba `—` **aunque el valor sí se calculaba**: el
  PDF y el unificado lo pintaban, el semanal no. Los entregables se
  contradecían entre sí.
* Las pastillas decían "Live (5 of 7 reporting states)" y "Live (1 of 2
  distributors)" escritas a mano, que dejarían de ser verdad al cambiar un feed.

Lo que se hizo:

| Pieza | Cambio |
| :--- | :--- |
| `discover_week_dirs` | Acepta que la ruta **sea** una semana o que las **contenga**. Una carpeta califica si trae los 4 insumos. |
| `process_sullivan_weekly_series` | Procesa todas y devuelve la serie ordenada. Una semana mal formada se avisa y se omite; no tumba a las demás. |
| `attach_wow` | WoW contra la semana inmediata anterior. La primera queda en `None`, **no en 0.0%**: no hay con qué comparar, y un cero afirmaría que no cambió. |
| Dashboard semanal | Selector real que repinta el tablero completo; tendencia sobre la serie con eje derivado del máximo; WoW, efectivo y pastillas derivados del dato. |
| Dashboard unificado | Selector propio. La homologación de canales se precalcula **por semana en Python**, para que siga viviendo en un solo lugar y la usen HTML y PDF. |
| PDF semanal | Documenta la más reciente y añade **página de tendencia** de toda la serie. 5 páginas con una semana, 6 con varias. |
| Datos demo | `WEEKLY_SERIES`: 4 semanas con escalas distintas y **no monótonas** (la del 8/16 baja 13.8%), porque con una subida constante no se distinguiría un WoW bien calculado de uno que siempre da positivo. La última va en escala 1.00 para reproducir exacto las cifras ya verificadas. |

**Un defecto que encontró la propia prueba.** Al cambiar de semana,
`renderExec` volvía a pintar la mezcla en cadencia mensual: el lector que estaba
viendo la semanal perdía su selección sin haber pedido nada. Ahora la cadencia
se recuerda.

### O.4 Traducción de los ocho entregables ✅ (`Scripts/i18n.py`)

**Un solo diccionario** para los 4 HTML y los 4 PDF. Ocho listas separadas
garantizan que a la tercera corrección alguna quede desincronizada y el cliente
reciba un reporte medio traducido.

Dos mecanismos, porque hay dos clases de texto:

1. **Pares exactos** para etiquetas completas ("Total DTC Sales").
2. **Fragmentos** para lo que se compone con datos dentro: `"$2,756 · 30% of
   weekly DTC volume"` no cabe en una tabla porque el importe cambia en cada
   corrida. Se aplican de más largo a más corto.

**Bidireccional a propósito.** Se descubrió midiendo que el tablero de Loco
Tequila ya tenía **12 nodos visibles en español** mientras los tres de Sullivan
estaban íntegros en inglés: hoy los entregables eran inconsistentes entre sí.
Traducir en un solo sentido habría dejado párrafos en español dentro de un
reporte en inglés.

**Cómo se aplica, y por qué así.** En el HTML, sobre el DOM **ya renderizado**,
no con una clave `data-i18n` en cada nodo de las cuatro plantillas. Dos razones:
buena parte de las etiquetas las concatena el JS en tiempo de ejecución (tablas,
tooltips, notas con cifras), y un atributo en la plantilla no las alcanza;
y cuatro plantillas de 900 a 2000 líneas con más de 300 etiquetas se habrían
tenido que instrumentar a mano una por una, donde cada nodo omitido sería un
texto en inglés que nadie nota. Un `MutationObserver` traduce lo que se pinte
después, así que los repintados (cambiar de semana, de cadencia, de pestaña)
salen ya en el idioma elegido sin que los generadores llamen a nada.

En los PDF, en la capa de dibujo compartida: en `fit_text`/`wrap_text` **antes
de medir** —el español es 15–25% más largo y calcular el recorte sobre el
original desbordaría la columna— y en el canvas, para las 52 llamadas directas a
`drawString` de portadas y pies.

**Cuatro trampas que había que resolver, y se resolvieron midiendo:**

* **Fragmentos cortos dentro de datos.** `"vs"` → `"contra"` convertía el
  apellido "Elvsborg" en "Elcontrasborg". Los fragmentos de una palabra corta se
  aplican con frontera de palabra.
* **Idempotencia.** Como los PDF traducen dos veces, `t(t(x))` tiene que dar
  `t(x)`. La prueba sobre 947 cadenas encontró **3 roturas reales**: mis propias
  traducciones al español conservaban dentro una palabra que también era
  fragmento en inglés (`"... California vs Texas"`, `"Jan–Aug ..."`,
  `"... paleta Maroon ("`). Corregidas en el lado español, no quitando el
  fragmento: "vs" y los meses **sí** deben traducirse cuando van solos.
* **Mayúsculas.** Las tarjetas de KPI y los encabezados suben el texto a
  mayúsculas, así que "TOTAL DTC SALES" no coincidía con ninguna clave. Se
  traduce antes de subir, y además la búsqueda es insensible a mayúsculas
  conservando el estilo del original.
* **`"Live feed"` → `"En vivo feed"`.** El fragmento corto se aplicaba dentro de
  la frase larga. Se resolvió añadiendo el par específico: los fragmentos van de
  más largo a más corto justamente para que el específico gane al genérico.

**Lo que no se traduce está garantizado por construcción:** la taxonomía no
figura en `i18n.py`. Lo que no está, no se toca. Hay una prueba que lo verifica
sobre las 46 cadenas congeladas, en los dos idiomas.

**Cobertura, medida y no supuesta.** El punto débil del enfoque es que una
etiqueta ausente del diccionario se queda en inglés **sin avisar**. Se convirtió
en un número: para el HTML se volcó todo el texto que los tableros llegan a
pintar (ejecutándolos en un DOM simulado, porque buena parte no está en el
archivo) y para los PDF se instrumentó `i18n.t` durante una generación real.
Resultado: **321 de 382** cadenas visibles del HTML cubiertas —las 5 restantes
son datos— y **177** cadenas cubiertas en la capa de dibujo de los PDF, partiendo
de 84.

### O.5 Dos fugas de presentación que salieron de medir

Buscando etiquetas sin traducir aparecieron dos violaciones de la regla de
"Presentación Ejecutiva Limpia", que llevaban tiempo ahí:

1. El PDF mensual titulaba una sección visible al cliente
   **"Final Checklist (Sullivan_data_guide.md)"**, nombrando un archivo interno
   de especificación.
2. Su anexo remitía al cliente a **`sullivan_c7_simulator.py`**, y la nota de
   fuente de datos imprimía el mismo nombre de script.

Corregidas conservando el hecho técnico y quitando la ruta: el cliente necesita
saber si la fuente es simulada o real, no con qué archivo del repo se generó.

### O.6 Una regresión que introduje y cómo se detectó

Al añadir la tabla de tendencia al final de la página de canales del PDF
semanal, la hoja se desbordó hasta **y = −90** (el límite es 61.2). La sonda lo
marcó como 5 bloques fuera de márgenes.

Rastreando la coordenada Y bloque por bloque se vio la causa exacta: la tabla de
canales ya terminaba en y=80.8, así que el título, la tabla y las dos notas no
tenían dónde caber. **La regresión era idéntica en inglés y en español**, lo que
descartó que fuera la traducción.

Apretarla más habría dejado barras de 15 pt y notas cortadas. La serie de varias
semanas es un tema distinto del mix de esta semana, así que se movió a su propia
página, con sus propios KPIs (mejor semana, más débil, promedio). Rango vertical
de vuelta a `23 .. 756`.

### O.7 Verificación de la ronda

| Prueba | Resultado |
| :--- | :--- |
| Compilación de los 16 scripts, sin warnings | OK |
| Los 8 entregables × 2 idiomas | 16 archivos, sin error |
| Los 4 PDF × 2 idiomas: desbordes de margen | **0** |
| Los 4 PDF × 2 idiomas: dato ausente impreso | **ninguno** |
| Los 4 PDF: rango vertical | `23 .. 756` **idéntico en los dos idiomas** |
| Páginas | mensual 8 · semanal 6 (4 semanas) · unificado 7 · Loco 7 |
| Idempotencia de traducir, 947 cadenas × 2 sentidos | 0 roturas |
| Taxonomía alterada (46 cadenas × 2 idiomas) | **0** |
| Selector ES/EN en los 4 HTML × 2 idiomas | 17 de 17 etiquetas traducidas · 14 de 14 datos y taxonomía intactos |
| Selector de semana, semanal | 4 opciones · manejador vivo · 0 desajustes entre lo pintado y el dato · 4 valores distintos |
| Selector de semana, unificado | 4 opciones · 4 de 4 firmas de mezcla distintas · cadencia preservada |
| Errores de ejecución en el DOM | **0** en los cuatro tableros |
| Orden descendente en los 8 payloads | 0 violaciones |
| Rutas internas en los 8 HTML | **ninguna** |
| Datos REALES: mensual | `Reconciliación al centavo: True`, diferencia `$0.00`, `$461,362.44` |
| Datos REALES: semanal | Total DTC `$14,503.84` · depletions `13.58` cs |
| Datos REALES: Loco | `220.65` · CA `198.23` · TX `22.42` exactos |

**Nota metodológica: tres falsos negativos de mis propias herramientas.**
Conviene dejarlos escritos porque cada uno habría hecho pasar una prueba vacía:

1. El medidor de cobertura contaba como "sin traducir" el texto que **ya estaba**
   en el idioma destino —el caso real del tablero de Loco—. Corregido para ser
   consciente de la dirección.
2. El verificador del unificado ejecutaba **solo el último `<script>`** del HTML.
   Al inyectar el selector de idioma al final del body, ese último dejó de ser el
   del tablero: la prueba reportaba 0 semanas y 0 series sin que hubiera nada
   roto. Ahora ejecuta todos, en orden, como el navegador.
3. El mismo verificador no definía `NodeFilter` ni `createTreeWalker`, así que el
   snippet de idioma tomaba su camino de respaldo en vez del que corre de verdad.
   Alineado con el navegador. De paso se añadió ese respaldo al producto: sin él,
   un entorno sin `TreeWalker` dejaría el selector inerte **y en silencio**.

Y una condición preexistente que conviene tener presente: el tablero semanal y
el de Loco cargan sus tipografías con `@import` de Google Fonts (4 apariciones
entre los ocho archivos). No bloquea el reporte —hay pila de respaldo— pero
significa que sin red esos dos no se ven con la tipografía de marca, a diferencia
del mensual y el unificado, que la llevan embebida en base64.

### O.8 Sigue pendiente

- [ ] **I.4.x** Sttupa: sin datos del cliente, ni reales ni demo.
- [ ] **Mejoras no bloqueantes del semanal:** leer `SalesbyChannel` /
      `SalesbyClub` / `SalesbyTag` de la semana. Habilita una reconciliación
      exacta gratis y los importes reales de Events / Corporate /
      Friends & Family, que hoy salen en 0 por falta de fuente.
- [ ] **Margen bruto de Loco:** requiere COGS por SKU del cliente. No se inventa.
- [ ] **Efectivo por región (panel 3 del semanal):** hoy declara "en espera del
      feed", pero el archivo de Open PO's **sí trae** columna `Market` y las
      facturas PAID traen `Total`. El desglose por región es derivable de lo que
      ya hay; queda anotado porque es una función nueva, no un arreglo.

---

## P. RONDA 2026-09-14 — Notas del cliente, portabilidad a Cowork, absorción del sistema del cliente y libro de Excel con dinámicas

> Entraron tres cosas a la vez y se planean juntas porque tocan el mismo reporte:
> las notas del cliente sobre Loco, la carpeta con **su propio** sistema de
> reportes, y un cuarto entregable en Excel para **los cuatro reportes que ya
> teníamos**.
>
> **Estado real (actualizado el mismo 2026-09-14, tras implementar):** las tres
> quejas de `notas_del_cliente.md` y el libro de Excel de referencia para
> **Loco** están **hechos, verificados con datos reales y con Excel de
> verdad**. El resto del plan de esta sección (Cowork/superficies, absorción
> del sistema del cliente, empaquetado, y el libro de Excel para los tres
> reportes de Sullivan) sigue en **PLAN**, con sus asignaciones a cada modelo
> en §P.8 sin tocar. Ver §P.12 para el detalle de lo entregado.

### P.1 Las cuatro preguntas y sus respuestas

**1. ¿Se puede volver skill el sistema del cliente?** Sí, pero **no conviene
replicar su Excel**. El 40% de su código (`final_report.py`, 1,305 de 3,271 líneas)
manipula coordenadas de celda con openpyxl sobre un libro **cuyo formato solo existe
dentro de los propios `.xlsx` de `outputs/`**: no hay plantilla versionada. Cada
semana copia el libro de la semana pasada y sobrescribe celdas. Decisión del
usuario: **absorber las reglas, no el libro.**

**2. ¿Chat o Cowork? ¿Ambas?** Un solo ZIP cubre **las dos**: comparten el registro
de skills de claude.ai. Lo que no sincroniza es entre *superficies*: claude.ai,
Claude Code (filesystem) y la API son tres registros independientes, cada uno con
su propia subida. En claude.ai las skills personalizadas son **por usuario, no por
organización** — no hay administración central.

**3. ¿Se pueden adaptar a Cowork para "solo señalar la carpeta"?** Sí, y es el
modelo nativo de **Cowork de escritorio**: el usuario elige una carpeta real y esa
carpeta es el directorio de trabajo. **Cowork en la nube no ve carpetas locales**,
solo conectores. Chat no tiene carpeta: archivos subidos a la conversación.

**4. Libro de Excel con dinámicas** como segunda validación de los cuatro reportes
(ver §P.6).

### P.2 Restricciones del entorno de skills (verificadas, no supuestas)

| Restricción | Dato | Consecuencia |
| :--- | :--- | :--- |
| Subida | **30 MB sin comprimir** | Hoy vamos en **19.99 MB** — 67% gastado antes de añadir nada |
| Red | **Nula** en la API; total, parcial o nula en claude.ai según ajustes | Los dos `@import` de Google Fonts fallan **en silencio** |
| Paquetes | Sin `pip install` en ejecución | Solo lo preinstalado |
| Preinstalado | pandas, numpy, scipy, matplotlib, seaborn, openpyxl, xlsxwriter, xlrd, pillow, **reportlab[pycairo]**, pypdf, pdfplumber | Cubre nuestra pila completa |
| Runtime | **Linux, sensible a mayúsculas**; 5 GiB RAM, 5 GiB disco | Ya contemplado por los empaquetadores |
| Frontmatter | Requeridos solo `name` + `description`; nombre ≤64 car., minúsculas/dígitos/guiones, **sin las palabras "anthropic" ni "claude"**; descripción ≤1024 car. | Nuestro nombre es válido. La descripción **no**: ver P.3 defecto 10 |

`requirements.txt` pide `cairosvg>=2.7.0`, que necesita `libcairo.so.2` del sistema,
**pero nunca se importa**: `Scripts/pdf_common.py:616-630` solo lee PNG ya
rasterizados y devuelve `None` si faltan. Línea muerta; quitarla deja las cinco
dependencias instalables puras de wheel.

### P.3 Defectos encontrados — el orden importa, estos van antes que cualquier feature

| # | Defecto | Evidencia | Severidad |
| :--- | :--- | :--- | :--- |
| 1 | **Dos bloques del tablero de Loco pintan datos inventados.** Cadencia de cuentas y rejilla de sparklines son arreglos literales en la plantilla, no derivados de `LOCO_DATA`: `Melrose Gas (DTC)`, `Lahontan`, `daysSince:614`, `Brasswood Bar + Kitchen`, `meta:'Jacky · CA · On Premise'` | `loco_dashboard_generator.py:1048-1057`, `:1117-1124` | **Crítica** |
| 2 | **Los 8 chips de "fuente" mienten.** Citan rangos de celda del libro manual del cliente (`Monthly Summary rows 3 & 9`, `YTD Summary A2:J13`, `Inventory A3:D10`), no los archivos que el procesador lee | `:463`, `:486`, `:509`, `:535`, `:558`, `:575`, `:591`, `:613` | **Alta** |
| 3 | **El leaderboard lo domina un "Unknown".** Corrida real: `Unknown (no map match)` **1488 botellas** contra Mark 24, Joe Pat 15, Jacky 14, Manuel 12. CA, el territorio más grande, no tiene atribución porque su único feed (`YTD by Month`) trae cuenta pero no vendedor. Cuatro cadenas "Unknown" distintas, una con mensaje engañoso: dice "no map match" cuando la causa es "no se suministró mapa" | `loco_tequila_us_relationships.py:687-694`, `:697-702`, `:624-628`, `:98-108` | **Alta** |
| 4 | **Número sin redondear** (la queja literal del cliente). `num(m.bottles) / 12` impreso crudo: 532/12 → `44.333333333333336`. Todas las demás gráficas sí se protegen | `:750`, impreso en `:774` y `:780` | Media |
| 5 | **Tres bugs de tipografía con fallo silencioso.** `Inter` y `Fraunces` **no existen en el repo**: los `@import` son su única fuente. Y el unificado declara `Poppins` pero `font_face_css()` solo emite EB Garamond | `dashboard_weekly_sullivan.py:94`, `loco_dashboard_generator.py:55`, `dashboard_sullivan_unified.py:235` vs `:1428` | Media |
| 6 | **Split de DTC en el eje equivocado.** El cliente pidió Shopify vs Memory; el código agrupa "Shopify sin tag" vs "con tag o Memory", así que Shopify etiquetado cae en el bucket de Memory | `relationships:506-507` | Media |
| 7 | **El semanal de CA está mal formado**: escribe `ytd_bottles` —columna **acumulada**— en la semana de `invoice_date` | `:546` | Media |
| 8 | **Riesgo latente de conversión a 9L.** La ruta de **inventario** convierte bien por volumen (200/9000 = 1/45; 24×200/9000 = 0.5333, idéntico al factor del cliente). La de **depletions** fija 750 mL y el JS divide entre 12 a secas. Hoy inocuo —el feed de CA solo trae 750 ML, verificado: tres `Item Names` únicos— pero el día que se deplete un 200 mL la cifra sale **3.75× inflada** | `:162`, `:484`, `:490` + `loco_dashboard_generator.py:750` | Latente |
| 9 | **El empaquetador reventaría hoy.** `references_to_delete/` (325 archivos, 109 MB, **295 rutas con espacios y apóstrofos**) no está excluido. Y la rama de respaldo con `zip` nativo **no corre ninguna de las 4 validaciones de portabilidad**, solo la de tamaño | `package_skill.ps1:48-61`, `package_skill.sh:81-94`, `:178-200` | **Bloqueante** |
| 10 | **La descripción de la skill está entera en español** (~430 de 1024 caracteres). Es contra lo que Claude compara la petición para decidir si activa la skill: con un prompt en inglés **puede no dispararse, y el fallo es silencioso** | `SKILL.md:1-4` | Media |
| 11 | **Los tres resolvedores de carpeta divergen.** `resolve_data_dir` tiene tres sitios de llamada con tres comportamientos, y el del mensual **invierte la precedencia** (demo antes que datos de cliente) | `generate_report.py:68-94` vs `:321`, `:571`, `:590-614`, `:616-634` | Media |
| 12 | **17 enlaces `file:///e:/Users/1167486/...` muertos** en la tabla de arquitectura, que además filtran un nombre de usuario. Y los comandos de Conda no existen en el sandbox | `SKILL.md:251-269`, `:173`; `README.md:92`; `AGENTS.md:134,146,150` | Baja |
| 13 | **Las 8 menciones de "Cowork" en el repo hablan de una unidad de red** (`Z:\Cowork\...`, `\\servidor\cowork\...`), **no del producto Claude Cowork**. Un agente corriendo en Cowork lee eso y se va a buscar una unidad que no existe | `SKILL.md:124,150,158,163`; `AGENTS.md:68,73,104`; `tutorial_datos_para_cliente.md:61,62,68,79` | Media |
| 14 | `dashboard_generator.py:91` **escribe** el caché `zcta_centroids.csv` al lado del script. El directorio de instalación puede ser de solo lectura en el sandbox | `:91` | Baja |

### P.4 Lo que el sistema del cliente nos resuelve gratis

El hallazgo que reordena el plan: **el sistema del cliente contiene las respuestas a
sus propias quejas.**

- **Margen bruto — cierra §O.8.** Sus `docs/RULES.md` §3 traen las tasas por botella:
  FOB Blanco 33.17 · Ámbar 46.00 · Puro Corazón 70.83; DTR Blanco 51.50 · Ámbar
  80.50 · Puro Corazón 144.50 · Alebrije 379.33 · Mantarraya 642.06 · VAP Blanco
  62.50 · **Aureo con dos tasas según canal** (614.50 mayoreo Park Street / 864.50
  DTC Melrose-BML). Ya no se inventa nada: es dato del cliente.
- **Mapa de cuentas — cierra §I.3.2.** Sus hojas `Accounts H1-2026` / `Accounts
  H2-2026` traen `Salesperson` y `Channel` por cuenta. La bandera `--account-map`
  está cableada desde septiembre y **simplemente nunca se suministró**.
- **Reglas de unidad**: ×6 para equivalentes de caja 4.5L (SGWS y ACS), Park Street
  según su columna `Unit`, Favorite Brands ya en botellas, ÷12 a cajas 9L **excepto
  200 mL ÷45**.
- **Regla de no atribuidos de TX**: sin match → Joe Pat Clayton / Off Premise, único
  rep de Texas. Y una exclusión: **nunca** leer el campo "Sales Rep" de ACS.
- **Definición de orden** (§9): CA = par (cuenta, fecha) · TX = par (cuenta, semana)
  con incremento · DTC = order id distinto. Habilita el conteo YTD de órdenes.
- **~20 alias y 6 consolidaciones de cadena** aprobadas, más `TOTAL WINE*` → Sara.

Y **datos ya parseados que hoy se tiran**, que es de donde salen casi todas las
pestañas pedidas sin trabajo de parseo nuevo:

| Se parsea en | Se descarta en | Habilita |
| :--- | :--- | :--- |
| `relationships:246` columna `SALES REP` de FB | nunca se usa | Atribuir Texas **sin mapa del cliente** |
| `:245`, `:493` columna `PREMISE` de FB | no llega a `build_accounts_summary` | On/Off Premise **autoritativo** en vez de adivinar por nombre |
| `:431-434` 4 columnas por bodega (SGWS SoCal/NorCal, Park St CA, FB TX) | `loco_data_processor.py:160-169` | La pestaña de inventario por SKU y bodega, **pura reexposición** |
| `:240-257`, `:308-320` rejillas por mes y por cuenta | solo se agregan a totales | Las pestañas Signature y Favorite Brands |
| `:373` columna `source` | se reagrupa mal | Split real Shopify vs Memory |

Más un activo sin explotar: `Client_Data/Loco_tequila_usa_data/FB Depletion Reports
2026/` tiene **119 snapshots semanales** y solo se lee el más reciente
(`find_latest_fb_depletion_file:211-221`). Diferenciar snapshots acumulados
consecutivos es la **única fuente honesta** de un semanal real en Texas.

### P.5 Presupuesto de 30 MB — recortar, no partir la skill

Partirla en dos es la respuesta equivocada: los reportes comparten `pdf_common.py`,
`i18n.py`, `chart.umd.min.js` y todo el toolkit de PDF, así que duplicaría ~1.7 MB
de código y **triplicaría la carga de instalación** (tres superficies × dos skills)
sin ganar nada.

| Acción | Ahorro medido |
| :--- | ---: |
| `Imagenes_iconos/Loco_Tequila_Logo.svg` + `_white.svg` — **no los referencia ningún código**; se usa el PNG de 16 KB | **4.18 MB** |
| `Data_for_demo/sullivan_dashboard_test.html` — artefacto generado | **3.38 MB** |
| Fuentes: conservar los 10 archivos que se usan, borrar el resto | **6.32 MB** |
| `.pptx` de ventas, `sullivan_report_test.pdf`, maquetas superadas, `to_do.md` | ~0.5 MB |
| **Total → paquete de ~5.6 MB (19% del presupuesto)** | **~14.4 MB** |

El recorte de fuentes está **de-riesgado con medición**, no estimado: los PDF
registran exactamente **cuatro** TTF (`pdf_common.py:89-90,103-104`) y el tablero
embebe **cinco** faces (`dashboard_generator.py:813-833`). Esos diez archivos son
3.06 MB de los 9.38 MB actuales.

### P.6 El libro de Excel con dinámicas — los cuatro reportes

Aplica a **Sullivan mensual, semanal, unificado y Loco**, no a uno. Hay ~23 gráficas
a replicar (mensual 2 + mapa Albers + 6 tablas · semanal 5 · unificado 6 paneles ·
Loco 10).

**Dos hechos medidos que fuerzan la arquitectura:**

1. **Los ocho libros que el cliente genera hoy no tienen ni una dinámica ni una
   gráfica nativa** — cero partes `pivotTable`, cero `chart`, verificado inspeccionando
   el interior de cada `.xlsx`. No están pidiendo una réplica: piden algo que su
   proceso no les da.
2. **openpyxl no puede crear tablas dinámicas.** Su documentación es explícita:
   *"it is not intended that client code should be able to create pivot tables"*.
   `add_pivot()` existe pero solo hace `append`; `TableDefinition` tiene 87
   parámetros opcionales. `xlsxwriter` no las soporta en absoluto. Lo que **sí**
   puede openpyxl es **editar** las existentes: cambiar rango de origen y poner
   `refreshOnLoad`.

**Diseño resultante:** plantillas versionadas en `Templates/`, autorizadas **una
sola vez** por COM (`win32com` disponible en esta máquina, Excel en
`C:\Program Files\Microsoft Office\Root\Office16\EXCEL.EXE`), y un escritor de
runtime con openpyxl que solo rellena datos y ajusta rangos — **sin Excel, sin COM,
sin red**, así que corre igual en el sandbox.

> No contradice la decisión de §P.1. Lo rechazado fue heredar *su* layout de 9 hojas
> indocumentado. Estas plantillas son **nuestras**: sin datos, generadas por script,
> versionadas, de decenas de KB.

**Nombres de hoja en inglés y fijos**, con título bilingüe *dentro* de la hoja: las
referencias del caché van por nombre de hoja, así que traducirlos obligaría a dos
plantillas por idioma. Excel además limita a 31 caracteres y prohíbe `: \ / ? * [ ]`.

**La segunda validación, hecha de verdad.** El modo de fallo por omisión aquí es
entregar un libro que **se ve vacío** porque openpyxl no escribe los registros del
caché. La solución convierte el defecto en la función pedida: cada hoja lleva **dos
cálculos independientes del mismo número** — la cruzada estática que calculamos
nosotros (visible siempre) y la dinámica que **Excel** repobla desde el dataset
crudo al abrir. Tienen que coincidir, y la diferencia la calcula Excel con fórmulas,
no nosotros.

**Y en Sullivan mensual esto vale más que replicar gráficas.** El reporte cuelga de
una sola afirmación: el cuadre al centavo contra el `FinancialReport` (§B.1, §B.2).
En el libro, **Excel re-deriva el Total DTC** agregando `Product SubTotal` desde el
dataset crudo y lo compara contra el `SubTotal` financiero. Si no da `$0.00`, o la
cascada de 9 categorías está mal o la reconciliación está mal. Es una re-derivación
independiente del número del que depende todo — y no se había pedido.

**Beneficio colateral:** la hoja `Dataset` permite pivotear sobre `Unclassified
Reason` (Sullivan) y `attribution_rule` (Loco). En Loco responde la pregunta 2 del
cliente; en Sullivan es justo lo que **§A** necesita — las 8 órdenes de Club sin
programa llevan desde agosto esperando una decisión que nadie podía tomar sin ver
los renglones.

**Tres trampas de modelado que hay que respetar:**

1. **Saldo contra flujo.** Inventario es saldo puntual; depletions y ventas son
   flujo. No comparten tabla de hechos sin riesgo de doble conteo.
2. **La cascada de 9 categorías es excluyente y ordenada.** Como dinámica pierde la
   semántica a menos que `priority` y `Unclassified Reason` viajen como columnas.
3. **Las series de tiempo no se ordenan descendente.** La regla de oro aplica a
   barras categóricas; §J.3 ya documenta esta trampa: ordenar una serie temporal
   destruye el eje.

El mapa Albers con puntos por ZIP **no tiene equivalente** que openpyxl pueda crear.
Se degrada a dinámica por estado más tabla por ZIP, y se declara como degradación.

**Atajo de autoría:** el unificado ya fusiona mensual y semanal, así que autorizar
su plantilla y la de Loco cubre casi todo; mensual y semanal reutilizan después esas
definiciones. Cuatro plantillas, dos esfuerzos.

### P.7 Fases

- [ ] **Fase 0 — Desbloquear el empaquetado** (defecto 9 y §P.5). Excluir
      `references_to_delete/` en las tres rutas, **eliminar la rama de `zip` nativo**
      y fallar duro pidiendo `python3` (un solo camino, un solo conjunto de
      garantías), compuerta de 30 MB de advertencia a error, aviso a los 24 MB,
      compuerta de hash entre `SKILL.md` y la copia de `.agents/`, soporte de globs
      en exclusiones, y el recorte medido.
- [ ] **Fase 1 — Los defectos** (1, 4, 5, 6, 7, 8). Borrar los bloques inventados el
      **primer día**; mover la conversión a 9L a Python y un formateador central —
      arregla el redondeo **y** blinda el 200 mL de un golpe, porque JS no puede
      aplicar una excepción por SKU sobre un agregado ya sumado; tipografía offline.
- [ ] **Fase 2 — Las reglas del cliente como dato.** `Config/loco_tequila_us/` con
      6 CSV declarativos (tasas de margen, conversiones, mapa de cuentas, alias,
      cadenas, roster, overrides), **fuera de `Client_Data/`** porque esa carpeta es
      confidencial y los lectores la recorren con glob. Más la **escalera de
      atribución** (R0 exclusión ACS → R1 `SALES REP` de FB → R2 mapa normalizado →
      R3 alias → R4 tag de orden DTC → R5 default TX → R6 desconocido con motivo),
      con el invariante `suma por rung == total de botellas`.
- [ ] **Fase 3 — Las 6 pestañas y la trazabilidad.** De 8 bloques apilados a 8
      pestañas con el patrón ya probado del unificado
      (`dashboard_sullivan_unified.py:271-293`, `:1211-1241`, `:410`). La pestaña de
      fuentes se modela sobre `renderRecon` (`:1128-1205`), que ya resolvió bien este
      problema. Activar margen y retirar las declaraciones de brecha de los 7
      documentos donde están.
- [ ] **Fase 3b — El libro de Excel** (§P.6). `--format xlsx`; pasamos de 8 a **12**
      entregables por idioma.
- [ ] **Fase 4 — Cowork, superficies y PDF.** `Scripts/input_discovery.py` con tabla
      declarativa de huellas y doble pasada (nombre primero, encabezados solo para lo
      ambiguo) más `--dry-run`; política de carpeta de salida en 4 niveles con sonda
      de escritura; unificar los tres resolvedores (defecto 11); frontmatter bilingüe
      (defecto 10); sección de detección de superficie; limpiar defectos 12, 13, 14.

### P.8 Reparto entre modelos

Criterio: **DeepSeek** (vía OpenCode, `AGENTS.md` §1) el trabajo mecánico, acotado y
verificable por aserción. **Claude Sonnet** lo que exige criterio, consistencia entre
archivos, gobernanza de diseño y texto de cara al cliente en dos idiomas — ahí un
error no truena, se publica.

| Track | ID | Tarea |
| :--- | :--- | :--- |
| DeepSeek | D1 | Fase 0 del empaquetado y sus compuertas |
| | D2 | Recorte medido, quitar `cairosvg` y la línea muerta del CDN, embarcar `zcta_centroids.csv` |
| | D3 | Borrar los dos bloques inventados |
| | D4 | Conversión a 9L en Python + formateador central + política de decimales |
| | D5 | Reexposiciones del procesador (§P.4) |
| | D6 | Transcribir las reglas a los 6 CSV + `derive_loco_account_map.py` |
| | D7 | Extraer `_flexible_pattern`, `_first_match` y el `find_file` anidado a `Scripts/file_matching.py` |
| | D8 | Arnés de verificación |
| | D9 | `Scripts/fact_table.py` + `Scripts/xlsx_writer.py` |
| | D10 | Las ~23 cruzadas estáticas con gráficas nativas de openpyxl |
| Sonnet | C1 | `Scripts/brand_assets.py` y los tres bugs de tipografía |
| | C2 | `Scripts/input_discovery.py` |
| | C3 | Unificar resolvedores + política de salida |
| | C4 | Escalera de atribución y diagnósticos |
| | C5 | Reestructura a 8 pestañas + pestaña de fuentes + reescritura de los 8 chips |
| | C6 | Activar margen y retirar las declaraciones de brecha |
| | C7 | Espejo en el PDF (7→10 páginas), helpers **aditivos** en `pdf_common.py`, i18n |
| | C8 | Las 4 plantillas por COM + diseño de `Reconciliation` / `Validation` |
| | C9 | Integrar `--format xlsx` en el orquestador y documentarlo |

**Dependencias:** D1 antes que todo · D5 antes de C4 · D6 antes de C4 y C6 · D7
antes de C2 · C4 antes de C5 · C5 antes de C7 · **D9 depende de D5, C4 y C6** (si la
tabla de hechos se construye antes de tener atribución y margen, hay que
reconstruirla) · C8 depende de D9 · D10 de C8 · C9 cierra.

**D3 y D4 son entregables el primer día** y juntos responden la queja literal del
cliente más el peor defecto de correctitud. **Sullivan mensual puede correr en
paralelo desde el principio**: su tabla de hechos y su hoja `Reconciliation` no
dependen de nada del trabajo de Loco.

### P.9 Verificación planeada

Hay intérprete en esta máquina: Conda `data_analytics_science` vía el hook de
PowerShell. *(La shell POSIX no tiene `python` en PATH, que es distinto de no
haberlo — vale dejarlo escrito porque un agente lo reportó como bloqueante.)*

- **Emparejamiento de fixtures, primero que nada.** Nuestros insumos son del **24 de
  agosto**, así que reconcilian contra el libro del 24 (`220.65` / CA `198.23` / TX
  `22.42`), **no** contra el del 31 (`212.98` / `196.07` / `16.92`). Ambas parejas se
  codifican con su fecha de corte asertada, para que la diferencia nunca se lea como
  un bug.
- **Redondeo: solo con datos reales.** El demo divide entre 12 de forma exacta y
  **esconde el bug**; el test tiene que negarse a pasar corriendo solo contra demo.
- **Atribución**: tabla de botellas por rung antes y después · la barra de 1488 debe
  colapsar · cada renglón sin atribuir con motivo y fuente no vacíos · cero literales
  de las cuatro cadenas viejas.
- **Offline**: `grep` de `fonts.googleapis|cdn.jsdelivr|https://` sobre los HTML
  generados debe salir vacío. Convertido en `Scripts/check_offline.py` y corrido
  desde el empaquetador, para que la regresión no pueda volver.
- **Libros de Excel**: sumar la tabla de hechos reproduce al centavo cada KPI ·
  confirmar que **sí existen** las partes `pivotTable`, `pivotCache` y `chart` (línea
  base inequívoca: los del cliente tienen cero de las tres) · el `ref` de la Table
  abarca todas las filas · `refreshOnLoad` en todos los cachés · encabezados de
  `Dataset` idénticos a lo que la plantilla espera.
- **El cuadre de Sullivan re-derivado**: `Reconciliation` debe dar `$0.00` en demo y
  real, **y delatar un descuadre de `$0.01` inyectado a propósito** — si no lo
  delata, la validación es decorativa.
- **Solo lectura**: copiar el árbol a un directorio no escribible y generar el
  mensual; no debe fallar por el caché de `zcta_centroids.csv`.
- **Sin regresión**: los 8 entregables × 2 idiomas, `pdf_common.py` solo aditivo,
  páginas intactas en los otros tres PDF, y las verificaciones de siempre.

**Manual, tras subir el ZIP** (no simulable): que la descripción dispare la skill en
inglés **y** en español; que en Cowork de escritorio el agente corra `--dry-run`
primero y escriba **en la carpeta del usuario**; que en Cowork nube detecte que no
hay carpeta local en vez de buscar `Z:\`; y **abrir los cuatro libros en Excel** para
confirmar que las dinámicas se pueblan, que las hojas de validación salen en cero, y
que las series de tiempo no quedaron ordenadas por valor.

### P.10 PENDIENTE — requiere decisión del cliente (no es deuda técnica)

Igual que §A, esto lo resuelve el usuario final:

- [ ] **Doble conteo de Melrose / Shopify.** Nuestra tubería suma DTC encima del
      depletion de Melrose; el cliente lo neutraliza con renglones negativos y excluye
      del volumen las órdenes de Shopify sin etiqueta. **Nuestra pestaña de DTC no
      puede cuadrar con la suya hasta que esto se decida.** Mayor riesgo de
      reconciliación del plan.
- [ ] **Archivo de costos.** Las tasas están transcritas de un documento interno; su
      propio `INPUT_FILE_REFERENCE.md` nombra `Bottle_Costs_and_Gross_Margin*.xlsx`
      como fuente de referencia. Pedirlo o una confirmación por escrito antes de
      publicar margen.
- [ ] **Aureo tiene dos tasas por canal.** ¿Cuáles de nuestras fuentes son mayoreo
      Park Street (614.50) y cuáles DTC (864.50)?
- [ ] **¿Adoptar el default de Texas** (sin match → Joe Pat / Off Premise)? Cambia
      materialmente el leaderboard.
- [ ] **¿Adoptar las 6 consolidaciones de cadena** y `TOTAL WINE` → Sara? Implica
      añadir a Sara al roster, que hoy no la tiene.
- [ ] ¿El mapa de cuentas derivado se versiona en el repo o se trata como dato de
      cliente y queda fuera del paquete?
- [ ] ¿Mostrar margen por cuenta y por vendedor, o solo agregado?
- [ ] ¿Los nombres del cliente —"Signature" y "Favorite Brands"— sustituyen a "CA" y
      "TX" en toda la interfaz?
- [ ] **Tipografía de Loco**: ¿sustituir Fraunces/Inter por Poppins, que ya viaja y
      cuesta 0 MB pero cambia el aire del tablero, o añadir ~0.5 MB de estáticas OFL?
- [ ] ¿Jerarquía Class B de Texas y las 63 cuentas on-premise de conteo únicamente en
      la pestaña POD?
- [ ] **Libros de Excel**: ¿destino Excel de escritorio confirmado? En Google Sheets
      las dinámicas no se refrescan igual.
- [ ] ¿Se replican las ~23 vistas **todas** o un subconjunto?
- [ ] **¿El dataset principal se entrega completo** (una fila por hecho atómico, con
      nombres de cuenta y de vendedor) o agregado? Es el archivo más sensible del
      lote: con él cualquiera reconstruye el negocio entero. En Sullivan incluye el
      detalle de órdenes de Club.
- [ ] ¿`--format all` incluye el `.xlsx` por omisión —tres archivos por corrida— o es
      opt-in?

### P.11 Riesgos

| Riesgo | Mitigación |
| :--- | :--- |
| El margen entra mal y se publican cifras equivocadas | Reconciliar contra `YTD Summary.Gross Margin` y `Lifetime GM` del propio libro del cliente; colector de SKU sin tasa que **avise en voz alta** — su `RULES.md` registra que durante meses toda orden de Aureo se descartó en silencio por SKU sin coincidencia |
| Unificar los resolvedores rompe invocaciones existentes | Ruta nueva detrás de `--auto`/`--data-dir` durante un release; el camino actual intacto |
| El recorte de fuentes degrada un PDF en silencio | Ya medido: 4 TTF registrados, 5 faces embebidos; verificar glifos con acentos tras el recorte |
| `pdf_common.py` es compartido y Loco crece 7→10 páginas | Solo cambios **aditivos**; línea base de páginas, textos, rectángulos y rango vertical antes y después, en los cuatro |
| El semanal de TX desde 119 snapshots resulta no derivable | Declararlo en el subtítulo y en la pestaña de fuentes, en lugar de publicar una línea mal formada |
| **Se borra `references_to_delete/` y con ella el único registro de estas reglas** | Transcribirlas a `Config/` y a documentación del repo **antes** de eliminar la carpeta. Es un paso del plan, no un detalle |
| El libro de Excel se entrega y se ve vacío porque nadie lo abrió | Modo de fallo por omisión de openpyxl. Lo evitan las cruzadas estáticas con gráfica nativa |
| Alguna plantilla se desincroniza del esquema de la tabla de hechos | Assertar en `xlsx_writer.py` que los encabezados de `Dataset` coinciden exactamente, y fallar en voz alta |
| `Validation` siempre da cero porque se compara consigo misma | La diferencia la calcula **Excel** contra la dinámica que él repobla desde `Dataset`. Se prueba inyectando un descuadre a propósito |

---

### P.12 IMPLEMENTADO 2026-09-14 — Las tres quejas del cliente y el libro de Excel para Loco

> Alcance de esta ronda de implementación, acotado por el usuario: **solo** lo
> que pide `notas_del_cliente.md` más el libro de Excel de referencia, **solo
> para Loco Tequila USA** (no los otros tres reportes — esos quedan en §P.6/§P.8
> con sus asignaciones intactas). Verificado con datos reales
> (`Client_Data/Loco_tequila_usa_data/`), no con demo: el demo divide entre 12
> de forma exacta y esconde el bug de redondeo.

**Archivos nuevos:**
- `Config/loco_tequila_us/` — 6 CSV declarativos: `gross_margin_rates.csv`,
  `unit_conversions.csv`, `account_mapping.csv` (derivado, 259 cuentas),
  `salespeople.csv` (roster con alias, incluye a Sara y Neeraj, que faltaban).
- `Scripts/loco_attribution.py` — la escalera de atribución (R0–R6).
- `Scripts/loco_margin.py` — tasas de margen y conversión a 9L con la excepción
  de 200 mL.
- `Scripts/tools/derive_loco_account_map.py` — deriva el mapa desde el libro
  del cliente.
- `Scripts/loco_excel_reference.py` — el libro de Excel de referencia.

**Archivos modificados:** `loco_tequila_us_relationships.py` (escalera
conectada, `build_fact_table`, split de `lines` en `to_weekly`/`to_lines`),
`Scripts/loco_data_processor.py` (bloques nuevos del payload, conversión a 9L
en Python), `Scripts/loco_dashboard_generator.py` (8 pestañas, se borraron los
bloques inventados), `Scripts/i18n.py`, `Scripts/generate_report.py`
(`--format xlsx`).

#### 1. Redondeo — resuelto
La conversión a cajas 9L se movió a Python (`loco_margin.to_9l`), con la
excepción del Blanco 200 mL (÷45) aplicada donde antes no podía estarlo — JS
recibía un agregado ya sumado y no puede diferenciar por SKU. Verificado: 0
valores sin redondear en el payload, 0 decimales largos pintados en el HTML.

#### 2. Atribución de vendedores — de 25% a 70.2% del volumen depletado
Reconocido en pruebas: la columna `SALES REP` de Favorite Brands son los
vendedores **del distribuidor** (`AUSTIN FB WAREHOUSE`, `BLAKE SCHNEIDER`), no
los de Loco — no se usa para atribuir. La regla de empate por prefijo en
frontera de palabra se probó contra los dos falsos positivos reales que el
propio código del cliente ya había documentado (`"A Restaurant"` vs
`"BRASSERIE CAPITALE,CAFE A COTE"`; `"The Mexican"` vs
`"RED O REST MEXICAN CUISINE"`) y **no cae en ninguno**. Conservación
verificada: suma de botellas por rung == total (1324.0 == 1324.0).

Hallazgo de la propia verificación: los retiros de inventario de vendedor en
Park Street (`Customer Type == "Salesperson"`) son stock hacia el maletero del
rep, no una venta depletada — se excluyeron del audit de atribución
(`to_lines=False`) pero se conservan en el pivote semanal (`to_weekly=True`),
que es donde siempre debieron vivir. Antes vivían mezclados.

#### 3. Las seis pestañas — hechas, más una de fuentes
`Overview · Salespeople · Signature · FavoriteBrands · Inventory · POD · DTC ·
Sources`. Los dos bloques con datos inventados (cadencia de cuentas,
sparklines: `Melrose Gas (DTC)`, `Brasswood Bar + Kitchen`, `daysSince:614`...)
se borraron —123 líneas—, no se disfrazaron. Margen bruto activado con las
tasas del cliente (FOB/DTR, Aureo a dos tasas por canal); la declaración de
"brecha de margen" se retira cuando el archivo de tasas está presente.

#### 4. Libro de Excel de referencia — `Scripts/loco_excel_reference.py`
`--format xlsx` (incluido en `all`): `Dataset` (505 filas, Excel Table
`FactLoco`) · `InventoryDataset` · `Overview/Salespeople/Signature/
FavoriteBrands/Inventory/Attribution` con fórmulas `SUMIFS` contra el dataset y
gráficas **nativas** de Excel · `Validation`, donde Excel re-deriva cada KPI.

**Verificado abriendo el libro en Excel de verdad (COM), no solo generándolo:**
las 6 filas de `Validation` dan `0.0` de diferencia tras recálculo completo; se
confirmaron 2 Excel Tables y 7 gráficas nativas en el `.xlsx` (los libros del
cliente tienen 0 de cada una); y se probó que `Validation` **no es tautológica**
inyectando un descuadre de 999,999 a propósito — la hoja lo delató.

**Un bug real que solo esta doble verificación encontró:** la primera versión
de `Validation` comparaba `SUM(FactLoco[Bottles])` contra el KPI
`depletions_bottles_ytd` del tablero, que por diseño excluye DTC — 1324 contra
985. No era un bug del Excel ni del tablero: eran dos preguntas distintas
("volumen total atribuible" contra "depletions CA+TX") comparadas como si
fueran la misma. Se corrigieron las filas de `Validation` para comparar cada
una contra su alcance real, y aparte se encontró y cerró la causa de fondo (el
párrafo anterior: Park Street salesperson-inventory mezclado en el audit de
atribución).

#### Verificación de no regresión
Sullivan mensual, semanal y unificado: cuadre al centavo intacto en los tres
(`$0.00` de diferencia) tras los cambios en `loco_tequila_us_relationships.py`.
Los 16 scripts compilan. DOM simulado del tablero de Loco: 0 errores de
ejecución, 24/24 bloques pintados, 8 pestañas creadas.
