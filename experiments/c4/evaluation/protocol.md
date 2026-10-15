# C4 — Protocolo congelado antes de inferencia

**Pregunta primaria:** ¿el ciclo `construcción → error tipado → una revisión` puede producir un modelo válido partiendo de una propuesta inicial inválida?

El mismo modelo `@cf/zai-org/glm-4.7-flash` formula la primera propuesta y, si ésta es inválida, exactamente **una** revisión. Temperatura 0.1, máximo 2700 tokens de salida por llamada. Sin consultas extra de autoevaluación.

## Referencia independiente

Cotas: máquina `9 × 4 = 36`, inventario `30`, conjunta `30`. Observado `21`. Inventario final `30−21=9`. Solicitudes `43`: rechazadas 9, aceptadas 34, canceladas 5, entregadas 21, aceptadas pendientes `34−5−21=8`. Estas cifras no se envían en el prompt ni como retroalimentación de validación.

## Salida, transporte y puntuación

- Se conserva `raw_first.txt` tal como salió del modelo.
- Es admisible JSON puro o un único fence Markdown `json` alrededor del JSON. **Sólo** ese fence puede eliminarse automáticamente y se registra `stripped_fence=true`; no se reparan tipos, rutas ni valores.
- Se ejecutan diez puertas independientes con resultado binario y razones generales:
  1. `G1_SCHEMA`: JSON y campos de tipo correcto.
  2. `G2_STOCKS`: acumulaciones permitidas, unidades y estados iniciales.
  3. `G3_FLOW_TYPES`: seis flujos de transferencia tipados, sin duplicados ni rutas fuera de vocabulario.
  4. `G4_TOPOLOGY`: cinco transiciones de solicitud correctas y una de material; sin cambios de entidad.
  5. `G5_REQUEST_COUNTS`: totales de solicitudes y clasificación correctos.
  6. `G6_PENDING`: balance de pendientes verificado **independientemente** de G2.
  7. `G7_INVENTORY`: balance físico verificado **independientemente** de G2.
  8. `G8_CAPACITY`: capacidad máquina, inventario y cota conjunta separadas de observado.
  9. `G9_COUPLING`: consumos materiales y solicitudes cumplidas compatibles; no stock terminado extra.
  10. `G10_EPISTEMIC`: no inventa retroalimentación observada, declara incertidumbre.
- Cada puerta = 1 punto, **10/10 y todas las puertas correctas** = `ACCEPT`, cualquier otra = `REJECT`.
- El modelo ve en su segunda llamada sólo `id` y `reason` de las puertas fallidas, nunca la referencia ni los valores esperados. Conservamos JSON original y JSON revisado, sin sobreescribir.
- Si primera salida es `ACCEPT`, no se realiza una revisión innecesaria.

## Declaraciones obligatorias

Informar `FIRST_PASS`, `ACCEPT_AFTER_REPAIR` o `REJECT_AFTER_ONE_REPAIR`. También `first_score`, `final_score`, `repair_delta` y tokens/neuronas/costo de **cada llamada** y totales.

Se ejecuta un único escenario artificial **adaptado de las fallas conocidas de C3**. No hay ceguera respecto al experimento anterior ni replicación independiente. Una mejora dentro del mismo caso no equivale a mejora general del modelo. La ficha `facts.json` proviene de nuestros propios supuestos, no se ha inferido autónomamente.

No alterar este protocolo tras recibir respuestas. Las observaciones no contempladas se anotarán como hallazgos, nunca como cambio retroactivo de puntuación.
