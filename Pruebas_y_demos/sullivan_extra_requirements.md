# Requerimientos de Datos Adicionales — Cliente Sullivan (Sullivan Rutherford Estate)

**Fecha:** Octubre 2026  
**Proyecto:** Implementación del Tablero Comparativo vs Plan y Reporte Ejecutivo Semanal  
**Destinatario:** Equipo Directivo y Equipo de Datos / Finanzas de Sullivan  
**Estado del Diagnóstico:** ❌ **DATOS INSUFICIENTES PARA GENERAR EL TABLERO COMPARATIVO VS PLAN**

---

## 1. Dictamen Ejecutivo

Tras una auditoría técnica profunda y exhaustiva de la carpeta `Datos_test_to_delete`, se concluye que **la información suministrada actualmente NO es suficiente** para generar el tablero de comparativa vs. plan (ni los entregables asociados en PDF directivo, Libro Excel analítico y Dashboard interactivo HTML).

Si bien los archivos contienen información valiosa de operaciones recientes en Commerce7 y resúmenes contables, existen **tres vacíos estructurales insalvables**:

1. **Inexistencia de un Plan / Presupuesto Semanalizado por Producto y Canal**: El sistema cuenta con estados financieros contables (P&L) y proyecciones de flujo de caja (Cash Flow) a nivel mensual global de la bodega, pero **no contiene ningún archivo de presupuesto de ventas desglosado a nivel semana, producto (SKU) y canal de comercialización**. Sin estas metas, es matemáticamente imposible calcular el cumplimiento %, variaciones en dólares ($) y variaciones porcentuales vs. Plan.
2. **Falta de Continuidad Temporal e Histórico Transaccional**: Solo se suministraron transacciones de un mes aislado (**Abril 2026**) y una semana puntual (**Semana del 17 al 23 de Agosto de 2026**). No existe el histórico transaccional de 2025 ni el acumulado continuo de 2026. Esto impide generar las comparativas directivas automáticas del motor:
   - Semana vs. Semana Anterior (**WoW**).
   - Semana vs. Misma Semana del Año Anterior (**YoY**).
   - Acumulado del Año en Curso vs. Año Anterior (**YTD**).
   - Tendencia anual móvil (**Rolling 52 semanas**).
3. **Silos Operativos no Unificados (DTC vs. Wholesale vs. Experiencias)**: Las ventas directas al consumidor (DTC en Commerce7), las ventas a distribuidores (órdenes de compra / *Idig Depletions*) y las reservaciones de *Tasting Room* (Tock) se encuentran en archivos desconectados con formatos dispares y sin un layout unificado de venta de producto.

---

## 2. Inventario y Evaluación de los Archivos Recibidos

| Archivo / Carpeta | Tipo de Información | Diagnóstico Técnico | ¿Permite Comparativa vs Plan? |
|---|---|---|:---:|
| `Apr_OrderSales.xlsx` | 583 transacciones de venta DTC de abril 2026 (Commerce7). | **Muy útil como base de Actuals**: Contiene SKU, botellas, importe, canal, estado y cliente. Sin embargo, cubre únicamente un mes (abril 2026) y mezcla venta de botellas con reservaciones y descuentos. | ⚠️ Parcial (solo actuals de 1 mes) |
| `Apr_FinancialReport.xlsx` | Resumen financiero por orden de abril 2026. | Archivo de control y conciliación financiera; redundante con `Apr_OrderSales.xlsx`. | ❌ No aporta plan ni histórico |
| `Apr_SalesbyChannel.xlsx` / `Apr_SalesbyClub.xlsx` / `Apr_SalesbyTag.xlsx` | Reportes pivote agregados de abril 2026. | Agregaciones estáticas sin detalle de SKU ni fecha diaria/semanal. | ❌ No |
| `April_C7_Data_Guide.xlsx` | Guía de clasificación de reglas de negocio de Commerce7. | **Excelente documento conceptual**: Define cómo clasificar Tasting Room, Estate Club, Founder's Club, Telesales, Eventos, Tock y Web. Debe aplicarse en la extracción de datos. | ℹ️ Guía metodológica |
| `Sullivan_SKU_Map.xlsx` | Mapeo maestro de SKUs entre C7, Biagi, Winecare y Western. | **Excelente insumo maestro**: Permite normalizar los nombres comerciales de los vinos (Cabernet Sauvignon, Coeur de Vigne, Merlot, etc.). | ℹ️ Catálogo maestro |
| `Weekly/Week_2026_08_23/` | 66 órdenes DTC de 1 semana de agosto 2026, 4 órdenes de compra (PO) mayoristas, depletions de distribuidores y 7 días de reservaciones Tock. | Una sola semana aislada en el tiempo. Desconectada de abril 2026 y sin histórico previo. | ❌ Incompleto (1 semana aislada) |
| `2025_P&L_and_Cash_flow/` | P&L contable de QuickBooks y modelo de Cash Flow 2025. | Visión contable/financiera mensual consolidada (ingresos globales de vino, fletes, salarios, etc.). No desglosa metas por SKU, ni por semana, ni por canal comercial. | ❌ No es presupuesto operativo de ventas |
| `2026_P&L_and_Cash_Flow/` | P&L contable a septiembre 2026 y Forecast mensual global. | Mismo caso: proyecciones financieras mensuales a alto nivel sin granularidad de SKU/semana. | ❌ No es presupuesto operativo de ventas |

