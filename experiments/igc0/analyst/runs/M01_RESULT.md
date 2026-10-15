# IGC-0 / M01 — Primera conexión y evaluación de DeepSeek-R1

**Ejecución:** 2026-10-14 (México) / 2026-10-15 (UTC).  
**Estado:** se ejecutó una inferencia ciega con datos públicos, se congeló la respuesta y posteriormente se realizó una auditoría semántica no preregistrada, sin nuevas inferencias.

- [Run original GitHub Actions #38682204680](https://github.com/yudocyudoc/short/actions/runs/38682204680)
- [Artefacto original íntegro: entrada, respuesta, razonamiento separado, JSON, validación y uso](https://github.com/yudocyudoc/short/actions/runs/38682204680/artifacts/11949086072)
- [Inspección posterior sin Cloudflare: #38682600443](https://github.com/yudocyudoc/short/actions/runs/38682600443)
- [Artefacto diagnóstico semántico](https://github.com/yudocyudoc/short/actions/runs/38682600443/artifacts/11948448972)

## Condiciones originales

El script `analyst/src/run_llm.py` construyó una petición con **únicamente** los datos públicos verificados de `output/inputs/M01.json` (42 filas POS y 14 cierres), más el prompt IGC público. Sin oráculo, sin generador, sin agregado no calibrado y sin reintentos.

- Modelo `@cf/deepseek-ai/deepseek-r1-distill-qwen-32b` por Cloudflare Workers AI
- `temperature=0.1`, `max_tokens=4500`, `stream=false`
- SHA-256 entrada canónica: `3ede7ef04e172c04f9ab5564c57bc1b1e5d88ba63c19b76660e9941f13dec6df`
- SHA-256 prompt: `39539b7da5d2a1334ca4edfe334a86312d72490b8264ba277a6d825f3b9eba05`
- 18,027 tokens de entrada, 1,023 de salida, **19,050** en total; **1,268.2407** neuronas reportadas
- Costo estimado con tarifa de experimentos anteriores (DeepSeek R1 Distill Qwen 32B US$0.497/M input, US$4.881/M output): aprox. **US$0.01395** antes de franquicia; no es factura.

## Resultado primario, sin modificaciones retroactivas

**`validate_model`: accepted=true**, salida con un bloque `<think>…</think>` y JSON final en fence.

- Stocks: **3** (`cash`, `inventory`, `receivables`).
- Pipes: **4** (`sales`, `costs`, `receivables_collection`, `supplier_payments`).
- Contrastes modelo virtual ↔ referencia factible: **0**.
- Proyecciones: **0** (correcto abstenerse de simulación numérica sin calibración).
- Decisión: `abstain`.
- Identificabilidad: `identifiable`, pero sin contrastes ni mecanismos rivales documentados.
- Incertidumbres: lista vacía.

El validador inicial comprueba estructura y existencia de referencias citadas, **pero no que las afirmaciones tipo OBSERVADO tengan citas, ni coherencia dimensional entre stocks y pipes, ni presencia obligatoria de contraste**. Por eso el veredicto original `accepted=true` fue un **falso positivo respecto del objetivo IGC**, no una demostración de cumplimiento.

## Auditoría semántica posterior, independiente y NO preregistrada

Se añadió `analyst/src/semantic_audit.py` después de observar el primer modelo, por lo cual su resultado **no debe reemplazar la puntuación original**. Se ejecutó únicamente sobre los archivos ya guardados, sin volver a consultar a DeepSeek.

**Resultado: REJECT, 9 incumplimientos**:
- **3** conexiones directas entre stocks de dominios incompatibles: `inventory→cash` (comidas a dinero) y `cash→inventory` en `costs` y `supplier_payments`. Las conversiones económicas requieren mecanismos separados y no son conservación física directa.
- **4** pipes marcados OBSERVADO carecen completamente de citas de evidencia.
- **1** stock de cuentas por cobrar tiene valor inicial 0, etiquetado OBSERVADO, sin referencia.
- **1** falta total del contraste (`contrast=[]`) que es parte esencial de IGC.

**Validación de código:** 9 tests del módulo original y 10 nuevos tests de salvaguardas semánticas pasaron en CI, antes de adjudicar el artefacto congelado con las nuevas reglas.

## Decisión de investigación

**Conexión y transporte: verificados. Identificación/grafo SD y contraste sustantivo: NO VALIDADOS.**

No desplegar recomendaciones de delivery con esta salida. No ejecutar M02–M08 automáticamente. Antes de una nueva inferencia, requerir al menos evidencia para cada afirmación observacional, coherencia dimensional, presencia explícita de contraste, y revisión sustantiva que pueda detectar omisiones de cocina compartida y colas. La auditoría nueva detecta algunos errores, **no sustituye una adjudicación independiente de modelación SD**.

Los archivos crudos permanecen en el artefacto GitHub Actions; esta nota y el auditor están versionados en el repositorio. El oráculo de los ocho mundos **permanece fuera del repositorio**.
