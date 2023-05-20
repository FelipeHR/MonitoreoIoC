from concurrent import futures
import time
from datetime import datetime
import json
import sys
import hashlib

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
reporteGlobal = time.time()/60  + 5
#A los 5 minutos de que empieza a correr el servidor, le pedira un reporte a todos los clientes conectados
#la siguiente peticion sera despues de reporteGlobalTiempo minutos


global colaReportesNagios 
colaReportesNagios = []

global colaReportesMD5
colaReportesMD5 = []

global colaCerrarConexion
colaCerrarConexion = []

global dicIndicadoresAPI
dicIndicadoresAPI = {}

global dicReportesAPI
dicReportesAPI = {}

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
        datos_reporte = (fecha, hora, datos)
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
        print(fecha)
        # Guarda Indicador
        datos_indicador = (descripcion, detector, origen, fecha, hora)
        id_indicador = create_indicador(conn, datos_indicador)

        # Asocia Indicador con Host
        datos_host_indicador = (origen, id_indicador)
        create_host_indicador(conn, datos_host_indicador)

    conn.close()

    return id_indicador

# ---------------------------------------------------------

def get_hash(origen, hasheo):
    
    database = "/usr/local/nagios/libexec/eventhandlers/Base.db"

    conn = create_connection(database)

    cur = conn.cursor()
    cur.execute("SELECT * FROM Hash WHERE Origen=?", (origen,))
    rows = cur.fetchone()
    """if hasheo == rows[0]:
        return True
    else:
        return False
"""
    return True

def get_indicators(fi,ff, origen):
        
    database = "/usr/local/nagios/libexec/eventhandlers/Base.db"

    conn = create_connection(database)
    print("entramos")
    cur = conn.cursor()
    cur.execute("SELECT * FROM Reporte WHERE Origen=?", ("192.168.4.101",))
    rows = cur.fetchall()
    print(rows)
    """    indicators = []
    for fecha in rows:
        if fecha[0] <=ff and fecha[0] >=fi:
            indicators.append(fecha[0])"""

    return None

def get_reports(fi,ff, origen):
        
    database = "/usr/local/nagios/libexec/eventhandlers/Base.db"

    conn = create_connection(database)

    cur = conn.cursor()
    cur.execute("SELECT Id_reporte FROM Host_Reporte WHERE IP = ?", (origen,))
    rows = cur.fetchall()
    reports = []
    for ids in rows:
        cur.execute("SELECT Datos FROM Reporte WHERE Id_reporte = ? AND Fecha >= ? AND Fecha <= ?", (ids[0],fi,ff,))
        reporte = cur.fetchone()
        if reporte != None:
            mensajeReporte = communication_pb2.ReportMessage(ip = origen, json = reporte[0])
            reports.append(mensajeReporte)
            print(type(mensajeReporte.ip))
            print(type(mensajeReporte.json))
    

    #cur.execute("SELECT Fecha , Id_reporte, Datos FROM Reporte WHERE Fecha >= ? AND Fecha <= ?", (fi,ff,))
    """for fecha in rows:
                    print(fecha[0])
                    print(fecha[1])
                    print(fecha[2][0])
                    if fecha[0] <=ff and fecha[0] >=fi:
                        reports.append(fecha[0])
            """
    return reports
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



# --------------------------------------------

