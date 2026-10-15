# C4.1 — Evaluación registrada antes de las inferencias

**Hipótesis:** JSON Mode nativo eleva la posibilidad de respuesta parseable como JSON sin extracción heurística de texto. La prueba no establece robustez con N=1 por condición.

- Modelo fijo: `@cf/deepseek-ai/deepseek-r1-distill-qwen-32b`.
- Escenario/prompt exactos: `experiments/c4/scenario.md`, `prompts/contract.md`, `prompts/build.md` (idénticos entre modos).
- Orden fijo: `prompt_only` → `json_mode`.
- Parámetros iguales: `temperature=0.1`, `max_tokens=3500`, `stream=false`.
- JSON Mode usa `response_format={"type":"json_object"}`, **no** se añade un esquema nuevo ni se suministra `facts.json`.
- Cada salida se evalúa con `c4_validator.validate_raw`; sin feedback ni reparación.

## Métricas predefinidas

1. `api_success`: si el proveedor acepta la solicitud y devuelve respuesta; `JSON Mode couldn't be met` es un fallo de formato del proveedor.
2. `response_kind`: `text`, `native_object`, `other`.
3. `strict_json_text`: `json.loads(raw)` funciona *directamente* cuando response es texto; no cuenta normalización.
4. `transport_parseable`: JSON puro o con fence externo, según C4; para respuesta nativa objeto se anota `provider_native_object`.
5. `reasoning_markers`: si contiene `<think>`, `</think>` o `reasoning` separado, sin intentar recuperar JSON de razonamientos.
6. `G1_SCHEMA` y puertas `G1–G10` del validador C4 como métrica aparte.
7. `prompt_tokens`, `completion_tokens`, `total_tokens`, `neurons`, y costo estimado antes de cuotas.

**Regla de no reparaciones:** no extraer `{...}` desde prosa, no quitar `<think>`, no cambiar cifras o aristas, ni ejecutar una nueva consulta si un modo falla. Un fallo en JSON Mode no impide documentar la primera corrida.

**Referencia cerrada:** se reutiliza `experiments/c4/evaluation/facts.json` *sólo* en el verificador; el modelo nunca ve ese documento. La puntuación de C4.1 no se fusiona con la de C4 porque se cambió modelo y modo de salida.

**Costos:** usar las tarifas publicadas actuales para DeepSeek R1 Distill Qwen 32B, `$0.497/M` input y `$4.881/M` output, sin confundir estimación con factura.
