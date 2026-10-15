# IGC-0 M01 v2 · Protocolo antes de la nueva inferencia

Este experimento es **adaptativo**: v1 ya fue observado. No cuenta como réplica independiente ni demuestra transferencia a otros mundos.

- Entrada: mismo paquete público M01, con 42 filas POS y 14 cierres diarios; mantener SHA de fuente e integridad.
- Modelo: @cf/deepseek-ai/deepseek-r1-distill-qwen-32b, temperatura 0.1, max_tokens 4500, stream false.
- Cambio deliberado: nuevo prompt del analista en prompts/igc_v2.md. No acceso a generador, simulador agregado no calibrado u oráculo. Un máximo de **una** llamada, sin feedback, reintento ni reparación automática.
- Criterio FORMAT: JSON extraído de un bloque final, con separación estricta <think> si existe.
- Criterio SOURCE: el validador original verifica existencia de pares source_id/sha256.
- Criterio SEMANTIC_V2: el auditor deberá comprobar familias dimensionales compatibles, observaciones citadas y tipo epistemológico coherente; contraste explícito, vinculado a una entidad del grafo y con alguna evidencia pública; cuatro roles considerados (cocina compartida, cola de órdenes, despacho y liquidación), pudiendo reconocer lo desconocido en lugar de inventarlo; ausencia de proyecciones y de decisión operativa sin modelo calibrado.
- Criterio IGC_CONTRACT_ACCEPT: FORMAT + SOURCE + SEMANTIC_V2. Incluso ACCEPT sólo significa cumplimiento del contrato, no validez causal o predictiva.
- Registrar stocks, pipes, fuentes, contrastes, mecanismos representados/desconocidos, incertidumbres, rechazo y consumo por llamada. Comparar con v1 sólo descriptivamente.
- Pruebas negativas automatizadas deben pasar antes de invocar Cloudflare. Guardar originales, prompt exacto y SHA256. No modificar respuestas originales ni cambiar validador después de la inferencia.

Los resultados históricos v1, incluida su aceptación técnica original y rechazo semántico posterior, permanecen inalterados.
