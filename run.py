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

import socket
from device_ip import mac_ip, isart_ip, notart_ip, describe_ip
from pi import get_message, send_message

class MotionDetector:
    def __init__(self, cap, background_path="background.jpg", detect_interval=1, text_num=50, zoom=0):
        self.cap = cap
        # check if the webcam is opened correctly, if not, exit the program
        if not self.cap.isOpened():
            raise RuntimeError("Failed to open webcam.")
        self.background_path = background_path
        self.detect_interval = detect_interval
        self.last_detect_time = time.time()
        self.zoom = zoom
        
        # 初始化背景影像
        self.background = self.initialize_background()
        self.state = "IDLE"
        self.last_frame = None
        self.text_num = text_num
    
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
        frame = self.center_crop(frame, gray_blur=True)
        cv2.imwrite(self.background_path, frame)
        return frame

    def compare(self, baseline):
        ret, image = self.cap.read()
        processed_img = self.center_crop(image, gray_blur=True)

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
    def trigger_action(self, image):
        print("NOW TRIGGER ACTION with new image")
        # 處理影像，例如計算或保存
        # cv2.imwrite("triggered.jpg", image)

        # centercrop image
        height, width = image.shape[:2]
        new_width = min(width, height)
        new_height = new_width
        left = (width - new_width) // 2
        top = (height - new_height) // 2
        image = image[top:top+new_height, left:left+new_width]
        # center crop and resize
        crop_size = image.shape[0]//2//2
        # center crop 
        image = image[crop_size:-crop_size, crop_size:-crop_size]
        cv2.imwrite("current.jpg", image)

        time_resize = time.time()
        image = gpt_utils.npimageResize(image, 0.5)
        time_resize_end = time.time()

        time_img2base64 = time.time()
        base64_image = gpt_utils.image2base64(image)
        time_img2base64_end = time.time()

        # time_describe = time.time()
        # describe = gpt_utils.describe_iamge(base64_image)
        # time_describe_end = time.time()
        # time_tts = time.time()
        # describe_sound = TTS_utils.openai_tts(describe, prefix="describe", voice='random', text_num=self.text_num)
        # time_tts = time.time()
        # time_play = time.time()
        # sound.play_mp3(describe_sound)
        # time_play_end = time.time()
        # print(f'resize: {time_resize_end-time_resize}, img2base64: {time_img2base64_end-time_img2base64}, describe: {time_describe_end-time_describe}, tts: {time_tts-time_describe_end}, play: {time_play_end-time_play}')

        isart = gpt_utils.is_art(base64_image, text_num=self.text_num)
        isart_sound = TTS_utils.openai_tts(isart, prefix="isart", voice='random')
        threading.Thread(target=sound.play_mp3, args=(isart_sound,)).start()
        # sound.play_mp3(isart_sound)

        # notart = gpt_utils.not_art(base64_image, text_num=self.text_num)
        # notart_sound = TTS_utils.openai_tts(notart, prefix="notart", voice='random')
        # sound.play_mp3(notart_sound)
        
    def run(self):
        while True:
            self.state_machine()

if __name__ == "__main__":
    args = argparse.ArgumentParser()
    args.add_argument("--zoom", type=int, default=0)
    args.add_argument("--text_num", type=int, default=50)
    args = args.parse_args()

    cap = cv2.VideoCapture(0)
    detector = MotionDetector(cap, zoom=args.zoom, text_num=args.text_num)
    detector.run()
    