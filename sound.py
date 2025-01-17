import time
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame
import argparse

def play_mp3(file_path):
    """
    Play an MP3 file, interrupting any currently playing audio.
    Optimized for Raspberry Pi 4 to minimize audio crackling.
    
    Args:
        file_path (str): Path to the MP3 file
    """
    try:
        # Initialize pygame mixer if not already initialized
        if not pygame.mixer.get_init():
            # Use higher frequency and larger buffer size to reduce crackling
            pygame.mixer.init(frequency=48000, size=-16, channels=2, buffer=8192)
        else:
            # Force stop any currently playing audio
            pygame.mixer.stop()  # Stop all sound channels
            pygame.mixer.music.stop()  # Stop music
            pygame.mixer.quit()  # Close audio device
            pygame.mixer.init(frequency=48000, size=-16, channels=2, buffer=8192)
            
        # Add small delay to ensure mixer is ready
        time.sleep(0.1)
            
        # Load and play the audio file
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.set_volume(0.8)  # Slightly reduce volume to prevent distortion
        pygame.mixer.music.play()
        
        # Get audio duration and wait for completion
        audio = pygame.mixer.Sound(file_path)
        duration = audio.get_length()
        
        # Use busy wait instead of sleep to prevent audio stuttering
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
        
        # Add small delay before cleanup
        time.sleep(0.1)
        
        # Cleanup
        pygame.mixer.music.stop()
        
    except Exception as e:
        print(f"Error playing audio: {str(e)}")
        if pygame.mixer.get_init():
            pygame.mixer.quit()

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=str, default='intro_alloy.mp3')
    args = parser.parse_args()

    # 播放音樂
    mp3_path = args.path
    
    if os.path.exists(mp3_path):
        print(f"開始播放: {mp3_path}")
        play_mp3(mp3_path)
    else:
        print(f"找不到檔案: {mp3_path}")
