import sqlite3
from sqlite3 import Error
from datetime import datetime
import time
import json

# CHECHO -------------------------------------------------------

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


def create_host_reporte(conn, datos):
    # datos = (ip, id_reporte)
    sql = ''' INSERT INTO Host_Reporte(IP, Id_reporte)
              VALUES(?,?) '''

    cur = conn.cursor()
    cur.execute(sql, datos)
    conn.commit()

#in sqlite: .open /home/pi1/Desktop/Base.db

def main():

    database = r"/home/pi1/Desktop/Base.db"

    # create a database connection
    conn = create_connection(database)

    with conn:

        #datos_host = ("192.168.4.103", "dir_MAC_aux")
        #create_host(conn, datos_host)

        d = datetime.now() 

        f = open("/home/pi1/Desktop/prototipo/192.168.4.101_informe.json")
        da = json.load(f)
        dat = json.dumps(da)
        

        datos_reporte = ( "errorDePrueba", str(d.date()), str(d.time()), dat)
        ide = create_reporte(conn, datos_reporte)
        
        f.close()


        datos_host_reporte = ("192.168.4.102", ide)
        create_host_reporte(conn, datos_host_reporte)

    conn.close()

if __name__ == '__main__':
    main()