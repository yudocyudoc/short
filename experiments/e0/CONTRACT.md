# E0 — Contrato mínimo, falsabilidad y frontera de ejecución

**Estado:** prospectivo. Este documento registra el diseño de M0; sólo los resultados de CI pueden confirmar sus verificaciones técnicas. **E0 no adjudica IGC.** Rector: [hoja de ruta v3](../../docs/IGC_SD_HOJA_DE_RUTA_CONSOLIDADA_v3_2026-10-18.md) §§4, 6–9; [fundación #32](https://github.com/yudocyudoc/short/pull/32).

| Campo | Decisión vinculante |
|---|---|
| Pregunta | ¿Es falsable el mínimo ideal sin proporcionar respuestas al constructor? |
| Hipótesis | S1 expresividad (sólo ejemplos manuales); S2–S5 e I1–I4 **NO adjudicadas** en E0 |
| Biblioteca | Cuatro clases declaradas en catalog.json, con BoundedQueue para tres roles y un adaptador de observación no intrusivo |
| Arquitecturas del evaluador | Seis referencias públicas (0/1/2 etapas físicas × reporte directo/filtrado). Su enumeración es un **control del evaluador**, no un constructor ni un mundo secreto |
| Parámetros P0 | Total residencia física 1.6 h, dividido por las etapas; capacidades de tránsito 3 y 100 unidades/h; reporte 1.6 h; estados iniciales 0 |
| Observables | P = despacho, recepción, tránsito agregado, reporte. Q = sólo reporte. Stocks internos y estructura no visibles |
| Estímulos | Pulso 6/h, escalón 6/h, rampa 6/h, pulso alto 14/h; las ventanas están congeladas en protocol.json |
| Presupuesto | Por mundo: 1 consulta inicial + 1 elegida + 1 reservada; máximo 96 simulaciones por brazo, 2 llamadas IA por caso y 3 revisiones |
| Comparación | Series numéricas en grilla coincidente; max absoluto y RMSE; error_bound operativo 1e-5 **sin certificación independiente aún**. Ninguna etiqueta LAG |
| Pre-registro | catálogos, observables, menú, umbral, coste, baselines y lógica de rechazo se incorporan antes de ensayos con mundos secretos |
| Verdades ocultas | **NO EXISTEN en este PR.** Antes de E2 deberán sellarse con sal secreta fuera del espacio del constructor, permisos segregados, y compromiso de predicción antes de revelar respuesta |
| Controles negativos | Tipos incompatibles, tap físico incorrecto, parámetros fuera de rango, tres etapas prohibidas, fuga en texto, observación Q que expone gold, consultas ilimitadas, señal Q que no discrimina |
| Artefactos | Python unit tests; fuente Modelica, archivos reales de simulación, matriz numérica evaluador-only, logs; sin publicar claves de mundo |
| Estados posibles E0 | CONTRACT_TECHNICAL_PASS o FAIL; E0_READY solamente después de revisar E0 contra todo el contrato; método IGC permanece NOT_RUN |

## Hipótesis — condiciones de éxito futuras predeclaradas

| ID | Prueba real requerida después de E0 | Falsificador / abstención |
|---|---|---|
| S1 | Todas las estructuras válidas del universo pequeño representadas; ninguna conexión prohibida admitida | Falta representación o entra conexión inválida |
| S2 | Compositor sin nombres de casos que derive topologías desde registro intercambiable, con canonicidad y auditoría de diff | Sólo opera con casos precableados; un alias no cuenta como mecanismo nuevo |
| S3 | Partición prevista antes de segunda consulta, con al menos un par separable por el menú; comparar selector con fijo/aleatorio | Pérdida de presupuesto, ausencia de separación o consulta a tabla de respuestas |
| S4 | Predicción cuantitativa y AST comprometidos antes de ver la respuesta reservada, con error dentro de cota verificada | Ajuste retrospectivo, mala predicción o fuga |
| S5 | Mutación estructural previa a simular, mejor que mero backtracking frente a BFS/exhaustiva y con mismo presupuesto | Sin oportunidad real a esta escala => NOT_TESTABLE_AT_THIS_SCALE |
| I1 | Extracción correcta de roles, entidades, stocks, límites y citas de narraciones neutrales nuevas frente a baseline léxico | Pistas de la solución o mecanismos inventados |
| I2 | Al menos una arquitectura válida y no entregada en el prompt, con contraste de casos no seleccionados a posteriori | Sólo adivina una macro o falla en AST/modelado |
| I3 | Crítica/test/reparación con acción verificable y control clásico de igual presupuesto | Pregunta bonita o re-etiqueta sin decisión válida |
| I4 | Comparación descriptiva por función entre Llama y modelo más capaz, con originales y costo | Falta de acceso/presupuesto común => INCONCLUSIVE, no fracaso general de IA |

**Regla anti-tautología:** ni generar correctamente un fixture ya sabido ni coincidir con él será un PASS de S2–S4. La matriz que produce el evaluador prueba sólo **posibilidades de contraste** bajo sus observables, intervenciones y grid; no constituye identidad de la verdad. Una pareja numéricamente indistinguible queda UNRESOLVED (nunca «equivalente» sin demostración analítica).

## Condiciones para cerrar E0 y abrir E1

1. Registro y descripciones compatibles con el backend original, verificables por hashes de blobs.
2. Los seis AST manuales admitidos y negativos rechazados; 0/1/2 etapas son **casos de referencia**, no compositor.
3. Matriz calculada desde CSV reales OpenModelica de ambos perfiles y capacidades; al menos un par numéricamente separable y al menos un caso que los estímulos no separan si ocurre realmente; **no fabricar el resultado**.
4. La incertidumbre del solver debe ser caracterizada **antes de E2**; el error_bound actual es umbral operativo, no una garantía de solver.
5. Ensayo de separación de ejecución antes de E2: el constructor no puede leer ninguna clave, sal o respuesta del evaluador (no basta esconder un campo del prompt).
6. Un evaluador/revisor comprueba no fuga, ausencia de saltos metodológicos, criterios y costos; si un punto crítico queda abierto se declara bloqueo, no se añade una nueva biblioteca.

**Contención:** este PR sólo tiene contratos, verificador de AST, referencias de evaluación y regresiones. No hay compositor ni IA. E0 cierra su preparación como **ENGINEERING_ONLY**; los experimentos sustantivos arrancan con E1 e IA-1.
