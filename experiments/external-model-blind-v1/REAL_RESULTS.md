# IGC — evaluación con fuente y árbitro externos: resultados y cierre metodológico

**Fecha local:** 2026-10-16; ejecuciones registradas en GitHub en 2026-10-17 UTC. **Estado: no hay score B/C de Llama.** Ninguna respuesta nueva de Llama se generó en estos intentos.

## Separación inicial de funciones

- Qwen3-30B-A3B genera 24 viñetas cualitativas a partir de 24 semillas sectoriales preregistradas.
- GLM-4.7-Flash actúa como árbitro automático ciego a resultados de Llama.
- Llama 3.3 70B B (SD general) y C (moléculas) siguen con prompts, scorer, baseline y catálogo byte-frozen desde PR #21.
- *Modelo evaluador distinto no equivale a verdad causal de un evaluador humano*. Objetivo exploratorio, NO confirmación independiente.

## Ejecución #1 — integración fallida ANTES de Llama

[Run #38995455018](https://github.com/yudocyudoc/short/actions/runs/38995455018) · [Originales y estado Qwen/GLM (artifact 12086714733)](https://github.com/yudocyudoc/short/actions/runs/38995455018/artifacts/12086714733).

| Evento | Casos |
|---|---:|
| Qwen responde | 24/24 |
| Qwen devuelve JSON formalmente válido | 16/24 |
| Qwen devuelve JSON con llave sobrante | 8/24 |
| GLM completa una adjudicación válida | **0/16** |
| Llama consultado | **0** |

El output de GLM contenía `choices[0].message.content=null` y texto extenso en `reasoning`: el límite `max_tokens=1300` se consumía antes de cualquier contenido final. El gate abortó con `INSUFFICIENT_REVIEWED_CASES_BEFORE_ANY_LLAMA`. No se reinterpretaron referencias vacías como abstenciones.

## Ejecución #2 — recuperación técnica prospectiva v1.1

[Run #38996096968](https://github.com/yudocyudoc/short/actions/runs/38996096968) · [16 viñetas originales, nuevos textos íntegros de GLM y referencias (artifact 12086839711)](https://github.com/yudocyudoc/short/actions/runs/38996096968/artifacts/12086839711).

- Se volvió a usar **exactamente el corpus original** de las 16 viñetas sintácticamente válidas, con huella SHA-256 de su artefacto fuente `b296c42fe129e59bffa158a2bec771b36d39e21e5ddbc7424c0734ac5cf122c9`. Ocho viñetas mal formadas permanecieron excluidas.
- No se generaron nuevos casos Qwen, no se modificaron las afirmaciones del campo y no hubo respuestas Llama para consultar al árbitro.
- La nueva solicitud GLM utilizó `chat_template_kwargs.enable_thinking=false` y `reasoning_effort=null`, según API de Cloudflare.

| Resultado GLM v1.1 | Casos |
|---|---:|
| Adjudicaciones recibidas y parseadas | 16/16 |
| GLM declara etiqueta determinada | **7/16** |
| GLM declara INDETERMINATE | **9/16** |
| Umbral fijado previamente para empezar Llama | 12 |
| Nuevas llamadas Llama | **0** |

GLM etiquetó como selección vacía determinada a X02, X07, X16 y X22. Eligió BACKLOG_FLOW para X05 y X24; y MTO_S2_PATTERN para X15. Nueve casos restantes quedaron INDETERMINATE. El gate detuvo las pruebas con `INSUFFICIENT_VALID_LABELS_STOP_BEFORE_LLAMA`.

## Advertencia mayor: el árbitro GLM no es gold semánticamente válido por defecto

La evaluación automática sólo garantiza **citas literales**, no pertinencia causal. Al inspeccionar las salidas originales aparecieron dos fallas:

1. **X15 es un posible falso positivo serio.** GLM infirió `MTO_S2_PATTERN` a partir de reuniones para priorizar entregas, retrasos de recepción y comunicación al cliente, pero los hechos no establecen la secuencia necesaria: cola de trabajo aceptado sin preparar → preparación → acumulación de trabajos terminados → despacho. La cita es textual y formalmente válida, pero la inferencia causal de una molécula completa no está sustentada.
2. En X03 y X14, GLM justificó abstenerse en parte porque faltaban *datos cuantitativos*. Sin embargo, la tarea se diseñó explícitamente para seleccionar estructuras **sin cifras**. Éste es un desacople metodológico del árbitro, no una razón automática para exigir valores numéricos.

Por tanto, **ni siquiera sería correcto evaluar los 7 casos determinados como verdad causal humana**. La cifra 7/16 describe cumplimiento de formato/decisión del modelo árbitro; no exactitud verificada.

## Veredicto

**Sin comparación de Llama B/C, sin resultados estadísticos y sin mejora demostrada en esta etapa.** Las barreras metodológicas previnieron inferencias no justificadas; no hay scores que completar o corregir retrospectivamente.

El hallazgo práctico es que sustituir al autor humano del benchmark por dos modelos distintos no resuelve el problema fundamental: los casos pueden carecer de evidencia estructural y el adjudicador puede cometer exactamente las mismas extrapolaciones semánticas que queremos medir en Llama.

## Próximo protocolo recomendado (sin ejecutar inferencias todavía)

1. Construir un paquete de casos **independientes de las predicciones del evaluado**, ligados a mecanismos positivos y contraejemplos. Preferir ejemplos con procedencia externa verificable o un anotador humano independiente.
2. Pedir a un revisor externo —idealmente humano, o Claude con sus propias instrucciones y ceguera— que determine tipos de mecanismo y prueba textual sin mirar respuestas Llama ni etiquetas GLM.
3. Incluir opción explícita `NO_MATCH`, `CONTRADICTORY` o `INSUFFICIENT_EVIDENCE` para que los negativos puedan ser evaluados como negativos sin confundirlos con etiquetas indecidibles; registrar controversias para adjudicación humana.
4. Congelar las adjudicaciones **antes** de llamar a Llama, comprobar tasa de casos informativos/negativos y sólo después ejecutar prompts B/C congelados.
5. Mantener controles de comportamiento separados: conocer el nombre de una molécula no prueba su dinámica ni observabilidad en una empresa real.

**No crear otro score exploratorio cambiando a posteriori etiquetas, umbral mínimo o casos.** Esta campaña v1/v1.1 queda archivada como falla de construcción de benchmark y demostración de los límites de usar árbitros LLM como verdad independiente.
