from device_ip import mac_ip, isart_ip, notart_ip, describe_ip
import socket

def get_message(ip, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((ip, port))
        data = s.recv(1024)
        print(f"Received message from {ip}:{port}")
        return data.decode('utf-8')

def send_message(ip, port, message):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((ip, port))
        s.sendall(message.encode('utf-8'))
        print(f"Sent message to {ip}:{port}")

