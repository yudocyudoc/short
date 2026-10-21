# EPI-01 — memoria epistemológica para un LLM

**Estado:** preparación y pruebas sin inferencia. El piloto de nueve llamadas requiere autorización manual aparte.

## Pregunta y condiciones
Con el mismo modelo, expediente y preguntas, ¿mejora la respuesta al añadir estado booleano o linaje explícito de justificaciones y entornos mínimos?

- **A — Documental:** expediente y revisión documental, sin etiquetas calculadas.
- **B — Booleano:** mismo expediente y estado actual soportado/no soportado.
- **C — Epistemológico:** mismo expediente, etiquetas mínimas, justificaciones, supuestos, evidencia y nogood.

La preparación compara dos cálculos independientes tipo ATMS y OR/AND; si las etiquetas no coinciden exactamente, falla.

## Ejecución
Los PRs/pushes ejecutan sólo preparación y pruebas sin secretos. El workflow manual acepta `auth_check` (consulta acceso/modelo sin inferencia) o `infer` (exige `RUN_EPI01_MAX9`, hasta nueve llamadas y sin reintentos). El archivo de evaluación nunca se carga en los prompts.

El workflow_dispatch sólo aparecerá en Actions cuando su definición llegue a la rama por defecto. Al estar este PR sin fusionar, las pruebas del PR sí corren; el lanzamiento manual queda preparado pero todavía no disponible.

## Límites
Piloto sintético y exploratorio: no prueba superioridad estadística, no evalúa el motor ATMS frente a OR/AND, ni valida causalidad o una organización real.

## Procedencia
Adaptador REST recuperado en forma acotada del experimento C0, commit `92049e34cb35d9ea0177d72f3c2b1c11c0459210`. Endpoints Cloudflare: `POST /accounts/{account_id}/ai/run/{model}` y `GET /accounts/{account_id}/ai/models/search`. No se copian credenciales.
