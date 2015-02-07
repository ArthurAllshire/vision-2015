import cv2
import numpy as np
import freenect
from collections import OrderedDict
from parseconfig import parse_config
from colour import *

class TrackDepth(object):
    def __init__(self):
        self.configuration = parse_config('track-depth')
    
    def mask_depth(self, depth, mask):
        result = cv2.bitwise_and(depth,depth, mask=mask)
        return result
    
    def get_depth(self):
        array,_ = freenect.sync_get_depth()
        
        array = np.multiply(array, 255.0/2048)
        max = np.max(array)
        min = np.min(array)
        array = array.astype(np.uint8)
        return array
    
    def white_threshold(self, depth_image, mask):
        ret, thresh = cv2.threshold(depth_image, 240, 255,cv2.THRESH_BINARY_INV)
        mask = cv2.bitwise_and(mask, thresh)
        return mask
    
    def find_sides(self, depth_image, mask, rect):
        (x, y, w, h) = rect
        if x is not 0:
            means = []
            depth_image = depth_image[y: y + h, x : x + w]
            mask = mask[y: y + h, x : x + w]
            height, width = depth_image.shape
            smallest_mean_index = -1
            smallest_mean = 256
            print "Width: " + str(width) + ", Height: " + str(height)
            for column in range(0, w, self.configuration['mean_band_size']):
                mean = cv2.mean(depth_image[:,column:column+self.configuration['mean_band_size']], mask[:,column:column+self.configuration['mean_band_size']])[0]
                print "Mean: " + str(mean) + ", X: " + str(column)
                means.append(mean)
                if mean < smallest_mean:
                    smallest_mean = mean
                    smallest_mean_index = column/self.configuration['mean_band_size']
            
            if means[0] < means[-1]:
                print "left is short side"
                cv2.line(depth_image, (0, 0), (0, height), (255, 255, 255),5);
            else:
                print "right is short side"
                cv2.line(depth_image, (width, 0), (width, height), (255, 255, 255),5);
            
            cv2.line(depth_image, (smallest_mean_index * self.configuration['mean_band_size'], 0), (smallest_mean_index * self.configuration['mean_band_size'], height), (255, 255, 255), 5)
            #print "length: " + str(len(means))
            #print "means: " + str(means)
            #print "greatest: " + str(greatest_mean)
        return depth_image
        
                
        
    
if __name__ == "__main__":
    track_colour = TrackColour()
    track_depth = TrackDepth()
    
    
    while True:
        depth = track_depth.get_depth()
        contour_mask, contour, found, rect_image, rect = track_colour.find()
        depth = cv2.bitwise_and(depth, depth, mask=contour_mask)
        mask = track_depth.white_threshold(depth, contour_mask)
        sides_depth = track_depth.find_sides(depth, mask, rect)
        cv2.imshow("Sides Depth", sides_depth)
        cv2.imshow("Depth Mask", depth)
        cv2.imshow("Colour", rect_image)
        cv2.imshow("Mask", mask)
        k = cv2.waitKey(5) & 0xFF
        if k == 27:
            break