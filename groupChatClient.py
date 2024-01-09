import socket
from cryptography.fernet import Fernet
import random
import base64
import struct
import threading

IP = "localhost"
PORT = 7877


def listenMessages(s, fernet):
    while True:
        
        # Reciving and decrypting sender name
        data = s.recv(4)
        byteSize = struct.unpack("I", data)[0]
        data = s.recv(byteSize)
        sender_name = fernet.decrypt(data).decode()

        # Reciving and decrypting sender message
        data = s.recv(4)
        byteSize = struct.unpack("I", data)[0]
        data = s.recv(byteSize)
        msg = fernet.decrypt(data).decode()

        # Taking care of server messages
        if sender_name == "\n":
            print(msg)

        # Taking care of other clients messages
        else:
            print(sender_name + ":", msg)
        
def connect_server(ip, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((ip, port))

    # Setting up Diffie Helman protocol 
    data = s.recv(12)
    unpacked_data = struct.unpack("III", data)
    pwrNum, modNum, serverPublicKey = unpacked_data

    # Generating the client private key
    privateKey = random.randint(1, modNum - 1)

    # Calculating the shared key   
    publicKey = pwrNum ^ privateKey % modNum
    sharedKey = serverPublicKey ^ privateKey % modNum
    shared_key_bytes = sharedKey.to_bytes(32, 'big')
    encoded_shared_key = base64.urlsafe_b64encode(shared_key_bytes)

    # Sending the client public key so the server could calculate the shared key as well
    s.send(publicKey.to_bytes(4, byteorder = 'little'))
    
    fernet = Fernet(encoded_shared_key)

    # Sending the server the client encrypted name
    encName = fernet.encrypt(name.encode())
    s.send(struct.pack("I", len(encName)))
    s.send(encName)

    # Creating a thread that always listens and prints new messages
    listenMessagesThread = threading.Thread(target=listenMessages, args=(s, fernet))
    listenMessagesThread.start()
    
    while True:
        
        # Sending and encrypting client message to server
        msg = input("")
        s.send(struct.pack("I", len(fernet.encrypt(msg.encode()))))
        encMessage = fernet.encrypt(msg.encode())
        s.send(encMessage)


if __name__ == "__main__":
    while True:
        name = input("Enter your name: ")
        if len(name) <= 20 and len(name) > 0:
            break
        else:
            print("name must to be less or equal 20 characters and greated than 0")
    connect_server(IP, PORT)
    
