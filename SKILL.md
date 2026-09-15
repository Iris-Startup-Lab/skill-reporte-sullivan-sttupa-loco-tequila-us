---
name: reporte-sullivan-sttupa-loco-tequila-us
description: Generador agnóstico de reportes ejecutivos (Dashboard HTML + Reporte PDF) para marcas de lujo y hospitalidad (Sullivan Rutherford Estate, Loco Tequila USA, Sttupa). Flujo interactivo con selección de marca, cadencias mensual o semanal, elección de datos demo o personalizados (.xlsx / .csv), reconciliación financiera automática y ordenamiento descendente estricto.
---

# Skill: Generador Agnóstico de Reportes Ejecutivos Multimarca

Esta skill orquesta la creación automatizada de reportes directivos y dashboards interactivos para un ecosistema de 3 marcas de lujo y hospitalidad:

1. **Sullivan Rutherford Estate** (Bodega / Viñedo, Napa Valley, CA, EEUU) &mdash; **[ACTIVO / PRODUCCIÓN]**
   * **Cadencia Mensual:** Reconciliación DTC al centavo ($461,362.44 con $0.00 de discrepancia), Club Deep Dive y mapa coroplético de envíos con centroides ZIP.
   * **Cadencia Semanal:** Consolidación de 9 canales DTC, Tock, Open POs de Park Street (balance, aging semaforizado >30d) y Depletions de Southern Glazer's (iDig 9L cases).
2. **Loco Tequila USA** (Destilados de ultra-lujo, Jalisco / EEUU) &mdash; **[DEMO DIRECTIVO ACTIVO]**
   * Dashboard directivo de 8 paneles (`summary_7.html`) con los tokens de `Design_loco_tequila.md`: KPIs del strip, tendencia y MoM, mix de vendedores, mix de productos (donut y GM/9L), cuentas clave, distribuidores mayoristas, heatmap de cadencia, sparklines, desempeño semanal (toggle 12w/YTD) e inventario on-hand CA vs TX.
3. **Sttupa** (Hospitalidad & Experiencias boutique) &mdash; **[PRÓXIMAMENTE]**
   * Activos preparados en `Designs/Design_sttupa.md`, tipografías en `Fonts/Font_sttupa/` y logotipos en `Imagenes_iconos/`.

---

## 0. REGLA INMUTABLE DE PRIMER TURNO: IDIOMA Y MARCA (OBLIGATORIO)

> **ATENCIÓN:** NUNCA emitas únicamente la pregunta de marca en tu primer mensaje.
> El cliente opera en dos idiomas (inglés o español). Sigue esta bifurcación sin excepción.

El idioma que se fije aquí gobierna **las dos cosas**, y no son la misma:

1. **La conversación**: toda la sesión continúa en ese idioma.
2. **Los entregables**: se traduce a `--lang es|en` al ejecutar
   `Scripts/generate_report.py`. Fija el PDF y el idioma con el que **abre** el
   dashboard HTML (que de todos modos lleva selector ES/EN embebido, así que un
   solo archivo sirve a los dos públicos).

### Caso A: El usuario inició explícitamente escribiendo en INGLÉS

Si el usuario escribió su prompt o consulta en inglés:

* Fija el idioma en **inglés** (`en`) y usa `--lang en`.
* Pregunta inmediatamente la marca en inglés:
  > *"Which of our 3 brands would you like to build the report for?*
  > ***1. Sullivan Rutherford Estate*** *— historic vineyard & winery in Rutherford, Napa Valley. Monthly, weekly or unified report.*
  > ***2. Loco Tequila USA*** *— terroir tequila, US market. Executive YTD report.*
  > ***3. Sttupa*** *— boutique hospitality & experiences. Coming soon."*

### Caso B: El usuario inició en ESPAÑOL, con un saludo o solo invocó la skill

Si el usuario escribió en español, saludó, o únicamente introdujo el comando de la skill:

