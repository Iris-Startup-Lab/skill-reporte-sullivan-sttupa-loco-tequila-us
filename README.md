# Sistema Tripartito de Reportes Ejecutivos Multimarca

> **Plataforma Agéntica de Inteligencia Comercial y Reporteo Directivo**  
> Generación de Dashboards Interactivos Standalone (HTML) y Reportes Directivos de Alta Calidad (PDF) para marcas de lujo, hospitalidad y destilados ultra-premium.

---

## 🏷️ Estado del Ecosistema de Marcas

| Marca | Industria / Región | Estado de la Skill | Entregables Disponibles |
| :--- | :--- | :---: | :--- |
| **Sullivan Rutherford Estate** | Bodega & Viñedo (Napa Valley, CA, EEUU) | 🟢 **ACTIVO** | Dashboard HTML (2 pestañas + mapa) + PDF Ejecutivo (~10 págs) |
| **Loco Tequila USA** | Tequila de Terruño Ultra-Premium (Jalisco, MEX / EEUU) | 🟡 **Próximamente** | Manual de diseño, tokens, tipografías y logos preparados |
| **Sttupa** | Hospitalidad & Experiencias Boutique | 🟡 **Próximamente** | Manual de diseño, tokens, tipografías y logos preparados |

---

## 🚀 Flujo de Operación de la Skill

La skill está diseñada de manera agnóstica para guiar al usuario o interactuar con agentes autónomos en 2 fases clave:

1. **Selección de Marca:**
   * Pregunta primero para cuál de las 3 marcas se requiere el reporte.
   * Si se elige **Loco Tequila** o **Sttupa**, el sistema notifica que la generación automatizada se encuentra en desarrollo (*"Próximamente"*).
   * Si se elige **Sullivan**, continúa a la configuración de datos.
2. **Selección de Fuente de Datos (Sullivan):**
   * **Opción A (Demo):** Utiliza los datasets de demostración preconfigurados en `Data_for_demo/Sullivan_data_demo/`.
   * **Opción B (Datos Propios):** Permite ingresar archivos en formato **Excel (`.xlsx`)** o **CSV (`.csv`)** para transacciones de venta y reconciliación contable.

---

## 📁 Estructura del Repositorio

```text
├── .agents/
│   └── skills/
│       └── reporte-marcas/
│           └── SKILL.md            # Definición formal de la skill agéntica
├── Client_Data/
│   └── Sullivan_data/              # Reportes fuente reales de Commerce7 (Abril 2026)
├── Data_for_demo/
│   └── Sullivan_data_demo/         # Datasets demo para pruebas y validaciones
├── Designs/                        # Design Systems y tokens de marca (Markdown)
│   ├── Design_loco_tequila.md      # Guía de estilo Loco Tequila
│   ├── Design_sttupa.md            # Guía de estilo Sttupa
│   └── Design_sullivan.md          # Guía de estilo Sullivan Rutherford Estate
├── Examples/                       # Muestras de dashboards y reportes generados
├── Fonts/                          # Fuentes tipográficas corporativas
│   ├── Font_loco_tequila/
│   ├── Font_sttupa/
│   └── Font_sullivan/              # EB Garamond (variable y estáticas)
├── Imagenes_iconos/                # Logotipos vectoriales y PNG de alta resolución
├── Scripts/                        # Motores de renderizado y orquestador
│   ├── generate_report.py          # Orquestador unificado multimarca (CLI / Interactivo)
│   ├── dashboard_generator.py      # Motor de Dashboard HTML Standalone (Albers Geo + KPIs)
│   ├── pdf_generator.py            # Motor de Reporte Ejecutivo PDF (ReportLab)
│   ├── sullivan_c7_simulator.py    # Generador de datos sintéticos mensuales
│   └── zcta_centroids.csv          # Caché de coordenadas lat/lon de ZIPs de EEUU
├── AGENTS.md                       # Protocolos de entorno Conda para agentes IA
├── Reportes_Sullivan_README.md     # Documentación técnica de los scripts de Sullivan
├── SKILL.md                        # Manifiesto principal de la skill
├── Sullivan_data_guide.md          # Guía de ingeniería y cascada de prioridades (1 a 9)
└── README.md                       # Este documento
```

---

