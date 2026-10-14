# C4.2 — Protocolo y reglas de adjudicación (congelados antes de inferencias)

**Modelo:** `@cf/deepseek-ai/deepseek-r1-distill-qwen-32b`.
**Dos llamadas máximo:** control A y tratamiento B. `temperature=0.1`, `max_tokens=3500`, `stream=false`, sin `response_format`. Orden A,B. Mismo contenido de `scenario`, `contract`, `build` usado en C4.1; B añade exclusivamente `flow-coverage.md` al final.

## Transporte (ambos brazos)
Permitir sólo cuatro formas exactas: objeto nativo de respuesta; JSON puro; un solo fence Markdown `json` externo; exactamente un `<think>...</think>` inicial seguido de JSON puro o un solo fence. No texto adicional, ni doble bloque think, ni JSON recuperado de una cadena mayor. La sección `think` se archiva, pero **nunca se considera parte del JSON semántico**. Mantener también el texto bruto íntegro. Si la forma no pasa, resultado `FORMAT_REJECT` y no puntuar como modelo SD válido. Registrar la razón.

## Comprobaciones
- `format_ok` y `G1_SCHEMA` de C4 se informan separadamente.
- Diez puertas originales `G1…G10` de `scripts/c4_validator.py`, **sin alteración**.
- **P11: STOCK_FLOW_CERTIFICATE**. Para cada stock declarado, leer flujos cuya `to`/`from` coincide exactamente con su `id`; confirmar `final = initial + sum(in) − sum(out)`, tipos y unidades compatibles; toda variación distinta de cero requiere flujos incidentes compatibles; prohibir flujos de cantidad negativa y desajustes entre tipos `request`/`material`. No se deducen flujos ausentes ni se completa el grafo. Si un stock extra aparece, P11 puede cerrarlo, pero G2 sigue rechazando acumulaciones no respaldadas. El certificado muestra por stock el delta declarado y el delta implicado por flujos, **sin sustituir números**.
- Aceptación estricta = formato OK, C4 10/10 y P11 PASS. Reportar puntajes C4 y P11 por separado, además del veredicto global.
- Éxito del tratamiento B sólo como **señal exploratoria** si B supera el control A en cobertura/puertas sin inventar mecanismos, con **N=1 por condición**. Nunca atribuir causalidad estadística.
- Reportar `prompt_tokens`, `completion_tokens`, `neurons`, costo estimado (tarifas: US$0.497/M entrada y US$4.881/M salida), y número de llamadas. No confundir estimación con factura.

## Controles antes de inferir
Ejecutar tests sin IA: caso válido construido desde la evidencia, ausencia de flujo material con stock numéricamente correcto, omisión de flujo request, arista mal tipada, exceso de stock, desbalance por stock, think JSON balanceado, cierre ausente, dos segmentos think, prosa extra, fences anidados y JSON truncado. Registrar fallas de CI y NO disparar inferencias si tests fallan.

## Restricciones de interpretación
Diseño adaptativo posterior al hallazgo de C4.1. Se probará **cobertura declarativa**, no identificación causal; el contrato tipado y la clave fija reducen el espacio de respuestas. Evitar llamar «generación espontánea de modelo» a un éxito condicionado por esquema y test de hechos previamente suministrados.
