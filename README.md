# MonitoreoIoC

Sistema distribuido de monitoreo de indicadores de compromiso (IoC) para equipos Linux. Integra detecciones de **LOKI**, solicitudes de **Nagios** y recopilación de información del sistema en un servidor central mediante **gRPC con TLS mutuo (mTLS)**.

El repositorio contiene un prototipo con configuración de laboratorio. Hay funciones pendientes y un error de arranque conocido; consultar la [guía de operación](docs/operacion.md) antes de ejecutarlo.

## Arquitectura en un vistazo

```text
Equipo Linux                       Servidor central
┌─────────────────────┐          ┌─────────────────────────┐
│ communicationClient │─ IoC ───►│ communicationServer     │
│ LOKI + recolector   │─ reporte►│                         │──► SQLite
│                     │◄═estado═►│ Solicitudes de reportes │
└─────────────────────┘          │                         │
                                 │                         │
┌─────────────────────┐          │                         │
│ communicationNagios │─ evento─►│                         │
└─────────────────────┘          │                         │
                                 │                         │
┌─────────────────────┐          │                         │
│ communicationAPI    │─consulta►│                         │
│ Consumidor de datos │◄═ datos ═│ Históricos y novedades  │
└─────────────────────┘          └─────────────────────────┘
```

Las flechas representan llamadas gRPC. El intercambio de estado usa un stream bidireccional; los consumidores reciben datos mediante server streaming.

## Funcionalidades

- Ejecutar LOKI y enviar sus indicadores al servidor.
- Recopilar puertos, conexiones, procesos, usuarios, logs, tareas cron y permisos SUID/SGID.
- Solicitar reportes por detecciones locales, eventos de Nagios o programación global.
- Guardar indicadores y reportes en SQLite y relacionarlos por sus IDs.
- Consultar históricos por IP y rango de fechas.
- Suscribir aplicaciones a nuevos indicadores o reportes.
- Enviar hashes MD5 para una comprobación de integridad cuya comparación todavía está pendiente.

## Documentación

| Guía | Contenido |
|---|---|
| [Arquitectura y flujos](docs/arquitectura.md) | Componentes, secuencias, temporización y límites del diseño actual. |
| [Contrato gRPC](protos/README.md) | RPC, mensajes, ejemplos y regeneración de código Protobuf. |
| [Operación](docs/operacion.md) | Dependencias, configuración, ejecución y diagnóstico. |
| [Certificados](certificates/README.md) | mTLS, archivos utilizados y cifrado de la clave del agente. |
| [Persistencia](docs/persistencia.md) | Tablas esperadas y diferencias respecto de `bd.sql`. |
| [LOKI incluido](Loki-0.45.0/README.md) | Documentación propia de la herramienta incorporada. |

## Mapa del repositorio

| Ruta | Responsabilidad |
|---|---|
| `communicationClient.py` | Agente Linux y recolector de reportes. |
| `communicationServer.py` | Implementación del servicio gRPC y acceso a SQLite. |
| `communicationNagios.py` | Adaptador de eventos de Nagios a gRPC. |
| `communicationAPI.py` | Cliente interactivo de consulta y suscripción; escribe archivos JSON. |
| `protos/communication.proto` | Contrato fuente del servicio. |
| `communication_pb2.py`, `communication_pb2_grpc.py` | Código generado desde el contrato. |
| `certificates/` | Material TLS y configuraciones de solicitudes de certificados. |
| `encript.py`, `decrypt.py` | Utilidades de cifrado y comprobación de la clave privada del agente. |
| `bd.sql` | Esquema parcial histórico; no inicializa la base completa del servidor. |
| `prueba*.py`, `base.py` | Experimentos manuales; no constituyen una suite automatizada. |

## Modelo de confianza

El acceso interno se basa en certificados emitidos por una CA de confianza. El servidor exige certificado de cliente y los clientes certificados comparten el mismo nivel de acceso. No se requiere separación por roles en este modelo.

## Estado y ejecución

El código usa la dirección fija `192.168.4.100:50051`, comandos Linux y una base SQLite en `/usr/local/nagios/libexec/eventhandlers/Base.db`. No hay un instalador ni versiones de dependencias fijadas para el proyecto principal.

La [guía de operación](docs/operacion.md) detalla los preparativos y bloqueos actuales. Esta documentación describe el código revisado; no acredita una ejecución extremo a extremo ni la validez de los certificados incluidos.
