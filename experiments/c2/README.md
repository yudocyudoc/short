# C2 — Reglas formales de SD frente a gramática descriptiva

**Fecha de diseño:** 2026-10-13. **Estado:** experimento ejecutado; diseño y referencia registrados antes de generar respuestas. [Resultados](results/README.md).

## Pregunta

¿Exigir las reglas formales de stocks y flujos de SD (según Sterman, *Business Dynamics*, capítulo 6, especialmente 6.1–6.2) ayuda a un LLM a reconstruir un sistema pequeño con mayor corrección que las recomendaciones generales entregadas en C1?

**Control:** A utiliza exactamente la gramática descriptiva de C1; B recibe reglas formales de construcción sin información de la respuesta correcta. La descripción C2 es nueva en números y resultados para no repetir C1 literalmente, pero no constituye una validación fuera de distribución.

La referencia y la rúbrica `evaluation/reference.md` se registran antes de ejecutar, y están excluidas del contexto del agente.

**Proveedor:** Cloudflare Workers AI `@cf/zai-org/glm-4.7-flash`; misma temperatura, modelo y límite para A y B; máximo dos inferencias.

**Limitaciones:** un par de corridas no demuestra robustez. Se estudia *representación formal* en un caso artificial, no descubrimiento de causalidad.
