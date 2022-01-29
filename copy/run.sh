echo "Allow 10 sec for JupyterLab to start @ http://192.168.55.1:$1 (password nvidia) or @ http://jetson_ip:$1 if wifi connection was set up."
echo "If running, Netron will be available @ http://192.168.55.1:$2 or @ http://jetson_ip:$2, run netron with: netron --host 0.0.0.0 /path/to/model"
nohup jupyter lab --ip 0.0.0.0 --allow-root --no-browser --notebook-dir="/" > /var/log/jupyter.log 2>&1 &
/bin/bash
