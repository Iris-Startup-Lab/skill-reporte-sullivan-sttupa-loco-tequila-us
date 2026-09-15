# Resumen para Comprender: Qué Hacía Exactamente el Cliente en el Sistema Anterior
## Análisis Detallado Paso a Paso de la Carpeta `references_to_delete/Reporte_del_cliente` y Comparativa con el Assessment

---

### Introducción y Propósito de este Documento

Este documento reconstruye con precisión **el día a día y el flujo operativo completo** que seguía el cliente (liderado por Sara Rowan) y su equipo antes de la nueva arquitectura. 

Al comparar los documentos [Loco_USA_Reporting_System_Assessment.md](file:///e:/Users/1167486/Local/scripts/skills_generales/reporte-sullivan-sttupa-loco-tequila-us/Loco_USA_Reporting_System_Assessment.md) y [Loco_USA_Reporting_System_Assessment_es.md](file:///e:/Users/1167486/Local/scripts/skills_generales/reporte-sullivan-sttupa-loco-tequila-us/Loco_USA_Reporting_System_Assessment_es.md) con el código y los archivos reales en `references_to_delete/Reporte_del_cliente`, se observa que el Assessment sintetizó muy bien la arquitectura general, las métricas y los riesgos; sin embargo, **en el código real, en los comentarios de control y en las notas operativas existen múltiples pasos, parches de emergencia, intervenciones manuales y hábitos semanales que enriquecen y completan la historia de qué pasaba exactamente**.

A continuación se detalla paso a paso todo lo que sucedía cada semana.

---

## 1. El Flujo Operativo Semanal del Cliente (Paso a Paso)

El reporte semanal de ventas de Loco Tequila USA se emitía con fecha de cada **lunes** (reflejando el corte de operaciones comerciales cerrado hasta el domingo anterior). Para lograrlo, el cliente ejecutaba el siguiente proceso operativo:

### Paso 1.1: Recolección y descarga de 8+ insumos desde portales externos
Sara debía acceder individualmente a múltiples plataformas web para descargar las exportaciones brutas:
1. **SGWS / Signature (California):** Reporte de depletions YTD (`YTD by Month [Bottles, Orders] (1).csv` o similar). SGWS cambió de interfaz en agosto y renombró el portal a "Signature", lo que obligó a adaptar la búsqueda de nombres de archivo.
2. **Park Street (California):** Ventas mayoristas y órdenes Direct to Retail / DTC (`SalesOrdersSummary*Park_Street*.csv` o `Orders-PSI.csv`).
3. **Favorite Brands (Texas):** Ventas mensuales de Texas (`1 - Depletion - By Month*.xlsx` o `Depletions-FB.xlsx`).
4. **Shopify Tienda Principal:** Exportación completa de pedidos DTC (`orders_export*.csv`). **Regla aprendida por Sara:** pedir siempre exportación COMPLETA y nunca incremental/MTD, porque las incrementales rompían los empalmes históricos si faltaba un periodo.
5. **Shopify Memory Bottles:** Tienda especial de ventas privadas y eventos (Mantarraya y botellas de colección reservadas).
6. **3 Archivos de Inventario Disponible:**
   - SGWS: `Inventory History (1).csv` (inventario en almacenes de SoCal y NorCal).
   - Park Street: `InventoryByLocation.csv` o `Inventory-PSI.csv` (almacén central y existencias asignadas).
   - Favorite Brands: `1 - Supplier - Inventory.xlsx` o `Inventory-FB.xlsx` (inventario en Texas).
7. **Libros de Rutas de Vendedores (Google Drive):**
   Tres hojas de cálculo independientes de Google Drive sincronizadas localmente en la laptop de Sara:
   - `Joe Pat Accounts and Route SOND.xlsx` (originalmente llamado `Q2`, luego renombrado `SOND` por Sep-Oct-Nov-Dec).
   - `Jacky Accounts and Route Q2.xlsx`.
   - `Mark Accounts and Route Q2.xlsx`.
   *(Manuel Leyshon no tenía ruta física porque se le trataba como vendedor enfocado en DTC/Shopify).*
8. **Insumos Ocasionales y Estáticos:**
   - Hoja de cálculo de Google Sheets en vivo `Y_Drink_Reporting` (cuentas On-premise Clase B de Texas). Sara debía descargarla periódicamente a mano en `static/Y_Drink_Reporting.xlsx`.
   - Archivo histórico `ACS 2024- 2025 DEPLETION SUMMARY.xlsx` (alojado en una ruta absoluta fija de Google Drive).

### Paso 1.2: Creación de la carpeta semanal de datos
- Sara creaba una carpeta en su Google Drive sincronizado con el formato `MMDDYY Data Input` (por ejemplo `083126 Data Input`).
- **Problema real encontrado en el código:** En una ocasión nombró la carpeta `"081026 Data Input "` (con un espacio al final). La expresión regular de Python falló silenciosamente y tomó la semana anterior, lo que obligó a agregar una limpieza con `.strip()` en `config.py`.
- Hacia finales de agosto de 2026, Sara intentó estandarizar los nombres de los 8 archivos a una nomenclatura fija (`Depletions-SGWS.csv`, `Inventory-PSI.csv`, `Inventory-FB.xlsx`, etc.).

### Paso 1.3: Ejecución de la Generación (`pipeline/final_report.py`)
El cliente abría una terminal o sesión de Claude Code y ejecutaba:
```bash
python pipeline/final_report.py
```
**Lo que el código hacía internamente (el motor de copia):**
1. **No existía una plantilla en blanco.** El script buscaba en `outputs/` el libro de trabajo de la semana anterior (ej. `Sales Report Loco USA August 24, 2026.xlsx`).
2. Copiaba ese archivo con el nuevo nombre: `Sales Report Loco USA August 31, 2026.xlsx`.
3. Si el archivo ya existía (porque Sara lo había abierto o ejecutado antes), el script **evitaba sobreescribir el archivo completo** para no destruir cambios o formatos que Sara hubiera hecho a mano directamente en Excel.
4. Cargaba el libro con `openpyxl.load_workbook()` y procedía a **sobreescribir las celdas de datos valor por valor**.

### Paso 1.4: Auto-archivado de la captura de Texas
En plena ejecución, el script copiaba automáticamente el archivo de Favorite Brands de esa semana hacia la carpeta histórica `TX_MONDAY_SNAPSHOTS_DIR` con el prefijo `MMDDYY 1 - Depletion - By Month.xlsx`. Esto lo hicieron porque Favorite Brands cambiaba frecuentemente el formato de sus nombres de archivo y rompía el cálculo semanal de Joe Pat si no se archivaba de inmediato.

### Paso 1.5: Verificación de Totales (`pipeline/verify_totals.py`)
El cliente ejecutaba:
```bash
python pipeline/verify_totals.py
```
Este script validaba 16 aserciones de suma en filas de `TOTAL` con una tolerancia de $0.05. Se implementó obligatoriamente el 19 de agosto de 2026 después de que Sara descubriera dos errores graves enviados a directores:
- El `TOTAL` regional sumaba en secreto a Melrose Gas.
- La columna combinada de años en DTC borraba los datos de 2026 debido a un conflicto de tipos en Pandas (`numpy.int64`).

### Paso 1.6: Comprobaciones manuales obligatorias que no estaban automatizadas
Sara tenía que abrir el archivo en Excel y verificar visualmente:
1. **Comprobar a Joe Pat Clayton:** Que la suma de su columna en la pestaña *Salesperson by Week* fuera idéntica al centavo a su total en *YTD Summary*. Si no coincidían, indicaba que la separación entre fechas reales de DTC y el rezago semanal de Texas tenía un desfase.
2. **Verificar el conteo de cuentas On-Premise de Joe Pat:** Confirmar que mostrara **63** (el conteo de cuentas hijas Clase B de Texas). Como esas cuentas no suman botellas ni dinero, el código a veces lo dejaba en blanco accidentalmente.
3. **Forzar recálculo en Excel:** Guardar y verificar que no hubiera fórmulas con `#REF!` o `#VALUE!`.

### Paso 1.7: Exportación a PDF (`pipeline/export_pdf.py`)
Se ejecutaba el comando para convertir el Excel a PDF usando LibreOffice en macOS:
```bash
python pipeline/export_pdf.py "outputs/Sales Report Loco USA August 31, 2026.xlsx"
```
El script configuraba el área de impresión, fijaba orientación horizontal (excepto *Salesperson by Week* en vertical), repetía los encabezados y llamaba al binario `soffice`.

### Paso 1.8: La hoja manual paralela
Sara mantenía a mano de forma 100% manual un archivo separado llamado `2025 vs 2026 Depletions Comparison.xlsx`. Ningún script de Python leía ni alimentaba este archivo; era un cálculo personal de Sara para la dirección.

---

## 2. Lo que Hacía Cada Pestaña del Libro Excel (Las 9 Pestañas + 1 Desaparecida)

Al inspeccionar los archivos reales generados en `outputs/`, se observa la estructura exacta:

| # | Nombre de Pestaña | Propósito Operativo | Comportamiento y Reglas Ocultas |
|:---|:---|:---|:---|
| 1 | **YTD Summary** | Resumen ejecutivo anual | Contiene 5 bloques: 1) Regiones (Total, CA, TX, DTC, Ecommerce); 2) Vendedores (Mark, Jacky, Joe Pat, Manuel); 3) Wholesale (distribuidores mayoristas); 4) Direct to Retail (Melrose + Park Street); 5) Productos (9 SKUs). |
| 2 | **Monthly Summary** | Ventas mes a mes (Ene–Dic) | Presenta 4 bloques verticales: Botellas, Margen Bruto, Cajas 9L Wholesale, Ingresos Wholesale. |
| 3 | **Salesperson by Week** | Seguimiento semanal 1 a 52 | Desglose por vendedor para las 52 semanas del año. Joe Pat se alimentaba de la resta de capturas de lunes; Mark y Jacky de fechas reales de facturación. |
| 4 | **Accounts H2-2026** | Cuentas 2do semestre (Jul–Dic) | **Cambio clave del cliente:** A partir del 10 de agosto de 2026, Sara pidió mover H2 **antes** que H1 para tener a la vista el periodo vigente. Muestra cada cuenta con su vendedor, canal y acumulado anual completo. |
| 5 | **Accounts H1-2026** | Cuentas 1er semestre (Ene–Jun) | Mismas cuentas del 1er semestre. La columna YTD no es del semestre, sino el acumulado de todo el año en ambas pestañas. |
| 6 | **Account Summary Total Business** | Ficha histórica de por vida | Botellas y margen histórico desde 2024; cantidad de órdenes por año (2024, 2025, 2026); promedio de meses entre pedidos y días transcurridos desde la última compra. |
| 7 | **DTC Sales by Month** | Desglose mensual DTC | Ventas mensuales por producto, por las 14 personas identificadas en DTC y por Ecommerce. |
| 8 | **DTC Sales by Year** | Comparativo anual DTC | 2024, 2025, 2026 y total consolidado. Solo 2026 se recalculaba con código; 2024 y 2025 eran datos estáticos heredados en las celdas. |
| 9 | **Inventory** | Existencias físicas y 9L | Inventario de SGWS (SoCal / NorCal), Park Street (almacén + pedidos abiertos) y Favorite Brands (Texas). Desglosado en vendible vs. muestras/no vendible (NSS). |
| 10 | **Overdue Accounts** *(Desaparecida)* | Cuentas con retraso en recompra | **Descubrimiento del análisis:** Apareció en el reporte del **20 de julio de 2026** y luego **desapareció**. Filtraba cuentas donde `Días sin comprar / (Promedio meses * 30.44) > 1.0x`. Nunca se reincorporó en el código de agosto tras el reinicio del sandbox. |

