# IGC-SL v0.1 — Gramática tipada de composición de moléculas

**Estado: propuesta de lenguaje y contratos, NO implementación validada.**  
**Fecha:** 16-oct-2026.  
**Principio:** el LLM produce únicamente una composición causal declarativa. No recibe series ni parámetros numéricos, no formula ecuaciones y no genera código Modelica. Las ecuaciones están en componentes previamente verificados; el compositor y OpenModelica construyen y ejecutan.

## 1. Fuentes examinadas

**Hines:** *Molecules of Structure*, v2.02 (128 páginas). Una molécula es una subestructura de stocks, flujos y/o auxiliares con función dinámica concreta. Hines documenta problema que resuelve, parentesco estructural, unidades, supuestos y precauciones. Ejemplos en el documento: Bathtub, Cascaded Levels, Decay, Material Delay, Close Gap, Smooth, Capacity Utilization, Backlog Shipping Protected by Flow y variantes. Distingue moléculas reutilizables de arquetipos que explican comportamiento.

**Fuente local IGC:** el repositorio contiene cuatro originales Hines verificados por SHA y paridad PySD: delay.mdl, CapUtil.mdl, invbakf.mdl, invbakl.mdl. CapUtil + invbakf se conectaron en el escenario sintético make-to-stock, cuya reproducción matemática en OM fue verificada. Otros ocho candidatos se inspeccionaron, pero NO se habilitaron como moléculas ejecutables. El respaldo completo tiene 82 modelos, no 82 interfaces autorizadas.

**SystemDynamics 2.1.2:** biblioteca BSD de Modelica con componentes mayoritariamente elementales de niveles y tasas. IGC ya ejecutó en CI Level, Level1a, Rate_1, RRate y Modelica.Blocks.Math.Gain. Es nuestro backend ejecutado, pero no confundir cada pieza con una molécula completa.

**BusinessSimulation 2.2.0 (BSL):** descubrimos el paquete existente BusinessSimulation.MoleculesOfStructure. Su documentación afirma inspiración directa en Hines y organiza los módulos por puertos: InformationProcessing, Policy, Blocks, Incubators, Transceivers y Actuators. El código contiene, entre otros, Policy.CloseGap, Policy.FirstOrderStockAdjustment, Transceivers.Reservoir, Transceivers.Chain, Transceivers.SplitFlow, Incubators.Collector, Blocks.EffectOfFatigue, InformationProcessing.Trend. Usa conectores acausales StockPort y FlowPort. Su licencia es EUPL-1.2 o posterior; requiere revisión de compatibilidad si se redistribuye una adaptación. **Sólo hemos examinado fuente y documentación; BSL todavía no ha compilado en nuestro CI.**

La gramática combina **función/parentesco Hines** + **interfaces/puertos BSL** + **ejecución verificada OpenModelica**.

## 2. Tres niveles

1. **ATOM:** un acumulador, una tasa, un limitador, una ganancia, una fuente, un retardo o un sensor.
2. **MOLECULE:** varios átomos que realizan un mecanismo dinámico significativo, con puertos, garantías y precondiciones.
3. **SYSTEM:** composición de moléculas, entidades, fronteras, evidencia e incógnitas.

**El LLM trabaja en MOLECULE y SYSTEM.** Puede ver el funcionamiento conceptual de los átomos, pero no debe sintetizar fórmulas ni inventar interfaces. El compositor resuelve todo en el nivel ATOM o mediante clases moleculares verificadas.

## 3. Sistema de tipos semánticos

Los siguientes son **tipos propios de IGC-SL** y NO nombres de conectores nativos Modelica:

| Tipo | Semántica |
|---|---|
| STOCK<Q> | cantidad acumulada de entidad Q |
| FLOW<Q>/TIME | transferencia por unidad de tiempo de la entidad Q |
| SIGNAL<U> | observación o información, sin transportar entidades |
| CONTROL<U> | orden o regulación de una política |
| REF<P> | parámetro externo requerido con tipo P, SIN valor numérico |
| BOUNDARY<Q> | entrada o salida de entidades en los límites del sistema |
| CONVERT<Q1,Q2> | transformación de entidades que necesita mecanismo declarado |
| EVIDENCE_ID | referencia documental que soporta una decisión |
| HYPOTHESIS | relación aún no verificada, no equivalente a evidencia |

Los puertos contienen DIRECCION (IN/OUT/OBSERVE), TIPO, UNIDADES SIMBÓLICAS, CARDINALIDAD y PERFIL DE INTERFAZ NATIVA.

