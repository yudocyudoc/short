# C4.2 — Resultados verificados

**[Informe con adjudicación](c42-2026-10-13-report.md)**

- [Run A/B Cloudflare](https://github.com/yudocyudoc/short/actions/runs/38511091953): 2 inferencias, sin repeticiones ni reparaciones automáticas.
- [Artefactos originales y certificados](https://github.com/yudocyudoc/short/actions/runs/38511091953/artifacts/11869548969): texto original, razonamiento separado, JSON final sin cambios, validación y costos.
- [Inspección de stocks y aristas a partir de los mismos artefactos](https://github.com/yudocyudoc/short/actions/runs/38511316541): cero inferencias adicionales.

**A:** 9/10 + P11 FAIL (stock de aceptadas pendientes final 5, pero sus propias entradas/salidas implicaban 8). **REJECT**.

**B:** 10/10 + P11 PASS (inventario 30→9, solicitudes aceptadas pendientes 0→8, respaldados por seis flujos tipados). **ACCEPT**.

**40 tests deterministas aprobados**, 20 del verificador previo y 20 nuevos. Ambas respuestas tenían un solo bloque `<think>` seguido de JSON en fence; el separador estricto funcionó en ambas.

**Costo:** 5,113 tokens, 1,124.9833 neuronas, aproximadamente US$0.01237448 antes de franquicia; no es cobro neto confirmado.

**Límite:** un caso sintético ya conocido, una corrida por brazo, regla B ajustada a las fallas anteriores. Éxito local, no demostración de descubrimiento generalizable.
