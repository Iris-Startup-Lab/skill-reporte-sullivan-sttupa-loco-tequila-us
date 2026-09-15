# Sistema Tripartito de Reportes Ejecutivos Multimarca

Autor: Fernando Dorantes Nieto

> **Plataforma Agéntica de Inteligencia Comercial y Reporteo Directivo**  
> Generación automatizada de Dashboards Interactivos Standalone (HTML) y Reportes Directivos de Alta Calidad (PDF) para marcas de ultra-lujo, hospitalidad y destilados premium.

<div align="center">

| Sullivan Rutherford Estate | Loco Tequila USA | Sttupa |
| :---: | :---: | :---: |
| <img src="Imagenes_iconos/Sullivan-Black.png" alt="Sullivan Rutherford Estate" height="38" /> | <img src="Imagenes_iconos/Loco_Tequila_Logo.svg" alt="Loco Tequila USA" height="38" /> | <img src="Imagenes_iconos/Stupa-Black.png" alt="Sttupa" height="38" /> |

</div>

---

## 🏷️ Estado del Ecosistema de Marcas

| Marca | Identidad | Industria / Región | Estado de la Skill | Entregables Disponibles |
| :--- | :---: | :--- | :---: | :--- |
| **Sullivan Rutherford Estate** | <img src="Imagenes_iconos/Sullivan-Black.png" alt="Sullivan" height="24" /> | Bodega & Viñedo (Napa Valley, CA, EEUU) | 🟢 **ACTIVO (Mensual + Semanal)** | • Dashboard HTML Mensual (3 pestañas + mapa Albers)<br>• Reporte PDF Mensual (~9 págs al centavo)<br>• Dashboard Semanal (DTC + Distribución + PO Aging + Depletions) |
| **Loco Tequila USA** | <img src="Imagenes_iconos/Loco_Tequila_Logo.svg" alt="Loco Tequila" height="24" /> | Tequila de Terruño Ultra-Premium (Jalisco, MEX / EEUU) | 🟢 **DEMO EJECUTIVO ACTIVO** | • Dashboard HTML Directivo (8 módulos: Depletion Trend, Leaderboard, Donut SKU, Heatmap, Sparklines, Toggle semanal e Inventario CA/TX) |
| **Sttupa** | <img src="Imagenes_iconos/Stupa-Black.png" alt="Sttupa" height="24" /> | Hospitalidad & Experiencias Boutique | 🟡 **Próximamente** | Manual de diseño (`Design_sttupa.md`), tokens, tipografías (`Fonts/Font_sttupa/`) y logos preparados |

---

## 🏛️ Reglas de Gobernanza de Diseño y Visualización

1. **🏛️ Gobernanza de Diseño (`Designs/`):**  
   El cliente propone la estructura funcional y métricas en `Client_Reports`, pero nosotros gobernamos y controlamos el diseño final rigiéndonos estrictamente por los manuales normativos de la carpeta `Designs/` (`Design_sullivan.md`, `Design_loco_tequila.md`, `Design_sttupa.md`), junto con sus fuentes corporativas (`Fonts/`) y logotipos vectoriales (`Imagenes_iconos/`).
2. **📊 Regla Estricta de Ordenamiento en Gráficas de Barras (Storytelling with Data):**  
   En todos los reportes (HTML y PDF, para todas las marcas), **todas las gráficas de barras (horizontales o verticales: canales, productos/SKUs, vendedores, estados, cuentas, distribuidores o aging) deben estar ordenadas estrictamente de mayor a menor (orden descendente por importe o volumen)**.
3. **🎯 Presentación Ejecutiva Limpia:**  
   Queda prohibido mostrar nombres de archivos de código o rutas internas (`Designs/...md`) en los encabezados o badges visibles para el cliente. Los badges deben reflejar sellos y fechas oficiales de corte (ej. `Official Weekly Cutoff · Aug 23, 2026`).

---

## 📁 Estructura del Repositorio

