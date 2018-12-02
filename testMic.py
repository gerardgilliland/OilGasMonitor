# testMic.py

from datetime import datetime
import pyaudio # used for microphone
import wave # save microphone as wav file

print ("\n\nMatch the input_device_index in record() with your mic:")
p = pyaudio.PyAudio()
for i in range(p.get_device_count()):
    dev = p.get_device_info_by_index(i)
    print((i,dev['name'],dev['maxInputChannels']))
print ("\n\n")


wavename = "testMic.wav"
recordseconds = 30
dtn = datetime.now()
print("* start recording ", dtn, " wavename ", wavename)
mic = pyaudio.PyAudio()
RATE = 44100
CHUNK = 4096
CHANNELS = 1
FORMAT = pyaudio.paInt16
stream = mic.open(format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        frames_per_buffer=CHUNK,
        input_device_index = 2,
        input = True)
frames = []
for i in range(0, int(RATE / CHUNK * recordseconds)):
    data = stream.read(CHUNK)
    frames.append(data)

stream.stop_stream()
stream.close()
mic.terminate()
wf = wave.open(wavename, 'wb')
wf.setnchannels(CHANNELS)
wf.setsampwidth(mic.get_sample_size(FORMAT))
wf.setframerate(RATE)
wf.writeframes(b''.join(frames))
wf.close()
dtn = datetime.now()
print("* done recording ", dtn, " wavename ", wavename)
