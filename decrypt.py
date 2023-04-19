from cryptography.fernet import Fernet
import hashlib

llave = input()
f = Fernet(llave)
with open("certificates/host-key-encrypted.pem","rb") as encrypted_file:
    encrypted = encrypted_file.read()
with open("certificates/host-key.pem","rb") as data:
    original = data.read()
decrypted =  f.decrypt(encrypted)
if hashlib.md5(decrypted).digest() == hashlib.md5(original).digest():
    print ("son igualitos")
