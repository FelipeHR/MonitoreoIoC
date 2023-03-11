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



global tiempoMaximoPeticion
tiempoMaximoPeticion = 2
global tiempoMaximoNagios
tiempoMaximoNagios = 1
global reporte
reporte = False
global tiempoReporte
tiempoReporte = None

#global cola_id_indicadores
#cola_id_indicadores = []
#global cola_id_reportes
#cola_id_reportes = []

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
        dat = json.dumps(datos)

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

def asociarID(id_indicador, id_reporte):

    database = "/usr/local/nagios/libexec/eventhandlers/Base.db"
    conn = create_connection(database)

    datos_reporte_indicador = (id_indicador, id_reporte)

    create_reporte_indicador(conn, datos_reporte_indicador)



#Transformar formato de hora a string: datetime.fromtimestamp(time_stamp) https://flexiple.com/python/python-timestamp/
# ---------------------------------------------------------


class CommunicationServicer(communication_pb2_grpc.CommunicationServicer):
    

    def SubmitReport(self, request, context):

        d = datetime.now()

        Fecha  = str(d.date())
        Hora   = str(d.time())
             
        id_reporte = guardarReporte(request.ip, Fecha, Hora, request.json)


        serverReply = communication_pb2.ServerMessage()
        serverReply.message = str(id_reporte)


        return serverReply
    

    def BidirectionalCommunication(self, request_iterator, context):
        tiempoInicial = None
        for request in request_iterator:
            mensaje, tiempoInicial = comprobar(request.message, tiempoInicial)
            print("Solicitud de "+request.ip+": "+request.message)
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


        id_indicador = guardarIndicador(request.indicator, request.detector, request.ip, fechaIndicator, horaIndicator)


        serverReply = communication_pb2.ServerMessage()
        serverReply.message = str(id_indicador)


        return serverReply

    def SaveIndicatorReport(self, request, context):

        idReporte = request.idReport
        idIndicador = request.idIndicator

        asociarID(idIndicador, idReporte)

        serverReply = communication_pb2.ServerMessage()
        serverReply.message = "Se asociaron " + idReporte + " - " + idIndicador

        return serverReply

def  comprobar(mensaje, tiempo):
    #Comprobamos si termino el tiempo de pedida de reporte por Nagios
    global tiempoReporte
    #tiempoReporte es el tiempo desde que se empezo a solicitar reportes (si no hay reportes es None)
    global reporte
    #reporte es True si se tiene que solicitar reporte
    global tiempoMaximoNagios
    #tiempoMaximoNagios es el tiempo maximo para no volver a perdir reportes desde nagios
    global tiempoMaximoPeticion
    #tiempoMaximoPeticion es el tiempo maximo para solicitarle reportes a las demas maquinas

    if tiempoReporte != None and tiempoReporte + tiempoMaximoNagios <= time.time()/60:
        reporte = False
        tiempoReporte = None
    
    
    if mensaje == "Tengo un problema":
        if tiempo != None and tiempo + tiempoMaximoPeticion > time.time()/60:
            return "Ya te solicite reporte", tiempo
        else:
            return "Dame tu reporte", time.time()/60
    
    else:
        if (tiempo != None and reporte and tiempo + tiempoMaximoPeticion <= time.time()/60) or (reporte and tiempo == None):
            return "Dame tu reporte", time.time()/60
        elif mensaje == "No pasa nada":
            return "Ok", tiempo
        else:
            return "No te entiendo",tiempo 

def comprobarReportes():
    global tiempoReporte
    global reporte
    global tiempoMaximoNagios

    if reporte:
        if tiempoReporte != None:
            if tiempoReporte + tiempoMaximoNagios > time.time()/60:
                return "Esperar"
            else:
                tiempoReporte = time.time/(60)
                return "Enviar Reporte"
    else:
        tiempoReporte = time.time()/60
        reporte = True
        return "Enviar Reporte"


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    communication_pb2_grpc.add_CommunicationServicer_to_server(CommunicationServicer(), server)
    credentials = grpc.ssl_server_credentials( [    (open('certificates/server100-key.pem', 'rb').read(), open('certificates/server100.pem', 'rb').read())], root_certificates=open('certificates/ca.pem', 'rb').read(), require_client_auth=True)
    server.add_secure_port("192.168.4.100:50051", credentials)
    server.start()
    print("Server Started")
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
