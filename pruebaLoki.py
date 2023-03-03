import subprocess
import time
from os import remove
i = 0 
while True:
    if i%5==0:
        print("Se ejecutara un analisis")
        subprocess.run("nohup python3 Loki-0.45.0/loki.py --onlyrelevant -l log.txt &", shell = True, check = True)
    else:
        try:
            file = open("log.txt")
            line = file.readline()
            j = 1
            while line!= "":
                print("Indicador "+str(j)+" :" + line)
                line = file.readline()
                j += 1
            file.close()
            remove("log.txt")
        except FileNotFoundError:
            print("No hay archivo")
    time.sleep(1200)
    i = i+1