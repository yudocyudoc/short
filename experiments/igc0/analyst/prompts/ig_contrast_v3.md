# IGC-0 · Etapa C, solo contraste (v3)

Recibirás: (1) observaciones públicas del mismo M01, (2) un grafo SD **congelado y previamente aceptado por validación estructural**, y (3) su SHA-256. **No cambies, completes ni reconstruyas stocks, pipes, unidades o relaciones del grafo**. El modelo aceptado es una representación candidata, NO verdad causal.

Tu tarea exclusiva es CONTRASTAR la operación observada con la referencia factible CALIBRADA: qué divergencias se sostienen, cuáles sólo son plausibles, qué no es identificable. Distingue `fulfilled` por cohorte de llegada de `service_window_completed` por ventana de servicio. No atribuyas los cuellos de botella sin separar cocina, despacho, demanda y pagos.

Exige al menos un contraste que señale un ID existente del grafo, una comparación explícita OBSERVADO vs CALIBRADO, fuentes textuales reales `source_id`/`sha256`, y límites de interpretación. Si no se identifica causalmente, `type:"possible_difference"`, `epistemic:"HIPÓTESIS"`. Reserva `none` para evidencia positiva de ausencia de diferencia; no uses `none` para falta de datos.

Al existir mecanismos rivales compatibles con la misma evidencia, usa `non_identifiable`, lista dos rivales y propone medición discriminante; si faltan magnitudes fundamentales, `insufficient_data`. `unknowns` debe explicar qué no conocemos. No tomes una decisión contrafactual con un simulador agregado no calibrado: `decision.choice:"abstain"`, `scenario_projections:[]`. Sin números futuros.

Entrega SOLO:
{
 "case_id":"M01",
 "graph_sha256":"HASH_EXACTO_RECIBIDO",
 "contrast":[{"pipe_or_mechanism_id":"ID_EXISTENTE_EN_GRAFO","type":"possible_difference","evidence_refs":[{"source_id":"ID_REAL","sha256":"HASH_REAL"}],"epistemic":"HIPÓTESIS","explanation":"comparación entre observado y referencia, y límites"}],
 "identifiability":{"status":"insufficient_data","rival_mechanisms":[],"discriminating_measurement":"medición discriminante"},
 "actions":["no_delivery","open_full","open_offpeak_capped"],
 "decision":{"choice":"abstain","reason":"no hay simulador calibrado","assumptions":[]},
 "scenario_projections":[],
 "unknowns":["evidencia insuficiente identificada"]
}
El esquema contiene marcadores de tipos, NO resultados. Copia el hash exacto y las referencias exactas. No agregues stocks ni pipes ni relaciones.
