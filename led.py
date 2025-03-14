import time
from rpi_ws281x import PixelStrip, Color

# LED 配置
LED_COUNT = 25         # 5x5 WS2812 矩陣
LED_PIN = 18           # 連接到 WS2812 的 GPIO (PWM0)
LED_FREQ_HZ = 800000   # LED 訊號頻率
LED_DMA = 10           # DMA 通道 (一般設 10)
LED_BRIGHTNESS = 255   # 亮度 (0-255)
LED_INVERT = False     # 反向信號 (通常設 False)
LED_CHANNEL = 0        # PWM 頻道


# 初始化 LED Strip
strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
strip.begin()

# 最外圍 16 顆 LED 的索引順序
outer_ring = [0, 1, 2, 3, 4, 5, 14, 15, 24, 23, 22, 21, 20, 19, 10, 9]

def set_all_leds(color):
    """設定所有 LED 為指定顏色"""
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(*color))
    strip.show()

def breathing_light(t):
    """白色呼吸燈效果，持續 30 秒"""
    start_time = time.time()
    while time.time() - start_time < t:
        for brightness in range(0, 256, 5):  # 逐漸變亮
            set_all_leds((brightness, brightness, brightness))
            time.sleep(0.02)
        for brightness in range(255, -1, -5):  # 逐漸變暗
            set_all_leds((brightness, brightness, brightness))
            time.sleep(0.02)

def blinking_light(t):
    """青色 (0, 255, 255) 閃爍，每 0.5 秒亮滅，持續 30 秒"""
    start_time = time.time()
    while time.time() - start_time < t:
        set_all_leds((0, 255, 255))  # 青色
        time.sleep(0.5)
        set_all_leds((0, 0, 0))  # 關閉
        time.sleep(0.5)

def steady_light(t):
    """綠色 (0, 255, 0) 恆亮，持續 30 秒"""
    set_all_leds((0, 255, 0))
    time.sleep(t)

def outer_ring_loop(t):
    """最外圍 16 顆 LED 以每秒一圈的速度繞圈閃白光，持續 30 秒"""
    start_time = time.time()
    while time.time() - start_time < t:
        for i in outer_ring:
            set_all_leds((0, 0, 0))  # 先清除所有 LED
            br = 255
            strip.setPixelColor(i, Color(br, br, br))  # 讓當前 LED 變白
            strip.show()
            time.sleep(1 / len(outer_ring))  # 一圈 16 顆，每秒一圈 = 1/16 秒換一顆 LED
            # time.sleep(1)

def turn_off():
    """關閉所有 LED"""
    set_all_leds((0, 0, 0))

def set_mode(mode, t=10):
    """設定 LED 模式"""
    if mode == 0:
        turn_off()
    elif mode == 1:
        breathing_light(t)
    elif mode == 2:
        blinking_light(t)
    elif mode == 3:
        steady_light(t)
    elif mode == 4:
        outer_ring_loop(t)
    else:
        print("無效模式！請選擇 0, 1, 2, 3 或 4")

# 讓使用者可以重複選擇模式
while True:
    try:
        mode = int(input("請輸入模式 (0: 關閉 LED, 1: 白色呼吸燈, 2: 青色閃爍, 3: 綠色常亮, 4: 外圍旋轉白光): "))
        set_mode(mode)
    except ValueError:
        print("請輸入有效數字！")