```text
├── .agents/
│   └── skills/
│       └── reporte-sullivan-sttupa-loco-tequila-us/
│           └── SKILL.md            # Definición formal de la skill agéntica
├── Client_Data/                    # Datos transaccionales y operativos de clientes
│   ├── Sullivan_data/              # Reportes mensuales y semanales de Sullivan
│   │   └── Weekly/                 # Lotes semanales organizados (ej. Week_2026_08_23)
│   ├── Loco_tequila_usa_data/      # Datos de Sara (distribuidores, Park Street, Shopify)
│   └── Sttupa_data/                # Datos de hospitalidad (en preparación)
├── Client_Reports/                 # Reportes y requerimientos propuestos por el cliente
│   ├── Sullivan_data/              # Dashboard blueprint y requerimientos semanales
│   └── Loco_tequila_usa_data/      # summary_7.html (blueprint directivo de 8 bloques)
├── Data_for_demo/                  # Datasets demo para pruebas y validaciones
├── Designs/                        # Design Systems y tokens de marca normativos (Markdown)
│   ├── Design_loco_tequila.md      # Guía de estilo e identidad Loco Tequila USA
│   ├── Design_sttupa.md            # Guía de estilo e identidad Sttupa
│   └── Design_sullivan.md          # Guía de estilo e identidad Sullivan Rutherford Estate
├── Fonts/                          # Fuentes tipográficas oficiales
│   ├── Font_loco_tequila/          # Fraunces e Inter
│   ├── Font_sttupa/                # Tipografía boutique
│   └── Font_sullivan/              # EB Garamond (variable y estáticas)
├── Imagenes_iconos/                # Logotipos vectoriales SVG y PNG de alta resolución
├── Output/                         # Directorio destino de dashboards y reportes generados
│   ├── sullivan_dashboard_april_2026.html
│   ├── sullivan_weekly_dashboard_aug_23_2026.html
│   └── loco_tequila_usa_dashboard_demo.html
├── Scripts/                        # Motores de renderizado y orquestador
│   ├── generate_report.py          # Orquestador unificado multimarca (CLI / Interactivo)
│   ├── dashboard_generator.py      # Motor de Dashboard HTML Mensual Sullivan (Geo Map + Reconciliación)
│   ├── i18n.py                     # Diccionario ES/EN único para los 8 entregables + selector del HTML
│   ├── pdf_generator.py            # Motor de Reporte Ejecutivo PDF Mensual Sullivan (ReportLab)
│   ├── sullivan_weekly_processor.py# Procesador e integrador de los 7 reportes semanales Sullivan
│   ├── dashboard_weekly_sullivan.py# Motor de Dashboard HTML Semanal Sullivan (DTC + Distribución)
│   └── loco_dashboard_generator.py # Motor de Dashboard HTML Directivo Loco Tequila USA
├── AGENTS.md                       # Protocolos de entorno Conda para agentes IA (Reglas de no-git)
├── SKILL.md                        # Manifiesto principal de la skill agéntica
├── to_do.md                        # Plan maestro y seguimiento de tareas
└── README.md                       # Este documento
```

---

## 🐍 Requisitos y Entorno de Ejecución

Todos los scripts requieren ejecutarse dentro del entorno de Conda **`data_analytics_science`**.

### Activación en PowerShell (Windows)

```powershell
# 1. Cargar hook de Conda
& "E:\Users\1167486\AppData\Local\anaconda3\Scripts\conda.exe" shell.powershell hook | Out-String | Invoke-Expression

# 2. Activar ambiente
conda activate data_analytics_science
```

---

## 💻 Guía de Uso del Orquestador (`Scripts/generate_report.py`)

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
  El periodo y el nombre del archivo se derivan de la fecha de pago más reciente
  del propio export, no de una constante.

* **Reporte Unificado (recomendado): las dos cadencias en un solo HTML.**
  ```powershell
  python Scripts/generate_report.py --brand sullivan --cadence unified --data-source demo --period-label "April 2026" --output-dir Output
  ```
  Los bloques que el mensual y el semanal decían igual —la mezcla de canales, el
  desglose de Club, la tabla de no clasificados, el encabezado— aparecen **una
  sola vez**, con un selector de cadencia. Lo exclusivo de cada uno se conserva:
  el mapa Albers con los puntos por código postal y la reconciliación al centavo
  del mensual, y las cuentas por cobrar, el aging y las depletions del semanal.
  La parte semanal es opcional: sin ella el reporte sale completo en su parte
  mensual y lo declara.

### Los cuatro reportes entregan HTML **y** PDF

`--format all` (por omisión) genera ambos; `--format html` o `--format pdf` uno solo.

| Reporte | Dashboard HTML | Reporte PDF |
| :--- | :--- | :--- |
| Sullivan mensual | `sullivan_dashboard_<periodo>.html` | `sullivan_report_<periodo>.pdf` — 8 pág. |
| Sullivan semanal | `sullivan_weekly_dashboard_<fecha>.html` | `sullivan_weekly_report_<fecha>.pdf` — 5 pág., **6 con varias semanas** |
| Sullivan unificado | `sullivan_dashboard_unified_<periodo>.html` | `sullivan_report_unified_<periodo>.pdf` — 7 pág. |
| Loco Tequila USA | `loco_tequila_usa_dashboard.html` | `loco_tequila_usa_report.pdf` — 7 pág. |

### 🌐 Bilingüe: un solo archivo para los dos públicos

