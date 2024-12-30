# 設定 device ip
mac_ip = "192.168.50.223"
isart_ip = "192.168.50.202" # pi A
notart_ip = "192.168.0.1"
describe_ip = "192.168.0.1"

addr_dict = {
    "192.168.50.223": "server",
    "192.168.50.202": "pi A",
    "192.168.0.1": "pi B",
    "192.168.0.2": "pi C",
    "127.0.0.1": "local"
}

inv_addr_dict = {v: k for k, v in addr_dict.items()}