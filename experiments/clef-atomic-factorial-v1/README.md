# EPI-06 · Separar efecto de preguntas atómicas vs instrucciones completas

**Estado:** diseño y simulación, **sin llamadas reales a Clef**. Continuación de [EPI-05](https://github.com/yudocyudoc/short/pull/49), que consiguió 8/8 con preguntas binarias frente a 6/8 con pregunta cuádruple, pero modificó simultáneamente las instrucciones.

## Pregunta falsable

En expedientes nuevos, ¿qué produce menos **falsos soportes**: a) formular dos preguntas binarias para H1 y H2 en lugar de seleccionar uno de cuatro estados, b) precisar explícitamente que una ruta parcialmente rota no conserva soporte, o c) su combinación?

**El motor lógico no se reemplaza con Clef.** El oráculo es una enumeración exhaustiva independiente, comprobada por entornos mínimos antichain.

## Diseño factorial 2×2: cuatro condiciones por expediente

| | Instrucción base | Instrucción reforzada |
|---|---|---|
| Una pregunta de cuatro alternativas | `CHOICE_BASE` | `CHOICE_EXPLICIT` |
| Dos preguntas binarias `noul` | `BINARY_BASE` | `BINARY_EXPLICIT` |

La misma cláusula literal de rutas completas (`STRONG` en `prepare.py`) se inserta en ambas modalidades. Entre condiciones no se cambia el estado, las reglas, los criterios de las alternativas, las invalidaciones ni el modelo.

- **Factor tarea**: `choice` (BOTH, ONLY_H1, ONLY_H2, NEITHER) frente a dos `noul` (`h1_supported`, `h2_supported`).
- **Factor instrucción**: texto de EPI-05 basado en reglas/revisiones frente a ese mismo texto MÁS «ruta completa, todos los supuestos vigentes, fragmentos no cuentan», tanto en choice como en binary.
- **No es un control semántico perfecto**: la API necesita formular una pregunta por hipótesis y opciones descriptivas propias de choice. Las diferencias intrínsecas de interfaz subsisten; la manipulación de claridad sí es idéntica entre modalidades.
- El *state* sigue siendo la misma cadena JSON serializada canónicamente para las cuatro condiciones, sin anotaciones extras que filtren el gold.

## Datos totalmente nuevos, sin selección retrospectiva de errores

**20 expedientes NX-01…NX-20**, no se usan los ocho de EPI-05. Cuatro topologías×cinco variantes:
- Cadenas profundas con dos caminos por hipótesis.
- Rutas que comparten dependencia.
- Nogoods de incompatibilidad.
- Revocación temporal, restauración y nuevas revocaciones.

Por cada familia: 2×NEITHER (dos conjuntos de revocaciones distintos), 1×BOTH, 1×ONLY_H1, 1×ONLY_H2. Totales: **8 NEITHER y 12 controles positivos**. Las clases están entremezcladas con IDs opacos, no colocadas siempre en el mismo orden. Estos ejemplos son sintéticos y correlacionados dentro de cada familia.

**Máximo 80 inferencias Clef** (20 casos×4 modalidades) **una por celda**, sin reintentos. No existe inferencia automática al hacer commit, abrir PR ni correr los tests.

## Métricas congeladas antes de inferencia

1. **Primaria**: falsos soportes sobre los ocho casos cuyo gold es NEITHER, por condición. Una salida inválida NO cuenta como acierto.
2. **Control de trivialidad**: aciertos entre 12 casos con soportes verdaderos; un modelo que responde siempre NEITHER obtiene 0/12 controles.
3. Aciertos emparejados caso a caso, tasa total y cambio emparejado por factor: `task_at_base`, `task_at_explicit`, `instruction_at_choice` e `instruction_at_binary`.
4. Diferencia de diferencias sobre exactitud agregada, meramente descriptiva. No es evidencia causal generalizable ni prueba de independencia de condiciones.
5. Evaluación probabilística dentro de cada modalidad solamente: Brier multicategoría para `choice`; media de Brier binario de H1 y H2 para `noul`. **No comparar ni mezclar estas dos escalas.** Las probabilidades no son probabilidades de verdad del mundo.
6. Latencia, consumo informado y respuestas malformadas; respuestas originales y hashes preservados.
7. Sin test de significancia ni umbrales de «éxito» inventados a posteriori. Cualquier pauta favorable se considerará **señal exploratoria local**, pendiente de replicación con documentos reales.

## Reproducibilidad y autorización

```bash
python -m unittest discover -s experiments/clef-atomic-factorial-v1 -p 'test_*.py' -v
python experiments/clef-atomic-factorial-v1/prepare.py --out /tmp/epi06
```

Un doble oráculo ejecuta todas las combinaciones de supuestos compatibles y cierra de forma independiente antichains de entornos mínimos. `gold.json` debe coincidir con ambos. El CI solo ejecuta 9 tests locales, incluyendo el camino completo con 80 respuestas mock, y publica el manifiesto previo, sin secretos.

Para correr de verdad se requieren `EPI06_AUTHORIZATION=RUN_EPI06_MAX80` y credenciales de Cloudflare; el runner verifica fixtures/gold/solicitudes y detiene la campaña ante el primer error, sin reintentos, guardando la evidencia. **No se habilita dispatcher de inferencia en main mediante este PR.** Se instalará de forma separada y manual solo tras revisar el SHA congelado.

## Alcance y consecuencias arquitectónicas

EPI-05 demuestra una mejora local de clasificación al variar el diseño de preguntas; no identifica la causa interna. EPI-06 contrasta dos factores con ejemplos no vistos. Incluso si las binarias ganan, el soporte determinado por ATMS sigue siendo autoridad exacta; Clef debe usarse para decisiones atómicas en información ambigua, sugerir rutas de investigación y señalar posibles discrepancias, no para reinstaurar una justificación revocada.
