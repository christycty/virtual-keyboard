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
        self.KEYDOWN_DISTANCE_THRESHOLD = 0.8  # arbitrary threshold
        self.KEYDOWN_CANDIDATE_THRESHOLD = 3  # max #finger to count keydown

        # detection results
        self.handedness_list = None
        self.hand_landmarks_list = None
        self.world_landmarks_list = None

        self.fingers = []
        self.init_fingers()

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
    def process_results(self, detection_result, timestamp):
        # no hand present
        if detection_result == None:
            self.hand_landmarks_list = None
            self.world_landmarks_list = None
            self.handedness_list = None
        else:
            self.hand_landmarks_list = detection_result.hand_landmarks
            self.world_landmarks_list = detection_result.hand_world_landmarks
            self.handedness_list = detection_result.handedness

        # update finger position
        self.update_finger()
        
        # update keydown keyup
        # self.update_keystroke()
        # print("result stored in hands")
    
    def update_finger(self):
        # mark fingers on screen
        on_screen = []
        index_displacement = {"Left" : 0, "Right" : 5}
        
        for hand_id, hand in enumerate(self.handedness_list):
            for i in range(0, 5):                                
                landmark_id = 4 * (i + 1)
                landmark = self.world_landmarks_list[hand_id][landmark_id]
                
                finger_id = index_displacement[hand[0].category_name] + i
                on_screen.append(finger_id)
                self.fingers[finger_id].update_present(landmark)
        
        for finger_id in range(10):
            if finger_id not in on_screen:
                self.fingers[finger_id].update_absent()

    # TODO: update to use finger class
    def update_keystroke(self):
        index_displacement = {"Left": 0, "Right": 5}
        # update each finger state
        for hand_id, handedness in enumerate(self.handedness_list):
            start_id = index_displacement[handedness[0].category_name]

            # if <= 3 keydown, only down the one with greatest dist
            keydown_candidate = []

            for idx in range(0, 5):
                finger = start_id + idx
                landmark_id = 4 * (idx + 1)
                landmark = self.world_landmarks_list[hand_id][landmark_id]

                # non existent originally
                if self.finger_state[finger] == -1:
                    self.finger_state[finger] = 0
                    self.finger_tip_pos[finger] = landmark.z * 100
                    continue

                cur_z = landmark.z * 100
                prev_z = self.finger_tip_pos[finger]

                # key down originally
                if self.finger_state[finger] == 1:
                    # keyup motion detected
                    if (
                        abs(cur_z - prev_z) > self.KEYDOWN_DISTANCE_THRESHOLD
                        and cur_z > prev_z
                    ):
                        self.finger_state[finger] = 0
                        self.finger_tip_pos[finger] = cur_z
                    # mark lowest point in key press
                    else:
                        self.finger_tip_pos[finger] = min(
                            self.finger_tip_pos[finger], cur_z
                        )

                # key up originally
                elif self.finger_state[finger] == 0:
                    if (
                        abs(cur_z - prev_z) > self.KEYDOWN_DISTANCE_THRESHOLD
                        and cur_z < prev_z
                    ):
                        keydown_candidate.append((finger, abs(cur_z - prev_z)))
                        # self.finger_state[finger] = 1
                        self.finger_tip_pos[finger] = cur_z

                    # down-ing, don't update tip position (cater slow keydown)
                    elif (
                        cur_z < prev_z
                        and abs(cur_z - prev_z) > self.KEYDOWN_DISTANCE_THRESHOLD / 2
                    ):
                        continue
                    else:
                        self.finger_tip_pos[finger] = cur_z

            # exist keydown candidate & not whole hand move
            # add rule: need keydown on same key to hold
            # add rule: consider only if lay in keyboard
            if (
                keydown_candidate
                and len(keydown_candidate) <= self.KEYDOWN_CANDIDATE_THRESHOLD
            ):
                keydown_finger = min(keydown_candidate, key=lambda x: x[1])[0]
                self.finger_state[keydown_finger] = 1

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

                x, y, z = landmark.x, landmark.y, landmark.z
                text = f"{finger+1} ({self.fingers[finger_id].keydown}): x {x*100:.1f}; y {y*100:.1f}; z {z*100:.1f}"

                cv2.putText(
                    annotated_img,
                    text,
                    (text_x, text_y),
                    cv2.FONT_HERSHEY_DUPLEX,
                    self.landmark_text_format["FONT_SIZE"],
                    self.landmark_text_format["TEXT_COLOR"],
                    self.landmark_text_format["FONT_THICKNESS"],
                    cv2.LINE_AA,
                )
                text_y += 15

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
