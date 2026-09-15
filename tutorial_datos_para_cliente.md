# Mini tutorial — Qué datos entregar para generar tus reportes
# Mini Tutorial — What Data to Provide to Generate Your Reports

> **ES:** Guía corta y práctica: qué archivos hay que entregar hoy, dónde ponerlos y
> qué comando ejecutar para obtener cada reporte con **tus datos reales**. Si lo que
> buscas es cómo *leer* los reportes una vez generados, eso está en
> [`tutorial_para_cliente.md`](tutorial_para_cliente.md). Si necesitas el detalle
> técnico de cada columna, está en [`DATOS_REQUERIDOS.md`](DATOS_REQUERIDOS.md).
>
> **EN:** A short, practical guide: which files to provide today, where to put them,
> and which command to run to get each report from **your real data**. To learn how
> to *read* the reports once generated, see
> [`tutorial_para_cliente.md`](tutorial_para_cliente.md). For the technical detail of
> every column, see [`DATOS_REQUERIDOS.md`](DATOS_REQUERIDOS.md).

---

## 0. Antes de empezar / Before you start

**ES:** Un solo paso, una sola vez. Abre PowerShell y activa el entorno:
**EN:** One step, once. Open PowerShell and activate the environment:

```powershell
& "E:\Users\1167486\AppData\Local\anaconda3\Scripts\conda.exe" shell.powershell hook | Out-String | Invoke-Expression
conda activate data_analytics_science
```

**ES:** ¿Quieres ver cómo funciona antes de entregar tus archivos? Todos los reportes
corren con datos de ejemplo sin que aportes nada:
**EN:** Want to see how it works before providing your files? Every report runs on
sample data without you providing anything:

```powershell
python Scripts/generate_report.py --brand sullivan --cadence unified --data-source demo --period-label "April 2026" --output-dir Output
```

> **ES:** Los datos de ejemplo son **inventados**. Sirven para ver el formato y
> comprobar que todo funciona, no para tomar decisiones.
> **EN:** The sample data is **synthetic**. Use it to see the format and confirm
> everything runs — never to make decisions.

---

## 1. ¿Qué reporte quieres? / Which report do you want?

| Reporte / Report | Archivos que entregas / Files you provide | Qué recibes / What you get |
| --- | --- | --- |
| **Sullivan — mensual / monthly** | 2 | Dashboard HTML + PDF de 8 páginas |
| **Sullivan — semanal / weekly** | 4 | Dashboard HTML + PDF de 5 páginas |
| **Sullivan — unificado / unified** ⭐ | 6 (los de arriba juntos / both sets) | Dashboard HTML + PDF de 7 páginas |
| **Loco Tequila USA** | 7 + 1 carpeta / + 1 folder | Dashboard HTML + PDF de 7 páginas |
| **Sttupa** | — | Todavía no disponible / Not available yet |

**ES:** ⭐ El **unificado** es el recomendado: contiene el mes y la semana en un solo
documento, sin repetir lo que ambos decían igual.
**EN:** ⭐ The **unified** report is the recommended one: it holds the month and the
week in a single document, without repeating what both said identically.

---

## 1b. ¿Dónde tienes tus archivos? (OneDrive, Google Drive, Cowork o Disco Local)
## 1b. Where are your files? (OneDrive, Google Drive, Cowork, or Local Disk)

**ES:** No hace falta que muevas tus archivos a la carpeta del proyecto. Puedes apuntar
directamente a donde los tengas guardados:
* **OneDrive:** Usa la ruta de tu carpeta sincronizada (ej. `C:\Users\<Usuario>\OneDrive - Empresa\Ventas\...`).
* **Google Drive:** Usa la letra de unidad asignada por Google Drive para escritorio (ej. `G:\Mi unidad\Reportes\...`) o tu carpeta de sincronización.
* **Cowork o Red Compartida:** Usa la ruta de red compartida o unidad asignada (ej. `Z:\Cowork\Datos\...` o `\\servidor\cowork\...`).
* **Disco local / Ingesta directa:** Pega la ruta local o arrastra el archivo a la terminal.

