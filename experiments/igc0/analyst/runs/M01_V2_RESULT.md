# IGC-0 / M01 v2 — Contrato reforzado y segunda inferencia DeepSeek

**Fecha:** 2026-10-14 (México) / 2026-10-15 UTC.  
**Estado:** segunda y única inferencia v2 ejecutada; **FORMAT_REJECT**. El modelo SD NO se adjudicó. Esta prueba es ADAPTATIVA después de ver M01 v1.

## Evidencia original e integridad

- [Protocolo previo](M01_V2_PROTOCOL.md) y [contrato v2](../prompts/igc_v2.md) (versionados antes de la llamada).
- [GitHub Actions #38683795266](https://github.com/yudocyudoc/short/actions/runs/38683795266), una llamada a DeepSeek y 36 tests previos PASS.
- [Originales y dictámenes](https://github.com/yudocyudoc/short/actions/runs/38683795266/artifacts/11949761238): respuesta cruda, razonamiento separado, entrada M01, prompt exacto, hashes y uso.
- [Diagnóstico de transporte sin otra inferencia](https://github.com/yudocyudoc/short/actions/runs/38684049858) · [artefacto](https://github.com/yudocyudoc/short/actions/runs/38684049858/artifacts/11949731529).

El input original canónico M01 SHA-256 se mantuvo idéntico a v1:
`3ede7ef04e172c04f9ab5564c57bc1b1e5d88ba63c19b76660e9941f13dec6df`.
Nuevo prompt v2 SHA-256:
`97dc09142e0764044d16452da9c59776c1940d6d200acc5288b9a6e5243d701c`.

## Contrato nuevo

Se añadió distinción entre pipes físicos, de pedidos y financieros, conexiones informativas separadas, revisión explícita de cuatro mecanismos (cocina compartida, cola, despacho, retardo de liquidación), fuentes/etiquetas epistemológicas y contraste mínimo con la referencia. El validador v2 independiente `analyst/src/semantic_audit_v2.py` comprueba cobertura y enlaces, fuentes, unidades compatibles y ausencia de proyecciones no calibradas. El código NO rellena ni repara JSON.

**36 pruebas automatizadas previas PASS**: 9 ingestión original, 10 controles semánticos v1 y 17 controles semánticos v2.

## Resultado

| Campo | v1 | v2 |
|---|---|---|
| Contrato | IGC preliminar | IGC reforzado; nuevos mecanismos explícitos |
| Respuesta JSON parseable | Sí (think + fence) | **No** |
| Validador técnico original | ACCEPT (falso positivo para IGC) | **REJECT** (sin JSON completo) |
| Auditor semántico | REJECT post hoc, nueve incumplimientos | **No evaluable por formato** |
| Comparación de mecanismos | Sin contraste | No evaluable |
| Inferencias | 1 | **1**, sin reintentos |
| Proyecciones | Ninguna | Ninguna |

La inspección automatizada de la respuesta cruda v2, realizada **después** de la inferencia pero sin nuevas consultas, encontró:
- texto de respuesta 7,145 caracteres;
- un bloque `<think>…</think>` **completo**;
- 2,751 caracteres posteriores a `</think>`, con un fence JSON abierto pero **sin cierre** ni llave final;
- formato reportado `invalid_json`, no extractable sin reparar o modificar contenido;
- respuesta del proveedor: **18,760 tokens entrada, 2,148 salida, 20,908 total, 1,800.5762 neuronas**.
- USD estimado antes de franquicia: **0.01980811** con tarifa previa de DeepSeek ($0.497/M entrada, $4.881/M salida), no facturación real.
- La salida de 2,148 tokens es menor al máximo solicitado de 4,500; **no se conoce la razón de la finalización incompleta**, ni se registró un finish_reason suficiente para atribuir el fallo a Cloudflare.

**Juicio:** infraestructura y fuentes públicas correctas; en M01 v2, la prueba no alcanzó la evaluación SD por formato. No es posible afirmar mejora o empeoramiento semántico entre v1 y v2. Sólo se puede afirmar que el segundo contrato y su carga condujeron a un JSON incompleto en esta muestra.

## Límite y siguiente diseño, sin ejecución nueva

No cambiar retroactivamente salida ni formato. Mantener M01 v1 y v2 como artefactos inmutables.

Antes de otra inferencia, separar la tarea en fases con contratos pequeños: (a) proponer grafo dimensionalmente correcto con citas; (b) contrastarlo con referencia y considerar rivales. Cada fase requeriría validación e historial, evitando pedir a un modelo de razonamiento que devuelva simultáneamente un JSON voluminoso sobre 18,760 tokens de contexto. Otra opción es salida estructurada del proveedor, pero debe verificarse con este modelo.

**No ejecutar M02–M08 ni habilitar escenarios hasta que el sistema IGC pueda validar la estructura del primero.** No se abrió el oráculo ni se tocó el simulador SD no calibrado.
