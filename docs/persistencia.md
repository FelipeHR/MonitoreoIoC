# Persistencia y esquema esperado

[Volver al proyecto](../README.md) · [Operación](operacion.md)

El servidor usa `sqlite3` y abre conexiones a:

```text
/usr/local/nagios/libexec/eventhandlers/Base.db
```

No hay migraciones ni un inicializador completo de base de datos en el repositorio. Esta guía describe el contrato de almacenamiento inferido de las consultas de `communicationServer.py`; no es un esquema de una base desplegada inspeccionada.

## Tablas utilizadas

| Tabla | Columnas referenciadas | Uso |
|---|---|---|
| `Reporte` | `Id_reporte`, `Fecha`, `Hora`, `Datos` | Reporte JSON y fecha/hora de recepción. El ID se obtiene con `lastrowid`. |
| `Indicador` | `Id_indicador`, `Descripcion`, `Detector`, `Origen`, `Fecha`, `Hora` | Indicador y fecha/hora derivada de su timestamp. El ID se obtiene con `lastrowid`. |
| `Host_Reporte` | `IP`, `Id_reporte` | Asociación entre equipo y reporte. |
| `Host_Indicador` | `IP`, `Id_indicador` | Asociación entre equipo e indicador. |
| `Reporte_Indicador` | `Id_indicador`, `Id_reporte` | Relación explícita solicitada mediante `SaveIndicatorReport`. |
| `Hash` | `Origen` y columnas de referencia no definidas completamente | `get_hash()` ejecuta `SELECT * ... WHERE Origen=?`; la comparación está comentada. |

`Host(IP, MAC)` aparece en `bd.sql`, pero el servidor actual no inserta ni consulta esa tabla. El agente lee su MAC, pero no la envía en los mensajes del contrato actual.

## Relaciones lógicas

```text
Host / IP ──< Host_Reporte >──── Reporte
                                  │
                           Reporte_Indicador
                                  │
Host / IP ──< Host_Indicador >── Indicador
```

El diagrama muestra asociaciones previstas, no garantiza restricciones efectivamente activas. El servidor no ejecuta `PRAGMA foreign_keys = ON` al abrir las conexiones.

## Escrituras

### Reporte

1. `SubmitReport` toma la fecha y hora del servidor.
2. Inserta `Reporte(Fecha, Hora, Datos)`.
3. Inserta `Host_Reporte(IP, Id_reporte)`.
4. Devuelve el ID al agente.

### Indicador LOKI / MD5 recibido por RPC

1. `IndicatorReport` convierte el timestamp Unix del mensaje a fecha y hora local del servidor.
2. Inserta `Indicador(Descripcion, Detector, Origen, Fecha, Hora)`.
3. Inserta `Host_Indicador(IP, Id_indicador)`.
4. Devuelve el ID al agente.

### Asociación

El agente llama a `SaveIndicatorReport` con los IDs recibidos y el servidor inserta una fila en `Reporte_Indicador`.

Cada función auxiliar de inserción hace su propio `commit()`. Las escrituras de una entidad y su asociación con el host no forman una única transacción atómica en la implementación actual.

## Consultas históricas

- Indicadores: filtro directo por `Origen` y `Fecha >= inicio AND Fecha <= fin`.
- Reportes: primero se buscan los IDs en `Host_Reporte`, luego se consulta cada reporte y su rango de fechas.
- Los filtros usan la fecha de almacenamiento, no el campo `TimeStamp` interno del JSON del reporte.
- No se usa `ORDER BY`; el orden cronológico no está garantizado. Después, el handler extrae resultados con `pop()`.

## Diferencias respecto de los archivos históricos

`bd.sql` solo define `Host`, `Reporte` y `Host_Reporte`. Faltan las tablas de indicadores, asociaciones y hashes utilizadas por el servidor. Además, `AUTO_INCREMENT` no es sintaxis válida de SQLite tal como aparece allí.

`pruebaBD.py` utiliza variantes como `Reporte.Error` e `Indicador_Reporte` que no coinciden con el servidor actual. `base.py` consulta otra base (`data/portal_mammals.sqlite`) y no inicializa el almacenamiento de MonitoreoIoC.

Antes de desplegar, preparar y validar un esquema compatible con el servidor. El repositorio no permite reconstruir con certeza las columnas originales de referencia de `Hash` a partir de la comparación incompleta.
