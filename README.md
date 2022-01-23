# Build docker image on Jetson Nano: GPIO, cam, ML
Purpose : build a reusable image using docker to control GPIO pins, speakers and microphone for Jetson Nano.\
Feel free to modify requirements.txt to install more libraries.

**Installed libraries:**\
TensorFlow 1.15.5 (base image)\
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
Jetson.GPIO 2.0.17\
pyaudio 0.2.11\
simpleaudio 1.0.4\
librosa 0.8.1\
transformers 4.15.0

## Installation
### 1) Flash jetson with Jetpack 4.6, no upgrade
### 2) Connect sensors before boot
### 3) Clone official repo for gpio pins control
`cd Desktop`\
`git clone https://github.com/NVIDIA/jetson-gpio.git`
### 4) Clone code for container creation
`git clone https://github.com/nlpTRIZ/container_jetson_audio_gpio.git`\
### 5) Création groupe gpio
`sudo groupadd -f -r gpio`
### 6) Ajout utilisateur dans le groupe gpio
`sudo usermod -a -G gpio $USER`
### 7) On copie le fichier donnant les permissions d'accès dans les règles systèmes
`sudo cp jetson-gpio/lib/python/Jetson/GPIO/99-gpio.rules /etc/udev/rules.d/`
### 8) On supprime le code pour le contrôle d'accès car plus besoin
`rm -rf jetson-gpio`
### 9) Add user to docker group
`sudo usermod -a -G docker jetson0`\
### 10) Reboot
`sudo reboot`
### 11) Build image (replace name_image with a proper name)
On crée l'image de l'environnement souhaité à partir de l'image officielle de nvidia dans laquelle on exécute le contenu du fichier Dockerfile\
Des modules pythons peuvent être ajoutés dans requirements.txt pour les installer dans l'image (vérifier qu'ils ne sont pas déjà là de base)\
`cd container_jetson_audio_gpio`\
`docker build -t name_image .`
### 12) Load run function
This will permanently set the launching command:\
`. install.sh`\
To temporarly set the command:\
`. copy/drun.sh`
## Run
Une fois l'image créée, plus besoin de la recréer, lancer un container à partir de l'image suffit.\
Lancement container\
`drun name_image`
