# C3 — Criterios congelados ANTES de las inferencias

El validador ejecuta comprobaciones computables basadas en `facts.json`. La IA no recibe este archivo. **No se repara automáticamente ninguna respuesta.** Se admite sólo un JSON sin texto extra y sin normalización semántica.

## Diez puertas verificables

Cada puerta vale 1 punto (0–10). Una salida será **aceptada únicamente con 10/10**. Un fallo individual conlleva `REJECT` y una explicación con código.

1. `G1_JSON`: JSON único, objetos/listas y campos requeridos bien tipados.
2. `G2_STOCKS`: stocks de inventario y solicitudes aceptadas pendientes, unidades y estados iniciales correctos; no stocks ficticios.
3. `G3_FLOW_TYPES`: flujos únicos con `entity`, unidades compatibles, cantidad no negativa y conexiones válidas.
4. `G4_REQUEST_PATHS`: las cinco transiciones permitidas de solicitudes están presentes exactamente una vez y no existen rutas prohibidas.
5. `G5_REQUEST_TOTALS`: los totales de solicitud recibida, rechazo, aceptación, cancelación y entrega corresponden a los hechos y a su partición exhaustiva.
6. `G6_PENDING_BALANCE`: stock final pendiente = inicial + aceptaciones − cancelaciones − entregas; comprueba contra el valor declarado.
7. `G7_MATERIAL_BALANCE`: consumo de insumos correcto; stock final = inicial + reposición − material consumido − otros usos.
8. `G8_CAPACITY`: horizonte, capacidad por hora, cota de máquina, cota de insumos, cota conjunta y preparado observado coherentes.
9. `G9_CROSS_DOMAIN`: cumplimiento acopla una bebida preparada con una solicitud completada, sin material transformado creado de la nada; no existe stock de bebidas terminadas.
10. `G10_EPISTEMIC`: no declara retroalimentaciones observadas y reconoce al menos una incertidumbre; no extrapola demanda fisiológica ni inventa nuevos hechos.

**Regla de comparación:** informar conteo de puertas por brazo, rechazo/aceptación y diferencia B−A. Dos respuestas solamente = humo experimental, no evidencia estadística. Si el esquema falla al parsear, todas las otras puertas se puntúan cero (sin tentativa de reparación). Si una puerta detecta error no cubierto, registrar como hallazgo sin modificar la rúbrica 0.1.

## Lo que no garantiza

La «verdad» de las transiciones la aporta una ficha `facts.json` preparada por nosotros, no un sensor independiente. El validador **sólo comprueba consistencia interna y contra hechos explícitos**; no descubrió el campo causal ni puede certificar que el modelo sea completo en un negocio real. Los datos del caso son enteros y muy acotados.

**Diferencia con C2:** las reglas formales comparten la inspiración SD pero la tarea C3 es salida procesable, no diagrama Mermaid. No comparar puntajes de distintos experimentos.