* **ESTÁ TERMINANTEMENTE PROHIBIDO preguntar solo la marca sin preguntar el idioma.**
* **Tu primer mensaje DEBE abrir preguntando el idioma:**

> *"¡Bienvenido! / Welcome!*
>
> ***1. ¿Prefieres que continuemos en español o en inglés? / Would you prefer to continue in Spanish or English?***
>
> ***2. ¿Para cuál de nuestras 3 marcas quieres el reporte? / Which of our 3 brands is the report for?***
>
> * ***Sullivan Rutherford Estate*** *(viñedo y bodega histórica, Rutherford, Napa Valley — reporte mensual, semanal o unificado)*
> * ***Loco Tequila USA*** *(tequila de terruño, mercado estadounidense — reporte directivo YTD)*
> * ***Sttupa*** *(hospitalidad y experiencias boutique — próximamente)*"

*(El usuario puede confirmar idioma y marca en un solo mensaje o paso a paso. Una
vez confirmado el idioma, toda la sesión continúa en ese idioma.)*

### Qué NO se traduce, y por qué

La **taxonomía del reporte se queda en inglés en los dos idiomas**: las 9
categorías de la cascada (`Tasting Room`, `Estate Club`, `Founder's Club`,
`Web / Ecommerce`, `Tock`, `Inbound Telesales`, `Event`, `Corporate`,
`Friends & Family`, `Unclassified`), los nombres de SKU, de distribuidores y de
cuentas. Son los nombres con los que el equipo del cliente cuadra contra
Commerce7 y Park Street: si el reporte dijera "Sala de Cata" y el sistema dice
"Tasting Room", quien audita pierde el hilo. Decisión del usuario, registrada en
`to_do.md`.

Sí se traduce todo lo demás: títulos, pestañas, secciones, etiquetas de KPI,
encabezados de tabla, ejes y leyendas, notas metodológicas, advertencias y
glosario. El glosario **explica en español** cada categoría sin renombrarla.

---

## 🏛️ Reglas de Oro de Visualización y Gobernanza

1. **Gobernanza de Diseño (`Designs/`):**  
   El cliente propone la estructura de métricas y componentes en `Client_Reports`, pero el diseño lo gobernamos nosotros basándonos estrictamente en los manuales normativos (`Design_sullivan.md`, `Design_loco_tequila.md`, `Design_sttupa.md`), tipografías (`Fonts/`) y logotipos oficiales (`Imagenes_iconos/`).
2. **Regla Estricta de Ordenamiento en Gráficas de Barras (Storytelling with Data):**  
   En todos los reportes (HTML y PDF, para todas las marcas), **todas las gráficas de barras (horizontales o verticales: canales, productos/SKUs, vendedores, estados, cuentas, distribuidores o aging) deben estar ordenadas estrictamente de mayor a menor (orden descendente por importe o volumen)**.
3. **Presentación Ejecutiva Limpia:**  
   Queda prohibido mostrar nombres de archivos de código o rutas internas (`Designs/...md`) en los encabezados o badges visibles para el cliente. Los badges deben reflejar sellos y fechas oficiales de corte (ej. `Official Weekly Cutoff · Aug 23, 2026`).

---

## 🧭 Flujo de Interacción Obligatorio

Cualquier agente (Antigravity, OpenCode, Claude Code) o usuario que active esta skill debe seguir este flujo interactivo:

