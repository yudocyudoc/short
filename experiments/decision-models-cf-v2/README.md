# EPI-04 — Triangulación lógico-probabilística y matemática

**Estado:** implementación de diseño, NO inferencias reales. EPI-03 se conserva intacto.

## Hipótesis que realmente se investiga
1. En expedientes sintéticos de **cinco familias topológicas distintas**, ¿se mantiene la ventaja de Clef sobre GLM-4.7-Flash en clasificar estados lógicos? Se incluyen AND/OR ramificados, cadenas intermedias, dependencias compartidas, nogoods incompatibles y retractación con restauración.
2. Para cálculos numéricos de stocks y flujos, ¿hasta qué punto Clairic coincide con un **oráculo matemático determinista independiente**? Clairic **nunca** sustituye el resultado duro ni puede cambiar la respuesta de la parte lógica.

## Diseño cerrado antes de inferencia
- 20 expedientes nuevos: 4 por familia. Etiquetas congeladas y balanceadas: BOTH / ONLY_H1 / ONLY_H2 / NEITHER, cinco por clase.
- 20 Clef + 20 GLM, mismos `state` y opciones por caso, diferentes APIs nativas. Una respuesta por modelo y caso; sin pseudo-replicaciones.
- En BOTH, las dos hipótesis poseen soporte **individualmente** consistente: los nogoods pueden impedir que ambos soportes coexistan.
- Para restauración, cada revisión declara el conjunto de supuestos *actualmente* invalidado; no se asume que toda invalidación anterior persista.
- 8 comprobaciones Clairic paralelas: balances con decimales, colas con capacidad y dos stocks acoplados con conservación de flujo interno. Un campo numérico, `number`, por caso.
- **Oracle formal doble**: enumeración exhaustiva de entornos compatibles y clausura de conjuntos mínimos (antichains), con error fatal si hay desacuerdo.
- **Oracle numérico**: aritmética Python Decimal, actualización por periodos y aserción de conservación en transferencias internas; un desacuerdo Clairic→math se anota como desacuerdo, no se corrige el gold.
- Gold y fixtures guardados en Git antes del primer run. `prepare.py` rehace los cálculos, exige hashes y excluye el gold de cualquier prompt.

## Evaluación preregistrada
- Primaria: exactitud top-1 por caso (20), Brier de cuatro clases en distribuciones formalmente válidas, cobertura de distribuciones y matriz pareada de victorias Clef/GLM.
- Desglose por **familia** además del agregado; cinco familias correlacionadas, por lo que 20 no son 20 mecanismos independientes ni permiten extrapolación estadística.
- Secundaria: tiempo de cliente, consumo según campos publicados, errores de formato/IDs e incidencias de interfaz.
- Matemática: comparación de 8 valores Clairic contra 8 resultados exactos Decimal; MAE, coincidencias/desacuerdos y fallos de respuesta. La discrepancia es una alerta de validación, nunca criterio para cambiar el resultado determinista.
- Prohibido tratar una probabilidad de opción Clef o GLM como P(estructura del mundo | evidencia). Aquí es confianza en un estado deductivo.
- Sin umbral inventado de significancia. Señal práctica para investigar: al menos 4 aciertos pareados netos para Clef **y** menor Brier en respuestas válidas; insuficiente para declarar superioridad general.

## Sin red ni costo

    python -m unittest discover -s experiments/decision-models-cf-v2 -p 'test_*.py' -v
    python experiments/decision-models-cf-v2/prepare.py --out /tmp/epi04-prepared

El CI del PR ejecuta las 8 pruebas y conserva el manifiesto de preparación. No usa secretos ni llama a Cloudflare.

## Real — exige decisión independiente
- Preflight **solo catálogo**, sin inferencias, mediante `preflight.py` (copiado de EPI-03).
- Para llamar realmente al proveedor: `EPI04_AUTHORIZATION=RUN_EPI04_MAX48`, secretos de Cloudflare y `python experiments/decision-models-cf-v2/run_cloudflare.py --out <directorio>`.
- **Máximo 48 llamadas (20 Clef + 20 GLM + 8 Clairic), cero reintentos**, detención al primer fallo, manifiesto parcial persistido y respuestas originales preservadas.
- El evaluador funciona contra manifest completado o parcial: `python experiments/decision-models-cf-v2/evaluate.py --out <directorio>`.
- Como en EPI-02/03, su ejecución en Actions requiere **otro dispatcher manual aislado**, fijado al SHA aprobado y fusionado por separado; no se modifica ningún dispatcher existente.

## Alcance
Este experimento pone a prueba robustez en cinco topologías *sintéticas*, no la verdad de estructuras empresariales, ni la identificación de causalidad, ni la necesidad del motor ATMS. El motor formal y el modelo de clasificación cumplen roles distintos. No mezcla Clairic y GLM en un promedio arbitrario.

## APIs
- https://developers.cloudflare.com/workers-ai/models/clef/
- https://developers.cloudflare.com/workers-ai/models/clairic/
- https://developers.cloudflare.com/workers-ai/models/glm-4.7-flash/
