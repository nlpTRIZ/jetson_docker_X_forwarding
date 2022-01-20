import librosa
import torch
import numpy as np
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor

tokenizer = Wav2Vec2Processor.from_pretrained("facebook/wav2vec2-base-960h")
model = Wav2Vec2ForCTC.from_pretrained("facebook/wav2vec2-base-960h")
model.cuda()

# boucle pour tous les traitements
for _ in range(10):
    file_name = '../data/Hello.wav'
    input_audio, _ = librosa.load(file_name, sr=16000)

    input_values = tokenizer(input_audio, sampling_rate=16000, return_tensors="pt").input_values
    logits = model(input_values.cuda()).logits.cpu() #on envoit les données sur gpu puis on transfère les résultats au cpu
    predicted_ids = torch.argmax(logits, dim=-1)
    transcription = tokenizer.batch_decode(predicted_ids)[0]
    print(transcription)

    if transcription[:4] == 'OPEN':
        print('production')
    elif transcription[:4] == 'TEST':
        print('maintenance')
    else:
        print('no access')