> 💡 **Tip en Windows:** Para obtener la ruta completa de un archivo o carpeta sin escribirla,
> mantén presionada la tecla `Shift`, haz clic derecho sobre el elemento en el Explorador
> de Windows y elige **"Copiar como ruta de acceso"** (*Copy as path*). Luego pégala entre comillas en el comando.

**EN:** You don't need to move your files into the project folder. You can point
directly to wherever they are stored:
* **OneDrive:** Use your locally synced folder path (e.g., `C:\Users\<User>\OneDrive - Organization\Sales\...`).
* **Google Drive:** Use your Google Drive for desktop mounted drive letter (e.g., `G:\My Drive\Reports\...`) or local sync folder.
* **Cowork or Shared Network:** Use the shared network path or mapped drive (e.g., `Z:\Cowork\Data\...` or `\\server\cowork\...`).
* **Local disk / Direct input:** Paste the local path or drag and drop the file into your terminal.

> 💡 **Windows Tip:** To get the full path without typing it, hold `Shift`,
> right-click the file or folder in Windows Explorer, and select **"Copy as path"**.
> Then paste it with quotation marks into the command.

---

## 2. Sullivan — reporte mensual / monthly report

**ES:** Entrega **2 archivos** que exportas de Commerce7:
**EN:** Provide **2 files** exported from Commerce7:

| # | Archivo / File | Cómo se llama normalmente / Typical name | ¿Obligatorio? |
| --- | --- | --- | --- |
| 1 | Ventas transaccionales / Transactional sales | `Apr_OrderSales.xlsx` | **Sí / Yes** |
| 2 | Reporte financiero / Financial report | `Apr_FinancialReport.xlsx` | Muy recomendado / Strongly recommended |

**ES — Por qué el segundo importa:** sin él el reporte se genera igual, pero **pierde
la reconciliación al centavo**, que es su principal argumento de confianza: la prueba
de que el total clasificado coincide exactamente con tu contabilidad.
**EN — Why the second matters:** without it the report still generates, but **loses
the cent-exact reconciliation** — the proof that the classified total matches your
accounting exactly.

```powershell
python Scripts/generate_report.py --brand sullivan --order-sales "C:\Ruta\A\Tus_Ventas.xlsx" --financial-report "C:\Ruta\A\Tu_Financiero.xlsx" --period-label "May 2026" --output-dir Output
```

**ES:** Acepta `.xlsx` y `.csv`. El texto de `--period-label` es el que aparece en la
portada, así que escríbelo como quieras verlo.
**EN:** Accepts `.xlsx` and `.csv`. The `--period-label` text is what appears on the
cover page, so write it the way you want it to read.

---

## Idioma / Language

**ES:** Los tableros HTML traen **los dos idiomas dentro del mismo archivo** y un
botón **ES / EN** en la esquina superior derecha. Le mandas un solo archivo a todo
el equipo y cada quien elige su idioma; no hay que pedir "la versión en español".

Los PDF sí salen en un idioma por archivo, porque un documento impreso no puede
alternar. Se elige al generar:

```powershell
python Scripts/generate_report.py --brand sullivan --cadence unified --lang es --data-source demo --period-label "April 2026" --output-dir Output
```

**EN:** The HTML dashboards embed **both languages in the same file**, with an
**ES / EN** button in the top-right corner. You send one file to the whole team
and each person picks their language.

PDFs are one language per file, since a printed document cannot switch. Choose it
when generating, with `--lang es` or `--lang en` (default `en`).

**ES:** Los nombres de canal y de producto **se quedan en inglés en los dos
idiomas** a propósito: `Tasting Room`, `Estate Club`, `Founder's Club`,
`Web / Ecommerce`, `Tock`, `Unclassified`, y los nombres de SKU y distribuidores.
Son los mismos nombres que usa Commerce7 y Park Street, así que quien revise el
reporte contra el sistema encuentra la misma etiqueta en los dos lados. Todo lo
demás —títulos, KPIs, tablas, notas y glosario— sí está traducido.

**EN:** Channel and product names **stay in English in both languages** on
purpose: they are the same names Commerce7 and Park Street use, so anyone
checking the report against the source system finds the same label on both
sides. Everything else is translated.

---

## 3. Sullivan — reporte semanal / weekly report