---

## 3. Las 5 Brechas Críticas que Sullivan Debe Resolver

### Brecha 1: Generación del Archivo de Presupuesto Semanal (Budget / Plan)
Para que el tablero despliegue las tarjetas de **Plan vs. Real**, gráficas de cumplimiento y desgloses por canal y producto, Sullivan debe proveer un archivo de presupuesto semanalizado con:
- **Semana y Año**: Semana ISO (ej. `2026-W16` o Año `2026` + Semana `16`).
- **Producto / SKU o Línea**: El vino o familia de vinos presupuestada (ej. `Estate Cabernet Sauvignon`, `Coeur de Vigne`, `Estate Merlot`).
- **Canal de Venta**: Canal presupuestado (`Tasting Room`, `Estate Club`, `Founder's Club`, `Telesales`, `Web / Ecommerce`, `Wholesale`).
- **Métricas Presupuestadas**:
  - `Plan_Venta_Neta` (USD): Monto en dólares sin impuestos presupuestado.
  - `Plan_Botellas`: Cantidad de botellas físicas proyectadas.
  - `Plan_Cajas_9L` (Opcional): Cajas de 9 litros equivalentes proyectadas.
  - `Plan_Margen_Pesos` o `COGS_Unitario` (Opcional): Costo o margen proyectado.

### Brecha 2: Profundidad Temporal e Histórico Transaccional Continuo
El motor analítico genera automáticamente 4 ventanas de tiempo comparativas. Para que estas funcionen sin huecos ni ceros artificiales, Sullivan requiere:
- **Año Base Actual (2026)**: Transacciones completas desde la **Semana 01 hasta la semana que se desee evaluar** (por ejemplo, Semana 1 a 35 continuas).
- **Año Anterior de Comparación (2025)**: Transacciones de venta de todo el año 2025 (Semana 01 a Semana 52). Esto permite calcular el comparativo contra la misma semana del año anterior (YoY) y el acumulado YTD año contra año.

