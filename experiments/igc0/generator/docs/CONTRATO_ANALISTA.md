# Instrucción para el analista IGC-0 (sin oráculo)

**Tarea:** para cada `public/Mxx/packet.json`, construir un modelo de Dinámica de Sistemas mínimo, una referencia factible y un contraste con la operación simulada bajo `open_full`. Debes trabajar únicamente con el paquete público; no abrir código del generador, semillas, trazas internas ni respuestas del evaluador.

Tu trabajo es **identificar mecanismos, construir el grafo y contrastar**, no inventar series ni usar un LLM como calculadora.

## Salida estructural mínima

```json
{
  "case_id":"Mxx",
  "stocks":[{"id":"...","unit":"...","initial_source_id":"..."}],
  "pipes":[{
    "id":"...","from":"...","to":"...","entity":"...",
    "unit_per_time":"...","capacity_source_id":"...",
    "mechanism":"...","evidence_refs":["POS:D01:pico"]
  }],
  "boundary":{"inside":["..."],"outside":["..."],"possible_omissions":["..."]},
  "contrast":[{
    "pipe_or_mechanism_id":"...","type":"difference|possible_difference|none",
    "evidence_refs":["..."],"epistemic":"OBSERVADO|INFERIDO|HIPÓTESIS|DESCONOCIDO",
    "explanation":"..."
  }],
  "identifiability":{
    "status":"identifiable|non_identifiable|no_material_deviation|insufficient_data",
    "rival_mechanisms":["..."],"discriminating_measurement":"..."
  },
  "actions":["no_delivery","open_full","open_offpeak_capped"],
  "decision":{"choice":"...|abstain","reason":"...","assumptions":["..."]},
  "scenario_projections":[{
    "decision":"open_full","model_run_id":"...","horizon_days":14,
    "metrics":[{"id":"...","value":0,"unit":"...","label":"SIMULADO",
                "source_id":"...","sha256":"..."}]
  }],
  "unknowns":["..."]
}
```

Los elementos son guía de interoperabilidad, no una lista de respuestas. No se exige utilizar exactamente esos IDs de stocks o pipes: propón una ontología mínima suficiente. El diagrama debe derivarse del **mismo JSON** que se pueda ejecutar, no dibujarse por separado.

**Regla de abstención:** una disminución de pedidos completados no identifica por sí sola una causa única. Cuando dos mecanismos rivales producen las mismas observaciones disponibles, declara `non_identifiable` y solicita el indicador que los separa. No elijas una causa sólo porque su historia resulte verosímil.

**Regla de frontera:** puedes proponer ampliar el modelo ideal si un proceso exterior cambia materialmente una decisión; no fuerces toda discrepancia en un coeficiente residual.

**Regla de proyección:** si no cuentas todavía con un simulador agregado calibrado con parámetros suficientes, **no inventes trayectorias numéricas**. Entrega estructura, intervención, relaciones esperadas y los datos/parámetros que faltan. Declararlo es válido, no un fracaso.

El objeto anterior será validado posteriormente por fuente, unidad, identidad de los pipes y coherencia interna. La calificación final no será un simple conteo de puertas.