**Distinción fundamental:** un FLOW material no es un SIGNAL ni un CONTROL. En particular, el StockPort/FlowPort acausal de BSL NO se conecta automáticamente con los RealInput/RealOutput y puertos de SystemDynamics. Cada traductor requiere una firma y un test de adaptador por versiones exactas.

## 4. Contrato de una molécula

Ejemplo de registro propuesto para la molécula de Hines Material Delay; **no es una nueva clase OpenModelica ya operativa**:

~~~yaml
id: HINES.MATERIAL_DELAY
origin: Hines/MoleculesOfStructure/2.02/delay.mdl
family: MATERIAL_DELAY
parents: [HINES.DECAY]
purpose: diferir un flujo material utilizando acumulacion
generic_entity: T

ports:
  material_in:  {direction: IN,      type: FLOW<T>/TIME}
  material_out: {direction: OUT,     type: FLOW<T>/TIME}
  in_transit:   {direction: OBSERVE, type: STOCK<T>}

required_parameters:
  - REF<TRANSIT_TIME>

contracts:
  - CONSERVE_MATERIAL
  - DO_NOT_EQUATE_INPUT_AND_OUTPUT_INSTANTANEOUSLY
  - NOT_EQUIVALENT_TO_ORDER_BACKLOG

verification:
  original_source: SHA_VERIFIED
  pysd_parity: PASS
  modelica_module: NOT_VERIFIED
~~~

Cada molécula registrará: identidad/versión/huellas/licencia, finalidad y condiciones de uso, parentesco, puertos semánticos, **puertos Modelica reales**, contrato de conservación y límites, referencias paramétricas sin valores, evidencias requeridas, contraejemplos y pruebas de compilación/paridad.

## 5. Gramática (DSL visible y AST de máquina)

~~~ebnf
MODEL       = "MODEL", Identifier, "CATALOG", RegistryVersion ;
USE         = "USE", InstanceId, ":", RegisteredMoleculeId ;
BOUNDARY    = "BOUNDARY", InstanceId, ":", RegisteredBoundaryId ;
LINK        = "LINK", PortRef, "->", PortRef ;
SENSE       = "SENSE", PortRef, "->", PortRef ;
GOVERN      = "GOVERN", PortRef, "->", PortRef ;
REQUIRE     = "REQUIRE", InstanceId, ".", RegisteredParameter ;
SUPPORT     = "SUPPORT", Reference, "BY", EvidenceId ;
HYPOTHESIS  = "HYPOTHESIS", Reference, "BY", EvidenceId ;
UNRESOLVED  = "UNRESOLVED", Reference, "REASON", ReasonCode ;
PortRef     = InstanceId, ".", RegisteredPort ;
~~~

**LINK = transferencia de entidades**; **SENSE = lectura de estado o tasa**; **GOVERN = señal de control**. Las conexiones causales no mueven material. El DSL es una **vista humana**: el formato de intercambio real será un AST JSON con instances, edges, parameters_needed, evidence y unresolved. El compilador NO ejecuta texto libre emitido por el LLM.

## 6. Plano conceptual de muestra: NO ejecutable en v0.1

~~~text
MODEL kitchen CATALOG IGC-SL-0.1

BOUNDARY incoming : ACCEPTED_ORDER_SOURCE<Order>
USE queue    : IGC.WORK_QUEUE<Order>
USE prepare  : IGC.BOUNDED_PROCESS<Order,PreparedOrder>
USE ready    : IGC.WORK_QUEUE<PreparedOrder>
USE deliver  : IGC.BOUNDED_DISPATCH<PreparedOrder>

LINK incoming.out -> queue.arrival
LINK queue.release -> prepare.material_in
LINK prepare.material_out -> ready.arrival
LINK ready.release -> deliver.material_in

SENSE queue.current -> prepare.work_available
SENSE ready.current -> deliver.work_available

SUPPORT queue BY F1
SUPPORT prepare BY F2
SUPPORT ready BY F3
SUPPORT deliver BY F3

REQUIRE prepare.capacity_policy
REQUIRE deliver.capacity_policy
UNRESOLVED prepare.capacity_policy REASON MISSING_EVIDENCE
UNRESOLVED deliver.capacity_policy REASON MISSING_EVIDENCE
~~~

Los nombres IGC.WORK_QUEUE, IGC.BOUNDED_PROCESS e IGC.BOUNDED_DISPATCH son **contratos de alto nivel por implementar** sobre los bloques que ya se ejecutaron en el S2. No fingir que existen como clases nativas. La conversión Order→PreparedOrder requiere un mecanismo de transformación validado, no cambiar el tipo de manera libre.

## 7. Reglas obligatorias de la gramática

