# IGC-0 M01 · Protocolo de separación I/G → C

**Registrado antes de cualquier nueva inferencia v3.** Estudio adaptativo sobre M01 tras fallas de v1 (grafo semánticamente erróneo) y v2 (JSON truncado); NO prueba confirmatoria independiente.

## Diseño

Etapa IG: **una** inferencia DeepSeek `@cf/deepseek-ai/deepseek-r1-distill-qwen-32b` sobre los mismos datos públicos M01; devuelve solo stocks, pipes, links, frontera, roles y límites. El verificador tipado revisa dimensión de pipes, citas y etiquetas, estructura válida del grafo y vinculación de mecanismos. El diagrama Mermaid se renderiza por código sólo si hay grafo válido.

**Puerta determinista:** si IG no entrega JSON íntegro, o falla alguna compuerta estructural, **C NO se ejecuta**, sin reintentos ni reparación. Los errores del validador se registran en disco y no se envían de vuelta al LLM.

Etapa C: **máximo una** inferencia adicional sobre el mismo paquete público MÁS el grafo validado, congelado y su hash. Solo emite contrastes con referencias, identifiabilidad, acciones permitidas y abstención. Ninguna modificación al grafo. El verificador comprueba hash del grafo, referencias, ID contrastado, y consistencia epistemológica; también revalida el modelo combinado con `igc.validate_model` y `semantic_audit_v2.audit_v2`.

## Controles

- Datos M01 inmutables: 42 filas POS, 14 cierres, SHA-256 del input canónico `3ede7ef04e172c04f9ab5564c57bc1b1e5d88ba63c19b76660e9941f13dec6df`.
- Orden fijo: **IG → (puerta) → C**; `temperature=0.1`, máximo `4500` tokens de salida por llamada, `stream=false`.
- Máximo **2 llamadas**, sin feedback ni retries automáticos.
- No usar el oráculo, código de generador, ni corridas contrafactuales no calibradas en inferencias. El simulador SD agregado no está autorizado para proyectar cifras.
- Conservar texto crudo y respuesta del proveedor, token/neuronas, formato, hashes de prompt/input/grafo, validación intermedia, modelo combinado y resultado. No borrar el historial de v1/v2.
- **Éxito de contrato** = IG aceptado Y C aceptado. Éxito técnico/semántico no es prueba de identificación causal ni de predicción.

## Limitaciones

Un solo mundo, mismo modelo y contrato diseñado después de observar errores anteriores. La terminación prematura o timeout cuenta como fallo, no se repara. Los enlaces y los roles no constituyen evidencia suficiente de que la cocina compartida exista de hecho en el mundo virtual.
