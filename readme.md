# TODO:
[] edit code to use finger class 
[] check key position on screen related to landmark pos

## Current Rules for detecting keyup/keydown
if originally down:
    if cur_z raise from anchor by over threshold: 
        set keyup
        anchor_pos = cur_z
    
    (either still downing or raising slowly)
    else:
        anchor_pos = min(cur_z, anchor_pos)

if originally up:
    (quick drop, likely a press)
    if cur_z drop from anchor by over threshold:
        push to keydown candidate
        anchor_pos = cur_z
    
    (downing slowly)
    elif cur_z drop from anchor by over threshold / 2:
        anchor_pos unchanged (still at position before "down")
    
    (maintaining up)
    else:
        anchor_pos = cur_z 

## TO ADD:
[] if landmark out of keyboard range, set as keyup only
[] only recognize keydown when finger stays on same key

## MAY ADD IF WANT:
[] different threshold for different fingers
[] calibration at start to log threshold for each finger
[] include x, y in movement detection (e.g. calc distance moved)