import gphoto2 as gp
import subprocess
import cv2
import numpy as np
from utils import log_and_print

def set_camera_setting(camera, context, setting, value):
    """Set a specific camera setting."""
    try:
        config = gp.check_result(gp.gp_camera_get_config(camera, context))
        setting_config = gp.check_result(gp.gp_widget_get_child_by_name(config, setting))
        gp.check_result(gp.gp_widget_set_value(setting_config, value))
        gp.check_result(gp.gp_camera_set_config(camera, config, context))
    except gp.GPhoto2Error as e:
        log_and_print(f"Error setting '{setting}' to '{value}': {e}", 'error')

def start_live_view():
    """Start the live view process using gphoto2."""
    return subprocess.Popen(['gphoto2', '--capture-movie', '--stdout'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def stream_live_view(process):
    """Stream the live view using OpenCV."""
    buffer = b""
    while True:
        data = process.stdout.read(1024)
        if not data:
            break
        buffer += data
        while b'\xff\xd8' in buffer and b'\xff\xd9' in buffer:
            start = buffer.find(b'\xff\xd8')
            end = buffer.find(b'\xff\xd9') + 2
            jpg = buffer[start:end]
            buffer = buffer[end:]
            image = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
            print(image.shape)
            cv2.imshow('Live View', image)
            if cv2.waitKey(1) == ord('q'):
                process.terminate()
                cv2.destroyAllWindows()
                return

def main():
    context = gp.gp_context_new()
    camera = gp.check_result(gp.gp_camera_new())
    gp.check_result(gp.gp_camera_init(camera, context))

    # Set camera parameters
    set_camera_setting(camera, context, 'iso', '3200')
    set_camera_setting(camera, context, 'aperture', '4')
    set_camera_setting(camera, context, 'shutterspeed', '1/200')
    set_camera_setting(camera, context, 'imageformatsd', 'Tiny JPEG')

    # Start live view streaming
    process = start_live_view()
    stream_live_view(process)

    gp.check_result(gp.gp_camera_exit(camera, context))

if __name__ == '__main__':
    main()
