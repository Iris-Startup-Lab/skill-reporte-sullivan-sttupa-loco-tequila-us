# AGENTS.md — Guía de Operación y Pruebas para Agentes IA y Usuarios

Este es el documento principal que deben leer los agentes; los usuarios pueden consultar también el `README.md` o el `SKILL.md` para entender cómo funciona el repositorio y cómo usarlo.

## 🐍 Configuración del Entorno Conda

Todos los comandos requieren ejecutarse dentro del entorno de Python **`data_analytics_science`**.

### Activación en PowerShell (Windows) — Entorno principal del desarrollador

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

Todo agente que atienda una solicitud de generación de reportes en este repositorio debe cumplir con las siguientes directrices:

0. **PRIMER TURNO — IDIOMA ANTES QUE MARCA (regla inmutable):**
   **NUNCA** emitas solo la pregunta de marca en tu primer mensaje. La redacción
   literal de las dos bifurcaciones (usuario en inglés / usuario en español o
   saludo suelto) está en la **sección 0 de `SKILL.md`** y es obligatoria; no la
   improvises.

   * Si el usuario escribió en **inglés** → idioma fijado en `en`, y preguntas la
     marca en inglés.
   * Si escribió en **español**, saludó o solo invocó la skill → tu primer
     mensaje pregunta **idioma y marca a la vez**, en formato bilingüe.

   El idioma elegido gobierna la conversación **y** los entregables: se pasa como
   `--lang es|en` a `Scripts/generate_report.py`. Determina el idioma del PDF y
   con cuál abre el dashboard; el HTML lleva selector ES/EN embebido, así que un
   solo archivo sirve a los dos públicos.

   **La taxonomía no se traduce en ningún idioma** (`Tasting Room`,
   `Founder's Club`, `Estate Club`, `Web / Ecommerce`, SKU, distribuidores,
   cuentas): son los nombres con los que el cliente cuadra contra Commerce7 y
   Park Street. Sí se traduce todo lo nuestro: títulos, pestañas, secciones,
   KPIs, encabezados de tabla, ejes, notas, advertencias y glosario.

1. **Pregunta Inicial de Marca (después del idioma):**
   El agente debe preguntar al usuario para cuál de las 3 marcas desea generar el reporte:
   * **Sullivan Rutherford Estate** *(Activo: Producción Mensual y Semanal)*
   * **Loco Tequila USA** *(Demo Ejecutivo Activo: Blueprint YTD Week 34)*
   * **Sttupa** *(Próximamente)*
2. **Respuesta para Sttupa:**
   Indicar que el soporte automatizado está en desarrollo (**"Próximamente"**), señalando que los manuales de diseño (`Designs/Design_sttupa.md`), logotipos (`Imagenes_iconos/`) y fuentes (`Fonts/Font_sttupa/`) ya están preparados.
3. **Flujo para Loco Tequila USA:**
   El dashboard se alimenta de datos reales. Preguntar si usará los datos del repo
   (`Client_Data/Loco_tequila_usa_data/`), los demo (`Data_for_demo/Loco_tequila_demo/`,
   que es a lo que cae automáticamente en una instalación limpia) o una carpeta propia
   (OneDrive sincronizado, unidad Google Drive, carpeta compartida en Cowork o ruta local):
   ```powershell
   # Datos del repo
   python Scripts/generate_report.py --brand loco_tequila --output-dir Output

   # Datos propios del usuario (OneDrive, Google Drive, Cowork o Local)
   python Scripts/generate_report.py --brand loco_tequila --data-dir "Ruta/A/Mis_Datos" --output-dir Output
   ```
   Opcional: `--account-map "cuentas.csv"` (cuenta → vendedor → canal). Sin él, vendedor y canal
   se estiman por heurística y el reporte lo declara.

   **No hay margen bruto:** los archivos crudos no traen COGS por SKU. Todas las cifras monetarias
   son ingreso bruto, y el reporte lo dice explícitamente. No inventar márgenes.
