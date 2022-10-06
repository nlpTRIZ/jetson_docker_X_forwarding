# Docker container with X forwarding for Jetson Nano
# Image Processing, Sound Processing, ML, GPIO control
Feel free to modify requirements.txt to install more libraries.

**Installed libraries:**\
PyTorch v1.9.0 (base image) \
torchvision v0.10.0 (base image)\
torchaudio v0.9.0 (base image) \
onnx 1.8.0 (base image) \
CuPy 9.2.0 (base image)\
numpy 1.19.5 (base image)\
numba 0.53.1 (base image)\
OpenCV 4.5.0 (base image)\
pandas 1.1.5 (base image)\
scipy 1.5.4 (base image)\
scikit-learn 0.23.2 (base image)\
JupyterLab 2.2.9 (base image)\
TensorFlow 2.7.0\
Jetson.GPIO 2.0.17\
pyaudio 0.2.11\
simpleaudio 1.0.4\
librosa 0.8.1\
transformers 4.15.0\
netron 5.5.4\
torch2trt 0.3.0\
trt-pose 0.0.1\
jetcam 0.0.0\
jetson-inference

# Installation
### 1) Flash jetson with Jetpack 4.6.1 https://developer.nvidia.com/jetson-nano-sd-card-image, no upgrade, headless setup https://www.jetsonhacks.com/2019/08/21/jetson-nano-headless-setup/
### 2) Connect sensors before boot
### 3) Clone official repositery for gpio pins control
`cd Desktop`\
`git clone https://github.com/NVIDIA/jetson-gpio.git`
### 4) Clone this repositery
`git clone https://github.com/nlpTRIZ/jetson_docker_X_forwarding`
### 5) Create gpio group
`sudo groupadd -f -r gpio`
### 6) Add user to gpio group
`sudo usermod -a -G gpio $USER`
### 7) Copy the permissions file
`sudo cp jetson-gpio/lib/python/Jetson/GPIO/99-gpio.rules /etc/udev/rules.d/`
### 8) Remove GPIO repo
`rm -rf jetson-gpio`
### 9) Add user to docker group
`sudo usermod -a -G docker $USER`
### 10) Install socat for socket management
`sudo apt update`\
`sudo apt install socat`
### 11) Make nvidia the default docker runtime
`sudo vim /etc/docker/daemon.json`
```bash
{
    "default-runtime": "nvidia",
    "runtimes": {
        "nvidia": {
            "path": "nvidia-container-runtime",
            "runtimeArgs": []
        }
    }
}
``` 
`sudo systemctl restart docker`
### 12) Add swap
`sudo fallocate -l 4G /var/swapfile`\
`sudo chmod 600 /var/swapfile`\
`sudo mkswap /var/swapfile`\
`sudo swapon /var/swapfile`\
`sudo bash -c 'echo "/var/swapfile swap swap defaults 0 0" >> /etc/fstab'`
### 13) Reboot
`sudo reboot`
### 14) Build image (replace name_image with a proper name)
Create the image of the desired environment from the official image of nvidia in which we execute the contents of Dockerfile.\
Python modules can be added in requirements.txt to install them (check that they are not already there).\
`cd Desktop/jetson_docker_X_forwarding`\
`docker build -t name_image .`
### 15) Load run function
To permanently set the containers starting command (`drun`) with proper options:\
`. install.sh`\
To temporarly set the command:\
`. copy/drun.sh`
# Run
Once an image is built, no need to rebuid it every time, just start a container:\
(don't forget to connect with -X option: ssh -X user@ip)\
`drun -c name_image`
### Optional: Set CPU, GPU clocks to maximum and start fan if any (not persistent across boots)
`sudo jetson_clocks --fan`

# Notes
Container structure:
```
menu  
│
└───app = working directory
│   
└───resources
    │   jetcam
    │   jetson-inference
    │   torch2trt
    │   trt_pose
```
You can find the documentation and examples in resources directory (directly copied from the installed libraries). \
**Note that in order to avoid errors when displaying the outputs of jetson-inference's examples, some minor modifications have to be made (basically just adding cv2.imshow() instead of regular output) as shown in src/camera/depth_estimation/depthnet.py (modified from resources/jetson-inference/python/examples/depthnet.py)** \
**Streaming data can also be achieved using the example in src/stream (to send video (processed or not) to another device).**\
**Displaying a stream directly from the container (cv2.imshow for example) is simple and paractical for debugging but very slow. For production use, consider streaming the data to the monitoring device.**

# With Windows
Install https://mobaxterm.mobatek.net/ and use it to connect to the jetson with -X option.

# With Mac
Type `DISPLAY=:0` and then connect to the jetson using -X option.
