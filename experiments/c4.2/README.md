# C4.2 — DeepSeek: transporte de razonamiento + cobertura exhaustiva de stocks

**Estado:** ejecutado y evaluado; diseño preregistrado antes de inferencia. **Fecha:** 2026-10-13 (México). [Ver resultados](results/c42-2026-10-13-report.md).

## Pregunta
¿Exigir explícitamente, dentro del prompt, que **cada variación de stock se justifique con flujos tipados** permite que DeepSeek-R1-Distill-Qwen-32B produzca un grafo completo sin convertir la coherencia interna en sustituto de evidencia observada?

### Condiciones: mismo modelo y mismos hechos

A = línea base **exactamente igual al prompt de C4.1** (archivos inalterados `experiments/c4/scenario.md`, `prompts/contract.md`, `prompts/build.md`).

B = exactamente ese prompt, seguido de `prompts/flow-coverage.md`. **Sólo este apéndice varía.**

Ambos: `@cf/deepseek-ai/deepseek-r1-distill-qwen-32b`, API REST de Cloudflare Workers AI, `temperature=0.1`, `max_tokens=3500`, `stream=false`, sin JSON Mode. Una llamada por brazo. Orden fijo A→B. Sin reintentos ni feedback entre brazos.

### Separar transporte de modelo
`scripts/c42_transport.py` identifica si el resultado es un objeto del proveedor, JSON puro, JSON con un solo fence Markdown, o **un único** bloque `<think>...</think>` al inicio seguido de JSON puro / único fence. No recupera JSON desde prosa, no descarta más de un bloque de pensamiento ni altera los datos. Conserva texto original, sección de razonamiento y JSON final separadamente en artefactos.

El control A recibe **la misma capa de transporte** que B: esto evita atribuir a la regla de flujos una mejora que en realidad proviene del parser.

### Validación
`scripts/c42_validator.py` mantiene inalteradas las 10 puertas de C4 y agrega una prueba independiente de **cierre de cada stock declarado por flujos incidentes**, con unidades correctas. El objeto no se repara; se emite un certificado auditable de balance por stock y se rechazan variaciones no explicadas.

`evaluation/protocol.md` contiene los criterios completos y se congela antes de correr.
`evaluation/evidence-ledger.md` mantiene por separado hechos de entrada y deducciones, sólo para auditoría del validador, NO para la IA.

### Precauciones
Este experimento es **adaptativo**: C4.1 mostró que faltaba el flujo material, y B está dirigido explícitamente a esa falla. No es un benchmark independiente ni demuestra recuperación de causalidad real, flexibilidad a otros sectores, ni desempeño estadístico robusto.
