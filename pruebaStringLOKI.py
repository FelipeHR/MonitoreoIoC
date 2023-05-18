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

cadena = input()
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
    if len(separados) > 1:

        dicReason["MATCHES"] = formated(separados[1].replace(";"," "))
        
    dicGeneral["REASON " + str(contadorReason)] = dicReason
    contadorReason += 1
        
import json
print(json.dumps(dicGeneral))
dicLoki = {}
dicLoki[fecha] = dicGeneral

with open('data.json', 'w') as outfile:
    json.dump(dicLoki, outfile)