```
┌─────────────────────────────────────────────────────────────┐
│          PASO 1: PREGUNTAR POR LA MARCA                     │
│  ¿Para qué marca deseas generar el reporte?                 │
│  1) Sullivan Rutherford Estate                              │
│  2) Loco Tequila USA                                        │
│  3) Sttupa                                                  │
└──────────────────────────────┬──────────────────────────────┘
                               │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
   [ Sttupa ]            [ Loco Tequila ]         [ Sullivan ]
        │                       │                       │
        ▼                       ▼                       ▼
 Responder:            Ejecutar Demo           ┌───────────────────────────────────────┐
 "Próximamente"        Directivo YTD           │ PASO 2: PREGUNTAR POR CADENCIA        │
                       (Scripts/generate_      │ 1) Mensual (DTC Reconciliado)         │
                       report.py --brand       │ 2) Semanal (DTC + Distribución + POs) │
                       loco_tequila)           │ 3) Unificado (recomendado)            │
                                               └───────────────────┬───────────────────┘
                                                                   │
                                                                   ▼
                                               ┌─────────────────────────────────────────────────────────────┐
                                               │ PASO 3: PREGUNTAR POR FUENTE Y UBICACIÓN DE DATOS           │
                                               │ 1) Datos Demo predeterminados (sintéticos)                  │
                                               │ 2) Proporcionar datos propios del cliente:                  │
                                               │    a) OneDrive (carpeta sincronizada localmente)            │
                                               │    b) Google Drive (unidad montada o sincronizada)          │
                                               │    c) Carpeta de Cowork / Red compartida                    │
                                               │    d) Ingesta directa (arrastrar / pegar rutas locales)     │
                                               └───────────────────────────┬─────────────────────────────────┘
                                                                           │
                                                                           ▼
                                               ┌─────────────────────────────────────────────────────────────┐
                                               │ PASO 4: EJECUCIÓN TÉCNICA (CONDA)                           │
                                               │ Scripts/generate_report.py                                  │
                                               └───────────────────────────┬─────────────────────────────────┘
                                                                           │
                                                                           ▼
                                               ┌─────────────────────────────────────────────────────────────┐
                                               │ PASO 5: ENTREGA DE RESULTADOS                               │
                                               │ Dashboard HTML + Reporte PDF                                │
                                               └─────────────────────────────────────────────────────────────┘
```

### 📋 Detalle del Paso 3: Pregunta de Fuente y Ubicación de Datos

Cuando el usuario requiera generar reportes con datos propios (o al consultar la fuente de datos tanto en Sullivan como en Loco Tequila), el agente debe ofrecer las opciones de origen para facilitar la localización de los archivos:

**En Español:**
> *"¿Qué fuente de datos deseas utilizar para generar el reporte?*
> 1. **Datos Demo predeterminados** *(pruebas rápidas con datos sintéticos sin requerir archivos reales)*
> 2. **Conectarse a OneDrive** *(indica la ruta de la carpeta sincronizada en tu equipo, ej. `C:\Users\<usuario>\OneDrive - Empresa\...`)*
> 3. **Conectarse a Google Drive** *(indica la ruta de tu unidad o carpeta montada, ej. `G:\Mi unidad\...` o `G:\Shared drives\...`)*
> 4. **Carpeta de Cowork / Red local compartida** *(indica la ruta local o compartida del espacio de Cowork, ej. `Z:\Cowork\...` o `\\servidor\cowork\...`)*
> 5. **Ingresar directamente los archivos** *(arrastra o pega las rutas a tus archivos `.xlsx` o `.csv` o a tu carpeta de datos)*"

**En Inglés:**
> *"Which data source would you like to use for the report?*
> 1. **Default Demo Data** *(quick synthetic test data without needing real files)*
> 2. **OneDrive folder** *(provide your locally synced OneDrive directory path, e.g., `C:\Users\<user>\OneDrive - Organization\...`)*
> 3. **Google Drive** *(provide your mounted Google Drive unit or local sync path, e.g., `G:\My Drive\...` or `G:\Shared drives\...`)*
> 4. **Cowork / Shared Network folder** *(provide your local or shared Cowork folder path, e.g., `Z:\Cowork\...` or `\\server\cowork\...`)*
> 5. **Direct file input** *(drag & drop or paste file paths to your `.xlsx` or `.csv` files or data folder)*"

