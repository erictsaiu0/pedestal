# 設定 device ip
addr_dict = {
    "192.168.18.25": "server", 
    "192.168.18.22": "isart", 
    "192.168.18.13": "notart",
    "192.168.18.27": "describe", 
    "127.0.0.1": "local"
}

inv_addr_dict = {v: k for k, v in addr_dict.items()}