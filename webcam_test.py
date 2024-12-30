import cv2
import time
import numpy as np
import threading

import cv2
import time
import numpy as np
import threading

class MotionDetector:
    def __init__(self, cap, background_path="background.jpg", detect_interval=1, audio_detach=False):
        self.cap = cap
        # check if the webcam is opened correctly, if not, exit the program
        if not self.cap.isOpened():
            print("Error: Could not open webcam.")
            exit()
        self.background_path = background_path
        self.detect_interval = detect_interval
        self.last_detect_time = time.time()
        
        # 初始化背景影像
        self.background = self.initialize_background()
        self.state = "IDLE"
        self.last_frame = None
        self.audio_detach = audio_detach
        
    def center_crop(self, img):
        img = np.array(img)
        height, width = img.shape[:2]
        new_width = min(width, height)
        new_height = new_width
        left = (width - new_width) // 2
        top = (height - new_height) // 2
        img = img[top:top+new_height, left:left+new_width]
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        img = cv2.resize(img, (224, 224))
        img = cv2.GaussianBlur(img, (15, 15), 0)
        return img

    def initialize_background(self):
        ret, frame = self.cap.read()
        if not ret:
            raise RuntimeError("Failed to capture image from webcam.")
        frame = self.center_crop(frame)
        cv2.imwrite(self.background_path, frame)
        return frame

    def compare(self, baseline):
        ret, image = self.cap.read()
        processed_img = self.center_crop(image)

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
        print(self.state, round(1 / (end - start), 4))
    '''
    def compare_background(self):
        start = time.time()
        ret, frame = self.cap.read()
        processed_img = self.center_crop(frame)
        
        # 計算當前影像與背景的差異
        diff = cv2.absdiff(self.background, processed_img)
        _, diff = cv2.threshold(diff, 50, 255, cv2.THRESH_BINARY)
        # diff = cv2.dilate(diff, None, iterations=2)
        threading.Thread(target=cv2.imwrite, args=("diff.jpg", diff)).start()
        
        # 記錄當前時間
        current_time = time.time()
        
        # 檢查是否達到偵測間隔並且是否有變化
        if np.sum(diff) > 0 and (current_time - self.last_detect_time > self.detect_interval):
            print("Something changed")
            self.last_detect_time = current_time  # 更新上次觸發時間
            
            start_image_processing = time.time()
            threading.Thread(target=self.trigger_action, args=(frame,)).start()
            print("Image processing time: ", time.time() - start_image_processing)
        else:
            # print(round(1 / (time.time() - start), 4))
            print(np.sum(diff), current_time - self.last_detect_time, end="\r")

    '''
    def trigger_action(self, image):
        print("NOW TRIGGER ACTION with new image")
        # 處理影像，例如計算或保存
        cv2.imwrite("triggered.jpg", image)

    def run(self):
        while True:
            self.state_machine()

if __name__ == "__main__":
    cap = cv2.VideoCapture(0)
    detector = MotionDetector(cap)
    detector.run()