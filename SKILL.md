---
name: reporte-sullivan-sttupa-loco-tequila-us
description: Generador agnóstico de reportes ejecutivos (Dashboard HTML + Reporte PDF) para marcas de lujo y hospitalidad (Sullivan Rutherford Estate, Loco Tequila USA, Sttupa). Flujo interactivo con selección de marca, elección de datos demo o personalizados (.xlsx / .csv) y reconciliación financiera automática.
---

# Skill: Generador Agnóstico de Reportes Ejecutivos Multimarca

Esta skill orquesta la creación de reportes directivos y dashboards interactivos para el ecosistema de marcas:

1. **Sullivan Rutherford Estate** (Bodega / Viñedo, Napa Valley, EEUU) — **[ACTIVO / PRODUCCIÓN]**
2. **Loco Tequila USA** (Destilados de ultra-lujo, México / EEUU) — **[PRÓXIMAMENTE]**
3. **Sttupa** (Hospitalidad / Experiencias boutique) — **[PRÓXIMAMENTE]**

---

## 🧭 Flujo de Interacción Obligatorio

Cualquier agente (Antigravity, OpenCode, Claude Code) o usuario que active esta skill debe seguir estrictamente este flujo secuencial:

```
┌─────────────────────────────────────────────────────────────┐
│          PASO 1: PREGUNTAR POR LA MARCA                     │
│  ¿Para qué marca deseas generar el reporte?                 │
│  1) Sullivan Rutherford Estate                              │
│  2) Loco Tequila USA                                        │
│  3) Sttupa                                                  │
└──────────────────────────────┬──────────────────────────────┘
                               │
               ┌───────────────┴───────────────┐
               ▼                               ▼
    [ Loco Tequila / Sttupa ]             [ Sullivan ]
               │                               │
               ▼                               ▼
     Responder: "Próximamente"     ┌───────────────────────────────────────┐
     y finalizar flujo             │ PASO 2: PREGUNTAR POR FUENTE DE DATOS │
                                   │ ¿Deseas usar datos demo o propios?    │
                                   │ 1) Datos Demo predeterminados         │
                                   │ 2) Proporcionar datos (.xlsx o .csv)  │
                                   └───────────────────┬───────────────────┘
                                                       │
                                                       ▼
                                   ┌───────────────────────────────────────┐
                                   │ PASO 3: EJECUCIÓN TÉCNICA (CONDA)     │
                                   │ Scripts/generate_report.py            │
                                   └───────────────────┬───────────────────┘
                                                       │
                                                       ▼
                                   ┌───────────────────────────────────────┐
                                   │ PASO 4: ENTREGA DE RESULTADOS         │
                                   │ Dashboard HTML + Reporte PDF          │
                                   └───────────────────────────────────────┘
```

---

### Paso 1: Selección de Marca

Al recibir la solicitud de generar reportes, el agente **debe preguntar primero** al usuario para cuál de las 3 marcas desea trabajar:

* **Si selecciona Loco Tequila USA o Sttupa:**  
  El agente debe responder de forma clara y amable:  
  > ⏳ **Próximamente.**  
  > La generación automatizada de reportes para esta marca se encuentra en desarrollo. Los activos corporativos (logos en `Imagenes_iconos/`, fuentes en `Fonts/` y directrices de diseño en `Designs/`) ya están preparados para su integración.

* **Si selecciona Sullivan Rutherford Estate:**  
  Proceder inmediatamente al **Paso 2**.

---

### Paso 2: Selección de Fuente de Datos (Sullivan)

El agente debe preguntar al usuario cómo desea alimentar el reporte:

1. **Usar Datos Demo:**
   * Utiliza los datasets de demostración preconfigurados en `Data_for_demo/Sullivan_data_demo/` (o datos auditados en `Client_Data/Sullivan_data/`).
   * No requiere que el usuario suba archivos adicionales.
2. **Proporcionar Datos Propios:**
   * El agente solicitará al usuario la ruta del archivo transaccional de ventas (**`order_sales`** o **`order_details`**).
   * Puede estar en formato **`.xlsx`** o **`.csv`**.
   * Opcionalmente, se solicita el archivo de reconciliación financiera (**`financial_report`**) en `.xlsx` o `.csv`.
   * Se solicita o confirma la etiqueta del periodo (por defecto: *"April 2026"*).

---

### Paso 3: Ejecución en el Entorno Conda

Todos los generadores requieren ejecutarse dentro del entorno de Python **`data_analytics_science`**.
Siempre y cuando no se tengan recursos extra como Claude Desktop

#### Comando PowerShell para activar el entorno y ejecutar el orquestador

