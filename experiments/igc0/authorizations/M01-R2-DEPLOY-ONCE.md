# M01-R2 · autorización de despliegue (una sola vez)

**Fecha:** 2026-10-15
**Aprobación:** el investigador autorizó expresamente desplegar el Worker R2, sin inferencia.
**Rama protegida del experimento:** `experiment/igc0-m01-r2-llama`.
**Alcance:** publicar el Worker `igc0-review-lab` con Llama 3.3 70B y JSON Schema IG.
**Prohibido:** llamadas a Workers AI, ejecutar M01, contraste, revisión automática, proyecciones o fusionar PR #3.
**Activación:** este archivo y el mensaje exacto del commit disparan el workflow de despliegue una sola vez. Tras verificarlo, retirar el disparador de `push` del workflow y conservar el modo manual.

**Verificación:** ejecución de despliegue registrada como check de PR #3 para lectura de logs. No autoriza inferencias.
