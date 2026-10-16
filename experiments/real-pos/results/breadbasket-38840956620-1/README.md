# Auditoría permanente — The Bread Basket (POS observado)

**Corrida:** [GitHub Actions #38840956620](https://github.com/yudocyudoc/short/actions/runs/38840956620).  
**Código:** PR #9, rama `experiment/breadbasket-real-observations`, commit `91809892ea96f81379dfb86f71acd65ba548340d`.

## Cómo verificar

1. Leer `audit_summary.json`, incluido el commit inmutable del mirror, git blob SHA-1 y SHA-256 de sus bytes.
2. Descargar exclusivamente la fuente fijada (`raw.githubusercontent.com/prasertcbs/basic-dataset/8415fd4eedd124d739d75430853796e13ded1009/BreadBasket_DMS.csv`), comprobar `sha256=72d21cc42c084d1e54a7b9183b0294d8b4142cf4b5a224eb41a21228a71797a8`.
3. Ejecutar `python experiments/real-pos/breadbasket_analyze.py --csv FILE --out RESULTS.json` desde el commit del PR #9 (Python 3.11).
4. El resultado completo serializado, con conteos diarios y ventanas de 15 minutos, debe tener SHA-256 `15e4ab830b9fd4958266110ad6f75cdd1f863a850914fa79131d1bb721013b98` (644,997 bytes).
5. El artifact original tiene ID **12021111990**, SHA-256 de ZIP `e03341715b63cc51467f08fe78f211e84bd9318ed1f591cdeb0a6db546e07c61`. El artifact caduca después de 90 días; los datos de fuente fijada, código, este resumen y sus hashes **no**.
6. No se publica el CSV original, dado que su permiso de redistribución no está verificado. Las estadísticas se pueden reconstruir.

## Interpretación

Este piloto fue el primer paso para abandonar observaciones puramente sintéticas: son **registros públicos atribuidos a una panadería real**, con procedencia secundaria y autenticidad no verificada independientemente.

**No** hay timestamps independientes de llegada o tiempo de cocina; cada `Transaction` identifica una transacción con productos. Los registros de producto `NONE` se excluyeron sin inventar ventas. La hora de venta no equivale necesariamente a llegada del cliente y el máximo histórico de ventas no establece capacidad máxima.

**Los resultados todavía no constituyen un modelo SD calibrado** ni explican inventarios, fugas o saturación. La próxima integración con moléculas de Hines, de hacerse, debe etiquetar todo valor de servicio/capacidad sin observar como hipotético.