```powershell
# 1. Cargar hook de Conda y activar ambiente
& "E:\Users\1167486\AppData\Local\anaconda3\Scripts\conda.exe" shell.powershell hook | Out-String | Invoke-Expression; conda activate data_analytics_science

# 2. Ejecutar con Datos Demo:
python Scripts/generate_report.py --brand sullivan --data-source demo --period-label "April 2026" --output-dir Output

# O Ejecutar con Datos Propios (CSV o Excel):
python Scripts/generate_report.py --brand sullivan --order-sales "Ruta/Al/Archivo.csv" --financial-report "Ruta/Al/Financiero.xlsx" --period-label "Abril 2026" --output-dir Output
```

---

### Paso 4: Entregables Generados

El proceso genera simultáneamente dos entregables complementarios en la carpeta de salida (`Output/`):

1. **Dashboard HTML Interactivo Standalone** (`sullivan_dashboard_<periodo>.html`):
   * **Pestaña 1 (DTC Reconciliation - Vista A):** KPIs ejecutivos, desglose horizontal de las 9 categorías finales de venta y tabla auditada con control de discrepancias contra *Net Sales*.
   * **Pestaña 2 (Club Deep Dive - Vista B):** Análisis de membresías Estate vs Founder's, tabla de paquetes y AOV, casos especiales de revisión (*Admin/POS Marked as Club*) y mapa coroplético de EEUU con proyección Albers y overlay de centroides ZIP.
2. **Reporte Directivo en PDF** (`sullivan_report_<periodo>.pdf`):
   * Documento formal de ~10 páginas generado con ReportLab.
   * Portada con sello de reconciliación, resumen ejecutivo, cascada de clasificación (prioridades 1-9), tabla detallada y apéndice técnico.

---

## 🛠️ Arquitectura de Scripts y Componentes

| Script / Archivo | Rol en la Skill |
| :--- | :--- |
| [`Scripts/generate_report.py`](file:///e:/Users/1167486/Local/scripts/skills_generales/reporte-sullivan-sttupa-loco-tequila-us/Scripts/generate_report.py) | **Orquestador Principal Multimarca.** Expone la interfaz CLI y el menú interactivo; valida marcas, enruta datos y dispara la generación. |
| [`Scripts/dashboard_generator.py`](file:///e:/Users/1167486/Local/scripts/skills_generales/reporte-sullivan-sttupa-loco-tequila-us/Scripts/dashboard_generator.py) | Motor de renderizado del Dashboard Web HTML (auto-contenido con CSS tokens, fuentes EB Garamond y logo en base64). Acepta `.xlsx` y `.csv`. |
| [`Scripts/pdf_generator.py`](file:///e:/Users/1167486/Local/scripts/skills_generales/reporte-sullivan-sttupa-loco-tequila-us/Scripts/pdf_generator.py) | Motor de renderizado vectorial en PDF (ReportLab). Acepta `.xlsx` y `.csv`. |
| [`Scripts/sullivan_c7_simulator.py`](file:///e:/Users/1167486/Local/scripts/skills_generales/reporte-sullivan-sttupa-loco-tequila-us/Scripts/sullivan_c7_simulator.py) | Generador de datos sintéticos mensuales para pruebas de volumen y tendencias. |
| [`Sullivan_data_guide.md`](file:///e:/Users/1167486/Local/scripts/skills_generales/reporte-sullivan-sttupa-loco-tequila-us/Sullivan_data_guide.md) | Manual normativo con la cascada de 9 prioridades, cruces de columnas y checklist de 10 puntos de control. |
| [`Designs/`](file:///e:/Users/1167486/Local/scripts/skills_generales/reporte-sullivan-sttupa-loco-tequila-us/Designs/) | Manuales de identidad, paletas de color y tokens visuales de las 3 marcas (`Design_sullivan.md`, `Design_loco_tequila.md`, `Design_sttupa.md`). |

---

## 📌 Reglas de Negocio Clave (Sullivan)

* **No sumar los 5 reportes:** Son perspectivas distintas de las mismas ventas; sumarlos duplica los ingresos.
* **Cascada de 9 Prioridades:**
  1. `Inbound` + `Event` $\rightarrow$ **Event**
  2. `Inbound` + `Corporate` $\rightarrow$ **Corporate**
  3. `Inbound` + `Friends & Family` $\rightarrow$ **Friends & Family**
  4. `Inbound` residual $\rightarrow$ **Telesales**
  5. `Web` + `Vendor = Tock` $\rightarrow$ **Tock**
  6. `Web` residual $\rightarrow$ **Web / Ecommerce**
  7. `POS` $\rightarrow$ **Tasting Room**
  8. `Club` + `Estate` $\rightarrow$ **Estate Club**
  9. `Club` + `Founder's` $\rightarrow$ **Founder's Club**
* **Reconciliación:** Total DTC clasificado debe coincidir exactamente con el campo `SubTotal` de `Apr_FinancialReport`.
