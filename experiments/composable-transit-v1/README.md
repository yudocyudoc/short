# IGC — segunda sonda y una molécula verdaderamente combinable

**Diseño:** 2026-10-17, antes de solicitar respuestas Llama. **Estado:** prueba técnica mínima, modelos sintéticos.

## Hipótesis técnica

El PR #27 generaba **dos arquitecturas completas** S1/MTS y S2/MTO, comparaba firmas y usaba Llama como crítico. En esta evolución dejamos de seleccionar solamente macros completas: el enumerador `enumerate.py` combina la misma cadena MTO ya verificada con una **molécula opcional reutilizada**: `IGCMolecules.BoundedQueue`, ahora como almacén en tránsito posterior al despacho. El catálogo tiene dos etapas obligatorias y una opcional. El motor genera todas las variantes permitidas, verifica tipos y **emite conectores Modelica realmente distintos**.

El modelo `IGCTransitCore.Upstream` encapsula fuente de pedidos, cola de preparación y cola de despacho; la parte final no está conectada. El generador determina si conectar directamente `dispatch.completed → delivered.arrival` o si insertar una instancia `transit` con `dispatch.completed → transit.arrival → delivered.arrival`. Todos los cálculos vienen de moléculas previas SystemDynamics/MSL; Llama no emite ecuaciones. La primera versión sigue acotada a **dos topologías**, aunque el algoritmo enumera los subconjuntos de módulos opcionales mediante restricciones de puertos. NO declarar esto composición libre de Hines.

## Dos experimentos independientes en OpenModelica

1. **NO_ACCEPTED_ORDERS:** pedidos entrantes nulos, stocks iniciales vacíos; las dos topologías no preparan ni despachan, tampoco reciben entregas.
2. **DISPATCH_TO_DELIVERY_LAG:** con una entrada temporal cambiante, `Direct` registra entrega simultánea al despacho (`deliveryRate == dispatchRate`); `Buffered` guarda unidades en tránsito y su recepción queda desfasada (`deliveryRate != dispatchRate` durante parte del experimento; stock `inTransit > 0`).

La selección de la segunda prueba es automática: `analyze_probes.py` carga los cuatro CSV de OpenModelica, deriva cualitativamente las firmas sin inventar resultados y elige la prueba que divide los candidatos en más grupos. Si los datos no reproducen esas propiedades, el workflow falla. Los parámetros del tránsito sólo se encuentran en el backend y no en el prompt.

## Llama como crítico y motor como selector

El revisor lee las dos arquitecturas, las firmas cualitativas de la simulación y un relato etiquetado por hechos F1/F2/F3. Ya **no redacta grafos, conexiones, ecuaciones, cifras ni citas textuales**. Debe declarar la expectativa causal del negocio para `DISPATCH_TO_DELIVERY_LAG`: `SYNC`, `LAG`, `UNKNOWN` o `CONFLICT`, con IDs de los hechos en que se basa.

El linter comprueba el contrato y la existencia de esos IDs. El motor conserva solamente las topologías cuya firma dinámica coincide con la expectativa propuesta. **Toda eliminación es CONDICIONAL A LA INTERPRETACIÓN DEL LLM**, no certificación de verdad causal. En `UNKNOWN` y `CONFLICT` ambas se preservan y Llama debe formular una pregunta discriminante.

## Casos nuevos y medición

Cuatro viñetas C01–C04, escritas y congeladas con sus etiquetas **antes del primer llamado**: entrega sólo al llegar tras transporte; retiro inmediato en ventanilla; documentación de despacho sin entrega; dos manuales incompatibles.

Se registran por separado:
- Enumeración y tipado sin LLM;
- Compilación real de ambos modelos con conexión distinta;
- Signaturas de las cuatro simulaciones;
- Primera prueba no discriminante, segunda discriminante;
- Acierto del crítico sobre los cuatro textos sintéticos, y rechazo de afirmaciones con IDs inexistentes;
- No duplicación de cifras o ecuaciones hacia el LLM.

**No hay potencia estadística ni observaciones de empresas reales**. Cuatro casos sintéticos elaborados por el mismo equipo no prueban generalización. El linter no verifica la pertinencia semántica de un fact_id, sólo su existencia y forma. La segunda prueba discrimina una opción de tránsito, no certifica su correspondencia causal con una organización observada.

## Ejecución

CI de GitHub: `.github/workflows/igc-composable-transit-v1.yml`.

El flujo corre tests, enumera grafos, genera Modelica, ejecuta ambas topologías en OpenModelica 1.26.5 con SystemDynamics 2.1.2 y MSL 4.0.0, y calcula firmas. Las cuatro llamadas reales a Cloudflare Llama 3.3 70B sólo se autorizan por un commit sentinela explícito. Se archivan los originales y todos los fallos sin adaptar ex post el gold, las reglas ni los contratos.

**Siguiente avance sólo si pasa:** expandir la biblioteca opcional con una segunda molécula física de comportamiento independiente y construir un enumerador que evite grafos equivalentes y compile incrementalmente. No presentar dos grafos como cientos de estructuras.
