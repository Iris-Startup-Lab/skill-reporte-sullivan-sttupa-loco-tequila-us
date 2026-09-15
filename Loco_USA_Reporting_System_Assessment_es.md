# Loco Tequila USA — Sistema de Reporte Semanal de Ventas

## Una evaluación: qué existe, qué produce y qué se necesitaría para dejarlo listo para producción

---

## 1. Por qué existe este documento

Ustedes compartieron la carpeta que contiene el sistema que genera semanalmente el
libro de trabajo **Sales Report Loco USA**. Lo revisamos por completo —cada módulo, cada
documento de reglas y cada salida generada— para responder a tres preguntas:

1. **¿Qué hay realmente allí dentro?** Un inventario preciso, para que nada dependa de la
   memoria de nadie.
2. **¿Qué produce?** Pestaña por pestaña, con las cifras reales que reporta actualmente.
3. **¿Qué se necesitaría para convertir esto en algo que se ejecute de manera confiable, para
   cualquiera, sin editar código a mano cada semana?** Incluyendo una lista honesta de lo que
   *no* debería trasladarse.

Hay algo importante que señalar de antemano, porque enmarca todo lo que sigue: **la lógica de
negocio de este sistema es la parte más valiosa, y se ha ganado a pulso con mucho esfuerzo.** El
código es reemplazable. Las reglas codificadas en él —la corrección de doble conteo, los alias de
cuentas, las conversiones de unidades, las correcciones históricas— representan meses de
descubrimientos reales, cada uno anotado junto al error que solucionó. Ese es el verdadero activo.
Las recomendaciones de este documento están orientadas a protegerlo.

---

## 2. Qué hay en la carpeta

**3,271 líneas de Python distribuidas en 20 módulos**, además de cuatro documentos de referencia,
cuatro archivos de datos históricos, ocho libros de trabajo generados y un subsistema separado de
captura de voz que almacena 108 MB de grabaciones de audio de campo.

### 2.1 El pipeline de datos — 18 módulos, 3,123 líneas

| Módulo | Líneas | Qué hace |
| :--- | ---: | :--- |
| `final_report.py` | 1,305 | El generador de reportes. Escribe las 9 pestañas. Esto es lo que se ejecuta. |
| `pipeline.py` | 248 | Carga la Lista Maestra de Cuentas desde los tres libros de trabajo de rutas de cada vendedor; realiza la coincidencia difusa (*fuzzy matching*) de cuentas; contiene las tablas de alias, consolidación y anulaciones (*overrides*). |
| `ca_load.py` | 257 | Ventas de SGWS (Signature) y Park Street California, año en curso más el histórico de 2025. Aplica tasas de margen FOB y DTR; redirige los seis pedidos conocidos del paquete Alebrije. |
| `inventory_load.py` | 183 | Inventario disponible (*on-hand*) de tres fuentes: SGWS, Park Street y Favorite Brands. Genera una fila por producto distribuida en ocho columnas de almacén. |
| `tx_monday_snapshots.py` | 173 | Lee cada captura de lunes de Favorite Brands y **calcula las diferencias (*diffs*) entre semanas consecutivas** para aislar el volumen semanal real. Omite intervalos que no sean de 7 días en lugar de atribuir incorrectamente un salto de varias semanas a una sola. |
| `acs_load.py` | 98 | Depletions históricos de ACS, desde 2024 hasta julio de 2025. Recorre 18 pestañas mensuales con nombres heterogéneos. |
| `mantarraya_load.py` | 81 | Shopify Memory Bottles: ventas privadas de Mantarraya más ventas de los representantes comerciales clave. Filtra por dos empleados y descarta un pedido reembolsado excluido permanentemente. |
| `dtc_load.py` | 77 | Tienda principal de Shopify. Contiene la corrección de etiquetas para pedidos multilínea y el desglose del paquete (*bundle explosion*) `OUR COLLECTION`. |
| `verify_totals.py` | 68 | Suite de verificación posterior a la ejecución. 16 aserciones. |
| `ydrink_load.py` | 62 | Reportes de Y Drink para las cuentas secundarias Clase B de Texas. |
| `sgws2025_load.py` | 60 | Histórico 2025 de SGWS. |
| `wholesale_load.py` | 59 | Entrada mayorista (*wholesale sell-in*) de Park Street; señala cualquier cliente fuera de los cuatro mayoristas conocidos. |
| `export_pdf.py` | 59 | Generación del reporte PDF complementario mediante LibreOffice. |
| `tx_load.py` | 58 | Favorite Brands Texas, año en curso. |
| `dtc_individuals.py` | 53 | Mapea etiquetas de pedidos a las 14 personas identificadas en DTC. |
| `tx2025_load.py` | 52 | Histórico 2025 de Favorite Brands. |
| `config.py` | 187 | Localiza la carpeta de entrada de la semana en curso y empareja cada archivo por palabras clave en lugar del nombre exacto. |
| `tx_weekly_ydrink.py` | 43 | **Código muerto** — reemplazado por `tx_monday_snapshots.py`, aún presente en disco. |

