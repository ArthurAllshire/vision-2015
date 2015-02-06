import cv2
import numpy as np
import freenect
from collections import OrderedDict
from parseconfig import parse_config
from colour import *

class TrackDepth(object):
    def __init__(self):
        pass
    
    def mask_depth(self, depth, mask):
        result = cv2.bitwise_and(depth,depth, mask=mask)
        return result
    
    def get_depth(self):
        array,_ = freenect.sync_get_depth()
        
        array = np.multiply(array, 255.0/2048)
        max = np.max(array)
        min = np.min(array)
        array = array.astype(np.uint8)
        print max, min
        return array
    
if __name__ == "__main__":
    track_colour = TrackColour()
    track_depth = TrackDepth()
    
    
    while True:
        mask, colour_img, contour = track_colour.find_contour(track_colour.erdi(track_colour.threshold(track_colour.get_video())))
        image = track_depth.mask_depth(track_depth.get_depth(), mask)
        cv2.imshow("Depth Mask", image)
        cv2.imshow("Colour", colour_img)
        k = cv2.waitKey(5) & 0xFF
        if k == 27:
            break