## 🐍 Requisitos y Entorno de Ejecución

Todos los scripts requieren ejecutarse dentro del entorno de Conda **`data_analytics_science`**.

### Activación en PowerShell (Windows):

```powershell
# 1. Cargar hook de Conda
& "E:\Users\1167486\AppData\Local\anaconda3\Scripts\conda.exe" shell.powershell hook | Out-String | Invoke-Expression

# 2. Activar ambiente
conda activate data_analytics_science
```

---

## 💻 Guía de Uso del Orquestador (`Scripts/generate_report.py`)

El script principal [`Scripts/generate_report.py`](file:///e:/Users/1167486/Local/scripts/skills_generales/reporte-sullivan-sttupa-loco-tequila-us/Scripts/generate_report.py) puede invocarse de manera interactiva o automatizada:

### 1. Modo Interactivo (Recomendado para usuarios en consola)
Al ejecutarse sin argumentos o con `--interactive`, despliega un menú interactivo guiado:
```powershell
python Scripts/generate_report.py
```

### 2. Modo Automatizado (CLI para Agentes IA)

#### Caso A: Sullivan con Datos Demo predeterminados
```powershell
python Scripts/generate_report.py --brand sullivan --data-source demo --period-label "April 2026" --output-dir Output
```

#### Caso B: Sullivan con Datos Propios (.xlsx o .csv)
```powershell
python Scripts/generate_report.py `
  --brand sullivan `
  --order-sales "Ruta/A/Mi_Archivo_Ventas.csv" `
  --financial-report "Ruta/A/Mi_Reporte_Financiero.xlsx" `
  --period-label "Abril 2026" `
  --output-dir Output
```

#### Caso C: Consulta de Marca en Desarrollo (Loco Tequila o Sttupa)
```powershell
python Scripts/generate_report.py --brand loco_tequila
# Salida: Informa que la marca está en estado "Próximamente" y muestra los recursos listos.
```

---

## 📊 Entregables del Reporte (Sullivan)

Cuando se procesa la marca Sullivan, el sistema genera simultáneamente:

1. **Dashboard HTML Interactivo Standalone** (`Output/sullivan_dashboard_<periodo>.html`):
   * **Tab 1 — DTC Reconciliation (Vista A):** KPIs globales, barras horizontales de las 9 categorías finales de venta y tabla auditada con control de reconciliación contra *Net Sales*.
   * **Tab 2 — Club Deep Dive (Vista B):** Análisis de membresías Estate vs Founder's, desglose de paquetes y AOV, casos especiales de revisión (*Admin/POS Marked as Club*) y mapa coroplético de EEUU con proyección cónica Albers y overlay de centroides ZIP.
   * Totalmente auto-contenido: no requiere internet ni dependencias externas en tiempo de ejecución.
2. **Reporte Directivo en PDF** (`Output/sullivan_report_<periodo>.pdf`):
   * ~10 páginas en formato carta de alta resolución directiva (ReportLab).
   * Portada con sello de reconciliación contable, resumen ejecutivo, tabla formal de cascada de prioridades (1 a 9) y desglose detallado de ventas.

---

## 📐 Reglas de Clasificación de Sullivan (Resumen)

Para garantizar consistencia y evitar duplicaciones de ingresos, las órdenes se evalúan en una cascada excluyente de 9 prioridades:

1. `Inbound` + Tag `Event` $\rightarrow$ **Event**
2. `Inbound` + Tag `Corporate` $\rightarrow$ **Corporate**
3. `Inbound` + Tag `Friends & Family` $\rightarrow$ **Friends & Family**
4. `Inbound` residual $\rightarrow$ **Telesales**
5. `Web` + `External Order Vendor = Tock` $\rightarrow$ **Tock**
6. `Web` residual $\rightarrow$ **Web / Ecommerce**
7. `POS` $\rightarrow$ **Tasting Room**
8. `Club` + nombre contiene `Estate` $\rightarrow$ **Estate Club**
9. `Club` + nombre contiene `Founder's` $\rightarrow$ **Founder's Club**

*Para la especificación completa, consultar [`Sullivan_data_guide.md`](file:///e:/Users/1167486/Local/scripts/skills_generales/reporte-sullivan-sttupa-loco-tequila-us/Sullivan_data_guide.md).*
