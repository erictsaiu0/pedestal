import pygame
import time
import os

def play_mp3(file_path):
    """
    播放MP3檔案
    
    參數:
    file_path (str): MP3檔案的路徑
    """
    try:
        # if pygame is used by other process, close it
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
            pygame.mixer.quit()

        # 初始化pygame的音訊系統
        pygame.init()
        pygame.mixer.init()
        
        # 載入並播放音樂
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()
        
        # 取得音訊長度（秒）
        audio = pygame.mixer.Sound(file_path)
        duration = audio.get_length()
        
        # 等待音樂播放完畢
        time.sleep(duration)
        
        # 清理資源
        pygame.mixer.music.stop()
        pygame.mixer.quit()
        
    except Exception as e:
        print(f"播放時發生錯誤: {str(e)}")

if __name__ == "__main__":
    # 播放音樂
    mp3_path = r'/Users/erictsai/Desktop/pedestal/test_speech_results/alloy.mp3'
    
    if os.path.exists(mp3_path):
        print(f"開始播放: {mp3_path}")
        play_mp3(mp3_path)
    else:
        print(f"找不到檔案: {mp3_path}")
