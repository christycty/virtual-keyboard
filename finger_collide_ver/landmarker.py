import mediapipe as mp


class HandLandmarker:
    def __init__(self, func):
        self.hand_landmarker_path = "hand_landmarker.task"

        self.options = self.set_options(func)

        self.landmarker = mp.tasks.vision.HandLandmarker.create_from_options(
            self.options
        )

    def set_options(self, func):
        BaseOptions = mp.tasks.BaseOptions
        HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
        VisionRunningMode = mp.tasks.vision.RunningMode

        options = HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=self.hand_landmarker_path),
            running_mode=VisionRunningMode.LIVE_STREAM,
            num_hands=2,
            result_callback=func,
        )

        return options
