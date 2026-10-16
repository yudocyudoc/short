# IGC — Auditoría estructural A/B + controles (protocolo v1)

**Diseño:** 2026-10-15 (México). **Estado:** preparado para inferencia; ninguna llamada LLM se atribuye hasta existir un run de GitHub Actions que archive las respuestas originales.

## Pregunta

¿Puede un LLM identificar fallas de correspondencia entre estructura ejecutable, evidencia y contrato operacional? ¿Mejora cuando recibe resultados aritméticos independientes? ¿Puede reconocer un caso estructuralmente consistente sin inventar defectos?

## Diseño de seis inferencias

- Brazo **A**, en orden BB01/W17/W18: solo especificación y resultados declarados del caso.
- Brazo **B**, en orden BB01/W17/W18: mismo contexto e instrucciones más informes aritméticos de probes.py. El modelo **no invoca herramientas autónomamente**; recibe salidas preparadas.
- Modelo fijado: `@cf/deepseek-ai/deepseek-r1-distill-qwen-32b`, temperatura 0.1, máximo 3500 tokens por llamada. Una única llamada independiente por caso/brazo, cero correcciones o reintentos automáticos.
- No comunicar respuestas, métricas ni instrucciones de revisión entre ejecuciones. Archivar entradas exactas, respuestas originales y hashes.
- No usar conocimiento posterior de un caso para modificar el prompt de otro.

## Material de cada caso

**BB01** utiliza transacciones registradas atribuidas a The Bread Basket y series simuladas de las moléculas de Hines `CapUtil` e `invbakf`; se derivan del repositorio `experiments/real-pos/bread-basket/`. Las ventas cobradas **no** son llegadas, servicio, tiempos de espera o demanda no atendida. Los parámetros de capacidad y despacho son hipotéticos. La fuente externa del POS se atribuye a un negocio real pero no está autenticada independientemente.

**W17/W18** son mundos sintéticos con plazo contractual fijo de dos días entre pedido y recepción, inventario inicial de nueve unidades y una orden de doce unidades en día 1. Un caso implementa una discrepancia estructural y el otro sirve de control consistente. Esa clasificación solo está en la clave reservada, no se entrega al LLM.

## Rúbrica congelada antes de inferir

Evaluar respuestas una vez archivadas, por mecanismo justificado y no por repetir advertencias genéricas.

### BB01 — 7 puntos

1. **2 pts** por identificar que `Production=C*f(D/C)` produce más que D cuando la curva lookup supera la diagonal, como propiedad del montaje y no del negocio.
2. **2 pts** por detectar que POS instantáneo determina producción mientras el trabajo pendiente no la realimenta; sin ventas el backlog puede permanecer congelado.
3. **1 pt** por distinguir conservación algebraica e invariantes operacionales; aprobar balances no certifica plausibilidad causal.
4. **1 pt** por distinguir ventas POS registradas de llegadas/demanda latente, capacidad, espera y servicio.
5. **1 pt** por no justificar una decisión de capacidad con estos datos y proponer una observación o prueba discriminante.

### W17/W18 — 4 puntos cada uno

- **2 pts** por juzgar correctamente la correspondencia entre implementación y plazo contractual, con día exacto de recepción y mecanismo.
- **1 pt** por distinguir falta de validación empírica de falla interna demostrable.
- **1 pt** por no recomendar promesas reales sin información del proveedor.
- **−2 pts** por acusación falsa grave contra el control estructuralmente consistente.
- Registrar *sensibilidad* a defecto y *especificidad* ante el caso consistente por separado.

### Comparación A/B

Tabla por caso con A, B y diferencia B−A; además indicadores `BB_both_mechanisms_detected`, `external_defect_detected` y `consistent_control_not_false_positive`. Seis llamadas no dan potencia estadística para inferir generalidad. No afirmar autonomía en SD, recuperación causal real o ROI por aprobar esta prueba.

## Integridad y procedencia

- Las comprobaciones `probes.py` son aritméticas sobre datos declarados; los casos de mutación son ejemplos algebraicos, **no mutaciones ejecutadas en Hines**.
- La cola de fluido supone servicio continuo y transacciones tratadas como llegadas a efectos de contraste; no es una estimación de la cola real.
- Resultados técnicos de transporte/API separados de errores de razonamiento. No reconstruir una respuesta perdida.
- Guardar originales íntegros; el parser puede agregar una copia estructurada, nunca modificar el original.
- El evaluador reservado **no** forma parte del repositorio, workflow, prompts ni artifacts públicos.
- Congelar puntuación antes de revelar etiquetas A/B a los evaluadores cuando sea posible.

## Compromiso previo de la clave privada

SHA-256 del archivo local reservado, fijado antes de ejecutar cualquier consulta:

`1c1c883a46a01b5fb71a453e9f0809e40d380db46a8d5faf5143f17fef38771b`

No subir soluciones o clasificaciones de W17/W18 hasta archivar y puntuar las respuestas originales. La clave queda custodiada fuera del repositorio.

## Parada

Después de una respuesta por brazo/caso, detener. No añadir prompts, casos, compuertas ni reparaciones para mejorar resultados. Los errores del modelo son datos del experimento.