### 2.2 Los documentos de referencia — los archivos más valiosos de la carpeta

- **`docs/RULES.md` (15.6 KB, 12 secciones).** La verdadera lógica de negocio. Tasas de margen,
  conversiones de unidades, la regla de doble conteo de Melrose Gas, la jerarquía de Clase B,
  definiciones de pedidos, tablas de alias y consolidaciones, correcciones históricas únicas,
  convenciones de formato. Su propio README indica leer esto antes de tocar cualquier código, y es
  un consejo totalmente acertado.
- **`docs/KNOWN_ISSUES.md`.** Aspectos simplificados o aproximados en la última entrega. Vale la
  pena destacar que tres de los seis puntos enumerados aquí **ya han sido corregidos** en el
  código, por lo que este archivo actualmente subestima las capacidades del sistema.
- **`docs/INPUT_FILE_REFERENCE.md`.** Las 14 fuentes de entrada esperadas y sus patrones de nombres
  de archivo.
- **`README.md`.** Instrucciones de ejecución. Actualmente desactualizado en parte: los pasos 2 y 3
  indican editar a mano rutas y fechas en el código fuente cada semana, algo que `config.py` ya ha
  automatizado.

### 2.3 Datos de referencia que nunca se actualizan

`static/` almacena cuatro archivos históricos únicos que suman 212 KB: depletions de Texas 2025 de
Favorite Brands, datos completos de Park Street 2025, SGWS 2025 y la captura de reportes de
Y Drink. Una quinta fuente histórica, el resumen de depletions de ACS 2024–2025, se referencia
mediante una ruta absoluta en lugar de estar copiada en el proyecto.

### 2.4 El subsistema de captura de voz para visitas de campo

`Field Sales Reports/` — 148 líneas distribuidas en dos scripts, más **93 archivos de audio
(~108 MB)** y 92 transcripciones. Transcribe notas de voz de los representantes localmente y luego
utiliza un modelo de IA para extraer datos estructurados de visitas (cuenta, tipo de activación,
artículos del pedido) en archivos CSV para revisión humana.

La Sección 5.2 trata esto por separado, ya que nuestra recomendación difiere del resto.

### 2.5 Las salidas generadas

Siete libros de trabajo semanales en `outputs/`, del 20 de julio al 31 de agosto de 2026, cada uno
de aproximadamente 120 KB — más un archivo independiente `2025 vs 2026 Depletions Comparison.xlsx`
que ningún componente del código lee ni escribe, por lo que parece mantenerse manualmente.

**Un punto estructural de enorme relevancia:** el reporte semanal se construye
**copiando el libro de trabajo de la semana anterior y sobreescribiendo las celdas de datos**. No
existe un archivo plantilla. Todo el formato, encabezados, celdas combinadas, formatos numéricos —y
todo el registro histórico de 2024 y 2025— existen *únicamente dentro de esos archivos `.xlsx`*. Si
se pierde `outputs/`, la estructura y el historial del reporte desaparecen con ella.

