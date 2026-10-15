# IGC-0 · Analista mínimo v0.1

**Estado: estructura y procedencia comprobadas; modelador LLM aún NO ejecutado; simulador SD agregado todavía NO calibrado.** 14 de octubre de 2026.

## Pregunta

Comprobar si un LLM, ayudado por herramientas deterministas, puede **Identificar → Graficar → Contrastar (IGC)** y proyectar decisiones sobre «¿abrir delivery con la cocina actual?». El mundo virtual verdadero está oculto al analista. La referencia factible es **CALIBRADA**, no un óptimo.

## Material separado

- **Paquete del analista:** este ZIP, con `inputs/IGC0_8_mundos_analista.zip`, `output/inputs/M01...M08.json`, scripts de ingestión/validador y esquemas de referencia. Nunca necesita el oráculo.
- **Simulación agregada experimental:** ZIP separado, **no introducirlo en el prompt del LLM**, porque sus salidas y errores podrían contaminar la evaluación. Sus discrepancias sirven a los desarrolladores para decidir si vale la pena proyectar.
- **Oráculo reservado:** `IGC0_oraculo_evaluador.zip`, existente en conversación anterior. No se abre aquí.

## Componentes

| Script | Función | Estado |
|---|---|---|
| `src/prepare.py` | Verifica SHA-256 de paquete, 336 filas POS y 112 cierres, identifica fuentes y genera entradas limpias | Ejecutado para 8 mundos |
| `src/igc.py` | Genera un **grafo de referencia técnico predefinido**, lo valida por tipos y citas y lo dibuja desde el mismo objeto JSON | 8 grafos generados; **no son hallazgo del LLM** |
| `src/run_llm.py` | Interfaz opcional con DeepSeek R1 en Cloudflare, 1 llamada por mundo, respuesta cruda + evaluación y sin reparaciones | Implementado, **no ejecutado** (no hay credenciales locales de Cloudflare) |
| `src/aggregate_sd.py` | Aproximación SD independiente por 2h con stocks, cocina compartida, despacho, inventario, cuentas por cobrar y caja | Ejecutado; **no apto aún para decidir** |
| `tests/test_ingest.py` | Tests de conservación de evidencia, citas, trazabilidad y rechazo de pronósticos sin procedencia | 9 PASS |

## Cómo ejecutar

Requiere Python 3.10+ sin dependencias externas:

```bash
python -m unittest discover -s tests -v
python src/prepare.py --public-zip inputs/IGC0_8_mundos_analista.zip --out output
python src/igc.py --inputs output/inputs --out output
```

Para experimentar opcionalmente con **un único LLM sin oráculo**:

```bash
# Primero configurar variables de entorno CLOUDFLARE_ACCOUNT_ID y CLOUDFLARE_API_TOKEN
python src/run_llm.py --inputs output/inputs --out output/llm --case M01
```

No hay llamadas automáticas al LLM; se necesita credencial de usuario. Después de generar respuestas, conservar originales sin editar y fijar hashes **antes** de abrir el oráculo.

Para probar el SD agregado en desarrollo:

```bash
python src/aggregate_sd.py --inputs output/inputs --out output/experimental
```

**No** utilizar las salidas `experimental/` como proyecciones aceptadas ni decisiones: faltan modelos operativos virtuales calibrados, tiempos individuales y eventos que separen mecanismos rivales.

## Contrato epistemológico

- `OBSERVADO` refiere sólo al mundo simulado y al paquete POS original, nunca datos de una empresa real.
- `CALIBRADO` refiere a parámetros de referencia, no a parámetros verdaderos del virtual.
- `INFERIDO` es una derivación con fuentes y unidad.
- `HIPÓTESIS` denota mecanismos candidatos.
- `DESCONOCIDO` detiene inferencias no respaldadas.
- `SIMULADO` requiere modelo/política/horizonte/parámetros/condiciones iniciales/hash. No implica precisión ni validación empírica.

