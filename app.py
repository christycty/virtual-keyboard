import cv2
import time
import numpy as np
import mediapipe as mp

from keyboard import Keyboard
from hands import Hands
from landmarker import HandLandmarker


class App:
    def __init__(self):
        self.FPS = 10
        self.window_width = 1280
        self.window_height = 720

        self.raw_img = None
        self.annotated_img = None

        self.landmarker = HandLandmarker(self.print_result).landmarker
        self.keyboard = Keyboard()
        self.hands = Hands()

    def print_result(
        self,
        result: mp.tasks.vision.HandLandmarkerResult,
        output_image: mp.Image,
        timestamp_ms: int,
    ):
        # print("landmarker result activated")
        try:
            self.raw_img = output_image.numpy_view()
            self.hands.process_results(result, timestamp_ms)

        except Exception as e:
            print(e)

    def process_img(self):
        img = np.copy(self.raw_img)
        
        # draw stuff
        keyboard_img = self.keyboard.draw_keyboard_on_img(img)
        annotated_img = self.hands.draw_landmarks_on_image(keyboard_img)

        # draw finger landmark coordiates (for development use only)
        annotated_img = self.hands.draw_fingertips(annotated_img)

        self.annotated_img = annotated_img

    def run(self):
        capture = cv2.VideoCapture(0)
        capture.set(3, self.window_width)
        capture.set(4, self.window_height)

        while True:
            ret, opencv_image = capture.read()
            # print("image read")

            if ret:
                opencv_image = cv2.flip(opencv_image, 1)

                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=opencv_image)

                try:
                    timestamp = int(time.time() * 1000)
                    self.landmarker.detect_async(mp_image, timestamp)
                except Exception as e:
                    print("detect async exception", e)

                if self.raw_img is not None:
                    # process the raw image
                    try:
                        self.process_img()
                        # display annotated image
                        cv2.imshow("annotated", self.annotated_img)
                    except Exception as e:
                        print(e)

            # wait for escape key
            if cv2.waitKey(1000 // self.FPS) == 27:
                break

        capture.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    try:
        app = App()
        app.run()
    except Exception as e:
        print(e)
