import sqlite3
from sqlite3 import Error
from datetime import datetime
import time
import json
import sys

# ------------------------- Base de Datos -------------------------

# /home/pi1/base1
def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Error as e:
        print(e)

    return conn


#-------- Entidades ---------
def create_host(conn, datos):

    sql = ''' INSERT INTO Host(IP,MAC)
              VALUES(?,?) '''

    cur = conn.cursor()
    cur.execute(sql, datos)
    conn.commit()


def create_reporte(conn, datos):
    #                      |
    #   -------------------
    #   |
    # datos = (date.today(),hora,JSON)
    # d = datetime.now()     |
    # hora = d.time()--------

    sql = ''' INSERT INTO Reporte(Error, Fecha, Hora, Datos)
              VALUES(?,?,?,?) '''

    cur = conn.cursor()
    cur.execute(sql, datos)
    conn.commit()

    return cur.lastrowid


def create_indicador(conn, datos):

    sql = ''' INSERT INTO Indicador(Id_indicador, Descripcion, Detector, Origen)
              VALUES(?,?,?,?) '''

    cur = conn.cursor()
    cur.execute(sql, datos)
    conn.commit()



#-------- Relaciones ---------

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
    sql = ''' INSERT INTO Indicador_Reporte(Id_indicador, Id_reporte)
              VALUES(?,?) '''

    cur = conn.cursor()
    cur.execute(sql, datos)
    conn.commit()

# -----------------------------------------------------------------



#in sqlite: .open /usr/local/nagios/libexec/eventhandlers/Base.db

def main():

    database = "/usr/local/nagios/libexec/eventhandlers/Base.db"

    # create a database connection
    conn = create_connection(database)

    er = sys.argv[1] + "--" + sys.argv[2]

    with conn:

        #datos_host = ("192.168.4.103", "dir_MAC_aux")
        #create_host(conn, datos_host)

        d = datetime.now() 

        f = open("/home/pi1/Desktop/prototipo/192.168.4.101_informe.json")#CAMBIAR POR JSON QUE SE GENERA 
        da = json.load(f)
        dat = json.dumps(da)
        

        datos_reporte = ( er, str(d.date()), str(d.time()), dat)
        ide = create_reporte(conn, datos_reporte)
        
        f.close()


        datos_host_reporte = (sys.argv[3], ide)
        create_host_reporte(conn, datos_host_reporte)

    conn.close()

if __name__ == '__main__':
    main()




"""
secuencia:
 
- nagios detecta problema.

- cambia estado del host o servicio en la base de datos.

- guarda primer problema del incidente relacionado al host o servicio especifico.

- comunica al servidor que pida reportes.

- el servidor queda esperando nueva comunicacion de agentes host para pedir reportes.

- los agentes host se comunican y envian el reporte.

- se almacenan los reportes en la base de datos y se ingresan sus id en una cola.

- mientras que los id esperan en la cola, se alamacenan en la base de datos los indicadores que estan siendo detectados y en una cola adicional sus id.

- termina de pasar el tiempo de recoleccion de informes e indicadores y se asocian los id de reportes de la cola a los indicadores detectados.

"""