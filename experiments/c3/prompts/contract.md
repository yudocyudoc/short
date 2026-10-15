# C3 — Contrato de salida (idéntico para A y B)

Devuelve **exclusivamente un objeto JSON válido**, sin Markdown, comentarios, texto explicativo ni bloques con tres comillas. El JSON tiene esta estructura:

{
  "horizon_hours": <numero>,
  "stocks": [
    {"id": "<identificador>", "unit": "<unidad>", "initial": <numero>, "final": <numero>}
  ],
  "flows": [
    {"id": "<identificador>", "entity": "<request|material>", "from": "<estado>", "to": "<estado>", "total": <numero>, "unit": "<unidad>"}
  ],
  "capacity": {
    "machine_per_hour": <numero>, "machine_period_max": <numero>,
    "material_period_max": <numero>, "joint_period_max": <numero>,
    "observed_prepared": <numero>
  },
  "feedback": [
    {"name":"<nombre>", "status":"hypothesis|observed", "justification":"<sustento>"}
  ],
  "unknowns": ["<incertidumbre>"]
}

**Vocabulario de interfaz para que el resultado sea verificable:**

- Stocks candidatas: `inventory` (unidad `beverage_equivalent`), `accepted_pending` (unidad `request`), `prepared_stock` (unidad `beverage`). Incluye solamente stocks que tienen sentido como acumulaciones en el escenario.
- Las transiciones de solicitudes usan `entity:"request"`, `unit:"request"` y estados de `external`, `submitted`, `accepted_pending`, `rejected`, `canceled`, `fulfilled`. Decide cuáles flujos hacen falta y sus conexiones. `external` es la frontera, `submitted` un punto de clasificación, no un stock físico obligatorio.
- Los flujos de insumos usan `entity:"material"`, `unit:"beverage_equivalent"`. Se dispone de `inventory` y `consumed` como origen y destino posibles.
- En `flows.total` escribe el total acumulado **durante el turno**, no una tasa por hora. No presupongas flujos uniformes en el tiempo.
- Usa identificadores de flujo únicos de tu elección. Un flujo debe conectar origen y destino sin alterar la naturaleza de la entidad transportada.
- `capacity` separa límites potenciales y producción realmente observada.
- Si no hay evidencia de bucles reales, usa `feedback: []`, o marca sólo bucles candidatos como `hypothesis`. No fabriques observaciones.
- Declara al menos una incertidumbre real en `unknowns`.

Estos campos permiten revisar el modelo, pero **no contienen sus valores de solución**. Cada brazo debe inferir las conexiones y cantidades desde el escenario.
