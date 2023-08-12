import numpy as np


class Finger:
    def __init__(self, name, name_id, handedness):
        # identify finger
        self.name = name                # THUMB/INDEX/MIDDLE/RING/PINKY
        self.name_id = name_id          # 0-4
        self.handedness = handedness    # Left or Right

        # finger state
        self.on_key = -1                # which key finger is on                
        self.on_screen = False          # present on screen?
        
        # position related
        self.tip_wcoor = [0, 0, 0]           # current tip position (world coor)
        self.tip_ncoor = [0, 0, 0]           # current tip pos (normalized coor)
    
    # update finger present on screen
    def update_present(self, wlandmark, nlandmark, keyboard):
        # update fingertip coordinates
        self.tip_wcoor = [wlandmark.x, wlandmark.y, wlandmark.z * 100]
        self.tip_ncoor = [nlandmark.x, nlandmark.y, nlandmark.z]
        
        # query currently lies on which key
        self.on_key = keyboard.query_key_id(self.tip_ncoor[0], self.tip_ncoor[1])
        self.on_screen = True

    # update finger out of screen
    def update_absent(self):
        self.tip_wcoor = [0, 0, 0]
        self.tip_ncoor = [0, 0, 0]
        
        self.on_screen = False
        self.on_key = -1