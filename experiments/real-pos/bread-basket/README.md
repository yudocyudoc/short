# Datos de operaciones atribuidas a cafetería real: The Bread Basket

**Experimento:** `BREAD_BASKET_OBSERVED_POS_V1`. Propósito: demostrar ingreso de información de venta registrada, verificable y no sintética, sin inventar stocks, tiempos de servicio o mecanismos.

## Fuente y procedencia

- Negocio atribuido: *The Bread Basket*, Edimburgo (2016-10-30 a 2017-04-09).
- Fuente atribuida original: https://www.kaggle.com/datasets/mittalvasu95/the-bread-basket
- Copia secundaria pública de archivo sin depurar: `prasertcbs/basic-dataset/BreadBasket_DMS.csv`.
- Commit fuente inmutable: `8415fd4eedd124d739d75430853796e13ded1009`.
- Identidad exacta del archivo Git blob SHA-1: `ceea9513b75a3dda41a9209b6fd1875c12580933`. El ejecutor también registra SHA-256 de los bytes originales.
- Licencia de redistribución del dataset original: **no verificada**. No subir registros crudos; solo preservar agregados estadísticos y manifiesto de procedencia.

La versión inicial contiene **21,293 líneas de artículo**; 786 corresponden a `NONE`. Las restantes son **20,507 líneas de artículos comprados**; agrupadas por `Transaction` dan **9,465 transacciones válidas**. Otras 66 transacciones tienen solamente `NONE` (9,531 IDs brutos en total). Estas magnitudes sirven como invariantes de integridad.

## Qué sabemos y qué ignoramos

| Evidencia | Etiqueta | ¿Qué puede alimentar en SD? |
|---|---|---|
| Hora registrada de transacción / artículo | Observado en un registro público atribuido | Patrón temporal de **ventas registradas**, por día/hora/15 min |
| Productos por transacción | Observado en registro | Mix de productos y conteos, no insumos reales |
| Hora de llegada del cliente, intentos sin venta | No observado | **No inferir demanda total** |
| Cocina, salida de despacho, tiempos de servicio, colas | No observado | **No calibrar servicio, capacidad ni backlog** |
| Recetas, inventarios, merma, devoluciones | No observado | **No estimar stocks materiales ni sus pérdidas** |
| Competencia, oficinas, hospitales, población | No observado | Requiere fuentes externas y delimitación territorial |

Es **datos atribuidos a un negocio real**, no certificación independiente de que cada fila refleje una venta auténtica. Registramos exactamente esa incertidumbre.

## Qué hace este experimento

- Descarga la copia secundaria fijada a un commit de GitHub (sólo en directorio temporal de Actions).
- Verifica la huella git de los bytes, su esquema, fechas, `NONE`, transacciones y cuentas esperadas.
- Produce series de **ventas observadas** agrupadas por hora y por intervalos de 15 minutos, distribución por día de la semana y conteo de productos.
- Conserva como salida derivada JSON de agregados y digest exacto; no publica filas originales.
- **No** ejecuta LLM, modelado de colas, ni intenta adivinar saturación, tiempos de preparación o mermas.

## Cómo ejecutarlo

```bash
python -m unittest discover -s experiments/real-pos -p 'test_*.py' -v
curl -fLsS 'https://raw.githubusercontent.com/prasertcbs/basic-dataset/8415fd4eedd124d739d75430853796e13ded1009/BreadBasket_DMS.csv' -o /tmp/BreadBasket_DMS.csv
python experiments/real-pos/bread-basket/breadbasket_analyze.py \
  --csv /tmp/BreadBasket_DMS.csv \
  --out /tmp/breadbasket-observed-patterns.json
```

El workflow `.github/workflows/breadbasket-real-pos.yml` automatiza todo y publica los agregados como artifact. No mezcla este dataset con M01 sintético ni con sus mundos ocultos.

## Siguiente uso de SD

El dato empírico de ventas observadas puede aportar **una entrada temporal descriptiva** a experimentos SD condicionales. Para hacer **diagnóstico de colas o predicciones** debemos obtener registro adicional de llegada, preparación, entrega y capacidad, o emplear parámetros hipotéticos explícitos para una demo sin atribuirlos al negocio.

Para el momento **Antes**, los registros históricos de venta pueden ayudar a plantear bandas de escenario bajo supuestos declarados; para **Durante** y **Problema**, hace falta instrumentación real de operación. No plantear las ventas registradas como demanda potencial universal.

## Carpeta permanente del experimento

Todos los componentes de la investigación quedan agrupados en `experiments/real-pos/bread-basket/`. Las evidencias auditadas están en la rama de resultados y [PR #10](https://github.com/yudocyudoc/short/pull/10); se conservan como archivos derivados, no como copia del CSV original.
