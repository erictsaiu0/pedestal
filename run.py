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
from utils import log_and_print
import logging
from datetime import datetime
import subprocess
import select
import json
import gphoto2 as gp

# DSLRCapture 類別：模擬 cv2.VideoCapture 行為，但讀取 DSLR live view 資料
class DSLRCapture:
    def __init__(self):
        self.context = gp.gp_context_new()
        self.camera = gp.check_result(gp.gp_camera_new())
        gp.check_result(gp.gp_camera_init(self.camera, self.context))
        self.apply_settings('camera_config.json')
        self.process = subprocess.Popen(['gphoto2', '--capture-movie', '--stdout'],
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.buffer = b""

    def set_camera_setting(self, setting, value):
        try:
            config = gp.check_result(gp.gp_camera_get_config(self.camera, self.context))
            setting_config = gp.check_result(gp.gp_widget_get_child_by_name(config, setting))
            gp.check_result(gp.gp_widget_set_value(setting_config, value))
            gp.check_result(gp.gp_camera_set_config(self.camera, config, self.context))
        except gp.GPhoto2Error as e:
            print(f"Error setting '{setting}' to '{value}': {e}")

    def apply_settings(self, setting_config_path):
        # 若有正在執行的 live view，先終止它
        if hasattr(self, 'process'):
            self.process.terminate()
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill()
        time.sleep(0.5)  # 給相機一些時間釋放 live view 資源

        # 重新關閉目前相機連線，再重新初始化連線
        try:
            gp.check_result(gp.gp_camera_exit(self.camera, self.context))
        except gp.GPhoto2Error as e:
            # 若錯誤為 [-52]，表示找不到裝置，則忽略
            if "-52" in str(e):
                pass
            else:
                print(f"Error exiting camera: {e}")
        time.sleep(1)
        self.camera = gp.check_result(gp.gp_camera_new())
        gp.check_result(gp.gp_camera_init(self.camera, self.context))
        
        # 更新參數設定
        # load setting_config_path, iis a json file
        with open(setting_config_path, 'r') as f:
            setting_config = json.load(f)
        self.iso_values = setting_config['iso']
        self.aperture_values = setting_config['aperture']
        self.shutter_speed_values = setting_config['shutter_speed']
        print(self.iso_values, self.aperture_values, self.shutter_speed_values)
        self.set_camera_setting('iso', str(self.iso_values))
        self.set_camera_setting('aperture', str(self.aperture_values))
        self.set_camera_setting('shutterspeed', str(self.shutter_speed_values))
        print(f"Apply with settings - ISO: {self.iso_values}, Aperture: {self.aperture_values}, Shutter Speed: {self.shutter_speed_values}")

    def read(self):
        # 內部循環最多等待 5 秒，嘗試取得一張完整的 JPEG 影像
        start_time = time.time()
        timeout = 5.0
        while time.time() - start_time < timeout:
            rlist, _, _ = select.select([self.process.stdout], [], [], 0.1)
            if self.process.stdout in rlist:
                data = self.process.stdout.read(4096)
                if data:
                    self.buffer += data
                start_idx = self.buffer.find(b'\xff\xd8')
                end_idx = self.buffer.find(b'\xff\xd9')
                if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                    end_idx += 2
                    jpg = self.buffer[start_idx:end_idx]
                    self.buffer = self.buffer[end_idx:]
                    frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                    if frame is not None:
                        return True, frame
            else:
                time.sleep(0.1)
        return False, None
    
    def isOpened(self):
        return self.process.poll() is None

    def release(self):
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill()

# FrameGrabber 類別：持續讀取最新影像（適用於 DSLRCapture 或 cv2.VideoCapture）
class FrameGrabber:
    def __init__(self, cap):
        self.cap = cap
        self.latest_frame = None
        self.running = True
        self.lock = threading.Lock()
        self.thread = threading.Thread(target=self.grab_frames, daemon=True)
        self.thread.start()
        
    def grab_frames(self):
        while self.running:
            # 針對 cap 類型，呼叫 read() 方法
            ret_frame = self.cap.read()
            # 如果是 cv2.VideoCapture，read() 返回 (ret, frame)
            if isinstance(ret_frame, tuple):
                ret, frame = ret_frame
            else:
                ret, frame = ret_frame, None  # 這裡通常不會發生
            if ret and frame is not None:
                with self.lock:
                    self.latest_frame = frame
            time.sleep(0.01)
            
    def get_frame(self):
        with self.lock:
            return self.latest_frame
        
    def stop(self):
        self.running = False
        self.thread.join()

# MotionDetector 類別
class MotionDetector:
    def __init__(self, cap, background_path="background.jpg", detect_interval=0.5, text_num=50, zoom=0, 
                 audio_detach=False, audio_playlist=['isart', 'notart', 'describe'], printer_detach=False, printer_list=[], high_sync=False):
        self.cap = cap
        if hasattr(self.cap, "isOpened"):
            if not self.cap.isOpened():
                log_and_print("Failed to open camera.", 'error')
                raise RuntimeError("Failed to open camera.")
        self.background_path = background_path
        self.detect_interval = detect_interval
        self.last_detect_time = time.time()
        self.zoom = zoom

        self.audio_detach = audio_detach
        self.audio_playlist = audio_playlist

        self.printer_detach = printer_detach
        self.printer_list = printer_list

        if len(self.audio_playlist) == 0 and len(self.printer_list) == 0:
            log_and_print("No action specified", 'error')
            raise ValueError("No action specified")

        self.resized_shape = (224, 224)
        # 建立 frame grabber 以持續取得最新影像
        self.frame_grabber = FrameGrabber(self.cap)
        self.background = self.initialize_background()
        self.state = "IDLE"
        self.last_frame = None
        self.text_num = text_num
        self.intro_sound_path = r'intro_alloy.mp3'
        self.high_sync = high_sync
        # 定義一個差異容許值，低於此值即視為「無變化」
        self.diff_threshold = self.resized_shape[0] * self.resized_shape[1] * 0.05

    def center_crop(self, img, gray_resize_blur=False):
        img = np.array(img)
        height, width = img.shape[:2]
        new_width = min(width, height)
        left, top = (width - new_width) // 2, (height - new_width) // 2
        img = img[top:top+new_width, left:left+new_width]
        if self.zoom == 0:
            pass
        elif self.zoom > 0:
            zoom_ratio = 1 + (self.zoom / 10)
            zoomed_size = int(new_width / zoom_ratio)
            crop_size = (new_width - zoomed_size) // 2
            img = img[crop_size:crop_size+zoomed_size, crop_size:crop_size+zoomed_size]
        else:
            log_and_print("zoom must be non-negative", 'error')
            raise ValueError("zoom must be non-negative")
        if gray_resize_blur:
            if img.ndim == 3 and img.shape[2] == 3:
                img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            img = cv2.resize(img, self.resized_shape)
            img = cv2.GaussianBlur(img, (15, 15), 0)
        return img

    def initialize_background(self):
        # DSLR 模式下等待較長時間以讓 live view 穩定
        if isinstance(self.cap, DSLRCapture):
            log_and_print("Waiting for DSLR live view to stabilize...", "info")
            time.sleep(5)
        attempts = 0
        frame = self.frame_grabber.get_frame()
        while frame is None and attempts < 20:
            log_and_print(f"Attempt {attempts+1}: No background frame available. Retrying...", "info")
            time.sleep(0.2)
            frame = self.frame_grabber.get_frame()
            attempts += 1
        if frame is None:
            log_and_print("Failed to capture image from camera.", "error")
            raise RuntimeError("Failed to capture image from camera.")
        frame = self.center_crop(frame, gray_resize_blur=True)
        cv2.imwrite(self.background_path, frame)
        log_and_print("Background captured successfully.", "info")
        return frame

    def compare(self, baseline):
        frame = self.frame_grabber.get_frame()
        if frame is None:
            log_and_print("No frame available.", 'error')
            return None, None, None, 0
        processed_img = self.center_crop(frame, gray_resize_blur=True)
        diff = cv2.absdiff(baseline, processed_img)
        _, diff = cv2.threshold(diff, 50, 255, cv2.THRESH_BINARY)
        current_time = time.time()
        return diff, processed_img, frame, current_time - self.last_detect_time

    def state_machine(self):
        start = time.time()
        if self.state == "IDLE":
            diff, frame, image, interval = self.compare(self.background)
            if diff is not None and np.sum(diff) > 0 and interval > self.detect_interval:
                self.state = "CHANGE"
                self.last_detect_time = time.time()
                self.last_frame = frame
        elif self.state == "CHANGE":
            last_frame_diff, last_frame, last_image, last_frame_interval = self.compare(self.last_frame)
            background_diff, background_frame, background_image, background_interval = self.compare(self.background)
            if background_diff is not None and np.sum(background_diff) == 0 and background_interval > self.detect_interval:
                self.state = "IDLE"
                self.last_detect_time = time.time()
            # 將判定條件改為低於 diff_threshold 而非完全等於 0
            elif last_frame_diff is not None and np.sum(last_frame_diff) < self.diff_threshold and last_frame_interval > self.detect_interval:
                self.state = "DETECTED"
                threading.Thread(target=self.trigger_action, args=(last_image,)).start()
                self.last_detect_time = time.time()
            elif last_frame_diff is not None and np.sum(last_frame_diff) >= self.diff_threshold and last_frame_interval > self.detect_interval:
                self.state = "CHANGE"
                self.last_detect_time = time.time()
                self.last_frame = last_frame
        elif self.state == "DETECTED":
            diff, frame, image, interval = self.compare(self.last_frame)
            # 同樣使用 diff_threshold 判定
            if diff is not None and np.sum(diff) < self.diff_threshold and interval > self.detect_interval:
                self.state = "DETECTED"
                self.last_detect_time = time.time()
            elif diff is not None and np.sum(diff) >= self.diff_threshold and interval > self.detect_interval:
                self.state = "CHANGE"
                self.last_detect_time = time.time()
                self.last_frame = frame
        end = time.time()
        print(self.state, round(1 / (end - start), 4), end='\r')

    def socket_playaudio(self, type, audio_path):
        try:
            socket = MacSocket(type)
            socket.send_file(audio_path)
            socket.end_connection()
        except:
            log_and_print("Socket connection failed for audio", 'error')
            raise RuntimeError("Socket connection failed for audio")
        
    def socket_printtext(self, printer_name, text):
        try:
            socket = MacSocket(printer_name)
            socket.send_printer_text(text)
            socket.end_connection()
        except:
            log_and_print("Socket connection failed for printer", 'error')
            raise RuntimeError("Socket connection failed for printer")
        
    def socket_playintro(self):
        try:
            time.sleep(1)
            socket = MacSocket(self.audio_playlist[0])
            socket.send_msg("play_intro")
            socket.end_connection()
        except:
            log_and_print("Socket connection failed for intro", 'error')
            raise RuntimeError("Socket connection failed for intro")

    def image_to_audio(self, base64_image, type):
        type_mapping = {
            'describe': (lambda img: gpt_utils.describe_iamge(img, text_num=self.text_num), 'describe'),
            'isart': (lambda img: gpt_utils.is_art(img, text_num=self.text_num), 'isart'),
            'notart': (lambda img: gpt_utils.not_art(img, text_num=self.text_num), 'notart')
        }
        if type not in type_mapping:
            log_and_print("type must be 'describe', 'isart', or 'notart'", 'error')
            raise ValueError("type must be 'describe', 'isart', or 'notart'")
        text_func, prefix = type_mapping[type]
        text = text_func(base64_image)
        audio_path = TTS_utils.openai_tts(text, prefix=prefix, voice='random')
        if self.audio_detach:
            threading.Thread(target=self.socket_playaudio, args=(type, audio_path)).start()
        else:
            threading.Thread(target=sound.play_mp3, args=(audio_path,)).start()

    def high_sync_image_to_audio(self, base64_image):
        type_mapping = {
            'describe': (lambda img: gpt_utils.describe_iamge(img, text_num=self.text_num), 'describe'),
            'isart': (lambda img: gpt_utils.is_art(img, text_num=self.text_num), 'isart'),
            'notart': (lambda img: gpt_utils.not_art(img, text_num=self.text_num), 'notart')
        }
        for type in self.audio_playlist:
            text_func, prefix = type_mapping[type]
            text = text_func(base64_image)
            audio_path = TTS_utils.openai_tts(text, prefix=prefix, voice='random')
            if self.audio_detach:
                threading.Thread(target=self.socket_playaudio, args=(type, audio_path)).start()
            else:
                threading.Thread(target=sound.play_mp3, args=(audio_path,)).start()

    def image_to_printer(self, base64_image, printer_name):
        type_mapping = {
            'describe': (lambda img: gpt_utils.describe_iamge(img, text_num=self.text_num), 'describe'),
            'isart': (lambda img: gpt_utils.is_art(img, text_num=self.text_num), 'isart'),
            'notart': (lambda img: gpt_utils.not_art(img, text_num=self.text_num), 'notart')
        }

        for type in self.printer_list:
            text_func, prefix = type_mapping[type]
            text = text_func(base64_image)
            print(text)
            if self.printer_detach:
                threading.Thread(target=self.socket_printtext, args=(printer_name, text)).start()
            else:
                self.printer_manager.print_text(text)

    def trigger_action(self, image):
        log_and_print("NOW TRIGGER ACTION with new image", 'info')

        height, width = image.shape[:2]
        size = min(width, height)
        start_x = (width - size) // 2
        start_y = (height - size) // 2
        image = image[start_y:start_y+size, start_x:start_x+size]
        image = self.center_crop(image, gray_resize_blur=False)
        image = gpt_utils.npimageResize(image, 0.5)
        base64_image = gpt_utils.image2base64(image)

        self.image_to_printer(base64_image, 'printer')
        # self.socket_printtext('printer', 'THIS IS A PRINTER TEST TEXT')

        # if self.audio_detach:
        #     threading.Thread(target=self.socket_playintro).start()
        # else:
        #     threading.Thread(target=sound.play_mp3, args=(self.intro_sound_path,)).start()
        # if self.high_sync:
        #     self.high_sync_image_to_audio(base64_image)
        # else:
        #     for audio_type in self.audio_playlist:
        #         self.image_to_audio(base64_image, audio_type)
            
    def run(self):
        while True:
            self.state_machine()

if __name__ == "__main__":
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    logname = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    logging.basicConfig(
        filename=os.path.join(log_dir, f'{logname}.log'),
        filemode='a',
        format='%(asctime)s\t %(levelname)s\t %(message)s',
        datefmt='%H:%M:%S',
        level=logging.DEBUG
    )

    parser = argparse.ArgumentParser()
    parser.add_argument("--zoom", type=float, default=5)
    parser.add_argument("--text_num", type=int, default=100)
    parser.add_argument("--detect_interval", type=int, default=2.5)
    parser.add_argument("--audio_detach", type=str, default='False')
    parser.add_argument("--audio_playlist", type=str, default='I')
    parser.add_argument("--printer_detach", type=str, default='False')
    parser.add_argument("--printer_list", type=str, default='I')
    parser.add_argument("--high_sync", type=str, default='False')
    parser.add_argument("--dslr", action="store_true", help="Use DSLR for live view and parameter adjustment")
    args = parser.parse_args()
    
    log_and_print(f'now activating pedestal', 'info')
    log_and_print(f'zoom: {args.zoom}', 'info')
    log_and_print(f'text_num: {args.text_num}', 'info')
    log_and_print(f'detect_interval: {args.detect_interval}', 'info')
    playlist_dict = {'I': ['isart'], 'N': ['notart'], 'D': ['describe']}
    playlist = [item for char in args.audio_playlist 
                for item in playlist_dict.get(char, [])]
    log_and_print(f'audio_playlist: {playlist}', 'info')
    audio_detach = False if args.audio_detach != 'True' else True
    log_and_print(f'audio_detach: {audio_detach}', 'info')

    printer_list = [item for char in args.printer_list
                    for item in playlist_dict.get(char, [])]
    log_and_print(f'printer_list: {printer_list}', 'info')
    printer_detach = False if args.printer_detach != 'True' else True
    log_and_print(f'printer_detach: {printer_detach}', 'info')

    high_sync = False if args.high_sync != 'True' else True
    log_and_print(f'high_sync: {high_sync}', 'info')
    log_and_print('================================================================================', 'info')
    log_and_print("Now activating pedestal", 'info')
    
    if args.dslr:
        cap = DSLRCapture()
    else:
        cap = cv2.VideoCapture(0)
    
    detector = MotionDetector(cap, zoom=args.zoom, text_num=args.text_num, detect_interval=args.detect_interval,
                                audio_detach=audio_detach, audio_playlist=playlist, printer_detach=printer_detach, printer_list=printer_list, high_sync=high_sync)
    detector.run()
    
    # python run.py --zoom 5 --audio_playlist ID --dslr
    # sudo python run.py --dslr --printer_detach True --printer_list I
