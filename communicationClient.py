import communication_pb2_grpc
import communication_pb2
import grpc
import subprocess
import json
import time
from os import remove 
credentials = grpc.ssl_channel_credentials(open('certificates/ca.pem','rb').read(),
    open('certificates/host-key.pem','rb').read(),open('certificates/host.pem','rb').read())

ipserver = '192.168.4.100:50051' 
ip = subprocess.getoutput("hostname -I").split(' ')[0]
mac = subprocess.getoutput("cat /sys/class/net/eno1/address")
channel = grpc.secure_channel(ipserver,credentials)
stub = communication_pb2_grpc.CommunicationStub(channel)
tiempoLog = -1 
tiempoReporte = 20
tiempoLoki = 120
def get_client_stream_requests():
    while True:
        mensaje = comprobarIndicador()
        request = communication_pb2.ClientMessage(ip = ip, message = mensaje)
        yield request
        time.sleep(60)

def comprobarIndicador():
    if tiempoLog == -1 or (tiempoLog >= 0 and tiempoLog < tiempoReporte):
        return "No pasa nada"
    elif tiempoLog > 20:
        try:
            file = open("log.txt")
            line = file.readline()
            j = 1
            while line!= "":
                request = communication_pb2.IndicatorMessage(ip = ip, timestamp = str(time.time()), indicator = line, detector = "LOKI")
                reply = stub.IndicatorReport(request)
                print("Se recibio el indicador numero "+str(j))
                line = file.readline()
                j += 1
            file.close()
            remove("log.txt")
            return ("Tengo un problema")
        except FileNotFoundError:
            return ("No pasa nada")
        tiempoLog = -1


def reporte(problem): 
    info = {}
    subprocess.run("export LC_ALL=C", shell = True, check = True)
    info["lastConnections"] = {}
    info["lastConnections"]["Established"] = subprocess.getoutput("netstat -antup | grep 'ESTABLISHED'").split('\n')
    info["lastConnections"]["Listen"] = subprocess.getoutput("netstat -antup | grep 'LISTEN'").split('\n')
    info["lastConnections"]["Others"] = subprocess.getoutput("netstat -antup | grep 'TIME_WAIT'").split('\n')
    info["lastConnectionsSSH"] = subprocess.getoutput("ss | grep ssh").split('\n')
    info["lastUsers"] = subprocess.getoutput("last").split('\n')
    info["processes"] = subprocess.getoutput("ps auxf").split('\n')
    info["AuthLogs"] = subprocess.getoutput("cat /var/log/auth.log").split('\n')
    info["SysLogs"] = subprocess.getoutput("cat /var/log/syslog").split('\n') #Datos de actividad del sistema
    info["RootKits"] = subprocess.getoutput("chkrootkit -q").split('\n')
    info["sudoers"] = subprocess.getoutput("getent group sudo | cut -d: -f4").split('\n')
    suid = {}
    for i in subprocess.getoutput("find . -perm /6000").split("\n"): #Se guardan los archivos
        line = subprocess.getoutput("ls -l "+i[2:]).split('\n')
        suid[i[2:]] = line
    info["SUID-SGID"] = suid
    info["TimeStamp"] = time.strftime("%c")
    crontabs = {}
    for i in getUsers():
        line = subprocess.getoutput("crontab -u "+i+" -l")
        crontabs[i] = line
    info["crontabs"] = crontabs
    data = json.dumps(info)
    request = communication_pb2.ReportMessage(ip = ip, json = data)
    reply = stub.SubmitReport(request)
    print(reply)
    

def run():       
    responses = stub.BidirectionalCommunication(get_client_stream_requests())
    for response in responses:
        print("Respuesta: " + response.message)
        if response.message == "Dame tu reporte":
            reporte(response.problem)


def getUsers():
	command = subprocess.getoutput("cut -d: -f1 /etc/passwd").split("\n")
	return command

    


run()

