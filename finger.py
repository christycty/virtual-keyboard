import numpy as np


class Finger:
    def __init__(self, name, name_id, handedness):
        # identify finger
        self.name = name                # THUMB/INDEX/MIDDLE/RING/PINKY
        self.name_id = name_id          # 0-4
        self.handedness = handedness    # Left or Right

        # on key
        self.on_key_name = -1           # which key fingertip is on (Q-M)
        self.on_key_id = -1             # 0-25    
        self.prev_key_id = -1           # on which key in prev frame
        
        # state
        self.keydown = 0                # if keydown
        self.on_screen = 0              # present on screen?
        
        # position related
        self.tip = None                 # current tip position (tuple)
        self.anchor_tip = None          # anchor tip pos (for keyup/down detection)
        
        
        # normalized coordinates -> related to screen
        # separately store world and norm coor
        # FUTURE: pos of other parts too
    
    # update finger present on screen
    def update_present(self, landmark):
        self.tip = (landmark.x, landmark.y, landmark.z) 
        
        if not self.on_screen:
            self.anchor_tip = self.tip        
        
        # check for on key
        self.prev_key_id = self.on_key_id
        
        # TODO: set on_key_id
        
        
        self.on_screen = 1
    
    # update finger out of screen
    def update_absent(self):
        self.on_screen = 0
        self.on_key_id = -1
        