El `.mmd` es sólo una vista del grafo tipado. La parte «G» consiste en **proponer correctamente el grafo**, no en que el modelo produzca un dibujo artístico.

## Advertencias importantes

1. `fulfilled` por cohorte de llegada no es `service_window_completed`; nunca medir el cuello de botella como si fueran iguales.
2. Los dos mundos observacionalmente equivalentes no pueden discriminarse sin nuevos datos; no se debe usar el archivo reservado del evaluador para ayudar al modelo.
3. El grafo base es ingeniería predefinida: debe compararse con un LLM real y una línea base convencional, **no contabilizarse como éxito de IGC**.
4. La discrepancia observada contra el prototipo SD agregado es grande (por ejemplo >46 mil MXN en caja M06; M01 se redujo a 701.4 MXN tras eliminar un doble cobro del propio motor); un motor que compila no basta para proyectar decisiones.
5. Ningún resultado de este paquete constituye todavía una validación de IGC ni una predicción comercial.


## DeepSeek IGC-0 / M01: dos intentos registrados

- [v1: informe](runs/M01_RESULT.md) y [respuesta original](https://github.com/yudocyudoc/short/actions/runs/38682204680): JSON válido; el validador de fuentes aceptó un grafo inválido en semántica SD (tres stocks, cuatro pipes, cero contrastes). Auditoría posterior rechazó nueve incumplimientos de procedencia, dimensiones y contraste.
- [Contrato v2](prompts/igc_v2.md), [protocolo previo](runs/M01_V2_PROTOCOL.md) e [informe v2](runs/M01_V2_RESULT.md): 36 tests previos PASS; una sola llamada DeepSeek, JSON final incompleto (`FORMAT_REJECT`). La auditoría v2 **no pudo evaluar semántica** porque no existía un objeto JSON completo.
- [Respuesta v2 y diagnósticos](https://github.com/yudocyudoc/short/actions/runs/38683795266/artifacts/11949761238); [inspección no-inferencial](https://github.com/yudocyudoc/short/actions/runs/38684049858).
- Nuevo auditor `src/semantic_audit_v2.py` y 17 pruebas de regresión `tests/test_semantic_audit_v2.py`; no se reemplazan los resultados de v1.

**No hay validación IGC completa aún.** Las inferencias están manuales, no se abrió el oráculo y el simulador agregado sigue no calibrado. Un siguiente experimento podría separar construcción de grafo y contraste en fases pequeñas, con contratos y trazabilidad, sin asumir que M01 fue comprendido.


## M01 v3 — I/G → compuerta → C (ejecutado)

- [Protocolo previo](runs/M01_IGC_SPLIT_PROTOCOL.md); [informe verificado](runs/M01_SPLIT_RESULT.md).
- Nuevo runner `src/run_split_igc.py`: I/G (identificar/graficar) solicita exclusivamente el grafo, `src/igc_split_gate.py` audita dimensiones, fuentes, tipos y conexiones. **C sólo puede ejecutarse cuando el grafo sea aceptado**; entonces se le entrega ese grafo con hash, y el contrato C es separado.
- [GitHub Actions](https://github.com/yudocyudoc/short/actions/runs/38684669725): **60 pruebas del analista PASS**, una llamada real a DeepSeek, salida I/G JSON parseable pero **REJECT** por falta de stock de pedidos y enlace informativo a un nodo inexistente. Etapa C **correctamente no ejecutada**.
- [Originales y diagnóstico del grafo](https://github.com/yudocyudoc/short/actions/runs/38684669725/artifacts/11949757660); [inspección sin IA adicional](https://github.com/yudocyudoc/short/actions/runs/38684843230).
- **Resultado de investigación:** la separación/gating funciona; la capacidad IGC de identificar/graficar sigue sin demostrarse. No se hicieron proyecciones ni se abrió el oráculo. El workflow de inferencia quedó **manual-only**.
