import time
import librosa
import torch
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor
import onnx
import numpy as np
from torch2trt import torch2trt
from torch2trt import TRTModule

from tensorrt_ import build_engine, load_engine, infer_with_trt, init_trt_buffers

task='serialize'
ENGINE_FILE_PATH = '../../models/wav2vec.trt'
ONNX_FILE_PATH = '../../models/wav2vec.onnx'
MAX_INPUT_SIZE = 50000

if task=='no TensorRT':
    tokenizer = Wav2Vec2Processor.from_pretrained("facebook/wav2vec2-base-960h")
    model = Wav2Vec2ForCTC.from_pretrained("facebook/wav2vec2-base-960h")
    model.eval()
    model.cuda()
    
    file_name = '../../data/Hello.wav'
    input_audio, _ = librosa.load(file_name, sr=16000)
    # boucle pour tous les traitements
    for _ in range(100):
        input_ = tokenizer(input_audio, sampling_rate=16000, return_tensors="pt").input_values
        start = time.time()
        logits = model(input_.cuda()).logits.cpu() #on envoit les données sur gpu puis on transfère les résultats au cpu
        end = time.time()
        print(f"Inference: {end-start} sec.")
        predicted_ids = torch.argmax(logits, dim=-1)
        transcription = tokenizer.batch_decode(predicted_ids)[0]
        print(transcription)

elif task=='serialize':
    model = Wav2Vec2ForCTC.from_pretrained("facebook/wav2vec2-base-960h")
    model.eval().cuda()
    # create example data
    dummy_input = torch.ones((1, 100000)).float().cuda()
    # convert to TensorRT feeding sample data as input
    model_trt = torch2trt(model, [dummy_input], fp16_mode=True)
    torch.save(model_trt.state_dict(), '../../models/wav2vec.trt')
    
elif task=='TensorRT': 
    model = TRTModule()
    model.load_state_dict(torch.load('../../models/wav2vec.trt'))
    tokenizer = Wav2Vec2Processor.from_pretrained("facebook/wav2vec2-base-960h")
    
    file_name = '../../data/Hello.wav'
    input_audio, _ = librosa.load(file_name, sr=16000)
    # boucle pour tous les traitements
    for _ in range(100):
        input_ = tokenizer(input_audio, sampling_rate=16000, return_tensors="pt").input_values
        start = time.time()
        logits = model(input_.cuda()).logits.cpu() #on envoit les données sur gpu puis on transfère les résultats au cpu
        end = time.time()
        print(f"Inference: {end-start} sec.")
        predicted_ids = torch.argmax(logits, dim=-1)
        transcription = tokenizer.batch_decode(predicted_ids)[0]
        print(transcription)
    
'''elif task=='save':
    # Saving model
    tokenizer = Wav2Vec2Processor.from_pretrained("facebook/wav2vec2-base-960h")
    model = Wav2Vec2ForCTC.from_pretrained("facebook/wav2vec2-base-960h")
    model.eval()
    file_name = '../../data/Hello.wav'
    input_audio, _ = librosa.load(file_name, sr=16000)
    dummy_input = tokenizer(input_audio, sampling_rate=16000, return_tensors="pt").input_values
    # indicates that the dimension 1 of input can vary
    dynamic_axes = {'input': {1: 'len_sound'},'output': {1: 'num_letters'}}
    torch.onnx.export(model, dummy_input, ONNX_FILE_PATH, input_names=['input'],
                      output_names=['output'], dynamic_axes=dynamic_axes, export_params=True)

    onnx_model = onnx.load(ONNX_FILE_PATH)
    onnx.checker.check_model(onnx_model)

elif task=='serialize':
    # Serializing model   
    build_engine(ONNX_FILE_PATH, ENGINE_FILE_PATH, MAX_INPUT_SIZE)

elif task=='TensorRT': 
    # initialize TensorRT engine
    engine = load_engine(ENGINE_FILE_PATH, ONNX_FILE_PATH)

    file_name = '../../data/Hello.wav'
    input_audio, _ = librosa.load(file_name, sr=16000)
    tokenizer = Wav2Vec2Processor.from_pretrained("facebook/wav2vec2-base-960h")
    context = engine.create_execution_context()
    cuda_input, host_output, cuda_output = init_trt_buffers(engine, context, MAX_INPUT_SIZE)
    
    for _ in range(100):
        # preprocess input data
        host_input = np.array((tokenizer(input_audio, 
                                         sampling_rate=16000, 
                                         return_tensors="pt").input_values).numpy(), dtype=np.float32, order='C')[:MAX_INPUT_SIZE]

        # run inference
        start = time.time()
        host_output = infer_with_trt(context, host_input, cuda_input, host_output, cuda_output, engine)
        end = time.time()
        print(f"Inference: {end-start} sec.")

        # postprocess results
        output_data = torch.Tensor(host_output).view(len(host_input), -1, 32)
        predicted_ids=torch.argmax(output_data, dim=-1)
        transcription = tokenizer.batch_decode(predicted_ids)[0]
        print(transcription)'''