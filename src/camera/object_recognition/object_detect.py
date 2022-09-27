from jetcam.csi_camera import CSICamera
from jetcam.utils import bgr8_to_jpeg
import jetson_inference
import jetson_utils

WIDTH=720
HEIGHT=480
camera = CSICamera(width=WIDTH, height=HEIGHT, capture_fps=15)
camera.running=True

# create net
net = jetson_inference.detectNet("ssd-mobilenet-v2", threshold=0.5)

# Create window
import cv2
cv2.namedWindow('TEST', cv2.WINDOW_AUTOSIZE)

#Mouse callback function to be executed when a mouse event take place (double click)
def mouse_click (event,x,y,flags,param):
    if event == cv2.EVENT_LBUTTONDBLCLK:
        camera.unobserve_all()
        cv2.destroyAllWindows()
        cv2.waitKey(1)
        print ("Closing window.")
        #Close camera
        camera.running = False
        camera.cap.release()

cv2.setMouseCallback('TEST', mouse_click)

def image_processing(image):
    # BRG to RGB (because this network was trained with RGB images)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGBA)
    img = jetson_utils.cudaFromNumpy(image) 
    detections = net.Detect(img, overlay="box,labels,conf")
    img = jetson_utils.cudaToNumpy(img)
    return cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)

#Main function
def execute(change):
    image = change['new']
    ###
    # process
    image = image_processing(image)
    ###
    cv2.imshow('TEST', image)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        pass
    
camera.observe(execute, names='value')