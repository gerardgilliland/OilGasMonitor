# testCamera.py

from picamera import PiCamera
from time import sleep

camera = PiCamera()
# camera.resolution = (1920,1080) # default -- can be up to (3280 x 2464)
camera.start_preview()
camera.brightness = 50 # I haven't messed with this
camera.annotate_text = "Title - Camera Test"
sleep(5)
camera.capture('/home/pi/Desktop/CameraTest.jpg')
camera.stop_preview()
camera.close()