4. **Flujo para Sullivan Rutherford Estate:**
   * **A) Selección de Cadencia:**
     - **Unificada (recomendada):** las dos cadencias en un solo HTML de 6 pestañas.
       Los bloques que ambos reportes decían igual aparecen una sola vez (mezcla de
       canales con selector mensual/semanal, Club, no clasificados, encabezado) y se
       conserva lo exclusivo: mapa Albers con puntos por ZIP y reconciliación al
       centavo del mensual, más cuentas por cobrar, aging y depletions del semanal.
       ```powershell
       python Scripts/generate_report.py --brand sullivan --cadence unified --data-source demo --period-label "April 2026" --output-dir Output
       ```
     - **Mensual:** Reconciliación contable DTC al centavo contra `FinancialReport` ($0.00 diferencia), Club Deep Dive y mapa Albers de envíos.
     - **Semanal:** Consolidación de 9 canales DTC, Tock, Open POs de Park Street con semáforo de aging (>30d crítico) y Depletions de Southern Glazer's (iDig 9L cases).
       El periodo y el nombre del archivo de salida se **derivan** de la fecha de
       pago más reciente del export; el desglose de depletions por estado se
       **deriva** del nombre del sitio de distribución del iDig, consolidando las
       regiones comerciales de un mismo estado (CA-North + CA-South -> CA).
   * **B) Selección de Fuente de Datos:**
     - **Datos Demo:** `Data_for_demo/Sullivan_data_demo/` (mensual) y
       `Data_for_demo/Sullivan_weekly_demo/` (semanal). Si no existen, generarlos:
       `python Scripts/make_demo_data.py`.
     - **Datos Propios del Cliente:** Preguntar al usuario por el origen de sus archivos:
       1. **OneDrive:** carpeta sincronizada en su equipo (ej. `C:\Users\<user>\OneDrive - Empresa\...`).
       2. **Google Drive:** unidad montada o carpeta local (ej. `G:\Mi unidad\...` o `G:\Shared drives\...`).
       3. **Carpeta de Cowork / Red local:** carpeta de trabajo en red o local del Cowork (ej. `Z:\Cowork\...` o `\\servidor\cowork\...`).
       4. **Ingesta directa de archivos:** rutas directas a `.xlsx` o `.csv` (mensual) o carpeta de insumos (semanal).
       *(Asistir al usuario recordando el atajo de Windows: `Shift + Clic derecho -> Copiar como ruta de acceso`).*
     - Precedencia automática: lo que indique el usuario > `Client_Data/` > demo.
       `Client_Data/` se excluye del paquete a propósito, así que en una instalación
       limpia se cae al demo y el proceso lo avisa.
   * **C) Qué columnas pide cada insumo:** `DATOS_REQUERIDOS.md`. Ahí está también
     el formato de los encabezados irregulares (el iDig de dos pisos, los layouts
     dispersos de Loco) que se leen por posición y no por nombre.
   * **D) Si el usuario pregunta qué datos entregar**, la respuesta corta y
     accionable está en `tutorial_datos_para_cliente.md` (bilingüe, con el comando
     de cada reporte). No improvisar la lista: esos documentos son la fuente.
5. **🏛️ Gobernanza de Diseño:**
   Todo reporte propuesto por el cliente en `Client_Reports` debe ser transformado bajo los manuales normativos de la carpeta `Designs/` (`Design_sullivan.md`, `Design_loco_tequila.md`, `Design_sttupa.md`).
6. **📊 Regla Estricta de Ordenamiento en Gráficas de Barras:**
   En todos los reportes (HTML y PDF, para todas las marcas), **todas las gráficas de barras deben estar ordenadas estrictamente de mayor a menor (orden descendente por importe o volumen)**.
7. **🎯 Presentación Ejecutiva:**
   Cero menciones de rutas internas de desarrollo (`Designs/...md`) en la interfaz final entregada al cliente.

---

## 💻 Guía de Ejecución por Entorno de IA y Modelo

### 1. OpenCode (CLI / IDE Agent)

* **Modelos recomendados**:
  * **DeepSeek V3 / R1 / V4 Pro**
  * **Kimi 3 / K1.5**
* **Ejecución activando Conda**:
  ```powershell
  & "E:\Users\1167486\AppData\Local\anaconda3\Scripts\conda.exe" shell.powershell hook | Out-String | Invoke-Expression; conda activate data_analytics_science; python Scripts/generate_report.py --brand sullivan --data-source demo --period-label "April 2026" --output-dir Output
  ```

---

### 2. Antigravity (Google DeepMind Agentic IDE)

