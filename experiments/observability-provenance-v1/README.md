# IGC — Observabilidad, procedencia y poda conservadora (v1)

Fecha: 2026-10-17. Estado: experimento sintético sin fusionar. Base: PR #29, rama experiment/igc-transit-report-observability-v1.

## Pregunta

¿Puede un sistema descartar arquitecturas con señales realmente disponibles sin confundir documentos, amplitud y retardo temporal?

Se reutilizan cuatro grafos (Direct, TransitOnly, ReportOnly y TransitAndReport), dos moléculas y ocho simulaciones reales OpenModelica del experimento anterior. No se añade ninguna molécula.

## Semántica de evidencia

- SIMULADO: todas las tasas provienen de un mundo sintético OpenModelica; no son datos OBSERVADOS de una organización.
- DOCUMENT_UNVERIFIED: manual o declaración contextual; no elimina modelos por sí solo.
- AVAILABLE: serie sintética efectivamente expuesta en el expediente, aunque el generador conozca todas.
- UNKNOWN: faltan señales o son incompatibles unidades, grilla temporal o fuentes.
- SYNC: tasas muestreadas iguales con tolerancia absoluta 1e-6.
- DISTINCT: tasas muestreadas diferentes. **No autoriza el diagnóstico LAG:** diferencias de forma, amplitud y tiempo pueden producir DISTINCT.

Las mediciones usan tres canales distintos de manera declarativa: ERP_EXPORT, RECEIVER_SCAN y DASHBOARD. Esto no demuestra independencia real en una empresa. Ninguna conclusión de estas simulaciones debe etiquetarse OBSERVADO en el sentido CEI.

## Campaña

Doce expedientes congelados en cases.json. La arquitectura generadora para evaluación está en truth.json, separado del paquete enviado a Llama. Cada caso expone un subconjunto de tres señales: despacho, recepción física, tasa del tablero. Algunos contienen documentos contradictorios; uno declara una unidad incompatible.

El guard extrae comparaciones de los CSV OpenModelica tras aplicar las máscaras de disponibilidad. Sólo estas comparaciones validadas podan el catálogo. Cuando hay más de una arquitectura, propone una observación adicional, considerando compatibilidad con las firmas conocidas, canales obtenibles y costo relativo.

Como comparación A/B, Llama recibe las mismas mediciones resumidas, la misma disponibilidad y documentos, sin curvas ocultas ni truth.json. Sus respuestas originales y la poda que producirían se archivan. La interpretación del LLM nunca constituye medición por sí misma. Si las credenciales Cloudflare no están disponibles, la evaluación de Llama queda NOT_RUN y se preserva la evaluación determinista.

## Métricas separadas

1. Falsos descartes de la arquitectura verdadera (meta 0/12 para el guard).
2. Modelos supervivientes por expediente y abstención cuando faltan mediciones.
3. Propuestas de medición factibles según presupuesto relativo.
4. Si se ejecuta Llama, respuestas admitidas, falsos descartes frente a guard y tamaño de los conjuntos supervivientes en los mismos casos.
5. Integridad de series y compatibilidad dimensional; nunca equiparar DISTINCT con retardo demostrado.

## Ejecución

El workflow está en .github/workflows/igc-observability-provenance-v1.yml y utiliza OpenModelica 1.26.5, ModelicaStandardLibrary 4.0.0, SystemDynamics 2.1.2, Python 3.11 y el Llama del PR #29 cuando hay secretos.

Prueba local: python -m unittest discover -s experiments/observability-provenance-v1 -p 'test_*.py' -v

Con los CSV del experimento dual: python experiments/observability-provenance-v1/observability.py --series experiments/dual-mechanism-v1/output --probes experiments/dual-mechanism-v1/output/probe_signatures.json --out experiments/observability-provenance-v1/output

Archivos de salida: measurement_results.json, measurement_score.json, critic_inputs_no_truth.json y, cuando se ejecuta la crítica real, llama_cases.json, llama_score.json y respuestas originales. El workflow guarda artefactos durante 90 días.

## Lo que esta prueba NO valida

Las doce viñetas fueron diseñadas dentro del proyecto. No son una muestra independiente de empresas, ni estiman rendimiento estadístico. Un modelo que produce curvas similares o pertenece al conjunto compatible no es por ello una estructura causal verdadera. La igualdad observacional no asegura equivalencia estructural. Los costos de instrumentación son ordinales ilustrativos, no presupuestos empresariales. El linter del PR #29 verifica IDs y formato, pero no el soporte semántico de cada afirmación.

**Criterio de avance:** si hay pocos falsos descartes y las sugerencias reducen incertidumbre con datos viables, llevar el procedimiento a un caso empresarial controlado. Si el guard no aporta valor frente a la línea base o exige más trabajo que la decisión, simplificarlo. No alterar resultados históricos de PR #28/#29.
