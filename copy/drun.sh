# Bash function enabling access to sensors and X forwarding when starting containers
drun () {
	
	# Stop if no argument for image name given
	if [[ $# -eq 0 ]] ; then
	    echo 'No image name provided. Use "docker images" to find the right one.'
	    return
	fi
	
	# Prepare target env
	CONTAINER_HOSTNAME="root"
	
	# Find open port for jupyterlab
	PORT=8888
	PORT_NET=8888
	quit=0
	inc=0
	while [ "$quit" -ne 2 ]; do
		netstat -a | grep $(($PORT + $inc)) >> /dev/null
		if [ $? -gt 0 ]; then
			quit=`expr $quit + 1`
			if [ "$quit" -eq 1 ]; then
				PORT=$(($PORT + $inc))
				CONTAINER_DISPLAY=$inc
			else
				PORT_NET=$(($PORT_NET + $inc))
			fi
		fi
		inc=`expr $inc + 1`
	done
	
	# Create a directory for the socket
	mkdir -p /tmp/display/socket
	touch /tmp/display/Xauthority${CONTAINER_DISPLAY}
	
	# Get the DISPLAY slot
	DISPLAY_NUMBER=$(echo $DISPLAY | cut -d. -f1 | cut -d: -f2)
	
	# Extract current authentication cookie
	AUTH_COOKIE=$(xauth list | grep "^$(hostname)/unix:${DISPLAY_NUMBER} " | awk '{print $3}')
	
	# Create the new X Authority file
	xauth -f /tmp/display/Xauthority${CONTAINER_DISPLAY} add ${CONTAINER_HOSTNAME}/unix:${CONTAINER_DISPLAY} MIT-MAGIC-COOKIE-1 ${AUTH_COOKIE}
	
	# Proxy with the :0 DISPLAY
	sudo rm -rf /tmp/display/socket/X${CONTAINER_DISPLAY} || true
	PROCESSES=$(pgrep socat -a | grep /tmp/display/socket/X${CONTAINER_DISPLAY} | awk '{print $1}')
	if [ ! -z "$PROCESSES" ]
	then
		echo "Cleaning old sockets..."
		sudo kill ${PROCESSES}
	fi
	echo "Creating new socket..."
	socat UNIX-LISTEN:/tmp/display/socket/X${CONTAINER_DISPLAY},fork TCP4:localhost:60${DISPLAY_NUMBER} &
	
	# Launch the container
	docker run -it --rm \
	  --runtime nvidia \
	  --gpus all \
	  -e DISPLAY=:${CONTAINER_DISPLAY} \
	  -e XAUTHORITY=/tmp/.Xauthority \
	  -e JPORT=${PORT} \
	  -e NPORT=${PORT_NET} \
	  --device /dev/snd \
	  --device /dev/bus/usb \
	  --cap-add SYS_PTRACE \
	  -v /sys:/sys \
	  -v /tmp/display/socket:/tmp/.X11-unix \
	  -v /tmp/display/Xauthority${CONTAINER_DISPLAY}:/tmp/.Xauthority \
	  -v /tmp/argus_socket:/tmp/argus_socket \
	  -v ${PWD}:/menu/app \
	  -p $PORT:8888 \
	  -p $PORT_NET:8080 \
	  --privileged \
	  --hostname ${CONTAINER_HOSTNAME} \
	  $1
}
