# IGC — Evaluación ciega automatizada entre tres familias de modelos

**Diseño preregistrado:** 2026-10-16. **Estado: evaluación exploratoria con referencias automáticas, NO gold humano externo.**

## Por qué este experimento

En los 24 casos diseñados y etiquetados por el mismo equipo, las variantes obtuvieron 10/24 (baseline regex), 15/24 (Llama SD general) y 18/24 (Llama + catálogo de moléculas). Aunque el andamiaje mejoró de manera descriptiva, los casos y etiquetas podían compartir los sesgos del diseñador.

Aquí se separan responsabilidades en **tres modelos de familias distintas**:

1. **Qwen3-30B-A3B** genera un caso cualitativo nuevo a partir de una semilla temática muy general, sin conocer categorías de moléculas, gold ni respuestas Llama.
2. **GLM-4.7-Flash** hace una adjudicación previa del caso, usando los cuatro contratos registrados de moléculas, y aporta citas literales; nunca recibe respuestas de Llama. Se archiva el gold **antes** de disparar la prueba. Sólo evaluamos casos con adjudicación formalmente válida; los excluidos se contabilizan.
3. **Llama 3.3 70B** recibe idénticos prompts, opciones y contrato de salida del PR #21 (dos condiciones, SD genérica y moléculas). **Ninguno de esos cuatro archivos originales se ha modificado**: el runner exige sus Git blob SHA exactos, de modo que las llamadas usan las mismas instrucciones que en los estudios anteriores.

4. **Reglas deterministas:** la misma función regex del PR #21 sobre esos nuevos casos, sin retocar palabras clave.

**Importantísimo:** una adjudicación por GLM, aunque sea ciega a Llama, es una **referencia automática**. No certifica que GLM tenga razón. Además, GLM recibe el catálogo molecular para poder aplicar contratos; esto puede favorecer conceptualmente la variante molecular frente a la general. El experimento mide *acuerdo con el revisor GLM* y ayuda a localizar desacuerdos; no establece calidad causal real sin revisión humana.

## Aislamiento y orden verificable

La CI separa los trabajos:

- `deterministic`: tests, hashes, generación de solicitudes sin llamadas.
- `independent-reference`: Qwen redacta hasta 24 relatos; GLM adjudica cada uno por separado. Archiva caso original, respuesta literal, cita y decisión. **Publica un artefacto con el gold y SHA-256 antes de que se ejecute Llama.**
- `frozen-llama-test`: descarga exclusivamente ese artefacto, verifica su hash y recién entonces ejecuta Llama. Alterna orden de los dos prompts por caso y puntúa con el `evaluate.py` original.

Toda solicitud/resultado se conserva. **No hay reintentos** si un modelo devuelve salida mal formada; cada exclusión queda registrada como tal. No se sustituyen casos fallidos ni se vuelven a solicitar hasta conseguir respuestas que nos gusten.

## Material y métricas

- `design.json`: 24 semillas temáticas, redactadas antes de consultas de modelos.
- `run_blind.py`: 3 fases con revisión de hashes, generación externa, adjudicación y contraste pareado.
- `test_blind.py`: pruebas de separación de modelos, no cifras, citas literales, hashes, sesgo de etiquetas.
- CI: `.github/workflows/igc-external-model-blind-v1.yml`.

Las métricas conservan selección exacta, citas literales, apoyo al hecho referenciado y aprobación estricta. Reporta exclusiones, abstenciones falsas, falsos positivos y casos discordantes B/C. McNemar exacto es **descriptivo y exploratorio**, no una declaración de potencia estadística.

## Límites

- Los casos son sintéticos de Qwen, no documentos de empresas existentes.
- Qwen no es un anotador independiente humano; las semillas sectoriales las redactó el investigador.
- GLM es un árbitro automático y puede equivocarse, especialmente ante mecanismos semejantes o relaciones negadas.
- El filtro de etiquetas válidas puede cambiar la mezcla de dificultad, aunque está congelado antes de Llama.
- No se pide al LLM ninguna cifra o ecuación, no se crean clases Modelica y **OpenModelica no participa** en esta evaluación.
- El conjunto es pequeño y no equivale a una prueba poblacional confirmatoria.
- Si las respuestas no demuestran un efecto robusto, no retocar retrospectivamente prompts ni pseudo-gold.

## Ejecución

Pruebas sin coste:
```sh
python -m unittest discover -s experiments/external-model-blind-v1 -p 'test_*.py' -v
python experiments/external-model-blind-v1/run_blind.py --prepare-only --out /tmp/igc-blind
```

Las llamadas auténticas sólo se activan por el commit de autorización en la rama experimental con el mensaje exacto `run(igc): Qwen generated blinded GLM labels before Llama`. Secrets Cloudflare ya registrados en GitHub, sin copiarlos al repo. La fase de referencia debe reunir al menos 12 adjudicaciones válidas entre 24 intentos; si no, **no se hacen llamadas a Llama**.

## Interpretación correcta

- Si C>B, es una ventaja contra un **árbitro automático ciego**, no una prueba de verdad causal.
- Si B>=C, el andamiaje no aporta ventaja demostrada en ese entorno.
- Si los resultados dependen de casos polémicos, la decisión científicamente útil es **adjudicación humana del subconjunto discordante** sin ver el nombre de cada brazo.
- Antes de construir un compilador completo IGC-SL o invertir en infraestructura de moléculas, comprobar si el beneficio causal supera el coste de su preparación y mantenimiento.

Fuentes de modelos Workers AI: [Qwen3](https://developers.cloudflare.com/ai/models/%40cf/qwen/qwen3-30b-a3b-fp8/), [GLM-4.7-Flash](https://developers.cloudflare.com/changelog/post/2026-02-13-glm-4.7-flash-workers-ai/).
