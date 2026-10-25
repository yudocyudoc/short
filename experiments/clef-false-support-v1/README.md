# EPI-05 · ¿Por qué Clef conservó rutas inexistentes?

**Estado: diseño congelado; CERO inferencias reales.** Estudio diagnóstico de los falsos positivos en `HET-08` y `HET-12`. El motor determinista no se sustituye.

## Hallazgo que da origen al protocolo

Se recuperaron directamente los artefactos de EPI-04 (run 39652794232). En ambos casos, el gold verificado por enumeración exhaustiva y clausura de entornos mínimos es **NEITHER**:

| Caso | Ruta 1 hacia soporte aparente | Ruta 2 hacia soporte aparente | Clef previo |
|---|---|---|---|
| HET-08, H2 | `e ∧ f → X2; X2 ∧ g → H2`, pero **e revocado** | `h → H2`, pero **h revocado** | ONLY_H2 (70.82 %) |
| HET-12, H1 | `base ∧ x → H1`, pero **x revocado** | `z ∧ w → H1`, pero **z revocado** | ONLY_H1 (64.72 %) |

Ambas hipótesis quedan sin soporte en ambos casos. Ninguna respuesta del modelo permite identificar directamente qué regla ignoró: es un diagnóstico por **resultado**, no por proceso interno.

**Hallazgo adicional de interfaz**: EPI-04 intentó rotar las opciones pero la función que serializaba las solicitudes utilizaba `sort_keys=True`, lo que ordenó alfabéticamente los `criteria` de **todos** los casos. El efecto del orden no fue medido. Además el estado se enviaba como una cadena JSON; la API oficial de Clef también admite estados objeto. Fuentes: https://developers.cloudflare.com/workers-ai/models/clef/ y https://developers.cloudflare.com/changelog/post/2026-10-01-clef-workers-ai/.

## Seis condiciones, exactamente los mismos casos

Se congela una submuestra de ocho expedientes **sin modificar sus reglas**:

- Cinco NEITHER: HET-04, HET-08, HET-12, HET-16, HET-20.
- Tres controles: HET-05 (BOTH), HET-06 (ONLY_H1), HET-07 (ONLY_H2).

Cada expediente se envía **una vez por condición** (6 × 8 = máximo 48 inferencias Clef). Todas las condiciones usan el **mismo modelo**. Los datos provienen exactamente del commit EPI-04 `047911d739676b15721fdafde20faad49387c250`.

| Condición | Única manipulación respecto a base |
|---|---|
| `BASE_STRING_CHOICE` | Reproducción del estado JSON-como-cadena y cuatro alternativas |
| `OBJECT_CHOICE` | Mismo estado como **objeto JSON** nativo, mismas cuatro opciones |
| `BASE_STRING_BINARY` | Misma cadena; dos preguntas `noul` independientes: soporte H1 / soporte H2 |
| `OBJECT_BINARY` | Dos preguntas `noul`; estado como objeto JSON |
| `EXPLICIT_ACTIVE_CHOICE` | Misma cadena, añade lista de **supuestos primitivos vigentes** calculada por diferencia; no incluye estados H1/H2 |
| `REVERSED_OPTIONS_CHOICE` | Estado e instrucción originales, opciones en **orden invertido** y serialización que conserva dicho orden |

**Hipótesis exploratorias distinguibles:** (a) modo de representación del estado, (b) agregación de dos decisiones frente a cuatro clases, (c) saliencia de invalidaciones, (d) posición de las respuestas. No son mecanismos internos demostrados; con una respuesta por celda no se identifica causalidad estable. La condición ACTIVE entrega una variable derivada, por lo que mide un cambio de información explícita, no solo de formato.

## Puntuación antes de ejecutar

1. **Primaria diagnóstica:** falsos soportes (NEITHER → BOTH/ONLY_H1/ONLY_H2) por condición, denominador fijo **5**.
2. **Control de seguridad:** aciertos en las otras tres categorías por condición; evitar un trivial clasificador que siempre contesta NEITHER.
3. Aciertos caso por caso HET-08 / HET-12 y distribuciones originales, sin reparar respuestas.
4. Para `choice`: Brier multicategoría sobre cuatro respuestas si distribución válida.
5. Para `noul`: regla preestablecida `P(H1) >= .5` y `P(H2) >= .5`; media de Brier binario para ambas etiquetas. **No comparar numéricamente ese Brier con el de cuatro clases** ni asumir que dos probabilidades marginales forman una distribución conjunta.
6. Consumo y latencia informados, por separado.

**Regla de interpretación:** si una condición elimina los dos falsos soportes pero genera errores de los tres controles, no la declararemos mejora. Toda mejora se presentará como *señal local* por falta de replicaciones. Una nueva ronda con casos diferentes sería necesaria para validar una modificación del diseño IGC.

## Ejecución sin inferencia / sin secretos

```bash
python -m unittest discover -s experiments/clef-false-support-v1 -p 'test_*.py' -v
python experiments/clef-false-support-v1/prepare.py --out /tmp/epi05-prepared
```

El CI ejecuta solo estas instrucciones y publica el manifiesto congelado. El runner de producción está protegido por `EPI05_AUTHORIZATION=RUN_EPI05_MAX48`, límite de 48 llamadas y política sin reintentos; **no hay dispatcher habilitado en main**, ni ejecución automática por PR. Para ejecutar en GitHub Actions hará falta un PR de infraestructura independiente y autorización específica.

## Criterio arquitectónico

El motor lógico calcula e invalida soporte. Clef responde decisiones aproximadas y **no puede reinstaurar una justificación extinguida** por su propia puntuación. Su posible aportación es clasificar información documental ambigua, señalar casos para revisión y dirigir investigación; el soporte deductivo conocido se computa exactamente.
