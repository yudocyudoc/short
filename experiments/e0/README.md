# IGC v3 — E0 (contrato previo, no descubrimiento)

[Contrato de una página](CONTRACT.md) · [Catálogo molecular](catalog.json) · [Protocolo ideal](protocol.json) · [Hoja de ruta v3](../../docs/IGC_SD_HOJA_DE_RUTA_CONSOLIDADA_v3_2026-10-18.md)

## Ejecutar controles

    python experiments/e0/check_contract.py --check
    python -m unittest discover -s experiments/e0 -p 'test_*.py' -v
    python -m unittest discover -s experiments/e0/evaluator -p 'test_*.py' -v

La CI de E0 ejecuta las 48 referencias **fijas del evaluador** (6 arquitecturas explícitas × 2 capacidades × 4 excitaciones) en OpenModelica nativo con paquetes fijados, y calcula series numéricas comparables bajo perfiles P y Q, con errores y matriz por pares. Estas referencias conocidas **no se ofrecen al compositor como respuestas** ni demuestran que un motor sea capaz de construirlas. Los nombres de estructuras del evaluador son públicos para auditar la matriz, pero no son el manifiesto de mundos ocultos E2.

La carpeta evaluator es infraestructura del juez: su generador de 48 ensayos **NO** es un generador de modelos candidatos. Se prohibe reciclar su tabla de seis clases como catálogo de respuestas de E1. E2 deberá incorporar verdad sellada aislada en otro contexto de ejecución, no simplemente un archivo gold dentro del checkout del constructor.

Los resultados de una matriz con diferencia numérica bajo cota se rotulan **UNRESOLVED**, nunca EQUIVALENTE sin prueba analítica. El perfil Q sólo observa el tablero; diferencias físicas invisibles NO pueden eliminar hipótesis.

**Estado metodológico inicial:** S1–S5 e I1–I4 = NOT_RUN; la CI, aun verde, sólo demuestra preparación E0/ENGINEERING_ONLY. Si la matriz, las unidades o los controles no pasan, registrar el bloqueo antes de comenzar E1.
