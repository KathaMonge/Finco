# Issues OCR Pendientes

## 1. Montos extraídos con errores de OCR

**Problema**: El OCR (ONNX PP-OCRv6) garblea muchos montos al leer vouchers. Algunos montos se confunden con números de referencia o se leen sin decimales.

### Evidencia (ref1.jpeg — estado de cuenta bancario)

| Línea | Monto OCR crudo | Monto parseado | Monto real esperado | Problema |
|---|---|---|---|---|
| 5237900060 | `2850` | $2,850.00 | ~$2,850 | OK |
| 5242485373 | `511210` | $511,210.00 | ~$511.21 | Falta decimal |
| 5277900m60 | `g9mn` | $9.00 | ~$2,850 | OCR garblea完全 |
| 60132480713 | `1hum` | $1.00 | ~$1,500 | OCR garblea |
| 6ugz9mmm6m | `040` | $40.00 | ~$40 | OK |
| 6112480581 | `4000` | $4,000.00 | ~$4,000 | OK |
| 615900060 | `54m0` | $540.00 | ~$540 | Parcial |
| 6152485244 | `38320` | $38,320.00 | ~$3,832 | Falta decimal |
| 6162480609 | `510` | $510.00 | ~$510 | OK |
| 5=IlUN-2 | `70011` | $70,011.00 | ~$7,001 | Falta decimal |
| 617900060 | `moo` | None | ~$2,500 | No parsea |
| 6182487424 | `bonn` | None | ~$1,800 | No parsea |
| 6192481631 | `2an` | $2.00 | ~$2,200 | Garblea |

**Total parseado**: ~$128,384 | **Total real**: $55,130 (según pie de página)

### Causa raíz

1. **OCR de baja resolución**: PaddleOCR PP-OCRv6 en imágenes de baja calidad (fotos de vouchers térmicos, PDFs bancarios comprimidos) confunde caracteres:
   - `m` ↔ `nn`, `rn`, `0` ↔ `o` ↔ `O`
   - `1` ↔ `l` ↔ `I` ↔ `|`
   - Puntos decimales se pierden o se confunden con espacios

2. **Falta de contexto de formato**: El parser no sabe que los montos bancarios argentinos usan formato `1.234,56` (punto como separador de miles, coma para decimales) o `1,234.56` (formato US).

3. **Montos confundidos con referencias**: En líneas donde el OCR falla completamente (ej: `g9mn`, `1hum`), el `parse_amount()` extrae solo los dígitos sueltos, giving valores incorrectos.

### Soluciones propuestas

- **Post-procesamiento de montos**: Detectar si un monto parseado es sospechosamente alto/bajo comparado con el promedio de la misma factura
- **Validación contra total**: Comparar la suma de montos extraídos contra el total del pie de página
- **Formato de monto por emisor**: Aprender el formato decimal de cada emisor (ARS vs USD vs CRC)
- **OCR ensemble**: Usar múltiples passes de OCR con diferentes configuraciones y votar

---

## 2. Soporte de moneda: CRC (Colones) y USD

**Problema**: Actualmente la app está hardcodeada a ARS (Pesos Argentinos). Necesita soportar CRC (Colones costarricenses) y USD (Dólares).

### Alcance del cambio

| Componente | Cambio necesario |
|---|---|
| `core/models.py` | `currency` ya acepta `String(3)`, solo cambiar default o detectar |
| `core/schemas.py` | `pattern=r"^[A-Z]{3}$"` ya acepta CRC/USD |
| `utils/helpers.py` | `format_currency()` solo formatea ARS con `$`. Necesita: `₡` para CRC, `US$` o `$` para USD |
| `ui/views/ocr_scan_view.py` | Agregar selector de moneda al formulario OCR |
| `ui/components/summary_cards.py` | Pasar currency desde datos, no hardcodeado |
| `ui/views/dashboard_view.py` | Respetar currency de las transacciones |
| `services/ocr/parsers/fallback.py` | Detectar moneda del documento (symptoms: "colones", "CRC", "USD", "$", "¢") |
| `services/backup_service.py` | Exportar/importar currency correctamente |

### Detección de moneda en OCR

Patrones a buscar en el texto OCR:
- **CRC/Colones**: `colones`, `crc`, `¢`, `₡`, `¢\d`, `CRC\s*\d`
- **USD**: `usd`, `d[oó]lar`, `us\$`, `u\$s`, `d[oó]lares`
- **ARS**: `peso`, `ars`, `\$\s*\d` (default si no detecta nada)

### Formato de visualización

| Moneda | Símbolo | Formato | Ejemplo |
|---|---|---|---|
| ARS | `$` | `$1.234,56` | `$55.130,00` |
| USD | `US$` | `US$1,234.56` | `US$55,130.00` |
| CRC | `₡` | `₡1.234.567` | `₡28.500.000` |

---

## 3. Parsing de montos por formato de país

**Problema**: `parse_amount()` actualmente limpia todos los no-numéricos y trata `.` y `,` de forma inconsistente.

### Formatos actuales vs necesarios

| País | Formato ejemplo | `parse_amount` actual | Resultado correcto |
|---|---|---|---|
| Argentina | `55.130,00` | Limpia a `5513000` → `5513000.00` ❌ | `55130.00` |
| Argentina | `55130` | `55130.00` ✓ | `55130.00` |
| Costa Rica | `₡28.500.000` | Limpia a `28500000` → `28500000.00` | `28500000.00` |
| USA | `1,234.56` | Limpia a `1234.56` → `1234.56` ✓ | `1234.56` |
| USA | `$1,234.56` | Limpia a `1234.56` ✓ | `1234.56` |

### Solución propuesta

`parse_amount()` necesita un parámetro `currency` o `format` para saber cómo interpretar separadores:
- Si `currency="ARS"`: último `.` = separador de miles, última `,` = decimal
- Si `currency="USD"`: última `.` = decimal, `,` = separador de miles
- Si `currency="CRC"`: `.` = separador de miles, sin decimales (colones redondeados)

---

## 4. Fechas truncadas por OCR (ya mitigado, no completamente resuelto)

**Estado**: ✅ Mitigado con fuzzy date parsing y heurística de año.

**Problema residual**: Algunas fechas aún fallan si el OCR garblea demasiado el mes (ej: `I11N` ahora parsea como Jun, pero la confianza es baja).

**Mejora futura**: Usar contexto del documento (footer con rango de fechas) para inferir el año correcto de todas las transacciones.

---

## 5. Línea sin referencia (formato genérico)

**Problema**: Algunas líneas no tienen número de referencia de 6+ dígitos al inicio. Ej: `5=IlUN-2 AINILAPAZAFLS laluel R 70011`

**Estado**: `LINE_TX_GENERIC` maneja estos casos, pero la descripción incluye el código `R` como parte del texto.

**Mejora**: Limpiar el código del emisor (`R`, `:R`, `:RI`) de la descripción extraída.

---

## Prioridad

| Issue | Prioridad | Esfuerzo |
|---|---|---|
| Formato de monto por país (parse_amount) | Alta | Medio |
| Soporte CRC/USD (format_currency + UI) | Alta | Bajo |
| Detección de moneda en OCR | Alta | Medio |
| Post-procesamiento de montos sospechosos | Media | Alto |
| Validación contra total del pie de página | Media | Medio |
| Limpiar código de emisor de descripciones | Baja | Bajo |
