# C4.1 — DeepSeek R1 Distill Qwen 32B: generación de JSON

**Diseño previo:** 2026-10-13. **Estado:** ejecutado y evaluado. [Informe C4.1](results/c41-2026-10-13-report.md).

## Objetivo
Comprobar si `@cf/deepseek-ai/deepseek-r1-distill-qwen-32b` genera un objeto JSON directamente utilizable en el mismo problema C4. Distinguir **sintaxis JSON**, **esquema tipado** y **fidelidad de modelo SD**.

**Controles:** el escenario y los tres archivos de instrucciones de C4 (`scenario.md`, `contract.md`, `build.md`) se reutilizan **sin cambiarlos**. Sólo cambia el motor. Dos corridas independientes con igual prompt y mismos parámetros:

1. `prompt_only`: sin `response_format` (similar a la ejecución previa de GLM).
2. `json_mode`: mismo prompt y `response_format: {"type":"json_object"}` nativo de Workers AI; no se comunica esquema/solución adicional al modelo.

No se ejecuta la revisión autorreparadora de C4. Es una prueba de la primera generación, no de reparación.

## Verificación por tres capas

1. **Transporte:** ¿Cloudflare respondió `response` como texto u objeto? ¿El texto es JSON puro, JSON tras retirar *únicamente* un fence Markdown, JSON acompañado de razonamiento, o no JSON?
2. **Esquema:** ¿el JSON tiene todos los campos y tipos obligatorios? Evaluación con la puerta `G1_SCHEMA` del validador C4.
3. **SD:** ¿cumple las diez puertas? Se informan *todos* los errores sin corregir valores.

La respuesta original y el JSON del proveedor se conservan íntegros en los artefactos. Un objeto nativo `response` de la API no se contabiliza como **texto JSON crudo** producido por el modelo; se clasifica como **objeto estructurado del proveedor**.

**Presupuesto:** máximo 2 inferencias, hasta 3,500 tokens de generación cada una, sin reintentos automáticos, costo estimado con las tarifas oficiales `$0.497/M` entrada y `$4.881/M` salida (antes de franquicia). El modelo es de razonamiento, por lo que el límite de salida también limita la cantidad de texto de reflexión y puede truncar la respuesta.

**Advertencia:** una o dos corridas no prueban fiabilidad estadística. JSON Mode puede producir errores de imposibilidad de satisfacer formato, y hay que registrar dichos errores como fallos de formato, no de SD. Ver: https://developers.cloudflare.com/workers-ai/features/json-mode/ y https://developers.cloudflare.com/workers-ai/models/deepseek-r1-distill-qwen-32b/.
