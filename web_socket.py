import socket
import threading
import os
import argparse
import time

import socket
import threading
import os

class ServerSocket:
    def __init__(self, host="192.168.50.223", port=12345):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients = []

    def start_server(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"Server started at {self.host}:{self.port}")

        while True:
            client_socket, client_address = self.server_socket.accept()
            print(f"Connection established with {client_address}")
            self.clients.append(client_socket)

            threading.Thread(target=self.handle_client, args=(client_socket,)).start()

    def handle_client(self, client_socket):
        while True:
            try:
                message = client_socket.recv(1024).decode()
                if not message:
                    break
                print(f"Received message from client: {message}")
            except:
                print("Client disconnected")
                self.clients.remove(client_socket)
                client_socket.close()
                break

    def send_file(self, client_socket, file_path):
        if not os.path.exists(file_path):
            print("File does not exist")
            return

        try:
            client_socket.send("file coming".encode())
            ack = client_socket.recv(1024).decode()
            if ack != "acknowledge":
                print("Client did not acknowledge file transfer")
                return

            with open(file_path, "rb") as file:
                while chunk := file.read(1024):
                    client_socket.send(chunk)
            print("File sent successfully")

        except Exception as e:
            print(f"Error sending file: {e}")


class ClientSocket:
    def __init__(self, host="192.168.50.223", port=12345):
        self.host = host
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect_to_server(self):
        try:
            self.client_socket.connect((self.host, self.port))
            print(f"Connected to server at {self.host}:{self.port}")

            threading.Thread(target=self.listen_to_server).start()
        except Exception as e:
            print(f"Error connecting to server: {e}")

    def listen_to_server(self):
        while True:
            try:
                message = self.client_socket.recv(1024).decode()
                if message == "file coming":
                    print("File transfer initiated by server")
                    self.client_socket.send("acknowledge".encode())
                    self.receive_file()
                else:
                    print(f"Received message from server: {message}")
            except Exception as e:
                print(f"Error receiving message: {e}")
                self.client_socket.close()
                break

    def receive_file(self):
        file_data = b""
        try:
            while True:
                chunk = self.client_socket.recv(1024)
                if not chunk:
                    break
                file_data += chunk

            file_name = "received_file"  # Save file with a default name
            with open(file_name, "wb") as file:
                file.write(file_data)
            print(f"File received and saved as {file_name}")
        except Exception as e:
            print(f"Error receiving file: {e}")

    def send_message(self, message):
        try:
            self.client_socket.send(message.encode())
        except Exception as e:
            print(f"Error sending message: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--id", type=str, default="server")
    args = parser.parse_args()

    if args.id == "server":
        server = ServerSocket()
        server.start_server()
    elif args.id == "client":
        client = ClientSocket()
        client.connect_to_server()
    else:
        print("Invalid id")
        exit(1)