**R1 Registro cerrado.** Sólo moléculas y puertos con ID/version exactos; no se aceptan clases o relaciones inventadas.

**R2 Tipado completo.** Coincidencia de significado físico, entidad y dimensión, direcciones y tipo de conector nativo/adaptador.

**R3 No stock→stock directo.** Si cambia una acumulación, debe existir tasa/transferencia intermedia verificada; una flecha causal no sustituye a un flujo.

**R4 Conservación y conversión.** No duplicar entidades al conectar dos destinos; utilizar split explícito con conservación o transformación declarada. Una política puede modelar creación/destrucción sólo con frontera o mecanismo justificados.

**R5 Semántica de dominio.** Un backlog de despacho NO es automáticamente trabajo sin preparar; utilización de capacidad no implica fabricar sólo tras pedido. No escoger moléculas únicamente por similitud del nombre.

**R6 Feedback no forzado.** Identificar lazos de balance/refuerzo sólo a partir de conexiones y políticas respaldadas. Las hipótesis quedan diferenciadas de hechos observados.

**R7 Cero cifras para Llama.** El modelo ve sólo presencia/tipos de parámetros REF<...>, jamás capacidades, stock inicial, duración, dt, lookups, tasas o series. Es el backend quien decide si existen los valores necesarios.

**R8 Políticas encapsuladas.** OpenModelica resuelve matemáticas ya presentes en la biblioteca. No descubre políticas del negocio. Sin política implementada, no hay autorización de ejecución.

**R9 Conectores nativos.** No basta con un tipo semántico compatible: los puertos acausales BSL y los puertos SystemDynamics requieren una tabla de correspondencia respaldada por compilación y pruebas.

**R10 Evidencia.** Cada instancia/enlace necesita soporte documental o marca HYPOTHESIS; compilar no valida causalidad empírica.

**R11 Permiso de ejecución separado.** El compilador verifica estructura y tipo; el backend verifica dependencias numéricas; OM compila/ejecuta; el auditor causal y de datos valida las afirmaciones sobre el sistema real. Son gates distintos.

**R12 Abstención explícita.** Admitir GRAPH_PARTIAL, NO_MATCHING_MOLECULE, MISSING_EVIDENCE, POLICY_UNIMPLEMENTED, BINDINGS_MISSING, INTERFACE_INCOMPATIBLE y READY_FOR_SIMULATION. No forzar un modelo completo.

## 8. Inventario inicial y su madurez real

| Pieza/mecanismo | Fuente | Estado que sabemos justificar |
|---|---|---|
| Level, Level1a, Rate_1, RRate | SystemDynamics 2.1.2 | **Ejecutados y cotejados en CI**; átomos reales |
| Gain | MSL 4.0.0 | **Ejecutado con la composición S2** |
| CAP_UTIL | Hines CapUtil.mdl | Original SHA/PySD verificado; reproducción OM en S1, **no módulo molecular encapsulado** |
| BACKLOG_FLOW | Hines invbakf.mdl | Original SHA/PySD; reproducción OM S1; **no módulo molecular encapsulado** |
| BACKLOG_LEVEL | Hines invbakl.mdl | Original SHA/PySD; sin wrapper OM |
| MATERIAL_DELAY | Hines delay.mdl | Original SHA/PySD; sin wrapper OM |
| DoingWork, Cascades, Workforce etc. | Copias Hines inspeccionadas | Candidatos; **no ejecutables admitidos** |
| CloseGap, FirstOrderStockAdjustment | BSL 2.2.0 | Existe fuente; **falta compilar y evaluar interfaz en OM** |
| Reservoir, Chain, SplitFlow, Collector | BSL 2.2.0 | Fuente con puertos acausales; **falta probar en OM** |
| EffectOfFatigue, Trend, Diffusion | BSL 2.2.0 | Existencia revisada, **sin gate ejecutable** |
| FirstOrder, Limiter | MSL 4.0.0 | Clases documentadas; **falta test de su uso IGC específico** |

Nunca afirmar que los 82 modelos del respaldo Hines ya están probados ni que BSL es intercambiable con SystemDynamics. Los cuatro originales Hines sí tienen procedencia/paridad propia, pero todavía no son cuatro clases Modelica importables con interfaces tipadas.

## 9. Diagnósticos y reparaciones

~~~yaml
verdict: REPAIRABLE
errors:
  - code: T_PORT_KIND
    edge: e04
    expected: SIGNAL<STOCK<Order>>
    received: FLOW<Order>/TIME
    repair_options: [RECONNECT, REMOVE_EDGE, VERIFIED_ADAPTER]
  - code: E_UNSUPPORTED_RELATION
    edge: e07
    action: JUSTIFY_OR_REMOVE
  - code: P_MISSING_PARAMETER_BINDING
    molecule: prepare
    action: STOP_REQUEST_DATA