* **Modelos recomendados**:
  * **Gemini 3.7 Flash** (Predeterminado para alta velocidad y precisión de código)
  * **Gemini 3.1 Pro / Ultra**
* **Ejecución Semanal Sullivan**:
  ```powershell
  & "E:\Users\1167486\AppData\Local\anaconda3\Scripts\conda.exe" shell.powershell hook | Out-String | Invoke-Expression; conda activate data_analytics_science; python Scripts/generate_report.py --brand sullivan --cadence weekly --output-dir Output
  ```
* **Ejecución Demo Loco Tequila USA**:
  ```powershell
  & "E:\Users\1167486\AppData\Local\anaconda3\Scripts\conda.exe" shell.powershell hook | Out-String | Invoke-Expression; conda activate data_analytics_science; python Scripts/generate_report.py --brand loco_tequila --output-dir Output
  ```

---

### 3. Claude Desktop y Claude Code

* **Modelos recomendados**:
  * **Claude Sonnet**
  * **Claude Opus**
* **Configuración en Claude Code (CLI)**:
  ```powershell
  python Scripts/generate_report.py --brand sullivan --cadence weekly --output-dir Output
  ```

---

### 4. Batería de humo — orden de ejecución para validar el repo completo

Todo dentro del ambiente Conda. Cada comando debe terminar sin traza de error.

```powershell
# 0. Regenerar los datos demo sintéticos (idempotente)
python Scripts/make_demo_data.py

# 1. Compilación de todos los scripts
python -c "import pathlib,py_compile; [py_compile.compile(str(p),doraise=True) for p in pathlib.Path('Scripts').glob('*.py')]; print('OK')"

# 2. Procesadores por separado (imprimen sus propios cuadres)
python Scripts/sullivan_weekly_processor.py --data-dir "Data_for_demo/Sullivan_weekly_demo"
python Scripts/loco_data_processor.py --data-dir "Data_for_demo/Loco_tequila_demo"

# 3. Los cuatro reportes — cada uno entrega HTML **y** PDF (--format all por omisión)
#    Repetir con --lang es: son OCHO entregables por idioma y hay que probar los dos.
python Scripts/generate_report.py --brand sullivan --data-source demo --period-label "April 2026" --output-dir Output
python Scripts/generate_report.py --brand sullivan --cadence weekly --weekly-data-dir "Data_for_demo/Sullivan_weekly_demo" --output-dir Output
python Scripts/generate_report.py --brand sullivan --cadence unified --data-source demo --period-label "April 2026" --output-dir Output
python Scripts/generate_report.py --brand loco_tequila --data-dir "Data_for_demo/Loco_tequila_demo" --output-dir Output

# 3b. Los mismos cuatro en español
python Scripts/generate_report.py --brand sullivan --data-source demo --period-label "April 2026" --lang es --output-dir Output
python Scripts/generate_report.py --brand sullivan --cadence weekly --weekly-data-dir "Data_for_demo/Sullivan_weekly_demo" --lang es --output-dir Output
python Scripts/generate_report.py --brand sullivan --cadence unified --data-source demo --period-label "April 2026" --lang es --output-dir Output
python Scripts/generate_report.py --brand loco_tequila --data-dir "Data_for_demo/Loco_tequila_demo" --lang es --output-dir Output

# 4. Empaquetado con autoverificación
.\package_skill.ps1
```

**Qué debe verificarse en la salida (no solo que no truene):**

* Mensual: `Reconciliación al centavo: True` y `diferencia: $0.00`, en demo y en real.
* Semanal: el periodo detectado debe corresponder a los datos, no a una constante;
  la suma de la mezcla de canales debe igualar el Total DTC.
* Loco con datos reales: inventario `220.65` cajas 9L (`CA 198.23` · `TX 22.42`),
  con las líneas no vendibles reportadas aparte.
* Los cuatro HTML: cero `nan`/`NaT`/`None`/`undefined` pintados, cero rutas
  internas (`Designs/*.md`, `Scripts/*.py`, `Client_Data`, rutas absolutas), y
  **todas** las gráficas de barras categóricas en orden descendente.