---

## 3. Qué produce el sistema

### 3.1 El libro de trabajo — nueve pestañas

Verificado contra `Sales Report Loco USA August 31, 2026.xlsx`.

| # | Pestaña | Contenido |
| :--- | :--- | :--- |
| 1 | **YTD Summary** | Diez métricas por región: depletions en cajas de 9L y botellas, margen bruto, margen bruto por caja de 9L, recuento de cuentas On-premise y Off-premise, cantidad de pedidos, tamaño promedio de pedido en botellas y margen bruto. Filas para TOTAL, California, Texas, DTC y Ecommerce; luego una fila por cada vendedor; después un bloque de **Wholesale** para los cuatro distribuidores en cajas de 9L e ingresos; un bloque de **Direct to Retail**; y un bloque de **Product** para nueve SKUs. |
| 2 | **Monthly Summary** | Las mismas regiones a lo largo de los doce meses, en cuatro bloques apilados: botellas, margen bruto, 9L mayorista, ingresos mayoristas. |
| 3 | **Salesperson by Week** | Semanas 1 a 52 en las filas, una columna por representante comercial, más una fila de acumulado anual (YTD). |
| 4 | **Accounts H2-2026** | Cada cuenta × Julio–Diciembre, con YTD de año completo, vendedor, canal y cuenta matriz Clase B. Ubicada antes de H1 por su convención interna. |
| 5 | **Accounts H1-2026** | Lo mismo, para Enero–Junio. |
| 6 | **Account Summary Total Business** | Botellas y margen bruto históricos por cuenta; cantidad de pedidos en 2026, 2025, 2024 e histórico general; promedio de meses entre pedidos; fecha del último pedido; días transcurridos desde el último pedido; canal; vendedor. |
| 7 | **DTC Sales by Month** | Doce meses × (botellas, margen bruto) en tres secciones: por producto, por las 14 personas identificadas en DTC, y comercio electrónico (*ecommerce*). |
| 8 | **DTC Sales by Year** | 2026, 2025, 2024 y consolidado. Solo 2026 se recalcula; el historial se conserva tal cual en su lugar. |
| 9 | **Inventory** | Cada producto desglosado en total general 9L, total CA, total TX, SO CAL SGWS, NOR CAL SGWS, CA Park Street, Texas FB, pedidos abiertos y producto en tránsito (*inbound*) — más un bloque separado de no vendibles / muestras (*samples*). |

**Una pestaña especificada en `RULES.md` no existe: Overdue Accounts (Cuentas Vencidas).** Las
secciones 9 y 10 la definen, incluida la fórmula para el umbral de vencimiento, pero ningún código la
construye y no está presente en el libro de trabajo.

### 3.2 Las cifras que reporta actualmente

A partir del libro de trabajo del 31 de agosto, para tener una escala concreta:

| | Cajas 9L | Botellas | Margen bruto | MB / 9L | On-prem | Off-prem | Pedidos |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **TOTAL** | **90.67** | **1,088** | | | 97 | 43 | |
| California | 46.08 | 553 | $27,835.60 | $604.03 | 34 | 20 | 110 |
| Texas | 27.08 | 325 | $14,316.66 | $528.62 | 63 | 23 | 63 |

Inventario en la misma fecha: **212.98** cajas equivalentes de 9L en total — CA 196.07, TX 16.92.

Y a partir de la comparación de depletions: 2025 cerró con 992 botellas y $46,701 de margen bruto;
2026 se sitúa en 1,051 botellas y $56,708 — **+5.9% en volumen pero +21.4% en margen**. Excluyendo
a Total Wine, la misma comparación muestra un crecimiento de +86.3% y +89.8%.

### 3.3 El reporte PDF complementario