**ES:** Pon los **4 archivos en una misma carpeta**. Los nombres pueden traer la fecha
o variar; lo único que importa es que el nombre **contenga** la palabra clave:
**EN:** Put the **4 files in one folder**. Names may include dates or vary; all that
matters is that the name **contains** the keyword:

| # | Debe contener / Must contain | Archivo típico / Typical file | De dónde sale / Source |
| --- | --- | --- | --- |
| 1 | `orderreport` | `OrderReport_8.23.26.xlsx` | Commerce7 |
| 2 | `tock` | `Tock_8.23.26.xlsx` | Tock |
| 3 | `open po` | `Open PO's 8.23.26.xlsx` | Park Street |
| 4 | `depletion` | `Idig Depletions 8.26.xlsx` | Southern Glazer's (iDig) |

**ES — varias semanas:** si guardas cada semana en su propia subcarpeta, el
reporte las muestra TODAS con un selector de semana, dibuja la tendencia y
calcula el cambio contra la semana anterior. Apunta `--weekly-data-dir` a la
carpeta que las contiene:

```text
Mis_Semanas/
├── Week_2026_08_09/   <- los 4 archivos de esa semana
├── Week_2026_08_16/
└── Week_2026_08_23/
```

**EN — several weeks:** keep each week in its own subfolder and the report shows
them ALL, with a week selector, a real trend line and week-over-week change.
Point `--weekly-data-dir` at the folder that contains them.

```powershell
python Scripts/generate_report.py --brand sullivan --cadence weekly --weekly-data-dir "C:\Ruta\A\Mi_Semana" --output-dir Output
```

**ES — No escribas la fecha en ningún lado.** El periodo del reporte y el nombre del
archivo de salida se deducen de la fecha de pago más reciente que traiga tu propio
export. Así dos semanas distintas nunca se sobreescriben.
**EN — Don't type the date anywhere.** The report period and the output filename are
derived from the most recent payment date in your own export, so two different weeks
can never overwrite each other.

---

## 4. Sullivan — reporte unificado / unified report ⭐

**ES:** Los 2 archivos del mensual **más** la carpeta de los 4 del semanal:
**EN:** The 2 monthly files **plus** the folder with the 4 weekly ones:

```powershell
python Scripts/generate_report.py --brand sullivan --cadence unified --order-sales "C:\Ruta\Tus_Ventas.xlsx" --financial-report "C:\Ruta\Tu_Financiero.xlsx" --weekly-data-dir "C:\Ruta\Mi_Semana" --period-label "May 2026" --output-dir Output
```

**ES:** La parte semanal es **opcional**. Si no la entregas, el reporte sale completo
en su parte mensual y lo dice explícitamente, en vez de mostrar ceros que parecerían
reales.
**EN:** The weekly part is **optional**. If you don't provide it, the report is
complete on its monthly side and says so explicitly, rather than showing zeros that
would look real.

---

## 5. Loco Tequila USA

**ES:** Pon los **7 archivos y la subcarpeta** en una misma carpeta. Aquí los nombres
sí importan: el **inicio** del nombre es lo que identifica cada fuente.
**EN:** Put the **7 files and the subfolder** in one folder. Here names do matter: the
**beginning** of the name identifies each source.

| # | El nombre debe empezar así / Name must start with | De dónde sale / Source |
| --- | --- | --- |
| 1 | `1 - Supplier - Inventory` … `.xlsx` | Favorite Brands (TX) |
| 2 | `Inventory History` … `.xlsx` | Southern Glazer's (CA) |
| 3 | `InventoryByLocation` … `.csv` | Park Street |
| 4 | `SalesOrdersSummary` … `.csv` | Park Street |
| 5 | `YTD by Month` … `.xlsx` | Southern Glazer's (CA) |
| 6 | `orders_export_1` … `shopify.csv` | Shopify |
| 7 | `orders_export_1` … `memory.csv` | Memory (eventos / events) |
| 8 | Carpeta / Folder: **`FB Depletion Reports 2026`** | Favorite Brands (TX) |

**ES:** El nombre de esa carpeta **no es libre**: debe empezar con
`FB Depletion Reports` (el año puede ser cualquiera, y si tienes varias se usa la del
año más alto). Dentro pon los `.xlsx` semanales tal como llegan; se usa
automáticamente el más reciente.
**EN:** That folder name is **not flexible**: it must start with
`FB Depletion Reports` (any year; if you keep several, the highest year is used). Put
the weekly `.xlsx` files inside as they arrive; the most recent one is used
automatically.

