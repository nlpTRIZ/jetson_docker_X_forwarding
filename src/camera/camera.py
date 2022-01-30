from jetcam.csi_camera import CSICamera
from jetcam.utils import bgr8_to_jpeg

WIDTH=1080
HEIGHT=720
camera = CSICamera(width=WIDTH, height=HEIGHT, capture_fps=12)
camera.running=True

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

#Main function
def execute(change):
    image = change['new']
    ###
    # process
    ###
    cv2.imshow('TEST', image)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        pass
    
camera.observe(execute, names='value')