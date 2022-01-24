import time
import librosa
import torch
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor
import onnx
import numpy as np
from torch2trt import torch2trt
from torch2trt import TRTModule

from tensorrt_ import build_engine, load_engine, infer_with_trt, init_trt_buffers

task='TensorRT' # run first with no TensoRT to export model
DYNAMIC_SIZES = False
ENGINE_FILE_PATH = '../../models/wav2vec.trt'
ONNX_FILE_PATH = '../../models/wav2vec.onnx'
FILENAME = '../../data/Open_test.wav'
MAX_INPUT_SIZE = 50000

if task=='no TensorRT':
    tokenizer = Wav2Vec2Processor.from_pretrained("facebook/wav2vec2-base-960h")
    model = Wav2Vec2ForCTC.from_pretrained("facebook/wav2vec2-base-960h")
    model.eval()
    model.cuda()
    
    input_audio, _ = librosa.load(FILENAME, sr=16000)
    # boucle pour tous les traitements
    for _ in range(1):
        input_ = tokenizer(input_audio, sampling_rate=16000, return_tensors="pt").input_values[... ,:MAX_INPUT_SIZE]
        start = time.time()
        logits = model(input_.cuda()).logits.cpu() #on envoit les données sur gpu puis on transfère les résultats au cpu
        end = time.time()
        print(f"Inference: {end-start} sec.")
        predicted_ids = torch.argmax(logits, dim=-1)
        transcription = tokenizer.batch_decode(predicted_ids)[0]
        print(transcription)
    
    ## This is not supposed to be done on a Jetson
    # Saving model
    print("Exporting model...")
    dummy_input = input_
    if DYNAMIC_SIZES:
        # indicates that the dimension 1 of input can vary
        dynamic_axes = {'input': {1: 'len_sound'}}
        torch.onnx.export(model, dummy_input[... ,:1000].cuda() , ONNX_FILE_PATH, input_names=['input'],
                          output_names=['output'], dynamic_axes=dynamic_axes, export_params=True)
    else:
        torch.onnx.export(model, dummy_input.cuda(), ONNX_FILE_PATH, input_names=['input'],
                          output_names=['output'], export_params=True)
    onnx_model = onnx.load(ONNX_FILE_PATH)
    #onnx.checker.check_model(onnx_model)

    # Serializing model   
    print("Serializing model...")
    build_engine(ONNX_FILE_PATH, ENGINE_FILE_PATH, MAX_INPUT_SIZE, DYNAMIC_SIZES)
    print("Done.")

elif task=='TensorRT': 
    # initialize TensorRT engine
    engine = load_engine(ENGINE_FILE_PATH, ONNX_FILE_PATH)

    input_audio, _ = librosa.load(FILENAME, sr=16000)
    tokenizer = Wav2Vec2Processor.from_pretrained("facebook/wav2vec2-base-960h")
    context = engine.create_execution_context()
    context.set_binding_shape(0, np.array((tokenizer(input_audio, 
                                         sampling_rate=16000, 
                                         return_tensors="pt").input_values).numpy()[... ,:MAX_INPUT_SIZE], dtype=np.float32, order='C').shape)
    cuda_input, host_output, cuda_output = init_trt_buffers(engine, context, MAX_INPUT_SIZE)
    
    for _ in range(100):
        # preprocess input data
        host_input = np.array((tokenizer(input_audio, 
                                         sampling_rate=16000, 
                                         return_tensors="pt").input_values).numpy(), dtype=np.float32, order='C')[... ,:MAX_INPUT_SIZE]

        # run inference
        start = time.time()
        host_output = infer_with_trt(context, host_input, cuda_input, host_output, cuda_output, engine)
        end = time.time()
        print(f"Inference: {end-start} sec.")

        # postprocess results
        output_data = torch.Tensor(host_output).view(len(host_input), -1, 32)
        predicted_ids=torch.argmax(output_data, dim=-1)
        transcription = tokenizer.batch_decode(predicted_ids)[0]
        print(transcription)
