#!/usr/bin/python3
# WindLocTest.py

import requests
from datetime import datetime

# change location from xx to your location number
location = xx
sloc = str(location)
url = requests.get("https://www.modelsw.com/OilGasMonitor/GetWindLoc.php?Loc="+sloc)
data = url.text
j = data.find("Loc:")
l = len("Loc:")
j+=l
k = data.find("<br>", j)
loc = data[j:k]
if (loc == sloc):
    j = data.find("WindLoc:",k)
    l = len("WindLoc:")
    j+=l
    k = data.find("<br>", j)
    if (k > j):
        windLoc = data[j:k]
    
else:
    print ("failed to get location")
    exit();
   
url.close()
data = ""

print ("Loc:" + loc + " WindLoc:" + windLoc)
    


def SaveWind():
    url = requests.get("https://www.wunderground.com/personal-weather-station/dashboard?ID="+windLoc)
    data = url.text
    """  
      <div id="windCompass" class="wx-data" data-station="KCOBROOM140" data-variable="wind_dir_degrees" data-update-effect="wind-compass" style="transform:rotate(216deg);">
      <div class="dial">
      <div class="arrow-direction"></div>
      </div>
      </div>
      <div id="windCompassSpeed" class="wx-data" data-station="KCOBROOM140" data-variable="wind_speed">
      <h4><span class="wx-value">
      2.7
      </span>
      </h4>
      mph
      </div>
     """
    if (url != ""):
        dtn = datetime.now()
        j = data.find("windCompass")
        j = data.find("transform:rotate(", j)
        l = len("transform:rotate(")
        j+=l
        k = data.find("deg);", j)
        windDir = data[j:k]

        j = data.find("windCompassSpeed", k)
        j = data.find("wind_speed", j)
        j = data.find("wx-value", j)
        l = len("wx-value")+2  # get past the quote and greater than sign
        j+=l
        k = data.find("</span>", j)
        windSpd = data[j:k]
        windSpd = windSpd.replace("\n", "")
        windSpd = windSpd.strip()
        windSpd = float(windSpd)
        windSpd = int(windSpd * 10)
        
        j = data.find("</h4>", k)
        l = len("</h4>")
        j+=l
        k = data.find("</div>", j)
        windUnits = data[j:k]
        windUnits = windUnits.replace("\n", "")
        windUnits = windUnits.strip()

        if (windUnits == "mph"): # I am not lost in the file so save the data 
            print ("date:" + str(dtn) + " windDir:" + windDir + " windSpd:" + str(windSpd) + " windUnits:" + windUnits)
        else:
            print ("I am lost in the file")
            
    url.close()
    data = ""
    

SaveWind()
    
