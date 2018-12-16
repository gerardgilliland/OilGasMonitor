# Monitor Oil and Gas 
"""
Inputs:
PM2.5 Air Quality Sensor - I2C
https://learn.adafruit.com/pm25-air-quality-sensor
    0 PM 1.0 um
    1 PM 2.5 um
    2 PM 10  um
BMI680 Air Quality - I2C
    3 Temp Degrees F
    4 Pressure Pa 
    5 RH   Percent (x 100)
    6 Ohms 0-300,000 Ohms
    7 Methane ppm -- place holder -- input removed
Samson Microphone - USB
http://www.samsontech.com/samson/products/microphones/usb-microphones/gomic/
    8 SoundDb  dB
    9 Freq  Hz
"""

# https://docs.python.org/3.5/library/multiprocessing.html
# https://dsp.stackexchange.com/questions/32076/fft-to-spectrum-in-decibel

# import Adafruit_ADS1x15 # A/D converer
from datetime import datetime
from multiprocessing import Process, Queue
from picamera import PiCamera
import os
import pyaudio # used for microphone
import pysftp # sftp to server
import serial
import time
import wave # save microphone as wav file
import numpy as np
import matplotlib.pyplot as plt
import scipy.io.wavfile as wf
import operator
import bme680
import pyautogui  # automate key strokes to clear the shell


# adc = Adafruit_ADS1x15.ADS1115()
# GAIN = 1 # set to 1
Location = xx
loc = str(Location)
port = serial.Serial('/dev/ttyS0', baudrate=9600, timeout=2.0)
root = "/home/pi/OilGasMonitor/Scan/"
savedb = -120
sensor = bme680.BME680()

print("Calibration data for BME680:")
for name in dir(sensor.calibration_data):

    if not name.startswith('_'):
        value = getattr(sensor.calibration_data, name)

        if isinstance(value, int):
            print("{}: {}".format(name, value))

# These oversampling settings can be tweaked to 
# change the balance between accuracy and noise in
# the data.

sensor.set_humidity_oversample(bme680.OS_2X)
sensor.set_pressure_oversample(bme680.OS_4X)
sensor.set_temperature_oversample(bme680.OS_8X)
sensor.set_filter(bme680.FILTER_SIZE_3)
sensor.set_gas_status(bme680.ENABLE_GAS_MEAS)

print("\n\nInitial reading BME680:")
for name in dir(sensor.data):
    value = getattr(sensor.data, name)

    if not name.startswith('_'):
        print("{}: {}".format(name, value))

sensor.set_gas_heater_temperature(320)
sensor.set_gas_heater_duration(150)
sensor.select_gas_heater_profile(0)

# Up to 10 heater profiles can be configured, each
# with their own temperature and duration.
# sensor.set_gas_heater_profile(200, 150, nb_profile=1)
# sensor.select_gas_heater_profile(1)

print ("\n\nMatch the input_device_index in record() with your mic:")
p = pyaudio.PyAudio()
for i in range(p.get_device_count()):
    dev = p.get_device_info_by_index(i)
    print((i,dev['name'],dev['maxInputChannels']))
print ("\n\n")


