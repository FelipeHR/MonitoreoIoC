import hashlib
ruta = "communicationClient.py"

with open(ruta,"rb") as f:
    text = f.read()
    md5 = hashlib.md5(text).hexdigest()
    print(md5)