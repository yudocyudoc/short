# M01 · Composición estructural con moléculas originales de Hines

**Experimento:** `M01_HINES_STRUCTURAL_COMPOSITION_V1`.  
**Rama:** `experiment/m01-hines-composition` (basada en `experiment/hines-pysd-parity`).  
**Propósito:** comenzar a componer estructuras SD verificadas para una cafetería sintética; **no** descubrir una nueva teoría, inventar un modelo desde cero ni ajustar mecanismos desconocidos.

## Base ya comprobada

En [GitHub Actions #38808748143](https://github.com/yudocyudoc/short/actions/runs/38808748143), PySD 3.14.3 reprodujo numéricamente las cuatro moléculas originales de Hines, descargadas directamente de Vensim y validadas mediante SHA-256. Los resultados permanentes están en [PR #6](https://github.com/yudocyudoc/short/pull/6).

Este nuevo ejercicio **no reimplementa las ecuaciones originales** ni supone que sean automáticamente el modelo de M01. Declara qué interfaces podrían utilizarse, qué representa cada acumulación y qué falta para construir un modelo ejecutable y calibrable.

## Traducción controlada de las moléculas

| Hines | Uso candidato en cafetería | Cuestión abierta |
|---|---|---|
| `invbakf.mdl` | Backlog de pedidos aceptados + inventario de pedidos ya preparados + despacho | Backlog inicial, cancelaciones, tiempos de preparación y pickup |
| `CapUtil.mdl` | Respuesta de producción de la cocina a carga/capacidad | Demanda real por minuto, producción observada y curva efectiva del negocio |
| `delay.mdl` | Insumos en tránsito desde proveedor | ¿Retardo fijo o primer orden? Entradas y stock inicial en tránsito no observados |
| `invbakl.mdl` | Alternativa de política de salida limitada por inventario | **No se incorpora simultáneamente** a `invbakf.mdl` |

Atención: el `Inventory` de `invbakf.mdl` debe interpretarse como pedidos preparados (*orders*), no como el inventario de ingredientes (`meals_equivalent`). Las dos cuentas de `Backlog` e `Inventory` comparten el evento de despacho, pero **no** representan un único stock físico que pueda sumarse sin más. Los inventarios de ingredientes y el dinero requieren balances separados.

`delay.mdl` utiliza retardo de primer orden, lo cual **no se deduce** del plazo nominal del proveedor de un día en M01.

## Evidencia pública de M01

El programa `prepare.py` original valida las filas y hashes del ZIP público de ocho mundos, sin abrir `holdout`, oráculo ni generador. El contrato de composición fija el SHA-256 exacto del M01 preparado: `3ede7ef04e172c04f9ab5564c57bc1b1e5d88ba63c19b76660e9941f13dec6df`.

La referencia declara:
- Cocina: **16 pedidos/hora**, capacidad nominal calibrada.
- Despacho: **15 pedidos/hora**, capacidad nominal calibrada.
- Ventanas: 2 horas cada una, 14 días y 3 ventanas diarias.
- Inventario inicial: **92 meals_equivalent** (observado).
- Caja inicial: **MXN 4,600** (observada).
- Plazo nominal de proveedor: **1 día** (observado como parámetro de referencia).

El reporte calcula solo la **presión de aceptación contra capacidad nominal de referencia** (32 pedidos/ventana cocina, 30 despacho). **No** interpreta excesos como prueba de saturación: aceptaciones son cohortes de llegada, completados son ventanas efectivas de servicio, y no hay trazas de procesos. La función de utilización original de Hines supera 100% a elevada demanda; una capacidad nominal no es un límite físico fijo demostrado.

## Regla de parada antes de pronosticar

**`STRUCTURE PASS` no significa `MODEL CALIBRATED`.** El reporte obliga `simulation_gate=BLOCKED_NOT_IDENTIFIED` por ausencia de:
- Conversión observada `meals_equivalent/order`.
- Cola inicial de pedidos y productos ya preparados.
- Eventos temporales de cocina y despacho.
- Registros de entradas del proveedor e inventario en tránsito.
- Flujos financieros reconstruibles y distribución del plazo de suministro.

No hay parámetros M01 imputados artificialmente, ni simulación contrafactual, ni comparación contra el mundo sintético secreto, ni uso del LLM.

## Resultado efectivo — 2026-10-15

La ejecución [Actions #38824913038](https://github.com/yudocyudoc/short/actions/runs/38824913038) aprobó **19 pruebas** y validó el paquete público. El resultado completo con hash por archivo quedó conservado en [PR #8 — auditoría M01](https://github.com/yudocyudoc/short/pull/8), mediante un archivado independiente sin reejecución ([Actions #38825023972](https://github.com/yudocyudoc/short/actions/runs/38825023972)).

- Contrato y dimensiones: **PASS**. Tres moléculas candidatas, una alternativa no compuesta, seis estados y siete tasas revisadas.
- Ventanas: 42. Total de aceptaciones por cohorte: 789; total de completados en ventanas de servicio: 780. **No** son categorías intercambiables.
- Un único evento de presión nominal superior a cocina de referencia: **día 2 / pico, 34 aceptaciones frente a 32 de capacidad nominal en dos horas**, fuente `POS:D02:pico`. No constituye una medición de saturación.
- Ocho puertos pendientes. `simulation_gate=BLOCKED_NOT_IDENTIFIED`; **cero proyecciones e inferencias**.
- La composición no fue ejecutada en PySD como un modelo calibrado; sí descansó en la paridad de los cuatro modelos originales ya comprobada en PR #5/#6.

## Reproducción y auditoría

```bash
python -m unittest discover -s experiments/hines-pysd -p 'test_*.py' -v
python experiments/igc0/analyst/src/prepare.py \
  --public-zip experiments/igc0/analyst/inputs/IGC0_8_mundos_analista.zip \
  --out /tmp/m01-public-prepared
python experiments/hines-pysd/compose_m01.py \
  --input /tmp/m01-public-prepared/inputs/M01.json \
  --out experiments/hines-pysd/output/m01_hines_composition.json
```

El workflow `.github/workflows/m01-hines-composition.yml` ejecuta los pasos y preserva el reporte como artifact de GitHub Actions.

**Siguiente decisión tras superar el gate:** qué instrumentación mínima haría identificable el modelo, si conviene una demo ilustrativa con parámetros abiertamente hipotéticos y cómo presentar las restricciones a una persona que administra una cafetería. No avanzar a una proyección de M01 antes de separar explícitamente demostración y evidencia.