class CommunicationServicer(communication_pb2_grpc.CommunicationServicer):
    

    def SubmitReport(self, request, context):

        print("\nSubmitReport()\n")


        d = datetime.now()

        Fecha  = str(d.date())
        Hora   = str(d.time())

        id_reporte = guardarReporte(request.ip, Fecha, Hora, request.json)
        encolarReporteIndicador(request, "reporte")
        print("\nSe recibio el reporte\n")

        #si es string
        dic = json.loads(request.json)
        

        serverReply = communication_pb2.ServerMessage()
        serverReply.message = str(id_reporte)

        return serverReply
    


    def BidirectionalCommunication(self, request_iterator, context):
        entregarReporte = None

        for request in request_iterator:
            mensaje, entregarReporte = comprobar(request.message, entregarReporte, request.ip)
            print("Solicitud de "+request.ip+": "+request.message)
            serverReply = communication_pb2.ServerMessage()
            serverReply.message = mensaje
            yield serverReply



    def IndicatorReport(self, request, context):

        tsIndicator = request.timestamp
        stamp = str(datetime.fromtimestamp(float(tsIndicator)))
        FyH = stamp.split()
        fechaIndicator = FyH[0]
        horaIndicator = FyH[1]


        if request.detector == "LOKI" or request.detector == "MD5":

            id_indicador = guardarIndicador(request.indicator, request.detector, request.ip, fechaIndicator, horaIndicator)
            print("Se recibio el indicador: ")
            print(request.indicator)
            encolarReporteIndicador(request, "indicador")
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

    def ServerComprobationMD5(self, request, context):

        global colaReportesMD5
        md5Host = request.md5
        ipHost = request.ip
        archivo = request.archive

        
        comprobacion = get_hash(archivo, md5Host)


        #consulta a la bd si el md5 del archivo es igual al md5 que se envio
        mensaje = "El archivo no ha sido modificado"


        if(not comprobacion):


            mensaje = "El archivo ha sido modificado"
            descripcion = "El archivo " + archivo + " ha sido modificado"
            tsIndicator = time.time()
            stamp = str(datetime.fromtimestamp(tsIndicator))
            FyH = stamp.split()
            fechaIndicator = FyH[0]
            horaIndicator = FyH[1]

            guardarIndicador(descripcion, "MD5", ipHost, fechaIndicator, horaIndicator)
            #Levantamos un indicador de compromiso, y posteriormente le pedimos reporte al host mediante una cola de reportes
            colaReportesMD5.append(ipHost)    

        serverReply = communication_pb2.ServerMessage(message = mensaje)


        return serverReply
    
    def StreamingServerIndicator(self, request, context):
        global dicIndicadoresAPI
        #Crear cola (una cola por cada ip, es decir una cola de colas) de indicadores para cada ip de terceros
        nombrePrograma = request.name
        dicIndicadoresAPI[nombrePrograma] = []
        while True:
            while (dicIndicadoresAPI[nombrePrograma]):
                indicador = dicIndicadoresAPI[nombrePrograma].pop() 
                yield indicador
            time.sleep(10)

    
    def StreamingServerReport(self, request, context):
        global dicReportesAPI
        #Crear cola (una cola por cada ip, es decir una cola de colas) de indicadores para cada ip de terceros
        nombrePrograma = request.name
        dicReportesAPI[nombrePrograma] = []
        while True:
            while dicReportesAPI[nombrePrograma]:
                reporte = dicReportesAPI[nombrePrograma].pop() 
                yield reporte
            time.sleep(10)
    
    def IndicatorRequest(self, request, context):
        #Crear consulta a la base de datos y construir la informacion del indicador 
        indicadores = get_indicators(request.start, request.end, request.ip)
        while not (indicadores):
            yield indicadores.pop

    
    def ReportRequest(self, request, context):
        reportes = get_reports(request.start, request.end, request.ip)
        while reportes:
            yield reportes.pop()
            time.sleep(1)
    
def encolarReporteIndicador(informacion, tipo):
    global dicIndicadoresAPI
    global dicReportesAPI
    if tipo == "indicador":
        for programa in dicIndicadoresAPI:
            #print("Se encolo un indicador en " + str(programa))
            dicIndicadoresAPI[programa].append(informacion)
    elif tipo == "reporte":
        for programa in dicReportesAPI:
            #print("Se encolo un reporte en " + str(programa))
            dicReportesAPI[programa].append(informacion)




def verificarReporteGlobal(reporte):
    global reporteGlobal
    global reporteGlobalTiempo
    global tiempoReporte
    global tiempoMaximoReporte

    if (time.time()/60) > reporteGlobal:
        print("entramos a la asignacion de reporte global")
        tiempoReporte = time.time()/60 + tiempoMaximoReporte
        reporteGlobal = time.time()/60 + reporteGlobalTiempo
    
    if tiempoReporte != None:
        if time.time()/60 > tiempoReporte:
            tiempoReporte = None
            return None

        if reporte == None :
            return True
        
        else:
            return False        
        
    return None


def  comprobar(mensaje, reporte, ip):
    global colaReportesNagios
    global colaReportesMD5
    #tiempoMaximoReporte es el tiempo maximo para solicitarle reportes a las demas maquinas

    reporte = verificarReporteGlobal(reporte)
    
    if mensaje == "Tengo un problema":
        return "Dame tu reporte", reporte 
    
    else:
        if (reporte):
            return "Solicitud de reporte global", reporte 

        elif ip in colaReportesNagios:
            colaReportesNagios.remove(ip)
            return "NAGIOS solicita tu reporte", reporte

        elif ip in colaReportesMD5:
            colaReportesMD5.remove(ip)
            colaCerrarConexion.append(ip)
            return "Server solicita tu reporte", reporte
        
        elif ip in colaCerrarConexion:
            colaCerrarConexion.remove(ip)
            return "Cerrar conexion", reporte
        
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
