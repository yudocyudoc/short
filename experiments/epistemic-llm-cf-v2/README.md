# EPI-02 · Persistencia y revisión epistemológica

**Estado:** piloto sintético preparado. Ninguna inferencia autorizada ni ejecutada por este PR.

## Pregunta
¿Los entornos mínimos históricos de soporte (C) ayudan a un LLM a reconstruir revisiones y resolver un contrafáctico nuevo mejor que disponer únicamente del estado booleano precomputado (B)?

Dos casos inéditos EPI02-SURVIVE y EPI02-LOSS, dos tareas por caso (HISTORY y COUNTERFACTUAL), dos brazos, tres repeticiones por celda: **24 llamadas máximo**.

Ambos brazos reciben las mismas fuentes, reglas, supuestos, revisiones y contrafáctico no resuelto. B recibe status_by_revision; C añade minimal_support_by_revision. El resultado del contrafáctico CF NO aparece en los contextos. Se verifica paridad entre una copia byte a byte de IGC F0 AtmsProbe y un cierre OR/AND independiente, únicamente para estas fixtures.

## Rigor y resultados
- IDs namespaced epi02:s1:* y epi02:s2:* (no identifican las moléculas CS-01/02 de IGC ni las hipótesis de EPI-01).
- Gold/rúbrica fijados en evaluation/gold.json, totalmente excluidos de los contextos e inferencias.
- Métrica principal predeclarada: estados por hipótesis/revisión correctos (6 en HISTORY y 2 en COUNTERFACTUAL). Comparar proporciones en vez de sumar denominadores arbitrarios.
- Evaluar formato puro y normalización de fences por separado del significado; no reparar estados ni justificaciones silenciosamente.
- Validar IDs y contradicciones internas; la salida original siempre permanece inalterada.
- Crear paquetes ciegos de respuestas y guardar la correspondencia por separado; anotar responsables y desacuerdos en evaluación humana posterior si se realiza.
- El modelo es @cf/zai-org/glm-4.7-flash, temperatura 0.1, salida máxima 1800 tokens, sin reintentos. Registrar uso y neuronas.
- Es un piloto exploratorio. No demuestra superioridad estadística ni preferencia ATMS frente a OR/AND.

## Preparar sin coste
Ejecutar:
    python experiments/epistemic-llm-cf-v2/prepare.py --out /tmp/epi02-prepared
    python -m unittest discover -s experiments/epistemic-llm-cf-v2 -p 'test_*.py' -v

## Inferencia (requiere autorización independiente)
scripts/run_cloudflare.py exige EPI02_AUTHORIZATION=RUN_EPI02_MAX24, CLOUDFLARE_ACCOUNT_ID y CLOUDFLARE_API_TOKEN. El workflow del PR no suministra secretos ni lo ejecuta. Para inferencia manual en GitHub Actions será necesario un dispatcher separado en main, fijado al SHA aprobado de EPI-02; el de EPI-01 permanece intacto. No fusionar por accidente ni lanzar llamadas pagadas.

## Después de inferencia
    python experiments/epistemic-llm-cf-v2/evaluate.py --results <directorio>

Genera métricas deterministas, validación formal y paquetes anonimizados en blinded/. El blinding-map.json permanece fuera de blinded/ para ocultar asignaciones al evaluador humano. No usar el gold ni la puntuación dentro de prompts.

## Procedencia
AtmsProbe idéntico a IGC/scripts/f0_atms_probe.py, blob Git SHA-1 659e9dfe463daf4a03144c8d55622c9eeffca79a. Runner Cloudflare derivado del piloto short EPI-01, sin credenciales incorporadas.
