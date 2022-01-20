import pyaudio
import wave
 
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
CHUNK = 512
RECORD_SECONDS = 5
WAVE_OUTPUT_FILENAME = "../data/pytest.wav"
MIC_INDEX = 11
 
audio = pyaudio.PyAudio()

# start Recording
stream = audio.open(format=FORMAT, channels=CHANNELS, input_device_index=MIC_INDEX,
                rate=RATE, input=True,
                frames_per_buffer=CHUNK)
print ("recording...")
frames = []
 
for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
    data = stream.read(CHUNK, exception_on_overflow = False)
    frames.append(data)
print ("finished recording")

# stop Recording
stream.stop_stream()
stream.close()
audio.terminate()
 
waveFile = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
waveFile.setnchannels(CHANNELS)
waveFile.setsampwidth(audio.get_sample_size(FORMAT))
waveFile.setframerate(RATE)
waveFile.writeframes(b''.join(frames))
waveFile.close()


audio = pyaudio.PyAudio()
# Open the sound file 
wf = wave.open(WAVE_OUTPUT_FILENAME, 'rb')

# Open a .Stream object to write the WAV file to
# 'output = True' indicates that the sound will be played rather than recorded
stream = audio.open(format = FORMAT,
                channels = CHANNELS,
                output_device_index=11,
                rate = RATE,
                frames_per_buffer=CHUNK,
                output = True)

# Read data in chunks
data = wf.readframes(CHUNK)

# Play the sound by writing the audio data to the stream
while len(data)>2:
    stream.write(data)
    data = wf.readframes(CHUNK)
    
# Close and terminate the stream
stream.close()
audio.terminate()