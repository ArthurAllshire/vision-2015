import cv2
import numpy as np
import freenect
from collections import OrderedDict
from parseconfig import parse_config
from types import NoneType
from numpy.ma.core import get_data

class TrackColour(object):
    def __init__(self, colour='blue'):
        self.colour = colour
        self.configuration = parse_config(colour) 
              
    def threshold(self, image):
        hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        lower = np.array(self.configuration['hsv_bounds'][0])
        upper = np.array(self.configuration['hsv_bounds'][1])
        
        mask = cv2.inRange(hsv_image, lower, upper) # filter out all but values in the above range
        result = cv2.bitwise_and(image,image, mask=mask)
        return mask, result
    
    def erdi(self, (mask, image)):
        kernel = cv2.getStructuringElement(cv2.MORPH_CROSS,(5,5))
        emask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=self.configuration['erode_dialate_iterations'])
        
        erd_dlt_image = cv2.bitwise_and(image,image, mask=mask)
        
        return emask, erd_dlt_image
    
    def find_contour(self, (mask, image)):
        contours, heirarchy = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        target_contour = None
        target_rect = None
        target_area = 0
        found_target = False
        stats = []
        rect = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area>target_area:# ifs are staggered for efficiency reasons
                rect = cv2.minAreaRect(contour)
                target_contour = contour
                target_area = area
                found_target = True
                target_rect = rect
        
        height, width = image.shape[:2]
        
        black = np.zeros((height, width, 1), np.uint8)
        
        cv2.drawContours(black, [target_contour], -1, (255, 0, 0), cv2.cv.CV_FILLED)
        
        return black, image, target_contour
    
    def get_min_area(self, contour):
        return 
    
    def get_obb_image(self, contour, image):
        if contour != None:
            rect = cv2.minAreaRect(contour)
            print "Rect = "
            print rect
            #print self.get_data(rect, image)
            
            obb_image = image
            obb = cv2.cv.BoxPoints(rect)
            obb = np.int0(obb)
            cv2.drawContours(obb_image, [obb], -1, (0,0,255), 3)
            return obb_image, rect
        return image, ((0, 0), (0, 0), 0)
    
    def rotate_image(self, image, rect):
        rows,cols,depth = image.shape
        
        stats = self.get_data(rect, image)
        
        M = cv2.getRotationMatrix2D((cols/2,rows/2),stats['angle'],1)
        dst = cv2.warpAffine(image,M,(cols,rows))
        
        return dst
        
    
    def get_data(self, rect, image):
        img_height, img_width, depth = image.shape
        if rect[1][0]>rect[1][1]:
            w=rect[1][0]/img_width
            h=rect[1][1]/img_width
            angle = rect[2]
        else:
            w=rect[1][1]/img_width
            h=rect[1][0]/img_width
            angle = 90+rect[2]
        x = 2*(rect[0][0]/img_width)-1
        y = 2*(rect[0][1]/img_height)-1
        return OrderedDict([('x',x), ('y',y), ('w',w), ('h',h), ('angle',angle)])
        
        
    def get_video(self):
        array,_ = freenect.sync_get_video()
        array = cv2.cvtColor(array,cv2.COLOR_RGB2BGR)
        return array
    
if __name__ == "__main__":
    track = TrackColour()
    
    while True:
        black, image, contour = track.find_contour(track.erdi(track.threshold(track.get_video())))
        image, rect = track.get_obb_image(contour, image)
        cv2.imshow("Normal    ", image)
        if rect[2] != 0:
            image = track.rotate_image(image, rect)
        cv2.imshow("Processed", image)
        k = cv2.waitKey(5) & 0xFF
        if k == 27:
            break