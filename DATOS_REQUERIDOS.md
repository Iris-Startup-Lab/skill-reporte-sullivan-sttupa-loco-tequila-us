# Qué datos pide cada tipo de reporte

Referencia de insumos por reporte: qué archivos hacen falta, cómo se llaman, qué
columnas se leen de cada uno y qué pasa si faltan. Los nombres de archivo se
buscan por **patrón**, no exactos, porque el cliente exporta con la fecha en el
nombre y ésta cambia cada periodo.

Para ver la forma de cada archivo sin tener datos reales:

```powershell
python Scripts/make_demo_data.py            # genera los tres juegos en Data_for_demo/
```

Los demos son sintéticos (nada de dato real de cliente) pero reproducen la
estructura exacta: mismos encabezados, mismas jerarquías, mismas reglas.

---

## Resumen en una tabla

| Reporte | Archivos | Fuente | Carpeta demo |
|---|---|---|---|
| Sullivan mensual | 2 obligatorios (+3 opcionales) | Commerce7 | `Data_for_demo/Sullivan_data_demo/` |
| Sullivan semanal | 4 obligatorios | Commerce7 + Tock + Park Street + iDig | `Data_for_demo/Sullivan_weekly_demo/` |
| Loco Tequila USA | 7 archivos + 1 subcarpeta | Favorite Brands + Southern Glazer's + Park Street + Shopify | `Data_for_demo/Loco_tequila_demo/` |
| Sttupa | — | todavía no hay datos | no existe |

---

## 1. Sullivan Rutherford Estate — mensual

Reconciliación contable DTC al centavo, Club Deep Dive y mapa de envíos.

```powershell
python Scripts/generate_report.py --brand sullivan --data-source demo --period-label "April 2026" --output-dir Output
python Scripts/generate_report.py --brand sullivan --order-sales "Mis_Ventas.xlsx" --financial-report "Mi_Financiero.xlsx" --period-label "May 2026" --output-dir Output
```

### `*_OrderSales.xlsx` — obligatorio

Export transaccional de Commerce7, **una fila por línea de producto** (no por
orden). El real trae 114 columnas; se leen éstas:

| Columna | Para qué |
|---|---|
| `Order Number` | Contar órdenes únicas sin duplicar por línea |
| `Channel` | Prioridades 1-8 de la cascada (`POS`, `Web`, `Club`, `Inbound`) |
| `Product SubTotal` | **Base monetaria del lado de ventas** (importe de la línea) |
| `Club Title`, `Club Package` | Distinguir Estate de Founder's; si ambas están vacías en un pedido de Club, cae en *Unclassified* |
| `External Order Vendor` | Separar Tock del Web propio |
| `Order Submitted Date` | Serie temporal |
| `Ship To State Code`, `Ship To Zip Code` | Mapa Albers y puntos por ZIP |

> **Cuidado con la columna de dinero.** `Product SubTotal` es de la **línea** y
> `SubTotal` es de la **orden completa repetido en cada línea**. Sumar `SubTotal`
> a nivel línea cuenta el mismo pedido tantas veces como líneas tenga. El motor
> usa `Product SubTotal` en ventas y `SubTotal` en el financiero, que es lo que
> hace cuadrar a $0.00.

### `*_FinancialReport.xlsx` — opcional pero recomendado

Espejo financiero, una fila por línea. Se leen `Order Number`, `Channel`,
`SubTotal`, `Club Name`. **Sin él no hay reconciliación**: el reporte se genera
igual, pero sin el cuadre al centavo, que es su principal argumento de confianza.

### `*_SalesbyChannel / SalesbyClub / SalesbyTag.xlsx` — opcionales

Agregados que Commerce7 exporta ya sumados (`Channel`/`Club`/`Order Tag`,
`Order Count`, `Sub Total`, ...). Sirven como validación cruzada gratuita: si el
total calculado desde `OrderSales` no coincide con el `Sub Total` de estos, el
export está incompleto. Hoy el mensual no los lee todavía.

---

## 2. Sullivan Rutherford Estate — semanal

Consolida 9 canales DTC, cuentas por cobrar de distribución y depletions.

```powershell
python Scripts/generate_report.py --brand sullivan --cadence weekly --output-dir Output
python Scripts/generate_report.py --brand sullivan --cadence weekly --weekly-data-dir "Mi_Semana" --output-dir Output
```

Los cuatro archivos van **en una misma carpeta**; se localizan por palabra clave
en el nombre (sin distinguir mayúsculas):

| Palabra clave | Archivo típico | Origen |
|---|---|---|
| `orderreport` | `OrderReport_8.23.26.xlsx` | Commerce7 |
| `tock` | `Tock_8.23.26.xlsx` | Tock |
| `open po` | `Open PO's 8.23.26.xlsx` | Park Street |
| `depletion` | `Idig Depletions 8.26.xlsx` | Southern Glazer's (iDig) |

