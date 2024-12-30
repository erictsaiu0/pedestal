import os
import numpy as np
import cv2

class ZoomInSetting:
    """
    This class helps users find the appropriate zoom-in parameter for the camera.
    """
    def __init__(self, cap=None):
        self.cap = cap
        self.zoom = 0
        self.save_path = "zoomin_check.jpg"
        self.test_img = cv2.imread(r"/Users/erictsai/Desktop/pedestal/triggered.jpg")

    def center_crop(self, img, gray_resize_blur=False):
        img = np.array(img)
        height, width = img.shape[:2]

        # Step 1: 基本裁切成正方形
        new_width = min(width, height)
        left, top = (width - new_width) // 2, (height - new_width) // 2
        img = img[top:top+new_width, left:left+new_width]

        # Step 2: 處理 zoom 的裁切
        if self.zoom == 0:
            # 當 zoom=0 時，直接返回中心正方形
            img = img
        elif self.zoom > 0:
            zoom_ratio = 1 + (self.zoom/10)
            zoomed_size = int(new_width / zoom_ratio)
            crop_size = (new_width - zoomed_size) // 2
            img = img[crop_size:crop_size+zoomed_size, crop_size:crop_size+zoomed_size]

        else:
            raise ValueError("zoom must be non-negative")

        # Step 3: 灰度轉換與高斯模糊（可選）
        if gray_resize_blur:
            if img.ndim == 3 and img.shape[2] == 3:
                img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            img = cv2.resize(img, (224, 224))
            img = cv2.GaussianBlur(img, (15, 15), 0)

        return img


    def update_zoom(self, zoom_value):
        """
        Update the zoom value based on the trackbar.
        """
        self.zoom = max(1, zoom_value / 10)  # Avoid zoom being less than 1

    def run(self):
        """
        Main loop to interactively adjust zoom and display the results.
        """
        cv2.namedWindow("Zoom Adjustment")

        # Create a trackbar to adjust zoom
        cv2.createTrackbar("Zoom", "Zoom Adjustment", int(self.zoom * 10), 50, self.update_zoom)

        while True:
            # Process the image with the current zoom
            processed_img = self.center_crop(self.test_img, gray_resize_blur=False)
            processed_img = cv2.resize(processed_img, (512, 512))
            # Update the window title to show the current zoom value
            window_title = f"Zoom Adjustment - Current Zoom: {self.zoom:.2f}"
            cv2.setWindowTitle("Zoom Adjustment", window_title)

            # Display the processed image
            cv2.imshow("Zoom Adjustment", processed_img)

            # Listen for key events
            key = cv2.waitKey(1)
            if key == ord("q"):  # Quit on 'q'
                print("final zoom value:", self.zoom)
                break
            elif key == ord("s"):  # Save on 's'
                cv2.imwrite(self.save_path, processed_img)
                print(f"Saved image to {self.save_path}")

        cv2.destroyAllWindows()

if __name__ == "__main__":
    cap = cv2.VideoCapture(0)
    checker = ZoomInSetting(cap)
    checker.run()


# class ZoomInSetting:
#     '''
#     This function is to find the appropriate zoom in parameter for the camera
#     '''
#     def __init__(self, cap):
#         self.cap = cap
#         self.zoom = 1.7
#         self.save_path = "zoomin_check.jpg"
#         self.test_img = cv2.imread(r"/Users/erictsai/Desktop/pedestal/triggered.jpg")
#     def center_crop(self, img, zoom=2, gray_resize_blur=False):
#         img = np.array(img)
#         height, width = img.shape[:2]

#         new_width = min(width, height)
#         left, top = (width - new_width) // 2, (height - new_width) // 2
#         img = img[top:top+new_width, left:left+new_width]

#         if zoom > 0:
#             zoom_ratio = 1 + (1 / zoom)
#             crop_size = int(new_width / zoom_ratio / 2)
#             if crop_size * 2 < new_width:
#                 img = img[crop_size:-crop_size, crop_size:-crop_size]
#             print(crop_size, img.shape)
#         elif zoom < 0:
#             raise ValueError("zoom must be non-negative")

#         if gray_resize_blur:
#             if img.ndim == 3 and img.shape[2] == 3:  # 確保是彩色圖片
#                 img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
#             img = cv2.resize(img, (224, 224))
#             img = cv2.GaussianBlur(img, (15, 15), 0)
#         return img

#     def test(self):
#         img = self.center_crop(self.test_img, zoom=self.zoom, gray_resize_blur=False)
#         cv2.imwrite(self.save_path, img)
#         return img
    
# if __name__ == "__main__":
#     checker = ZoomInSetting(None)
#     img = checker.test()