# IGC-0 · Ocho mundos sintéticos para una prueba de Dinámica de Sistemas

**Estado:** piloto de desarrollo generado y auditado localmente el 14 de octubre de 2026. **No se han ejecutado inferencias de LLM ni evaluado un método IGC.**

**Decisión focal:** «¿Abrir delivery con la cocina actual?» en tres variantes: mantener sólo presencial, abrir delivery todo el horario o abrirlo únicamente en las ventanas valle con límite de pedidos.

## Tres paquetes con accesos distintos

1. **Analista**: `IGC0_8_mundos_analista.zip`. Ocho casos M01–M08, observaciones POS por ventanas y estados diarios de inventario/caja/cuentas por cobrar, parámetros de la referencia factible, unidades, fuentes e integridad SHA-256. **No incluye semillas, desviaciones ni respuestas.** Entregar este paquete al LLM o a una línea base convencional.
2. **Implementador**: `IGC0_motor_y_pruebas.zip`. Código del simulador de eventos, generador genérico, tests públicos y documentación del protocolo. No contiene el archivo de ocho mundos secretos. **No entregar al analista ciego**: el código permite inferir qué mecanismos se consideran posibles.
3. **Evaluador**: `IGC0_oraculo_evaluador.zip`. Configuraciones exactas, tipos de mundo, mecanismos inyectados, mundos de referencia, resultados de decisiones y trazas internas. **No compartir con analistas antes de congelar sus respuestas.**

El código y las observaciones tienen procedencia sintética. `OBSERVADO` significa **observado dentro del mundo simulado**, nunca observación real de una empresa. `CALIBRADO` designa el modelo de referencia sintético. Las proyecciones del motor son `SIMULADO`.

## Lo que existe

- **8 mundos × 14 días × 3 ventanas** = 336 registros POS de ventanas, más 112 cierres diarios de existencias y finanzas.
- Un mundo generador de **eventos individuales**, no ecuaciones SD agregadas: llegadas, admisión, turnos compartidos de cocina, despacho, cancelaciones, reabastecimiento y liquidación de plataforma.
- El mismo calendario potencial de demanda se reutiliza en las tres decisiones de cada mundo, evitando ruido adicional al comparar políticas.
- Una referencia operativa factible, con fronteras y unidades; no se presenta como óptimo.
- Ocho mundos con una mezcla sellada de casos nulos, restricciones de pico y liquidación, fronteras no incluidas y mecanismos alternativos indistinguibles en los datos disponibles.
- Dos mecanismos ocultos diferentes generan una **misma evidencia pública** y responden de forma distinta a dos intervenciones diagnósticas. Ésta es una prueba expresa de identificabilidad, no un error del generador.

## Cómo verificar los archivos

```bash
python -m unittest discover -s tests -v
```

La prueba privada adicional, si se tiene el paquete de evaluador, se ejecuta después de colocar `holdout/` junto a `src/`:

```bash
python -m unittest discover -s holdout/tests -v
```

Para reproducir los mundos con las configuraciones privadas:

```bash
python src/generate.py --config holdout/config.json --out .
```

## Alcance de la prueba

Estos mundos permiten estudiar si un sistema IGC identifica stocks/pipes y fronteras, los representa en un modelo SD mínimo, distingue ausencia de desviación y no identificabilidad, contrasta una referencia factible contra un virtual y evalúa acciones bajo un horizonte definido.

**No prueban todavía** que un LLM pueda hacerlo. La construcción del generador fue iterativa y sus ejemplos se revisaron durante el diseño: son un **set de desarrollo**, no un benchmark confirmatorio preregistrado o independiente. Los umbrales y la función de pérdida sintética se congelan ahora para pruebas posteriores sobre estos ocho casos, pero no adquieren por ello carácter independiente.

Para la futura validación IGC, se recomienda un simulador agregado de SD **separado** del generador por eventos, para evitar evaluar el mundo contra su misma implementación.

## Estructura

- `public/Mxx/packet.json`: entradas del analista, sin verdad oculta.
- `public/index.json`: códigos y checksums de casos.
- `src/simulator.py`: generador de eventos individuales.
- `src/generate.py`: exporta observaciones y oráculo en carpetas separadas.
- `tests/test_public.py`: validaciones divulgables.
- `holdout/config.json`: identidades ocultas de los ocho mundos (**evaluador solamente**).
- `holdout/oracle/Mxx.json`: resultado y contrafactuales por acción (**evaluador solamente**).
- `holdout/event_traces/Mxx.json`: traza interna de cada mundo (**evaluador solamente**).
- `docs/PROTOCOLO.md`, `docs/CONTRATO_ANALISTA.md`, `docs/NOTAS_VALIDACION.md`.
