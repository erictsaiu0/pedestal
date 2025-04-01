import os
import numpy as np
import cv2
import argparse
import gphoto2 as gp
import subprocess
import time
import select
import json

class CameraController:
    def __init__(self, use_dslr=False, camera_index=0, save_config_path=None):
        self.use_dslr = use_dslr
        if self.use_dslr:
            self.context = gp.gp_context_new()
            self.camera = gp.check_result(gp.gp_camera_new())
            gp.check_result(gp.gp_camera_init(self.camera, self.context))
            
            self.iso_values = [6400, 3200, 1600, 800, 400, 200, 100]
            self.aperture_values = ['16', '11', '8', '5.6', '4', '3.5']
            self.shutter_speed_values = ['1/1000', '1/500', '1/250', '1/125', '1/60', '1/30', '1/15', '1/8', '1/4', '1/2', '1']
            
            self.iso_index = 2           # 預設 1600
            self.aperture_index = 2        # 預設 '8'
            self.shutter_speed_index = 2   # 預設 '1/60'
            
            self.apply_settings()  # 初始參數設定
        else:
            self.cap = cv2.VideoCapture(camera_index)
            self.zoom = 0
        self.save_config_path = save_config_path

    def set_camera_setting(self, setting, value):
        try:
            config = gp.check_result(gp.gp_camera_get_config(self.camera, self.context))
            setting_config = gp.check_result(gp.gp_widget_get_child_by_name(config, setting))
            gp.check_result(gp.gp_widget_set_value(setting_config, value))
            gp.check_result(gp.gp_camera_set_config(self.camera, config, self.context))
        except gp.GPhoto2Error as e:
            print(f"Error setting '{setting}' to '{value}': {e}")

    def apply_settings(self):
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
        self.iso = self.iso_values[self.iso_index]
        self.aperture = self.aperture_values[self.aperture_index]
        self.shutter_speed = self.shutter_speed_values[self.shutter_speed_index]
        self.set_camera_setting('iso', str(self.iso))
        self.set_camera_setting('aperture', self.aperture)
        self.set_camera_setting('shutterspeed', self.shutter_speed)
        print(f"Updated settings - ISO: {self.iso}, Aperture: {self.aperture}, Shutter Speed: {self.shutter_speed}")

    def update_iso(self, value):
        self.iso_index = int(value)
        self.update_window_title()

    def update_aperture(self, value):
        self.aperture_index = int(value)
        self.update_window_title()

    def update_shutter_speed(self, value):
        self.shutter_speed_index = int(value)
        self.update_window_title()

    def update_window_title(self):
        title = f"ISO: {self.iso_values[self.iso_index]}, Aperture: {self.aperture_values[self.aperture_index]}, Shutter Speed: {self.shutter_speed_values[self.shutter_speed_index]} (Press 'u' to update)"
        cv2.setWindowTitle("DSLR Settings Adjustment", title)

    def start_live_view(self):
        self.process = subprocess.Popen(['gphoto2', '--capture-movie', '--stdout'],
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def stream_live_view(self):
        buffer = b""
        update_requested = False
        while True:
            # 使用 select 監控 stdout，timeout 設為 0.01 秒
            rlist, _, _ = select.select([self.process.stdout], [], [], 0.01)
            if self.process.stdout in rlist:
                data = self.process.stdout.read(4096)  # 一次讀取較大資料塊
                if not data:
                    break
                buffer += data

            # 當 buffer 中有完整 JPEG 時處理影像
            while b'\xff\xd8' in buffer and b'\xff\xd9' in buffer:
                start = buffer.find(b'\xff\xd8')
                end = buffer.find(b'\xff\xd9') + 2
                jpg = buffer[start:end]
                buffer = buffer[end:]
                image = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                if image is not None and image.size > 0:
                    cv2.imshow('Live View', image)
                key = cv2.waitKey(1)
                if key == ord('q'):
                    if self.save_config_path:
                        print(f"Now quiting, saving config to {self.save_config_path}") 
                        config = {'iso': self.iso_values[self.iso_index], 'aperture': self.aperture_values[self.aperture_index], 'shutter_speed': self.shutter_speed_values[self.shutter_speed_index]}
                        # overwrite the config file
                        with open(self.save_config_path, 'w') as f:
                            json.dump(config, f, indent=4)
                    return 'quit'
                elif key == ord('u'):
                    update_requested = True
                    break
            if update_requested:
                break
        return 'update'

    def update_zoom(self, zoom_value):
        self.zoom = max(1, zoom_value / 10)

    def center_crop(self, img):
        img = np.array(img)
        height, width = img.shape[:2]
        new_width = min(width, height)
        left, top = (width - new_width) // 2, (height - new_width) // 2
        img = img[top:top+new_width, left:left+new_width]
        if self.zoom > 0:
            zoom_ratio = 1 + (self.zoom/10)
            zoomed_size = int(new_width / zoom_ratio)
            crop_size = (new_width - zoomed_size) // 2
            img = img[crop_size:crop_size+zoomed_size, crop_size:crop_size+zoomed_size]
        return img

    def run(self):
        if self.use_dslr:
            cv2.namedWindow("DSLR Settings Adjustment")
            cv2.createTrackbar("ISO", "DSLR Settings Adjustment", self.iso_index, len(self.iso_values)-1, self.update_iso)
            cv2.createTrackbar("Aperture", "DSLR Settings Adjustment", self.aperture_index, len(self.aperture_values)-1, self.update_aperture)
            cv2.createTrackbar("Shutter Speed", "DSLR Settings Adjustment", self.shutter_speed_index, len(self.shutter_speed_values)-1, self.update_shutter_speed)
            self.update_window_title()
            print("Press 'u' to update settings, 'q' to quit.")
            while True:
                self.start_live_view()
                action = self.stream_live_view()
                if action == 'quit':
                    break
                elif action == 'update':
                    self.apply_settings()
            # 最後嘗試關閉相機連線，忽略找不到裝置的錯誤
            try:
                gp.check_result(gp.gp_camera_exit(self.camera, self.context))
            except gp.GPhoto2Error as e:
                if "-52" in str(e):
                    pass
                else:
                    print(f"Error during exit: {e}")
            cv2.destroyAllWindows()
        else:
            cv2.namedWindow("Zoom Adjustment")
            cv2.createTrackbar("Zoom", "Zoom Adjustment", int(self.zoom * 10), 100, self.update_zoom)
            while True:
                ret, frame = self.cap.read()
                if not ret:
                    raise RuntimeError("Failed to capture image from webcam.")
                processed_img = self.center_crop(frame)
                processed_img = cv2.resize(processed_img, (512, 512))
                window_title = f"Zoom Adjustment - Current Zoom: {self.zoom:.2f}"
                cv2.setWindowTitle("Zoom Adjustment", window_title)
                cv2.imshow("Zoom Adjustment", processed_img)
                key = cv2.waitKey(1)
                if key == ord("q"):
                    if self.save_config_path:
                        print(f"Now quiting, saving config to {self.save_config_path}") 
                        config = {'zoom': self.zoom}
                        with open(self.save_config_path, 'w') as f:
                            json.dump(config, f)
                    print("Final zoom value:", self.zoom)
                    break
                elif key == ord("s"):
                    cv2.imwrite("zoomin_check.jpg", processed_img)
                    print("Saved image to zoomin_check.jpg")
            cv2.destroyAllWindows()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dslr", action="store_true", help="Use DSLR for live view and parameter adjustment")
    parser.add_argument("--camera", type=int, default=0, help="Camera index for webcam")
    parser.add_argument("--save_config", type=str, default='camera_config.json', help="Path to save the camera configuration")
    args = parser.parse_args()
    controller = CameraController(use_dslr=args.dslr, camera_index=args.camera, save_config_path=args.save_config)
    controller.run()
