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
global tiempoMaximoIndicador
tiempoMaximoIndicador = 2
global tiempoIndicador
tiempoIndicador = None
global tiempoReporte
tiempoReporte = None

global cola_id_indicadores
cola_id_indicadores = []

global cola_id_reportes
cola_id_reportes = []



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


def asociarIDNagios():

    global cola_id_reportes
    global cola_id_indicadores


    database = "/usr/local/nagios/libexec/eventhandlers/Base.db"
    conn = create_connection(database)

    for reporte in cola_id_reportes:

        for indicador in cola_id_indicadores:

            datos_reporte_indicador = (indicador, reporte)
            create_reporte_indicador(conn, datos_reporte_indicador)

    conn.close()

    cola_id_reportes = []
    cola_id_indicadores = []

# ------------------ TIEMPO ------------------

def setTiempoIndicador():

    global tiempoMaximoIndicador
    global tiempoIndicador

    #elif (default_timer() - tiempoIndicador)/60 <= tiempoMaximoIndicador:

    if tiempoIndicador != None and (time.time() - tiempoIndicador)/60 > tiempoMaximoIndicador:   
        asociarIDNagios()
        tiempoIndicador = time.time()
    elif tiempoIndicador == None:
        tiempoIndicador = time.time()
    #tiempoIndicador = default_timer()

def verificarTiempoIndicador():

    global tiempoMaximoIndicador
    global tiempoIndicador

    if tiempoIndicador == None or (tiempoIndicador != None and (time.time() - tiempoIndicador)/60 > tiempoMaximoIndicador):
        tiempoIndicador = None
        return False
    return True
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

        global cola_id_reportes

        d = datetime.now()

        Fecha  = str(d.date())
        Hora   = str(d.time())
             
        id_reporte = guardarReporte(request.ip, Fecha, Hora, request.json)

        print("\nSe recibio el reporte\n")

        #si es string
        dic = json.loads(request.json)
        
        if dic['Detector'] == "NAGIOS":

            cola_id_reportes.append(id_reporte)

        serverReply = communication_pb2.ServerMessage()
        serverReply.message = str(id_reporte)

        return serverReply
    


    def BidirectionalCommunication(self, request_iterator, context):
        tiempoInicial = None
        for request in request_iterator:
            mensaje, tiempoInicial = comprobar(request.message, tiempoInicial)
            print("Solicitud de "+request.ip+": "+request.message + "; Tiempo de reporte: " + str(tiempoInicial))
            serverReply = communication_pb2.ServerMessage()
            serverReply.message = mensaje
            #serverReply.problem = request.problem
            yield serverReply



    def IndicatorReport(self, request, context):

        global tiempoIndicador
        global tiempoMaximoIndicador
        global cola_id_indicadores

        tsIndicator = request.timestamp
        stamp = str(datetime.fromtimestamp(float(tsIndicator)))
        FyH = stamp.split()
        fechaIndicator = FyH[0]
        horaIndicator = FyH[1]


        if request.detector == "LOKI":

            id_indicador = guardarIndicador(request.indicator, request.detector, request.ip, fechaIndicator, horaIndicator)
            print("Se recibio el indicador: " + str (tiempoIndicador))

            serverReply = communication_pb2.ServerMessage()
            serverReply.message = str(id_indicador)


        if request.detector == "NAGIOS":
            

            setTiempoIndicador()
            #cola_id_indicadores.append(id_indicador)

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



def  comprobar(mensaje, tiempo):
    #Comprobamos si termino el tiempo de pedida de reporte por Nagios
    #global tiempoIndicador
    #tiempoIndicador es el tiempo desde que se empezo a solicitar reportes (si no hay reportes es None)
    #global tiempoMaximoIndicador
    #tiempoMaximoIndicador es el tiempo maximo para no volver a perdir reportes desde nagios
    global tiempoMaximoReporte
    #tiempoMaximoReporte es el tiempo maximo para solicitarle reportes a las demas maquinas
    if tiempo!= None and (time.time()-tiempo)/60 > tiempoMaximoReporte:
        tiempo = None

    print("Comprobamos: "+ str(verificarTiempoIndicador()) + " " + str(tiempo)) 
    if mensaje == "Tengo un problema":
        return "Dame tu reporte", tiempo
    
    else:

        if (tiempo == None and verificarTiempoIndicador()):
                  

            return "NAGIOS solicita tu reporte", time.time()

        elif mensaje == "No pasa nada":
            return "Ok", tiempo

        else:
            return "No te entiendo", tiempo



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
