import socket
from cryptography.fernet import Fernet
import random
import base64
import struct
import threading


IP = "localhost"
PORT = 7877

# Setting up Diffie-Hellman protocol
modNum = 23
pwrNum = 9
privateKey = random.randint(1, modNum - 1)
publicKey = pwrNum ** privateKey % modNum

# A dictionary for addresses names
addrName = {
    
}

# A dictionary for addresses and connection seasons
connected_clients = {
    
}

# A dictionary for addresses and encryption keys
addrKeys = {
    
}


# A thread that always accepts new clients
def listenNewClients(s):
    while True:
        s.listen()
        conn, addr = s.accept()
        print('Connected by', addr)
        
        # Setting up Diffie Helman protocol
        info = struct.pack('III', pwrNum, modNum, publicKey)
        conn.send(info)

        data = conn.recv(4)
        clientPublicKey = int.from_bytes(data, byteorder='little')
        sharedKey = clientPublicKey ** privateKey % modNum
        shared_key_bytes = sharedKey.to_bytes(32, 'big')
        encoded_shared_key = base64.urlsafe_b64encode(shared_key_bytes)
        fernet = Fernet(encoded_shared_key)
        addrKeys[addr] = fernet

        # Reciving sender name
        data = conn.recv(4)
        byteSize = struct.unpack("I", data)[0]
        data = conn.recv(byteSize)
        sender_name = fernet.decrypt(data).decode()

        addrName[addr] = sender_name
        connected_clients[addr] = conn
        
        listenClientMessagesThread = threading.Thread(target=listenClientMessages, args=(conn, sender_name, fernet))
        listenClientMessagesThread.start()

def listenClientMessages(conn, sender_name, fernet):
    while True:
        try:
            
            # Reciving and decrypting message 
            data = conn.recv(4)
            byteSize = struct.unpack("I", data)[0]
            data = conn.recv(byteSize)
            if not data:
                break
            msg = fernet.decrypt(data).decode()
            print(sender_name + ":", msg)

            # Sending the message to other clients except the one who sent it
            sendMessagesToOtherClients(sender_name, msg)

        # Handling the case that a client disconnects
        except(ConnectionResetError, BrokenPipeError):
            msg = f"Connection with {sender_name} {conn.getpeername()} closed."
            sendMessagesToOtherClients("\n", msg)
            print(msg)
            break
        
def StartServer(ip, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((ip, port))

    listenNewClientsThread = threading.Thread(target=listenNewClients, args=(s, ))
    listenNewClientsThread.start()
    
def sendMessagesToOtherClients(sender_name, msg):

    # To remove the disconnected clients from the dictionaries
    to_remove = []
    
    for addr, client_conn in connected_clients.items():
        try:
            
            # Skip sending the message to the sender
            if addrName[addr] != sender_name:
                fernet = addrKeys[addr]
            
                # Sending and encrypting the sender name
                enc_sender_name = fernet.encrypt(sender_name.encode())
                client_conn.send(struct.pack("I", len(enc_sender_name)))
                client_conn.send(enc_sender_name)
            
               # Sending and encrypting the sender message
                enc_msg = fernet.encrypt(msg.encode())
                client_conn.send(struct.pack("I", len(enc_msg)))
                client_conn.send(enc_msg)

        # Removing the disconnected clients from the dictionaries
        except(ConnectionResetError, BrokenPipeError):
            to_remove.append(addr)
            
    # Remove disconnected clients from the dictionaries
    for addr in to_remove:
        del connected_clients[addr]
        del addrName[addr]
        del addrKeys[addr]

if __name__ == "__main__":
    StartServer(IP, PORT)
    
