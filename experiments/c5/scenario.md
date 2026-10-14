# C5 — Biblioteca pública, circulación en una semana

Una biblioteca administra **ejemplares físicos intercambiables de un mismo tipo** y una cola de reservas. Los préstamos y devoluciones desplazan ejemplares; las reservas son solicitudes, no ejemplares físicos.

**Existencias al inicio de la semana:**
- 40 ejemplares disponibles en estantería.
- 18 ejemplares prestados a lectores.
- 4 ejemplares en reparación.
- 5 reservas vigentes pendientes de atención.
- No hay ejemplares ni reservas en otros estados internos.

**Eventos registrados durante la semana:**
- Llegaron 6 ejemplares nuevos desde fuera de la biblioteca y se colocaron en estantería.
- Se prestaron 21 ejemplares disponibles. Cada préstamo transfiere un ejemplar de disponible a prestado.
- Se devolvieron 14 ejemplares prestados y regresaron directamente a disponibles.
- Se enviaron 3 ejemplares disponibles a reparación.
- Se terminaron 2 reparaciones; esos ejemplares volvieron a disponibles.
- Se dio de baja definitivamente 1 ejemplar que estaba en reparación; salió del sistema.
- Se recibieron 17 reservas nuevas.
- Se atendieron y cerraron 12 reservas pendientes mediante préstamos incluidos dentro de los **21 préstamos** anteriores; no son 12 préstamos adicionales.
- Se cancelaron otras 3 reservas pendientes, sin transferencia física adicional.

Los registros son exhaustivos: **no hubo otros ingresos, préstamos, devoluciones, reparaciones, bajas ni cambios de reserva** durante la semana. No conocemos horas exactas de cada evento, motivos de cancelación, identidad de lectores ni los mecanismos causales de demanda.

Construye el modelo mínimo de stocks y flujos; distingue ejemplares físicos de reservas, representa sus transferencias y calcula stocks al cierre. No infieras bucles de retroalimentación observados.
