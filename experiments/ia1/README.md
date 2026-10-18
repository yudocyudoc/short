# IGC v3 — IA-1: descripción → evidencia → hipótesis molecular

PR encadenado a E1 #34 y E0 #33, aún sin fusionar. Ver [contrato](CONTRACT.md), [casos](cases.json), [rúbrica declarada antes de la inferencia](evaluation_gold.json), [protocolo](protocol.json) y [hoja de ruta v3](../../docs/IGC_SD_HOJA_DE_RUTA_CONSOLIDADA_v3_2026-10-18.md).

El experimento pide a Llama 3.3 70B interpretar hechos breves en español, separar evidencia física de transformación informacional y entregar un AST que E1 pueda validar. **El problema no entrega una solución completa.** No es un benchmark independiente de empresas ni la recuperación de verdad estructural.

Prueba sin IA ni API:

    python -m unittest discover -s experiments/ia1 -p 'test_*.py' -v
    python experiments/ia1/run.py --prepare-only --out experiments/ia1/output/prepared

Inferencia real sólo desde workflow autorizado de GitHub Actions con Cloudflare Workers AI, usando secretos del repositorio; los tokens nunca se imprimen ni se exportan. Se conservan solicitudes depuradas, respuestas crudas, resultados del linter, rúbrica, código y errores. Nunca se reescriben respuestas de un modelo para que entren en el AST.

**Doble veredicto:** clasificación de evidencia y construcción de AST son cosas diferentes; las dos pueden pasar o fallar independientemente. El AST propone una hipótesis, no identifica el grafo real. El baseline usa los mismos textos y no llama a modelos de IA.

Un resultado de Llama bajo no agota la exploración con IA: en otra corrida comparable se podrá usar GPT, Claude, Gemini u otro modelo más capaz autorizado.

## Enmienda preregistrada v2, antes de la primera llamada a Llama

La prueba mecánica previa (sin IA) produjo **12/12 clasificaciones correctas** con la colección inicial. Este resultado reveló un techo determinado por palabras clave y un experimento incapaz de detectar ventaja semántica. Antes de ejecutar cualquier inferencia Llama se añadieron **seis viñetas adversariales I13–I18**: negación de un supuesto, reclasificación física por auditoría, evidencia positiva sin palabras clave, y conflicto entre afirmación y confirmación. Se conserva el precedente 12/12 y se congela la nueva población de 18 casos sin modificar la respuesta del modelo en función de resultados posteriores. El nuevo conjunto sigue siendo sintético, redactado por autores y no ciego externamente.
