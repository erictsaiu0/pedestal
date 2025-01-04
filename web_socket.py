import socket
import threading
import os
import argparse
import time
import struct
from device_ip import addr_dict, inv_addr_dict
import sound

def recv_msg(sock):
    # Read message length and unpack it into an integer
    raw_msglen = recvall(sock, 4)
    if not raw_msglen:
        return None
    msglen = struct.unpack('>I', raw_msglen)[0]
    return recvall(sock, msglen)


def recvall(sock, n):
    # Helper function to recv n bytes or return None if EOF is hit
    data = bytearray()
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None
        data.extend(packet)
    return data


def send_msg(sock, msg):
    # Prefix each message with a 4-byte length (network byte order)
    msg = struct.pack('>I', len(msg)) + msg
    sock.sendall(msg)


class PiSocket:
    """伺服器端，等待客戶端連線並接收檔案"""

    def __init__(self, pi_name):
        self.ip = inv_addr_dict[pi_name]
        self.port = 12345
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.ip, self.port))
        self.server_socket.listen(5)
        print(f"[{pi_name}] Listening on {self.ip}:{self.port}")

    def new_socket_handler(self, client_socket):
        try:
            while True:
                data = client_socket.recv(1024)
                if not data:
                    print(f"[{self.ip}] No data received, closing connection.")
                    break

                command = data.decode()
                print(f"Received: {command}")

                if command == "quit":
                    client_socket.send("Goodbye.".encode())
                    break
                elif command == "file":
                    client_socket.send("ACK, start receiving file...".encode())
                    file_len_data = client_socket.recv(1024)
                    if not file_len_data:
                        print(f"[{self.ip}] Did not receive file length, closing connection.")
                        break
                    file_len = int(file_len_data.decode())
                    client_socket.send("file len ACK!".encode())

                    file_data = recv_msg(client_socket)
                    if file_data:
                        with open(f"{addr_dict[self.ip]}.mp3", "wb") as f:
                            f.write(file_data)
                        client_socket.send("file received!".encode())
                    break
                elif command == "play_intro":
                    sound.play_mp3("intro_alloy.mp3")
                    client_socket.send("intro played!".encode())
                else:
                    print(f"[{self.ip}] Unknown command: {command}")
                    client_socket.send("Unknown command".encode())
        except Exception as e:
            print(f"[{self.ip}] Error during connection: {e}")
        finally:
            client_socket.close()
            print(f"[{self.ip}] Connection closed")

    def run(self):
        while True:
            client_socket, addr = self.server_socket.accept()
            print(f"Connected by {addr_dict.get(addr[0], 'Unknown')}")
            threading.Thread(target=self.new_socket_handler, args=(client_socket,), daemon=True).start()


class MacSocket:
    """客戶端，連接到伺服器並傳送檔案"""

    def __init__(self, pi_name):
        self.target_pi_name = pi_name
        self.target_pi_ip = inv_addr_dict[pi_name]
        self.port = 12345
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.target_pi_ip, self.port))
    
    def send_msg(self, msg):
        try:
            self.client_socket.send(msg.encode())
        except Exception as e:
            print(f"Error sending message: {e}")

    def send_file(self, file_name):
        try:
            self.client_socket.send("file".encode())
            response = self.client_socket.recv(1024).decode()
            print(f"[{self.target_pi_name}] {response}")

            if not os.path.exists(file_name):
                print(f"File {file_name} does not exist!")
                return

            data = open(file_name, "rb").read()
            self.client_socket.send(str(len(data)).encode())
            response = self.client_socket.recv(1024).decode()
            print(f"[{self.target_pi_name}] {response}")

            send_msg(self.client_socket, data)
            print(f"[{self.target_pi_name}] File sent successfully.")
        except Exception as e:
            print(f"Error sending file: {e}")
        finally:
            self.client_socket.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--id", type=str, default="server")
    parser.add_argument("--Test", type=bool, default=False)
    args = parser.parse_args()

    if args.Test:
        if args.id == "server":
            sckt = MacSocket("local")
            time.sleep(3)
            sckt.send_file("test_speech_results/isart.mp3")
        elif args.id == "clientA":
            sckt = PiSocket("local")
            sckt.run()
        else:
            print("Invalid id")
            exit(1)
    else:
        if args.id == "server":
            sckt = MacSocket("isart")
            sckt.send_file("test_speech_results/isart.mp3")
        elif args.id == "isart":
            sckt = PiSocket("isart")
            sckt.run()
        elif args.id == "notart":
            sckt = PiSocket("notart")
            sckt.run()
        elif args.id == "describe":
            sckt = PiSocket("describe")
            sckt.run()
        else:
            print("Invalid id")
            exit(1)
