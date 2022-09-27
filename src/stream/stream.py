import sys
import argparse

import jetson.inference
import jetson.utils


# parse the command line
parser = argparse.ArgumentParser()
parser.add_argument("--ip", type=str, default="localhost", help="ip to stream to")
parser.add_argument("--port", type=str, default="1234", help="port to stream to")
opt = parser.parse_known_args()[0]

is_headless = ["--headless"] if sys.argv[0].find('console.py') != -1 else [""]

net = jetson.inference.detectNet("ssd-mobilenet-v2", threshold=0.5)
camera = jetson.utils.videoSource("csi://0", argv=sys.argv)

display = jetson.utils.videoOutput(f"rtp://{opt.ip}:{opt.port}", argv=sys.argv+is_headless)
while True:
    img = camera.Capture()
    detections = net.Detect(img)
    display.Render(img)
    print(f"FPS: {net.GetNetworkFPS()}")