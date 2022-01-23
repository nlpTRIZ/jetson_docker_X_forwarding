#!/bin/bash

# Prepare target env
CONTAINER_DISPLAY="0"
CONTAINER_HOSTNAME="root"

# Create a directory for the socket
mkdir -p display/socket
touch display/Xauthority

# Get the DISPLAY slot
DISPLAY_NUMBER=$(echo $DISPLAY | cut -d. -f1 | cut -d: -f2)

# Extract current authentication cookie
AUTH_COOKIE=$(xauth list | grep "^$(hostname)/unix:${DISPLAY_NUMBER} " | awk '{print $3}')

# Create the new X Authority file
xauth -f display/Xauthority add ${CONTAINER_HOSTNAME}/unix:${CONTAINER_DISPLAY} MIT-MAGIC-COOKIE-1 ${AUTH_COOKIE}

# Proxy with the :0 DISPLAY
socat UNIX-LISTEN:display/socket/X${CONTAINER_DISPLAY},fork TCP4:localhost:60${DISPLAY_NUMBER} &

# Launch the container
docker run -it --rm \
  --runtime nvidia \
  --gpus all \
  -e DISPLAY=:${CONTAINER_DISPLAY} \
  -e XAUTHORITY=/tmp/.Xauthority \
  --device /dev/snd \
  --device /dev/bus/usb \
  --cap-add SYS_PTRACE \
  -v /sys:/sys \
  -v ${PWD}/display/socket:/tmp/.X11-unix \
  -v ${PWD}/display/Xauthority:/tmp/.Xauthority \
  -v /tmp/argus_socket:/tmp/argus_socket \
  -v ${PWD}:/app \
  -p 8888:8888 \
  --privileged \
  --hostname ${CONTAINER_HOSTNAME} \
  jetson_c
