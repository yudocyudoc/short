# C4 — Contrato de modelo tipado

**Devuelve sólo un objeto JSON**, sin explicación adicional. Se verificará la estructura y el significado de los campos.

Estructura requerida:

{
  "horizon_hours": 0,
  "stocks": [
    {"id":"inventory","unit":"beverage_equivalent","initial":0,"final":0},
    {"id":"accepted_pending","unit":"request","initial":0,"final":0}
  ],
  "flows": [
    {"id":"identificador_unico","entity":"request","from":"origen","to":"destino","total":0,"unit":"request"}
  ],
  "capacity": {
    "machine_per_hour":0,
    "machine_period_max":0,
    "material_period_max":0,
    "joint_period_max":0,
    "observed_prepared":0
  },
  "feedback":[],
  "unknowns":["incertidumbre observacional"]
}

**Importante:** los ceros son ejemplos de tipo, **no valores de solución**. Incluye stocks adicionales sólo si tienen existencia acumulable respaldada por el escenario. `prepared_stock` (unidad `beverage`) es una opción a evaluar, no un elemento obligatorio.

Estados posibles para solicitudes: `external`, `submitted`, `accepted_pending`, `rejected`, `canceled`, `fulfilled`. Las solicitudes son `entity:"request"`, `unit:"request"`. Materiales usan `entity:"material"`, `unit:"beverage_equivalent"`, estados `inventory` y `consumed`.

En `flows.total` coloca **cantidades acumuladas en cuatro horas**, no tasas. Cada ID de flujo es único. No hay valores predeterminados más allá de los tipos de dato.

El stock `accepted_pending` representa solicitudes **aceptadas** pendientes; los rechazos anteriores a aceptación no pertenecen a él.

Capacidad: `machine_per_hour` (bebidas/h), `machine_period_max` (bebidas posibles en el turno), `material_period_max` (bebidas posibles por insumos), `joint_period_max` (menor de esas cotas), `observed_prepared` (realmente observadas).

`feedback` es una lista de objetos `{"name": "...", "status":"hypothesis|observed", "justification":"..."}`. Si no existe bucle causal probado, escribe `[]`.

`unknowns` debe contener al menos una incertidumbre real.

Usa exactamente las claves indicadas, con números enteros no negativos para cantidades.