```powershell
python Scripts/generate_report.py --brand sullivan --cadence unified --lang es --data-source demo --period-label "April 2026" --output-dir Output
```

`--lang es|en` (por omisión `en`) fija el idioma del **PDF** y con cuál **abre**
el dashboard. El HTML lleva **los dos idiomas embebidos y un selector ES/EN** en
la esquina superior derecha: un solo archivo se le manda a todos y cada quien
elige, sin riesgo de enviar la versión equivocada. Los PDF sí necesitan un
idioma por archivo, porque un documento impreso no puede alternar.

**La taxonomía NO se traduce en ningún idioma** (decisión de negocio): las 9
categorías de la cascada (`Tasting Room`, `Estate Club`, `Founder's Club`,
`Web / Ecommerce`, `Tock`, `Inbound Telesales`, `Event`, `Corporate`,
`Friends & Family`, `Unclassified`), los nombres de SKU, de distribuidores y de
cuentas se quedan en inglés. Son los nombres con los que el equipo del cliente
cuadra contra Commerce7 y Park Street: si el reporte dijera "Sala de Cata" y el
sistema dice "Tasting Room", quien audita pierde el hilo. Sí se traduce todo lo
nuestro: títulos, pestañas, secciones, KPIs, encabezados de tabla, ejes, notas,
advertencias y glosario.

Todo el texto sale de un solo diccionario,
[`Scripts/i18n.py`](Scripts/i18n.py), que sirve a los ocho entregables. Ocho
listas separadas garantizarían que a la tercera corrección alguna quedara
desincronizada.

### 📅 Varias semanas en el reporte semanal

Si el cliente entrega más de una semana, el reporte las muestra **todas**:

```text
Client_Data/Sullivan_data/Weekly/
├── Week_2026_08_09/     <- los 4 archivos de esa semana
├── Week_2026_08_16/
└── Week_2026_08_23/
```

El dashboard trae un **selector de semana** que repinta el tablero completo
—KPIs, gráficas y notas—, la línea de tendencia dibuja la serie real y el
**cambio semanal (WoW)** compara contra la semana inmediata anterior. El PDF,
que no puede llevar selector, documenta la semana más reciente y añade una
página con la tendencia de toda la serie.

Con una sola semana el reporte sale como siempre y el selector se queda oculto:
un desplegable de un solo renglón sugiere que hay algo que elegir cuando no lo
hay.

Toda la maquetación de los cuatro PDF sale de
[`Scripts/pdf_common.py`](Scripts/pdf_common.py): alturas de fila y anchos de columna
que se derivan del espacio disponible (por eso ya no quedan tablas diminutas con media
página en blanco), ajuste de línea real en los párrafos, y `—` en lugar de `nan` como
última barrera antes de dibujar.

### 2. Loco Tequila USA

* **Dashboard Ejecutivo alimentado con datos reales:**
  ```powershell
  # Datos del repo (o los demo si no hay datos de cliente)
  python Scripts/generate_report.py --brand loco_tequila --output-dir Output

  # Datos propios del usuario
  python Scripts/generate_report.py --brand loco_tequila --data-dir "Ruta/A/Mis_Datos" --account-map "cuentas.csv" --output-dir Output
  ```
  **No hay margen bruto:** los archivos crudos no traen COGS por SKU, así que
  todas las cifras monetarias son ingreso bruto y el reporte lo declara.

### 3. Datos demo

Los flujos semanal y de Loco leen de `Client_Data/`, que el empaquetador excluye
a propósito. Para que los tres reportes corran en una instalación limpia:

```powershell
python Scripts/make_demo_data.py            # los tres juegos
python Scripts/make_demo_data.py --brand loco
```

Genera archivos **sintéticos** (ningún dato real de cliente) con la estructura
exacta de los insumos reales.

**Documentación de datos, en tres niveles:**

* [`tutorial_datos_para_cliente.md`](tutorial_datos_para_cliente.md) — mini tutorial
  bilingüe para el cliente: qué archivos entregar, dónde ponerlos y qué comando correr.
* [`DATOS_REQUERIDOS.md`](DATOS_REQUERIDOS.md) — referencia técnica: columna por
  columna, incluidos los encabezados irregulares que se leen por posición.
* [`tutorial_para_cliente.md`](tutorial_para_cliente.md) — cómo **leer** los reportes
  una vez generados.

Sttupa no tiene demo a propósito: sin ningún archivo real del cliente en el que
basar la estructura, un demo inventado enseñaría un formato que después no
coincidiría.

### 4. Modo Interactivo

Al ejecutarse sin argumentos o con `--interactive`, despliega un menú interactivo guiado en consola:

```powershell
python Scripts/generate_report.py --interactive
```
