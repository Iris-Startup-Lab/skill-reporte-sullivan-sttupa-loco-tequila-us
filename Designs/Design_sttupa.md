# Design.md — Reporte Ejecutivo · Sttupa Estate

Documento de sistema de diseño para adaptar la arquitectura de reportes ejecutivos
(PDF + XLSX + Dashboard HTML), usada como base `Design_loco_tequila.md`, a la marca
**Sttupa Estate** (operación en Estados Unidos — Napa Valley).

> ⚠️ **Nota sobre datos de negocio:** los HEX, tipografías y activos de logo de este
> documento provienen directamente de `Sttupa_Toolkit_250328 1.pdf` (Brand Toolkit
> oficial) y son fuente única de verdad. El **catálogo de "productos"** (aquí: tipos
> de villa/habitación) y el **mapeo de canales de venta** (reservas directas, OTA,
> agencias, corporativo, walk-in) **no vienen documentados** en el toolkit de marca —
> deben confirmarse con el archivo de datos de ventas/ocupación real antes de
> implementar el generador (ver Bloque B de `knowledge_for_another_reports.md`). Las
> tablas de la §5 usan las 5 habitaciones temáticas conocidas como placeholder
> estructural.

---

## 1. Identidad y meta

| Campo | Valor |
|---|---|
| Marca | Sttupa Estate |
| Tagline comercial | **"Curated by art & nature"** |
| Título del reporte sugerido | **Ocupación y Ventas** (placeholder — confirmar con negocio) |
| Subtítulo | `De la Semana {NN}-{AAAA}` (mismo patrón que Loco Tequila) |
| Logo | `Stupa-White.svg/png` sobre fondo oscuro; `Stupa-Black.svg/png` sobre fondo claro |
| Ubicación de logos | `Imagenes_iconos/Stupa-Black.svg`, `Stupa-Black.png`, `Stupa-White.svg`, `Stupa-White.png` |
| Idioma | Inglés (US) — la marca es 100% en inglés en todo material oficial |
| Moneda | USD, formato `$1,889` (miles, sin decimales; Ticket Promedio con 2 decimales) |
| Posicionamiento | Lujo, arte y naturaleza; fotografía cinematográfica, tono editorial y sobrio |
| Numeración | Número de página abajo a la derecha (heredado del patrón Loco) |

---

## 2. Paleta de color (tokens)

### 2.1 Marca / estructura (Master Brand — pág. 3 del toolkit)

| Token | HEX | Pantone | Uso |
|---|---|---|---|
| `--brand-charcoal` | `#3F3D3B` | Black 7 C | Banda de encabezado, títulos de sección, fondo primario de marca |
| `--brand-copper` | `#C7AC96` | 480 C | Acento cálido — resaltados, íconos secundarios |
| `--brand-stone-gray` | `#8B8D8E` | 480 C (gris) | Subtítulos, líneas divisorias, texto secundario |
| `--header-text` | `#FFFFFF` | — | Texto sobre banda charcoal |
| `--page-bg` | `#FFFFFF` | — | Fondo de página |
| `--rule-line` | `#D9D9D9` | — | Líneas divisorias / borde inferior de página |

### 2.2 Colores por HABITACIÓN/VILLA (Estate Rooms — pág. 5 del toolkit)

Estos son los colores canónicos de las 5 habitaciones temáticas de Sttupa Estate.
Si el negocio confirma un catálogo distinto de "productos" (ej. tipos de reserva,
paquetes, experiencias), remapear conservando esta paleta como base cromática de marca.

| Orden | Habitación / Villa | Token | HEX | Pantone |
|---|---|---|---|---|
| 1 | Pa Vinea | `--r-pavinea` | `#E7C372` | 141 C (dorado) |
| 2 | Loco | `--r-loco` | `#BF001C` | 199 C (rojo) |
| 3 | Vineyard | `--r-vineyard` | `#969150` | 5767 C (oliva) |
| 4 | Sanctuary | `--r-sanctuary` | `#E3D3C2` | 7527 C (arena) |
| 5 | Poetry | `--r-poetry` | `#451B0F` | 4625 C (vino/madera) |

### 2.3 Colores de CANAL (placeholder — pendiente de confirmar con negocio)

No existe una definición de canales de venta en el brand toolkit (es una guía de
identidad, no de operación). Sugerido, a validar con el cliente:

