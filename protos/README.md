# Contrato gRPC

[Volver al proyecto](../README.md)

`communication.proto` es la fuente del contrato de comunicación. Usa **proto3**, paquete **`greet`** y servicio **`Communication`**. El nombre completo de un método tiene la forma `/greet.Communication/SubmitReport`.

## Modalidades de llamada

```text
Unary                  cliente ── petición ──► servidor
                               ◄─ respuesta ──

Bidireccional          cliente ══ estados ═══► servidor
                               ◄═ órdenes ════

Server streaming       cliente ── petición ──► servidor
                               ◄═ resultado 1
                               ◄═ resultado 2 ...
```

| RPC | Modalidad | Entrada → salida | Comportamiento actual |
|---|---|---|---|
| `SubmitReport` | Unary | `ReportMessage` → `ServerMessage` | Guarda el reporte, lo encola para consumidores y devuelve su ID como texto. |
| `IndicatorReport` | Unary | `IndicatorMessage` → `ServerMessage` | Para LOKI/MD5 guarda y distribuye el indicador; para NAGIOS encola una solicitud de reporte. |
| `SaveIndicatorReport` | Unary | `ReportXIndicator` → `ServerMessage` | Inserta la relación entre indicador y reporte. |
| `ServerComprobationMD5` | Unary | `ComprobationMD5` → `ServerMessage` | Recibe un hash; la función de comparación actualmente devuelve siempre `True`. |
| `BidirectionalCommunication` | Bidireccional | `stream ClientMessage` → `stream ServerMessage` | Recibe estados del agente y devuelve instrucciones. |
| `StreamingServerIndicator` | Server streaming | `SoftwareMessage` → `stream IndicatorMessage` | Entrega nuevos indicadores al suscriptor. |
| `StreamingServerReport` | Server streaming | `SoftwareMessage` → `stream ReportMessage` | Entrega nuevos reportes al suscriptor. |
| `IndicatorRequest` | Server streaming | `SpecificRequest` → `stream IndicatorMessage` | Consulta indicadores por IP y fechas; termina al agotar resultados. |
| `ReportRequest` | Server streaming | `SpecificRequest` → `stream ReportMessage` | Consulta reportes por IP y fechas; termina al agotar resultados. |

No existe una RPC de client streaming puro.

## Mensajes

Todos los campos actuales son `string`.

| Mensaje | Campos | Convención utilizada |
|---|---|---|
| `ClientMessage` | `ip`, `message` | IP declarada y estado textual. |
| `ServerMessage` | `message` | Instrucción, confirmación, resultado o ID según el método. |
| `SoftwareMessage` | `name` | Clave de registro del consumidor en las listas del servidor. |
| `ReportMessage` | `ip`, `json` | Reporte completo serializado como JSON dentro de texto. |
| `IndicatorMessage` | `ip`, `timestamp`, `indicator`, `detector` | Detector esperado: `LOKI`, `MD5` o `NAGIOS`. |
| `ReportXIndicator` | `idReport`, `idIndicator` | IDs recibidos previamente del servidor. |
| `ComprobationMD5` | `ip`, `md5`, `archive` | El agente envía `archive="client"`; su función de hash también contempla `loki`. |
| `SpecificRequest` | `ip`, `start`, `end` | Las consultas existentes utilizan fechas `YYYY-MM-DD`, con ambos extremos incluidos. |

### Convenciones que debe conocer un consumidor

- Al enviar un indicador, `timestamp` debe contener segundos Unix convertidos a texto: el servidor ejecuta `float(timestamp)`.
- En indicadores históricos, el servidor devuelve `timestamp` como fecha y hora concatenadas, no como segundos Unix. El formato no es uniforme entre suscripción e histórico.
- LOKI envía `indicator` como JSON; Nagios envía texto separado por `---` y lo utiliza para solicitar un reporte.
- Protobuf valida el sobre, pero no la estructura del JSON ni las instrucciones textuales.
- Los detectores distintos de los contemplados no tienen una respuesta válida implementada.

## Protocolo de estado del agente

| Estado / condición | Respuesta del servidor | Acción del agente |
|---|---|---|
| `Tengo un problema` | `Dame tu reporte` | `reporte("LOKI")` |
| Ventana de reporte global activa | `Solicitud de reporte global` | `reporte("GLOBAL")` |
| IP pendiente en cola de Nagios | `NAGIOS solicita tu reporte` | `reporte("NAGIOS")` |
| IP pendiente en cola MD5 | `Server solicita tu reporte` | `reporte("MD5")` |
| IP pendiente de cierre | `Cerrar conexion` | Cierra el canal. |
| `No pasa nada`, sin solicitudes pendientes | `Ok` | Continúa. |
| Otro mensaje, sin solicitudes pendientes | `No te entiendo` | No tiene una acción específica. |

El orden de la tabla refleja la prioridad de `comprobar()`. El servidor responde a cada mensaje recibido: no hay un productor independiente de instrucciones en este stream. Los reportes se envían por `SubmitReport`, fuera del stream de estado.

## Ejemplo de consulta histórica

Ejecutar desde la raíz, con certificados válidos y un servidor operativo:

```python
from pathlib import Path
import grpc
import communication_pb2 as messages
import communication_pb2_grpc as services

credentials = grpc.ssl_channel_credentials(
    root_certificates=Path("certificates/ca.pem").read_bytes(),
    private_key=Path("certificates/clientNagios-key.pem").read_bytes(),
    certificate_chain=Path("certificates/clientNagios.pem").read_bytes(),
)

with grpc.secure_channel("192.168.4.100:50051", credentials) as channel:
    stub = services.CommunicationStub(channel)
    request = messages.SpecificRequest(
        ip="192.168.4.20", start="2026-10-01", end="2026-10-30"
    )
    for report in stub.ReportRequest(request, timeout=30):
        print(report.ip, report.json)
```

El timeout del ejemplo limita la llamada completa; ajustar según el volumen de resultados. El servidor introduce una pausa de un segundo entre resultados históricos.

## Regenerar los archivos Python

Desde la raíz, dentro del entorno Python del proyecto:

```bash
python -m pip install grpcio grpcio-tools protobuf
python -m grpc_tools.protoc -I protos --python_out=. --grpc_python_out=. protos/communication.proto
```

Se generan o reemplazan estos archivos en la raíz:

- `communication_pb2.py`: clases y serialización de mensajes.
- `communication_pb2_grpc.py`: stub de cliente, clase base del servicio y registro de handlers.

No editar manualmente el código generado. Revisar el diff después de regenerar y mantener compatibles las versiones del generador y del runtime. Conservar los números de campo existentes al evolucionar el contrato; no reutilizar números retirados.

## Límites actuales del streaming

Las suscripciones revisan listas en memoria cada 10 segundos y extraen con `pop()` (último en entrar, primero en salir). No incluyen replay, confirmaciones ni almacenamiento persistente de pendientes. El nombre del software identifica la lista: conexiones con el mismo nombre pueden sobrescribirla o compartirla. Los bucles de suscripción tampoco comprueban explícitamente `context.is_active()`.

Más contexto en [arquitectura](../docs/arquitectura.md) y [operación](../docs/operacion.md).
