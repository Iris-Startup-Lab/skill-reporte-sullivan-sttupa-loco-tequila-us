# Design.md — Reporte Ejecutivo · Sullivan Rutherford Estate

Documento de sistema de diseño para adaptar la arquitectura de reportes ejecutivos
(PDF + XLSX + Dashboard HTML), usada como base `Design_loco_tequila.md`, a la marca
**Sullivan Rutherford Estate** (viñedo/bodega, operación en Estados Unidos — Napa Valley).

> ⚠️ **Nota sobre datos de negocio:** los HEX, tipografía y activos de logo de este
> documento provienen directamente de `Sullivan_SRE Brand Guidelines.pdf` (Brand
> Guidelines oficial, Canva) y son fuente única de verdad. El **catálogo de SKUs de
> vino** y el **mapeo de canales de venta** (wine club/DTC, tasting room, wholesale/
> distribuidor, on-premise, exportación) **no vienen documentados** en las guidelines
> de marca — deben confirmarse con el archivo de datos de ventas real antes de
> implementar el generador (ver Bloque B de `knowledge_for_another_reports.md`). Se
> observó al menos un SKU de referencia en el material fotográfico: *"Sullivan James
> O'Neil — Merlot, Napa Valley"*, usado aquí solo como ejemplo, no como catálogo completo.

---

## 1. Identidad y meta

| Campo | Valor |
|---|---|
| Marca | Sullivan Rutherford Estate |
| Fundación | 1972 · 50th Anniversary (sello conmemorativo 1972–2022) |
| Título del reporte sugerido | **Sales & Depletions** (placeholder — confirmar con negocio) |
| Subtítulo | `Week {NN}-{AAAA}` (mismo patrón que Loco Tequila) |
| Logo | Wordmark serif "SULLIVAN" + regla + "RUTHERFORD ESTATE" en versalitas |
| Ubicación de logos | `Imagenes_iconos/Sullivan-Black.svg`, `Sullivan-Black.png`, `Sullivan-White.svg`, `Sullivan-White.png` |
| Idioma | Inglés (US) |
| Moneda | USD, formato `$1,889` (miles, sin decimales; Ticket/Price Point con 2 decimales) |
| Misión | "To be at the forefront of quality in our vineyards, wines and customer experience, while staying authentic to the classical nature of the winemaking tradition." |
| Propósito | Desarrollar relaciones duraderas y hospitalidad genuina; celebrar la excelencia y la pasión por el vino. |
| Posicionamiento | Clásico, elegante, tradición vitivinícola; fondo azul marino profundo, textura de pintura abstracta como fondo de marca |
| Numeración | Número de página abajo a la derecha (heredado del patrón Loco) |

---

## 2. Paleta de color (tokens)

### 2.1 Marca / estructura (Color Palette — pág. 6 del brand guideline)

| Token | HEX | RGB | CMYK | Uso |
|---|---|---|---|---|
| `--brand-navy` | `#003057` | 0, 48, 87 | 100, 45, 0, 66 | Banda de encabezado, títulos de sección, fondo primario de marca |
| `--brand-gray` | `#656565` | 101, 101, 101 | 0, 0, 0, 60 | Subtítulos, líneas divisorias, texto secundario |
| `--brand-tan` | `#A67C52` | 166, 124, 82 | 0, 25, 51, 35 | Acento cálido — resaltados, íconos, detalles editoriales |
| `--brand-cream` | `#FFFBEF` | 255, 251, 239 | 0, 2, 6, 0 | Fondo claro alternativo, tarjetas sobre navy |
| `--header-text` | `#FFFFFF` | — | — | Texto sobre banda navy |
| `--page-bg` | `#FFFFFF` | — | — | Fondo de página |
| `--rule-line` | `#D9D9D9` | — | — | Líneas divisorias / borde inferior de página |

### 2.2 Colores de PRODUCTO (SKU de vino) — placeholder, pendiente de catálogo real

Las guidelines de marca no definen una paleta por varietal/SKU (a diferencia del
toolkit de Sttupa, que sí trae paleta por habitación). Sugerido, a validar con el
cliente, usando la paleta corporativa como base y variaciones tonales:

| Orden | SKU / Varietal (tentativo) | Token | HEX (tentativo) |
|---|---|---|---|
| 1 | Cabernet Sauvignon | `--w-cabernet` | `#451B0F` (vino profundo, prestado del tono Poetry/madera) |
| 2 | Merlot (ej. "James O'Neil") | `--w-merlot` | `#A67C52` (tan de marca) |
| 3 | Chardonnay | `--w-chardonnay` | `#E7C372` (dorado) |
| 4 | Sauvignon Blanc | `--w-sauvignonblanc` | `#FFFBEF` (cream de marca) |
| 5 | Rosé | `--w-rose` | `#BF6B6B` (rosado, a validar) |
| 6 | Reserve / Library | `--w-reserve` | `#003057` (navy de marca) |

