# AGENTS.md — Guía de Operación y Pruebas para Agentes IA y Usuarios

## 🐍 Configuración del Entorno Conda

Todos los comandos requieren ejecutarse dentro del entorno de Python **`data_analytics_science`**.

### Activación en PowerShell (Windows)

```powershell
# 1. Cargar el hook de Conda
& "E:\Users\1167486\AppData\Local\anaconda3\Scripts\conda.exe" shell.powershell hook | Out-String | Invoke-Expression

# 2. Activar el ambiente de trabajo
conda activate data_analytics_science
```

### Instalación de Dependencias (si se prueba en un nuevo ambiente)

```powershell
# Dependencias gráficas nativas (Cairo para SVG -> PNG del logo)
conda install -c conda-forge cairo pycairo -y

# Requerimientos de Python
pip install -r requirements.txt
```

---

## 🤖 Protocolo Obligatorio para Agentes IA (`SKILL.md`)

Todo agente que atienda una solicitud de generación de reportes en este repositorio debe cumplir con el siguiente protocolo interactivo:

1. **Pregunta Inicial de Marca:**
   El agente debe preguntar al usuario para cuál de las 3 marcas desea generar el reporte:
   * **Sullivan Rutherford Estate** *(Activo / Producción)*
   * **Loco Tequila USA** *(Próximamente)*
   * **Sttupa** *(Próximamente)*
2. **Respuesta si se elige Loco Tequila o Sttupa:**
   El agente responderá inmediatamente indicando que el soporte automatizado está en desarrollo (**"Próximamente"**), señalando que los manuales de diseño (`Designs/`), logotipos (`Imagenes_iconos/`) y fuentes (`Fonts/`) ya están preparados.
3. **Flujo para Sullivan:**
   El agente preguntará si el usuario desea:
   * **A) Usar datos Demo:** Emplear los archivos precargados en `Data_for_demo/Sullivan_data_demo/` (o datos auditados en `Client_Data/Sullivan_data/`).
   * **B) Proporcionar datos propios:** Solicitar la ruta del archivo transaccional de ventas en formato **`.xlsx`** o **`.csv`**, y opcionalmente el reporte financiero.

---

## 💻 Guía de Ejecución por Entorno de IA y Modelo

### 1. OpenCode (CLI / IDE Agent)

- **Modelos recomendados**:
  - **DeepSeek V3 / R1 / V4 Pro**
  - **Kimi 3 / K1.5**
- **Instrucciones para OpenCode**:
  1. Abrir la carpeta del proyecto en OpenCode.
  2. Detectará automáticamente `SKILL.md`, `README.md` y `AGENTS.md`.
  3. Ejecutar la llamada activando el entorno conda antes de invocar Python:

     ```powershell
     & "E:\Users\1167486\AppData\Local\anaconda3\Scripts\conda.exe" shell.powershell hook | Out-String | Invoke-Expression; conda activate data_analytics_science; python Scripts/generate_report.py --brand sullivan --data-source demo --period-label "April 2026" --output-dir Output
     ```

---

### 2. Antigravity (Google DeepMind Agentic IDE)

- **Modelos recomendados**:
  - **Gemini 3.7 Flash** (Predeterminado para alta velocidad y precisión de código)
  - **Gemini 3.1 Pro / Ultra**
- **Instrucciones para Antigravity**:
  1. Antigravity descubre automáticamente las skills en la raíz de trabajo (`SKILL.md`) o en `.agents/skills/reporte-marcas/SKILL.md`.
  2. Al ejecutar comandos en la terminal de Antigravity, anteponer la activación del hook de Conda.
  3. Para datos personalizados provistos por el usuario en CSV o Excel:

     ```powershell
     & "E:\Users\1167486\AppData\Local\anaconda3\Scripts\conda.exe" shell.powershell hook | Out-String | Invoke-Expression; conda activate data_analytics_science; python Scripts/generate_report.py --brand sullivan --order-sales "Ruta/Al/Archivo.csv" --financial-report "Ruta/Al/Financiero.xlsx" --period-label "April 2026" --output-dir Output
     ```

---

### 3. Claude Desktop y Claude Code

- **Modelos recomendados**:
  - **Claude Sonnet**
  - **Claude Opus**
- **Configuración en Claude Desktop**:
  - Servidores MCP: `@modelcontextprotocol/server-filesystem` y `@modelcontextprotocol/server-powershell`.
  - Cargar `SKILL.md` en el espacio de conocimiento (*Project Knowledge*).
- **Configuración en Claude Code (CLI)**:
  - Abrir la terminal en la raíz del proyecto y lanzar `claude`.
  - Claude Code ejecutará el comando del orquestador:

    ```powershell
    python Scripts/generate_report.py --brand sullivan --data-source demo --output-dir Output
    ```
