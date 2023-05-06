from concurrent import futures
import time
from datetime import datetime
import json
import sys

import grpc
import communication_pb2
import communication_pb2_grpc

import sqlite3
from sqlite3 import Error
import subprocess

from timeit import default_timer

global tiempoMaximoReporte
tiempoMaximoReporte = 3
global tiempoReporte
tiempoReporte = None

global reporteGlobalTiempo 
reporteGlobalTiempo = 240
global reporteGlobal
reporteGlobal = time.time()/60 + (reporteGlobalTiempo - 5)
#A los 5 minutos de que empieza a correr el servidor, le pedira un reporte a todos los clientes conectados
#la siguiente peticion sera despues de reporteGlobalTiempo minutos


global colaReportesNagios 
colaReportesNagios = []



'''

1.- cambiar mensaje de respuesta del servidor cuando el indicador es enviado por nagios(detector) 

2.- mientras no termine el tiempo para mandar a pedir reportes, acumular los indicadores encontrados
    por nagios para despues asociar los reportes e indicadores

3.- 

'''

# --------------------- BASE DE DATOS ---------------------
def create_connection(db_file):
   
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Error as e:
        print(e)

    return conn


def create_reporte(conn, datos):

    sql = ''' INSERT INTO Reporte(Fecha, Hora, Datos)
              VALUES(?,?,?) '''

    
    cur = conn.cursor()
    cur.execute(sql, datos)
    conn.commit()

    return cur.lastrowid


def create_indicador(conn, datos):
    
    sql = ''' INSERT INTO Indicador(Descripcion, Detector, Origen, Fecha, Hora)
              VALUES(?,?,?,?,?) '''

    cur = conn.cursor()
    cur.execute(sql, datos)
    conn.commit()

    return cur.lastrowid


def create_host_reporte(conn, datos):
    # datos = (ip, id_reporte)

    sql = ''' INSERT INTO Host_Reporte(IP, Id_reporte)
              VALUES(?,?) '''

    cur = conn.cursor()
    cur.execute(sql, datos)
    conn.commit()


def create_host_indicador(conn, datos):
    # datos = (ip, id_reporte)
    sql = ''' INSERT INTO Host_Indicador(IP, Id_indicador)
              VALUES(?,?) '''


    cur = conn.cursor()
    cur.execute(sql, datos)
    conn.commit()


def create_reporte_indicador(conn, datos):
    # datos = (ip, id_reporte)
    sql = ''' INSERT INTO Reporte_Indicador(Id_indicador, Id_reporte)
              VALUES(?,?) '''

    cur = conn.cursor()
    cur.execute(sql, datos)
    conn.commit()


def guardarReporte(origen, fecha, hora, datos):
    
    database = "/usr/local/nagios/libexec/eventhandlers/Base.db"
    conn = create_connection(database)

    with conn: 

        d = datetime.now()
        
        #da = json.load(Dir)
        #dat = json.dumps(datos)

        # Guarda Reporte
        datos_reporte = (fecha, hora, dat)
        id_reporte = create_reporte(conn, datos_reporte)

        # Relaciona reporte con host
        datos_host_reporte = (origen, id_reporte)
        create_host_reporte(conn, datos_host_reporte)

    conn.close()

    return id_reporte


def guardarIndicador(descripcion, detector, origen, fecha, hora):

    database = "/usr/local/nagios/libexec/eventhandlers/Base.db"
    conn = create_connection(database)

    with conn: 
    
        # Guarda Indicador
        datos_indicador = (descripcion, detector, origen, fecha, hora)
        id_indicador = create_indicador(conn, datos_indicador)

        # Asocia Indicador con Host
        datos_host_indicador = (origen, id_indicador)
        create_host_indicador(conn, datos_host_indicador)

    conn.close()

    return id_indicador




# ---------------------------------------------------------

def asociarIDLoki(id_indicador, id_reporte):

    database = "/usr/local/nagios/libexec/eventhandlers/Base.db"
    conn = create_connection(database)

    datos_reporte_indicador = (id_indicador, id_reporte)
    create_reporte_indicador(conn, datos_reporte_indicador)



# ------------------ TIEMPO ------------------

