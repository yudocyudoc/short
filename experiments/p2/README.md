# IGC v5.1 — P2 (subconjunto) · IR conceptual y linter tipado para redes

**Estado:** `P2_CONCEPTUAL_IR_ENGINEERING_ONLY`; **NO** `P2_EXECUTABLE_NETWORK_PASS`. Parte de P1 [#39](https://github.com/yudocyudoc/short/pull/39) → E1 [#34](https://github.com/yudocyudoc/short/pull/34) → E0 [#33](https://github.com/yudocyudoc/short/pull/33). Reglas rectoras v5.1. No se reescribió la gramática IGC-SL de [#20](https://github.com/yudocyudoc/short/pull/20); se aplicó un **subconjunto conceptual** de `LINK/SENSE/GOVERN`, evidencia/hipótesis y estados pendientes. Ningún LLM construye AST/Modelica.

## Capacidad pequeña que se añadió

- `registry_conceptual.json`: clases abstractas parametrizadas por entidad genérica `$T`, puertos físicos y lógicos, semántica por familias de mecanismo, origen y madurez. **Ninguna** está aprobada como clase ejecutable en OpenModelica.
- `linter.py`: verifica dirección/identidad/dimensión exacta declarada, conservación **topológica** de stock con distintas salidas registradas, rechazo a clonar una tasa, incompatibilidad semántica explícita, soporte/hipótesis, `SENSE` con observador solo de stock y `GOVERN` con política no verificada que bloquea ejecución. No hay código de casos específicos (ni `if cafe`).
- `test_linter.py`: POS-01, NEG-01/02/03/04, POS-02 y adversariales de adaptadores/control/números no autorizados. Se ejecutan junto a las regresiones de E1 y sondas P1.

**Resultados esperados del contrato:** POS-01 y POS-02 sólo pasan como `STRUCTURAL_ONLY`, **`executable:false`**, porque no existe la política/modelo nativo de abandono; NEG-01 rechaza duplicación; NEG-02 rechaza un mecanismo de propósito incompatible y sin apoyo; NEG-03 expresa `POLICY_UNIMPLEMENTED` con `executable:false` cuando existe una política conceptual sin wrapper verificado; NEG-04 rechaza entidades distintas aunque los tipos generales y unidades coincidan.

## Limitaciones que BLOQUEAN afirmar P2 completado

1. El contrato de conservación `balance` prueba solamente que los puertos del stock están declarados como entradas/salidas distintas. **NO demuestra** que el modelo dinámico cumpla balances, no-negatividad, saturación o igualdad de integrales: no se generan ni ejecutan ecuaciones.
2. Las unidades se comparan como cadenas registradas, **no** mediante un sistema dimensional general. Conversiones y adaptadores requieren versión y prueba propia.
3. La revisión semántica es **negativa y contractual**: una familia declara su capacidad y evidencia, pero eso no establece causalidad real ni que un mecanismo transferido resulte científicamente adecuado.
4. No se admitieron políticas de `GOVERN` nativas ni feedback ejecutable, ni se prueban bucles algebraicos, splits con merges, integridad con BSL o parámetros numéricos. Ninguna clase conceptual es importable en OpenModelica.
5. El vocabulario es experimental; no hay catálogo externo Hines/BSL con licencias e interfaces auditadas, ni construcción desde lenguaje natural.

**Gate técnico de la porción P2:** positivos estructurales y negativos específicos bajo una gramática general + E1 inalterado. **Gate pleno P2:** todavía falta una **red pequeña ejecutable** con split conservativo y política/feedback verificados nativamente en Modelica, sin perder controles L0–L6. Se necesita revisión adversativa **del código nuevo**, independiente del diseño P1, antes de integrar.

**Siguiente acción única después de esta entrega:** presentar a revisión independiente los contratos y tests del nuevo IR, en particular un contraejemplo de conservación dinámica que pasaría L2 pero violaría balance físico; **no ampliar a P3** hasta resolverlo y documentar qué clase Modelica mínima puede admitir ese split/feedback.

No hay merge, no hay PASS causal y no se repite X1. Las diferencias de mundo no son conocidas por el revisor ni el constructor porque este experimento no usa mundos ocultos.
