import communication_pb2_grpc
import communication_pb2
import sqlite3
from sqlite3 import Error
import grpc
import subprocess
import json
import time
import sys

credentials = grpc.ssl_channel_credentials(open('/home/pi1/Downloads/MonitoreoIoC-main/certificates/ca.pem','rb').read(),
    open('/home/pi1/Downloads/MonitoreoIoC-main/certificates/clientNagios-key.pem','rb').read(),open('/home/pi1/Downloads/MonitoreoIoC-main/certificates/clientNagios.pem','rb').read())

ipserver = '192.168.4.100:50051' 

channel = grpc.secure_channel(ipserver,credentials)
stub = communication_pb2_grpc.CommunicationStub(channel)



def reporte():

    indicador = sys.argv[2] + "---" + sys.argv[3]
    request = communication_pb2.IndicatorMessage(indicator = indicador, ip = sys.argv[1], timestamp = str(time.time()), detector = "NAGIOS")
    reply = stub.IndicatorReport(request)
    print("La respuesta es: "+reply.message)


if __name__ == "__main__":

    
    reporte()









