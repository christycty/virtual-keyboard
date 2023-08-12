import cv2
import numpy as np

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)


class Keyboard:
    def __init__(self):
        # top left corner
        self.keyboard_pos = (200, 300)

        # key size
        self.keysize = 80
        self.key_border = 8
        
        self.keycolor = BLACK
        self.key_opacity = 0.6
        self.key_type_opacity = 0.8

        self.text_pos = (30, 50)
        self.fontcolor = WHITE
        self.fonttype = cv2.FONT_HERSHEY_DUPLEX
        self.fontscale = 1

        # letters
        self.letters = [list("QWERTYUIOP"), list("ASDFGHJKL"), list("ZXCVBNM←")]                
        self.letter_pos = {}
        
        # typed letters
        self.typed = ""

    def type_key(self, letter):
        # print(f"type key {letter}")
        if letter == "←":
            if self.typed != "":
                self.typed = self.typed[:-1]
        else:
            self.typed += letter
        
    # return which key (x, y) lies on
    def query_key_id(self, x_norm, y_norm):        
        x = int(x_norm * 1280)
        y = int(y_norm * 720)
                
        for key, pos in self.letter_pos.items():
            # print(f"checking {key} {pos}")
            if pos[0] <= x and x <= pos[0] + self.keysize \
                and pos[1] <= y and y <= pos[1] + self.keysize:
                    # print(f"key name of {x}, {y} is {key}")
                    return key
        
        # print("no key is at query coordinates")
        return -1
        
        
    def draw_key(self, img, text, topx, topy):
        # mark letter key position
        self.letter_pos[text] = (topx, topy)
        
        # draw semi-transparent key
        img_key = img[topy : topy + self.keysize, topx : topx + self.keysize]

        key_rect = np.ones(img_key.shape, dtype=np.uint8)
        key_rect[:] = self.keycolor

        img_key = cv2.addWeighted(
            src1=img_key,
            alpha=self.key_opacity,
            src2=key_rect,
            beta=1 - self.key_opacity,
            gamma=0,
        )
        img[topy : topy + self.keysize, topx : topx + self.keysize] = img_key

        # draw key letter
        if text == "←":
            text = "<-"
            
        cv2.putText(
            img=img,
            text=text,
            org=(topx + self.text_pos[0], topy + self.text_pos[1]),
            fontFace=self.fonttype,
            fontScale=self.fontscale,
            color=self.fontcolor,
            thickness=1,
        )

    def draw_typed_words(self, src_img):
        img = np.copy(src_img)
        x, y = self.keyboard_pos[0], self.keyboard_pos[1] - 150
        text = self.typed
        cv2.putText(
            img=img,
            text=text,
            org=(x, y),
            fontFace=self.fonttype,
            fontScale=self.fontscale,
            color=self.fontcolor,
            thickness=1,
        )
        return img
    
    # draw keyboard on image
    def draw_keyboard_on_img(self, src_img):
        # print("start draw keyboard", src_img.shape)
        img = np.copy(src_img)
        try:
            (cur_x, cur_y) = self.keyboard_pos
            for id, row in enumerate(self.letters):
                for letter in row:
                    # print(letter)
                    self.draw_key(img, letter, cur_x, cur_y)
                    cur_x += self.keysize + self.key_border

                cur_y += self.keysize + self.key_border
                cur_x = self.keyboard_pos[0] + (self.keysize // 2) * (id + 1)
            
            img = self.draw_typed_words(img)
        except Exception as e:
            print(e)
    
        return img
