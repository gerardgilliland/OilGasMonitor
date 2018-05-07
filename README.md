# OilGasMonitor
Citizen’s Oil and Gas Monitoring of Particles, VOCs, and Sound. Store data on Common server.

The concept is to monitor Air Particles, VOCs, and Sound levels in real-time. 
Five second data averaged each minute. Sound is maximum for the minute and updated each minute. 
The intent is to keep the driller and producer honest in their commitment to low air particles, noise, and VOCs.
	
Application: Citizen’s Oil and Gas Monitor.
I see this as a "citizen" monitoring system. 
Each system can be built for less than $200 and uses their router and internet connection. 
The data is sent to a server each minute and displayed along with other monitors on Google Maps.

Raspberry Pi with System Inputs:<br>

PM2.5 Air Particle Sensor<br>
PM 0.3--1.0 um<br>
PM 1.0--2.5 um<br>
PM 2.5—10.0 um<br>

BME680 Air Quality<br>
Temperature Degrees F<br>
Pressure Pa<br>
Relative Humidity  Percent<br>
Resistance Ohms<br>
Quality Percent function of Resistance, and Relative Humidity)<br>
VOCs PPM (Function of Quality)<br>

Samson USB Microphone<br>
Sound maximum dB<br>
Freq at maximum dB Hz<br> 
