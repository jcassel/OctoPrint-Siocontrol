# OctoPrint-Siocontrol
The Serial IO Control OctoPrint plugin, Adds a sidebar with on/off buttons for controlling of Outputs and monitoring of Inputs. Is also a SubPlugin for integration with PSU control, incorporates a physical EStop and simple Filament runout as sensor. Serves as an alterative IO control for users that are not using a Raspberry Pie or other device that can take advantage local IO. Requires a Microcontroller as the IO. See details below.
![sidebar view](https://github.com/jcassel/OctoPrint-Siocontrol/blob/main/extras/SideBarExample.PNG)

With the Serial IO Control and an inexpensive Micro controller you can add Serial IO to any OctoPrint instance. Use a serial connection to a micro controller like the Arduino Mega, Nano, Esp8266/ESP32 over a direct wired serial connection. Use the micro controllers Digital IO from Octoprint. An alternative to using GPIO/local IO on a Raspberry Pi like device. Specifically target at users of Octoprint that have chosen to not use a Raspberry Pi. 

Some hardware options are listed at the end of this readme.

## Setup

Install via the bundled [Plugin Manager](https://docs.octoprint.org/en/master/bundledplugins/pluginmanager.html)
or manually using this URL:

    https://github.com/jcassel/OctoPrint-Siocontrol/archive/master.zip

## Getting Started
Follow the [instructions on setting up the IO board of choice](#) first. Ensure you know what IO numbers are setup as Inputs and Outputs. Once ready continue on.


Before you plug in your IO device, you should ensure that you can connect to your printer. Make note of the port that your printer is on and set the Octoprint connection parameters for the port to the known port for your printer. Select the check box to "Save connection settings". This will ensure that OctoPrint tries to connect to your printer directly based on the ports you set and not do an auto connect sequence which can often mistake the IO for the printer. Once you have that set, connect your IO device and follow the steps below to configure. 

## Configuration
Configure the Serial Port Details. 
- Port Path(Linux) or Port Name(Windows)
- Baud rate (default firmware is 115200)  
- Sensing/reporting interval (default is 3000ms (3 seconds))

![Connection and integrations](https://github.com/jcassel/OctoPrint-Siocontrol/blob/main/extras/SettingsExampleConnAndIntegratons.PNG)

Save these settings check in the lower left navigation pain. It should now say "Connected". If not you may not have put in the correct connection details. You can now reopen the SIO setting and assign the rest of the details as needed. 

Simple selections for integrations (Optional)
- Enable and select IO point for PSU Control Sub Plugin.
- Enable and select IO point for physical EStop.
- Enable and select IO point for Filament runout sensor.

![IO Configuration](https://github.com/jcassel/OctoPrint-Siocontrol/blob/main/extras/SettingsExampleIOConfig.PNG)


As you add SIO configurations they will appear on the side bar for interaction and monitoring:
- select icon using icon picker (or typing manually) for easy identification
- Type in a short name for the device connected to the IO Pin
- Type or select the pin number for your IO point. Note that the available numbers are based on the communication to the IO device. If you have 10 points, you should have 10 pins to select from.
- select if device an Input or an Output and what is its active state.
  - Out_HIGH means that this Pin is an output and its resting state is LOW. When turned on, it will go HIGH (To V+).
  - Out_LOW means that this Pin is an input and its resting state is HiGH. When it is turned on it will go LOW(To ground).
- select if device should be on or off by default after/on startup.(Only applies to Outputs)
  - Off would mean that no command will be sent to the IO after start up. 
  - On would cause a command to set the Pin to its active level after start up of OctoPrint.


### Note:
Configuration of a Pin makes it accessible in the sideNav. It is ok if the pin is used by the other integrations like PSUCorol. Inputs and outputs not configured at the device level from within OctoPrint. Misconfiguring a Pin in the interface will not change the pins type in the controller. To set the pins IO type see the directions for that device. The official example firmware repositories all have some general instructions on how to set IO point types either in the device code or as part of the readme. 

IO Point numbers and configurations must match the IO device firmware setup. In the [D1SerialIO firmware](https://github.com/jcassel/D1SerialIO) there are a total of 8 IO points. The [nanoSerialIO Firmware](https://github.com/jcassel/nanoSerialIO) has 20 digital points. All can configure each as either an input or an output. The OctoPrint-Serial IO Board I offer on Tindie has 2 relays and 6 other IO points that can be setup as either inputs or outputs. 


## SIO Serial Commands 

All commands must end with a new line character (\n) If the command is recognized as a valid command the device will respond with an "OK" as an Ack. if it is not recognized, it will return an error in the format of: if command "AA" is sent to the device.A return code of: "ERROR: Unrecognized command[AA]\n" will be sent.

- BIO Begin AutoReporting IO status (only needed if EIO has been called.) 

- EIO Pause/End IO Status Autoreporting. This setting is not maintained through restarts of the device.

- IC returns the number of IO points being monitored. 

- debug [0/1] turns on[1] or off[0] debug output. Should not be used while connected to Octoprint SIOControl. This setting is not maintained through restarts of the device.

- CIO [io pattern] The [io pattern]  is an string of integers as a single value. For example: 0000111111 (this sets the first 4 io points to inputs and the last 6 to output.) There are 4 posible values that can be used for each type. 0=input, 1=output, 2 input_Pullup, 3 input_pulldown, Output_open_drain. Not all devices support all of the types listed. 0-2 are supported in most cases. This setting is not maintained through restarts of the device unless settings are stored using SIO command.

- SIO Stores current IO point type settings to local storage. This causes the current IO point types to be maintained through restarts of the device.

- IOT outputs the current IO Point types pattern

- IO [#] [0/1] Sets an IO point {#:position in IO pattern] to a logic level [0:low] [1:HIGH]. Example: "IO 9 1" will set the io point 9 to High 

- SI [500-4,294,967,295]  .5 seconds to ~1,193 hours realistically you would want this setting to be no less than 10,000 or 10 seconds to ensure generally acceptable feedback on changes made to the IO.
##
## Hardware options
The number of IO and use case is configurable in the firmware of the micro controller. The serial protocol used is simple and can be ported to just about any micro controller with ease. There are several examples of firmware that can be used as is or adjusted to your needs. There are also several off the shelf IO board kits that can be purchased if you do not want to design and build one yourself.

- [ESP32 2 Channel Relay board](https://www.amazon.com/dp/B0B8J9SNB5?psc=1&ref=ppx_yo2ov_dt_b_product_details) is a good option. This is my board of choice. Its has good isolation for the relays so you should not have any issues with switching mains power though these. It also leaves a lot of room for expansion.  I have some other related projects coming for this board as well. This is one of the boards I will be offering on [Tindie.com](https://www.tindie.com) in the near future. 
- [CANADUINO PLC MEGA328](https://www.amazon.com/dp/B085F3YRK4) with 6 relay outputs and 4 digital inputs. Example firmware: [CanaduinoPLCSerialIO](https://github.com/jcassel/CanaduinoPLCSerialIO). This board is a great option having both inputs and outputs but also does not come assembled. Meaning it requires a lot of soldering so be ready for that. 
- [SerialIO Control board] using an ESP8266 DIY board. Example firmware:[D1SerialIO](https://github.com/jcassel/D1SerialIO) 

- I also have some options coming soon through [Tindie.com](https://www.tindie.com). Check back here for future details. 

Additional options that will work but have some drawbacks. 
- [Arduino shield](https://www.amazon.com/dp/B00DDEIW1Y): with 6 relay outputs and 6 digital inputs. Also requires an [Arduino UNO](https://www.amazon.com/Arduino-A000066-ARDUINO-UNO-R3/dp/B008GRTSV6). Example firmware:[Mega2560-SerialIO_PKA05IOShield](https://github.com/jcassel/Mega2560-SerialIO_PKA05IOShield) 
	###### [I don't really recommend this as the terminals are very small. You likely also do not want to put mains power through the relays on this board. You should add a secondary mains power capable  relay to use with this. ]
##


## Recognition of reference works
Thank you to the other plugin developers doing great work in this space. 
- [GpoiControl(@catgiggle)](https://github.com/catgiggle/OctoPrint-GpioControl) A lot of the initial code for this was directly pulled from GPIO Control as a starting point. 
  
- [PSUControl(kantlivelong)](https://github.com/kantlivelong/OctoPrint-PSUControl) A well known and well used bit of code that I knew I could rely on as a good example of what to do.
  
- [jneilliii](https://github.com/jneilliii) so many great Plugins. The BedLevelVisualizer specifically was very helpful in working out how to deal with core ViewModels. 

