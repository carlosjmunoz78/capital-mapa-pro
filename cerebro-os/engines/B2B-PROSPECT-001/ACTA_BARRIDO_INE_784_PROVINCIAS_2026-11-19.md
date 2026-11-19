# CEREBRO B2B-PROSPECT-001 · ACTA FÍSICA DEL BARRIDO DE 784 MUNICIPIOS · 2026-11-19

**Estado:** HECHO = barrido regional de datos abiertos + carga en Notion; PARCIAL = verificación independiente de cada agencia, exhaustividad frente a negocios no catalogados, autorizaciones comerciales y listas Brevo (no se han importado).

## Evidencia de escritura y lectura real

- Directorio Notion privado: https://app.notion.com/p/41d81b1a756d8164b829f8357e36673a
- Cobertura INE municipal privada: https://app.notion.com/p/41d81b1a756d815cac2fe44abd9025c8
- **4.560 fichas comerciales físicamente guardadas, 2.789 con email, 4.354 con teléfono**. `COUNT(DISTINCT Clave) = 4.558`; dos claves históricas duplicadas ya estaban marcadas para revisión, sin borrar orígenes.
- Nuevas desde Overture Places: **3.512** fichas añadidas físicamente y verificadas por Notion; directorio anterior **1.048**.
- **784 / 784 códigos INE de la ruta** registrados físicamente, con un campo de presencia según fuentes. **309 municipios con al menos una inmobiliaria detectada**, **475 municipios sin ficha registrada en las fuentes consultadas**. Esto NO equivale a prueba de inexistencia de inmobiliarias en esos 475.
- Se preserva Córdoba capital: **327 fichas** del directorio provincial; queda fuera del orden prioritario de búsqueda de pueblos, sin eliminar sus datos.
- 25 `REACTIVACION_REVISAR` («NO QUIERE» histórico, no baja necesariamente), 18 `COLABORADOR_PROTEGIDO`. Las oposiciones verificadas no se pueden ignorar.

## Recuento por provincia verificado en Notion

| Provincia | Municipios de ruta | Con agencias en directorio | Sin ficha en fuentes | Fichas del directorio provincial | Email | Teléfono |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Córdoba | 76 | 34 | 42 | 491 (164 pueblos + 327 capital histórica) | 272 | 433 |
| Jaén | 97 | 53 | 44 | 252 | 107 | 197 |
| Sevilla | 106 | 46 | 60 | 635 | 410 | 624 |
| Málaga | 103 | 51 | 52 | 1.711 | 1.065 | 1.657 |
| Granada | 174 | 49 | 125 | 437 | 295 | 432 |
| Cádiz | 45 | 25 | 20 | 526 | 334 | 513 |
| Almería | 103 | 30 | 73 | 352 | 216 | 344 |
| Huelva | 80 | 21 | 59 | 156 | 90 | 154 |
| TOTAL | **784** | **309** | **475** | **4.560** | **2.789** | **4.354** |

## Procedimiento de barrido (cobertura geográfica, no confirmación de ausencia)
1. INE municipios 2026 derivados del catálogo público; código y prioridad deterministas, Córdoba capital excluida de la ruta y conservada en históricos.
2. CRM real PROD (solo SELECT), Notion maestros históricos, API Andalucía, UNEXIA; deduplicación por nombre/municipio y contacto, protegiendo colaboradores y oposiciones.
3. OpenStreetMap completo Andalucía desde Geofabrik (197.619.043 bytes) con clasificación `office=estate_agent`, geometría de municipios geoBoundaries ESP ADM3, extracción de teléfonos/emails disponibles.
4. **Overture Places release 2026-11-18** consultada en 4 bloques geográficos de Andalucía: **545.717 puntos de actividad examinados**, **5.236 registros inmobiliarios candidatos con datos de contacto** entre 300 municipios; se filtraron categorías ajenas, cierres permanentes, confianza inferior a 0,65, colisiones y contactos no validables antes de insertar **3.512** nuevos registros. Licencias Overture: CDLA-Permissive-2.0 / Apache-2.0. Geometría geoBoundaries ADM3 derivada de fuentes IGN.
5. Registro físico de cada municipio con **CON_AGENCIAS** o **SIN_FICHAS_EN_FUENTES**, `Comprobación independiente=PENDIENTE` en TODOS los casos (no afirmar revisión presencial o verificaciones web individuales inexistentes). 8 vistas provinciales en la tabla de municipios y 8 vistas provinciales en la tabla de agencias.

## Gate de contacto y costes
- **0 envíos comerciales** y **0 € de coste adicional contratado**. Solo entorno LAB, herramientas existentes y fuentes abiertas. GitHub Actions en rama `cerebro/b2b-prospect001-continuity-lab-20261119`, nunca main.
- Brevo: listas provinciales #25 Córdoba, #26 Jaén, #27 Sevilla, #28 Málaga, #29 Granada, #30 Cádiz, #31 Almería, #32 Huelva, **sin contactos importados**; NEWS-001 original #17/#18 intacta. No asumir que un email empresarial público consiente campañas.
- CRM PROD, App, WordPress, DNS, automatizaciones, NEWS-001 **sin modificaciones**.
- La cobertura *exhaustiva de todas las agencias existentes* no se puede certificar con los directorios abiertos; hay 475 municipios sin resultados identificados que requieren verificación independiente focalizada. El escaneo de datos abiertos sí abarcó físicamente toda Andalucía.
- Para envío posterior, se requiere revisión editorial del propietario, comprobación de bajas/oposiciones y base legal aplicable.

**Resultado en esta ejecución:** se pasó de **894 → 4.560 fichas** (+3.666), se asignaron a provincias, y el inventario de **784 municipios** quedó actualizado de forma visible y verificable. La suma incluye 154 fichas nuevas de Geofabrik OSM y 3.512 nuevas de Overture.
