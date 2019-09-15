#!/usr/bin/python3
# monitor.py

# 2019-04-12 -- Wind Version 3
# 2019-04-22 -- A.4 Separate folders for Images and Sound. SFTP all files to server
# 2019-04-22 -- A.6 Auto reboot on failure to transfer files to server
# 2019-04-25 -- A.7 Save filename local then move to Scan folder
# 2019-04-26 -- B.1 Change file date to use python strftime() instead of str()
# 2019-04-26 -- D.1 Add sleep in loop as workaround for time.sleep(wait) 
# 2019-04-26 -- E.1 Improve WiFiBoot file name and status
# 2019-05-18 -- J.1 Add ActiveLoc to selectively start LoadMonitor


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
Wind - weather page 
    8 Wind Direction degrees
    9 Wind Speed mph
Samson Microphone - USB
http://www.samsontech.com/samson/products/microphones/usb-microphones/gomic/
    10 SoundDb  dB
    11 Freq  Hz
"""

# https://docs.python.org/3.5/library/multiprocessing.html
# https://dsp.stackexchange.com/questions/32076/fft-to-spectrum-in-decibel

# import Adafruit_ADS1x15 # A/D converer
from datetime import datetime
from multiprocessing import Process, Queue
from picamera import PiCamera
import os
import logging
import pyaudio # used for microphone
import pysftp # sftp to server
import serial
import time
import wave # save microphone as wav file
import numpy as np
import scipy.io.wavfile as wf
import operator
import bme680
import requests

monlog = "/home/pi/Desktop/monitor.log"
fmt="%(asctime)s %(message)s"
logging.basicConfig(filename=monlog, level=logging.WARN, format=fmt)

# change location from xx to your location number
Location = xx
loc = str(Location)
cmd = 1
cmdfile = "/home/pi/cmdfile.txt"
activeLoc = 1
port = serial.Serial('/dev/ttyS0', baudrate=9600, timeout=2.0)
root = "/home/pi/OilGasMonitor/Scan/"
sound = "/home/pi/OilGasMonitor/Sound/"
image = "/home/pi/OilGasMonitor/Image/"
savedb = -120
sensor = bme680.BME680()
requestcntr = 0

dtn = datetime.now()
print(dtn, "Calibration data for BME680:")
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

dtn = datetime.now()
print(dtn, "\n\nInitial reading BME680:")
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

dtn = datetime.now()
print (dtn, "\n\nMatch the input_device_index in record() with your mic:")
p = pyaudio.PyAudio()
for i in range(p.get_device_count()):
    dev = p.get_device_info_by_index(i)
    print((i,dev['name'],dev['maxInputChannels']))
print ("\n\n")

# get the wind location during startup
dtn = datetime.now()
print (dtn, "\n\nGet the wind location during startup")
windLoc = ""
windDir = 0 # will be updated in readwind
windSpd = 0 # will be updated in readwind
fnam = open ("/home/pi/winddata.txt" ,"w")
s = str(int(windDir)) + "," + str(int(windSpd)) + ","
fnam.write(s)
fnam.close()

url = requests.get("https://www.modelsw.com/OilGasMonitor/GetWindLoc.php?Loc="+loc)
data = url.text
j = data.find("Loc:")
l = len("Loc:")
j+=l
k = data.find("<br>", j)
sloc = data[j:k]
if (loc == sloc):
    j = data.find("WindLoc:",k)
    l = len("WindLoc:")
    j+=l
    k = data.find("<br>", j)
    if (k > j):
        windLoc = data[j:k]
    
else:
    print ("failed to get wind location")
   
url.close()
data = ""
print ("Loc:" + loc + " WindLoc:" + windLoc + "\n\n")


def record(q, wavename, recordseconds):
    dtn = datetime.now()
    print(dtn, " * start recording ", " wavename ", wavename)
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
    wf = wave.open(sound + wavename, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(mic.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()
    dtn = datetime.now()
    print(dtn, " * done recording ", " wavename ", wavename)
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
    global sound
    global image
    global activeLoc

    if prevwavename == "":
        print ("prevwavenmame is null")

    else:
        dtn = datetime.now()
        print(dtn, " * start analyzing ", " prevwavename ", prevwavename)

        # Load the file
        fs, signal = wf.read(sound + prevwavename)
        # Take slice
        N = 32768
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
            os.remove(sound + prevwavename)

        else:
            camera = PiCamera()
            #camera.rotate = 180  # if needed
            camera.start_preview()
            camera.annotate_text_size = 60
            camera.brightness = 50 # I haven't messed with this
            sdtn = str(dtn)
            camera.annotate_text = sdtn[:16]
            camera.capture(image + prevcameraname)
            camera.stop_preview()
            camera.close()

        fnam = open ("/home/pi/" + prevfilename,"a") 
        s = str(int(maxdb)) + "," + str(int(freqmxdb)) + "\n"
        fnam.write(s)
        fnam.close()
        # move the completed file to the Scan folder
        os.rename("/home/pi/" + prevfilename, root + prevfilename)
        dtn = datetime.now()
        print(dtn, " * save db and freq: ", " prevfilename ", prevfilename)

        fnam = open (root + prevfilename,"r")
        s = fnam.read()
        fnam.close()

        dtn = datetime.now()
        print(" prevfilename ", prevfilename, "data: ", s)
        x = savefile(prevfilename)
        prevwavename = ""

        cf = open (cmdfile,"r")
        cmd = int(cf.read())
        cf.close

        if Location == activeLoc and cmd == 1:
            dtn = datetime.now()
            print(dtn, " * sleep 7 ")
            time.sleep(7)
            dtn = datetime.now()
            print(dtn, " * activeLoc:" + str(activeLoc) + " run LoadMonitor.php ")
            import requests
            try:
                r = requests.get('https://www.modelsw.com/OilGasMonitor/LoadMonitor.php')
                dtn = datetime.now()
                # r = 200 -- the server successfully answered the http request  
                print(dtn, " * done LoadMonitor.php status:", str(r))
                if (r == 200):
                    requestcntr = 0  
            except:
                requestcntr = requestcntr + 1
                if requestcntr == 4:
                    cmd = 4
                    print("request:" + str(r))
                    fnamloc = "ConnectLoad" + basename + ".txt"
                    fnam = open (root + fnamloc, "w") 
                    dtn = datetime.now()
                    s = str(dtn) + '\n'
                    s += "request: " + str(r) + '\n'
                    s += "OSError: " + str(e.errno) + '\n'
                    s += "error: " + str(e) + '\n'
                    s += "cmd: 4" + '\n'
                    fnam.write(s)
                    fnam.close()

#end spectrum


def savefile(prevfilename):
    global root
    global activeLoc

    cf = open (cmdfile,"r")
    cmd = int(cf.read())
    cf.close
    dtn = datetime.now()
    print(dtn, " * start saving ")

    if prevfilename > "" and cmd == 1:
        # replace xx with your location (2 places) and yourlogin with the login you use to log into modelsw.com
        srv = pysftp.Connection(host="home208845805.1and1-data.host", username="u45596567-OilGas-xx", password="yourlogin_Mxx")

        local = os.listdir(root)
        for j in local:
            srv.put(root + j)
        
        # Get the directory and file listing
        # http://stackoverflow.com/questions/3207219/how-to-list-all-files-of-a-directory-in-python
        remote = srv.listdir()
        srv.get("zActiveLocFile.txt")
        # Closes the connection
        srv.close()

        af = open ("zActiveLocFile.txt","r")
        slocations = af.read()
        af.close
        locations = slocations.split(",")
        activeLoc = int(locations[0])
        nextLoc = int(locations[1])
        maxLoc = int(locations[2]) * 2

        # prints out the directories and files, line by line
        cntr = 0
        for i in remote:
            if i[:1] < "z":
                cntr = cntr + 1
            #else:  # remove the z from the front of the file name.
            #    i = i[1:]

            for j in local:
                if i == j:
                    # print ("delete local file: " + j)
                    os.remove(root + j)
                    break
        
        remote = ""
        local = ""
        
        if cntr > maxLoc:  # if the LoadMonitor has not been loading files
            if Location == nextLoc:  # if I will be loading next time
                activeLoc = nextLoc  # run LoadMonitor

        dtn = datetime.now()
        print(dtn, " * done transfering ", " prevfilename ", prevfilename)

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
    wait = (60 - dtn.second) / rng   # approx 5 seconds

    print(dtn, " * start monitoring ", " filename ", filename)
    locArray = [0]*8 # will add two more below and two more under spectrum
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
        #dtn = datetime.now()
        #print(dtn, ' pms:' + str(p[0]) + ", "  + str(p[1]) + ", " + str(p[2]) + " t:" + str(int(s[0])) + " p:" + str(int(s[1])) + " rh:" + str(int(s[2])) + " ohms:" + str(int(s[3])))       

    #for i in range(4):
    #    methane[i] = methane[i]/rng+0.5

    for i in range(3):
        pms[i] = pms[i]/rng+0.5

    for i in range(4):
        scns[i] = scns[i]/rng+0.5

    locArray[0]=int(pms[0]) # pms1.0
    locArray[1]=int(pms[1]) # pms2.5
    locArray[2]=int(pms[2]) # pms10.
    locArray[3]=int(scns[0]) # temp degrees F
    locArray[4]=int(scns[1]) # pressure Pa
    locArray[5]=int(scns[2]) # Rh * 100
    locArray[6]=int(scns[3]) # VOC Ohms
    locArray[7]=int(0) # int(methane[0]) # ppm -- will (hopefully) become smog

    fnam = open ("/home/pi/" + filename,"w")
    for i in range(8): # will append two more below and two more in spectrum
        sep = ","
        s = str(locArray[i]) + sep
        fnam.write(s)

    fnam.close()

    fnam = open ("/home/pi/winddata.txt" ,"r")
    s = fnam.read()
    fnam.close()
    fnam = open ("/home/pi/" + filename, "a") 
    fnam.write(s)
    fnam.close()

    # print ("monitor locArray=", locArray)
    dtn = datetime.now()
    print(dtn, " * done monitoring ", " filename ", filename)

# end monitor


def readwind(q, wait):
    if (windLoc == ""):
        return

    time.sleep(wait) # get the data appoximately half way into the minute
    # https://www.wunderground.com/weather/us/co/broomfield/KCOBROOM140
    # works with different cities but needs a city i.e. co/erie/KCOB..., co/northglen/KCOB ... 
    # error if us/co/KCO...
    try:
        url = requests.get("https://www.wunderground.com/weather/us/co/broomfield/"+windLoc)
        urldata = url.text
        """  
            class="wind-compass" style="transform:rotate(184deg);">
            <div _ngcontent-c21="" class="dial">
            <div _ngcontent-c21="" class="arrow-direction"></div>
            </div>
            </div>
            <div _ngcontent-c21="" class="wind-north">N</div>
            <div _ngcontent-c21="" class="wind-speed">
            <strong _ngcontent-c21="">0</strong>
            </div>       
        """
        k = -1
        if (urldata != ""):
            requestcntr = 0
            dtn = datetime.now()
            j = urldata.find('class="wind-compass"') # this is unique in the file
            data = urldata[j:j+500]
            url.close()
            urldata = ""
            #print (data)
            j = data.find('transform:rotate(') 
            l = len('transform:rotate(') 
            j +=l
            k = data.find('deg);', j)        
            windDir = data[j:k]
            if (k > 1): # I am not lost in the file so continue
                j = data.find('class="wind-speed"', k)
                j = data.find('<strong _ngcontent', j)
                j = data.find('="">', j)
                l = len('="">')
                j +=l
                k = data.find('</strong>', j)
                windSpd = data[j:k]
                if (k > 1): # I am not lost in the file so continue
                    #print (" ")
                    print (dtn, " * windDir:" + str(windDir) + " windSpd:" + str(windSpd))

        data = ""

        if (k < 1):
            windDir = 0
            windSpd = 0
            print ("I am lost in the wind file")

    except:
        requestcntr = requestcntr + 1
        if requestcntr == 4:
            cmd = 4
            print("request:" + str(r))
            fnamloc = "ConnectWeather" + basename + ".txt"
            fnam = open (root + fnamloc, "w") 
            dtn = datetime.now()
            s = str(dtn) + '\n'
            s += "request: " + str(r) + '\n'
            s += "OSError: " + str(e.errno) + '\n'
            s += "error: " + str(e) + '\n'
            s += "cmd: 4" + '\n'
            fnam.write(s)
            fnam.close()

    fnam = open ("/home/pi/winddata.txt" ,"w")
    s = str(int(windDir)) + "," + str(int(windSpd)) + ","
    fnam.write(s)
    fnam.close()

# end readwind


def main():
    # Main loop.
    import os
    filename = ""
    wavename = ""
    cameraname = ""
    cf = open (cmdfile,"w")
    cmd = 1
    cf.write (str(cmd))
    cf.close
    isRunning = cmd
    dtn = datetime.now()
    dow = dtn.weekday()
    print (dtn, " mainloop", "weekday", dow)
    while dtn.second > 0:
        time.sleep(.5)
        dtn = datetime.now()
        print (dtn, "waiting")

    dtn = datetime.now()
    print (dtn, " isRunning")

    while isRunning == cmd:
        dtn = datetime.now()
        basename = dtn.strftime("%Y-%m-%d %H_%M") + "_" + loc    # 2018-05-17 02_21_1
        print (dtn, "basename: " + basename)
        prevfilename = filename
        prevwavename = wavename
        prevcameraname = cameraname
        filename = basename + ".txt"
        wavename = basename + ".wav"
        cameraname = basename + ".png"
        recordseconds = 60 - dtn.second
        rng = 12

        q = Queue()
        mon = Process (target=monitor, args=(q, rng, filename))
        dtn = datetime.now()
        # print (dtn, " * start monitor ", " rng", rng, " filename ", filename)
        mon.start()

        rec = Process(target=record, args=(q, wavename, recordseconds))
        dtn = datetime.now()
        # print (dtn, " * start record ", " wavename ", wavename, " recordseconds ", recordseconds)
        rec.start()

        spec = Process(target=spectrum, args=(q, prevwavename, prevfilename, prevcameraname))
        dtn = datetime.now()
        # print (dtn, " * start spectrum ", " prevwavename ", prevwavename, " prevfilename ", prevfilename, " prevcameraname ", prevcameraname)
        spec.start()

        wind = Process(target=readwind, args=(q, 25))
        dtn = datetime.now()
        # print (dtn, " * start readwind ")
        wind.start()

        mon.join()
        rec.join()
        spec.join()
        wind.join()

        cf = open (cmdfile,"r")
        cmd = int(cf.read())
        cf.close

        # reboot if the files are not being transferred
        # specifically 5 files -- 5 minutes -- just try it once
        # if they don't transfer then the one added here will be number 6 so we won't reboot again
        local = os.listdir(root)
        cntr = len(local)
        if cntr == 5:            
            fnamloc = "WiFiBoot" + basename + ".txt"
            fnam = open (root + fnamloc, "w") 
            dtn = datetime.now()
            s = str(dtn) + '\n'
            s += "cmd: " + str(cmd) + '\n'
            s += "Record Count: " + str(cntr) + '\n'
            for j in local:
                s += j + '\n'

            fnam.write(s)
            fnam.close()
            cmd = 0

        if isRunning != cmd: # 1 = run
            print ("check interrupt") 
            if cmd == -1:
                print ("cmd -1 = shutdown")
                os.system("sudo shutdown -h now")
            elif cmd == 0:
                print ("cmd 0 = reboot")
                os.system("sudo reboot -h now")                
            elif cmd == 2:
                print ("cmd 2 = exit")
                exit()
            elif cmd == 3:
                print ("cmd 3 = test WiFi failure")
                isRunning = cmd
            elif cmd == 4:
                print ("cmd 4 = reboot Connection error")
                os.system("sudo reboot -h now")                
            else: # unknown
                print ("cmd " + str(cmd) + "unknown")
                isRunning = cmd

        if dow != dtn.weekday():
            dow = dtn.weekday()
            os.system("clear")



if __name__ == '__main__':
    main()
