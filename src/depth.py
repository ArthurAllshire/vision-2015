import cv2
import numpy as np
import freenect
from collections import OrderedDict
from parseconfig import parse_config
from colour import *
import udp

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
        #this function basically removes the typical 'shadow' that is seen around objects from a kinect
        ret, thresh = cv2.threshold(depth_image, 248, 255,cv2.THRESH_BINARY_INV)
        mask = cv2.bitwise_and(mask, thresh)
        return mask
    
    def find_sides(self, depth_image, mask, rect):
        (x, y, w, h) = rect
        if x is not 0:
            means = []
            tote_image = depth_image[y: y + h, x : x + w]
            mask = mask[y: y + h, x : x + w]
            height, width = tote_image.shape
            smallest_mean_index = -1
            smallest_mean = 256
            print "Width: " + str(width) + ", Height: " + str(height)
            for column in range(0, w, self.configuration['mean_band_size']):
                mean = cv2.mean(tote_image[:,column:column+self.configuration['mean_band_size']], mask[:,column:column+self.configuration['mean_band_size']])[0]
                print "Mean: " + str(mean) + ", X: " + str(column)
                means.append(mean)
                if mean < smallest_mean:
                    smallest_mean = mean
                    smallest_mean_index = column/self.configuration['mean_band_size']
            
            tote_far_corner_short_index = -1
            if means[0] < means[-1]:
                print "left is short side"
                cv2.line(tote_image, (0, 0), (0, height), (255, 255, 255),5);
                tote_far_corner_short_index = 0
            else:
                print "right is short side"
                cv2.line(tote_image, (width, 0), (width, height), (255, 255, 255),5);
            
            cv2.line(tote_image, (smallest_mean_index * self.configuration['mean_band_size'], 0), (smallest_mean_index * self.configuration['mean_band_size'], height), (255, 255, 255), 5)
            #print "length: " + str(len(means))
            #print "means: " + str(means)
            #print "greatest: " + str(greatest_mean)
            offsets =  self.calculate_offsets(depth_image, x, y, tote_image, means, smallest_mean_index, tote_far_corner_short_index)
            return tote_image, offsets
        return depth_image, [0, 0, 0]
    
    def calculate_offsets(self, depth_image, tote_x, tote_y, tote_image, tote_means, tote_near_corner_index , tote_far_corner_short_index):
        #calculate the numbers that we are able to send over udp to the robot code as offsets
        tote_image_height, tote_image_width = tote_image.shape
        depth_image_height, depth_image_width = depth_image.shape
        z_diff = 0.0
        if self.data_range(tote_means[1:-1]) > self.configuration['tote_range_tolerance']:
            z_diff = (tote_means[tote_far_corner_short_index] - tote_means[tote_near_corner_index])/255.0
        short_side_center_x = (tote_x +(tote_means[tote_far_corner_short_index] + tote_means[tote_near_corner_index]))/2
        x_diff = 2*(short_side_center_x/depth_image_width)-1
        y_diff = depth_image[tote_y + (tote_image_height/2), short_side_center_x]
        return [x_diff, y_diff, z_diff]
        
        
                
    def data_range(self, array):
        big = -256
        small = 256
        for element in array:
            if element > big:
                big = element
            if element < small:
                small = element
                
        return big - small
    
if __name__ == "__main__":
    track_colour = TrackColour()
    track_depth = TrackDepth()
    
    
    while True:
        depth = track_depth.get_depth()
        contour_mask, contour, found, rect_image, rect = track_colour.find()
        depth = cv2.bitwise_and(depth, depth, mask=contour_mask)
        mask = track_depth.white_threshold(depth, contour_mask)
        sides_depth, offsets = track_depth.find_sides(depth, mask, rect)
        depth = cv2.cvtColor(depth, cv2.COLOR_GRAY2BGR)
        cv2.imshow("Sides Depth", sides_depth)
        cv2.imshow("Depth Mask", depth)
        cv2.imshow("Colour", rect_image)
        cv2.imshow("Mask", mask)
        udp.udp_send(offsets)
        k = cv2.waitKey(5) & 0xFF
        if k == 27:
            break