*💡 **Tip para el usuario en Windows:** Para obtener la ruta exacta sin escribirla a mano, mantén presionada la tecla `Shift`, haz clic derecho sobre el archivo o carpeta en el Explorador de Windows y selecciona **"Copiar como ruta de acceso"** (Copy as path).*

Una vez obtenida la ruta (sea de OneDrive, Google Drive, Cowork o carpeta local), el agente la pasa entre comillas a los argumentos correspondientes (`--data-dir`, `--weekly-data-dir`, `--order-sales`, `--financial-report`).

---

## 💻 Comandos de Ejecución por Entorno (Conda `data_analytics_science`)

Todos los comandos requieren ejecutarse dentro del entorno de Python **`data_analytics_science`**:

```powershell
# 1. Cargar hook de Conda y activar ambiente
& "E:\Users\1167486\AppData\Local\anaconda3\Scripts\conda.exe" shell.powershell hook | Out-String | Invoke-Expression
conda activate data_analytics_science
```

### 1. Sullivan Rutherford Estate

* **Reporte Mensual Demo (DTC Reconciliado al centavo):**
  ```powershell
  python Scripts/generate_report.py --brand sullivan --data-source demo --period-label "April 2026" --output-dir Output
  ```

* **Reporte Mensual con Datos Propios (CSV o Excel):**
  ```powershell
  python Scripts/generate_report.py --brand sullivan --order-sales "Ruta/Al/OrderSales.csv" --financial-report "Ruta/Al/Financiero.xlsx" --period-label "Abril 2026" --output-dir Output
  ```

* **Reporte Semanal (DTC + Distribución Park Street + Aging de POs + Depletions iDig):**
  ```powershell
  python Scripts/generate_report.py --brand sullivan --cadence weekly --output-dir Output
  ```
  **Varias semanas:** se descubren TODAS las carpetas de semana que haya bajo la
  ruta indicada (`Week_2026_08_16/`, `Week_2026_08_23/`, ...). El dashboard trae
  selector de semana que repinta el tablero completo, la tendencia dibuja la
  serie real y el WoW compara contra la semana anterior. El PDF documenta la más
  reciente y añade una página de tendencia (5 páginas con una semana, 6 con
  varias).

* **Reporte Unificado — recomendado (las dos cadencias en un solo HTML):**
  ```powershell
  python Scripts/generate_report.py --brand sullivan --cadence unified --data-source demo --period-label "April 2026" --output-dir Output
  ```
  Seis pestañas. Los bloques que las dos cadencias decían igual aparecen **una
  sola vez** (la mezcla de canales, con selector mensual/semanal; el desglose de
  Club; la tabla de no clasificados; el encabezado y la tira de KPIs), y se
  conserva lo exclusivo: mapa Albers con puntos por código postal y
  reconciliación al centavo del mensual, más cuentas por cobrar, aging y
  depletions del semanal.

### 2. Loco Tequila USA

* **Dashboard Ejecutivo con datos reales (bajo `Design_loco_tequila.md`):**
  ```powershell
  python Scripts/generate_report.py --brand loco_tequila --output-dir Output
  python Scripts/generate_report.py --brand loco_tequila --data-dir "Ruta/A/Mis_Datos" --account-map "cuentas.csv" --output-dir Output
  ```
  **Sin margen bruto:** los archivos crudos no traen COGS por SKU. Todas las
  cifras monetarias son ingreso bruto y el reporte lo declara. No inventar
  márgenes.

### 3. Idioma de los entregables (`--lang es|en`)

```powershell
python Scripts/generate_report.py --brand sullivan --cadence unified --lang es --data-source demo --period-label "April 2026" --output-dir Output
```

Fija el idioma del PDF y con cuál **abre** el dashboard. El HTML embebe **los
dos idiomas** y un selector ES/EN, así que un solo archivo sirve a los dos
públicos. La taxonomía se queda en inglés en ambos idiomas (ver sección 0).
Todo el texto sale de `Scripts/i18n.py`.

