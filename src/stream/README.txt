Use these examples to stream a video (sent by stream.py) and receive it in get_stream.py
In this example, stream.py is streaming to localhost which is not useful. You should change HOST to your computer ip in stream.py and launch get_stream.py on your computer (or another device) to get the video stream.
    python3 stream.py --headless --width=1080 --height=720 (other options are possible https://github.com/dusty-nv/jetson-inference)
    python3 get_stream.py
To get the stream you can also use gstreamer (https://gstreamer.freedesktop.org/documentation/installing/) and use following command:
    gst-launch-1.0 -v udpsrc port=1234  caps = "application/x-rtp, media=(string)video, clock-rate=(int)90000, encoding-name=(string)H264, payload=(int)96" !  rtph264depay ! decodebin ! videoconvert ! autovideosink