#!/usr/bin/python3
# WindLocTest.py
# version 3

import requests
from datetime import datetime

# change location from xx to your location number
location = xx
loc = str(location)
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
    #exit();
   
url.close()
data = ""

print ("Loc:" + loc + " WindLoc:" + windLoc)
# KCOBROOM10    
# 1 KCOBROOM140
# 2 KCOBROOM187
# 4 KCOTHORN61 


def readwind():
    # https://www.wunderground.com/weather/us/co/broomfield/KCOBROOM140
    # works with different cities but needs a city i.e. co/erie/KCOB..., co/northglen/KCOB ... 
    # error if us/co/KCO...
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
                print (dtn, " * windSpd:" + str(windSpd) + " windDir:" + str(windDir))

    if (k < 1):
        windDir = 0
        windSpd = 0
        print ("I am lost in the wind file")

    data = ""
    

readwind()
