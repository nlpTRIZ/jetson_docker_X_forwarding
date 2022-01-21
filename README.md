# Control GPIO pins and audio devices using Jetson Nano
Purpose : build a reusable image using docker to control GPIO pins, speakers and microphone for Jetson Nano.\
Feel free to modify requirements.txt to install more libraries.

**Installed libraries:**\
TensorFlow 1.15.5 \
PyTorch v1.9.0 \
torchvision v0.10.0\
torchaudio v0.9.0 \
onnx 1.8.0 \
CuPy 9.2.0\
numpy 1.19.5\
numba 0.53.1\
OpenCV 4.5.0 (with CUDA)\
pandas 1.1.5\
scipy 1.5.4\
scikit-learn 0.23.2\
JupyterLab 2.2.9\
Jetson.GPIO 2.0.17\
pyaudio 0.2.11\
simpleaudio 1.0.4\
librosa 0.8.1\
transformers 4.15.0

## Prepare and build image
### 1) Follow INSTALLATION guidelines of the following repo to make the gpio pins available and controlable

Be sure to follow all INSTALLATION guidelines of this repo https://github.com/NVIDIA/jetson-gpio.git, otherwise you will have a permission error when using the gpio pins.

`git clone https://github.com/NVIDIA/jetson-gpio.git` (clone the repo to be able to copy the rules)

You can find examples of gpio uses in samples directory (in repo).

### 2) Find the relevant ids to build the image

`id $USER`

for example `id jetson0` and get uid, gid and the group corresponding to gpio (gid_gpio)

### 3) Build image (replace numbers by your uid, gid, gid_gpio)

`sudo docker build -t jetson_gpio --build-arg uid=1000 --build-arg gid=1000 --build-arg gid_gpio=999 .`

## Create a container from image to execute codes
**Replace 999 by your gid_gpio:**

`sudo docker run --rm -it --runtime=nvidia --net host --gpus all --device /dev/snd --device /dev/bus/usb -v $(pwd):/app -v /sys:/sys --group-add 999 -e DISPLAY=$DISPLAY -v /tmp/.X11-unix/:/tmp/.X11-unix jetson_gpio:latest`

-v $(pwd):/app means that the user working directory (where the user uses this command) will be available in /app directory inside the container. Files in this directory are shared between the host and the container.\
Use Ctrl+D to exit container.
