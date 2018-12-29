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


wavename = "/home/pi/Desktop/testMic.wav"
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

"""
Adding Volume control
sudo nano ~/.asoundrc
#This section makes a reference to your I2S hardware, adjust the card name
# to what is shown in arecord -l after card x: before the name in []
#You may have to adjust channel count also but stick with default first
pcm.dmic_hw {
	type hw
	card sndrpisimplecar
	channels 2
	format S32_LE
}

#This is the software volume control, it links to the hardware above and after
# saving the .asoundrc file you can type alsamixer, press F6 to select
# your I2S mic then F4 to set the recording volume and arrow up and down
# to adjust the volume
# After adjusting the volume - go for 50 percent at first, you can do
# something like 
# arecord -D dmic_sv -c2 -r 48000 -f S32_LE -t wav -V mono -v myfile.wav
pcm.dmic_sv {
	type softvol
	slave.pcm dmic_hw
	control {
		name "Boost Capture Volume"
		card sndrpisimplecar
	}
	min_dB -3.0
	max_dB 30.0
}

arecord -D dmic_sv -c2 -r 44100 -f S32_LE -t wav -V mono -v file.wav
ctrl+C to break
Now you can run alsamixer - press F6 and select the I2S simple sound card
F5 change volume
record with software volume modified - NOTE: -c2 required or error
arecord -D dmic_sv -c2 -r 44100 -f S32_LE -d 10 -t wav -V mono -v recording.wav
-d, --duration=#        interrupt after # seconds
point aplay output to HDMI
amixer cset numid=3 2 # force HDMI output
volume control in upper right
aplay test1.wav
"""