`export_pdf.py` define áreas de impresión a partir de los límites de contenido reales, ajusta cada
hoja al ancho en orientación horizontal (vertical únicamente para *Salesperson by Week*), repite la
fila de encabezados, agrega pies de página y luego convierte mediante LibreOffice.

### 3.4 La suite de verificación

`verify_totals.py` ejecuta 16 aserciones con una tolerancia de 5 centavos y se detiene con error ante
cualquier discrepancia. Cada una valida que una fila TOTAL sea exactamente igual a la suma de las
filas de detalle bajo ella, a lo largo de YTD Summary, Monthly Summary, ambas pestañas de DTC,
Inventory y Salesperson by Week.

Existe debido a que anteriormente se enviaron dos errores reales: un TOTAL regional que incluía a
Melrose de manera silenciosa, y una columna de años combinados que omitía valores por una
incompatibilidad de tipos numéricos. El principio que aplica —*si una fila dice TOTAL, debe ser un
total exacto de las cifras debajo de ella*— es el correcto, y lo hemos adoptado íntegramente.

Dos verificaciones cruzadas que `RULES.md` identifica como detectoras de errores reales **no están**
en la suite automatizada y se mantienen manuales: que el total semanal de cada representante iguale
su total en el YTD Summary, y que el conteo de cuentas On-premise coincida con la fila regional.

---

## 4. Qué se puede rescatar y trasladar

La mayor parte del valor, y a un costo menor del que cabría esperar — porque las partes verdaderamente
valiosas son **reglas, no código**.

| Qué | Por qué se transfiere de forma óptima |
| :--- | :--- |
| **Tasas de margen por botella** — FOB para tres niveles (*three-tier*), DTR para venta directa a minoristas (*direct-to-retail*) y DTC, incluidas las dos tarifas de Aureo según el canal | Pasa a ser un archivo de configuración editable que ustedes pueden actualizar directamente, sin tocar código. Este único elemento nos permite reportar margen bruto, algo que antes no era posible. |
| **Conversiones de unidades** — ×6 para equivalencias de cajas de 4.5L, manejo de unidades por fila de Park Street, ÷12 para cajas de 9L con la excepción de 200 mL en ÷45 | Pequeño, exacto y fácil de verificar |
| **Mapeo cuenta → vendedor → canal** | Deducible directamente de sus pestañas Accounts H1/H2. Es el elemento de mayor impacto individual: es lo que actualmente deja una gran porción del volumen de California sin atribuir. |
| **Tablas de alias y consolidación de cadenas** | Se convierten en archivos de datos en lugar de constantes fijas en el código |
| **Definiciones de pedidos** — California como cuenta y fecha, Texas como cuenta y semana con incremento, DTC como IDs de pedidos distintos | Permite los recuentos de pedidos YTD que solicitaron |
| **La asignación por defecto de Texas** y la regla de ignorar el campo de vendedor propio de ACS | Dos líneas de regla, atribución sustancialmente superior |
| **El método de diferencias entre capturas de lunes (*Monday-snapshot diffing*)** | La única forma rigurosa de obtener el volumen semanal real de Texas a partir de reportes acumulados. Tienen 119 capturas semanales; hoy solo se lee la más reciente. |
| **La corrección multilínea de Shopify, el comparador de cuentas por límites de palabra (*word-boundary*), la invariante de suma en filas totales** | Cada uno de estos es un error real ya identificado y resuelto. Rediseñarlos desde cero sería un desperdicio. |

Lo que obtienen a cambio:

- **Sin edición semanal de código.** Se apunta a una carpeta; el sistema detecta lo que hay, reporta
  lo que encontró y lo que falta, y genera a partir de ello.
- **Margen bruto en nuestros reportes**, lo cual antes era imposible.
- **Historial de versiones.** Cada cambio queda registrado y cada estado previo es recuperable.
- **Ejecución en cualquier equipo** — Mac, Windows o en el navegador — sin requerir configuración de
  Python, sin LibreOffice y sin suposiciones sobre rutas de Google Drive.
