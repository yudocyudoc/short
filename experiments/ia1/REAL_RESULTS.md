# IA-1 — REAL_RESULTS · Llama 3.3 70B: evidencia y propuesta molecular

**Ejecución real autorizada:** [GitHub Actions #39105269372](https://github.com/yudocyudoc/short/actions/runs/39105269372) · [artefacto con peticiones, respuestas originales, baselines y puntuación](https://github.com/yudocyudoc/short/actions/runs/39105269372/artifacts/12128675568).  
**Commit ejecutado:** `0ccd9923a757dab16aead894bea7e1e4e0193359`. **Fecha:** 2026-10-18 UTC.  
**Modelo:** `@cf/meta/llama-3.3-70b-instruct-fp8-fast` en Cloudflare Workers AI. Temperatura 0, un intento por caso, sin reparación de outputs ni re-prompting.

## Enmienda pre-LLM del diseño — NO ocultar

La primera colección tenía 12 casos y el baseline léxico obtuvo **12/12** clasificaciones conjuntas correctas. Era demasiado fácil: podría producirse un PASS vacío por patrones de palabras. **Antes de emitir la primera consulta a Llama** se añadieron seis casos de contraste I13–I18 con negación, auditoría correctiva, evidencia sin palabras clave y datos no concluyentes. La nueva colección (18 casos) se congeló antes de la llamada y el baseline bajó a **12/18**. El resultado inicial y las ejecuciones CI fallidas por un conteo de casos desactualizado siguen registrados en el historial. No se hizo segunda muestra con Llama.

## Puntuación primaria congelada, estricta

| Medida | Baseline léxico + AST fijo | Llama 3.3 70B |
|---|---:|---:|
| Casos | 18 | 18 |
| Respuesta admitida en esquema y linter completo | **18/18** | **4/18** |
| AST aceptado por verificador E1 y renderizable por backend | **18/18** | **4/18** |
| Evidencia física estricta (requiere respuesta admitida) | **15/18** | **3/18** |
| Evidencia informacional estricta (requiere respuesta admitida) | **14/18** | **4/18** |
| Ambas dimensiones estrictas por caso | **12/18** | **3/18** |

**Interpretación:** en esta evaluación conjunta, Llama falló principalmente al construir AST compatibles con el contrato. El baseline siempre emite el mismo AST mínimo, así que sus **18/18 AST válidos no prueban identificación causal ni mejor propuesta estructural**. Sin embargo, Llama tampoco puede reclamar un PASS global sólo por detectar algunos mecanismos a nivel textual.

**Los 18 outputs de Llama pudieron parsearse como JSON.** De los 14 AST inválidos, **8** fueron `INVALID_ADAPTER` y **6** `UNKNOWN_PORT`. Son errores funcionales: ejemplos originales muestran `receipt.total → report.physicalArrivalRate` (stock acumulado frente a tasa de recepción) o `receipt.arrival → report.physicalArrivalRate` utilizando un puerto de entrada como fuente. No se corrigieron manualmente.

## Diagnóstico post-corrida: I1 textual separado de I2 AST

El evaluador original de IA-1 acopló injustificadamente la puntuación de evidencia al PASS completo de AST (`is_valid` antes de puntuar cada dimensión). Esto es un **defecto de diseño del scoring**, porque I1 e I2 debían poder fallar o pasar por separado. Se calculó un diagnóstico adicional directamente sobre los JSON originales, sin modificarlos ni rerun del modelo:

| Acierto de clasificación + evidencia citada, **ignorando la validez del AST** | Baseline | Llama |
|---|---:|---:|
| Familia física | 15/18 | **15/18** |
| Transformación informacional | 14/18 | **17/18** |
| Ambas dimensiones en el caso | 12/18 | **14/18** |

**Estos tres números son exploratorios/post hoc, no reemplazan el gate primario preregistrado.** Confirman una posible asimetría: Llama interpreta relativamente bien la distinción verbal entre material e información, pero no transfiere esa interpretación de modo confiable a conexiones Modelica válidas. La diferencia de 14/18 frente a 12/18 es demasiado pequeña, no independiente y no se usa para afirmar superioridad estadística. Si esta separación I1/I2 se adopta como puntuación oficial, requerirá un nuevo contrato y casos inéditos antes de otra inferencia.

**Casos ilustrativos:** I01 e I13 incluyeron evidencia positiva de acumulación física posterior al despacho y AST válidos. En I05 Llama clasificó como acumulación posterior lo que el caso atribuía exclusivamente a preparación **antes del despacho**, y además su AST no incorporó tránsito pese a la clasificación positiva; esto muestra inconsistencia entre explicación verbal y arquitectura. En I04 atribuyó transformación informacional a un retraso del tablero sin medición independiente de recepción física. Ninguno de estos errores se enmascara como “respuesta casi correcta”.

## Qué quedó probado y qué no

- **I1:** lectura textual plausible y potencialmente útil; el gate primario acopló indebidamente esta función a I2 y no permite adjudicar I1 por sí sola. Resultado descriptivo pendiente de evaluación independiente.
- **I2:** existen **4 respuestas estructuralmente admitidas**, con algunos ejemplos causalmente respaldados, pero **14/18 fallos estructurales**. Hay factibilidad puntual, no fiabilidad. El backend renderizó Modelica para AST aceptados, pero **NO se ejecutó OpenModelica sobre esos cuatro AST del LLM** en esta campaña; no confundir con las 21 simulaciones de E1.
- **I3, E2, E3, I4:** NOT_RUN. No se consultó un mundo oculto, no se hizo diseño de prueba causal, ni predicción reservada, ni revisión estructural, ni comparación de modelos más capaces.
- La referencia son 18 viñetas redactadas por el equipo y puntuadas por los mismos autores; no son un benchmark independiente ni prueba de modelación empresarial.
- Que este Llama falle 14/18 AST **no invalida explorar IA con modelos más capaces**. El próximo paso con IA debería enfrentar exactamente este tipo de contrato y observaciones, manteniendo respuestas originales y sin conceder crédito por simples reparaciones de formato.

## Decisión de la campaña

Resultado global: **IA1_EXPLORATORY_MIXED / I2_STRICT_LOW / METHOD_NOT_DEMONSTRATED**. Documentar los errores del puerto y del adaptador. No cambiar prompts ni linter para reclasificar esta corrida como PASS. Mantener [PR #35](https://github.com/yudocyudoc/short/pull/35) encadenado a [#34](https://github.com/yudocyudoc/short/pull/34) y [#33](https://github.com/yudocyudoc/short/pull/33), sin fusionar mientras se pospone la revisión adversativa.

Siguiente prueba útil: modelo de IA más avanzado en un **nuevo set de casos** con scoring I1 textual separado de I2 estructural predeclarado, o continuar a E2 ideal si se construye evaluador de mundos ocultos separado. En ningún caso usar las mismas 18 situaciones repetidas a temperatura 0 como nuevas muestras independientes.