### 4. Datos demo (para que los 3 reportes corran en instalación limpia)

```powershell
python Scripts/make_demo_data.py                      # los tres juegos
python Scripts/make_demo_data.py --brand loco         # solo uno
```

Genera insumos **sintéticos** con la estructura exacta de los reales en
`Data_for_demo/`. Los flujos semanal y de Loco leen de `Client_Data/`, que el
empaquetador excluye, así que sin esto fallarían de entrada; ahora caen al demo
y lo avisan. Qué columnas pide cada reporte: `DATOS_REQUERIDOS.md`.

---

## 🛠️ Arquitectura de Scripts y Componentes

| Script / Archivo | Rol en la Skill |
| :--- | :--- |
| [`Scripts/generate_report.py`](file:///e:/Users/1167486/Local/scripts/skills_generales/reporte-sullivan-sttupa-loco-tequila-us/Scripts/generate_report.py) | **Orquestador Principal Multimarca.** Expone la interfaz CLI y el menú interactivo; valida marcas, cadencias y enruta la generación. |
| [`Scripts/sullivan_weekly_processor.py`](file:///e:/Users/1167486/Local/scripts/skills_generales/reporte-sullivan-sttupa-loco-tequila-us/Scripts/sullivan_weekly_processor.py) | Procesador e integrador semanal de los 7 reportes de Sullivan (DTC dedup, Tock, Aging de POs y Depletions). |
| [`Scripts/dashboard_weekly_sullivan.py`](file:///e:/Users/1167486/Local/scripts/skills_generales/reporte-sullivan-sttupa-loco-tequila-us/Scripts/dashboard_weekly_sullivan.py) | Generador de Dashboard Semanal interactivo de Sullivan bajo tokens de `Design_sullivan.md` y barras ordenadas de mayor a menor. |
| [`Scripts/dashboard_generator.py`](file:///e:/Users/1167486/Local/scripts/skills_generales/reporte-sullivan-sttupa-loco-tequila-us/Scripts/dashboard_generator.py) | Motor del Dashboard Mensual de Reconciliación DTC (3 pestañas, Albers Geo Map y tooltips). |
| [`Scripts/dashboard_sullivan_unified.py`](file:///e:/Users/1167486/Local/scripts/skills_generales/reporte-sullivan-sttupa-loco-tequila-us/Scripts/dashboard_sullivan_unified.py) | **Dashboard unificado (recomendado).** Fusiona las dos cadencias en un solo HTML de 6 pestañas: los bloques comunes aparecen una vez y se conserva lo exclusivo de cada una. Reutiliza los motores de cálculo del mensual y del semanal, sin duplicar lógica. |
| [`Scripts/loco_data_processor.py`](file:///e:/Users/1167486/Local/scripts/skills_generales/reporte-sullivan-sttupa-loco-tequila-us/Scripts/loco_data_processor.py) | Procesador de los 7 insumos crudos de Loco Tequila USA (FB, Southern Glazer's, Park Street, Shopify/Memory) hacia la estructura del reporte. |
| [`Scripts/make_demo_data.py`](file:///e:/Users/1167486/Local/scripts/skills_generales/reporte-sullivan-sttupa-loco-tequila-us/Scripts/make_demo_data.py) | Generador de datos demo **sintéticos** con la estructura exacta de los insumos reales, para que los tres reportes corran sin datos de cliente. |
| [`Scripts/sullivan_c7_simulator.py`](file:///e:/Users/1167486/Local/scripts/skills_generales/reporte-sullivan-sttupa-loco-tequila-us/Scripts/sullivan_c7_simulator.py) | Simulador de los 5 exports mensuales de Commerce7, anclado a las proporciones reales de canal y club. |
| [`Scripts/i18n.py`](file:///e:/Users/1167486/Local/scripts/skills_generales/reporte-sullivan-sttupa-loco-tequila-us/Scripts/i18n.py) | **Diccionario ES/EN único** para los ocho entregables. Pares exactos + fragmentos para el texto que se compone con datos dentro; bidireccional, porque el tablero de Loco nació con parte de su texto en español. Emite también el selector ES/EN que se inyecta en cada HTML. La taxonomía no está aquí: lo que no está, no se traduce. |
| [`Scripts/pdf_common.py`](file:///e:/Users/1167486/Local/scripts/skills_generales/reporte-sullivan-sttupa-loco-tequila-us/Scripts/pdf_common.py) | **Toolkit compartido de PDF.** Maquetación adaptativa (alturas y anchos derivados del espacio disponible), ajuste de línea real, `—` en lugar de `nan`, y temas de marca. Los cuatro PDF lo usan, así que una corrección de layout se aplica una vez. |
| [`Scripts/pdf_weekly_sullivan.py`](file:///e:/Users/1167486/Local/scripts/skills_generales/reporte-sullivan-sttupa-loco-tequila-us/Scripts/pdf_weekly_sullivan.py) | Reporte semanal de Sullivan en PDF (5 páginas): DTC, cuentas por cobrar con antigüedad, depletions y auditoría de no clasificados. |
| [`Scripts/pdf_sullivan_unified.py`](file:///e:/Users/1167486/Local/scripts/skills_generales/reporte-sullivan-sttupa-loco-tequila-us/Scripts/pdf_sullivan_unified.py) | Reporte unificado en PDF (7 páginas): las dos cadencias en un documento, sin repetir los bloques comunes. |
| [`Scripts/pdf_loco_tequila.py`](file:///e:/Users/1167486/Local/scripts/skills_generales/reporte-sullivan-sttupa-loco-tequila-us/Scripts/pdf_loco_tequila.py) | Reporte de Loco Tequila USA en PDF (7 páginas) bajo los tokens de `Design_loco_tequila.md`, con una página final que declara las brechas de dato. |
| [`DATOS_REQUERIDOS.md`](file:///e:/Users/1167486/Local/scripts/skills_generales/reporte-sullivan-sttupa-loco-tequila-us/DATOS_REQUERIDOS.md) | Referencia técnica: qué archivos y columnas pide cada reporte, y cómo se trata el dato ausente. |
| [`tutorial_datos_para_cliente.md`](file:///e:/Users/1167486/Local/scripts/skills_generales/reporte-sullivan-sttupa-loco-tequila-us/tutorial_datos_para_cliente.md) | **Mini tutorial bilingüe para el cliente:** qué archivos entregar hoy, dónde ponerlos y qué comando correr para cada reporte con datos reales. |
| [`Scripts/pdf_generator.py`](file:///e:/Users/1167486/Local/scripts/skills_generales/reporte-sullivan-sttupa-loco-tequila-us/Scripts/pdf_generator.py) | Motor de Reporte Ejecutivo PDF mensual (ReportLab) con cuadre al centavo. |
| [`Scripts/loco_dashboard_generator.py`](file:///e:/Users/1167486/Local/scripts/skills_generales/reporte-sullivan-sttupa-loco-tequila-us/Scripts/loco_dashboard_generator.py) | Motor del Dashboard Ejecutivo de Loco Tequila USA bajo tokens de `Design_loco_tequila.md` (8 bloques directivos con barras ordenadas de mayor a menor). |
| [`Designs/`](file:///e:/Users/1167486/Local/scripts/skills_generales/reporte-sullivan-sttupa-loco-tequila-us/Designs/) | Manuales de identidad, paletas de color y tokens visuales normativos (`Design_sullivan.md`, `Design_loco_tequila.md`, `Design_sttupa.md`). |
| [`AGENTS.md`](file:///e:/Users/1167486/Local/scripts/skills_generales/reporte-sullivan-sttupa-loco-tequila-us/AGENTS.md) | Guía de operación para agentes IA (entorno Conda, prohibición de comandos git). |
