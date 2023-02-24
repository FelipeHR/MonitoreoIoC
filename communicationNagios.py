import communication_pb2_grpc
import communication_pb2
import grpc
import subprocess
import json
import time

credentials = grpc.ssl_channel_credentials(open('certificates/ca.pem','rb').read(),
    open('certificates/clientNagios-key.pem','rb').read(),open('certificates/clientNagios.pem','rb').read())

ipserver = '192.168.4.84:50051' 

channel = grpc.secure_channel(ipserver,credentials)
stub = communication_pb2_grpc.CommunicationStub(channel)

def reporte(): 
    request = communication_pb2.ClientMessage(message = "Necesito Reporte", problem = "Puerto no reconocido", ip = "192.168.0.5")
    reply = stub.NagiosCommunication(request)
    print("La respuesta es: "+reply.message)


if __name__ == "__main__":
    reporte()