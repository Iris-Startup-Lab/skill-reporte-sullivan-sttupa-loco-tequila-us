# Guía Maestra de Datos de Commerce7 — Sullivan Estate (Abril)

> **Fuentes integradas:**  
> 1. `Client_Data\Sullivan_data\April_C7_Data_Guide.xlsx` (Guía de Reglas de Negocio, Clasificación y Checklist).  
> 2. `Client_Data\Sullivan_data\Commerce7_April_Report_Connections_Google_Docs.pdf` / `.docx` (Especificación Técnica de Cruce de Columnas y Volúmenes Auditados).  
>
> **Objetivo:** Manual definitivo de ingeniería de datos para transformar, clasificar, validar y reconciliar los 5 reportes de exportación de Commerce7 en un único reporte consolidado de ventas DTC.

---

## 📌 1. Principio Fundamental y Arquitectura de Conexión

> [!CAUTION]
> ### REGLA DE ORO: NUNCA SUMAR LOS REPORTES ENTRE SÍ
> Los 5 archivos exportados representan **las mismas ventas del mes de abril desde distintas dimensiones analíticas** (transaccional, financiera, por canal, por club o por etiquetas). Sumar los totales de los archivos generaría una duplicación masiva y ficticia de ingresos.

### Flujo Canónico de Datos
$$\begin{matrix}
\mathbf{Apr\_OrderSales} & \longrightarrow & \mathbf{Apr\_FinancialReport} & \longrightarrow & \mathbf{Apr\_SalesbyChannel} & \longrightarrow & \mathbf{Apr\_SalesbyClub} \\
\text{(Datos Crudos / Nivel Ítem)} & & \text{(Validación Financiera)} & & \text{(Control de Canales)} & & \text{(Desglose de Club)}
\end{matrix}$$

* **Dataset Base:** `Apr_OrderSales` (o `Apr_OrderDetails`) contiene el detalle transaccional más granular (línea por línea de producto).
* **Validación Financiera:** `Apr_FinancialReport` contiene las mismas **430 órdenes y 583 renglones de producto** para verificar subtotales, impuestos, fletes y descuentos.
* **Controles Agregados:** `Apr_SalesbyChannel`, `Apr_SalesbyClub` y `Apr_SalesbyTag` sirven exclusivamente como puntos de control (*benchmarks*) para validar que la clasificación dé exactamente los mismos importes.

---

## 🔗 2. Conexión y Cruce de Columnas entre Reportes (*Joins*)

| Conexión entre Reportes | Columna en `OrderSales` | Columna en el Otro Reporte | Tipo de Coincidencia | Propósito y Regla Técnica |
| :--- | :--- | :--- | :---: | :--- |
| **`OrderSales` $\leftrightarrow$ `FinancialReport`** | `Order Number` | `Order Number` | Idéntico | Identifica unívocamente la orden. |
| **`OrderSales` $\leftrightarrow$ `FinancialReport`** | `SKU` | `SKU` | Idéntico | Identifica el producto específico dentro de la orden. |
| **`OrderSales` $\leftrightarrow$ `FinancialReport`** | `Quantity` / `Price` / `Product Title` | `Quantity` / `Price` / `Product Title` | Idéntico | **Desambiguación de ítems repetidos** (ver regla abajo). |
| **`OrderSales` $\rightarrow$ `SalesbyChannel`** | `Channel` | `Channel` | Idéntico | Agrupa en los 4 canales origen: `POS`, `Web`, `Club` e `Inbound`. |
| **`OrderSales` $\rightarrow$ `SalesbyClub`** | `Club Title` | `Club` | **Distinto nombre** | Permite cruzar y validar el desglose de ventas del canal Club. |
| **`OrderSales` $\leftrightarrow$ `FinancialReport` (Club)** | `Club Title` | `Club Name` | **Distinto nombre** | Vincula cada orden con la membresía de club correspondiente. |

