# Bash function which will be written in ~/.bashrc file.
drun () {
	
	# Stop if no argument for image name given
	if [[ $# -eq 0 ]] ; then
	    echo 'No image name provided. Use "docker images" to find the right one.'
	    return
	fi
	
	# Prepare target env
	CONTAINER_DISPLAY=$(( $(ps aux | grep -c "docker run") - 1))
	CONTAINER_HOSTNAME="root"
	
	# Find open port for jupyterlab
	port=8888
	quit=0
	
	while [ "$quit" -ne 1 ]; do
		netstat -a | grep $port >> /dev/null
		if [ $? -gt 0 ]; then
			quit=1
		else
			port=`expr $port + 1`
		fi
	done
	
	# Create a directory for the socket
	mkdir -p display/socket
	touch display/Xauthority
	
	# Get the DISPLAY slot
	DISPLAY_NUMBER=$(echo $DISPLAY | cut -d. -f1 | cut -d: -f2)
	
	# Extract current authentication cookie
	AUTH_COOKIE=$(xauth list | grep "^$(hostname)/unix:${DISPLAY_NUMBER} " | awk '{print $3}')
	
	# Create the new X Authority file
	xauth -f display/Xauthority${CONTAINER_DISPLAY} add ${CONTAINER_HOSTNAME}/unix:${CONTAINER_DISPLAY} MIT-MAGIC-COOKIE-1 ${AUTH_COOKIE}
	
	# Proxy with the :0 DISPLAY
	sudo rm -rf display/socket/X${CONTAINER_DISPLAY} || true
	PROCESSES=$(ps aux | grep display/socket/X${CONTAINER_DISPLAY} | head -n -1 | awk '{print $2}')
	if [ ! -z "$PROCESSES" ]
	then
		echo "Cleaning old sockets..."
		sudo kill ${PROCESSES}
	fi
	echo "Creating new socket..."
	socat UNIX-LISTEN:display/socket/X${CONTAINER_DISPLAY},fork TCP4:localhost:60${DISPLAY_NUMBER} &
	
	# Launch the container
	docker run -it --rm \
	  --runtime nvidia \
	  --gpus all \
	  -e DISPLAY=:${CONTAINER_DISPLAY} \
	  -e XAUTHORITY=/tmp/.Xauthority \
	  -e JPORT=${port} \
	  --device /dev/snd \
	  --device /dev/bus/usb \
	  --cap-add SYS_PTRACE \
	  -v /sys:/sys \
	  -v ${PWD}/display/socket:/tmp/.X11-unix \
	  -v ${PWD}/display/Xauthority${CONTAINER_DISPLAY}:/tmp/.Xauthority \
	  -v /tmp/argus_socket:/tmp/argus_socket \
	  -v ${PWD}:/app \
	  -p $port:8888 \
	  --privileged \
	  --hostname ${CONTAINER_HOSTNAME} \
	  $1
}