'''
def comprobarTiempo(tiempo, tiempoMax, esIndicador):

    retorno = None

    if tiempo != None and tiempo + tiempoMax > time.time()/60:
        
        if esIndicador:

            asociarIDNagios()

            return (time.time()/60)

        else:

            return None 
    

    elif tiempo == None and esIndicador:

        return (time.time()/60) 


    else :

        return tiempo    
'''
# --------------------------------------------


class CommunicationServicer(communication_pb2_grpc.CommunicationServicer):
    

    def SubmitReport(self, request, context):

        print("\nSubmitReport()\n")


        d = datetime.now()

        Fecha  = str(d.date())
        Hora   = str(d.time())
             
        id_reporte = guardarReporte(request.ip, Fecha, Hora, request.json)

        print("\nSe recibio el reporte\n")

        #si es string
        dic = json.loads(request.json)
        

        serverReply = communication_pb2.ServerMessage()
        serverReply.message = str(id_reporte)

        return serverReply
    


    def BidirectionalCommunication(self, request_iterator, context):
        entregarReporte = None

        for request in request_iterator:
            mensaje, tiempoInicial = comprobar(request.message, entregarReporte, request.ip)
            print("Solicitud de "+request.ip+": "+request.message + "; Tiempo de reporte: " + str(tiempoInicial))
            serverReply = communication_pb2.ServerMessage()
            serverReply.message = mensaje
            #serverReply.problem = request.problem
            yield serverReply



    def IndicatorReport(self, request, context):

        tsIndicator = request.timestamp
        stamp = str(datetime.fromtimestamp(float(tsIndicator)))
        FyH = stamp.split()
        fechaIndicator = FyH[0]
        horaIndicator = FyH[1]


        if request.detector == "LOKI":

            id_indicador = guardarIndicador(request.indicator, request.detector, request.ip, fechaIndicator, horaIndicator)
            print("Se recibio el indicador: ")

            serverReply = communication_pb2.ServerMessage()
            serverReply.message = str(id_indicador)


        if request.detector == "NAGIOS":
            colaReportesNagios.append(request.ip)
            serverReply = communication_pb2.ServerMessage()
            serverReply.message = "Se pediran los reportes"

        return serverReply


    def SaveIndicatorReport(self, request, context):

        idReporte = request.idReport
        idIndicador = request.idIndicator

        asociarIDLoki(idIndicador, idReporte)

        serverReply = communication_pb2.ServerMessage()
        serverReply.message = "Se asociaron " + idReporte + " - " + idIndicador

        return serverReply

def verificarReporteGlobal(reporte):
    global reporteGlobal
    global reporteGlobalTiempo
    global tiempoReporte
    global tiempoMaximoReporte

    if reporteGlobal < time.time()/60 - reporteGlobalTiempo:
        tiempoReporte = time.time()/60
        reporteGlobal = time.time()/60 
    
    if tiempoReporte != None:
        if time.time()/60 - tiempoReporte > tiempoMaximoReporte:
            tiempoReporte = None
            return None

        if reporte == None :
            return True
        
        else:
            return False        
        
    return None


def  comprobar(mensaje, reporte, ip):
    global colaReportesNagios
    #tiempoMaximoReporte es el tiempo maximo para solicitarle reportes a las demas maquinas

    reporte = verificarReporteGlobal(reporte)

    if mensaje == "Tengo un problema":
        return "Dame tu reporte", reporte 
    
    else:
        if (reporte):
            return "Solicitud de reporte global", reporte 

        if ip in colaReportesNagios:
            colaReportesNagios.remove(ip)
            return "NAGIOS solicita tu reporte", reporte
    
        elif mensaje == "No pasa nada":
            return "Ok", reporte 

        else:
            return "No te entiendo", reporte 



def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10)) #10 solicitudes simultaneas como maximo (conjunto de subprocesos que ejecutan tareas de forma concurrente (varias al mismo tiempo))
    communication_pb2_grpc.add_CommunicationServicer_to_server(CommunicationServicer(), server)
    credentials = grpc.ssl_server_credentials( [    (open('certificates/server100-key.pem', 'rb').read(), open('certificates/server100.pem', 'rb').read())], root_certificates=open('certificates/ca.pem', 'rb').read(), require_client_auth=True)
    server.add_secure_port("192.168.4.100:50051", credentials)
    server.start()
    print("Server Started")
    server.wait_for_termination()



if __name__ == "__main__":
    serve()