| Canal (tentativo) | Token | HEX (tentativo) |
|---|---|---|
| Reserva Directa (web/teléfono) | `--c-directa` | `#3F3D3B` (charcoal) |
| OTA (Booking, Expedia, etc.) | `--c-ota` | `#8B8D8E` (gris) |
| Agencias de viaje | `--c-agencias` | `#C7AC96` (copper) |
| Corporativo / Eventos | `--c-corporativo` | `#969150` (oliva) |
| Walk-in / Referido | `--c-walkin` | `#E7C372` (dorado) |

### 2.4 Elementos de gráfica y estados

| Token | HEX (heredado del patrón Loco, a validar) | Uso |
|---|---|---|
| `--chart-plan-line` | `#BF001C` | Línea de "Plan / Presupuesto de ocupación" |
| `--chart-lastyear-area` | `#E3D3C2` | Área rellena "Año Pasado" (tono Sanctuary) |
| `--chart-grid` | `#E2E2E2` | Cuadrícula horizontal / ejes |
| `--chart-label` | `#3F3D3B` | Etiquetas de dato |
| `--highlight-cream` | `#E3D3C2` | Columna/fila resaltada ("Año/Semana Actual", Totales) |
| `--pos-value` | `#3F3D3B` | Variación positiva / neutra |
| `--neg-value` | `#BF001C` | Variación negativa (color Loco room) |

---

## 3. Tipografía

| Rol | Familia | Peso | Fuente / disponibilidad |
|---|---|---|---|
| Título de marca / signage / naming | **Solido Condensed** | Light, Book, Medium | Fuente oficial de marca — **no incluida** en `Fonts/Font_sttupa` (solo se descargó Inria). Conseguir licencia o usar fallback condensado (ej. "Oswald", "Bebas Neue") si no se consigue. |
| Títulos secundarios / encabezados de sección | **Inria Serif** | Light, Regular | ✅ Disponible en `Fonts/Font_sttupa/Inria_Serif/` (Light, Regular, Bold, Italic, LightItalic, BoldItalic) |
| Cuerpo de texto / tablas | **Inria Sans** | Light, Regular | ⚠️ Mencionada en el toolkit pero **no está** en la carpeta `Fonts/Font_sttupa` (solo Inria Serif). Descargar de Google Fonts antes de producción, o sustituir temporalmente por Inria Serif Regular. |
| Barra de título de gráfica | Inria Serif | Bold, blanco sobre charcoal | 9–10 pt |

Alineación numérica: **derecha** en todas las celdas de valor. Etiquetas de fila: **izquierda**.
Tracking amplio (letter-spacing) en títulos, imitando el estilo editorial del toolkit
("BRAND TOOLKIT", "ESTATE ROOMS", nombres de villa en mayúsculas espaciadas).

---

## 4. Estructura de página

```
┌───────────────────────────────────────────────┐
│  BANDA CHARCOAL (#3F3D3B)  Título · Semana  LOGO│  ← --brand-charcoal, logo Stupa-White
├───────────────────────────────────────────────┤
│  Título de sección          (Por Habitación/Canal)│  ← Inria Serif, charcoal
│                                                 │
│  [Leyenda / desglose]   [Tabla resumen]         │
│  o                                              │
│  [Bloque de tablas SEMANAL/ANUAL]               │
│                                                 │
│  [Barra charcoal: "Ventas netas por ... $X"]    │
│  [Gráfica 1]                                    │
│  [Barra charcoal: "Noches vendidas por ... N"]  │
│  [Gráfica 2]                                    │
├───────────────────────────────────────────────┤
│  línea gris                                  #N │
└───────────────────────────────────────────────┘
```

---

## 5. Esquemas de TABLA (estructura heredada de Loco Tequila, adaptada)

> Sustituir "producto" → habitación/villa; "botellas" → noches/reservas cuando se
> confirme el modelo de datos real.

### 5.1 Tabla Resumen (Canal × Habitación)

- **Columnas (5 + total):** `Pa Vinea | Loco | Vineyard | Sanctuary | Poetry | Total`
- **Filas (5 + total):** `Reserva Directa | OTA | Agencias | Corporativo | Walk-in | Total`
- Fila `Total` y columna `Total` con fondo `--highlight-cream`, negrita, `$valor (%)`.

### 5.2 Tabla de detalle (bloques por canal)

Igual patrón que Loco (§5.2): bloques por canal con clientes/agencias top, cierre con
`Ventas Netas {AAAA}` y `Participación %` resaltados en `--highlight-cream`.

### 5.3 Tabla histórica mensual

