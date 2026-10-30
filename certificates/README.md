# Certificados y TLS mutuo

[Volver al proyecto](../README.md)

El proyecto utiliza **mTLS** para su comunicación interna gRPC. La pertenencia al entorno de confianza se acredita mediante un certificado emitido por la CA aceptada; todos los clientes certificados tienen el mismo nivel de acceso previsto por el diseño.

```text
Cliente                                  Servidor
   │                                         │
   │◄──── Certificado del servidor ───────────┤
   │      Cliente lo valida con ca.pem        │
   │                                         │
   ├───── Certificado del cliente ───────────►│
   │      Servidor lo valida con ca.pem       │
   │                                         │
   │◄══════ Canal TLS para llamadas gRPC ════►│
```

## Archivos utilizados por el código

| Componente | CA | Certificado | Clave privada |
|---|---|---|---|
| Servidor | `ca.pem` | `server100.pem` | `server100-key.pem` |
| Agente | `ca.pem` | `host.pem` | Descifrada desde `host-key-encrypted.pem`. |
| Cliente API | `ca.pem` | `clientNagios.pem` | `clientNagios-key.pem` |
| Adaptador Nagios | `ca.pem` | `clientNagios.pem` | `clientNagios-key.pem` |

Las rutas son relativas a la raíz salvo en `communicationNagios.py`, que contiene rutas absolutas de un entorno anterior. El servidor configura `require_client_auth=True`.

Otros archivos `server84*`, `server98*`, `server99*` y `serverNagios*` están presentes, pero no son los seleccionados por el servidor actual.

## Tipos de archivo

- `*.pem`: certificados, claves o contenido cifrado; el nombre determina su uso en este repositorio.
- `*.csr`: solicitudes de firma de certificado.
- `*-csr.json`: parámetros de solicitudes de certificado.
- `ca-config.json`: perfil de firma con usos `server auth` y `client auth`, y expiración configurada de `8760h`.

El JSON de solicitud `server-csr.json` contiene un CN histórico `192.168.4.84`. No demuestra la identidad ni los SAN del certificado `server100.pem`: para eso se debe inspeccionar el certificado real.

## Clave cifrada del agente

`encript.py` lee `host-key.pem`, genera una clave Fernet, escribe `host-key-encrypted.pem` e imprime la clave Fernet necesaria para descifrarlo.

```bash
python encript.py
```

Este comando **sobrescribe el archivo cifrado** y genera una clave Fernet nueva en cada ejecución. Conservar la clave correspondiente al archivo desplegado.

Al arrancar, `communicationClient.py` solicita esa clave, descifra el archivo en memoria y pasa la clave privada a `grpc.ssl_channel_credentials`. No necesita escribir el contenido descifrado a disco durante ese arranque.

`decrypt.py` es una comprobación manual: solicita la clave Fernet y compara el contenido descifrado con el archivo local `host-key.pem` usando hashes MD5. No emite certificados ni configura TLS.

## Comprobaciones con OpenSSL

Desde la raíz del proyecto:

```bash
openssl x509 -in certificates/server100.pem -noout -subject -issuer -dates -ext subjectAltName
openssl verify -CAfile certificates/ca.pem certificates/server100.pem certificates/host.pem certificates/clientNagios.pem
```

El certificado del servidor debe corresponder a la dirección utilizada por el cliente, actualmente `192.168.4.100`. Verificar cadena, vigencia e identidad si falla el handshake. Estos comandos no prueban que las claves privadas correspondan a los certificados ni que el servicio esté operativo.

## Manejo del material

La carpeta contiene claves privadas, incluida la de la CA. Son material sensible: distribuir a cada componente únicamente los archivos que necesita y mantener la clave de la CA bajo control del emisor. Si este material se compartió fuera del entorno de confianza, sustituirlo antes de reutilizarlo en otro despliegue.

La documentación no reproduce claves privadas ni claves Fernet. No se ha validado la vigencia de los certificados incluidos.
