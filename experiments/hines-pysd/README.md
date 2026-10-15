# Hines — paridad PySD de moléculas originales (C01)

**Propósito:** verificar en GitHub Actions, con un segundo motor, las cuatro moléculas ya recuperadas en el Drive del investigador, sin modelos nuevos ni inferencias LLM.

**Material original:** Jim Hines, *Molecules of Structure*, directorio de Vensim: https://vensim.com/documentation/Models/Molecules/. Los archivos del Drive se verificaron localmente, y sus SHA-256 y parámetros constan en `specifications_extracted.json`.

- `delay.mdl`: Material Delay
- `CapUtil.mdl`: Capacity Utilization
- `invbakf.mdl`: Backlog Shipping Protected by Flow
- `invbakl.mdl`: alternativa de inventario / backlog según nivel

**Razón para no publicar los originales:** este repositorio es público. GitHub Actions descarga directamente de Vensim los `.mdl` **a una ruta temporal** y solo los acepta si los SHA-256 y el tamaño coinciden con las copias del Drive. No se guardan fuentes `.mdl`, traducciones PySD a Python ni otras copias del código de Hines como artefactos o commits.

## Experimento
1. `fetch_sources.py`: descarga y verifica los cuatro archivos originales frente a las huellas ya congeladas. Si Vensim modificó los archivos o bloquea descargas, produce `SOURCE_BLOCKED` y no ejecuta simulación.
2. `independent_euler.py`: reconstrucción independiente de las ecuaciones y tablas lookup verificadas previamente. **No es Vensim ni PySD**.
3. `run_pysd.py`: carga `.mdl` íntegros con `pysd.read_vensim` (PySD 3.14.3 / Python 3.11); ejecuta condiciones originales con el paso temporal original; compara cada variable relevante y punto temporal frente a Euler. Guarda las series PySD, sus diferencias y reporte.
4. `test_euler.py`: ocho controles offline sobre parámetros, tablas lookup, condiciones iniciales y salida independiente.
5. `.github/workflows/hines-pysd-parity.yml`: prueba sin IA, artifact conservado 90 días incluso si falla.

**Interpretación:** `PASS` indica concordancia numérica de ambos motores para estos cuatro archivos, con tolerancias declaradas; no certifica correspondencia causal con la cafetería ni identidad con Vensim. `BLOCKED_SOURCE` significa problema de procedencia/acceso; `BLOCKED_TRANSLATION_OR_EXECUTION` significa limitación de compatibilidad de PySD; `MISMATCH` indica diferencia numérica real a investigar, no que debamos modificar las funciones originales.

**Futuro:** solo tras este gate evaluar cómo ensamblar moléculas en M01, conservando conversiones explícitas entre `orders` y `meals_equivalent`. CEI es una lente comunicativa opcional; el objetivo final es hacer SD accesible a pequeños negocios.

Repositorio fuente de la investigación: `yudocyudoc/short`. Los archivos previos de la fase 1 y del cotejo con fuente están en los paquetes entregados al investigador; este experimento lleva la paridad inter-motor al repositorio público y almacena evidencia de su propia ejecución.