```powershell
python Scripts/generate_report.py --brand loco_tequila --data-dir "C:\Ruta\A\Mis_Datos_Loco" --output-dir Output
```

**ES — Opcional pero valioso:** un CSV con tres columnas —`account`, `salesperson`,
`channel`— convierte al vendedor y al canal de *estimados* en *exactos*:
**EN — Optional but valuable:** a CSV with three columns — `account`, `salesperson`,
`channel` — turns salesperson and channel from *estimated* into *exact*:

```powershell
python Scripts/generate_report.py --brand loco_tequila --data-dir "C:\Ruta\Mis_Datos_Loco" --account-map "C:\Ruta\cuentas.csv" --output-dir Output
```

---

## 6. Cómo sabes que salió bien / How to know it worked

**ES:** Al final de cada corrida se imprime la lista de archivos generados. Además,
revisa esto:
**EN:** Each run prints the list of generated files at the end. Also check this:

| Reporte / Report | Debe aparecer / Must appear |
| --- | --- |
| Mensual y unificado / Monthly and unified | `Reconciliación al centavo: True` y `diferencia: $0.00` |
| Semanal / Weekly | El periodo detectado corresponde a tu semana / The detected period matches your week |
| Loco | El inventario coincide con tu libro maestro / Inventory matches your master book |
| Todos / All | Ningún `nan` ni `—` donde esperabas un número / No `nan` or `—` where you expected a number |

**ES:** Si ves un aviso `[AVISO]`, **no es un error**: es el sistema diciéndote qué
supuesto tomó o qué dato faltó. Vale la pena leerlo.
**EN:** If you see an `[AVISO]` warning, it's **not an error**: it's the system telling
you which assumption it made or which data was missing. Worth reading.

---

## 7. Lo que todavía no se puede / What isn't possible yet

**ES:** Tres cosas, con lo que hace falta para desbloquearlas:
**EN:** Three things, with what it takes to unblock them:

| Falta / Missing | Por qué / Why | Qué se necesita / What's needed |
| --- | --- | --- |
| **Margen bruto de Loco / Loco gross margin** | Ningún archivo trae el costo por producto / No file carries per-product cost | Un archivo con el COGS por SKU / A file with cost of goods per SKU |
| **Events, Corporate y Friends & Family en el semanal** | Falta leer el archivo de etiquetas de la semana / The weekly tag file isn't read yet | Nada de tu parte: es trabajo nuestro / Nothing from you: it's on us |
| **Sttupa** | No hay ningún archivo de referencia / No reference file exists | Un export real, aunque sea de un mes / One real export, even a single month |

> **ES — Importante:** mientras no exista el COGS por SKU, **todas** las cifras
> monetarias de Loco Tequila son **ingreso bruto, no margen**. El reporte lo dice en
> la portada y dedica una página a explicarlo. No inventamos márgenes.
>
> **EN — Important:** until per-SKU cost of goods exists, **all** monetary figures for
> Loco Tequila are **gross revenue, not margin**. The report states this on the cover
> and devotes a page to explaining it. We do not invent margins.

---

## 8. Resumen en una hoja / One-page summary

**ES:** Recorta esto y tenlo a mano.
**EN:** Cut this out and keep it handy.

```
SULLIVAN MENSUAL      2 archivos  ->  --order-sales  +  --financial-report
SULLIVAN SEMANAL      1 carpeta   ->  --weekly-data-dir      (4 archivos dentro)
SULLIVAN UNIFICADO    ambos       ->  --cadence unified
LOCO TEQUILA USA      1 carpeta   ->  --data-dir             (7 archivos + 1 subcarpeta)
                                      --account-map          (opcional, mejora la precisión)

Todos aceptan  --output-dir  y  --format all | html | pdf
Sin datos propios, todos corren con  --data-source demo
```

**ES:** Tus archivos **nunca se distribuyen**: las carpetas de datos y reportes del
cliente están excluidas del paquete que se comparte.
**EN:** Your files are **never distributed**: client data and report folders are
excluded from the shareable package.