### ⚠️ Regla Crítica de Desambiguación para el Cruce (*Matching Rule*)
Aunque `Order Number` identifica la orden y `SKU` identifica el producto, en el periodo de abril la combinación `Order Number + SKU` **se repite en 9 casos** (órdenes con renglones separados del mismo producto, por ejemplo promociones, empaques o tarifas diferenciadas).

Para lograr un emparejamiento exacto 1 a 1 entre `Apr_OrderSales` y `Apr_FinancialReport`, se debe utilizar la **clave compuesta**:
$$\text{Clave Compuesta} = \mathbf{Order\ Number} + \mathbf{SKU} + \mathbf{Quantity} + \mathbf{Price}\;(\text{o }\mathbf{Product\ Title})$$

---

## 🗂️ 3. Hoja por Hoja de `April_C7_Data_Guide.xlsx`

### 3.1. Hoja: `Quick Guide` (Guía Rápida de Clasificación)

Define el mapeo directo de cada categoría final y el orden secuencial estricto de ejecución.

#### Mapeo de Categorías de Ventas
| Categoría de Venta | Cómo Identificarla en los Datos | Regla de Negocio |
| :--- | :--- | :--- |
| **Telesales** | `Channel = "Inbound"` **Y** sin tags de `Event`, `Corporate` o `Friends & Family` | Todas las ventas restantes de `Inbound` son consideradas Telesales. |
| **Event** | `Channel = "Inbound"` **Y** `Tag = "Event"` | Se extrae de `Inbound` y se reporta en su propia categoría como **Event**. |
| **Corporate** | `Channel = "Inbound"` **Y** `Tag = "Corporate"` | Se extrae de `Inbound` y se reporta en su propia categoría como **Corporate**. |
| **Friends & Family** | `Channel = "Inbound"` **Y** `Tag = "Friends & Family"` | Se extrae de `Inbound` y se reporta como **Friends & Family**. |
| **Tasting Room** | `Channel = "POS"` | Todas las ventas del canal `POS` corresponden íntegramente a **Tasting Room**. |
| **Estate Club** | `Channel = "Club"` **Y** `Club = "Estate"` | Se reporta de forma independiente y separada de Founder's Club. |
| **Founder's Club** | `Channel = "Club"` **Y** `Club = "Founder's"` | Se reporta de forma independiente y separada de Estate Club. |
| **Web / Ecommerce** | `Channel = "Web"`, excluyendo transacciones de `Tock` | $\text{Web/Ecommerce} = \text{Total Web} - \text{Tock}$. |

#### Orden de Clasificación Obligatorio (Paso a Paso)
1. **Revisar tags de Inbound primero:** Extraer `Event`, `Corporate` y `Friends & Family` antes de catalogar el remanente de Inbound como `Telesales`.
2. **Separar Tock de Web:** Identificar órdenes Tock dentro del canal `Web`, reportarlas bajo `Tock` y sustraerlas del total de `Web / Ecommerce`.
3. **Asignar POS:** Asignar todo el canal `POS` directamente a `Tasting Room`.
4. **Dividir Club:** Usar el nombre del club para separar `Estate Club` de `Founder's Club`.
5. **Exclusividad categórica:** Cada orden (`Order ID` / `Order Number`) debe aparecer únicamente en una categoría final.
6. **Reconciliación:** La suma de las categorías finales debe cuadrar con el alcance de *Net Sales* del reporte financiero.

---

### 3.2. Hoja: `Classification Logic` (Lógica Jerárquica en Cascada)

> [!IMPORTANT]
> **Evaluación en Cascada (Top to Bottom):**  
> Las reglas se aplican en orden estricto de prioridad (1 a 9). La **primera regla que coincida** define la categoría final.