Columnas = 5 habitaciones + Total; filas = meses año anterior + año actual. Gráfica de
barras apiladas por habitación + línea `Total` en `--chart-plan-line`.

### 5.4 Tabla "Ventas Totales / {Habitación}" — SEMANAL y ANUAL

Misma estructura de 3 zonas que el reporte Loco (§5.4):

**Zona A:** `Semana Año Ant.` | `Semana Anterior` | `Plan` | `Semana Actual` (resaltada)
**Zona B:** `Semana {NN} - {AAAA} / Del {fecha} al {fecha}`
**Zona C — Variaciones vs:** `Plan` | `Semana Anterior` | `Año Anterior` (negativas en `--neg-value`)

Filas — versión "Por Habitación":
```
Pa Vinea
Loco
Vineyard
Sanctuary
Poetry
Ventas Netas Semanales / Anuales   ▓
Ocupación %
#Noches Vendidas
Tarifa Promedio (ADR, USD) $
```

### 5.5 Nota de celdas vacías

`$0` / `0` / `0%` explícitos, nunca en blanco (mismo criterio que Loco §5.5).

---

## 6. Especificación de GRÁFICAS

### 6.1 Resumen (portada) — ≤4-5 categorías → **Dona** permitida
- Segmentos = 5 habitaciones (§2.2), colores en orden fijo.
- Centro: `${Total}` + `Total de ventas`.
- Leyenda derecha: bullet · nombre · `$valor` · píldora con `%` (tono copper `#C7AC96`).

### 6.2 Barras apiladas + línea (histórico mensual)
- Eje X: meses. Barras apiladas por habitación (§2.2).
- Línea `--chart-plan-line` = Plan/Presupuesto, con etiqueta por mes.
- Separador vertical punteado entre años.

### 6.3 Combo por semana/mes (fichas por habitación/canal)
Dos gráficas por página, dentro de barra de título charcoal:
1. `Ventas netas por semana/mes ($): ${total}`
2. `Noches vendidas por semana/mes: {total}`

Capas: área `--chart-lastyear-area` (Año Pasado) + barras apiladas por canal o
habitación + línea `--chart-plan-line` (Plan) + etiquetas de dato + leyendas inferiores.

---

## 7. Inventario de páginas (propuesto, a validar con negocio)

| Pág. | Contenido |
|---|---|
| 1 | Resumen Ventas Anual (desglose + matriz + detalle por canal) |
| 2 | Resumen Ventas Semanal |
| 3 | Histórico mensual |
| 4–5 | Ventas Totales Por Habitación (Semanal / Anual) |
| 6–7 | Ventas Totales Por Canal (Semanal / Anual) |
| 8–17 | Una habitación por par de páginas (Pa Vinea, Loco, Vineyard, Sanctuary, Poetry) × (Semanal + Anual) |

---

## 8. Reglas de formato numérico (USD)

| Métrica | Formato | Ejemplo |
|---|---|---|
| Ventas ($ miles) | `$` + separador de miles, sin decimales | `$1,889` |
| Participación / variación | entero + `%` | `47%`, `-12%` |
| #Noches Vendidas | entero | `2,829` |
| Tarifa Promedio (ADR) | `$` con 2 decimales | `$1,450.00` |
| Variación negativa | color `--neg-value`, con signo `-` | `-$487` / `-12%` |
| Fechas | `MMM D, YYYY` (formato US) | `Aug 26, 2026` |

---

## 9. Checklist de replicación para la skill

1. Banda `--brand-charcoal` con título + subtítulo `Week {NN}-{AAAA}` + logo `Stupa-White`.
2. Respetar orden y color de las 5 habitaciones (§2.2) en toda gráfica y tabla.
3. Resaltar en `--highlight-cream` (tono Sanctuary) la columna/fila de Totales y periodo actual.
4. Variaciones negativas en `--r-loco` (#BF001C).
5. Confirmar con negocio: catálogo real de "productos" (¿habitación, paquete, experiencia?)
   y canales de venta antes de programar `data_processor.py` — no están en el brand toolkit.
6. Tipografía: usar Inria Serif como disponible; conseguir Solido Condensed e Inria Sans
   antes de producción final (ver §3).
7. Logos oficiales en `Imagenes_iconos/Stupa-Black.*` y `Stupa-White.*` (SVG preferido para PDF).
8. Numeración de página abajo-derecha. Formatos numéricos de §8 (USD, formato US).
9. Idioma del reporte: inglés (US) en todos los textos y encabezados.
