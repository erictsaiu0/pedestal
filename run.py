import gpt_utils
from KEYS import OPENAI_KEY
import sound
import TTS_utils
import os

import cv2
import time
import numpy as np
import threading
import argparse

from web_socket import MacSocket, PiSocket

class MotionDetector:
    def __init__(self, cap, background_path="background.jpg", detect_interval=5, text_num=50, zoom=0, audio_detach=False, audio_playlist=['isart', 'notart', 'describe'], high_sync=False):
        self.cap = cap
        if not self.cap.isOpened():
            raise RuntimeError("Failed to open webcam.")
        self.background_path = background_path
        self.detect_interval = detect_interval
        self.last_detect_time = time.time()
        self.zoom = zoom
        self.audio_detach = audio_detach
        # if audio_detach is True, then the audio will not be played in this device, audio will be sent to other device by web_socket.py
        self.audio_playlist = audio_playlist
        # Configurable audio playlist that determines which audio files will be played and their order
        if len(self.audio_playlist) == 0:
            raise ValueError("audio_playlist must be non-empty")

        self.background = self.initialize_background()
        self.state = "IDLE"
        self.last_frame = None
        self.text_num = text_num
        self.intro_sound_path = r'intro_alloy.mp3'
        self.high_sync = high_sync
    
    def center_crop(self, img, gray_resize_blur=False):
        img = np.array(img)
        height, width = img.shape[:2]

        new_width = min(width, height)
        left, top = (width - new_width) // 2, (height - new_width) // 2
        img = img[top:top+new_width, left:left+new_width]

        if self.zoom == 0:
            img = img
        elif self.zoom > 0:
            zoom_ratio = 1 + (self.zoom / 10)
            zoomed_size = int(new_width / zoom_ratio)
            crop_size = (new_width - zoomed_size) // 2
            img = img[crop_size:crop_size+zoomed_size, crop_size:crop_size+zoomed_size]
        else:
            raise ValueError("zoom must be non-negative")

        if gray_resize_blur:
            if img.ndim == 3 and img.shape[2] == 3:
                img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            img = cv2.resize(img, (224, 224))
            img = cv2.GaussianBlur(img, (15, 15), 0)
        return img
    '''
    def center_crop(self, img, zoom=2, gray_resize_blur=False):
        img = np.array(img)
        height, width = img.shape[:2]

        new_width = min(width, height)
        left, top = (width - new_width) // 2, (height - new_width) // 2
        img = img[top:top+new_width, left:left+new_width]

        if zoom > 0:
            zoom_ratio = 1 + (1 / zoom)
            crop_size = int(new_width / zoom_ratio / 2)
            if crop_size * 2 < new_width:
                img = img[crop_size:-crop_size, crop_size:-crop_size]
            print(crop_size, img.shape)
        elif zoom < 0:
            raise ValueError("zoom must be non-negative")

        if gray_resize_blur:
            if img.ndim == 3 and img.shape[2] == 3:  # 確保是彩色圖片
                img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            img = cv2.resize(img, (224, 224))
            img = cv2.GaussianBlur(img, (15, 15), 0)
        return img
    ''' 

    def initialize_background(self):
        ret, frame = self.cap.read()
        if not ret:
            raise RuntimeError("Failed to capture image from webcam.")
        frame = self.center_crop(frame, gray_resize_blur=True)
        cv2.imwrite(self.background_path, frame)
        return frame

    def compare(self, baseline):
        ret, image = self.cap.read()
        processed_img = self.center_crop(image, gray_resize_blur=True)

        diff = cv2.absdiff(baseline, processed_img)
        _, diff = cv2.threshold(diff, 50, 255, cv2.THRESH_BINARY)

        current_time = time.time()

        return diff, processed_img, image, current_time-self.last_detect_time
    
    def state_machine(self):
        start = time.time()
        if self.state == "IDLE":
            diff, frame, image, interval = self.compare(self.background)
            if np.sum(diff) > 0 and interval > self.detect_interval:
                self.state = "CHANGE"
                self.last_detect_time = time.time()
                self.last_frame = frame
        elif self.state == "CHANGE":
            last_frame_diff, last_frame, last_image, last_frame_interval = self.compare(self.last_frame)
            background_diff, background_frame, background_image, background_interval = self.compare(self.background)
            if np.sum(background_diff) == 0 and background_interval > self.detect_interval:
                self.state = "IDLE"
                self.last_detect_time = time.time()
            elif np.sum(last_frame_diff) == 0 and last_frame_interval > self.detect_interval:
                self.state = "DETECTED"
                threading.Thread(target=self.trigger_action, args=(last_image,)).start()
                self.last_detect_time = time.time()
            elif np.sum(last_frame_diff) > 0 and last_frame_interval > self.detect_interval:
                self.state = "CHANGE"
                self.last_detect_time = time.time()
                self.last_frame = last_frame
        elif self.state == "DETECTED":
            diff, frame, image, interval = self.compare(self.last_frame)
            if np.sum(diff) == 0 and interval > self.detect_interval:
                self.state = "DETECTED"
                self.last_detect_time = time.time()
            elif np.sum(diff) > 0 and interval > self.detect_interval:
                self.state = "CHANGE"
                self.last_detect_time = time.time()
                self.last_frame = frame
        end = time.time()
        print(self.state, round(1 / (end - start), 4), end='\r')

    def image_to_audio(self, base64_image, type):
        # Pre-define type mappings to avoid repeated conditionals
        type_mapping = {
            'describe': (lambda img: gpt_utils.describe_iamge(img, text_num=self.text_num), 'describe'),
            'isart': (lambda img: gpt_utils.is_art(img, text_num=self.text_num), 'isart'),
            'notart': (lambda img: gpt_utils.not_art(img, text_num=self.text_num), 'notart')
        }

        if type not in type_mapping:
            raise ValueError("type must be 'describe', 'isart', or 'notart'")

        # if self.audio_detach:
        #     try:
        #         mac_socket = MacSocket(type)
        #         mac_socket.send_msg("play_intro")
        #         mac_socket.end_connection()
        #     except:
        #         raise RuntimeError("Socket connection failed for intro")
        # else:
        #     threading.Thread(target=sound.play_mp3, args=(self.intro_sound_path,)).start()

        # Get text generation function and prefix from mapping
        text_func, prefix = type_mapping[type]
        
        # Generate text and audio
        text = text_func(base64_image)
        audio_path = TTS_utils.openai_tts(text, prefix=prefix, voice='random')

        # Play generated audio
        if self.audio_detach:
            try:
                mac_socket = MacSocket(type)
                mac_socket.send_file(audio_path)
                mac_socket.end_connection()
            except:
                raise RuntimeError("Socket connection failed for audio")
        else:
            threading.Thread(target=sound.play_mp3, args=(audio_path,)).start()

    def high_sync_image_to_audio(self, base64_image):
        type_mapping = {
            'describe': (lambda img: gpt_utils.describe_iamge(img, text_num=self.text_num), 'describe'),
            'isart': (lambda img: gpt_utils.is_art(img, text_num=self.text_num), 'isart'),
            'notart': (lambda img: gpt_utils.not_art(img, text_num=self.text_num), 'notart')
        }
        # # first send play intro command to all sockets to avoid delay
        # for type in self.audio_playlist:
        #     if type not in type_mapping:
        #         raise ValueError("type must be 'describe', 'isart', or 'notart'")
        #     else:
        #         if self.audio_detach:
        #             try:
        #                 mac_socket = MacSocket(type)
        #                 mac_socket.send_msg("play_intro")
        #                 mac_socket.end_connection()
        #             except:
        #                 raise RuntimeError("Socket connection failed for intro")
        #         else:
        #             threading.Thread(target=sound.play_mp3, args=(self.intro_sound_path,)).start()
        
        # then do the audio generation and sending to sockets
        for type in self.audio_playlist:
            text_func, prefix = type_mapping[type]
        
            # Generate text and audio
            text = text_func(base64_image)
            audio_path = TTS_utils.openai_tts(text, prefix=prefix, voice='random')

            if self.audio_detach:
                try:
                    mac_socket = MacSocket(type)
                    mac_socket.send_file(audio_path)
                    mac_socket.end_connection()
                except:
                    raise RuntimeError("Socket connection failed for audio")
            else:
                threading.Thread(target=sound.play_mp3, args=(audio_path,)).start()

    def trigger_action(self, image):
        print("NOW TRIGGER ACTION with new image")
        # Center crop image to square
        height, width = image.shape[:2]
        size = min(width, height)
        start_x = (width - size) // 2
        start_y = (height - size) // 2
        image = image[start_y:start_y+size, start_x:start_x+size]
        
        image = self.center_crop(image, gray_resize_blur=False)
        
        # cv2.imwrite("current.jpg", image)

        image = gpt_utils.npimageResize(image, 0.5)
        base64_image = gpt_utils.image2base64(image)

        # play intro in only first device:
        if self.audio_detach:
            try:
                mac_socket = MacSocket(self.audio_playlist[0])
                mac_socket.send_msg("play_intro")
                mac_socket.end_connection()
            except:
                raise RuntimeError("Socket connection failed for intro")
        else:
            threading.Thread(target=sound.play_mp3, args=(self.intro_sound_path,)).start()

        # generate audio and play
        if self.high_sync:
            self.high_sync_image_to_audio(base64_image)
        else:
            for audio_type in self.audio_playlist:
                self.image_to_audio(base64_image, audio_type)
            
    def run(self):
        while True:
            self.state_machine()

if __name__ == "__main__":
    args = argparse.ArgumentParser()
    args.add_argument("--zoom", type=float, default=5)
    args.add_argument("--text_num", type=int, default=50)
    args.add_argument("--audio_detach", type=bool, default=False)
    args.add_argument("--audio_playlist", type=str, default='I')
    args.add_argument("--high_sync", type=bool, default=False)
    args = args.parse_args()
    print(f'now activating pedestal')
    print(f'zoom: {args.zoom}')
    print(f'text_num: {args.text_num}')
    audio_detach = bool(args.audio_detach)
    print(f'audio_detach: {audio_detach}')
    playlist_dict = {'I': ['isart'], 'N': ['notart'], 'D': ['describe']}
    playlist = [item for char in args.audio_playlist 
               for item in playlist_dict.get(char, [])]
    print(f'audio_playlist: {playlist}')
    high_sync = bool(args.high_sync)
    print(f'high_sync: {high_sync}')

    print('================================================================================')
    print("Now activating pedestal")
    cap = cv2.VideoCapture(0)
    detector = MotionDetector(cap, zoom=args.zoom, text_num=args.text_num, audio_detach=audio_detach, audio_playlist=playlist)
    detector.run()
    
    # python run.py --zoom 5 --audio_playlist ID