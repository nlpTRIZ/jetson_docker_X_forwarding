FROM nvcr.io/nvidia/l4t-ml:r32.6.1-py3

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
COPY ./copy/run.sh /usr/
CMD /bin/bash /usr/run.sh ${JPORT}