#### Matriz de Prioridades
| Prioridad | Channel | Tag / Identificador | Club | Categoría Final | Regla del Ingeniero de Datos |
| :---: | :--- | :--- | :--- | :--- | :--- |
| **1** | `Inbound` | `Event` | Cualquiera / vacío | **Event** | Si `Channel = Inbound` y el tag incluye `Event`, clasificar como Event. |
| **2** | `Inbound` | `Corporate` | Cualquiera / vacío | **Corporate** | Si `Channel = Inbound` y el tag incluye `Corporate`, clasificar como Corporate. |
| **3** | `Inbound` | `Friends & Family` | Cualquiera / vacío | **Friends & Family** | Si `Channel = Inbound` y el tag incluye `Friends & Family`, clasificar como Friends & Family. |
| **4** | `Inbound` | Ninguno de los 3 anteriores | Cualquiera / vacío | **Telesales** | Todo el remanente de `Inbound` se clasifica como Telesales. |
| **5** | `Web` | `External Order Vendor = "Tock"` | Cualquiera / vacío | **Tock** | Órdenes Tock se reportan por separado; se excluyen de Web/Ecommerce. |
| **6** | `Web` | Sin identificador Tock | Cualquiera / vacío | **Web / Ecommerce** | Todo el remanente de `Web` se clasifica como Web / Ecommerce. |
| **7** | `POS` | Cualquiera / vacío | Cualquiera / vacío | **Tasting Room** | Todas las órdenes de `POS` se clasifican como Tasting Room. |
| **8** | `Club` | Cualquiera / vacío | Contiene `Estate` | **Estate Club** | Canal `Club` + nombre `Estate` clasifica como Estate Club. |
| **9** | `Club` | Cualquiera / vacío | Contiene `Founder's` | **Founder's Club** | Canal `Club` + nombre `Founder's` clasifica como Founder's Club. |

#### Fórmulas de Cálculo y Control
* **Telesales:** $\text{Telesales} = \text{Inbound Total} - \text{Event} - \text{Corporate} - \text{Friends \& Family}$
* **Web / Ecommerce:** $\text{Web / Ecommerce} = \text{Web Total} - \text{Tock}$
* **Total DTC Clasificado:**
  $$\text{Total DTC} = \text{Telesales} + \text{Event} + \text{Corporate} + \text{Friends \& Family} + \text{Tock} + \text{Web/Ecommerce} + \text{Tasting Room} + \text{Estate Club} + \text{Founder's Club}$$
* **Control:** $\text{Total DTC Clasificado} \equiv \text{Venta Total de Control (Net Sales Abril)}$. Tolerancia cero de discrepancias.

---

### 3.3. Hoja: `Reports to Use` (Catálogo Funcional de Archivos)

| Archivo | Rol Operativo | Regla Crítica | Campos Clave |
| :--- | :--- | :--- | :--- |
| **`Apr_FinancialReport`** | Control financiero y reconciliación | Comparar totales del mismo tipo (**Net Sales vs Net Sales**, Total Revenue vs Total Revenue). Separar fletes, impuestos, propinas y reembolsos. | `Net sales`, `discounts`, `refunds`, `shipping`, `tax`, `total revenue`. |
| **`Apr_OrderSales`** | Dataset principal a nivel ítem | Validar que cada fila es un ítem de orden. Agrupar por `Order Number` para métricas a nivel orden. | `Order Number`, `SKU`, `Channel`, `Club Title`, `External Order Vendor`, `Quantity`, `Price`, `SubTotal`. |
| **`Apr_SalesbyChannel`** | Resumen agregado por canal | Punto de control macro para validar que la suma de subtotales cuadre con `POS`, `Web`, `Club` e `Inbound`. | `Channel`, `Order Count`, `Sub Total`, `Total`. |
| **`Apr_SalesbyClub`** | Resumen de membresías de Club | Control para auditar la separación de Estate vs Founder's. **No sumar sobre el total general.** | `Club`, `Order Count`, `Sub Total`, `Total`. |
| **`Apr_SalesbyTag`** | Resumen por etiquetas de orden | Control para auditar tags superpuestos. | `Order Tag`, `Order Count`, `Sub Total`. |

#### 🎯 Lo que desea el cliente como Producto Final ("The finished report should show")
El objetivo del cliente no es mantener los 5 reportes aislados, sino transformarlos en **un único reporte final de ventas consolidado y exacto** (*"one accurate sales report"*). 

Según especifica explícitamente la hoja **`Reports to Use`** del Excel, el reporte terminado que desea el cliente debe mostrar las siguientes **9 categorías finales**:
1. **Telesales**
2. **Event**
3. **Corporate**
4. **Friends & Family**
5. **Tock**
6. **Web / Ecommerce** *(después de sustraer Tock)*
7. **Tasting Room**
8. **Estate Club**
9. **Founder's Club**

---

### 3.4. Hoja: `Final Checks` (Lista de Chequeo Previa a Publicación)

1. **Same reporting period:** Todas las exportaciones deben coincidir en rango de fechas y zona horaria.
2. **One Order ID:** Cada orden debe contabilizarse exactamente una vez tras resolver filas de ítems.
3. **Inbound split:** `Event`, `Corporate` y `Friends & Family` deben sustraerse antes de calcular `Telesales`.
4. **Tock subtraction:** `Tock` se desglosa por separado y se resta de `Web / Ecommerce`.
5. **POS mapping:** Cada transacción `POS` se asigna a `Tasting Room`.
6. **Club split:** Cada orden de `Club` debe ir a `Estate` o `Founder's`; transacciones anómalas (como *Admin/POS Order Marked as Club*) deben listarse para revisión.
7. **Exclusive categories:** Ninguna orden puede figurar en más de una categoría final.
8. **Refunds:** Los reembolsos deben ser tratados de forma uniforme en signo y período contable.
9. **Like-for-like totals:** Comparar estrictamente *Net Sales* contra *Net Sales*.
10. **Final reconciliation:** La suma de las 9 categorías debe cuadrar al centavo contra el reporte financiero.

