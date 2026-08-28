# TO-DO — Revisión de la skill Sullivan

> Revisión original: 2026-08-26 · Rondas de debuggeo aplicadas: **2026-08-27** (§B–§F y §H)
> Alcance: `dashboard_generator.py`, `pdf_generator.py`, `generate_report.py`, entregables en `Output/`,
> contra `Sullivan_data_guide.md` y `SKILL.md`.
>
> **Estado: todos los puntos de la revisión están cerrados.** Quedan 2 decisiones de negocio
> (§A) que necesitan al cliente, no código.

---

## A. PENDIENTE — requiere decisión del cliente (no es deuda técnica)

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
