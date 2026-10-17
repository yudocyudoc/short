# IGC — 40 pruebas de ruido y parámetros ocultos: resultados ejecutados

**Fecha:** 2026-10-17. **Estado:** campaña sintética ejecutada satisfactoriamente en GitHub Actions. **Código:** PR #31, borrador, sin fusionar.

## Evidencia auditable

- [GitHub Actions completo, push #39074098516](https://github.com/yudocyudoc/short/actions/runs/39074098516) — PASS.
- [Comprobación PR #39074113649](https://github.com/yudocyudoc/short/actions/runs/39074113649) — PASS.
- [Artifact original #12115972392](https://github.com/yudocyudoc/short/actions/runs/39074098516/artifacts/12115972392) — CSV de ocho mundos fuera de los parámetros nominales, series de referencia, 40 expedientes sintéticos, comparación caso a caso y puntuación.
- [PR #31](https://github.com/yudocyudoc/short/pull/31).

## Protocolo ejecutado

Se construyeron ocho mundos de OpenModelica: cuatro grafos existentes, con dos juegos alternativos de tiempos de respuesta (preparación, despacho, tránsito y filtro cuando aplica). Sobre cada mundo se generaron cinco condiciones instrumentales: CLEAN_ALL, BOUNDED_ALL, SPARSE_ALL, MISSING_RECEIPT y BAD_CALIBRATION. El ruido se aplicó a tasas simuladas con error uniforme independiente por canal y acotado a ±0.03; se conservaron timestamps comunes sin rellenar ausencias.

El evaluador de la rama B **no recibió** la identidad del grafo verdadero ni los parámetros modificados. El generador/puntuador sí los conoce. Se compararon:
- **A (negativo, tipo PR #30):** igualdad vs diferencia con tolerancia fija 1e-6, aplicada a mediciones ruidosas sin un contrato adicional de precisión.
- **B (guard con cotas):** si la mayor diferencia supera la suma de los errores absolutos certificados para dos canales calibrados, se refuta sólo la igualdad. Si no, INCONCLUSIVE. Sensor no calibrado, comparación no disponible o pocos puntos comunes: no hace poda.

## Resultado principal

| Indicador | A: tolerancia fija | B: guard por cotas |
|---|---:|---:|
| Casos | 40 | 40 |
| **Falsos descartes de la arquitectura generadora** | **20** | **0** |
| Conjuntos vacíos | 0 | 0 |
| Casos con único candidato | 32 | 6 |
| Media de arquitecturas conservadas | 1.40 | 2.60 |

### Resultados por condición (8 casos cada una)

| Condición | Falsos descartes A | Falsos descartes B | Media restantes A | Media restantes B |
|---|---:|---:|---:|---:|
| CLEAN_ALL | 0 | 0 | 1.00 | 2.25 |
| BOUNDED_ALL | 6 | 0 | 1.00 | 2.25 |
| SPARSE_ALL | 6 | 0 | 1.00 | 2.25 |
| MISSING_RECEIPT | 2 | 0 | 3.00 | 3.25 |
| BAD_CALIBRATION | 6 | 0 | 1.00 | 3.00 |
| **Total** | **20** | **0** | **1.40** | **2.60** |

El guard cumplió las tres puertas originales: 0 falsos descartes, el control negativo falla, y el guard consigue reducir las cuatro alternativas en varios casos (no se limita a abstenerse siempre).

## Interpretación

El error del procedimiento A es claro: ante dos señales que proceden del mismo proceso, un pequeño error independiente hace que `max|x-y| > 1e-6` y permite descartar precisamente la hipótesis de igualdad verdadera. Cuando el sensor tiene una ganancia no calibrada, el mismo problema se amplifica. Una elección aparentemente específica puede ser incorrecta.

El procedimiento B compra seguridad condicional a costa de menor especificidad. **No confirma igualdad**, sólo detecta no-igualdad por encima de un presupuesto instrumental supuesto. Las 34 situaciones en que B conserva múltiples modelos no representan fallos por sí solas.

## Límites que no se deben borrar del informe

1. Las cuatro arquitecturas generadoras son las mismas del catálogo de candidatos. Se varían parámetros, pero **no se introduce un mecanismo fuera de catálogo**.
2. La cota ±0.03, calidad y sincronización de sensores son verdaderas **por construcción**. La experimentación no demuestra que puedan certificarse en datos empresariales reales.
3. Las 40 observaciones no son independientes desde el punto de vista estadístico: provienen de ocho mundos Modelica, repetidos bajo cinco transformaciones instrumentales. No extrapolar tasas 20/40 o 0/40 al mundo empresarial.
4. Las tasas compatibles y los tres tests numéricos no identifican de forma única el mecanismo causal; las inferencias son condicionales a cuatro grafos, parámetros y ventanas simuladas.
5. No se ha recuperado formalmente un retardo temporal, validado dependencias entre sensores ni diseñado una prueba de causalidad experimental en campo.
6. El experimento **no ejecutó Llama**. Aísla deliberadamente la frontera instrumental/estadística de la interpretación textual.

## Decisión

El guard del PR #30 no puede trasladarse sin cambios a tasas empresariales ruidosas. La versión B merece una prueba posterior porque controla un fallo demostrable, pero todavía necesita detectar **rotura de supuestos de medición** y reconocer **sistemas fuera del catálogo**.

**Siguiente prueba más importante:** introducir un mecanismo de referencia ausente del catálogo y una degradación de sensor no anunciada, y medir si el método puede emitir una señal de fuera de soporte o insuficiencia sin fingir identificación.