---

## 3. Detalles Críticos y Trucos Ocultos en el Código que Enriquecen el Assessment

Al revisar línea por línea `pipeline/final_report.py`, `pipeline.py`, `ca_load.py` y `config.py`, se identificaron comportamientos sumamente específicos que realizaba el sistema:

### 3.1 "Auto-sanación" e inserción dinámica de filas (Hack de código)
Como no había plantilla base y se copiaba el archivo de la semana previa, cuando Sara solicitaba cambios en la estructura, los programadores idearon un truco en Python llamado *"self-healing insert"*:
- **Fila de subtítulo de fecha:** Revisaba si en la celda `A2` decía "Region" o "Depletions". Si decía eso, significaba que era un archivo viejo, entonces **insertaba una fila nueva**, empujando todas las demás filas hacia abajo (+1) y escribiendo la fecha en gris de 8pt.
- **Bloque Wholesale:** Revisaba si en la fila 16 decía "Wholesale". Si no estaba, **insertaba 6 filas**.
- **Bloque Direct to Retail:** En agosto se movió de lugar. El script buscaba en qué fila estaba el bloque viejo, **lo borraba con `delete_rows()` y lo insertaba en la fila 22**.
- **Títulos en pestañas:** Revisaba si `A1` tenía el título en negrita Arial 14; si no, insertaba una fila en 5 pestañas.
*Consecuencia:* Los números de fila fijos en el código cambiaron tres veces en un mes, provocando desfases en las fórmulas hasta que se parchaba de nuevo.

