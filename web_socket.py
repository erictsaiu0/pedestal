import socket
import threading
import os
import argparse

class ServerSocket:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.ip, self.port))
        self.socket.listen(1)
        print(f"Server is listening on {self.ip}:{self.port}")
        self.clients = []
        self.client_lock = threading.Lock()

    def accept(self):
        client_socket, client_address = self.socket.accept()
        print(f"Accepted connection from {client_address}")
        return client_socket
    
    def close(self):
        self.socket.close()
        print("Server socket closed")
 
    def send_msg(self, client_socket, message):
        client_socket.sendall(message.encode('utf-8'))
        print(f"Sent message to {client_socket.getpeername()}")  # Fix to show client address

    def recv_msg(self, client_socket):
        data = client_socket.recv(1024)
        print(f"Received message from {client_socket.getpeername()}")  # Fix to show client address
        return data.decode('utf-8')
    
    def send_file(self, client_socket, file_path):  # Add client_socket parameter
        file_size = os.path.getsize(file_path)
        self.send_msg(client_socket, "file coming")
        self.recv_msg(client_socket)
        self.send_msg(client_socket, str(file_size))
        self.recv_msg(client_socket)
        with open(file_path, 'rb') as file:
            client_socket.sendfile(file)
        self.recv_msg(client_socket)

    def handle_client(self, client_socket):
        try:
            while True:
                message = self.recv_msg(client_socket)
                # Broadcast message to all clients
                with self.client_lock:
                    for client in self.clients:
                        if client != client_socket:  # Don't send back to sender
                            self.send_msg(client, message)
        except (ConnectionResetError, ConnectionAbortedError):
            with self.client_lock:
                self.clients.remove(client_socket)
            client_socket.close()
            print(f"Client {client_socket.getpeername()} disconnected")
    
    def run(self):
        while True:
            client_socket = self.accept()
            self.clients.append(client_socket)
            threading.Thread(target=self.handle_client, args=(client_socket,)).start()


class ClientSocket:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connected = False
        
    def connect(self):
        try:
            self.socket.connect((self.ip, self.port))
            self.connected = True
            print(f"Connected to server at {self.ip}:{self.port}")
            # Start receiving thread
            threading.Thread(target=self.receive_messages).start()
        except ConnectionRefusedError:
            print("Connection failed - server may be offline")
            
    def send_msg(self, message):
        if self.connected:
            self.socket.sendall(message.encode('utf-8'))
            print(f"Sent message: {message}")
            
    def recv_msg(self):
        data = self.socket.recv(1024)
        return data.decode('utf-8')
    
    def receive_messages(self):
        while self.connected:
            try:
                message = self.recv_msg()
                if message == "file coming":
                    self.receive_file()
                else:
                    print(f"Received message: {message}")
            except:
                self.connected = False
                print("Disconnected from server")
                break
                
    def receive_file(self):
        self.send_msg("ready")
        file_size = int(self.recv_msg())
        self.send_msg("size received")
        
        received_data = b""
        while len(received_data) < file_size:
            data = self.socket.recv(min(1024, file_size - len(received_data)))
            if not data:
                break
            received_data += data
            
        self.send_msg("file received")
        return received_data
    
    def close(self):
        self.connected = False
        self.socket.close()
        print("Connection closed")
    
    def run(self):
        while True:
            message = self.recv_msg()
            if message == "file coming":
                self.receive_file()
            else:
                print(f"Received message: {message}")

if __name__ == "__main__":
    args = argparse.ArgumentParser()
    args.add_argument("--id", type=str, default="server or client")
    args.add_argument("--ip", type=str, default="127.0.0.1")
    args.add_argument("--port", type=int, default=12345)
    args = args.parse_args()

    if args.id == "server":
        server = ServerSocket(args.ip, args.port)
        server.run()
    else:
        client = ClientSocket(args.ip, args.port)
        client.run()
