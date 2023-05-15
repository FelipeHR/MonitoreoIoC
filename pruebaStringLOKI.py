def formated(texto):
    texto_modificado = texto.replace(": ", "~~~")
    string = texto_modificado

    items = string.split("~~~")
    anterior = ""
    dic = {}
    for i in items:
        actual = i.split(" ")[0].isupper() and len(i.split(" ")) <= 1
        if i != items[0] and i != items[-1]:
            if not actual:
                position = i.rfind(" ")
                if position != -1:
                    dic[anterior.split(" ")[-1]] = i[:position]
                else:
                    dic[anterior.split(" ")[-1]] = i
        elif i == items[-1]:
            dic[anterior.split(" ")[-1]] = i
        anterior = i
    return dic

cadena = "20230510T03:17:18Z memoria LOKI: Warning: MODULE: FileScan MESSAGE: FILE: /home/memoria/Documentos/GitHub/MonitoreoIoC/signature-base/iocs/hash-iocs.txt SCORE: 70 TYPE: UNKNOWN SIZE: 1138146 FIRST_BYTES: 230a23204c4f4b4920435553544f4d204556494c / <filter object at 0x7f72fc49b580> MD5: dd14d9d04d555261c1e3fbfd1dc60833 SHA1: 7278ee797cef3e68c1e8c3b4127d4ba81773ce20 SHA256: defbdb21fd7cf847ba841c47a15329a2f4208768d69ab86ce750c3ad00ab3af1 CREATED: Tue Apr 18 18:45:14 2023 MODIFIED: Tue Apr 18 18:45:14 2023 ACCESSED: Tue May  9 18:32:09 2023 REASON_1: Yara Rule MATCH: EquationDrug_HDDSSD_Op SUBSCORE: 70 DESCRIPTION: EquationDrug - HDD/SSD firmware operation - nls_933w.dll REF: http://securelist.com/blog/research/69203/inside-the-equationdrug-espionage-platform/ AUTHOR: Florian Roth (Nextron Systems) @4nc4p MATCHES: Str1: nls_933w.dll"
fecha = cadena.split('Z')[0]
if len(cadena.split('Alert')) > 1:
    info = cadena.split('Alert: ')[1]
else:
    info = cadena.split('Warning: ')[1]

alert_reason = info.split('REASON_')
infoseparada = alert_reason[0].split(": ")

dicGeneral = formated(alert_reason[0])
dicGeneral["TIMESTAMP"] = fecha
contadorReason = 1
for i in alert_reason[1:]:
    separados = i.split("MATCHES: ")
   
    
    dicReason = formated(separados[0])
    listMatches = [] 

    dicReason["MATCHES"] = formated(separados[1].replace(";"," "))
    dicGeneral["REASON " + str(contadorReason)] = dicReason
    contadorReason += 1

import json
print(json.dumps(dicGeneral))
dicLoki = {}
dicLoki[fecha] = dicGeneral

with open('data.json', 'w') as outfile:
    json.dump(dicLoki, outfile)

