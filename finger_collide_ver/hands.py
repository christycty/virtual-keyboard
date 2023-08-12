import cv2
import numpy as np
from mediapipe.framework.formats import landmark_pb2
from mediapipe import solutions

from typing import Mapping, Tuple
from mediapipe.python.solutions.drawing_utils import DrawingSpec
from mediapipe.python.solutions import hands_connections

from finger import Finger

BLUE = (249, 209, 101)
WHITE = (255, 255, 255)


class Hands:
    def __init__(self):
        # detection results
        self.handedness_list = None
        self.hand_landmarks_list = None
        self.world_landmarks_list = None

        # finger objects
        self.fingers = []
        self.init_fingers()
        
        # check if index and thumb collides
        self.TOUCH_THRESHOLD = 0.015
        
        self.left_dist = 0
        self.right_dist = 0
        
        self.left_touch = False
        self.right_touch = False

        # formatting
        self.LR_text_format = {
            "MARGIN": 10,
            "FONT_SIZE": 1,
            "FONT_THICKNESS": 2,
            "TEXT_COLOR": BLUE,
        }

        self.landmark_text_format = {
            "FONT_SIZE": 0.5,
            "FONT_THICKNESS": 1,
            "TEXT_COLOR": BLUE,
        }
    
    # create the 10 finger objects
    def init_fingers(self):
        finger_names = ["THUMB", "INDEX", "MIDDLE", "RING", "PINKY"]
        hands = ["Left", "Right"]
        for hand in hands:
            for finger_id, finger_name in enumerate(finger_names):
                finger = Finger(finger_name, finger_id, hand)
                self.fingers.append(finger)
        
    # interpret and store hand landmark detection result
    # may add more processing here
    def process_results(self, detection_result, timestamp, keyboard):
        # no hand present
        if detection_result == None:
            self.hand_landmarks_list = None
            self.world_landmarks_list = None
            self.handedness_list = None
        else:
            self.hand_landmarks_list = detection_result.hand_landmarks
            self.world_landmarks_list = detection_result.hand_world_landmarks
            self.handedness_list = detection_result.handedness
        
        # update finger
        self.update_finger(keyboard)
        
        # check for key typed
        typed = self.detect_type()
        if typed != "":
            for letter in typed:
                keyboard.type_key(letter)

    def update_finger(self, keyboard):
        index_displacement = {"Left": 0, "Right": 5}
        
        # to identify which fingers absent
        on_screen_fingers = []
        
        # for each hand on screen
        for hand_id, handedness in enumerate(self.handedness_list):
            start_id = index_displacement[handedness[0].category_name]

            # for each finger in hand
            for idx in range(0, 5):
                finger = start_id + idx
                
                # retrieve landmark
                landmark_id = 4 * (idx + 1)
                wlandmark = self.world_landmarks_list[hand_id][landmark_id]
                nlandmark = self.hand_landmarks_list[hand_id][landmark_id]

                self.fingers[finger].update_present(wlandmark, nlandmark, keyboard)
                
                on_screen_fingers.append(finger)
                
        # update for all absent fingers     
        for finger_id in range(10):
            if finger_id not in on_screen_fingers:
                self.fingers[finger_id].update_absent()

    def calc_dist(self, a, b):
        D = ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5
        return D
        
    # detect if key is pressed
    def detect_type(self):
        self.left_dist = self.calc_dist(self.fingers[0].tip_wcoor, self.fingers[1].tip_wcoor)
        self.right_dist = self.calc_dist(self.fingers[5].tip_wcoor, self.fingers[6].tip_wcoor)
        
        typed = ""
        if self.left_dist <= self.TOUCH_THRESHOLD \
            and self.fingers[0].on_key == self.fingers[1].on_key \
                and self.fingers[0].on_key != -1:
                    if not self.left_touch:
                        # print(f"type key {self.fingers[0].on_key}")
                        typed += self.fingers[0].on_key
                    self.left_touch = True
        else:
            self.left_touch = False
                    
        if self.right_dist <= self.TOUCH_THRESHOLD \
            and self.fingers[5].on_key == self.fingers[6].on_key \
                and self.fingers[5].on_key != -1:
                    if not self.right_touch:
                        # print(f"type key {self.fingers[5].on_key}")
                        typed += self.fingers[5].on_key
                        
                    self.right_touch = True
        else:
            self.right_touch = False

        return typed

    ######## DRAWING UTILITIES #########
    def draw_text(self, img, text, text_x, text_y):
        cv2.putText(
            img,
            text,
            (text_x, text_y),
            cv2.FONT_HERSHEY_DUPLEX,
            self.landmark_text_format["FONT_SIZE"],
            self.landmark_text_format["TEXT_COLOR"],
            self.landmark_text_format["FONT_THICKNESS"],
            cv2.LINE_AA,
        )
        
        
    def draw_fingertips(self, img):
        annotated_img = np.copy(img)

        text_start_pos = {"Left": 20, "Right": 400}
        finger_displacement = {"Left": 0, "Right": 5}

        for hand_id, hand in enumerate(self.handedness_list):
            text_x = text_start_pos[hand[0].category_name]
            text_y = 40

            for finger in range(5):
                finger_id = finger + finger_displacement[hand[0].category_name]
                landmark_id = 4 * (finger + 1)
                landmark = self.world_landmarks_list[hand_id][landmark_id]
                # landmark = self.hand_landmarks_list[hand_id][landmark_id]

                x, y, z = landmark.x, landmark.y, landmark.z
                text = f"{finger+1} ({self.fingers[finger_id].on_key}): x {x*100:.1f}; y {y*100:.1f}; z {z*100:.1f}"

                self.draw_text(annotated_img, text, text_x, text_y)
                text_y += 15
                
            text = self.left_dist if hand[0].category_name == "Left" else self.right_dist
            text = str(text)
            self.draw_text(annotated_img, text, text_x, text_y)

        return annotated_img

    # show coordinates of specified landmarks
    def draw_finger(self, img):
        annotated_img = np.copy(img)

        # extract which hand is right hand
        hand_id = -1
        for id, hand in enumerate(self.handedness_list):
            if hand[0].category_name == "Right":
                hand_id = id

        if hand_id == -1:
            return annotated_img

        # right hand index finger
        landmark_id_list = [5, 6, 7, 8]
        landmark_names = ["MCP", "DIP", "PIP", "TIP"]
        local_text_x, text_y = 20, 40
        world_text_x = 400
        for idx, landmark_id in enumerate(landmark_id_list):
            # parse landmark coordinates
            landmark = self.hand_landmarks_list[hand_id][landmark_id]
            x, y, z = landmark.x, landmark.y, landmark.z
            text = f"{landmark_names[idx]}: x {x*100:.1f}; y {y*100:.1f}; z {z*100:.1f}"

            cv2.putText(
                annotated_img,
                text,
                (local_text_x, text_y),
                cv2.FONT_HERSHEY_DUPLEX,
                self.landmark_text_format["FONT_SIZE"],
                self.landmark_text_format["TEXT_COLOR"],
                self.landmark_text_format["FONT_THICKNESS"],
                cv2.LINE_AA,
            )

            landmark = self.world_landmarks_list[hand_id][landmark_id]
            x, y, z = landmark.x, landmark.y, landmark.z
            text = f"{landmark_names[idx]}: x {x*100:.1f}; y {y*100:.1f}; z {z*100:.1f}"
            cv2.putText(
                annotated_img,
                text,
                (world_text_x, text_y),
                cv2.FONT_HERSHEY_DUPLEX,
                self.landmark_text_format["FONT_SIZE"],
                self.landmark_text_format["TEXT_COLOR"],
                self.landmark_text_format["FONT_THICKNESS"],
                cv2.LINE_AA,
            )

            text_y += 15

        return annotated_img

    def simple_hand_landmark_style(self) -> Mapping[Tuple[int, int], DrawingSpec]:
        hand_landmark_style = {}
        spec = DrawingSpec(color=BLUE, thickness=-1, circle_radius=5)

        for landmark_id in range(21):
            hand_landmark_style[landmark_id] = spec

        return hand_landmark_style

    def simple_hand_connection_style(self) -> Mapping[Tuple[int, int], DrawingSpec]:
        hand_connection_style = {}
        spec = DrawingSpec(color=WHITE, thickness=2)

        for conn in hands_connections.HAND_CONNECTIONS:
            hand_connection_style[conn] = spec

        return hand_connection_style

    def draw_landmarks_on_image(self, rgb_image):
        annotated_image = np.copy(rgb_image)

        # Loop through the detected hands to visualize.
        for idx in range(len(self.hand_landmarks_list)):
            hand_landmarks = self.hand_landmarks_list[idx]
            handedness = self.handedness_list[idx]

            # Draw the hand landmarks.
            hand_landmarks_proto = landmark_pb2.NormalizedLandmarkList()
            hand_landmarks_proto.landmark.extend(
                [
                    landmark_pb2.NormalizedLandmark(
                        x=landmark.x, y=landmark.y, z=landmark.z
                    )
                    for landmark in hand_landmarks
                ]
            )
            solutions.drawing_utils.draw_landmarks(
                annotated_image,
                hand_landmarks_proto,
                solutions.hands.HAND_CONNECTIONS,
                self.simple_hand_landmark_style(),
                self.simple_hand_connection_style(),
            )

            # Get the top left corner of the detected hand's bounding box.
            height, width, _ = annotated_image.shape
            x_coordinates = [landmark.x for landmark in hand_landmarks]
            y_coordinates = [landmark.y for landmark in hand_landmarks]
            text_x = int(min(x_coordinates) * width)
            text_y = int(min(y_coordinates) * height) - self.LR_text_format["MARGIN"]

            # Draw handedness (left or right hand) on the image.
            cv2.putText(
                annotated_image,
                f"{handedness[0].category_name}",
                (text_x, text_y),
                cv2.FONT_HERSHEY_DUPLEX,
                self.LR_text_format["FONT_SIZE"],
                self.LR_text_format["TEXT_COLOR"],
                self.LR_text_format["FONT_THICKNESS"],
                cv2.LINE_AA,
            )

        return annotated_image