* El paquete: cero archivos de `Client_Data`/`Client_Documents`/`Client_Reports`,
  rutas con `/` (no `\`), sin colisiones de capitalización, y **cada ruta
  únicamente con `[A-Za-z0-9._/-]`**. El instalador rechaza el ZIP completo
  ("Zip file contains path with invalid characters") si encuentra un espacio, un
  apóstrofo, una coma o un corchete en cualquier entrada. Los dos empaquetadores
  ya revientan ahí, así que no hace falta revisarlo a mano.
  Por eso los archivos demo van con guiones (`Open-POs-demo-8.23.26.xlsx`)
  aunque el cliente entregue `Open PO's 8.23.26.xlsx`: los lectores hacen match
  **tolerante a la puntuación** (`_flexible_pattern` en
  `loco_tequila_us_relationships.py`, `find_file` en
  `Scripts/sullivan_weekly_processor.py`) y reconocen los dos nombres. Al añadir
  un insumo nuevo, el archivo que viaje en el paquete no puede llevar espacios.
* Cuidado con la carpeta de salida al probar: la exclusión va por nombre exacto,
  así que solo `Output` se excluye. Generar en `Output_check` o similar mete los
  entregables al ZIP (se nota como un salto de 108 a 116 entradas).
* Los cuatro PDF: cero desbordes de margen, cero `nan` impreso, y el número de
  páginas esperado (mensual 8 · semanal 5, **6 si hay varias semanas** ·
  unificado 7 · Loco 7). El rango vertical debe ser `23 .. 756` en los ocho
  (cuatro reportes × dos idiomas): cualquier valor negativo es contenido fuera
  de la hoja.
* **Semanal con varias semanas:** el `<select>` debe traer una opción por
  carpeta `Week_*`, y cambiar de semana debe repintar TODO el tablero, no solo
  el rótulo. La prueba útil es comprobar que el valor pintado coincide con el
  dato de ESA semana y que las semanas se ven distintas entre sí; si el selector
  no repintara, las filas saldrían idénticas y una prueba mal hecha pasaría.
  El WoW de la primera semana de la serie va en blanco, **no en 0.0%**: no hay
  con qué comparar, y un cero afirmaría que no cambió.
* **Idioma (`--lang es|en`):** los ocho entregables deben generar en los dos.
  Cuatro cosas que hay que comprobar y no son obvias:
  1. **La taxonomía NO se traduce** en ningún idioma (`Tasting Room`,
     `Founder's Club`, `Estate Club`, `Web / Ecommerce`, SKU, distribuidores,
     cuentas). Se garantiza porque esas cadenas no están en `Scripts/i18n.py`:
     lo que no está, no se toca.
  2. **Traducir es idempotente**: `t(t(x)) == t(x)` en los dos sentidos. Hace
     falta porque los PDF traducen dos veces —en `fit_text`, para medir el
     ancho sobre el texto que de verdad se dibuja, y en el canvas, para los
     `drawString` directos de las portadas—. Si una traducción al español
     dejara dentro una palabra que también es fragmento en inglés, el texto se
     degradaría en cada pasada.
  3. **La geometría del PDF no debe cambiar entre idiomas.** El español es
     15–25% más largo, así que se traduce ANTES de medir; si el rango vertical
     del PDF en español difiere del inglés, el recorte se está calculando sobre
     el texto equivocado.
  4. **Cobertura**: el punto débil del enfoque es que una etiqueta ausente del
     diccionario se queda en inglés sin avisar. Se mide instrumentando `i18n.t`
     durante una generación real y contando las cadenas que salieron sin
     cambio; ese número debe quedar en datos y taxonomía, no en etiquetas.
* Al añadir un texto visible nuevo, va también a `Scripts/i18n.py`. Un solo
  diccionario para los ocho entregables: ocho listas separadas garantizan que a
  la tercera corrección alguna quede desincronizada.

**Al tocar la maquetación de cualquier PDF**, la capa de dibujo es compartida
(`Scripts/pdf_common.py`), así que hay que revisar los cuatro, no solo el que se
editó. Antes de refactorizarla se toma una línea base (páginas, fragmentos de
texto, rectángulos, rango vertical) y se compara después: así se prueba que no
hubo regresión visual sin abrir el PDF.

### 5. Los cambios en Git los hace el usuario no el agente

No hacer `git commit`, `git push`, `git pull` ni ninguna otra operación de control de versiones. Todo lo relacionado con Git lo gestiona exclusivamente el usuario.
