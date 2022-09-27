import sys
import time

import cv2
import jetson_utils
from jetson_utils import cudaToNumpy


camera = jetson_utils.videoSource("rtp://localhost:1234", argv=['--input-codec=h264'])

# Create window
cv2.namedWindow('Hello Stream', cv2.WINDOW_AUTOSIZE)
img_count = 0
time_start = time.time()
while True:
    img = camera.Capture()
    img = cudaToNumpy(img)
    cv2.imshow('Hello Stream', cv2.cvtColor(img, cv2.COLOR_RGBA2BGR))
    if cv2.waitKey(1) & 0xFF == ord('q'):
        pass
    img_count += 1
    if time.time() - time_start > 1:
        print(f"FPS: {img_count / (time.time() - time_start)}")
        time_start = time.time()
        img_count = 0
