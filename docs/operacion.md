# Guía de operación

[Volver al proyecto](../README.md)

## Entorno esperado

- Python 3 y un entorno Linux para el agente.
- Acceso de red al servidor configurado en `192.168.4.100:50051`.
- Certificados y claves correspondientes, emitidos por la CA aceptada.
- Base SQLite preparada para el servidor.
- Comandos del agente: `hostname`, `cat`, `netstat`, `ss`, `last`, `ps`, `getent`, `cut`, `find`, `ls`, `crontab`, `nohup` y `python3`.
- Permisos para leer los logs y consultar las tareas cron requeridas. La disponibilidad de `/var/log/auth.log`, `/var/log/syslog` y la interfaz `eno1` depende de la distribución.

No hay versiones fijadas ni una matriz de compatibilidad verificada para el proyecto principal. LOKI 0.45.0 tiene dependencias y documentación propias.

## Dependencias Python

Desde la raíz, en Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install grpcio protobuf cryptography
python -m pip install -r Loki-0.45.0/requirements.txt
```

`grpcio-tools` solo es necesario si se va a [regenerar el contrato](../protos/README.md#regenerar-los-archivos-python). `sqlite3` forma parte de Python. Según el entorno, dependencias como `yara-python` pueden requerir preparación adicional; consultar [LOKI](../Loki-0.45.0/README.md).

## Preparación necesaria

### 1. Resolver el listener del servidor

`serve()` contiene `server.add_unsecure_port(...)`, que no existe en gRPC Python estándar. A continuación intenta registrar un listener seguro en la misma dirección.

Para el modelo mTLS del proyecto, el arranque debe registrar el servicio con sus credenciales mediante `add_secure_port(...)`. El código actual necesita corregirse antes de poder ejecutar ese flujo. Esta documentación no aplica esa corrección.

### 2. Preparar SQLite

La ruta utilizada es:

```text
/usr/local/nagios/libexec/eventhandlers/Base.db
```

El directorio debe existir y el proceso debe poder acceder a él. `bd.sql` está incompleto y usa `AUTO_INCREMENT`, sintaxis que SQLite no acepta tal como está escrita. Consultar [persistencia](persistencia.md) para las tablas y columnas esperadas por el código actual.

### 3. Ajustar configuración fija

| Archivo | Configuración a revisar |
|---|---|
| `communicationServer.py` | Dirección de escucha, ruta SQLite y certificados `server100*`. |
| `communicationClient.py` | `ipserver`, interfaz `eno1`, comandos Linux, rutas de logs e intervalos. |
| `communicationAPI.py` | `ipserver`, certificados y `nombreSoftware`, inicialmente `Prueba`. |
| `communicationNagios.py` | `ipserver` y rutas absolutas de certificados bajo `/home/pi1/Downloads/MonitoreoIoC-main/`. |

Verificar la [cadena y la identidad TLS](../certificates/README.md). El agente solicita la clave Fernet del archivo privado cifrado al iniciar.

## Ejecución después de preparar el entorno

Ejecutar cada componente en una terminal o proceso separado. Usar la raíz del repositorio como directorio de trabajo para las rutas relativas.

### Servidor

```bash
python communicationServer.py
```

Registra el servicio, inicia gRPC y espera hasta la terminación del proceso.

### Agente del equipo

```bash
python communicationClient.py
```

Solicita la clave Fernet, prepara mTLS, envía el hash del cliente y abre el stream de estado. El generador lanza LOKI desde el primer ciclo.

El archivo llama a `run()` al final sin guardia `if __name__ == "__main__"`; importarlo también inicia el agente.

### Consumidor de datos

```bash
python communicationAPI.py
```

El menú permite:

1. Recibir nuevos reportes.
2. Recibir nuevos indicadores.
3. Consultar reportes por IP y fechas.
4. Consultar indicadores por IP y fechas.
5. Salir.

Las suscripciones mantienen el proceso esperando mensajes. Las consultas históricas terminan y escriben un JSON. Los archivos se crean en el directorio actual con prefijos `reporte streaming`, `indicador streaming`, `consulta reportes` o `consulta indicadores`.

### Integración Nagios

```bash
python communicationNagios.py 192.168.4.20 HOST DOWN
```

El adaptador interpreta los argumentos como IP, primer dato y segundo dato, y envía `HOST---DOWN` con detector `NAGIOS`. Este ejemplo ilustra la invocación; no existe una configuración de event handler de Nagios incluida que haga automáticamente ese enlace.

## Diagnóstico

| Síntoma | Punto a revisar |
|---|---|
| `AttributeError` sobre `add_unsecure_port` | Bloqueo de arranque descrito arriba. |
| Error al abrir SQLite o `no such table` | Ruta, permisos y esquema completo; también se consulta `Hash` durante el inicio del agente. |
| Falla de handshake / `UNAVAILABLE` | Servidor activo, red, CA, vigencia, correspondencia de certificados y claves e identidad del servidor. |
| Clave Fernet inválida o `InvalidToken` | Clave correspondiente a `host-key-encrypted.pem`. |
| Nagios solicita, pero no llega un reporte inmediatamente | La orden se entrega en el siguiente mensaje de estado del agente. |
| Suscripción tarda en recibir datos | Revisión cada 10 segundos, generación de datos y disponibilidad de trabajadores del servidor. |
| No aparecen datos anteriores en una suscripción | Las suscripciones no hacen replay; usar consultas históricas. |
| Reporte grande rechazado por gRPC | No se configuran límites propios de tamaño; logs completos pueden superar los límites del runtime. |
| Se agota la capacidad de atención | Streams persistentes y pool de 10 trabajadores. |

## Verificación manual del flujo

Con los bloqueos resueltos y en un entorno preparado:

1. Iniciar el servidor y un agente con certificados válidos.
2. Confirmar el resultado de la RPC MD5 y el intercambio de estado. El resultado MD5 no prueba integridad mientras `get_hash()` siga incompleto.
3. Abrir una suscripción de reportes en `communicationAPI.py`.
4. Enviar un evento de Nagios para la IP que declara el agente.
5. Esperar el siguiente ciclo de estado y observar la solicitud y recepción del reporte.
6. Consultar los reportes por esa IP y fecha y revisar el JSON de salida.

Los scripts `prueba*.py` son experimentos independientes con rutas y esquemas históricos. No hay una suite automatizada de integración. Los pasos anteriores describen una comprobación propuesta; no se ejecutaron como parte de esta documentación.
