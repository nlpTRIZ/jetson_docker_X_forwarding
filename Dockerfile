FROM nvcr.io/nvidia/l4t-ml:r32.6.1-py3

WORKDIR /menu/resources
COPY ./requirements.txt .

RUN pip3 uninstall -y tensorflow \
    && apt-get update \
    && apt-get install -y libhdf5-serial-dev hdf5-tools libhdf5-dev zlib1g-dev zip libjpeg8-dev liblapack-dev libblas-dev gfortran pkg-config \
    && pip3 install -U testresources setuptools==49.6.0 \
    && pip3 install -U --no-deps numpy==1.19.4 future==0.18.2 mock==3.0.5 keras_preprocessing==1.1.2 keras_applications==1.0.8 gast==0.4.0 cython pkgconfig \
    && env H5PY_SETUP_REQUIRES=0 pip3 install -U h5py==3.1.0 \
    && pip3 install --pre --extra-index-url https://developer.download.nvidia.com/compute/redist/jp/v461 tensorflow==2.7.0+nv22.1

RUN curl https://sh.rustup.rs -sSf > install_rust.sh \
    && sh install_rust.sh -y \
    && . $HOME/.cargo/env \
    && apt-get update \
    && apt-get install -y portaudio19-dev \
    && pip3 install setuptools_rust \
    && pip3 install -r requirements.txt \
    && rm install_rust.sh requirements.txt

RUN git clone --recursive https://github.com/dusty-nv/jetson-inference \
    && cd jetson-inference \
    && sed -i 's/nvcaffe_parser/nvparsers/g' CMakeLists.txt \
    && mkdir build \
    && cd build \
    && cmake -DENABLE_NVMM=off ../ \
    && make -j$(nproc) \
    && make install \
    && ldconfig
    
RUN git clone https://github.com/NVIDIA-AI-IOT/torch2trt.git \
    && cd torch2trt/scripts  \
    && bash build_contrib.sh
    
RUN git clone https://github.com/NVIDIA-AI-IOT/jetcam \
    && cd jetcam \
    && python3 setup.py install
    
RUN git clone https://github.com/NVIDIA-AI-IOT/trt_pose \
    && cd trt_pose \
    && python3 setup.py install

WORKDIR /menu/app

COPY ./copy/gpio_pin_data.py /usr/local/lib/python3.6/dist-packages/Jetson/GPIO/gpio_pin_data.py
COPY ./copy/run.sh /usr/

WORKDIR /menu

CMD /bin/bash /usr/run.sh ${JPORT} ${NPORT}
