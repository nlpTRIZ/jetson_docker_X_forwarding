# Bash function enabling access to sensors and X forwarding when starting containers
drun () {
	
	# Stop if no argument for image name given
	if [[ $# -eq 0 ]] ; then
	    echo 'No image name provided. Use "docker images" to find the right one.'
	    return
	fi
	
	# Prepare target env
	CONTAINER_HOSTNAME="root"
	
	# Find open port for jupyterlab and netron
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
    
	if [ -n "$SSH_CLIENT" ] || [ -n "$SSH_TTY" ]; then
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
			echo Killing old sockets...
			sudo kill ${PROCESSES}
		fi
		echo Starting new socket...
		socat UNIX-LISTEN:/tmp/display/socket/X${CONTAINER_DISPLAY},fork TCP4:localhost:60${DISPLAY_NUMBER} &
		XFORWARD="\
		-e XAUTHORITY=/tmp/.Xauthority \
		-e DISPLAY=:${CONTAINER_DISPLAY} \
		-v /tmp/display/socket:/tmp/.X11-unix \
        	-v /tmp/display/Xauthority${CONTAINER_DISPLAY}:/tmp/.Xauthority"

	else
		xhost + >> /dev/null
		XFORWARD="\
		-e DISPLAY=$DISPLAY \
		-v /tmp/.X11-unix:/tmp/.X11-unix"
	fi

	# generate mount commands for jetson-inference models
	NETWORKS_DIR="data/networks"
	CLASSIFY_DIR="python/training/classification"
	DETECTION_DIR="python/training/detection/ssd"
	DOCKER_ROOT="/menu/resources/jetson-inference"
	DATA_J="/data_jetson_inference"
	sudo mkdir -p $DATA_J
	sudo mkdir -p $DATA_J/$NETWORKS_DIR
	sudo mkdir -p $DATA_J/$CLASSIFY_DIR
	sudo mkdir -p $DATA_J/$DETECTION_DIR
	sudo chmod -R 777 $DATA_J

	DATA_VOLUME="\
	--volume $DATA_J/data:$DOCKER_ROOT/data \
	--volume $DATA_J/data_cls/data:$DOCKER_ROOT/$CLASSIFY_DIR/data \
	--volume $DATA_J/data_cls/models:$DOCKER_ROOT/$CLASSIFY_DIR/models \
	--volume $DATA_J/data_detect/data:$DOCKER_ROOT/$DETECTION_DIR/data \
	--volume $DATA_J/data_detect/models:$DOCKER_ROOT/$DETECTION_DIR/models \
	--volume $DATA_J/data_local:/usr/local/bin/networks"

	# parse user arguments
	USER_VOLUME=""
	USER_COMMAND=""
	USER_PORT=""

	while :; do
	case $1 in
	    -v|--volume)
		if [ "$2" ]; then
		    USER_VOLUME=" -v $2 "
		    shift
		else
		    die 'ERROR: "--volume" requires a non-empty option argument.'
		fi
		;;
	    --volume=?*)
		USER_VOLUME=" -v ${1#*=} " # Delete everything up to "=" and assign the remainder.
		;;
	    --volume=)         # Handle the case of an empty --image=
		die 'ERROR: "--volume" requires a non-empty option argument.'
		;;
	    -c|--container)       # Takes an option argument; ensure it has been specified.
		if [ "$2" ]; then
		    CONTAINER_IMAGE=$2
		    shift
		else
		    die 'ERROR: "--container" requires a non-empty option argument.'
		fi
		;;
	    --container=?*)
		CONTAINER_IMAGE=${1#*=} # Delete everything up to "=" and assign the remainder.
		;;
	    --container=)         # Handle the case of an empty --image=
		die 'ERROR: "--container" requires a non-empty option argument.'
		;;
	    -r|--run)
		if [ "$2" ]; then
		    shift
		    USER_COMMAND=" $@ "
		else
		    die 'ERROR: "--run" requires a non-empty option argument.'
		fi
		;;
	    -p|--publish)
		if [ "$2" ]; then
		    USER_PORT=" -p $2 "
		    shift
		else
		    die 'ERROR: "--publish" requires a non-empty option argument.'
		fi
		;;
	    --)              # End of all options.
		shift
		break
		;;
	    -?*)
		printf 'WARN: Unknown option (ignored): %s\n' "$1" >&2
		;;
	    *)               # Default case: No more options, so break out of the loop.
		break
	esac

	shift
	done

	if [ "$USER_PORT" ]; then
		echo Mapping $USER_PORT...
	fi
	if [ "$USER_VOLUME" ]; then
		echo Mounting $USER_VOLUME...
	fi
	if [ "$USER_COMMAND" ]; then
		echo Executing $USER_COMMAND...
	fi

	# check for V4L2 devices
	V4L2_DEVICES=" "
	for i in {0..9}
	    do
		if [ -a "/dev/video$i" ]; then
		    V4L2_DEVICES="$V4L2_DEVICES --device /dev/video$i "
		fi
	    done

	# Launch the container
	docker run -it --rm \
	--runtime nvidia \
	--gpus all \
	-e JPORT=${PORT} \
	-e NPORT=${PORT_NET} \
	--device /dev/snd \
	--device /dev/bus/usb \
	--cap-add SYS_PTRACE \
	-v /sys:/sys \
	-v /tmp/argus_socket:/tmp/argus_socket \
	-v /etc/enctune.conf:/etc/enctune.conf \
	-v ${PWD}:/menu/app \
	-p $PORT:8888 \
	-p $PORT_NET:8080 \
	--privileged \
	--hostname ${CONTAINER_HOSTNAME} \
	$XFORWARD $DATA_VOLUME $USER_VOLUME $USER_PORT $V4L2_DEVICES\
	$CONTAINER_IMAGE $USER_COMMAND
}

