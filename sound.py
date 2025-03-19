import time
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame
import threading
import argparse
from utils import log_and_print
import logging

# 紀錄當前播放的執行緒與控制變數
current_thread = None
stop_flag = False  # 用來通知執行緒應該停止
lock = threading.Lock()  # 確保執行緒同步


def play_mp3(file_path):
    """
    Play an MP3 file, but allows interruption by checking `stop_flag`.
    """
    global stop_flag

    with lock:
        # 強制停止任何正在播放的音訊
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
            pygame.mixer.stop()
            time.sleep(0.1)

        # 初始化 pygame.mixer（如果尚未初始化）
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=48000, size=-16, channels=2, buffer=8192)

    try:
        # 載入與播放音樂
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.set_volume(0.8)
        pygame.mixer.music.play()

        # 等待音樂播放完成，但允許中途被強制停止
        while pygame.mixer.music.get_busy():
            if stop_flag:
                pygame.mixer.music.stop()
                return  # 停止當前執行緒
            time.sleep(0.1)

    except Exception as e:
        log_and_print(f"Error playing audio: {str(e)}", "ERROR")

    finally:
        pygame.mixer.music.stop()


def play_mp3_threaded(file_path):
    """
    確保前一個執行緒結束後，才開啟新的播放執行緒。
    """
    global current_thread, stop_flag

    # 設定 stop_flag，讓舊的執行緒可以結束
    stop_flag = True
    time.sleep(0.2)  # 給舊執行緒時間檢查 stop_flag 並結束

    # 開啟新的播放執行緒
    stop_flag = False  # 重設 stop_flag，允許新音樂播放
    current_thread = threading.Thread(target=play_mp3, args=(file_path,))
    current_thread.start()


if __name__ == "__main__":
    logname = 'log_sound'
    logging.basicConfig(
        filename=f'{logname}.log',
        filemode='a',
        format='%(asctime)s\t %(levelname)s\t %(message)s',
        datefmt='%H:%M:%S',
        level=logging.DEBUG
    )
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=str, default="intro_alloy.mp3")
    parser.add_argument("-p", "--pressuretest", action="store_true", help="Enable pressure test mode")
    parser.add_argument("-t", "--repeattime", type=int, default=50, help="Pressure test play time")
    parser.add_argument("-i", "--interval", type=int, default=5, help="Pressure test interval time in seconds")
    args = parser.parse_args()

    mp3_path = args.path

    if args.pressuretest:
        for _ in range(args.repeattime):
            print(f"{_}/{args.repeattime}")
            play_mp3_threaded(mp3_path)
            time.sleep(0.2)  # 減少間隔，測試播放中斷
    else:
        if os.path.exists(mp3_path):
            print(f"開始播放: {mp3_path}")
            play_mp3(mp3_path)
        else:
            print(f"找不到檔案: {mp3_path}")