- **Un dashboard interactivo junto con el libro de trabajo**, con una pestaña que indica de qué
  archivo y columna proviene cada número, y un desglose de cada línea no atribuida junto con el
  motivo por el que no pudo asignarse.
- **Un libro de trabajo con tablas dinámicas y gráficos interactivos** construidos sobre un único
  conjunto de datos subyacente — de modo que cualquier cifra puede desglosarse a fondo (*drill-down*),
  y los totales se recalculan de forma independiente en Excel como comprobación cruzada. Sus libros
  actuales no contienen tablas dinámicas ni gráficos nativos; cada valor es estático.

---

## 5. Qué no debería trasladarse

### 5.1 El modelo de libro de trabajo por copia sucesiva ("copy-forward")

No porque esté mal implementado —es ingenioso dadas las limitaciones— sino porque su estructura y
todo su historial residen únicamente dentro de los archivos generados. No existe una plantilla bajo
control de versiones. Reproducir ese modelo implicaría heredar esa fragilidad, solo para entregarles
el mismo archivo de Excel que ya poseen.

En su lugar, construimos a partir de una plantilla versionada sin datos, lo que permite recuperar el
diseño de manera independiente a cualquier salida producida.

### 5.2 El subsistema de transcripción de voz

Recomendamos dejar este apartado de lado, y la razón no es exclusivamente técnica.

**Técnicamente**, no puede ejecutarse en el mismo entorno que la generación de reportes. Dicho
entorno no cuenta con acceso a internet ni permite instalar software, y este pipeline requiere
`ffmpeg` instalado, un modelo de voz descargado y una clave de API con acceso a la red. Son factores
incompatibles.

**Sin embargo, el argumento de mayor peso radica en el flujo de trabajo en sí.** Al observar el
estado actual:

- 92 transcripciones están en espera de extracción.
- La carpeta de aprobados está **vacía** — el ciclo de revisión nunca se ha completado una sola vez,
  de extremo a extremo.
- Hay cuatro carpetas de audio por vendedor dentro de la bandeja de entrada donde el script no puede
  verlas, ya que solo lee archivos en el nivel superior. Esos audios jamás se procesarían, sin
  importar cuánto tiempo se ejecutara.

Además, el resultado final de toda esa maquinaria es un conjunto pequeño de campos estructurados:
cuenta, fecha, vendedor, tipo de activación y artículos del pedido. Un representante comercial
podría ingresarlos en menos de un minuto mediante un formulario en su teléfono, de forma correcta
desde el primer intento, sin etapas de transcripción ni personas revisando manualmente cada fila
extraída después.

Su propia documentación ya califica esto como Fase 2, desacoplado del reporte semanal. Coincidimos —y
vamos un paso más allá: **capturen los datos estructurados directamente en el punto de origen.** Las
93 grabaciones ya existentes no se desperdician; constituyen un excelente insumo para definir qué
campos debe incluir el formulario.

Si con el tiempo desean implementar el flujo de transcripción, este pertenece a una herramienta
independiente en una computadora estándar, integrando sus CSVs revisados como una fuente de entrada
más. No debe formar parte del sistema central de reportes.

### 5.3 Supuestos dependientes de una máquina específica

Tres aspectos atan el sistema a una sola computadora y a una sola persona:

- **Tres rutas absolutas de Google Drive** para los libros de trabajo de rutas, la carpeta de capturas
  de lunes y el archivo de ACS.
- **El proyecto debe ubicarse dentro de la carpeta de Drive** que contiene las carpetas de datos
  semanales, ya que las entradas se buscan de forma relativa al directorio padre del propio proyecto.
- **Dos comportamientos exclusivos de macOS** que impiden su funcionamiento en Windows: un indicador
  de formato de fecha que genera error, y el proceso de conversión de LibreOffice con gestión de rutas
  exclusiva para entornos POSIX.

