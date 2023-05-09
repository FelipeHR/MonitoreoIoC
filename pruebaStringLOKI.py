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

cadena = "20230317T22:09:24Z memoria LOKI: Alert: MODULE: FileScan MESSAGE: FILE: /home/memoria/.config/Code/User/History/-5013641f/7e79.txt SCORE: 480 TYPE: UNKNOWN SIZE: 10665 FIRST_BYTES: 32303233303232385432323a30353a34335a206d / <filter object at 0x7f107729ab90> MD5: cc06d9e1fb2526925ee3d7ecb1cfccfc SHA1: 4a0f73af597296d6dedbd0c7dc7600c2c0de2042 SHA256: c337e13af11fe0b55c50e9a95366d3dc7c6e7d4498b6f6fba3916e246b4935ca CREATED: Thu Mar  9 16:58:54 2023 MODIFIED: Thu Mar  9 16:58:54 2023 ACCESSED: Fri Mar 17 18:23:53 2023 REASON_1: Yara Rule MATCH: EquationDrug_HDDSSD_Op SUBSCORE: 70 DESCRIPTION: EquationDrug - HDD/SSD firmware operation - nls_933w.dll REF: http://securelist.com/blog/research/69203/inside-the-equationdrug-espionage-platform/ AUTHOR: Florian Roth (Nextron Systems) @4nc4p MATCHES: Str1: nls_933w.dllREASON_2: Yara Rule MATCH: webshell_browser_201_3_400_in_JFolder_jfolder01_jsp_leo_ma_warn_webshell_nc_download SUBSCORE: 70 DESCRIPTION: Web Shell REF: - AUTHOR: Florian Roth (Nextron Systems) MATCHES: Str1: UplInfo info = UploadMonitor.getInfo(fi.clientFileName); Str2: long time = (System.currentTimeMillis() - starttime) / 1000l;"
fecha = cadena.split('Z')[0]
info = cadena.split('Alert: ')[1]
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

print(dicGeneral)
import json
print(type(json.dumps(dicGeneral)))
dicLoki = {}
dicLoki[fecha] = dicGeneral

with open('data.json', 'w') as outfile:
    json.dump(dicLoki, outfile)

