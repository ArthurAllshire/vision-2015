import cv2
import numpy as np
import freenect
from collections import OrderedDict
from parseconfig import parse_config

class TrackColour(object):
    def __init__(self, colour='yellow'):
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
        
        return black, target_contour
    
    def get_bounding_rect(self, contour, image):
        if contour != None:
            x,y,w,h = cv2.boundingRect(contour)
            print x
            print y
            print w
            print h
            rect_image = image
            cv2.rectangle(rect_image,(x,y),(x+w,y+h),(0,255,0),2)
            return rect_image, (x, y, w, h)
        return image, (0, 0, 0, 0)
        
    def get_video(self):
        array,_ = freenect.sync_get_video()
        array = cv2.cvtColor(array,cv2.COLOR_RGB2BGR)
        return array
    
    def find(self):
        #called by the depth class to get a mask for depth
        raw_image = self.get_video()
        contour_mask, contour = self.find_contour(self.erdi(self.threshold(raw_image)))
        bounded_image, rect = self.get_bounding_rect(contour, raw_image)
        found = False
        if rect[2] is not 0:
            found = True

        return contour_mask, contour, found, bounded_image, rect
    
if __name__ == "__main__":
    track = TrackColour()
    while True:
        mask, contour, found, image, rect = track.find()
        cv2.imshow("Image", image)
        cv2.imshow("Mask", mask)
        k = cv2.waitKey(5) & 0xFF
        if k == 27:
            break