Ninguno de estos problemas es complejo de resolver. Se señalan porque explican por qué el sistema
actualmente solo funciona en una máquina específica.

### 5.4 Elementos menores que conviene retirar

- **El año 2026 está fijado de forma rígida (*hardcoded*)** en cinco lugares como año actual. No
  cambiará automáticamente de ciclo.
- **Un módulo inactivo** (`tx_weekly_ydrink.py`) que sigue existiendo en el disco.
- **Una dependencia listada que nunca se utiliza**, y **otra utilizada pero no listada** — por lo que
  una instalación limpia falla a mitad del proceso.
- **Desfase en la documentación**: `RULES.md` todavía describe el cálculo neto de Melrose que fue
  eliminado deliberadamente en agosto; `INPUT_FILE_REFERENCE.md` señala que los tres cargadores de
  inventario nunca fueron reconstruidos, cuando en realidad existen y funcionan.

---

## 6. Qué se necesita para dejarlo listo para producción

### 6.1 Archivos que necesitamos de su parte

| Archivo | Motivo |
| :--- | :--- |
| **Libro de costos por botella y margen bruto (*Bottle Costs and Gross Margin*)** | Su archivo `INPUT_FILE_REFERENCE.md` lo menciona como la fuente de las tasas de margen, que actualmente están transcritas directamente en el código. Requerimos el archivo original, o la confirmación por escrito de las tarifas, antes de publicar cualquier cifra de margen. |
| **La Lista Maestra de Cuentas (*Master Account List*)**, en su versión vigente | `RULES.md` señala que se solicitó una versión actualizada y aún no ha sido recibida. Esto es lo que determina la atribución de vendedor y canal. |
| **El resumen de depletions de ACS 2024–2025** | Referenciado por ruta absoluta, nunca copiado dentro del proyecto. Es el fundamento de todas las métricas históricas por cuenta. |
| **Una carpeta completa de insumos semanales** | Disponemos del código y de las salidas, pero no de las entradas en bruto, por lo que actualmente nada puede ejecutarse ni conciliarse de principio a fin. |

### 6.2 Decisiones que solo ustedes pueden tomar

1. **Melrose Gas y Shopify.** Su reporte trata a Melrose como entrada mayorista (*sell-in*) a su propio
   almacén y excluye del volumen los pedidos de Shopify no etiquetados. El nuestro actualmente suma
   DTC por encima del depletion de Melrose. **Esto genera totales distintos, y ambos no pueden
   conciliarse hasta que determinen cuál criterio es el correcto.** Es el tema pendiente más
   importante.
2. **Las dos tasas de margen de Aureo.** ¿Qué fuentes se contabilizan como mayorista de Park Street a
   $614.50 y cuáles como DTC a $864.50?
3. **El valor predeterminado de Texas** — cuentas no coincidentes asignadas a Joe Pat Clayton y
   Off Premise. Aplicarlo modifica sustancialmente la tabla de posiciones de los representantes.
   ¿Se confirma este criterio?
4. **Las seis consolidaciones de cadenas aprobadas**, y enrutar todo lo que comience con "TOTAL WINE"
   hacia una fila consolidada bajo Sara. ¿Se confirma que siguen vigentes?
5. **Las correcciones históricas únicas** descritas en la sección 7 de `RULES.md` — ¿deben seguir
   aplicándose o han quedado sin efecto?
6. **Visibilidad del margen bruto.** ¿Solo agregado a nivel global, o detallado por cuenta y por
   vendedor?
7. **La pestaña de Cuentas Vencidas (*Overdue Accounts*)** — especificada pero nunca construida.
   ¿Desean incorporarla?
8. **¿Qué nivel de detalle en bruto debe incluir el entregable?** Un dataset subyacente único con una
   fila por transacción, incluyendo nombres de cuentas y representantes comerciales, es lo que hace
   posible el análisis detallado (*drill-down*) y la verificación. Es también el archivo más sensible
   que generaríamos: cualquiera con acceso a él puede reconstruir todo el negocio. La decisión de
   quién lo recibe queda en sus manos.

