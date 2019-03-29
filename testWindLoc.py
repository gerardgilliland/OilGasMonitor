#!/usr/bin/python3
# WindLocTest.py

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
    #url = requests.get("https://www.wunderground.com/dashboard/pws/"+windLoc+"?cm_ven=localwx_pwsdash")
    url = requests.get("https://www.wunderground.com/dashboard/pws/"+windLoc)
    urldata = url.text
    """  
    class="wind-dial" src="https://s.w-x.co/wu/assets/static/images/pws/Wind-Dial.svg">
    class="big" style="font-size:   
    ;">             
    7
    </span>
    <span _ngcontent-c7="" class="small">
    mph
    </span></div>
    <div _ngcontent-c7="" 
    class="arrow-wrapper" style="transform: translateX(-50%) 
    rotate(287deg);">
    """
    if (urldata != ""):
        dtn = datetime.now()
        j = urldata.find('class="wind-dial"') # this is unique in the file
        data = urldata[j:j+500]
        url.close()
        urldata = ""
        #print (data)
        j = data.find('class="big" style="font-size:') # this line varies after font-size: 
        j = data.find(';">') # but they both end with this
        l = len(';">')   # should be 3
        j +=l
        k = data.find("</span>", j)
        windSpd = data[j:k]
        
        j = data.find('class="small">', j)
        l = len('class="small">')
        j +=l
        k = data.find("</span>", j)
        windUnits = data[j:k]

        j = data.find('class="arrow-wrapper"', j)
        j = data.find('rotate(', j)
        l = len('rotate(')
        j +=l
        k = data.find('deg);', j)
        windDir = data[j:k]
        windDir = int(windDir)
        windDir -= 180

        if (windUnits == "mph"): # I am not lost in the file so save the data
            #print (" ")
            print ("date:" + str(dtn) + " windSpd:" + str(windSpd) + " windUnits:" + windUnits + " windDir:" + str(windDir))
            print ("The Weather Information is Copyright by TWC Product and Technology LLC.")
            print ("I read it once each minute. You can only use it for personal, non-commercial use.")
        else:
            print ("I am lost in the wind file")
        data = ""
    

readwind()
    
