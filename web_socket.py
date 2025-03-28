import socket
import threading
import os
import argparse
import time
import struct
from device_ip import addr_dict, inv_addr_dict
import sound
from utils import log_and_print
import logging

import platform
if platform.machine() in ('armv7l', 'armv6l', 'aarch64'):
    import printer

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
        self.pi_name = pi_name
        if pi_name == "printer":
            self.printer_manager = printer.ThermalPrinterManager()
        self.port = 12345
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.ip, self.port))
        self.server_socket.listen(5)
        log_and_print(f"[{pi_name}] Listening on {self.ip}:{self.port}", 'info')

    def new_socket_handler(self, client_socket):
        try:
            while True:
                data = client_socket.recv(1024)
                if not data:
                    log_and_print(f"[{self.ip}] No data received, closing connection.", 'info')
                    break

                command = data.decode()
                log_and_print(f"[{self.ip}] Received: {command}", 'info')

                if command == "quit":
                    client_socket.send("Goodbye.".encode())
                    break
                elif command == "file":
                    client_socket.send("ACK, start receiving file...".encode())
                    file_len_data = client_socket.recv(1024)
                    if not file_len_data:
                        log_and_print(f"[{self.ip}] Did not receive file length, closing connection.", 'info')
                        break
                    file_len = int(file_len_data.decode())
                    client_socket.send("file len ACK!".encode())

                    file_data = recv_msg(client_socket)
                    if file_data:
                        with open(f"{addr_dict[self.ip]}.mp3", "wb") as f:
                            f.write(file_data)
                        client_socket.send("file received!".encode())
                        sound.play_mp3_threaded(f"{addr_dict[self.ip]}.mp3")
                    break
                elif command == "play_intro":
                    sound.play_mp3_threaded("intro_alloy.mp3")
                    client_socket.send("intro played!".encode())
                elif command == "print":
                    client_socket.send("ACK, start receiving text...".encode())
                    
                    printer_text = client_socket.recv(1024).decode()
                    log_and_print(f"[{self.ip}] Received printer text: {printer_text}", 'info')
                    if not printer_text:
                        log_and_print(f"[{self.ip}] Did not receive printer text, closing connection.", 'info')
                        break
                    else:
                        self.printer_manager.print_text(printer_text)
                    client_socket.send("print done!".encode())
                else:
                    print(f"[{self.ip}] Unknown command: {command}")
                    client_socket.send("Unknown command".encode())
        except Exception as e:
            log_and_print(f"[{self.ip}] Error during connection: {e}", 'error')
        finally:
            client_socket.close()
            log_and_print(f"[{self.ip}] Connection closed", 'info')

    def run(self):
        while True:
            client_socket, addr = self.server_socket.accept()
            log_and_print(f"Connected by {addr_dict.get(addr[0], 'Unknown')}", 'info')
            threading.Thread(target=self.new_socket_handler, args=(client_socket,), daemon=True).start()


class MacSocket:
    """客戶端，連接到伺服器並傳送檔案"""

    def __init__(self, pi_name):
        self.target_pi_name = pi_name
        self.target_pi_ip = inv_addr_dict[pi_name]
        self.port = 12345
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.target_pi_ip, self.port))
    
    def end_connection(self):
        self.client_socket.close()

    def send_msg(self, msg):
        try:
            self.client_socket.send(msg.encode())
        except Exception as e:
            log_and_print(f"Error sending message: {e}", 'error')

    def send_file(self, file_name):
        try:
            self.client_socket.send("file".encode())
            response = self.client_socket.recv(1024).decode()
            print(f"[{self.target_pi_name}] {response}")

            if not os.path.exists(file_name):
                log_and_print(f"File {file_name} does not exist!", 'debug')
                return

            data = open(file_name, "rb").read()
            self.client_socket.send(str(len(data)).encode())
            response = self.client_socket.recv(1024).decode()
            print(f"[{self.target_pi_name}] {response}")

            send_msg(self.client_socket, data)
            log_and_print(f"[{self.target_pi_name}] File sent successfully.", 'info')
        except Exception as e:
            log_and_print(f"Error sending file: {e}", 'error')
        finally:
            self.client_socket.close()
    
    def send_printer_text(self, text):
        try:
            self.client_socket.send("print".encode())
            response = self.client_socket.recv(1024).decode()
            log_and_print(f"[{self.target_pi_name}] {response}", 'info')

            self.client_socket.send(text.encode())
            response = self.client_socket.recv(1024).decode()
            log_and_print(f"[{self.target_pi_name}] {response}")
        except Exception as e:
            log_and_print(f"Error sending printer text: {e}", 'error')
        finally:
            self.client_socket.close()

if __name__ == "__main__":
    logname = 'log_web_socket'
    logging.basicConfig(
        filename=f'{logname}.log',
        filemode='a',
        format='%(asctime)s\t %(levelname)s\t %(message)s',
        datefmt='%H:%M:%S',
        level=logging.DEBUG
    )
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