### OrderReport

Mismo formato que el mensual. Aquí se **deduplica por `Order Number`** y se usa
el `SubTotal` de la orden (verificado: esa suma coincide exacto con el
`Sub Total` de `SalesbyChannel`). Columnas: `Order Number`, `Channel`,
`SubTotal`, `External Order Vendor`, `Club Package`, `Club Title`,
`Order Paid Date`.

`Order Paid Date` define el **periodo del reporte y el nombre del archivo de
salida**: se toma la fecha de pago más reciente y se calcula su semana comercial
lunes-domingo. Si el export no trae ninguna fecha usable, el periodo se reporta
como dato ausente en vez de inventarse.

### Tock

Una fila por día. Se leen `Date` y, según la base elegida, `Net receivable`
(recomendado: lo efectivamente cobrable) o `Net sales`. Se controla con
`--tock-basis`.

### Open PO's

Una fila por factura de distribución. Columnas: `Status` (`Open`/`Paid`),
`Balance`, `Total`, `Aging`, `Total Cases`, `Invoice #`, `Customer`, `Market`.

> `Total` es lo facturado y `Balance` lo que falta por cobrar. En una factura
> pagada el balance es 0 por definición, así que el efectivo cobrado se lee del
> `Total` de las filas `Paid`.

### iDig Depletions

El más irregular: **encabezado de dos pisos**.

```
fila 0  Supplier: SULLIVAN RUTHERFORD EST/P
fila 1  (vacío) ...            1 Depletion Month Aug 2026 (celda combinada)
fila 2  Sites | OnOff Premises | Brands | Item Names | Item Name ID |  Sales Depletions Decimal Cases |  Sales Depletions 9L Cases
fila 3  Total | Total | Total | Total | Total | 84.41668 | 42.33332
fila 4+ Southern Glazer's - CA-North | ...
```

Se lee sin encabezado, se combinan las filas 1 y 2 para formar los nombres de
columna, y se elige automáticamente el **mes más reciente** presente.

El desglose por estado sale del nombre del sitio:
`"Southern Glazer's - CA-North"` → `CA`. Las regiones comerciales de un mismo
estado (`CA-North` + `CA-South`, `NY-Metro` + `NY-Upstate`) se **consolidan**,
porque el cliente razona por estado. Se usa el nivel de subtotal por sitio
(`Sites` ≠ Total y los tres niveles inferiores en `Total`): verificado contra el
archivo real, esos subtotales suman **exacto** la fila `Total/Total`. Si no
cuadraran, el proceso lo avisa en vez de taparlo.

`TX` y `PR` aparecen en 0 y marcados "sin feed": el cliente vende ahí pero su
distribuidor (Favorite Brands) no manda sell-through.

---

## 3. Loco Tequila USA

```powershell
python Scripts/generate_report.py --brand loco_tequila --output-dir Output
python Scripts/generate_report.py --brand loco_tequila --data-dir "Mis_Datos" --account-map "cuentas.csv" --output-dir Output
```

Siete archivos y una subcarpeta, todos en la misma carpeta. Los patrones **sí**
importan: el prefijo es lo que identifica cada fuente.

| Patrón | Origen | Qué aporta | Columnas leídas |
|---|---|---|---|
| `1 - Supplier - Inventory*.xlsx` | Favorite Brands (TX) | Inventario TX en botellas | `ITEM #`, `Product`, `Total` (encabezado en la fila que contiene `ITEM #`) |
| `Inventory History*.xlsx` | Southern Glazer's (CA) | Inventario CA jerárquico | `Sites`, `Plants`, `Item Names`, ` On Hand Decimal  Cases` (encabezado donde la col. 0 dice `Sites`) |
| `InventoryByLocation*.csv` | Park Street | On-hand por SKU y ubicación | `product_id`, `sub_brand_product_name`, `onhand`, `location_grp` |
| `SalesOrdersSummary*.csv` | Park Street | Mayoristas, retail directo, vendedores | `Customer`, `Customer Type`, `Date Posted`, `Qty`, `Unit`, `Total`, `Total Value`, `Product Code`, `Product Description` |
| `YTD by Month*.xlsx` | Southern Glazer's (CA) | Depletions CA por cuenta y mes | `Retail Accounts`, `City`, `Item Names`, `Invoice Dates`, `1 Depletion Month <Mes> 2026  Bottles`, la columna de año que termina en `Bottles` y la que contiene `9L` |
| `orders_export_1*shopify.csv` | Shopify | Ecommerce | `Created at`, `Lineitem quantity`, `Lineitem name`, `Lineitem price`, `Tags` |
| `orders_export_1*memory.csv` | Memory | DTC de eventos | idem |
| `FB Depletion Reports 2026/*.xlsx` | Favorite Brands (TX) | Depletions TX por cuenta y mes | `CUSTOMER`, `CITY`, `STATE`, `CHAIN`, `PREMISE`, `SALES REP`, `ITEM ` (con espacio final), `PRODUCT`, `JAN`..`DEC` |

