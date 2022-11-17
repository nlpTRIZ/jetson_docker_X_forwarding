#!/usr/bin/env python3
#
# Copyright (c) 2021, NVIDIA CORPORATION. All rights reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
#

import sys
import argparse

import cv2
from jetson_inference import depthNet
import jetson_utils
from jetson_utils import videoSource, videoOutput, logUsage, cudaOverlay, cudaDeviceSynchronize, cudaToNumpy

from depthnet_utils import depthBuffers

# parse the command line
parser = argparse.ArgumentParser(description="Mono depth estimation on a video/image stream using depthNet DNN.", 
                                 formatter_class=argparse.RawTextHelpFormatter, 
                                 epilog=depthNet.Usage() + videoSource.Usage() + videoOutput.Usage() + logUsage())

parser.add_argument("input_URI", type=str, default="", nargs='?', help="URI of the input stream")
parser.add_argument("output_URI", type=str, default="", nargs='?', help="URI of the output stream")
parser.add_argument("--network", type=str, default="fcn-mobilenet", help="pre-trained model to load, see below for options")
parser.add_argument("--visualize", type=str, default="input,depth", help="visualization options (can be 'input' 'depth' 'input,depth'")
parser.add_argument("--depth-size", type=float, default=1.0, help="scales the size of the depth map visualization, as a percentage of the input size (default is 1.0)")
parser.add_argument("--filter-mode", type=str, default="linear", choices=["point", "linear"], help="filtering mode used during visualization, options are:\n  'point' or 'linear' (default: 'linear')")
parser.add_argument("--colormap", type=str, default="viridis-inverted", help="colormap to use for visualization (default is 'viridis-inverted')",
                                  choices=["inferno", "inferno-inverted", "magma", "magma-inverted", "parula", "parula-inverted", 
                                           "plasma", "plasma-inverted", "turbo", "turbo-inverted", "viridis", "viridis-inverted"])

try:
	opt = parser.parse_known_args()[0]
except:
	print("")
	parser.print_help()
	sys.exit(0)

# load the segmentation network
net = depthNet(opt.network, sys.argv)

# create buffer manager
buffers = depthBuffers(opt)

# create video sources & outputs
width  = 640     # 1640      # 1280
height = 360      # 1232      # 720
framerate = 50    # 30        # 60      # choose 30 or 60

param_videoSource = []
param_videoSource.append("--input-width=" + str(width))
param_videoSource.append(f"--input-height=" + str(height))
param_videoSource.append(f"--input-flip=vertical")
param_videoSource.append(f"--input-rate=" +str(framerate))

input = jetson_utils.videoSource('csi://0',   argv=param_videoSource )

# Create window
cv2.namedWindow('Depth', cv2.WINDOW_AUTOSIZE)

# process frames until user exits
while True:
    # capture the next image
    img_input = input.Capture()

    # allocate buffers for this size image
    buffers.Alloc(img_input.shape, img_input.format)

    # process the mono depth and visualize
    net.Process(img_input, buffers.depth, opt.colormap, opt.filter_mode)

    # composite the images
    if buffers.use_input:
        cudaOverlay(img_input, buffers.composite, 0, 0)
        
    if buffers.use_depth:
        cudaOverlay(buffers.depth, buffers.composite, img_input.width if buffers.use_input else 0, 0)

    img = cudaToNumpy(buffers.composite)
    cv2.imshow('Depth', cv2.cvtColor(img, cv2.COLOR_RGBA2BGR))
    if cv2.waitKey(1) & 0xFF == ord('q'):
        pass

    # print out performance info
    cudaDeviceSynchronize()
    net.PrintProfilerTimes()

    # exit on input/output EOS
    if not input.IsStreaming():
        break
