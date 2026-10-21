Devuelve sólo un objeto JSON válido, sin Markdown. No añadas hechos fuera del expediente. Distingue lo reportado, supuestos y derivaciones; soporte no significa verdad ni causalidad. Si falta fundamento, dilo.

Esquema:
{"task_id":"T1|T2|T3","answer":"string","hypothesis_status":[{"id":"CS-01|CS-02","status":"supported|unsupported|unknown","reason":"string"}],"justification_changes":[{"id":"string","status":"survives|invalidated|unknown","evidence_refs":["DOC-01"],"assumption_refs":["A-id"]}],"evidence_refs":["DOC-id"],"assumption_refs":["A-id"],"discriminating_observation":"string","uncertainties_and_limits":["string"],"unsupported_causal_claims":["string"]}

Completa sólo los campos pertinentes. Usa identificadores exactos si están disponibles. No elijas una estructura verdadera si el contexto no lo demuestra.