### 2.3 Colores de CANAL — placeholder, pendiente de confirmar con negocio

| Canal (tentativo) | Token | HEX (tentativo) |
|---|---|---|
| Wine Club / DTC | `--c-dtc` | `#003057` (navy) |
| Tasting Room / Hospitality | `--c-tasting` | `#A67C52` (tan) |
| Wholesale / Distribuidor | `--c-wholesale` | `#656565` (gris) |
| On-Premise (restaurantes) | `--c-onpremise` | `#451B0F` |
| Exportación | `--c-export` | `#E7C372` |

### 2.4 Elementos de gráfica y estados

| Token | HEX (heredado del patrón Loco, a validar) | Uso |
|---|---|---|
| `--chart-plan-line` | `#A67C52` | Línea de "Plan / Presupuesto" (tan de marca en vez de rojo, para mantener tono clásico) |
| `--chart-lastyear-area` | `#FFFBEF` | Área rellena "Año Pasado" (cream de marca) |
| `--chart-grid` | `#E2E2E2` | Cuadrícula horizontal / ejes |
| `--chart-label` | `#003057` | Etiquetas de dato |
| `--highlight-cream` | `#FFFBEF` | Columna/fila resaltada (Totales, periodo actual) |
| `--pos-value` | `#003057` | Variación positiva / neutra |
| `--neg-value` | `#8C2F2F` | Variación negativa (rojo vino, no está en la guía oficial — validar con marca antes de usar) |

---

## 3. Tipografía

| Rol | Familia | Peso | Fuente / disponibilidad |
|---|---|---|---|
| Título de marca / wordmark / titulares | **Garamond** (guideline oficial dice solo "Garamond", sin especificar variante) | Regular | ✅ Disponible como **EB Garamond** en `Fonts/Font_sullivan/EB_Garamond/` (variable + estáticos: Regular, Medium, SemiBold, Bold, ExtraBold + itálicas). Usar EB Garamond como sustituto tipográficamente fiel (misma familia clásica tipo "old-style serif"). |
| Subtítulos / cuerpo editorial | EB Garamond | Regular / Medium | ✅ Disponible (ver arriba) |
| Encabezados de tabla | EB Garamond | SemiBold / Bold | ✅ Disponible |
| Cuerpo de tabla | EB Garamond | Regular | ✅ Disponible |
| Filas de total / resaltadas | EB Garamond | Bold | ✅ Disponible |
| Barra de título de gráfica | EB Garamond, blanco sobre navy | Bold | 9–10 pt |

Alineación numérica: **derecha** en todas las celdas de valor. Etiquetas de fila: **izquierda**.
Estilo editorial clásico: mayúsculas versales con tracking amplio para subtítulos
institucionales (ej. "RUTHERFORD ESTATE"), serif clásica en todo lo demás — nunca
sans-serif geométrica, rompe el tono de la marca.

---

## 4. Estructura de página

```
┌───────────────────────────────────────────────┐
│  BANDA NAVY (#003057)   Título · Semana   LOGO │  ← --brand-navy, logo Sullivan-White
├───────────────────────────────────────────────┤
│  Título de sección          (Por SKU/Canal)     │  ← EB Garamond, navy
│                                                 │
│  [Desglose de ventas]   [Tabla resumen]         │
│  o                                              │
│  [Bloque de tablas SEMANAL/ANUAL]               │
│                                                 │
│  [Barra navy: "Net sales by ... $X"]            │
│  [Gráfica 1]                                    │
│  [Barra navy: "Cases sold by ... N"]            │
│  [Gráfica 2]                                    │
├───────────────────────────────────────────────┤
│  línea gris                                  #N │
└───────────────────────────────────────────────┘
```

---

## 5. Esquemas de TABLA (estructura heredada de Loco Tequila, adaptada)

> Sustituir "producto/SKU" → varietal de vino; "botellas/cajas" se mantiene igual
> (unidad estándar de la industria vitivinícola) cuando se confirme el modelo real.

### 5.1 Tabla Resumen (Canal × SKU)

- **Columnas (6 + total):** los 6 SKU tentativos de §2.2 + `Total`.
- **Filas (5 + total):** `Wine Club/DTC | Tasting Room | Wholesale | On-Premise | Export | Total`.
- Fila `Total` y columna `Total` con fondo `--highlight-cream`, negrita, `$valor (%)`.

### 5.2 Tabla de detalle (bloques por canal)

Igual patrón que Loco (§5.2): bloques por canal con cuentas/distribuidores top,
cierre con `Net Sales {AAAA}` y `% Share` resaltados en `--highlight-cream`.

### 5.3 Tabla histórica mensual

Columnas = SKUs + Total; filas = meses año anterior + año actual. Gráfica de barras
apiladas por SKU + línea `Total` en `--chart-plan-line` (tan).

