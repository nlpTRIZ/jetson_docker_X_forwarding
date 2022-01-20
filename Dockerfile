FROM nvcr.io/nvidia/l4t-ml:r32.6.1-py3

ARG uid
ARG gid
ARG gid_gpio
RUN groupadd -f -r -g $gid_gpio gpio
RUN groupadd -f -r -g 1000 user

# gpio needs to be main group, otherwise we get permission problems
RUN useradd -M --uid $uid -g $gid_gpio user --groups uucp,$gid,user 
RUN mkdir -p /etc/sudoers.d \ 
   && echo 'user ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers.d/user \
   && echo 'Defaults exempt_group+=user' >> /etc/sudoers.d/user \
   && chmod a=r,o= /etc/sudoers.d/user

WORKDIR /app
COPY ./requirements.txt .

RUN curl https://sh.rustup.rs -sSf > install_rust.sh \
    && sh install_rust.sh -y \
    && . $HOME/.cargo/env \
    && apt-get update \
    && apt-get install -y portaudio19-dev \
    && pip3 install setuptools_rust \
    && pip3 install -r requirements.txt

COPY ./copy/gpio_pin_data.py /usr/local/lib/python3.6/dist-packages/Jetson/GPIO/gpio_pin_data.py