### Brecha 3: Unificación de Canales y Consolidación Transaccional
Sullivan opera con tres plataformas distintas:
1. **Commerce7**: Ventas Direct-to-Consumer (Tasting Room, Clubes de Vino, Web, Telesales, Eventos).
2. **Ventas Mayoristas (Wholesale / Distribuidores)**: Facturas y órdenes de compra de distribuidores (Southern Glazer's, RNDC, etc.) actualmente en `Open PO's` e `Idig Depletions`.
3. **Tock**: Cobros por experiencias de degustación.

**Requerimiento**: Sullivan debe integrar o exportar estas fuentes en **un único archivo unificado de transacciones de venta**, donde cada fila sea una línea de venta con su fecha, cliente, canal y producto.

### Brecha 4: Estandarización de Canales según la Guía de Clasificación de Sullivan
En `April_C7_Data_Guide.xlsx`, Sullivan especifica que los canales en Commerce7 no deben tomarse de forma cruda sino con su lógica de negocio:
- `Inbound` con tag `Event` ➔ **Event**
- `Inbound` con tag `Corporate` ➔ **Corporate**
- `Inbound` con tag `Friends & Family` ➔ **Friends & Family**
- Resto de `Inbound` ➔ **Telesales**
- `Web` con identificador `Tock` ➔ **Tock**
- Resto de `Web` ➔ **Web / Ecommerce**
- `POS` ➔ **Tasting Room**
- `Club` con nombre `Estate` ➔ **Estate Club**
- `Club` con nombre `Founder's` ➔ **Founder's Club**
- Facturación mayorista ➔ **Wholesale**

El archivo de ventas reales debe incluir directamente la columna **`Canal`** o **`Canal_Reporte`** con esta clasificación ya asignada, evitando discrepancias en el tablero.

### Brecha 5: Distinción entre Botellas de Vino y Otros Conceptos (Servicios / Degustaciones / Descuentos)
El sistema del cliente incluye líneas que no son botellas de vino físicas (por ejemplo: *"Founder's Reserve Tasting"*, *"The Poetry Merlot Mastery Experience"*, *"Complimentary Discount"*, *"Order Fee"*).
- Es indispensable contar con una columna **`Categoria_Negocio`** (ej. `Producto (Botellas)` vs. `Experiencias / Tastings` vs. `Servicios / Cuotas` vs. `Descuentos`).
- De este modo, el tablero de comparativa vs. plan evalúa el desempeño del vino embotellado sin distorsionar el volumen de botellas ni el precio promedio por botella.

---

## 4. Estructura de Archivos Requerida para Sullivan

Para implementar de inmediato la skill con los datos de Sullivan, se definen los siguientes **archivos CSV oficiales de entrada**:

```
raíz_de_datos/
├── sullivan_ventas_reales.csv      <-- [OBLIGATORIO] Transacciones históricas y del año en curso
├── sullivan_plan_semanal.csv       <-- [OBLIGATORIO para vs Plan] Presupuesto semanalizado
└── sullivan_catalogo_sku.csv       <-- [RECOMENDADO] Maestro de productos, líneas y costos
```

---

## 5. Diccionario de Datos de los Archivos Requeridos

### A. Archivo de Ventas Reales (`sullivan_ventas_reales.csv`)
Cada fila representa una línea de producto vendida en una orden.

| Columna | Tipo | Requerido | Descripción / Formato | Ejemplo |
|---|---|:---:|---|---|
| `Fecha` | Fecha | **Sí** | Fecha de venta en formato `YYYY-MM-DD`. | `2026-04-15` |
| `Semana` | Texto / Entero | **Sí** | Número de semana o formato `YYYY-Www`. | `2026-W16` o `16` |
| `Anio` | Entero | **Sí** | Año de la transacción. | `2026` |
| `SKU` | Texto | **Sí** | Código único del producto. | `20CS712` |
| `Producto` | Texto | **Sí** | Nombre comercial estandarizado del vino. | `2020 Estate Cabernet Sauvignon` |
| `Linea_Producto` | Texto | Opcional | Familia o nivel de vino (Estate, Reserve, Coeur, Blanco). | `Cabernet Sauvignon` |
| `Categoria_Negocio` | Texto | **Sí** | Permite aislar vino embotellado de tastings/fees. | `Producto (Botellas)` |
| `Canal` | Texto | **Sí** | Canal comercial clasificado. | `Tasting Room`, `Estate Club`, `Founder's Club`, `Telesales`, `Web / Ecommerce`, `Wholesale` |
| `Cliente` | Texto | **Sí** | Nombre del cliente, socio de club o distribuidor. | `John Smith`, `Southern Glazer's CA` |
| `Estado` | Texto | **Sí** | Estado o región de destino. | `California`, `Texas`, `New York` |
| `Botellas` | Entero / Decimal | **Sí** | Unidades de botellas vendidas en la línea. | `6` |
| `Precio_Unitario` | Decimal | **Sí** | Precio unitario de venta (USD). | `125.00` |
| `Venta_Neta` | Decimal | **Sí** | Subtotal neto vendido en USD (sin impuestos ni flete). | `750.00` |
| `Impuestos` | Decimal | Opcional | Monto de impuestos (sales tax / excise). | `58.13` |
| `Venta_Total` | Decimal | Opcional | Total cobrado con impuestos y flete. | `808.13` |
| `Costo_Unitario` | Decimal | Opcional | Costo unitario del producto (COGS) en USD. | `38.50` |
| `Margen_Dolares` | Decimal | Opcional | Margen bruto en USD (`Venta_Neta - (Botellas * Costo)`). | `519.00` |
| `Cajas_9L` | Decimal | Opcional | Cajas de 9L equivalentes (`Botellas * 0.75 / 9.0`). | `0.50` |
| `Estatus` | Texto | Opcional | `Vigente` / `Completada` (se excluyen `Cancelada`). | `Vigente` |

---

### B. Archivo de Presupuesto Semanal (`sullivan_plan_semanal.csv`)
Cada fila representa la meta presupuestada para una combinación de Semana + Producto + Canal.

| Columna | Tipo | Requerido | Descripción / Formato | Ejemplo |
|---|---|:---:|---|---|
| `Anio` | Entero | **Sí** | Año del presupuesto. | `2026` |
| `Semana` | Texto / Entero | **Sí** | Semana presupuestada (`2026-W16` o `16`). | `2026-W16` |
| `Producto` | Texto | **Sí** | Nombre del vino o línea presupuestada. | `Estate Cabernet Sauvignon` |
| `Canal` | Texto | **Sí** | Canal presupuestado. | `Tasting Room`, `Estate Club`, `Founder's Club`, `Telesales`, `Web / Ecommerce`, `Wholesale` |
| `Plan_Botellas` | Decimal | **Sí** | Cantidad de botellas presupuestadas para esa semana. | `120` |
| `Plan_Venta_Neta` | Decimal | **Sí** | Monto de venta neta en USD presupuestado. | `15000.00` |
| `Plan_Margen_Dolares` | Decimal | Opcional | Margen bruto en USD presupuestado. | `10200.00` |
| `Plan_Cajas_9L` | Decimal | Opcional | Cajas de 9 litros presupuestadas. | `10.0` |

---

### C. Archivo de Catálogo Maestro y Costos (`sullivan_catalogo_sku.csv`)
Permite automatizar el cálculo de COGS, margen y volumen en litros.

| Columna | Tipo | Descripción | Ejemplo |
|---|---|---|---|
| `SKU` | Texto | Código del producto en Commerce7 o inventario. | `20CS712` |
| `Producto` | Texto | Nombre canónico de reporte. | `2020 Estate Cabernet Sauvignon` |
| `Familia` | Texto | Familia de vino. | `Cabernet Sauvignon` |
| `Tamano_ML` | Entero | Volumen por botella en mililitros. | `750` |
| `Precio_Lista` | Decimal | Precio sugerido de venta al público (USD). | `125.00` |
| `Costo_COGS` | Decimal | Costo unitario estándar de producción (USD). | `38.50` |
| `Activo` | Booleano | Si el producto se encuentra a la venta. | `True` |

---

## 6. Archivos de Ejemplo Generados en la Raíz del Proyecto

Para facilitar la adopción por parte del equipo de Sullivan, se han generado en la raíz de este proyecto **tres archivos CSV de muestra** que implementan exactamente las especificaciones anteriores con datos realistas del catálogo de Sullivan:

1. **`sullivan_ventas_reales_ejemplo.csv`** (100 filas): Muestra transaccional completa con órdenes representativas de 2025 y 2026, cubriendo todos los canales, productos emblemáticos de Sullivan, estados de EE.UU., precios y costos reales.
2. **`sullivan_plan_semanal_ejemplo.csv`** (100 filas): Muestra del presupuesto semanalizado 2026 desglosado por semana, canal y vino, listo para alimentar el motor de comparativa vs. Plan.
3. **`sullivan_catalogo_sku_costos_ejemplo.csv`** (25 filas): Maestro de productos con SKUs auténticos de Sullivan, familias, capacidades en ml, precios de lista y costos unitarios (COGS).

---

## 7. Próximos Pasos Recomendados

1. **Compartir estas especificaciones** con el administrador de Commerce7 y el equipo financiero de Sullivan.
2. **Extraer el histórico continuo** de ventas reales desde el 01 de enero de 2025 hasta la fecha más reciente de 2026.
3. **Consolidar el presupuesto 2026** a nivel semanal siguiendo la plantilla provista en `sullivan_plan_semanal_ejemplo.csv`.
4. Una vez recopilados los archivos completos, colocarlos en la carpeta de datos designada y ejecutar el generador de la skill para obtener el tablero integral con sus 3 entregables ejecutivos.
