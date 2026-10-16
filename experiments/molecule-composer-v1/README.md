# IGC — Hines Molecule Composer v1

**Objetivo:** probar una ruta pragmática: **LLM reconoce la pregunta y selecciona estructuras existentes; compilador independiente controla interfaces y frontera operacional; PySD ejecuta las moléculas originales verificadas**. No se le pide al LLM generar JSON, ecuaciones ni código Python.

**Estado:** exploratorio y sintético. **Una composición que corre no constituye validación causal del negocio.**

## Fuentes y respaldo

- Origen editorial de los originales: Jim Hines, *Molecules of Structure*, accesible a través de Vensim. Los cuatro archivos ya verificados están fijados en `experiments/hines-pysd/specifications_extracted.json` y se obtienen mediante `fetch_sources.py`, con SHA-256 y tamaño comprobados.
- Respaldo facilitado por el investigador: carpeta privada de Google Drive con **83 archivos**: 81 `.mdl`, 1 `.2mdl` y 1 `.pdf`. El índice `drive_backup_discovery.json` registra únicamente nombres, tamaños y estado de revisión; **no guarda Drive IDs ni bytes originales**.
- `inspected_candidates.json` registra inspección de contenido de ocho moléculas adicionales, incluyendo `DoingWork`, `BuildingInvDoingWork`, `produc`, `workf` y `c2capord`; esos archivos **no están habilitados para ejecución**.

**Advertencia sobre nombres sugerentes:** `DoingWork.mdl` incluye `Work To Do = INTEG(-producing,100)` y `producing = workers*productivity`; por sí sola esta forma puede agotar el trabajo sin limitar producción y no representa toda la lógica de una cocina bajo pedido. `BuildingInvDoingWork.mdl` acumula producto, pero tampoco cierra la demanda y el despacho. No declarar que existe una solución compuesta hasta verificarla.

## Tres escenarios

| Caso | Planteamiento | Comportamiento requerido |
|---|---|---|
| S1 | Fabricación para stock con plan independiente y pedidos aceptados | **Puede seleccionar** `CapUtil + invbakf`, con enlace tipado `Production → Producing` y parámetros *hipotéticos* |
| S2 | Cocina estrictamente bajo pedido, necesidad de control endógeno | **Abstenerse** con las cuatro conexiones verificadas; solicitar molécula adecuada y comprobar el estado de trabajo sin preparar |
| S3 | POS de ventas cobradas, capacidad y cola desconocidas | **Abstenerse** de inferir capacidad, esperas y pedidos perdidos |

Los tres casos sirven para comprobar selección, compatibilidad y abstención. El compilador ya conoce qué composiciones están autorizadas: **esta prueba no mide descubrimiento causal autónomo ni búsqueda exhaustiva entre las 82 moléculas**. El inventario permite detectar candidatos pendientes de verificar sin confundirlos con soluciones ejecutables.

## Estructura de archivos

- `catalog.json`: cuatro moléculas verificadas, roles, puertos y limitaciones.
- `drive_backup_discovery.json`: inventario privado *sin IDs*, con clasificación explícita de nivel de confianza.
- `inspected_candidates.json`: evidencia de lectura de ocho candidatos adicionales.
- `cases_public.json`: problemas y evidencia disponible que recibe el LLM.
- `compiler_policies.json`: restricciones operacionales que **no forman parte** del prompt del LLM.
- `run_llm.py`: hasta tres consultas independientes con Llama 3.3 70B; solicita una **explicación en prosa** y selección mínima, sin JSON.
- `composer.py`: convierte la selección textual a un grafo tipado **solo si** existe contrato autorizado; rechaza nombres, puertos, unidades y mecanismos faltantes.
- `simulate.py`: ejecuta el modelo condicional S1 en PySD sobre archivos originales SHA-verificados, siguiendo el adaptador temporal de unidades del experimento Bread Basket.
- `test_composer.py`: controles positivos y negativos; rechaza grafos ficticios, y no acredita a la IA el acierto de los ejemplos de prueba.

## Secuencia y condiciones

```text
Evidencia y pregunta
   ↓
LLM → Selección + justificación en prosa
   ↓
Compilador determinista (catálogo + frontera + puertos + unidades + SHA)
   ├─ REJECT / ABSTAIN → detener, informar qué falta
   └─ COMPILED → permitir PySD únicamente en escenario autorizado
                   ↓
            Datos y parámetros explícitos
                   ↓
          Resultado SIMULADO, no dato observado
```

El compilador no genera nuevas ecuaciones: solo permite la única conexión que ya se ensayó entre `CapUtil.Production` e `invbakf.Producing`. El significado operacional se diferencia del montaje anterior: **producción planificada independiente de ventas** en un fabricante para inventario.

## Reproducción sin inferencias

```sh
cd experiments/molecule-composer-v1
python3 -m unittest -v test_composer.py
python3 run_llm.py --dry-run --out ./output/prepared
python3 composer.py --case S1 --proposal samples/S1.txt --out ./output/s1.json
```

Para ejecutar PySD sobre una selección de muestra:

```sh
pip install -r experiments/hines-pysd/requirements.txt
python experiments/hines-pysd/fetch_sources.py --dest /tmp/hines-originals --out /tmp/hines-manifest
python experiments/molecule-composer-v1/simulate.py \
  --case S1 --proposal experiments/molecule-composer-v1/samples/S1.txt \
  --originals /tmp/hines-originals --scratch /tmp/hines-ephemeral \
  --out /tmp/hines-composition-synthetic
```

GitHub Actions ejecuta las pruebas y la simulación S1 de muestra en PR sin llamar al LLM. El workflow manual tiene `RUN_THREE_CASES` y llama a Llama mediante los secretos Cloudflare existentes. **No ejecutar inferencias automáticamente al abrir PR.**

## Qué puede y qué no puede demostrarse

- **Sí, si CI pasa:** catalogación sin redistribuir fuentes, separación entre LLM y ecuaciones, rechazo de composiciones incompatibles, ejecución de dos originales Hines mediante PySD, balances numéricos del escenario sintético y negativa a simular S2/S3.
- **No:** que la librería completa ya esté indexada semánticamente, que las 82 moléculas funcionen en PySD, que la composición sea autónoma y causalmente correcta o que los supuestos sintéticos describan capacidad/productividad de un negocio.
- **Siguiente avance valioso, fuera de v1:** seleccionar una molécula adicional del respaldo según su contenido (no solo por nombre), verificar su original, identificar puertos/estados y ejecutar una segunda composición útil, especialmente para trabajo pendiente de preparación.
