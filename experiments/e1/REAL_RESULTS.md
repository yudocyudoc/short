# E1 — REAL_RESULTS · Composición molecular por registro

**Corrida adjudicable técnica:** [GitHub Actions #39104098853](https://github.com/yudocyudoc/short/actions/runs/39104098853) · [artefactos originales de Modelica y evaluación](https://github.com/yudocyudoc/short/actions/runs/39104098853/artifacts/12127229929) · cabeza ejecutada: `769585020903ff736ce941d63a6356df227d7147`. Fecha de ejecución UTC: 2026-10-18.

**Estado técnico: PASS. Estado metodológico: COMPOSITION_ENGINEERING_ONLY.** S3/S4/S5 e I1–I4: NOT_RUN. No se identifica un mundo, ni se infiere arquitectura desde evidencia natural ni se consulta un oráculo.

## Contraste medido, no esperado

| Gate | Resultado observado |
|---|---|
| Suite Python (con negativos) | **11/11 PASS** |
| Registro base | **6 AST válidos, 6 canónicos distintos, 6 CSV nativos** |
| Registro extendido | **15 AST válidos, 15 canónicos distintos, 15 CSV nativos** |
| Cambio de motor entre registros | **0**: mismos archivos `composer.py` y `backend.py` |
| Canónicos nuevos por cambiar exclusivamente el inventario JSON | **9**, y los seis previos permanecen |
| Diferencia física máxima entre modelos con igual ruta material pero diferente ruta informativa | **2.5177502616102743e-7**, menor que el umbral operativo E1 de 1e-4 |
| Máxima diferencia físico/reporte en casos con filtro | **3.035602156130383** (unidades de tasa/h) |
| Máxima diferencia físico/reporte en casos con ganancia | **2.6545526561183728** (unidades de tasa/h) |
| Nuevas ecuaciones diferenciales escritas por IA o motor | **0**; se instanciaron clases originales de SystemDynamics/MSL |
| Resultado de CI | **success** |

En ambos registros, el generador partió de las descripciones declarativas de roles, puertos y límites. La extensión incorporó `Modelica.Blocks.Math.Gain` de MSL con `k=1.25`, sin modificar la lógica del compositor. Los nueve canónicos adicionales son **alternativas sintácticas composicionales de la rama informacional**: no nueve mecanismos causales distintos, ni nueve mundos identificables.

### Qué prueba

- El compositor de puertos abiertos deriva conexiones tipadas de un registro intercambiable, no de una tabla de escenarios `TransitOnly` o `TransitAndReport`.
- Permite sustituir nombres de rol, límites de instancias y catálogo; el backend genera instancias y enlaces nativos sin producir ecuaciones de estado.
- Rechaza casos deliberadamente incompatibles: unidad, tipo, desconexión material, límites de roles, parametrización, canon duplicado y presupuesto de búsqueda.
- Los modelos generados realmente corrieron en OpenModelica 1.26.5, MSL 4.0.0 y SystemDynamics 2.1.2, según la CI y sus artefactos.

### Qué NO prueba

- Que un LLM extraiga fronteras, stocks, política y mecanismos de una narración neutral (IA-1).
- Que IGC seleccione correctamente una arquitectura para un mundo desconocido (E2).
- Que encuentre un experimento causal discriminante antes de ver la respuesta, o que prediga una intervención reservada.
- Que las rutas con Gain y filtro sean identificables o causalmente diferentes. La composición puede producir estructuras dinámicamente equivalentes.
- Que la misma gramática ya pueda construir bucles de realimentación entre módulos, bifurcaciones físicas, múltiples entradas o un sistema empresarial completo.

### Fallo inicial conservado

[Primera corrida #39103995772](https://github.com/yudocyudoc/short/actions/runs/39103995772): los 11 tests y ambas generaciones (6/15) pasaron, pero el backend no creó directorios de salida para los CSV, causando fallos del simulador. Se corrigió explícitamente la creación de `generated/{base,extended}/results/`; la siguiente corrida #39104098853 ejecutó la suite completa y verificó los CSV. **El primer FAIL no se elimina ni se reetiqueta.**

### Decisión sugerida

E1 aporta evidencia de **factibilidad composicional acotada por contratos**, más fuerte que la enumeración booleana del PR #29. No valida la metodología IGC completa. Debe seguir **IA-1**, donde una IA proponga entidades, fronteras y grafos a partir de descripciones sin solución incorporada, con baseline y mundos reservados. El examen adversativo de E0/E1 se realizará más adelante, antes de integrar ambos PR en `main`.

Referencias: [Contrato E1](CONTRACT.md) · [registro base](registry.base.json) · [registro extendido](registry.extended.json) · [PR #33 E0](https://github.com/yudocyudoc/short/pull/33) · [hoja de ruta v3](../../docs/IGC_SD_HOJA_DE_RUTA_CONSOLIDADA_v3_2026-10-18.md).
