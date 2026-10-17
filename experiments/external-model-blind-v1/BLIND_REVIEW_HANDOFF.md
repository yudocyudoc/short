# IGC — paquete para adjudicación ciega independiente (NO contiene predicciones Llama)

**Estado:** solicitud de revisión, no benchmark validado. No etiquetar a partir de los outputs de GLM; sus etiquetas deben permanecer ocultas al adjudicador.

## Material de entrada — únicamente Qwen, antes de cualquier Llama

- Corpus original: [run #38995455018, artifact #12086714733](https://github.com/yudocyudoc/short/actions/runs/38995455018/artifacts/12086714733). Abrir `generated_cases.json` para leer las **16 viñetas que pasaron el parser original**.
- Huella SHA-256 del archivo original `generated_cases.json`: `b296c42fe129e59bffa158a2bec771b36d39e21e5ddbc7424c0734ac5cf122c9`.
- Catálogo fijo: [catalog_public.json del PR #21](https://github.com/yudocyudoc/short/blob/experiment/igc-evidence-molecules-pilot-v1/experiments/evidence-molecules-pilot-v1/catalog_public.json). Cuatro alternativas: CAP_UTIL, BACKLOG_FLOW, MATERIAL_DELAY, MTO_S2_PATTERN.

**No abrir** `proxy_reference.json`, `status.json`, `reviewer/`, respuestas originales de GLM, score del PR #23 ni salidas Llama del PR #21 mientras se realice la adjudicación. El adjudicador deberá conocer únicamente los hechos externos y los contratos del catálogo.

## Instrucción para el revisor externo

Debes evaluar exclusivamente las afirmaciones cualitativas de cada caso. No rellenes cifras y no generes ecuaciones. Para cada una de las cuatro moléculas determina si se cumplen **todos** sus requisitos funcionales, y cuáles de sus exclusiones aplican. Una coincidencia terminológica no implica correspondencia causal.

Separa con cuidado:

- trabajo *todavía sin preparar* de pedidos *ya terminados y pendientes de despacho*;
- retardo por transporte/almacenamiento físico de una demora en decisión administrativa;
- producción deseada y capacidad industrial de servicio/citas o contratación de trabajadores;
- falta de evidencia de estructura de una contradicción efectiva;
- respaldo de una **molécula completa** de respaldo de sólo un fragmento de su función.

**No exijas mediciones numéricas para elegir una estructura:** los valores están fuera de la tarea del LLM deliberadamente. Tampoco interpretes una cita textual presente como justificación automática de la molécula.

Para cada caso emite:

~~~json
{
  "case_id": "X02",
  "verdict": "DETERMINATE | NO_MATCH | CONTRADICTORY | INSUFFICIENT_EVIDENCE",
  "molecules": ["BACKLOG_FLOW"],
  "support": [
    {"target":"BACKLOG_FLOW","fact_id":"F1","quote":"cita literal exacta","reason":"mecanismo que soporta"}
  ],
  "counterevidence": [
    {"molecule":"CAP_UTIL","fact_id":"F3","quote":"cita literal exacta","reason":"requisito negado o ausente"}
  ],
  "uncertainties": ["Indica únicamente incógnitas de estructura, no ausencia genérica de cifras"],
  "reviewer_confidence": "HIGH | MEDIUM | LOW"
}
~~~

Las etiquetas `NO_MATCH`, `CONTRADICTORY` e `INSUFFICIENT_EVIDENCE` **no deben agruparse ni adjudicarse como COMPOSE**, y requieren justificación. `DETERMINATE` puede seleccionar varias moléculas sin afirmar que sus conectores Modelica son compatibles. Toda cita debe existir literalmente en el hecho y sostener causalmente el mecanismo.

## Integridad y evaluación posterior

- Prohibido ver las respuestas Llama antes de fechar, firmar y congelar esta adjudicación.
- Documentar identidad del revisor, versión de modelo si es IA, fecha, procedimiento, posibles diferencias y conflictos.
- No ajustar prompts B/C del PR #21, regex ni catálogo tras ver etiquetas nuevas.
- Si el adjudicador no puede distinguir confiablemente moléculas de textos ambiguos, **no atribuirle verdad**: registrar `INSUFFICIENT_EVIDENCE` y, si es posible, revisar por otra persona.
- Sólo comparar B/C después de convertir y congelar las decisiones de revisión con evidencia positiva y negativa.

**El experimento v1/v1.1 de árbitro automático terminó sin score Llama.** Este paquete prepara una revisión independiente de verdad, no sustituye la revisión.