---

### 3.5. Hoja: `Sources` (Referencias Normativas)
* **Reglas de negocio:** Validadas y provistas por **Maya**.
* **Documentación oficial de Commerce7:**
  * [*Sales Summary Report*](https://documentation.commerce7.com/sales-summary-report): Agrupaciones por canal, perfil POS, club y tags.
  * [*Order Channels*](https://documentation.commerce7.com/what-are-order-channels-and-can-i-add-additional-channels): Definiciones de canal.
  * [*Sales Attributes*](https://documentation.commerce7.com/assigning-sales-attributes): Atributos de venta vs canal de origen.
  * [*Reports Overview*](https://documentation.commerce7.com/reports-1): Criterios de reembolsos y metodologías de cálculo.

---

## 📊 4. Cifras y Volúmenes Reales Auditados — Abril 2026

Datos auditados directamente de los archivos de exportación de Sullivan:

### 4.1. Resumen por Canal Original (`Apr_SalesbyChannel`)
| Canal Original | Órdenes (`Order Count`) | % Ventas | SubTotal (Venta Neta) | Tax Total | Ship Total | Total Facturado |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **POS** | 61 | 11.69% | $51,196.00 | $3,344.10 | $800.58 | $55,340.68 |
| **Web** | 56 | 1.94% | $8,705.00 | $483.82 | $0.00 | $9,188.82 |
| **Club** | 295 | 85.63% | $370,445.55 | $27,654.40 | $7,242.59 | $405,342.54 |
| **Inbound** | 18 | 0.74% | $3,033.50 | $251.35 | $218.00 | $3,502.85 |
| **TOTALES** | **430** | **100%** | **$433,380.05** | **$31,733.67** | **$8,261.17** | **$473,374.89** |

### 4.2. Clasificación Confirmada de Ventas (Abril)
| Categoría Final | Regla Aplicada en Abril | Órdenes Reales | SubTotal Venta Neta | Observaciones Clave |
| :--- | :--- | :---: | :---: | :--- |
| **Telesales** | `Channel = "Inbound"` | **18** | $3,033.50 | En abril, ninguna orden Inbound tuvo tag de Event o Corporate. |
| **Tasting Room** | `Channel = "POS"` | **61** | $51,196.00 | 100% del canal POS. |
| **Tock** | `Channel = "Web"` & `Vendor = "Tock"` | **56** | $8,705.00 | Todas las órdenes Web de abril fueron reservaciones vía Tock. |
| **Web sin Tock** | $\text{Total Web} - \text{Tock}$ | **0** | $0.00 | No hubo compras tradicionales directas en el portal web. |
| **Club (Total)** | `Channel = "Club"` | **295** | $370,445.55 | Desglosado abajo por tipo de membresía. |
| **TOTAL DTC** | **Suma de las categorías** | **430** | **$433,380.05** | **Cuadre perfecto con FinancialReport (583 líneas)**. |

### 4.3. Auditoría del Desglose de Club (`Apr_SalesbyClub`)
* **Estate Club (95 órdenes | $51,759.05):**
  * `Estate 4 Bottle`: 87 órdenes ($45,231.05 Subtotal).
  * `Estate 6 Bottle`: 8 órdenes ($6,528.00 Subtotal).
* **Founder's Club (197 órdenes | $315,888.50):**
  * `Founder's 3 Bottle`: 101 órdenes ($97,108.50 Subtotal).
  * `Founder's Half Case`: 77 órdenes ($138,290.00 Subtotal).
  * `Founder's Single Case`: 17 órdenes ($63,690.00 Subtotal).
  * `Founder's Double Case`: 2 órdenes ($16,800.00 Subtotal).
* ⚠️ **Caso Especial de Auditoría:**
  * `Admin/POS Order Marked as Club`: **3 órdenes** ($2,798.00 Subtotal).  
    *Nota:* Corresponde al punto #6 del Checklist (*unexpected blanks/names listed for review*). Estas órdenes se marcaron manualmente como club desde el panel administrativo de POS.

---

## 💻 5. Implementación de Referencia en Python (`pandas`)

Snippet optimizado con manejo de la clave compuesta y la regla de Tock:

```python
import pandas as pd
import numpy as np

def process_sullivan_c7(df_orders: pd.DataFrame) -> pd.DataFrame:
    """
    Clasifica y desglosa las transacciones de Commerce7 según la Guía C7 de Sullivan.
    df_orders: DataFrame proveniente de Apr_OrderSales.xlsx
    """
    # 1. Normalizar textos
    channel = df_orders['Channel'].fillna('').str.strip().str.lower()
    tags = df_orders['Order Tags'].fillna('').astype(str) if 'Order Tags' in df_orders else pd.Series('', index=df_orders.index)
    vendor = df_orders['External Order Vendor'].fillna('').str.strip().str.lower()
    club_title = df_orders['Club Title'].fillna('').str.strip()

    # 2. Condiciones en orden jerárquico (Prioridades 1 a 9)
    cond_event = (channel == 'inbound') & tags.str.contains('Event', case=False)
    cond_corp = (channel == 'inbound') & tags.str.contains('Corporate', case=False)
    cond_ff = (channel == 'inbound') & tags.str.contains('Friends & Family|Friends and Family', case=False)
    cond_tele = (channel == 'inbound')
    
    cond_tock = (channel == 'web') & (vendor == 'tock')
    cond_web = (channel == 'web')
    
    cond_pos = (channel == 'pos')
    
    cond_estate = (channel == 'club') & club_title.str.contains('Estate', case=False)
    cond_founders = (channel == 'club') & club_title.str.contains("Founder", case=False)
    cond_club_review = (channel == 'club') # Casos anómalos como Admin/POS Marked as Club

    conditions = [
        cond_event,
        cond_corp,
        cond_ff,
        cond_tele,
        cond_tock,
        cond_web,
        cond_pos,
        cond_estate,
        cond_founders,
        cond_club_review
    ]

    choices = [
        'Event',
        'Corporate',
        'Friends & Family',
        'Telesales',
        'Tock',
        'Web / Ecommerce',
        'Tasting Room',
        'Estate Club',
        "Founder's Club",
        'Club - Review (Admin/POS)'
    ]

    df_orders['final_sales_category'] = np.select(conditions, choices, default='Unassigned')
    return df_orders
```
