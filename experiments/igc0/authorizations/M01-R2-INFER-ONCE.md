# IGC-0 · M01-R2 — autorización de UNA inferencia

**Fecha:** 2026-10-15.
**Investigador:** autorización explícita en el chat para ejecutar M01-R2.

## Alcance autorizado
- Cloudflare Worker: `igc0-review-lab.oulipo.workers.dev`, versión desplegada `4ac1bd77-ea85-4f51-aae9-fab8b564606a`.
- Modelo: `@cf/meta/llama-3.3-70b-instruct-fp8-fast`.
- Caso: `M01` y solo paquete público preparado por `prepare.py`.
- Etapa: `IG`, una llamada máxima a Workers AI, `max_tokens=4500`.
- Sin intentos automáticos adicionales, sin `REVIEW`, sin `C`, sin modificaciones del oráculo ni simulaciones.
- Guardar entrada, prompt, respuesta original, identificadores, uso de tokens y validación determinista en artifact de GitHub Actions.

## Puerta de seguridad
La rama `experiment/igc0-m01-r2-llama` y PR #3 deben coincidir.
El commit con mensaje `infer(igc0): authorize one-shot M01-R2 Llama call` dispara un solo workflow; `GITHUB_RUN_ATTEMPT != 1` bloquea reejecuciones facturables.

**No se autoriza** ninguna segunda ejecución ni ampliar el alcance.