def record(q, wavename, recordseconds):
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
    wf = wave.open(root + wavename, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(mic.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()
    dtn = datetime.now()
    print("* done recording ", dtn, " wavename ", wavename)
#end record

def dbfft(x, fs, win=None, ref=32768):
    """
    Calculate spectrum in dB scale
    Args:
        x: input signal
        fs: sampling frequency
        win: vector containing window samples (same length as x).
             If not provided, then rectangular window is used by default.
        ref: reference value used for dBFS scale. 32768 for int16 and 1 for float

    Returns:
        freq: frequency vector
        s_db: spectrum in dB scale
    """

    maxdb = -120
    fmxdb = 0

    N = len(x)  # Length of input sequence

    if win is None:
        win = np.ones(1, N)
    if len(x) != len(win):
            raise ValueError('Signal and window must be of the same length')
    x = x * win

    # Calculate real FFT and frequency vector
    sp = np.fft.rfft(x)
    freq = np.arange((N / 2) + 1) / (float(N) / fs)

    # Scale the magnitude of FFT by window and factor of 2,
    # because we are using half of FFT spectrum.
    s_mag = np.abs(sp) * 2 / np.sum(win)

    # Convert to dB Full Scale
    s_dbfs = 20 * np.log10(s_mag/ref)

    if maxdb < s_dbfs.any():
        # maxdb = s_dbfs.max()
        max_index, maxdb = max(enumerate(s_dbfs), key=operator.itemgetter(1))
        # print ("max_index=", max_index)
        freqmxdb = freq[max_index]
        # print ("max dB=", maxdb, " freq at max dB=", fmxdb)

    #freq = int(freq)
    #db = int(s_dbfs)

    return freqmxdb, maxdb


def spectrum(q, prevwavename, prevfilename, prevcameraname):
    global savedb
    global root

    if prevwavename == "":
        print ("prevwavenmame is null")

    else:
        dtn = datetime.now()
        print("* start analyzing ", dtn, " prevwavename ", prevwavename)

        # Load the file
        fs, signal = wf.read(root + prevwavename)
        # Take slice
        N = 1024
        win = np.hamming(N)
        freqmxdb, maxdb = dbfft(signal[0:N], fs, win)

        cmdsound = "cmdsound.txt"
        cs = open (cmdsound,"r")
        dblimit = int(cs.read())
        cs.close
        cmddbK = "cmddbK.txt"
        cdbK = open (cmddbK,"r")
        K = int(cdbK.read())
        cdbK.close

        # Scale from dBFS to dB
        maxdb = int(maxdb + K)

        # in case of error use zeros so file transfers
        if maxdb < 0:
            maxdb = 0
        if freqmxdb < 0:
            freqmxdb = 0

        # if a low maxdb then delete the wave file else save it for off line analysis
        if maxdb < dblimit:
            os.remove(root + prevwavename)

        else:
            camera = PiCamera()
            #camera.rotate = 180  # if needed
            camera.start_preview()
            camera.annotate_text_size = 60
            camera.brightness = 50 # I haven't messed with this
            sdtn = str(dtn)
            camera.annotate_text = sdtn[:16]
            camera.capture(root + prevcameraname)
            camera.stop_preview()
            camera.close()

        fnam = open (root + prevfilename,"a") 
        s = str(int(maxdb)) + "," + str(int(freqmxdb)) + "\n"
        fnam.write(s)
        fnam.close()
        dtn = datetime.now()
        print("* save db and freq: ", dtn, " prevfilename ", prevfilename)

        fnam = open (root + prevfilename,"r")
        s = fnam.read()
        fnam.close()

        dtn = datetime.now()
        print("data: ", s, " prevfilename ", prevfilename)
        x = savefile(prevfilename)
        prevwavename = ""

        if Location == 1:
            dtn = datetime.now()
            print("* sleep 7 ", dtn)
            time.sleep(7)
            dtn = datetime.now()
            print("* run LoadMonitor.php ", dtn)
            import requests
            r = requests.get('https://www.modelsw.com/OilGasMonitor/LoadMonitor.php')
            dtn = datetime.now()
            # r = 200 -- the server successfully answered the http request  
            print("* done LoadMonitor.php status:", str(r), " ", dtn)

#end spectrum


def savefile(prevfilename):
    global root

    dtn = datetime.now()
    # print("* start saving ", dtn)

    if prevfilename > "":
        srv = pysftp.Connection(host="home208845805.1and1-data.host", username="u45596567-OilGas-xx", password="yourlogin_Mxx")
        srv.put(root + prevfilename)
        # Get the directory and file listing
        # http://stackoverflow.com/questions/3207219/how-to-list-all-files-of-a-directory-in-python
        data = srv.listdir()
        # Closes the connection
        srv.close()

        # Prints out the directories and files, line by line
        #for i in data:
        #    print (i)  
        #    if (i == prevfilename):
        #        os.remove(root + prevfilename)
        os.remove(root + prevfilename)

    dtn = datetime.now()
    print("* done transfering ", dtn, " prevfilename ", prevfilename)
    prevfilename = ""

# end savefile


def read_pm_line(_port):
    rv = b''
    while True:
        ch1 = _port.read()
        if ch1 == b'\x42':
            ch2 = _port.read()
            if ch2 == b'\x4d':
                rv += ch1 + ch2
                rv += _port.read(28)
                return rv
#end read_pm_line


def monitor(q, rng, filename):
    global root
    global sensor

    dtn = datetime.now()
    sdtn = str(dtn)
    wait = (60 - dtn.second) / rng

    print("* start monitoring ", dtn, " filename ", filename)
    locArray = [0]*8 # will add two more under spectrum
    # methane = [0.0]*4
    scns = [0.0]*4
    pms = [0.0]*3
    # v = [0.0]*4 # methane
    s = [0.0]*4 # temp, press, rh, ohms
    p = [0.0]*3 # pms 1, 2.5, 10


    # sum the data
    for t in range(rng): # every 5 seconds
        # Pause for 5 seconds.
        time.sleep(wait)

        #for i in range(4): # I am only using v[0]
            # Read the specified ADC channel using the previously set gain value.
        #    v[i] = adc.read_adc(i, gain=GAIN)
        #    methane[i] += v[i]

        rcv_list = []
        rcv = read_pm_line(port) # read the pms25 port
        # ACTUAL
        p[0] = rcv[10] * 256 + rcv[11] # 0.3 to 1.0 um
        p[1] = rcv[12] * 256 + rcv[13] # 1.0 to 2.5 um
        p[2] = rcv[14] * 256 + rcv[15] # 2.5 to 10.0 um
        # TEST (higher numbers)
        #p[0] = rcv[16] * 256 + rcv[17] # 0.3 to 1.0 um
        #p[1] = rcv[18] * 256 + rcv[19] # 1.0 to 2.5 um
        #p[2] = rcv[20] * 256 + rcv[21] # 2.5 to 10.0 um
        for i in range(3):
            pms[i] += p[i]

        # read temp, press, humidity, voc ohms
        if sensor.get_sensor_data():
            s[0] = int(sensor.data.temperature * 9 / 5 + 32.5)
            s[1] = int(sensor.data.pressure * 100) # pascals
            s[2] = int(sensor.data.humidity + 0.5)
            s[3] = int(sensor.data.gas_resistance)

        for i in range(4):
            scns[i] += s[i]

        # print the values.
        dtn = datetime.now()
        # print('pms:' + str(p[0]) + ", "  + str(p[1]) + ", " + str(p[2]) + " t:" + str(int(s[0])) + " p:" + str(int(s[1])) + " rh:" + str(int(s[2])) + " ohms:" + str(int(s[3])) + " dtn:" + str(dtn))       

    #for i in range(4):
    #    methane[i] = methane[i]/rng+0.5

    for i in range(3):
        pms[i] = pms[i]/rng+0.5

    for i in range(4):
        scns[i] = scns[i]/rng+0.5

    locArray[0]=int(pms[0]) # pms1.0
    locArray[1]=int(pms[1]) # pms2.5
    locArray[2]=int(pms[2]) # pms10.
    locArray[3]=int(scns[0]) # temp C * 100
    locArray[4]=int(scns[1]) # pressure Pa
    locArray[5]=int(scns[2]) # Rh * 100
    locArray[6]=int(scns[3]) # VOC Ohms
    locArray[7]=int(0) # int(methane[0]) # ppm

    fnam = open (root + filename,"w")
    for i in range(8): # will append two more in spectrum
        sep = ","
        s = str(locArray[i]) + sep
        fnam.write(s)

    fnam.close()

    # print ("monitor locArray=", locArray)
    dtn = datetime.now()
    # print("* done monitoring ", dtn)    
# end monitor


def main():
    # Main loop.
    cmdfile = "cmdfile.txt"
    cf = open (cmdfile,"w")
    cmd = 1
    cf.write (str(cmd))
    cf.close
    isRunning = cmd

    dtn = datetime.now()
    dow = dtn.weekday()
    print ("mainloop ", dtn, "weekday", dow)
    wait = 60 - dtn.second
    print ("wait:" + str(wait))
    time.sleep(wait)
    print (" isRunning")
    filename = ""
    wavename = ""
    cameraname = ""

    while isRunning == cmd:
        prevfilename = filename
        prevwavename = wavename
        prevcameraname = cameraname

        dtn = datetime.now()
        rng = 12
        sdtn = str(dtn)
        #basename = sdtn[:16] + "_" + loc   # was 2018-05-17 02:21_1  colon won't transfer to windows os
        basename = sdtn[:13] + "_" + sdtn[14:16] + "_" + loc    # now 2018-05-17 02_21_1
        filename = basename + ".txt"
        wavename = basename + ".wav"
        cameraname = basename + ".png"
        recordseconds = 60 - dtn.second

        q = Queue()
        mon = Process (target=monitor, args=(q, rng, filename))
        dtn = datetime.now()
        # print ("* start monitor ", dtn, " rng", rng, " filename ", filename)
        mon.start()

        rec = Process(target=record, args=(q, wavename, recordseconds))
        dtn = datetime.now()
        # print ("* start record ", dtn, " wavename ", wavename, " recordseconds ", recordseconds)
        rec.start()

        spec = Process(target=spectrum, args=(q, prevwavename, prevfilename, prevcameraname))
        dtn = datetime.now()
        # print ("* start spectrum ", dtn, " prevwavename ", prevwavename, " prevfilename ", prevfilename, " prevcameraname ", prevcameraname)
        spec.start()

        mon.join()
        rec.join()
        spec.join()

        cf = open (cmdfile,"r")
        cmd = int(cf.read())
        cf.close
        if isRunning != cmd:
            # print ("check interrupt")
            if cmd < 0:
                import os
                os.system("sudo shutdown -h now")
            elif cmd == 0:
                import os
                os.system("sudo reboot -h now")
            else: # incremented
                exit()

        if dow != dtn.weekday():
            dow = dtn.weekday()
            # clear the shell ctrl+l
            pyautogui.keyDown('ctrl')
            pyautogui.keyDown('l')
            pyautogui.keyUp('l')
            pyautogui.keyUp('ctrl')



if __name__ == '__main__':
    main()