### 3.2 El corte de fecha en domingo (`_week_capped_iso`)
Las facturas de SGWS a veces se generaban la misma mañana del lunes en que Sara descargaba el archivo. Como el reporte siempre corre un lunes pero corresponde a la semana comercial cerrada el domingo anterior:
- El código forzaba a que cualquier registro con fecha igual o posterior al lunes se recortara al domingo inmediatamente anterior (`clip(upper=TODAY - 1 day)`), evitando que ventas de la nueva semana aparecieran prematuramente.

### 3.3 El dilema de celdas vacías vs. guion (`"-"` vs. `""`)
- Si un mes pasado tenía 0 ventas confirmadas, el reporte colocaba un guion (`"-"`).
- Si era el **mes en curso** o un mes futuro con 0 ventas, el reporte dejaba la celda en **blanco riguroso** (`None`), porque un guion transmite que el mes cerró en cero, lo cual es falso si el mes sigue abierto.

### 3.4 El caso del tequila Aureo ($614.50 vs $864.50)
Durante meses, todas las ventas de Loco Tequila Aureo vía Park Street (como órdenes en Wally's, Grapes & Grains o Lahontan) **se eliminaban silenciosamente** porque no existía un precio DTR asignado para ese SKU. El 24 de agosto de 2026, Sara aclaró que debía calcularse a:
- **$614.50 / botella:** para ventas mayoristas por Park Street.
- **$864.50 / botella:** para ventas DTC cumplidas por Melrose/BML.
Se recuperaron de golpe $4,400 dólares de ventas que estaban invisibles.

### 3.5 Reasignación de órdenes Alebrije (Piezas de Colección de Arte)
Las botellas de edición limitada Alebrije ($379.33 DTR) son ventas de arte/regalo privadas, pero Park Street las facturaba a través de cuentas comerciales como Wally's o Grapes & Grains.
- En lugar de dejar el crédito a la tienda minorista, el código tenía un diccionario de excepciones fijas (`ALEBRIJE_ORDER_OVERRIDES`):
  - Orden `LCU20371` y `LCU20361`: asignadas a **Mark**.
  - Orden `LCU20431`: asignada a **Cuquita Dalla Brea**.
  - Orden `LCU20413`: asignada a **Sara**.
  - Orden `LCU20489`: orden con 2 botellas de Alebrije confirmada como simple resurtido de almacén para Melrose Gas, por lo que no se le dio comisión a ningún vendedor.

### 3.6 El bug de coincidencia por palabras: "Bottega" vs "A Restaurant"
Un vendedor (Mark) tenía asignada una cuenta llamada *"A Restaurant"*. El código original buscaba si el nombre de la cuenta estaba contenido en el texto del cliente.
- Al procesar la cuenta *"BOTTEGA RESTAURANT"*, la letra final "A" de Bottega junto con " Restaurant" formaba *"A Restaurant"*, por lo que durante semanas **Bottega Restaurant (de Jacky) se le acreditó erróneamente a Mark**.
- Tuvieron que inventar la función `_starts_at_word_boundary()` con expresiones regulares para exigir que la coincidencia empiece en un límite de palabra (*word boundary*).

### 3.7 Cuentas consolidadas y cadenas (Total Wine, Wally's, Vendome)
- **Total Wine:** Cualquier cuenta que empiece con "TOTAL WINE" (con más de 22 sucursales en CA y 14 en TX) se unifica en una sola fila para Sara, pero en las métricas de conteo de cuentas físicas se cuenta cada sucursal por separado.
- **Wally's:** Tres sucursales unificadas bajo Mark.
- **Vendome:** Consolidado bajo Mark tras resolver variantes tipográficas.
- **Giuseppe's:** 4 variantes unificadas bajo Mark (revirtiendo una decisión anterior de dejarlas separadas).

### 3.8 El algoritmo de capturas de lunes para Texas (`tx_monday_snapshots.py`)
Dado que Favorite Brands no proporciona fechas de facturación diarias sino solo acumulados mensuales:
- El sistema leía cada archivo de los lunes.
- Si entre dos capturas consecutivas había exactamente **7 días de diferencia**, calculaba la resta (`s1 - s0`).
- Si la diferencia de botellas era positiva, esa diferencia se asignaba como la venta real de esa semana para Joe Pat.
- Si había un salto de más de 7 días (por ejemplo, si faltaba un lunes), el sistema **no inventaba datos** y dejaba la semana en blanco.
- Además, utilizaba este mismo cálculo para saber cuántas órdenes hubo en Texas: cada vez que una cuenta aumentaba su saldo de botellas entre dos lunes consecutivos, se contabilizaba como **1 orden**.

---

## 4. El Subsistema de Notas de Voz de Campo (`Field Sales Reports/`)

En la carpeta se encontró un proyecto experimental ("Fase 1") diseñado para que los vendedores no tuvieran que escribir reportes de visitas en un teclado:
1. **Grabación:** Los vendedores abrían la app *Notas de Voz* del iPhone durante o después de visitar un bar o tienda. Mencionaban el nombre de la cuenta, la fecha, las promociones, los cócteles y las órdenes levantadas.
2. **Depósito:** Compartían el audio a una carpeta de Google Drive sincronizada en `Field Sales Reports/audio_inbox/`.
3. **Procesamiento Técnico:**
   - `transcribe.py`: Usaba herramientas locales para pasar el audio a texto en `transcripts/` y movía el audio a `archive/`.
   - `extract.py`: Enviaba la transcripción al API de Anthropic (Claude) mediante un prompt para extraer entidades JSON estructuradas (Cuenta, Vendedor, Tipo de Activación, SKUs, Cantidades).
   - Generaba dos archivos CSV en `drafts_pending_review/`: uno para órdenes y otro para activaciones.
4. **Por qué fracasó en la práctica:**
   - Se acumularon **93 archivos de audio (108 MB)** y **92 transcripciones**.
   - La carpeta `reviewed_approved/` estaba **completamente vacía**: nadie en la empresa revisó ni aprobó jamás un solo borrador.
   - Varios vendedores crearon subcarpetas con sus nombres dentro de `audio_inbox/`, pero el script solo leía archivos en la raíz, por lo que decenas de audios quedaron abandonados sin procesar.

---

## 5. Tabla Comparativa: Lo que Decía el Assessment vs. Lo que Revela el Código Real

| Tema | Declarado en el Assessment | Detalle Oculto Descubierto en el Código Real |
|:---|:---|:---|
| **Modelo de Libro de Salida** | Se copia el libro anterior y se sobreescriben celdas. | Si el archivo de la semana ya existe en `outputs/`, no se sobreescribe para **no borrar ediciones manuales hechas en Excel por Sara**. Además, usa código dinámico para insertar o mover filas completas si detecta que la semana previa tenía formato viejo. |
| **Pestaña de Cuentas Vencidas** | "Definida en RULES.md pero nunca construida". | **Sí existió:** se generó en el archivo del 20 de julio de 2026 y tenía lógica real (`Days Since Last / (Avg Months * 30.44) > 1.0`). Fue abandonada tras el reinicio del sandbox. |
| **Orden de Pestañas H1 / H2** | "Por convención interna H2 se coloca antes de H1". | En julio H1 iba primero. El cambio a poner **H2 antes que H1** fue una solicitud explícita de Sara el 10 de agosto al comenzar a analizar el segundo semestre. |
| **Manejo de Fechas en SGWS** | SGWS tiene fechas de factura reales. | Los lunes por la mañana SGWS factura antes de la descarga; el script tiene un tope forzado (`clip`) para recortar fechas del mismo lunes al domingo previo. |
| **SKU Loco Aureo** | Faltaba la tasa de margen hasta agosto. | Al no tener tasa, el código **eliminaba todas las órdenes de Aureo**, ocultando miles de dólares de ventas hasta que se programó la corrección el 24 de agosto. |
| **Órdenes de Edición Especial Alebrije** | Reenrutadas de Park Street a DTC. | Se gestionaban con una lista manual de números de orden específicos (`LCU20371`, `LCU20361`, etc.) asignando manualmente la comisión a Mark, Sara o Cuquita. |
| **Archivado de Texas** | Usa capturas de lunes para restar semanas. | El script copia y renombra automáticamente el archivo de Favorite Brands en cada corrida hacia una carpeta histórica de Drive para que no se pierda la serie. |
| **Reporte de Depletions 2025 vs 2026** | "Existe un archivo complementario no tocado por el código". | Es una plantilla puramente manual mantenida por Sara fuera de todo pipeline. |

---

## 6. Conclusiones y Aprendizajes Fundamentales

1. **La fragilidad del sistema anterior no era solo técnica, sino de flujo humano:**
   Todo el proceso dependía de que Sara descargara a tiempo 8 archivos, los colocara en una ruta específica de su laptop, mantuviera actualizados 3 archivos de rutas con nombres cambiantes en Google Drive y ejecutara scripts que modificaban un archivo Excel heredado.
2. **El gran valor a preservar son las 12 secciones de reglas (`RULES.md`):**
   Las tasas de margen por canal, la prohibición de duplicar ventas de Melrose Gas con Shopify, las reglas de límite de palabras para no atribuir mal las cuentas y las excepciones de productos son el verdadero conocimiento del negocio.
3. **Por qué la solución unificada actual es superior:**
   Al independizar la lógica de las rutas personales de Sara, desacoplar el formato del contenido mediante datos estructurados y validaciones automáticas, y presentar un Dashboard interactivo con conciliación al centavo, se elimina el riesgo de que la pérdida de un archivo o un reinicio de equipo deje a la empresa sin su reporte financiero.