### 5.4 Tabla "Sales / {SKU}" — SEMANAL y ANUAL

Misma estructura de 3 zonas que el reporte Loco (§5.4):

**Zona A:** `Same Week Last Year` | `Prior Week` | `Plan` | `Current Week` (resaltada)
**Zona B:** `Week {NN} - {AAAA} / {fecha} to {fecha}`
**Zona C — Variance vs:** `Plan` | `Prior Week` | `Prior Year` (negativas en `--neg-value`)

Filas — versión "Por SKU":
```
Cabernet Sauvignon
Merlot
Chardonnay
Sauvignon Blanc
Rosé
Reserve / Library
Net Sales (Weekly / Annual)   ▓
Gross Margin %
#Bottles Sold
Cases (9L)
Average Price per Bottle $
```

### 5.5 Nota de celdas vacías

`$0` / `0` / `0%` explícitos, nunca en blanco (mismo criterio que Loco §5.5).

---

## 6. Especificación de GRÁFICAS

### 6.1 Resumen (portada) — >4 SKUs → evitar dona, usar **treemap o barras horizontales**
Con 6 SKU tentativos se recomienda **barras horizontales** en vez de dona (regla del
Bloque E de `knowledge_for_another_reports.md`: dona solo tolera 3-4 categorías).
- Barras = 6 SKU (§2.2), colores en orden fijo, etiqueta `$valor` y `%` al final de cada barra.
- Total agregado en encabezado: `${Total} · Total Net Sales`.

### 6.2 Barras apiladas + línea (histórico mensual)
- Eje X: meses. Barras apiladas por SKU (§2.2).
- Línea `--chart-plan-line` (tan) = Plan/Presupuesto, con etiqueta por mes.
- Separador vertical punteado entre años.

### 6.3 Combo por semana/mes (fichas por SKU/canal)
Dos gráficas por página, dentro de barra de título navy:
1. `Net sales by week/month ($): ${total}`
2. `Cases sold by week/month: {total}`

Capas: área `--chart-lastyear-area` (cream, Año Pasado) + barras apiladas por canal
o SKU + línea `--chart-plan-line` (tan, Plan) + etiquetas de dato + leyendas inferiores.

---

## 7. Inventario de páginas (propuesto, a validar con negocio)

| Pág. | Contenido |
|---|---|
| 1 | Resumen Anual (barras horizontales + matriz + detalle por canal) |
| 2 | Resumen Semanal |
| 3 | Histórico mensual |
| 4–5 | Sales Totals Por SKU (Semanal / Anual) |
| 6–7 | Sales Totals Por Canal (Semanal / Anual) |
| 8–19 | Un SKU por par de páginas (los 6 varietales tentativos) × (Semanal + Anual) |

---

## 8. Reglas de formato numérico (USD)

| Métrica | Formato | Ejemplo |
|---|---|---|
| Ventas ($ miles) | `$` + separador de miles, sin decimales | `$1,889` |
| Participación / variación | entero + `%` | `47%`, `-12%` |
| #Bottles Sold | entero | `2,829` |
| Cases (9L) | entero | `206` |
| Average Price per Bottle | `$` con 2 decimales | `$42.00` |
| Variación negativa | color `--neg-value`, con signo `-` | `-$487` / `-12%` |
| Fechas | `MMM D, YYYY` (formato US) | `Aug 26, 2026` |

---

## 9. Checklist de replicación para la skill

1. Banda `--brand-navy` con título + subtítulo `Week {NN}-{AAAA}` + logo `Sullivan-White`.
2. Respetar orden y color de los SKU (§2.2) en toda gráfica y tabla — **confirmar
   catálogo real de varietales/etiquetas con el cliente antes de fijar el mapeo**.
3. Resaltar en `--highlight-cream` (cream de marca) la columna/fila de Totales y periodo actual.
4. Variaciones negativas en `--neg-value` (rojo vino — no es color oficial de marca,
   validar con Sullivan antes de producción).
5. Confirmar con negocio: catálogo real de SKUs y canales de venta antes de programar
   `data_processor.py` — no están en las brand guidelines (solo identidad visual).
6. Tipografía: usar EB Garamond (disponible localmente) como equivalente fiel de
   "Garamond" indicado en la guía oficial.
7. Logos oficiales en `Imagenes_iconos/Sullivan-Black.*` y `Sullivan-White.*` (SVG
   preferido para PDF; notar que `Sullivan-White.svg` pesa solo 440 bytes — verificar
   que no esté vacío/corrupto antes de usarlo, usar el PNG blanco como respaldo).
8. Con >4 categorías de producto, usar barras horizontales o treemap en portada, no dona.
9. Numeración de página abajo-derecha. Formatos numéricos de §8 (USD, formato US).
10. Idioma del reporte: inglés (US) en todos los textos y encabezados.
