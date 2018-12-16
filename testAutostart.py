#!/usr/bin/python3.5
# testAutostart.py
# also tests clear the shell

import time
import pyautogui


cmdfile = "cmdfile.txt"
cf = open (cmdfile,"w")
cmd = 1
cf.write (str(cmd))
cf.close
isRunning = cmd
cntr = 0
wait = 10

while isRunning == cmd:
    cntr += 1
    print("Hello World:", cntr)
    cf = open (cmdfile,"r")
    cmd = int(cf.read())
    cf.close
    if isRunning != cmd:
        print ("check interrupt")
        if cmd == 0:
            import os
            os.system("sudo reboot -h now")
        else: # incremented
            exit()

    if cntr > 20:
        cntr = 0
        # clear the shell
        pyautogui.keyDown('ctrl')  # hold down the ctrl key
        pyautogui.keyDown('l')     # press the l key
        pyautogui.keyUp('l')     # release the l
        pyautogui.keyUp('ctrl')    # release ctrl key

    time.sleep(wait)
