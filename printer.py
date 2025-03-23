import serial
import adafruit_thermal_printer
import threading
from PIL import Image, ImageOps, ImageDraw, ImageFont
import time

printer_manager = None
printer_lock = threading.Lock()  # 確保執行緒安全

class ThermalPrinterManager:
    def __init__(self, port="/dev/serial0", baudrate=19200, timeout=3):
        """初始化熱敏打印機"""
        global printer_manager  # 這裡的 global 只是在此函式內部修改變數
        if printer_manager is not None:
            return  # 如果已經初始化過，就不再初始化
        
        self.uart = serial.Serial(port, baudrate=baudrate, timeout=timeout)
        ThermalPrinter = adafruit_thermal_printer.get_printer_class(2.69)
        self.printer = ThermalPrinter(self.uart)

        # 設置 GBK 編碼模式（某些打印機可能需要）
        # self.printer._uart.write(b'\x1B\x74\x26')  # ESC t 38 (GB18030)
        self.printer._uart.write(b'\x1B\x7B\x01')  # ESC { 1 -> 開啟倒置模式

        # 設定全域變數的實例
        printer_manager = self

    def print_text(self, text):
        """列印傳統中文字（確保執行緒安全）"""
        with printer_lock:  # 使用鎖來保護串口操作
            encoded_text = text.encode('gbk')  # 轉換為 GBK 編碼
            self.printer._uart.write(encoded_text)
            self.printer.feed(5)  # 走紙 2 行

    def print_test_page(self):
        """列印測試頁"""
        with printer_lock:
            self.printer.test_page()
            self.printer.feed(5)
    
if __name__ == "__main__":
    printer_manager = ThermalPrinterManager()  # 只有第一次執行時才初始化
    printer_manager.print_text("您好，歡迎使用熱感印表機！這是繁體中文不是簡體中文國字國字")