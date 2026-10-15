# C5 — Contrato común de salida JSON tipada (igual para A y B)

Devuelve **un solo objeto JSON** sin explicaciones externas. Usa exactamente:

{
  "stocks":[{"id":"stock_id","unit":"copy|reservation","initial":0,"final":0}],
  "flows":[{"id":"flow_id","entity":"copy|reservation","from":"state_id","to":"state_id","total":0,"unit":"copy|reservation"}],
  "feedback":[],
  "unknowns":["una incertidumbre relevante"]
}

Los números 0 son sólo ejemplos de tipos, no cifras del caso.

Para permitir cotejo reproducible, usa únicamente el siguiente **vocabulario controlado** (no significa que debas incluir todos los candidatos):

- Candidatos a stocks: `available_copies`, `loaned_copies`, `repair_copies` (unidad `copy`); `pending_reservations` (unidad `reservation`); `returned_bin` (unidad `copy`, sólo si realmente permanece inventario allí).
- Estados de frontera (NO stocks): `external`, `retired`, `served`, `canceled`.
- Para transferencias físicas usa `entity:"copy"`, `unit:"copy"`. Para creación, servicio y cancelación de reservas usa `entity:"reservation"`, `unit:"reservation"`.
- Cada flujo lleva total acumulado **en la semana**, nunca una tasa instantánea. `id` puede ser cualquier identificador único.
- Declara el stock final que se pueda deducir mediante flujos; no inventes estados ni movimientos.
- Un servicio de reserva puede corresponder a **uno de los préstamos ya registrados**: no sumes de nuevo ejemplares prestados por haber atendido reservas.
- `feedback`: sólo lista de `{"name":"...","status":"hypothesis|observed","justification":"..."}`; usa `[]` si no hay causalidad endógena demostrada.
- `unknowns`: al menos una incertidumbre sustantiva.

Este contrato delimita tipos y nombres para cotejo; **no te entrega el conjunto de stocks obligatorio, la lista de aristas ni los valores finales**.
