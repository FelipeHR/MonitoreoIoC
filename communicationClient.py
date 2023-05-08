import communication_pb2_grpc
import communication_pb2
import grpc
import subprocess
import json
import time
import hashlib
from cryptography.fernet import Fernet
from os import remove 


global ipserver
ipserver = '192.168.4.100:50051'
global ip
ip = subprocess.getoutput("hostname -I").split(' ')[0]
global mac
mac = subprocess.getoutput("cat /sys/class/net/eno1/address")
global channel
channel = ""
global stub
stub = ""
global tiempoLog
tiempoLog = -1
global tiempoReporte
tiempoReporte = 20
global tiempoLoki
tiempoLoki = 120
global contadorTiempoLoki
contadorTiempoLoki = 0
global indicadores
indicadores = []

def get_client_stream_requests():
    global contadorTiempoLoki
    global tiempoLoki
    global tiempoLog
    global ip

    while True:
        if contadorTiempoLoki % tiempoLoki == 0:
            ejecutarLoki()
            tiempoLog = 0
        
        mensaje = comprobarIndicador()
        request = communication_pb2.ClientMessage(ip = ip, message = mensaje)
        contadorTiempoLoki += 1
        yield request
        time.sleep(60)

def comprobarIndicador():
    global tiempoLog
    global tiempoReporte
    global ip
    global stub
    global indicadores
    if tiempoLog == -1 or (tiempoLog >= 0 and tiempoLog < tiempoReporte):
        if tiempoLog != -1:
            tiempoLog += 1
        return "No pasa nada"
    
    elif tiempoLog >= tiempoReporte:
        try:
            file = open("log.txt")
            line = file.readline()

            while line!= "":
                request = communication_pb2.IndicatorMessage(ip = ip, timestamp = str(time.time()), indicator = line, detector = "LOKI")
                reply = stub.IndicatorReport(request)
                indicadores.append(reply.message)
                line = file.readline()
            file.close()
            remove("log.txt")
            return ("Tengo un problema")
        except FileNotFoundError:
            return ("No pasa nada")
        tiempoLog = -1

def reporte(detector):
    global ip
    global stub
    global mac
    global indicadores
    info = {}
    subprocess.run("export LC_ALL=C", shell = True, check = True)
    info["OpenPorts"] = subprocess.getoutput("netstat -tulpna").split('\n')
    info["LastConnections"] = {}
    info["LastConnections"]["Established"] = subprocess.getoutput("netstat -antup | grep 'ESTABLISHED'").split('\n')
    info["LastConnections"]["Listen"] = subprocess.getoutput("netstat -antup | grep 'LISTEN'").split('\n')
    info["LastConnections"]["Others"] = subprocess.getoutput("netstat -antup | grep 'TIME_WAIT'").split('\n')
    info["LastConnectionsSSH"] = subprocess.getoutput("ss | grep ssh").split('\n')
    info["LastUsers"] = subprocess.getoutput("last").split('\n')
    info["Processes"] = subprocess.getoutput("ps auxf").split('\n')
    info["AuthLogs"] = subprocess.getoutput("cat /var/log/auth.log").split('\n')
    info["SysLogs"] = subprocess.getoutput("cat /var/log/syslog").split('\n') #Datos de actividad del sistema
    #info["RootKits"] = subprocess.getoutput("chkrootkit -q").split('\n')
    info["sudoers"] = subprocess.getoutput("getent group sudo | cut -d: -f4").split('\n')
    suid = {}
    for i in subprocess.getoutput("find . -perm /6000").split("\n"): #Se guardan los archivos
        line = subprocess.getoutput("ls -l "+i[2:]).split('\n')
        suid[i[2:]] = line
    info["SUID-SGID"] = suid
    info["TimeStamp"] = time.strftime("%c")
    info["Detector"] = detector
    crontabs = {}
    for i in getUsers():
        line = subprocess.getoutput("crontab -u "+i+" -l")
        crontabs[i] = line
    info["Crontabs"] = crontabs
    data = json.dumps(info)
    request = communication_pb2.ReportMessage(ip = ip, json = data)
    reply = stub.SubmitReport(request)
    report = reply.message
    while bool(indicadores):
        indicador = indicadores.pop()
        print(report)
        save = communication_pb2.ReportXIndicator(idReport = report, idIndicator = indicador)
        replySave = stub.SaveIndicatorReport(save)


def hashComprobation(archivo):
    ruta = ""
    if archivo == "client":
        ruta = "communicationClient.py"
    elif archivo == "loki":
        ruta = "Loki-0.45.0/loki.py"
    
    with open(ruta,"rb") as f:
        text = f.read()
        md5 = hashlib.md5(text).hexdigest()

    return md5

def run():
    global ipserver
    global ip
    llave = input() #Se pide la llave para desencriptar la clave privada
    f = Fernet(llave) #Se crea el objeto de la llave
    with open("certificates/host-key-encrypted.pem","rb") as encrypted_file:
        encrypted = encrypted_file.read() #Se lee el archivo encriptado
    decrypted =  f.decrypt(encrypted) #Se desencripta el archivo
    credentials = grpc.ssl_channel_credentials(open('certificates/ca.pem','rb').read(),
    decrypted,open('certificates/host.pem','rb').read()) #Se crean las credenciales
    global channel
    channel = grpc.secure_channel(ipserver,credentials)
    global stub
    stub = communication_pb2_grpc.CommunicationStub(channel)
    
    mensajeMD5 = communication_pb2.ComprobationMD5(ip = ip, md5 = hashComprobation("client"), archive = "client")

    serverReply = stub.ServerComprobationMD5(mensajeMD5)
    
    if serverReply != "El archivo no ha sido modificado":
        indicadores.append(serverReply)
    
    print(serverReply)
    
    responses = stub.BidirectionalCommunication(get_client_stream_requests())
    for response in responses:
        print("Respuesta: " + response.message)

        if response.message == "Dame tu reporte":
            reporte("LOKI")

        elif response.message == "Solicitud de reporte global":
            reporte("GLOBAL")
            
        elif response.message == "NAGIOS solicita tu reporte":
            reporte("NAGIOS")

        elif response.message == "Servidor solicita tu reporte":
            reporte("MD5")
        
        elif response.message == "Cerrar conexion":
            print("Se cerrara la conexion")
            channel.close()
            break


def getUsers():
	command = subprocess.getoutput("cut -d: -f1 /etc/passwd").split("\n")
	return command

def ejecutarLoki():
    print("Se ejecutara un analisis")
    subprocess.run("nohup python3 Loki-0.45.0/loki.py --onlyrelevant -l log.txt &", shell = True, check = True)    

run()

