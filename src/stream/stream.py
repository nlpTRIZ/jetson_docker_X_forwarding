import sys

import jetson.inference
import jetson.utils

HOST = "192.168.55.100"
HOST = "localhost"
PORT = "1234"

is_headless = ["--headless"] if sys.argv[0].find('console.py') != -1 else [""]

net = jetson.inference.detectNet("ssd-mobilenet-v2", threshold=0.5)
camera = jetson.utils.videoSource("csi://0", argv=sys.argv)

display = jetson.utils.videoOutput(f"rtp://{HOST}:{PORT}", argv=sys.argv+is_headless)
while True:
    img = camera.Capture()
    detections = net.Detect(img)
    display.Render(img)
    print(f"FPS: {net.GetNetworkFPS()}")