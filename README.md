# jetson_container

## Follow INSTALLATION guidelines to make the gpio pins available and controlable

Be sure to follow all INSTALLATION guidelines, otherwise you will have a permission error when using the gpio pins.

https://github.com/NVIDIA/jetson-gpio.git


`git clone https://github.com/NVIDIA/jetson-gpio.git` (clone the repo to be able to copy the shield rules)

## Find the relevant ids to build the image

`id $USER`

for example `id jetson0` and get uid, gid and the group corresponding to gpio (gid_gpio)

## Build image (replace numbers by your uid, gid, gid_gpio)

`sudo docker build -t jetson_gpio --build-arg uid=1000 --build-arg gid=1000 --build-arg gid_gpio=999 .`

## Run Container from image (replace number by your gid_gpio)

`sudo docker run --rm -it --runtime=nvidia --net host --gpus all --device /dev/snd --device /dev/bus/usb -v $(pwd):/app -v /sys:/sys --group-add 999 jetson_gpio:latest`

-v $(pwd):/app means that the user working directory (where the user uses this command) will be available in /app directory inside the container. Files in this dir are shared between the host and the container.