protected_edges: [e01, e02]
repair_scope: [e04, e07]
~~~

**Reparable por LLM:** selección/retirada de una molécula autorizada, reconexión de puertos y eliminación de relaciones no sustentadas, sin nuevos cálculos.

**No reparable automáticamente:** molécula ausente, política no implementada, datos numéricos que faltan, contradicciones y evidencia insuficiente; detenerse en vez de repetir prompts.

Familias: S_* sintaxis; T_* puertos/tipos; M_* mecanismos; E_* evidencia; P_* parámetros; C_* compilación; D_* comportamiento dinámico; V_* soporte empírico.

Preservar cada propuesta y su diagnóstico; comparar límites de 1, 5 y 30 intentos como experimento. Las llamadas adicionales sólo son útiles cuando la crítica puede resolverse mediante modificación estructural. El resultado no se puntúa sólo por checkModel().

## 10. Separación operacional absoluta

**LLM recibe:** narraciones sin cifras, catálogo de propósito/puertos/semántica, evidencia cualitativa, problemas de compatibilidad, diagnósticos categóricos.

**Backend exclusivo recibe:** métricas, parámetros, unidades concretas, curva lookup, series, dt, stocks iniciales y criterios de estabilidad. El validador vincula referencias REF a datos por su cuenta. El LLM no recibe valores ni puede cambiarlos.

**OpenModelica recibe:** un modelo generado por templates/adaptadores verificados y binding numérico del backend; **no código suministrado por LLM**. Calcula resultados matemáticos, pero no certifica que el mecanismo elegido represente la empresa.

## 11. Camino mínimo antes de ampliar el catálogo

1. Encapsular el S2 ya probado en **dos o tres wrappers moleculares reutilizables con puertos estables**, sin reescribir sus ecuaciones. Verificar cada wrapper con OMC.
2. Implementar checker IGC-SL v0.1 con AST, tipado, referencias de evidencia y estados parciales. Sin parámetros al LLM.
3. En rama aislada, clonar una versión fija BSL 2.2.0; intentar cargar/compilar Policy.CloseGap, Reservoir y Chain con OMC; documentar dependencias, puertos y compatibilidad. No asumir PASS a priori.
4. Comparar A: átomos; B: moléculas tipadas; C: moléculas tipadas + hasta 5 reparaciones estructurales. Usar **casos ciegos nuevos**; separar validez causal, conectividad, ejecutabilidad y comportamiento dinámico.
5. Incorporar Hines/BSL de forma incremental y con trazabilidad de licencia y pruebas, no por el nombre del archivo.

## 12. Criterios de aceptación

El próximo IGC-SL puede calificarse PASS solamente si: (1) el LLM no produce ninguna ecuación o valor numérico; (2) todas las instancias/puertos existen en registro; (3) el checker rechaza conectores o políticas no verificadas; (4) los modelos aprobados compilan y se comparan por invariantes; (5) los incompletos se abstienen sin rellenar datos; (6) la corrección causal y el soporte empírico se reportan separados de la compilación; y (7) se conserva cada intento y cada fallo.

## Fuentes auditables

- Hines, Molecules of Structure, versión 2.02: https://www.vensim.com/documentation/Models/Molecules/molecule.pdf
- Teoría e historia: https://www.vensim.com/documentation/introduction_2.html
- Hines repositorio IGC: experiments/molecule-composer-v1/catalog.json y experiments/hines-pysd/specifications_extracted.json
- SystemDynamics v2.1.2, BSD: https://github.com/modelica-3rdparty/SystemDynamics
- BusinessSimulation v2.2.0, EUPL: https://github.com/bslMS/BusinessSimulation
- Taxonomía BSL: https://build.openmodelica.org/Documentation/BusinessSimulation.MoleculesOfStructure.html
- Clases BSL con interfaces: BusinessSimulation/MoleculesOfStructure/{Policy,Transceivers,Incubators,...} en fuente GitHub
- Modelica Standard Library v4.0.0: https://doc.modelica.org/Modelica%204.0.0/Resources/helpWSM/Modelica/Modelica.Blocks.html
- IGC PR #16, #17 y #19: https://github.com/yudocyudoc/short/pull/19

**Nota final:** las firmas IGC-SL y los wrappers de ejemplo son diseño propuesto. No deben presentarse como clases Modelica realmente implementadas hasta superar pruebas de puertos, compilación, semántica y paridad.
