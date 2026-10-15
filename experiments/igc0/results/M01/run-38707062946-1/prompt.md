# IGC-0 · Etapa IG, solo estructura SD (v3)

Analiza exclusivamente el paquete PUBLICO de M01: registros POS, cierres, notas y referencia factible CALIBRADA. Tu tarea es **IDENTIFICAR y GRAFICAR** un modelo mínimo de stocks, pipes, relaciones informativas y fronteras. Otro programa dibujará el JSON que tú propongas. No hagas contraste, decisiones o proyecciones en esta etapa.

Reglas estrictas:
- Un stock conserva UNA entidad: pedidos (`orders`), insumos (`meals_equivalent`) o dinero (`MXN`). Un pipe que incide en un stock debe transportar la misma entidad. **Prohibido** `inventory → cash` o `cash → inventory`; ventas/compras generan flujos físicos y monetarios SEPARADOS ligados con relaciones informativas.
- La capacidad de cocina compartida para presencial/delivery es una restricción que regula pipes, no un stock de dinero ni un flujo. Distingue acumulaciones de pedidos, inventario, caja/cuentas por cobrar, despacho y retardos donde la evidencia lo permita. No copies un diagrama conocido.
- El referente CALIBRADO no demuestra qué mecanismos operan en el mundo virtual. `OBSERVADO`, `CALIBRADO`, `INFERIDO`, `HIPÓTESIS`, `DESCONOCIDO` no son intercambiables. Copia literalmente `source_id` y `sha256`; un dato inicial no sustentado es `null` + `DESCONOCIDO`.
- Separa las conexiones que TRANSPORTAN entidades (pipes) de las que sólo INFORMAN/RESTRINGEN (informational_links). El `from` y `to` de links deben ser IDs que tú hayas declarado de stock o pipe.
- Examina por separado cuatro roles: cocina compartida (`shared_kitchen`), cola de pedidos (`order_backlog`), despacho (`delivery_dispatch`) y liquidación diferida (`payout_delay`). Puedes concluir `unknown` o `hypothesis`: es preferible a afirmar un mecanismo falso. Si lo marcas `represented`, indica IDs que hayas declarado y evidencia pertinente.
- **No confundas** `fulfilled` (cohorte de llegada) con `service_window_completed` (ventana de entrega). No atribuyas causalidad de saturación a cifras agregadas.
- Sé conciso; entrega SOLO un objeto JSON (es posible que la API agregue un único bloque `<think>` previo). **No incluyas campos de contraste ni de decisión**.

Objeto requerido:
{
 "case_id":"M01",
 "stocks":[{"id":"id","unit":"orders|meals_equivalent|MXN","initial":null,"initial_label":"DESCONOCIDO","initial_refs":[]}],
 "pipes":[{"id":"id","from":"state","to":"state","unit_per_time":"orders/hour|meals_equivalent/day|MXN/day","capacity_source":null,"mechanism":"descripción breve","evidence_refs":[],"epistemic":"HIPÓTESIS"}],
 "informational_links":[{"from":"id_stock_o_pipe","to":"id_stock_o_pipe","type":"information","why":"relación no conservativa"}],
 "boundary":{"inside":["proceso"],"outside":["proceso"],"possible_omissions":["incertidumbre"]},
 "mechanism_checks":[
  {"role":"shared_kitchen","status":"unknown|hypothesis|represented","linked_ids":[],"evidence_refs":[],"explanation":"breve"},
  {"role":"order_backlog","status":"unknown|hypothesis|represented","linked_ids":[],"evidence_refs":[],"explanation":"breve"},
  {"role":"delivery_dispatch","status":"unknown|hypothesis|represented","linked_ids":[],"evidence_refs":[],"explanation":"breve"},
  {"role":"payout_delay","status":"unknown|hypothesis|represented","linked_ids":[],"evidence_refs":[],"explanation":"breve"}
 ],
 "unknowns":["información no identificada"]
}

Los valores del esquema son EJEMPLOS, no soluciones. No copies IDs sugeridos como si fueran datos. No inventes números ni mecanismos.
