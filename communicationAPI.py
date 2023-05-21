import communication_pb2_grpc
import communication_pb2
import sqlite3
from sqlite3 import Error
import grpc
import subprocess
import json
import time
import sys

credentials = grpc.ssl_channel_credentials(open('certificates/ca.pem','rb').read(),
    open('certificates/clientNagios-key.pem','rb').read(),open('certificates/clientNagios.pem','rb').read())

ipserver = '192.168.4.100:50051' 

channel = grpc.secure_channel(ipserver,credentials)
global stub
stub = communication_pb2_grpc.CommunicationStub(channel)
global nombreSoftware
nombreSoftware = "Prueba"

def guardarReportes(reportes, marcador):
    global nombreSoftware

    globalDic = {}


    with open('consulta reportes '+ nombreSoftware + " "+ str(marcador) +'.json', 'w') as outfile:
        
        for reporte in reportes:
            info = json.loads(reporte.json)
            info['ipHost'] = reporte.ip
            globalDic[info["TimeStamp"]] = info
        json.dump(globalDic, outfile)


def guardarIndicadores(indicadores, marcador):
    global nombreSoftware

    globalDic = {}


    with open('consulta indicadores '+ nombreSoftware + " "+ str(marcador) +'.json', 'w') as outfile:
        
        for indicador in indicadores:
            info = json.loads(indicador.indicator)
            info['ipHost'] = indicador.ip
            info['detector'] = indicador.detector
            globalDic[indicador.timestamp] = info
        json.dump(globalDic, outfile)


def recibirReportes():
    global nombreSoftware
    global stub
    request = communication_pb2.SoftwareMessage(name = nombreSoftware)
    responses = stub.StreamingServerReport(request)
    for response in responses:
        print("REPORTE RECIBIDO")
        print("   IP del host: " + response.ip)
        print()

def recibirIndicadores():
    global nombreSoftware
    global stub
    request = communication_pb2.SoftwareMessage(name = nombreSoftware)
    responses = stub.StreamingServerIndicator(request)
    for response in responses:
        print("INDICADOR DE COMPROMISO DETECTADO")
        print("   IP donde se detecto: " + response.ip)
        print("   Timestamp: " + response.timestamp)
        print("   Detector: " + response.detector)
        print()

def consultaEspecificaReportes( ipConsulta, fechaInicial, fechaFinal):
    global nombreSoftware
    global stub

    request = communication_pb2.SpecificRequest(ip = ipConsulta, start = fechaInicial, end = fechaFinal)
    responses = stub.ReportRequest(request)
    reportesRecibidos = []
    for response in responses:
        print("REPORTE RECIBIDO IP del host: " + response.ip)
        reportesRecibidos.append(response)
    
    
    return reportesRecibidos

def consultaEspecificaIndicadores(ipConsulta, fechaInicial, fechaFinal):
    global nombreSoftware
    global stub

    request = communication_pb2.SpecificRequest(ip = ipConsulta, start = fechaInicial, end = fechaFinal)
    responses = stub.IndicatorRequest(request)
    indicadoresRecibidos = []
    for response in responses:
        indicadoresRecibidos.append(response)

    return indicadoresRecibidos
    

if __name__ == "__main__":
    print("1. Recibir reportes")
    print("2. Recibir indicadores")
    print("3. Consulta especifica de reportes")
    print("4. Consulta especifica de indicadores")
    print("5. Salir")
    opcion = input("Ingrese una opcion: ")
    if opcion == "1":
        recibirReportes()
    elif opcion == "2":
        recibirIndicadores()

    elif opcion == "3" or opcion == "4" :

        ipConsulta = input("Ingrese la IP del host a consultar: ")
        fechaInicial = input("Ingrese la fecha inicial (YYYY-MM-DD): ")
        fechaFinal = input("Ingrese la fecha final (YYYY-MM-DD): ")
        marcador = time.time()

        if opcion == "3":
            reportes = consultaEspecificaReportes(ipConsulta, fechaInicial, fechaFinal)
            guardarReportes(reportes, marcador)

        else:
            indicadores = consultaEspecificaIndicadores(ipConsulta, fechaInicial, fechaFinal)
            guardarIndicadores(indicadores, marcador)
        
    elif opcion == "5":
        sys.exit()

