# IGC-0 / M01 — Primera ejecución ciega de DeepSeek

**Registrado antes de la solicitud a Workers AI.** Fecha de experimento: 2026-10-14, Ciudad de México.

## Entrada

Únicamente `experiments/igc0/analyst/output/inputs/M01.json`, regenerado por `src/prepare.py` del ZIP **público**, verificando SHA-256 de los archivos y cada registro.

El proceso del analista no lee `experiments/igc0/generator`, `experiments/igc0/aggregate` ni el ZIP del oráculo del evaluador.

## Configuración

- Modelo: `@cf/deepseek-ai/deepseek-r1-distill-qwen-32b`.
- Modelo definido en `analyst/src/run_llm.py`; exactamente **una** llamada API.
- `temperature=0.1`, `max_tokens=4500`, sin streaming.
- Contrato del analista existente: identificar stocks, pipes y fronteras, grafo tipado, contraste con referencia y limitaciones de identificabilidad.
- `scenario_projections=[]` mientras el SD agregado no esté calibrado.
- Sin revisiones ni intentos automáticos. M01 solamente, M02–M08 permanecen intactos.

## Salidas y adjudicación

Guardar `raw_response.txt` (o JSON nativo), `reasoning.txt` si existe, `proposed_model.json`, `validation.json`, `usage.json` y `diagram.mmd` si el validador acepta.

El validador comprueba **integridad de referencias y estructura tipada**, no equivale a aprobar el diagnóstico causal ni las proyecciones.

Una respuesta incorrecta, no parseable, con afirmaciones infundadas o insuficiente se documentará como resultado sin modificar el prompt ni el verificador tras ver la respuesta. No abrir el oráculo del generador en esta ejecución.

## Costo

Registrar consumo real de tokens y neuronas reportados por Cloudflare. Cualquier cifra USD sería estimada antes de franquicia gratuita, no facturación neta.
