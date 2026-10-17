# IGC — Selección causal entre dos arquitecturas compatibles por tipos (v1)

**Fecha:** 2026-10-16. **Estado:** piloto de decisiones y ejecución real, no benchmark ciego ni validación de empresa observada.

## Hipótesis concreta

El primer ciclo molecular [PR #25](https://github.com/yudocyudoc/short/pull/25) compiló, pero el compilador exigía los cuatro módulos y una sola cadena. Claude demostró que un unificador de tipos sin LLM podía generar el mismo Modelica. Esta vez **MTO y MTS tienen deliberadamente los MISMOS puertos abstractos**; no se puede elegir sólo por tipos. El motor de composición reconoce **ambas** topologías, sin consultar el gold de cada caso.

- **MTO:** [IGCS2MakeToOrder.Components](../openmodelica-mto-s2/IGCS2MakeToOrder.mo): pedidos aceptados → cola de preparación → cola de trabajos terminados → entregas.
- **MTS:** [IGCS1Parity.Components](../openmodelica-s1-parity/IGCS1Parity.mo): producción planificada externa → inventario terminado + backlog de pedidos pendientes de despacho.
- Ambos se exponen provisionalmente como un módulo causal con firma `FLOW<Order> → FLOW<DeliveredOrder>`. Esa firma de alto nivel es una **fachada declarativa**, no implica que sean clases de puertos Modelica físicamente enchufables.
- `MATERIAL_DELAY`, `BACKLOG_LEVEL`, `WORKFORCE_ADJUSTMENT`, `ADMIN_APPROVAL_DELAY` figuran como distractores semánticos **NO EJECUTABLES**; no fingimos tener ocho moléculas Modelica intercambiables.

**Límite importante:** esta prueba compara selección de dos arquitecturas nativas completas más su representación estructural tipada, **NO composición libre de átomos de Hines**. El compilador instancia el modelo aprobado por la política elegida, sin pasar texto libre del LLM a Modelica.

## Muestra y condiciones

`cases.json` y `evaluation_gold.json`: **12 situaciones redactadas y congeladas antes de inferencias**:
- cuatro casos de política bajo encargo MTO;
- cuatro de producción para inventario MTS;
- dos sin evidencia de la política;
- dos con afirmaciones contradictorias en el mismo periodo.

El LLM recibe **el problema completo y todo el catálogo**, incluidos límites y exclusiones. No recibe etiquetas del gold, números, escenarios numéricos ni ecuaciones. Puede declarar `COMPOSE`, `PARTIAL` o `ABSTAIN` con `unresolved` real.

El validador exige firmas de puerto, estructura SOURCE → (MTO | MTS) → SINK y citas literales tanto para instancias como para aristas, así como `support` y `counterevidence`. **No comprueba la corrección semántica comparando contra la respuesta del caso**; una elección errónea MTS en un caso MTO puede pasar el checker, y debe contarse como **error causal** en la evaluación posterior. Las citas literales, incluso largas, **no certifican pertinencia causal**.

El evaluador sólo carga `evaluation_gold.json` **después de completar la propuesta**; no se filtra al prompt. El estudio declara dos baselines transparentes: unificador de tipos (no puede elegir entre alternativas de firma idéntica) y regex lexical simple, congelado antes de la primera solicitud. No se ajustan baselines ni claves después de conocer resultados.

## Prueba dinámica que distingue arquitecturas

La simulación **no compara S2 contra S2**.

`BehaviorProbes.mo` utiliza los modelos S1 y S2 existentes con una intervención hipotética independiente: **no llegan pedidos nuevos y los estados de trabajo iniciales están vacíos**. El S2 MTO debe dejar preparación/entrega en cero; el S1 MTS puede fabricar para inventario a partir de un plan exógeno aunque no lleguen pedidos. `verify_behavior.py` comprueba dos comportamientos distintos.

Esto prueba una propiedad causal del **mecanismo preautorizado**, pero **no contrasta predicciones con datos observados de una empresa** ni valida empíricamente S1; sus curvas Hines tienen limitaciones conocidas, incluida producción superior a lo deseado en ciertos rangos.

En inferencia real, las propuestas Llama aprobadas se renderizan a `IGCSelected.Candidate`, se compilan y simulan con OpenModelica y se archivan los CSV originales; no se inventan matemáticas desde Llama. Se prueba cada **política distinta seleccionada**, porque la misma arquitectura no requiere recompilarse doce veces para fingir independencia.

## Comandos y ejecución

Sin inferencia:
```sh
python -m unittest discover -s experiments/policy-choice-v1 -p 'test_*.py' -v
python experiments/policy-choice-v1/run_study.py --prepare-only --out /tmp/igc-policy-choice
```

El workflow de GitHub obtiene contenedor `openmodelica/openmodelica:v1.26.5-minimal`, MSL 4.0.0 y SystemDynamics v2.1.2, ejecuta las sondas, y **sólo ante el commit autorizado** ejecuta doce casos Llama 3.3 70B en Cloudflare (un intento y a lo sumo una reparación de esquema/puertos/citas). Respuestas originales y diagnósticos se conservan aunque la elección sea incorrecta.

## Qué permite concluir, y qué no

Una mejora sobre el baseline sólo indica que Llama logra extraer significado causal más allá de tipos y una heurística sencilla en **esta pequeña muestra creada por el equipo**. No hay evaluación ciega independiente, no hay inferencia estadística robusta, no se ha demostrado reparación útil por retroalimentación de dinámica ni composición general Hines/BSL. La clave de validación causal sigue siendo un criterio humano preregistrado del propio proyecto.

**Criterio de éxito limitado:** comprobar que (a) ambas opciones realmente compilan/son distinguibles por experimento de comportamiento; (b) el compilador admite una elección equivocada sintácticamente, en lugar de imponer la respuesta; (c) Llama decide casos positivos, negativos y contradicciones con mayor acierto que los controles sencillos; (d) conserva trazas originales y la posibilidad de fallar.
