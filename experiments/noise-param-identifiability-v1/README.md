# IGC — Robustez de identificabilidad ante ruido y parámetros no vistos (v1)

Fecha: 2026-10-17. Base: PR #30. Experimento de ingeniería; **sin datos empresariales**.

## Pregunta

Cuando la tasa física y el tablero se observan por canales separados, ¿el guard del PR #30 elimina indebidamente la arquitectura correcta porque el ruido convierte dos tasas físicamente idénticas en números ligeramente distintos? ¿Puede evitarlo una regla que utiliza límites certificados de error sin dejar de descartar algunos mecanismos?

## Mundos verdaderos y perturbaciones

- 4 arquitecturas **existentes**; sin nuevas moléculas ni ecuaciones LLM.
- 2 regímenes **nuevos de parámetros Modelica**, rápidos y lentos (modificaciones de tiempos de preparación, despacho, tránsito y filtro según el grafo). Se simulan **8 mundos** realmente distintos en OpenModelica, no curvas inventadas por Python.
- 5 regímenes instrumentales por mundo: CLEAN_ALL, BOUNDED_ALL, SPARSE_ALL, MISSING_RECEIPT y BAD_CALIBRATION.
- Total **40 expedientes predefinidos**. Los registros numéricos proceden de los mundos OpenModelica con ruido uniforme independiente, determinista por caso/canal y estrictamente acotado a ±0.03 pedidos/hora (salvo registros exactos). SPARSE_ALL descarta aleatoriamente 45% de las muestras de cada sensor. MISSING_RECEIPT no expone recepciones reales. BAD_CALIBRATION aplica una ganancia 1.3 al tablero **y la declara no calibrada**.
- Los parámetros de generación y etiquetas verdaderas sólo los utiliza el generador/evaluador. La función classify_observations recibe exclusivamente expediente, firmas candidatas y modo; ni parámetro ni grafo verdadero.

**Importante:** la etiqueta CALIBRATED y la cota ±0.03 son **supuestos conocidos por construcción** de este benchmark, no evidencia de calibración de sensores en una empresa real. El benchmark no prueba detección de sensores que mienten sobre su estado.

## Condiciones A/B

**A — Tolerancia exacta del PR #30:** máximo |tasa1 − tasa2| comparado con 1e-6; SYNC o DISTINCT, con poda dura en el catálogo. Se preserva su manejo básico de ausencias. Como control negativo deliberado, no sabe manejar ruido ni ganancia no calibrada.

**B — Cota instrumental conservadora:** si cualquier medición en la intersección de tiempos excede la suma de cotas de error de ambos sensores, entonces puede **refutarse la igualdad**. Esto elimina exclusivamente grafos que imponen igualdad de esas dos tasas. Si la diferencia no supera el límite, NO se concluye igualdad y se mantiene el estado INCONCLUSIVE. No se utiliza un resultado sintético para afirmar una estructura causal real.

Un sensor no calibrado queda excluido de las comparaciones de B. El método exige al menos 8 muestras comparables y sólo compara timestamps comunes, sin rellenar huecos.

## Métricas y puertas

- Falsos descartes del grafo generador (B: objetivo = 0/40; A: control negativo debe fallar al menos una vez).
- Casos sin candidatos, casos con candidato único, media de grafos supervivientes y desglose por régimen instrumental.
- B debe descartar **alguna** opción en el conjunto (media de supervivientes inferior a 4); de lo contrario una abstención universal satisfaría cero falsos descartes de forma trivial.
- Resultados históricos PR #28–#30 intocados.

Los indicadores no equivalen a precisión, recall o cobertura en empresas. Tampoco se calcula probabilidad de que un mecanismo sea verdadero; sólo se prueban imposibilidades condicionales al catálogo y cotas de error.

## Límites

1. Las firmas estructurales vienen de los mismos cuatro mecanismos que generan los mundos, aunque los parámetros y canales sean distintos. La estructura verdadera permanece **dentro del catálogo**. No se evalúa aún mundo fuera de catálogo.
2. Las cotas de error son verdaderas por construcción. Ruido gaussiano no acotado, sesgo no detectado, fuentes dependientes y reloj desalineado quedan fuera de este contrato.
3. El método distingue no-igualdad; NO identifica retardo temporal por sí mismo.
4. Una arquitectura directa con ruido puede parecer retrasada. Un muestreo imperfecto no distingue siempre un filtro informacional de tránsito físico.
5. No se obtiene evidencia de adopción, beneficio económico, instrumentación viable ni validez externa.

## Ejecución y evidencia

El workflow `.github/workflows/igc-noise-param-identifiability-v1.yml` instala versiones fijas de OpenModelica, ModelicaStandardLibrary y SystemDynamics, genera el mismo modelo de referencia del PR #29, simula 8 variantes de parámetros y produce expedientes reproducibles con semilla fija.

Salidas: `observations_no_truth.json`, `evaluations_with_truth.json`, `score.json`, CSV Modelica y logs. El evaluador conserva la verdad sólo en el artefacto de puntuación, no en el paquete de observaciones. No se llama Llama: esta fase aísla un error matemático de instrumentación, evitando confundirlo con desempeño de lectura semántica.

**Criterio de continuación:** si B reduce falsos descartes sin convertirse en una abstención absoluta, el siguiente reto será la validez del contrato instrumental y sistemas fuera de catálogo, no ampliar artificialmente la combinatoria molecular.