### 6.3 Qué haríamos nosotros de todos modos

- Extraer cada regla del código y llevarla a archivos de configuración editables, de forma que tasas,
  alias y mapeos puedan actualizarse sin la intervención de un desarrollador.
- Reemplazar las cuatro etiquetas distintas de "desconocido" por una jerarquía de atribución
  unificada y ordenada donde cada línea indique la regla que la resolvió — y cada línea no resuelta
  especifique la causa exacta.
- Conservar las validaciones de suma en filas totales, pero ancladas a rangos derivados en lugar de
  números de fila fijos. Su suite actual se descalibra cada vez que se inserta una fila, y el propio
  comentario de cabecera advierte que esto ya sucedió.
- Incorporar a la suite automatizada las dos comprobaciones cruzadas manuales que `RULES.md`
  identifica como eficaces para detectar anomalías.
- Procesar las 119 capturas de lunes en lugar de únicamente la última, lo que permitirá generar una
  vista semanal real de Texas.

---

## 7. El riesgo que vale la pena nombrar

Su propio README lo expresa con mayor elocuencia de la que usaríamos nosotros:

> *"Este proyecto fue reconstruido anteriormente a partir de la memoria de una persona tras un largo
> historial de chat luego de reiniciar el entorno — eso es frágil y propenso a errores."*

Ese fue el diagnóstico correcto y la redacción de `RULES.md` fue la respuesta adecuada. Sin embargo,
la vulnerabilidad no se ha cerrado por completo:

- **La estructura del libro de trabajo y su historial 2024–2025 existen únicamente dentro de los
  archivos de salida.** No hay plantilla ni registro independiente.
- **Tres de las catorce fuentes de entrada solo son accesibles a través de las rutas de Drive de una
  sola persona.**
- **`RULES.md` y el código ya han divergido** en al menos dos aspectos, lo que significa que el
  registro documental y el comportamiento efectivo ya no coinciden.
- **El sistema opera en una única máquina**, y no iniciaría en un equipo con Windows.

Nada de esto es crítico en el sentido de que el reporte de esta semana esté en peligro inminente. Es
crítico en el sentido de que el conocimiento se encuentra concentrado de tal manera que el fallo de
una sola computadora portátil, o la ausencia de una sola persona, dejaría el proceso al descubierto.

---

## 8. Qué recomendamos

**Conserven las reglas, no el libro de trabajo.**

Trasladen las tasas de margen, las conversiones de unidades, el mapeo de cuentas, las tablas de
alias, las definiciones de pedidos y las soluciones obtenidas con tanto esfuerzo — todo ello como
configuración accesible y editable. Generen a partir de allí un dashboard, un PDF y un libro de
trabajo de Excel con tablas dinámicas interactivas sobre un único conjunto de datos subyacente, de
manera que cada cifra pueda rastrearse hasta el archivo y la columna de origen y recalcularse de
manera independiente.

Mantengan su libro de trabajo actual operando en paralelo hasta que ambos concuerden, número por
número, sobre los datos de la misma semana. Esa comparación constituirá la prueba de aceptación, y es
además la única vía honesta para resolver la cuestión de Melrose.

Dejen de lado la captura por voz; si los datos de visitas de campo resultan indispensables, captúrenlos
como datos estructurados directamente en el momento de la visita en lugar de intentar
reconstruirlos a partir de grabaciones de audio después.

---

*Elaborado a partir de la revisión exhaustiva de la carpeta compartida: los 20 módulos de Python, los
cuatro documentos de referencia, los cuatro archivos de datos históricos y los ocho libros de trabajo
generados. Las cifras citadas corresponden al libro de trabajo del 31 de agosto de 2026 y a la
comparación de depletions 2025 vs 2026.*
