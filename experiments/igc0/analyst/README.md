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
