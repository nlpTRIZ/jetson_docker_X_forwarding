import time
import onnx
import librosa
import torch
import numpy as np
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor
import pycuda.driver as cuda
import pycuda.autoinit
import numpy as np
import tensorrt as trt

task='TensorRT'

if task=='no TensorRT':
    tokenizer = Wav2Vec2Processor.from_pretrained("facebook/wav2vec2-base-960h")
    model = Wav2Vec2ForCTC.from_pretrained("facebook/wav2vec2-base-960h")
    model.eval()
    model.cuda()

    # boucle pour tous les traitements
    for _ in range(10):
        file_name = '../data/Hello.wav'
        input_audio, _ = librosa.load(file_name, sr=16000)

        input_ = tokenizer(input_audio, sampling_rate=16000, return_tensors="pt").input_values
        start = time.time()
        logits = model(input_.cuda()).logits.cpu() #on envoit les données sur gpu puis on transfère les résultats au cpu
        end = time.time()
        print(f"Inference: {end-start} sec.")
        predicted_ids = torch.argmax(logits, dim=-1)
        transcription = tokenizer.batch_decode(predicted_ids)[0]
        print(transcription)

elif task=='save_model_onnx':
    tokenizer = Wav2Vec2Processor.from_pretrained("facebook/wav2vec2-base-960h")
    model = Wav2Vec2ForCTC.from_pretrained("facebook/wav2vec2-base-960h")
    model.eval()
    file_name = '../data/Hello.wav'
    input_audio, _ = librosa.load(file_name, sr=16000)
    input_ = tokenizer(input_audio, sampling_rate=16000, return_tensors="pt").input_values
    ONNX_FILE_PATH = '../models/wav2vec.onnx'
    torch.onnx.export(model, input_, ONNX_FILE_PATH, input_names=['input_'],
                      output_names=['logits'], export_params=True)

elif task=='TensorRT': 
    ONNX_FILE_PATH = '../models/wav2vec.onnx'
    print('Loading model...')
    onnx_model = onnx.load(ONNX_FILE_PATH)
    print('Model loaded.')

    # logger to capture errors, warnings, and other information during the build and inference phases
    TRT_LOGGER = trt.Logger()

    def build_engine(onnx_file_path):
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

        config = builder.create_builder_config()
        config.set_flag(trt.BuilderFlag.FP16)

        # generate TensorRT engine optimized for the target platform
        print('Building an engine...')
        engine = builder.build_engine(network, config)
        context = engine.create_execution_context()
        print("Completed creating Engine")

        return engine, context


    # initialize TensorRT engine and parse ONNX model
    engine, context = build_engine(ONNX_FILE_PATH)
    # get sizes of input and output and allocate memory required for input data and for output data
    for binding in engine:
        if engine.binding_is_input(binding):  # we expect only one input
            input_shape = engine.get_binding_shape(binding)
            input_size = trt.volume(input_shape) * engine.max_batch_size * np.dtype(np.float32).itemsize  # in bytes
            device_input = cuda.mem_alloc(input_size)
        else:  # and one output
            output_shape = engine.get_binding_shape(binding)
            # create page-locked memory buffers (i.e. won't be swapped to disk)
            host_output = cuda.pagelocked_empty(trt.volume(output_shape) * engine.max_batch_size, dtype=np.float32)
            device_output = cuda.mem_alloc(host_output.nbytes)
    stream = cuda.Stream() 

    tokenizer = Wav2Vec2Processor.from_pretrained("facebook/wav2vec2-base-960h")
    for _ in range(10):
        # preprocess input data
        file_name = '../data/Hello.wav'
        input_audio, _ = librosa.load(file_name, sr=16000)
        host_input = np.array((tokenizer(input_audio, sampling_rate=16000, return_tensors="pt").input_values).numpy(), dtype=np.float32, order='C')
        cuda.memcpy_htod_async(device_input, host_input, stream)

        # run inference
        start = time.time()
        context.execute_async(bindings=[int(device_input), int(device_output)], stream_handle=stream.handle)
        cuda.memcpy_dtoh_async(host_output, device_output, stream)
        stream.synchronize()
        end = time.time()
        print(f"Inference: {end-start} sec.")

        # postprocess results
        output_data = torch.Tensor(host_output).view(len(host_input), -1, 32)
        predicted_ids=torch.argmax(output_data, dim=-1)
        transcription = tokenizer.batch_decode(predicted_ids)[0]
        print(transcription)
