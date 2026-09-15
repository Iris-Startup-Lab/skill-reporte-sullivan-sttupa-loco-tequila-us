# Loco Tequila USA — de los datos crudos al Weekly Sales Report

Este documento explica, hoja por hoja, de dónde sale cada número del reporte semanal que Sara (directora de Loco USA) usa cada semana (`Client_Data/Loco_tequila_usa_data/Sales Report Loco USA August 24, 2026.xlsx`), a partir de los 8 archivos crudos que llegan de los distribuidores, del ecommerce y de Park Street. También documenta qué se validó con números reales, qué quedó como hipótesis razonable sin confirmar, y — en la sección final — qué haría falta para construirle a Loco Tequila USA un reporte con el mismo formato de 3 entregables (PDF + XLSX + Dashboard HTML) que ya existe para Loco Tequila México en el proyecto hermano `skill_reporte`, usando las tablas de las secciones 1-5 como insumo.

Punto de partida clave, verificado programáticamente: el workbook del reporte **no tiene ninguna fórmula** (0 fórmulas en las 9 hojas). Todo son valores pegados. Eso confirma que hoy el reporte se construye "a mano" o con un proceso fuera de Excel — exactamente lo que este documento y el script intentan reproducir.

## 1. Inventario de fuentes crudas

| Archivo | Quién lo manda | Qué es realmente | Grano de la fila |
| :--- | :--- | :--- | :--- |
| `1 - Supplier - Inventory (*).xlsx` | Favorite Brands (distribuidor TX) | Inventario disponible por SKU y por bodega TX (MCA, HAR, LAR, CC, EP, ROS, ABQ, AUS, HOU, DAL) | SKU × bodega, en **botellas** |
| `FB Depletion Reports 2026/*.xlsx` | Favorite Brands (TX) | Depletions off-premise (venta del distribuidor a la cuenta final) acumuladas por mes calendario. Se guarda una copia nueva cada semana con la fecha de llegada, no hay fecha "real" en el archivo | Cuenta × producto, con una columna por mes (ene-dic) |
| `Inventory History (*).xlsx` | Signature Wine & Spirits (distribuidor CA, vía VIPIDIG) | Inventario disponible en el distribuidor CA, jerárquico por sitio (Southern Glazer's North/South) y producto | Sitio × producto, en **cases decimales de 6 botellas** |
| `YTD by Month [Bottles, Orders] (*).xlsx` | Signature (CA, exportado de VIPIDIG) | Depletions CA por cuenta, por producto y por factura, con columnas mensuales ene-ago y un acumulado YTD | Cuenta × producto × factura |
| `InventoryByLocation (*).csv` | Park Street | Inventario disponible por bodega/ubicación, incluyendo bodegas propias (CA Napa Aldenbridge) y el stock que cada vendedor carga consigo ("Salesperson Inventory") | SKU × ubicación, en **cases decimales** (6 botellas para 750mL, 24 botellas para 200mL) |
| `SalesOrdersSummary (*).csv` | Park Street | Todas las órdenes que Park Street facilita: venta mayorista (sell-in a los distribuidores), venta directa a retail/on-premise, y salidas del inventario que cada vendedor carga | 1 fila por línea de producto dentro de una orden |
| `orders_export_1 (*) shopify.csv` | Shopify (ecommerce loco-usa.com) | Órdenes de la tienda en línea, formato estándar de exportación de Shopify (79 columnas) | 1 fila por línea de producto dentro de una orden |
| `orders_export_1 (*) memory.csv` | Memory (mismo motor Shopify, usado para "event pick-up") | Mismo formato que el export de Shopify, para compras que el cliente recoge en un evento | 1 fila por línea de producto dentro de una orden |

Dos distinciones de negocio hay que tener siempre presentes porque el reporte las trata como cosas distintas:

**Depletions vs. Wholesale.** "Depletion" es cuánto le vendió el distribuidor a la cuenta final (lo que de verdad se movió al consumidor). "Wholesale" es cuánto le vendió Loco USA *al distribuidor* (la orden de reabasto). Son dos flujos de dinero y de unidades distintos, y el reporte tiene tablas separadas para cada uno: la sección "Depletions" de `YTD Summary`/`Monthly Summary` usa los archivos de depletion (FB Depletion, YTD by Month), mientras que la sección "Wholesale" de esas mismas hojas usa `SalesOrdersSummary.csv` filtrado a `Customer Type == 'Wholesaler'`.

**Snapshots semanales, no un histórico limpio.** Los `FB Depletion Reports` no tienen fecha real de negocio: cada semana llega un archivo con el acumulado del año a la fecha, y se guarda con la fecha de recepción en el nombre. Para saber "qué pasó esta semana" hay que restar el archivo de esta semana menos el de la semana anterior, columna por columna. El mismo principio parece aplicar a `Inventory History` (Signature) y a `1-Supplier-Inventory` (FB): son fotos del inventario al momento de descarga, no series de tiempo.

## 2. Qué contiene cada hoja del reporte

| Hoja | Contenido |
| :--- | :--- |
| `YTD Summary` | Depletions YTD por territorio (California, Texas, DTC, Ecommerce) en 9L/botellas/margen; ranking de vendedores; ventas wholesale por cuenta de distribuidor; ventas "Direct to Retail"; ranking de producto |
| `Monthly Summary` | Las mismas métricas de arriba pero desglosadas mes a mes (columnas fechadas el 26 de cada mes), más % de crecimiento MoM |
| `Salesperson by Week` | Botellas totales por semana ISO y por vendedor (Mark, Joe Pat, Manuel, Jacky) |
| `Accounts H1-2026` / `Accounts H2-2026` | Botellas por cuenta, mes a mes, con Salesperson, Channel (On/Off Premise/DTC) y una columna "Class B" |
| `Account Summary Total Business` | Vista de vida completa por cuenta: botellas y margen histórico, órdenes por año (2024/2025/2026), fecha del último pedido, días desde el último pedido |
| `DTC Sales by Month` / `DTC Sales by Year` | Ventas directas al consumidor (ecommerce + event pick-up + Melrose Gas/BML) por producto y por vendedor/referidor, más un bloque "Ecommerce" separado para órdenes sin atribución |
| `Inventory` | Resumen de inventario disponible en 9L, por producto, con el detalle de cada fórmula de conversión escrito en la propia hoja |

## 3. Mapeo tabla por tabla

### 3.1 Hoja `Inventory` — 100% reproducible y validada con números reales

Esta es la única hoja donde pude reconstruir los números exactos del reporte a partir de los archivos crudos, porque la hoja misma documenta sus fórmulas de conversión en la fila 18:

- Favorite Brands (TX): las cantidades en `1 - Supplier - Inventory` están en **botellas individuales** → 9L = botellas ÷ 12. Verificado: Loco Blanco TX = 126 botellas ÷ 12 = 10.5, que es exactamente el valor de "Total TX (9L)" para Blanco en el reporte.
- Signature/Southern Glazer's (CA): `Inventory History` reporta "On Hand Decimal Cases" en cases de 6 botellas → 9L = cases × 0.5. Verificado: el total combinado de Southern Glazer's North + South (68.667 cases) × 0.5 = 34.33, que coincide con la suma de "SO CAL SGWS" + "NOR CAL SGWS" del reporte (13.4167 + 20.9167 = 34.3334).
- Park Street 750mL: `InventoryByLocation.csv` reporta cases decimales de 6 botellas → 9L = cases × 0.5.
- Park Street 200mL: cases decimales de 24 botellas → 9L = cases × (24×200÷9000) = cases × 0.5333. Verificado exacto: Blanco 200mL CA = 10.75 cases × 0.5333 = 5.7333, igual al reporte.
- Grand Total TX (9L) = solo Favorite Brands (Park Street no reporta inventario propio en TX en este corte).
- Grand Total CA (9L) = SO CAL SGWS + NOR CAL SGWS + CA Park St (On Hand).

El script (`loco_tequila_us_relationships.py`) implementa esta hoja completa y **reproduce exactos, al centésimo, los 3 renglones de control del reporte** (Grand Total 9L = 220.65, Total CA = 198.23, Total TX = 22.42) y las 7 categorías de producto, incluida "NOT SELLABLE - SAMPLES ONLY" (que el reporte deja fuera de la suma "TOTAL" a propósito, como bloque aparte — el script respeta esa exclusión).

Un detalle de captura que vale la pena anotar porque hizo perder la cuenta la primera vez: en `InventoryByLocation.csv`, el sufijo "NSS" (not-sellable-samples) casi siempre vive en `product_id` (p. ej. `LCU-BLANCO-750NSS`) y **no** en `sub_brand_product_name` (que dice "Loco Blanco Tequila 750mL/6", igual que la versión vendible). Clasificar el producto usando solo `sub_brand_product_name` mete las muestras no vendibles dentro del inventario vendible y descuadra el total por la cantidad exacta de muestras en bodega — hay que clasificar combinando `product_id` + `sub_brand_product_name`.

### 3.2 Tabla "Wholesale" (dentro de `YTD Summary` y `Monthly Summary`) — validada exacta

Fuente única: `SalesOrdersSummary.csv`, filtrado a `Customer Type == 'Wholesaler'`, agrupado por `Customer`.

- **9L**: `Qty` (en cases de 6 botellas para estas filas) × 0.5. Verificado exacto para las 4 cuentas del reporte (Southern Glazer's Union City = 20.0, Santa Fe = 36.0, Favorite Brands Houston = 23.0, Brescome & Barton = 2.0).
- **Revenue**: sumar la columna **`Total`** (el importe de esa línea de producto), **no** la columna `Total Value`. Este es el hallazgo más importante de todo el ejercicio: `Total Value` es el total de la *orden completa* y se repite idéntico en cada línea de producto de esa orden, así que sumarlo de más cuenta el mismo pedido varias veces (en la orden `LCU20460` a Favorite Brands, `Total Value` = $28,419.80 aparece en las 3 líneas de producto, así que sumarlo da $85,259.40 — casi exactamente 3×). Usando `Total` en vez de `Total Value` da los 4 valores exactos del reporte ($25,625 / $58,000 / $28,419.80 / $2,805). Esta corrección aplica a **cualquier** reporte que consuma `SalesOrdersSummary.csv` de Park Street, incluyendo potencialmente otros reportes de esta skill.

### 3.3 Tabla "Direct to Retail" (dentro de `YTD Summary`) — aproximada, con hueco de negocio abierto

Misma fuente, filtrada a `Customer Type == 'Retailer'`, agrupado por `Customer`, usando la misma corrección `Total` (no `Total Value`).

Sumando así, "Melrose Gas - CA" da ~$24,996 contra los $23,152 del reporte, y el resto de cuentas retailer (Grapes & Grains, Lahontan Golf Club, Wally's, Monsey Wine & Liquor, Monterey Peninsula CC, Old Town Liquor) suman ~$13,478, mientras que el reporte solo deja $11,804 en el renglón "Other Park Street sales". La hipótesis más probable es que algunas de esas cuentas pequeñas (que parecen asignaciones puntuales de Aureo/Puro Corazón a cuentas on/off-premise de CA) ya se cuentan dentro de `Accounts H1/H2-2026` bajo el vendedor correspondiente, y por eso Sara las excluye de "Other Park Street sales" para no duplicar. **Esto habría que confirmarlo con Sara** antes de automatizarlo con confianza; el script deja el número "crudo" (todas las retailer) y también un número "candidato" excluyendo cuentas que ya aparecen en `Accounts H2-2026`.

### 3.4 Bloque "Depletions" (California / Texas) en `YTD Summary` y `Monthly Summary` — orden de magnitud correcto, sin cuadrar al 100%

- **California**: suma de la columna `1 Depletion Year Jan 2026 thru Aug 2026 Bottles` (o el equivalente por mes) de `YTD by Month [Bottles, Orders].xlsx`, sobre las 69 cuentas del archivo. Da 635 botellas Jan-Ago 2026 contra 545 en el reporte.
- **Texas**: suma de las columnas mensuales JAN..AUG del último `FB Depletion Reports 2026/*.xlsx` (el snapshot con fecha más reciente). Da 350 botellas contra 319 en el reporte. Nota importante: en el snapshot analizado, **el 100% de las filas de FB tienen `PREMISE = 'OFF'`** — es decir, Favorite Brands solo reporta depletions off-premise. Sin embargo el reporte muestra 63 cuentas on-premise en Texas, así que esas cuentas on-premise de TX deben salir de otra fuente: lo más probable, `SalesOrdersSummary.csv` con `Customer Type == 'Salesperson'` y vendedor TX (Joe Pat Clayton, Manuel Leyshon), es decir, ventas que el vendedor hace directo desde el inventario que carga consigo, sin pasar por el distribuidor.
- La diferencia entre el total crudo y el total del reporte (90 botellas en CA, 31 en TX) puede deberse a: filtrar por estatus de la orden, no contar ajustes/devoluciones negativas, un corte de fecha distinto al último día del archivo, o reclasificar algunas cuentas hacia el bucket "Direct to Consumer". No alcancé a aislar la regla exacta con los datos disponibles — queda documentado como brecha abierta.
- **Direct to Consumer** y **Ecommerce**: ver 3.6.

### 3.5 `Salesperson by Week`

Estructura: una fila por semana ISO (columna `WEEK`, arranca en la semana del 1-ene-2026) con el lunes de esa semana en `STARTING`, y una columna por vendedor (`MARK`, `JOE PAT`, `MANUEL`, `JACKY`) con botellas de esa semana.

Para reconstruirla hace falta, por cada transacción de cada fuente, saber (a) en qué semana ISO cayó y (b) a qué vendedor se le atribuye:

- `YTD by Month` (Signature/CA): tiene `Invoice Dates` por fila → semana ISO directa. El vendedor se infiere de a qué cuenta pertenece (Mark Harding y Jacky Gonzalez son los vendedores CA; hace falta la tabla cuenta→vendedor que se ve en `Accounts H1/H2-2026`, columna `Salesperson`).
- `FB Depletion Reports` (TX): no tiene fecha de transacción, solo acumulado mensual — para semanalizar hay que restar snapshots consecutivos y repartir la diferencia dentro del mes, o usar la columna `SALES REP` del archivo (viene con el rep de Favorite Brands, no necesariamente el vendedor de Loco).
- `SalesOrdersSummary.csv`: tiene `Date Posted` y, para las filas `Customer Type == 'Salesperson'`, el nombre del vendedor está en la columna `Customer` (p. ej. "Mark Harding - CA", "Jackquelin Gonzalez - CA").
- `orders_export_1 (*) shopify/memory.csv`: tiene `Created at` / `Paid at` y, cuando existe, la columna `Employee` o la primera palabra de `Tags` como posible atribución a vendedor.

El script implementa esta semanalización para las fuentes que sí tienen fecha (Signature, Park Street, Shopify/Memory) y deja el reparto de FB Depletion como aproximación mensual (no semanal) por la falta de fecha real en ese archivo.

### 3.6 `DTC Sales by Month` / `DTC Sales by Year`

El pie de página de estas hojas en el propio archivo da la pista de la fuente: *"Source: Park Street Sales History (Melrose Gas - CA, exclusively DTC) + Limited Edition Alebrije Art Collection sales"* para el bloque `ITEM`/`SALESPERSON`, y *"Shopify orders with no Tags value at the order level... excludes fully refunded orders"* para el bloque `ECOMMERCE`.

Interpretación (hipótesis, no verificada con exactitud numérica):

- **Ecommerce** (bloque separado, sin vendedor): filas de `orders_export_1 (*) shopify.csv` cuya columna `Tags` está vacía — es decir, compras que llegaron solas por la web, sin que un vendedor las haya generado o gestionado.
- **DTC** (bloque `ITEM`/`SALESPERSON`, el que suma 115 botellas en 2026): ventas de Melrose Gas/BML (que en `SalesOrdersSummary.csv` aparece como `Customer Type == 'Retailer'`, `Customer == 'Melrose Gas - CA'` — Melrose Gas/BML es la entidad minorista con licencia que Park Street usa para poder despachar los pedidos de la tienda en línea) más las ventas de la colección de arte limitada (Alebrije). Los nombres que aparecen como "vendedor" en el bloque `SALESPERSON` de esta hoja (Aileen Ruiz, Cuquita Dalla Brea, Eddie Gutierrez...) se parecen más a referidores/anfitriones de evento que a los 4 vendedores de planta — coinciden con lo que aparece en la columna `Tags` de `orders_export_1 (*) memory.csv` (compras de "event pick-up"), así que probablemente ese bloque en realidad cruza `Melrose Gas` (para el total en botellas/margen) con los `Tags` de Shopify/Memory (para saber a quién atribuírselo), no viene de un solo archivo.
- El **margen (GM)** de estas hojas no se puede derivar de los archivos crudos: ninguno de los 8 archivos trae costo unitario (COGS) por SKU. El script deja el GM en `None`/vacío y calcula solo unidades y, donde hay precio de venta (Shopify/Memory `Lineitem price`, Park Street `Unit Price`), el revenue bruto — dejando explícito que el margen requeriría una tabla de costos que hoy no está entre las 8 fuentes.

### 3.7 `Accounts H1-2026` / `Accounts H2-2026` y `Account Summary Total Business`

Estas tres hojas son, en esencia, la unión de cuentas de las tres fuentes con nivel de cuenta (Signature `YTD by Month`, FB `Depletion Reports`, y `SalesOrdersSummary.csv` con `Customer Type` en `Retailer`/`Salesperson`), con tres columnas que **no vienen en ningún archivo crudo**: `Salesperson`, `Channel` (On Premise / Off Premise / DTC / Unknown) y `Class B`. Esas tres columnas son, con altísima probabilidad, una tabla maestra que Sara mantiene a mano (cuenta → vendedor asignado, cuenta → canal comercial), porque el mismo nombre de cuenta (p. ej. "BOTTEGA RESTAURANT") aparece igual en el archivo de Signature y en el reporte con el `Channel` ya asignado, sin que el archivo de Signature traiga ese dato.

El script puede construir el "esqueleto" de estas tres hojas (botellas por cuenta y por mes, órdenes por año, última fecha de orden) directamente de las fuentes, pero para `Salesperson`/`Channel`/`Class B` usa un heurístico por palabras clave en el nombre de la cuenta (restaurante/bar/club/resort/hotel → On Premise; liquor/wine/spirits/market → Off Premise) marcado explícitamente como aproximación, y acepta opcionalmente un CSV de mapeo manual (`--account-map archivo.csv` con columnas `account,salesperson,channel`) para sobreescribir el heurístico cuenta por cuenta. Sin ese mapeo, el script etiqueta el canal como `"Unknown (heuristic)"` para que nunca se confunda con un dato confirmado.

## 4. Resumen de brechas para robustecer la skill

1. **Falta una tabla maestra cuenta → vendedor → canal.** Es el hueco más grande. Sin ella, `Accounts H1/H2`, `Account Summary Total Business` y parte de `Salesperson by Week` no se pueden reproducir con exactitud, solo aproximar.
2. **Falta un costo unitario (COGS) por SKU.** Sin él no se puede calcular Gross Margin en ninguna hoja — solo unidades y, donde hay precio, revenue bruto.
3. **`SalesOrdersSummary.csv`: usar siempre la columna `Total`, nunca `Total Value`**, para evitar triplicar/duplicar revenue en órdenes con más de una línea de producto. Vale la pena revisar si la skill hermana (`reporte-loco-tequila`, que también consume datos de Park Street) tiene el mismo riesgo.
4. **`FB Depletion Reports` no tiene fecha de transacción real**, solo el acumulado del mes a la fecha de descarga. Para tener depletions semanales de TX hay que quedarse con snapshots consecutivos (uno por semana) y restar.
5. **La regla exacta de qué cuenta cuenta como "California"/"Texas" depletions vs. "Direct to Consumer" no cuadra al 100%** con una suma directa de los archivos — hay ~15% de diferencia en ambos territorios que no pude explicar solo con los 8 archivos. Recomendación: preguntarle a Sara qué filtro aplica (¿excluye devoluciones? ¿corta en una fecha distinta a la del archivo más reciente? ¿reclasifica algunas cuentas?).
6. **La separación DTC vs. Ecommerce depende de la columna `Tags` de Shopify/Memory**, que es texto libre capturado a mano — cualquier inconsistencia de captura (typo en el tag, tag vacío por error) desalinea el reporte real.

## 5. El script `loco_tequila_us_relationships.py`

Implementa lo anterior de forma modular: una función de carga por archivo fuente, y una función de construcción por tabla del reporte. Con `--data-dir` (por defecto `Client_Data/Loco_tequila_usa_data`) recalcula las tablas y las guarda como CSV en `--output-dir`, e imprime una tabla de "reconciliación" comparando lo calculado contra los valores reales del reporte del 24-ago-2026 (los que se pudieron verificar), para que quede claro qué tan cerca o lejos queda la simulación en cada hoja. Uso básico:

```bash
python loco_tequila_us_relationships.py --data-dir "Client_Data/Loco_tequila_usa_data" --output-dir "Output/simulacion_loco_usa"
```

Opcional, para mejorar la atribución de cuenta→vendedor→canal:

```bash
python loco_tequila_us_relationships.py --account-map mi_mapeo_cuentas.csv
```

Limitaciones que el script deja explícitas en su salida (no las esconde ni las redondea para que "se vean bien"): sin tabla maestra de cuentas, sin costo unitario, y sin fecha real en FB Depletion, las hojas `Accounts H1/H2`, `Account Summary Total Business`, `DTC Sales`, y el margen en cualquier hoja quedan como aproximaciones etiquetadas, no como el número exacto de Sara.

## 6. Llevar el formato de reporte de México (`skill_reporte`) a Loco Tequila USA

Aclaración de alcance: esta sección **no** es sobre editar ni ejecutar el reporte de México. `skill_reporte` (`E:\Users\1167486\Local\scripts\data_analytics_science\tequila_loco\skill_reporte`) es el proyecto de la skill hermana `reporte-loco-tequila`, que genera el reporte semanal de **Loco Tequila México** (venta doméstica, en pesos, semanas tipo "Semana 33 2026", canales Tradicional/Moderno, contexto CRT/agave/NOM-006) — un mercado y una moneda distintos a los de Loco Tequila USA. Lo que se documenta aquí es **qué se necesitaría para darle a Loco Tequila USA un reporte con el mismo formato y la misma disciplina analítica** (los 3 entregables, las 4 ventanas comparativas fijas, la línea de diseño *storytelling with data*), construido a partir de las tablas de las secciones 1-5, no a partir de reemplazar los datos de México.

### 6.1 Qué es exactamente lo que valdría la pena copiar de México

- **Los 3 entregables**: PDF ejecutivo con paleta institucional y storytelling (situación → hallazgo/riesgo → recomendación), Excel de varias hojas analíticas, y un dashboard HTML interactivo y filtrable.
- **Las 4 ventanas comparativas fijas** que el motor de México siempre reporta, sin que nadie las pida: (A) semana vs. semana inmediata anterior (WoW), (B) misma semana del año anterior (YoY), (C) acumulado YTD vs. el mismo acumulado del año anterior, y (D) últimas 52 semanas vs. las 52 del año anterior (solo si hay ≥ 40 semanas de historia).
- **Los principios de diseño** documentados en `designs/storytelling_summary.md`: color intencional (todo en gris/neutro salvo lo que importa), nada de pie charts para tendencia, semáforos por umbral de relevancia (no solo por signo), tablas con fila de total resaltada.
- **El contexto de mercado obligatorio** vía búsqueda web en cada corrida (en México: CRT, precio del agave, NOM-006).

### 6.2 El "esquema canónico" que alimenta el motor de México, columna por columna

El motor de México (`data_processor.py`, `generate_report.py`) no lee los archivos crudos del cliente directamente: lee siempre los mismos 2 CSV con un esquema fijo (`loco_actuals_enriquecido.csv` de 20 columnas, `loco_actual_vs_plan_semanal.csv` de 21 columnas — documentados en su propio `SKILL.md`). Copiar ese esquema es, de hecho, el atajo más práctico para reusar el motor con datos de USA: si se le entrega un CSV con esas mismas columnas (adaptadas), en teoría no habría que tocar `xlsx_generator.py`/`pdf_generator.py`/`dashboard_generator.py`. Así queda cada columna del archivo de actuals si se intenta poblar con lo que hay en Loco USA:

| Columna canónica (México) | ¿Se tiene en USA? | Fuente / nota |
| :--- | :--- | :--- |
| `semana de venta`, `fecha de venta`, `anio` | Sí, parcial | Signature (`Invoice Dates`), Park Street (`Date Posted`), Shopify/Memory (`Created at`) tienen fecha real → semana ISO directa. **FB Depletion (TX) no tiene fecha de transacción**, solo acumulado del mes — mismo hueco de la sección 3.5. |
| `SKU/producto`, `categoria_o_linea` | Sí | Ya resuelto por el clasificador de producto del script (`categorize_product`), usado en las 5 fuentes. |
| `unidades_de_venta`, `botellas`, `ml_botella`, `litros`, `cajas_9L` | Sí | Mismo cálculo que ya usa el script para `Inventory`/`Depletions` (bottles ÷ 12 = 9L, o cases × 0.5 / 0.5333 según fuente). |
| `cliente` | Sí | Nombre de cuenta/cliente, presente en las 5 fuentes con nivel de cuenta. |
| `canal`, `canal_reporte`, `sub_canal` | **No** (parcial) | México usa Off Trade/On Trade/Directo y Tradicional/Moderno; el equivalente en USA (On Premise/Off Premise/DTC/Ecommerce) **depende de la misma tabla maestra cuenta→canal que falta** en la sección 3.7. Lo único que sí viene "gratis" es el `Customer Type` de Park Street (Wholesaler/Retailer/Salesperson) y el `PREMISE` de FB (aunque en el corte analizado siempre es `OFF`). |
| `region_o_estado` | Sí, y más rico que en México | TX trae `STATE` (siempre "TX"), CA siempre es CA, y **Shopify/Memory traen `Billing/Shipping Province` con el estado real del comprador** (vimos TX, CA, PA, OH, NV en la muestra) — se podría armar un mapa de ventas DTC por estado de EUA que el reporte actual de Sara ni siquiera tiene. |
| `precio_unitario`, `venta_con_impuestos`, `venta_sin_impuestos` | **No, para los dos canales más grandes** | Este es el hallazgo nuevo de esta sección: ni `FB Depletion Reports` ni `YTD by Month` (Signature) traen **ninguna columna de precio o venta en dinero** — son reportes de depletion en unidades, punto. Solo Park Street (`SalesOrdersSummary.csv`) y Shopify/Memory traen precio/venta. Eso significa que hoy, para poner un signo de dólar a lo que pasa en California y Texas (las dos columnas "Depletions" más grandes del reporte de Sara), hace falta —igual que en México— una **lista de precio por SKU** que no viene en ninguno de los 8 archivos. |
| `margen_pct`, `margen_pesos` (→ `margen_usd`) | **No** | Mismo hueco ya documentado en 3.6/4: sin costo unitario (COGS) por SKU no hay margen en ninguna hoja, en ningún canal. |

### 6.3 El archivo de Plan/Presupuesto: hueco completo, no parcial

El esquema de México también depende de `loco_actual_vs_plan_semanal.csv` (metas semanales de botellas/venta/margen por canal y producto, con `var_vs_plan_%` y `cumplimiento_%`) para poder narrar "vamos arriba o abajo del plan". **No existe ningún archivo de metas, cuota o presupuesto entre los 8 archivos de Loco USA.** Sin uno, un reporte estilo México para USA puede tener las 4 ventanas comparativas (WoW/YoY/YTD/Rolling52), pero no puede tener la comparación contra Plan — habría que pedirle a Sara (o a quien maneje el forecast comercial) un archivo de meta por semana/mes, por territorio y por producto, aunque sea aproximado.

### 6.4 Histórico multi-año: alcanza para DTC, no para distribuidor

Las ventanas B, C y D (YoY, YTD vs. año anterior, Rolling 52) necesitan al menos un año de historia previa. De las fuentes de Loco USA, **solo el canal DTC ya trae 2024/2025/2026** (visible en `DTC Sales by Year` del propio reporte de Sara, que cita como fuente el historial de Park Street/Melrose Gas y Shopify/Memory). Los archivos de depletion de distribuidor (`FB Depletion Reports 2026`, `YTD by Month`) solo tienen 2026 — no hay carpeta equivalente a "FB Depletion Reports 2025" ni un export de Signature con años previos entre los 8 archivos. Mientras eso no se consiga, las 3 ventanas que dependen de año anterior solo se podrían reportar de verdad para DTC/Ecommerce; para California y Texas quedarían en blanco o marcadas como "sin histórico", igual que hace el motor de México cuando detecta que solo tiene un año de datos.

### 6.5 Contexto de mercado: mismo mecanismo, otro tema

México usa CRT (Consejo Regulador del Tequila), precio del agave y NOM-006 porque es venta doméstica regulada por esas normas. Para Loco Tequila USA, que es venta de exportación, el contexto equivalente que tendría sentido buscar cada semana es otro: regulación de importación/comercialización de bebidas alcohólicas en EUA (TTB), el sistema *three-tier* estado por estado (relevante porque literalmente define por qué existen distribuidores como Favorite Brands/Southern Glazer's), tendencia de la categoría tequila en el mercado estadounidense, y el tipo de cambio USD/MXN si se quiere ligar el costo de producción (en pesos, vía agave/CRT) con el margen de exportación (en dólares). El mecanismo de "buscar en la web antes de cada corrida" de México se podría reusar tal cual, solo cambiando los temas de búsqueda.

### 6.6 Ruta recomendada, en orden

1. **Extender `loco_tequila_us_relationships.py`** para que, en vez de solo diagnosticar/reconciliar, emita un CSV con el mismo esquema de 20 columnas de `loco_actuals_enriquecido.csv` (en USD, con `canal_reporte` en `On Premise/Off Premise/DTC/Ecommerce`, y `margen_pct`/`margen_usd`/`precio_unitario`/`venta_*` en blanco o con un supuesto explícito marcado como tal, igual que México usa 60% de margen de referencia cuando no hay COGS real).
2. **Conseguir dos insumos que hoy no existen entre los 8 archivos**: una lista de precio por SKU (mínimo, para poder poner $ a las Depletions de CA/TX) y, si se quiere Plan vs. Actual, un archivo de metas semanales/mensuales por territorio y producto.
3. **Aceptar la limitación de histórico** mientras no se consiga un export de FB/Signature con 2024-2025: las ventanas YoY/YTD-vs-año-anterior/Rolling52 del reporte estilo México, para USA, solo se podrían mostrar con confianza para el canal DTC hasta entonces.
4. Con eso resuelto, `xlsx_generator.py`, `pdf_generator.py` y `dashboard_generator.py` de `skill_reporte` son, en su mayoría, agnósticos de canal/moneda (reciben el CSV canónico y aplican la paleta/formato) — la adaptación real de esos tres scripts sería sobre todo de textos (cambiar "Off Trade"/"On Trade" por "Off Premise"/"On Premise", quitar CRT/NOM-006 y meter TTB/three-tier) más que de lógica.
