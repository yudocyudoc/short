# IGC v3 — Fundación molecular

**Estado:** transición técnica, no resultado científico. La [hoja de ruta v3](docs/IGC_SD_HOJA_DE_RUTA_CONSOLIDADA_v3_2026-10-18.md) es la única norma para los siguientes experimentos.

## Historia preservada

- [Archivo principal hasta PR #31](https://github.com/yudocyudoc/short/tree/archive/igc-pre-v3-2026-10-17): commit 75e9706b0761fb0920e1a1bb90171d87b88ad74d.
- [Archivo lateral de evidencia hasta PR #24](https://github.com/yudocyudoc/short/tree/archive/igc-evidence-pre-v3-2026-10-17): commit f10510816701f0853102fbfd12065f4197007079.

Los PR históricos siguen abiertos y no se han fusionado. No son referencias de código aprobadas para nuevos experimentos, pero sí evidencia histórica accesible.

## Fuentes migradas literalmente

- src/modelica/IGCMolecules.mo: clases AcceptedSource, BoundedQueue y DeliveryCounter, originales del experimento del [PR #25](https://github.com/yudocyudoc/short/pull/25), objeto Git 2f83de72d38d0b8f5e866295b806d19067c5194d.
- src/modelica/IGCInformationMolecules.mo: FirstOrderReportFilter, del [PR #29](https://github.com/yudocyudoc/short/pull/29), objeto Git 36d97a7e9de4d7ee80bf884beec6094a9bb1cf98.

La prueba de integridad comprueba ambos objetos por bytes. Son wrappers IGC sobre SystemDynamics/MSL, no la biblioteca original íntegra de Jim Hines.

NO se han migrado los generadores de cuatro variantes, las firmas SYNC/LAG precalculadas, los golds históricos, los guard de #30–31, la selección Gini ni los flujos experimentales anteriores. Continúan disponibles en las ramas archivadas.

## Regresión técnica de la fundación

Para ejecutar pruebas independientes de OpenModelica:

    python -m unittest discover -s foundation -p 'test_*.py' -v

GitHub Actions utiliza OpenModelica 1.26.5, ModelicaStandardLibrary 4.0.0 y SystemDynamics 2.1.2 para simular dos rutas conocidas con las mismas moléculas físicas. La ruta filtrada debe modificar solamente la señal reportada y nunca el flujo físico. Se comprueban stocks, topes, acumulados y comparación de series.

Los controles negativos fuerzan situaciones inválidas para demostrar que el verificador puede rechazar cambios incorrectos.

El único veredicto metodológico permitido por esta fundación es **ENGINEERING_ONLY**. La estructura del fixture es conocida: esto no prueba composición por contratos, identificación de mecanismo, IA, diseño de ensayos o generalización.

## Siguiente trabajo, aún no realizado

E0 — contrato de observabilidad, parámetros, registro molecular y controles antifuga.
E1 — compositor realmente dirigido por registro; reemplazo de registro sin editar el algoritmo y pruebas de canonicidad.
IA-1 — extracción y construcción desde narraciones que no revelen la respuesta, comparando Llama con otros modelos.
E2/E3 — mundos ocultos, predicciones selladas y contrafactuales.

Ni E0 ni E1 se declaran completados por esta migración.

La hoja de ruta en §9 menciona históricamente partir del PR #29. La decisión administrativa posterior es partir de esta rama limpia, migrando solo las fuentes verificadas. Los compromisos y gates de la hoja de ruta no cambian.
