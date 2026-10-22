# EPI-03 · Decidir sin narrar: Clef, GLM y Clairic

**Estado: preparación únicamente. Sin inferencias reales. Sin cambios en IGC ni en workflows EPI-01/EPI-02.**

## Por qué
Comprobar si la respuesta acotada por alternativas/probabilidades resuelve mejor que una respuesta generativa el estado formal de soporte. No confundir la probabilidad que emite un clasificador con P(estructura real | evidencia): los expedientes son sintéticos y el gold es una consecuencia lógica de reglas explícitas.

## Subexperimento 1: clasificación cerrada (Clef frente a GLM-4.7-Flash)
- 12 casos sintéticos nuevos: 3 BOTH, 3 ONLY_H1, 3 ONLY_H2 y 3 NEITHER, congelados antes de llamar al proveedor. Cuatro opciones mutuamente excluyentes.
- 2 anclas diagnósticas de EPI-02 obtenidas de `short` commit `dc62f04bc0498d687c963c941f348dc793fbc9a4`, no incluidas en la métrica primaria.
- Los dos modelos reciben exactamente el mismo STATE JSON (fuentes, supuestos, reglas AND/OR, invalidaciones, historial). Ninguno recibe el gold, cierres calculados ni explicaciones anticipadas.
- Clef: `@cf/cloudflare/clef`, API nativa `model`/`state`/`questions` con `type: choice`, `criteria` y probabilidades explícitas por opción.
- GLM: `@cf/zai-org/glm-4.7-flash`, API `messages`; solo solicita `choice` y distribución de probabilidades, no explicaciones. Se preservan los resultados tal cual y se marcan los fences de Markdown si aparecen.
- El orden de las opciones rota de forma determinista por caso y es idéntico entre ambos modelos. Las llamadas se intercalan con semilla 20261021.

**Métrica primaria predeclarada** (solo 12 casos balanceados): exactitud top-1 con distribución válida y Brier multicategoría (menor es mejor), indicando por separado casos con probabilidades no válidas. Se registran resultados de las dos anclas por separado; no cuentan como éxitos del diseño balanceado. Se conservan respuestas crudas, latencia medida de cliente y consumo bruto devuelto por proveedor. Las probabilidades de GLM son auto-reportadas; las de Clef son la salida del modelo decisor: no asumir equivalencia de calibración ni probabilidades bayesianas.

**Regla exploratoria de interpretación:** tres o más aciertos adicionales en 12 casos y menor Brier en respuestas válidas constituyen solo una señal práctica a investigar; un empate o diferencia menor no autoriza proclamar superioridad. Un Brier con cobertura distinta debe presentarse acompañado por el número de distribuciones válidas. No se adjudicará un efecto estadístico con n=12.

## Subexperimento 2: Clairic numérico (independiente)
- `@cf/cloudflare/clairic` con `model: clairic`, `state` y `fields.stock_value` tipado.
- 4 problemas de balance de stocks **CALC** con solución aritmética exacta (`number`).
- 4 ejemplos **FORECAST** de series sintéticas con siguiente valor oculto (`estimate`, rango 0..100).
- Métricas: error absoluto/MAE, acierto exacto en CALC, cobertura p10-p90 si el proveedor la devuelve. Los cuatro pronósticos NO prueban calibración de intervalos ni habilidad causal; la serie no identifica un mecanismo dinámico.
- Clairic no se compara por Brier ni clasificación con Clef/GLM. Son problemas y objetivos distintos.

## Ejecución de diseño: sin coste ni credenciales

    python -m unittest discover -s experiments/decision-models-cf-v1 -p 'test_*.py' -v
    python experiments/decision-models-cf-v1/prepare.py --out /tmp/epi03-prepared

## Protocolos con red (NO autorizados en este PR)
- Para preflight no inferencial: `python experiments/decision-models-cf-v1/preflight.py`. Requiere secretos pero solo consulta el catálogo de tres modelos.
- Para inferencia se exige `EPI03_AUTHORIZATION=RUN_EPI03_MAX36`, `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_API_TOKEN`; preparar primero y ejecutar `python experiments/decision-models-cf-v1/run_cloudflare.py --out <directorio>`.
- Un máximo de 36 solicitudes: 14 Clef + 14 GLM + 8 Clairic. Sin reintentos; primer error detiene campaña y preserva manifiesto/artefactos parciales.
- Para ejecución en GitHub Actions se necesita otro dispatcher, separado en `main`, fijado a un SHA revisado del experimento y con autorizaciones distintas para preflight e inferencia. **No utilizar ni modificar el dispatcher de EPI-02.** Abrir un PR no ejecuta ningún modelo.
- Después de inferencia: `python experiments/decision-models-cf-v1/evaluate.py --out <directorio>`.

## Condiciones de validez
Todas las opciones corresponden a estados lógicos, NO a hipótesis verdaderas en el mundo; los escenarios son ficticios y el gold se calcula mediante cierre determinista. No fusionar estos resultados con puntajes de EPI-02 como si fueran el mismo protocolo. No eliminar fallos de formato ni renormalizar probabilidades post-hoc.

## Referencias de API verificadas
- Clef: https://developers.cloudflare.com/workers-ai/models/clef/
- Clairic (preview): https://developers.cloudflare.com/workers-ai/models/clairic/
- Cloudflare changelog: https://developers.cloudflare.com/changelog/post/2026-10-19-clairic-workers-ai/

## Integridad
`fixtures/*.json` y `evaluation/gold.json` están comprometidos en Git antes de ejecutar. `prepare.py` recomputa cada etiqueta lógica y falla si discrepa del gold. Las solicitudes se guardan con SHA256. En inferencia el runner verifica los hashes antes de la primera llamada. `results/` queda excluido de Git.
