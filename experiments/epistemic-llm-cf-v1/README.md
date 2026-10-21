# EPI-01 — memoria epistemológica para un LLM

**Estado:** preparación y pruebas sin inferencia. El piloto de nueve llamadas requiere autorización manual aparte.

## Pregunta y condiciones

Con el mismo expediente y las mismas tareas, ¿ayuda al modelo recibir estados booleanos o memoria explícita de soportes y revisiones?

- **A — Documental:** expediente con documentos, afirmaciones, supuestos y justificaciones originales, sin etiquetas calculadas.
- **B — Booleano:** todo A + estado actual soportado/no soportado.
- **C — Epistemológico:** todo A + entornos mínimos antes/después de la revisión, derivación de nogoods y estado calculado de cada justificación.

Los tres brazos comparten las mismas fuentes, afirmaciones y reglas declarativas. La diferencia experimental está en la información derivada que se añade en B y C. La sugerencia de observación discriminante no aparece en el expediente.

## Referencia lógica

La preparación usa una copia byte a byte del prototipo `AtmsProbe` de IGC, junto con un cierre OR/AND independiente. Se comparan sus etiquetas en esta fixture solamente. No se afirma equivalencia general entre motores ni se identifica el prototipo como motor de producción.

- Fuente: `yudocyudoc/IGC/scripts/f0_atms_probe.py`
- Git blob SHA-1: `659e9dfe463daf4a03144c8d55622c9eeffca79a`
- Referencia de rama: `fm-12-13-atms-llm-ablation`
- Semántica comparada: entornos mínimos de soporte de CS-01 y CS-02, antes y después de REV-1.

## Ejecución

Los PRs/pushes ejecutan sólo preparación y pruebas sin secretos. El workflow manual del experimento acepta `auth_check` (consulta sin inferencia) o `infer` (requiere `RUN_EPI01_MAX9`, hasta nueve llamadas y sin reintentos). La rúbrica nunca se carga en los prompts.

El workflow de inferencia no está en `main`, por lo que Actions no puede despacharlo desde la rama por defecto mientras PR #41 siga abierto. Un dispatcher independiente en una rama/PR separado permitirá seleccionar un SHA explícito de la rama experimental; no fusionará EPI-01.

## Límites

Piloto sintético y exploratorio: no prueba superioridad estadística, no evalúa ATMS frente a OR/AND como motores, ni valida causalidad o una organización real. El dictamen lógico se limita a esta fixture y a la versión exacta del prototipo referenciado.

## Procedencia de Cloudflare

Adaptador REST recuperado en forma acotada del experimento C0, commit `92049e34cb35d9ea0177d72f3c2b1c11c0459210`. No se copian credenciales.
