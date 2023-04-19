from cryptography.fernet import Fernet
import hashlib

llave = input()
f = Fernet(llave)
with open("certificates/host-key-encrypted.pem","rb") as encrypted_file:
    encrypted = encrypted_file.read()
    
decrypted =  f.decrypt(encrypted)
h = open('certificates/host-key.pem','rb').read()

if hashlib.md5(decrypted).digest() == hashlib.md5(h).digest():
    print ("son igualitos")
