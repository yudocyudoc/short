# C5 — Pre-registro y rúbrica antes de inferencia

Modelo `@cf/deepseek-ai/deepseek-r1-distill-qwen-32b`; dos inferencias máximo, orden A → B; `temperature=0.1`, `max_tokens=3500`, `stream=false`. Sin reintentos ni retroalimentación entre brazos.

**A** recibe `scenario.md` + `prompts/contract.md` + `prompts/common.md`. **B** recibe exactamente eso + contenido sin modificar de `experiments/c4.2/prompts/flow-coverage.md`. La gramática no se personaliza para libros. Mismo modelo y mismo separador de razonamiento de `scripts/c42_transport.py`.

## Referencia (no enviada a la IA)

- Disponible final = 40 + 6 − 21 + 14 − 3 + 2 = **38**.
- Prestado final = 18 + 21 − 14 = **25**.
- En reparación final = 4 + 3 − 2 − 1 = **4**.
- Reservas pendientes final = 5 + 17 − 12 − 3 = **7**.
- Existencias físicas totales: 62 iniciales → 62 + 6 − 1 = **67** finales = 38 + 25 + 4.
- Las **12 reservas atendidas** son parte de los **21 préstamos**, no un flujo físico adicional.

## Once puertas deterministas, 1 punto cada una

1. `T1_SCHEMA`: JSON válido y todos los tipos/claves conforme al contrato.
2. `T2_STOCKS`: los cuatro stocks obligatorios, unidades correctas, valores iniciales y ningún stock ficticio.
3. `T3_FLOW_TYPES`: nueve flujos con IDs únicos, cantidades enteras no negativas, entidad y unidad compatibles.
4. `T4_TOPOLOGY`: las nueve transiciones físicas/de reservas correctas sin omisiones ni rutas extra.
5. `T5_PHYSICAL_COUNTS`: cantidades físicas observadas por arista correctas.
6. `T6_RESERVATION_COUNTS`: creación/servicio/cancelación observados correctos.
7. `T7_STOCK_BALANCES`: cada stock cierra independientemente con sus flujos y los registros observados; certificado por stock.
8. `T8_TOTAL_CONSERVATION`: balance agregado físico 62 → 67 sin contar reservas como ejemplares.
9. `T9_NO_DOUBLE_COUNT`: 12 reservas atendidas son subconjunto de 21 préstamos; sin aristas extra de ejemplares por la atención de reservas.
10. `T10_EPISTEMIC`: no declara bucles observados; al menos una incertidumbre.
11. `T11_COVERAGE`: el certificado genérico de C4.2 comprueba que cada stock cambió a través de flujos compatibles, sin reparación.

**ACCEPT** requiere **11/11**; cualquier fallo es `REJECT`. Una salida sin formato admisible es `FORMAT_REJECT`; no se extrae JSON desde texto libre. Cada puerta tiene explicación general, y las cantidades correctas provienen de `facts.json` que no se manda a la IA.

## Interpretación y sesgos

- Adaptación al experimento anterior: se eligió un sistema con retorno de ejemplares y una cola de reservas, después de analizar la cafetería. Sin embargo **la regla B no se modifica** tras ver ese nuevo escenario.
- El contrato proporciona vocabulario candidato; por ello probamos **transferencia de balances y conexiones**, no inferencia libre de una ontología empresarial.
- Una respuesta por brazo no permite inferencia estadística. Aun un 11/11 demostraría sólo capacidad local bajo estructura y hechos dados.
- Reportar tokens, neuronas y costos por llamada; no confundir estimación con facturación de Cloudflare.
