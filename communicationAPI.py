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

ipserver = '192.168.4.84:50051' 

channel = grpc.secure_channel(ipserver,credentials)
stub = communication_pb2_grpc.CommunicationStub(channel)
ip = "Direccion IP"




def recibirReportes():
    request = communication_pb2.ClientMessage(ip = ip, message = "Recibir reportes")
    responses = stub.StreamingServerReport(request)
    for response in responses:
        print("REPORTE RECIBIDO")
        print("   IP del host: " + response.ip)
        print()

def recibirIndicadores():
    request = communication_pb2.ClientMessage(ip = ip, message = "Recibir indicadores")
    responses = stub.StreamingServerIndicator(request)
    for response in responses:
        print("INDICADOR DE COMPROMISO DETECTADO")
        print("   IP donde se detecto: " + response.ip)
        print("   Timestamp: " + response.timestamp)
        print("   Detector: " + response.detector)
        print()

def consultaEspecificaReportes():
    ipConsulta = input("Ingrese la IP del host a consultar: ")
    fechaInicial = input("Ingrese la fecha inicial (YYYY-MM-DD): ")
    fechaFinal = input("Ingrese la fecha final (YYYY-MM-DD): ")
    request = communication_pb2.SpecificRequest(ip = ipConsulta, start = fechaInicial, end = fechaFinal)
    responses = stub.SpecificReport(request)
    for response in responses:
        print("REPORTE RECIBIDO") 

def consultaEspecificaIndicadores():
    ipConsulta = input("Ingrese la IP del host a consultar: ")
    fechaInicial = input("Ingrese la fecha inicial (YYYY-MM-DD): ")
    fechaFinal = input("Ingrese la fecha final (YYYY-MM-DD): ")
    request = communication_pb2.SpecificRequest(ip = ipConsulta, start = fechaInicial, end = fechaFinal)
    responses = stub.SpecificReport(request)
    for response in responses:
        print("INDICADOR RECIBIDO") 

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
    elif opcion == "3":
        consultaEspecificaReportes()
    elif opcion == "4":
        consultaEspecificaIndicadores()
    elif opcion == "5":
        sys.exit()

