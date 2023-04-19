from cryptography.fernet import Fernet

key = Fernet.generate_key()
f = Fernet(key)
with open ("certificates/host-key.pem","rb") as original_file:
    original = original_file.read()

encrypted = f.encrypt(original)
with open ("certificates/host-key-encrypted.pem","wb") as encrypted_file:
    encrypted_file.write(encrypted)
print(key)
#M0O8zY9aU6HoKx9BHWWaO3sFXgRtUNo7scny1HTYJjc=