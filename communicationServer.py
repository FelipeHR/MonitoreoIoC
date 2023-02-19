from concurrent import futures
import time

import grpc
import communication_pb2
import communication_pb2_grpc


global tiempoMaximoPeticion
tiempoMaximoPeticion = 2
global tiempoMaximoNagios
tiempoMaximoNagios = 1
global reporte
reporte = False
global tiempoReporte
tiempoReporte = None

class CommunicationServicer(communication_pb2_grpc.CommunicationServicer):
    def SubmitReport(self, request, context):
        print(request.ip)
        serverReply = communication_pb2.ServerMessage()
        serverReply.message = f"Se recibio la informacion correctamente"
        with open(request.ip+" informe.json","w") as file:
            file.write(request.json)
        return serverReply
    

    def BidirectionalCommunication(self, request_iterator, context):
        tiempoInicial = None
        for request in request_iterator:
            mensaje, tiempoInicial = comprobar(request.message, tiempoInicial)
            

            print("Solicitud de "+request.ip+": "+request.message)
            serverReply = communication_pb2.ServerMessage()
            serverReply.message = mensaje
            yield serverReply

    def NagiosCommunication(self, request, context):
        mensaje = request.message
        estado = comprobarReportes()
        print(mensaje)
        serverReply = communication_pb2.ServerMessage()
        if mensaje == "Necesito Reporte":
            if estado == "Esperar":
                serverReply.message = "Se pidio reporte hace poco"
            elif estado == "Enviar Reporte":           
                 serverReply.message = "Se pidieron los reportes"

        
        return serverReply

def  comprobar(mensaje, tiempo):
    #Comprobamos si termino el tiempo de pedida de reporte por Nagios
    global tiempoReporte
    global reporte
    global tiempoMaximoNagios
    global tiempoMaximoPeticion

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
    credentials = grpc.ssl_server_credentials( [    (open('certificates/server101-key.pem', 'rb').read(), open('certificates/server101.pem', 'rb').read())], root_certificates=open('certificates/ca.pem', 'rb').read(), require_client_auth=True)
    server.add_secure_port("192.168.4.101:50051", credentials)
    server.start()
    print("Server Started")
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
