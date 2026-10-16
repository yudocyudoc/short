# IGC 3×2 — réplica exploratoria con Llama 3.3 70B

**Modelo seleccionado:** `@cf/meta/llama-3.3-70b-instruct-fp8-fast` (Cloudflare Workers AI), utilizado previamente en el proyecto IGC para M01-R2.

**Motivo:** a petición del investigador, contrastar con una variante de Llama después de ver los resultados de DeepSeek. Esta selección post hoc hace la comparación **exploratoria**, no un ensayo confirmatorio con selección previa de modelos.

## Condiciones fijadas

- Son exactamente los seis prompts de BB01, W17 y W18, brazos A/B, comparados con la corrida DeepSeek [38848438175](https://github.com/yudocyudoc/short/actions/runs/38848438175).
- El CI comprueba los seis SHA-256 previos de texto de prompt. Mismo JSON de casos, mismo código de probes, temperatura 0.1, máximo 3500 tokens, seis solicitudes aisladas, cero reparaciones y sin feedback.
- Único cambio experimental intencional: identificador del modelo servido por Cloudflare.
- Variación de respuestas y de proveedor es un factor de ruido; una corrida/caso/modelo no permite inferir superioridad estadística.
- Conservar el informe DeepSeek y la rúbrica previamente fijada en [protocol.md](protocol.md), sin ajustar criterios para Llama.
- Artefacto Llama separado, sin mezclar respuestas originales de ambos modelos.

## Juicio

Evaluar por mecanismo correcto en BB01 (lookup por encima de diagonal y congelación de backlog al desaparecer POS), tiempo exacto contractual W17, y ausencia de falsas alarmas en W18, más distinción entre falla estructural y falta de datos comerciales. Comparar explícitamente las seis parejas de respuestas y no puntuar solo JSON válido.

## Ejecución

La autorización de gasto para esta única ronda la dio el investigador en la conversación. El PR efímero dispara una corrida mediante un cambio de título y luego se restaura el título y el workflow a autorización manual para evitar nuevas consultas. El preflight no factura inferencias. No exponer claves Cloudflare ni evaluar respuestas con criterios nuevos.