**El nombre de la subcarpeta no es libre**, pero tampoco literal: se busca la
subcarpeta cuyo nombre, quitando todo lo no alfanumérico, empiece con
`fbdepletionreports`. Así valen `FB Depletion Reports 2026`, la variante con
guiones y el año que sea (si hay varias, gana la del año más alto). Dentro se
elige el archivo más reciente parseando la fecha del nombre
(`...2026-08-24.xlsx` o `082426 ...xlsx`).

**Los nombres se comparan sin puntuación.** Todo patrón de esta sección tolera que
los separadores cambien: cada tramo no alfanumérico vale por cualquier otro. Es
lo que permite que `1 - Supplier - Inventory*.xlsx` reconozca a la vez el archivo
del cliente y el demo `1-Supplier-Inventory-demo.xlsx` — que **tiene** que ir con
guiones, porque el instalador rechaza el paquete completo si alguna ruta del ZIP
trae un espacio, un apóstrofo, una coma o un corchete.

### Reglas de negocio que hay que respetar en los datos

* **`Total` vs `Total Value`** en `SalesOrdersSummary`: `Total` es el importe de
  la línea; `Total Value` es el de la orden completa repetido en cada línea.
* **Muestras fuera del inventario comercial.** Todo lo que se clasifique como
  `NOT SELLABLE - SAMPLES ONLY` (por `NSS`, `NOT SELLABLE` o `SAMPLE` en el
  nombre o el SKU) se excluye del total y se reporta aparte. Con los datos reales
  esto explica la diferencia entre 226.73 y las 220.65 cajas 9L del libro del
  cliente.
* **El sufijo `NSS` vive en `product_id`, no en el nombre comercial.** El nombre
  de una muestra es idéntico al de la versión vendible, así que clasificar solo
  por nombre las cuela al inventario.
* **Empaque excluido.** SKU con prefijo `Z-` o cuyo nombre diga
  `Value Added Packaging`, `Gift Box`, `Outer Shipper` o `Slit Insert`.
* **Conversión a caja 9L.** 1 caja 9L = 9000 mL. Un 750 mL son 6 botellas por
  caja; un **200 mL son 24**, con otro factor.
* **Sumar en crudo y redondear una sola vez.** Redondear cada fila antes de sumar
  desvía el total: estas cajas 9L son fracciones periódicas (x/12) y el error se
  acumula (220.64 en vez de 220.65).

### `--account-map` (opcional)

CSV con columnas `account`, `salesperson`, `channel`. Sin él, vendedor y canal
(on/off premise) se estiman por heurística sobre el nombre de la cuenta y el
reporte lo declara como estimado.

### No hay margen bruto

Ninguno de los archivos crudos trae COGS por SKU, así que **el margen bruto no se
puede calcular**. Todas las cifras monetarias del reporte son ingreso bruto, y
el reporte lo dice. Donde antes se mostraba un "GM por caja" inventado, hoy se
muestra ingreso por caja 9L (ingreso ÷ cajas), que sí sale del dato.

---

## 4. Sttupa

Sin reporte automatizado todavía, y **sin datos demo a propósito**: no existe
ningún archivo real del cliente en el que basar la estructura, y un demo
inventado de punta a punta enseñaría un formato que después no coincidiría con
el real. Lo que ya está preparado: manual de diseño (`Designs/Design_sttupa.md`),
logotipos (`Imagenes_iconos/`) y fuentes (`Fonts/Font_sttupa/`).

---

## Cómo trata el sistema los datos que faltan

1. **Nunca se imprime `nan`, `NaT`, `None` ni `undefined`.** Cualquier forma de
   dato ausente se pinta como `—`, en HTML y en PDF.
2. **Nada se rellena con un número plausible.** Lo que no está en los archivos se
   reporta como ausente con su motivo. El margen bruto de Loco es el ejemplo.
3. **Lo que no se puede clasificar se muestra, no se descarta.** Un pedido de Club
   sin programa nombrado va a *Unclassified* con su motivo y **entra al total**,
   para que la suma siga cuadrando y quede rastro de qué revisar en el origen.
4. **Un archivo faltante falla en voz alta**, con el patrón que se buscaba y la
   carpeta donde se buscó.
