import sys
import os
import onnx
import pycuda.driver as cuda
import pycuda.autoinit
import tensorrt as trt
import numpy as np

TRT_LOGGER = trt.Logger(trt.Logger.INFO)

def build_engine(onnx_file_path, engine_file_path, max_input_size):
    # initialize TensorRT engine and parse ONNX model
    builder = trt.Builder(TRT_LOGGER)
    explicit_batch = 1 << (int)(trt.NetworkDefinitionCreationFlag.EXPLICIT_BATCH)
    network = builder.create_network(explicit_batch)
    parser = trt.OnnxParser(network, TRT_LOGGER)

    # parse ONNX
    with open(onnx_file_path, 'rb') as model:
        print('Beginning ONNX file parsing')
        parser.parse(model.read())
    print('Completed parsing of ONNX file')
    last_layer = network.get_layer(network.num_layers - 1)
    # Check if last layer recognizes it's output
    if not last_layer.get_output(0):
        # If not, then mark the output using TensorRT API
        network.mark_output(last_layer.get_output(0))
    
    # Config (add a profile to deal with dynamic shapes)
    profile = builder.create_optimization_profile();
    profile.set_shape("input", (1, 20000), (1, 50000), (1, max_input_size)) #min size, opt size, max size
    profile.set_shape("output", (1, 20), (1, 200), (1, 500)) #min size, opt size, max size
    config = builder.create_builder_config()
    config.add_optimization_profile(profile)
    config.max_workspace_size = 1 << 28 #2**28 bits
    config.set_flag(trt.BuilderFlag.FP16)
    builder.max_batch_size = 1
    
    # generate TensorRT engine optimized for the target platform
    print('Building an engine...')
    engine = builder.build_engine(network, config)
    print("Completed creating Engine")

    with open(engine_file_path, "wb") as f:
        f.write(engine.serialize())
    return engine

def load_engine(engine_file_path, onnx_filepath):
    if os.path.exists(engine_file_path):
        # If a serialized engine exists, use it instead of building an engine.
        print("Reading engine from file {}".format(engine_file_path))
        trt.init_libnvinfer_plugins(None, "")
        with open(engine_file_path, "rb") as f, trt.Runtime(TRT_LOGGER) as runtime:
            return runtime.deserialize_cuda_engine(f.read())
    elif os.path.exists(engine_file_path):
        print("No serialized model found.")
        return build_engine(onnx_filepath, engine_file_path)
    else:
        print("No saved model found.")
        sys.exit(0)

def init_trt_buffers(engine, context, max_input_size):
    """Initialize host buffers and cuda buffers for the engine."""
    # get sizes of input and output and allocate memory required for input data and for output data
    for binding in engine:
        if engine.binding_is_input(binding):  # we expect only one input
            idx = engine.get_binding_index(binding)
            input_shape = engine.get_binding_shape(binding)
            print("net input_shape", input_shape)
            input_size = trt.volume((input_shape[0], max_input_size)) * engine.max_batch_size * np.dtype(np.float32).itemsize  # in bytes
            device_input = cuda.mem_alloc(input_size)
        else:  # and one output
            output_shape = engine.get_binding_shape(binding)
            print("net output_shape", output_shape)
            # create page-locked memory buffers (i.e. won't be swapped to disk)
            host_output = cuda.pagelocked_empty(trt.volume(output_shape) * engine.max_batch_size, dtype=np.float32)
            device_output = cuda.mem_alloc(host_output.nbytes)
    return device_input, host_output, device_output

def infer_with_trt(context, host_input, cuda_input, host_output, cuda_output, engine):
    """Inference the image with TensorRT engine."""
    stream = cuda.Stream()
    print("actual input shape", host_input.size)
    cuda.memcpy_htod_async(cuda_input, host_input, stream)
    context.execute_async_v2(bindings=[int(cuda_input), int(cuda_output)],
                             stream_handle=stream.handle)
    cuda.memcpy_dtoh_async(host_output, cuda_output, stream)
    stream.synchronize()
    return host_output