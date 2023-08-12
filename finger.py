import numpy as np


class Finger:
    def __init__(self, name, name_id, handedness):
        self.KEYDOWN_DISTANCE_THRESHOLD = 0.8  # arbitrary threshold
        self.KEYUP_DISTANCE_THRESHOLD = 0.4  # arbitrary threshold
        
        # identify finger
        self.name = name                # THUMB/INDEX/MIDDLE/RING/PINKY
        self.name_id = name_id          # 0-4
        self.handedness = handedness    # Left or Right

        # on key
        self.on_key_name = -1           # which key fingertip is on (Q-M)
        self.on_key = -1                # which key name
        # self.prev_key_id = -1           # on which key in prev frame
        
        # state
        self.keydown = False                # if keydown
        self.on_screen = False              # present on screen?
        
        # position related
        self.tip_wcoor = None                 # current tip position (world coor)
        self.tip_ncoor = None                 # current tip pos (normalized coor)
        
        self.anchor_tip_wcoor = None          # anchor tip pos (for keyup/down detection)
        # anchor tip is the tip used for comparing with current tip position (e.g. peak/bottom values)
        
        # normalized coordinates -> related to screen
        # FUTURE: pos of other parts too
    
    # update finger present on screen
    def update_present(self, wlandmark, nlandmark, keyboard):
        # update fingertip coordinates
        self.tip_wcoor = [wlandmark.x, wlandmark.y, wlandmark.z * 100]
        self.tip_ncoor = [nlandmark.x, nlandmark.y, nlandmark.z]
        
        # query currently lies on which key
        cur_key = keyboard.query_key_id(self.tip_ncoor[0], self.tip_ncoor[1])

        # check for potential keydown
        possible_keydown = False
        displacement = 0
        
        # originally not existing
        if not self.on_screen:
            self.anchor_tip_wcoor = self.tip_wcoor 
            self.keydown = False
            self.on_screen = True
        
        # originally down
        elif self.on_screen and self.keydown:
            # keyup motion detected
            if self.tip_wcoor[2] - self.anchor_tip_wcoor[2] > self.KEYUP_DISTANCE_THRESHOLD:
                self.keydown = False
                self.anchor_tip_wcoor[2] = self.tip_wcoor[2]
                
            # slowly up / still dropping
            else:
                # mark lowest point in key press as anchor
                self.anchor_tip_wcoor[2] = min (
                     self.anchor_tip_wcoor[2],
                     self.tip_wcoor[2]
                )
        
        # originally up
        elif self.on_screen and not self.keydown:
            # on the way of key down
            # may add threshold on down coordinates here too
            if cur_key == self.on_key \
            and self.on_key != -1 and cur_key != -1 \
            and self.anchor_tip_wcoor[2] > self.tip_wcoor[2]:
                # pass threshold
                if self.anchor_tip_wcoor[2] - self.tip_wcoor[2] > self.KEYDOWN_DISTANCE_THRESHOLD:
                    # push to keydown candidate
                    possible_keydown = True
                    displacement = self.anchor_tip_wcoor[2] - self.tip_wcoor[2]
                    # print(f"potential keydown {self.name} on {cur_key}")
                    
                    self.anchor_tip_wcoor[2] = self.tip_wcoor[2]

                # on the way down, anchor unchanged (peak pos)
                else:
                    # print("on the way down")
                    pass 
            # maintaining keyup
            else:
                # print("maintaining keyup")
                self.anchor_tip_wcoor[2] = self.tip_wcoor[2]

        # update key id
        # print("updating key id")
        self.on_key = cur_key
        
        return possible_keydown, displacement
    

    # update finger out of screen
    def update_absent(self):
        self.on_screen = 0
        self.on_key = -1
        
    def set_keydown(self):
        # print(f"set finger {self.name} to keydown on {self.on_key}")
        self.keydown = True
        return self.on_key