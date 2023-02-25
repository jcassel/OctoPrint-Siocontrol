# OctoPrint-Siocontrol
The Serial IO Control OctoPrint plugin, Adds a sidebar with on/off buttons for controling of Outputs and monitoring of Inputs. Is also a Subplugin for integration with PSU control, incorperates a physical EStop and simple Filament runout as sensor. Serves as an alteritive IO control for users that are not using a Raspberry Pie or other device that can take advantage local IO. Requires a Microcotroler as the IO. See details below.
![sidebar view](https://github.com/jcassel/OctoPrint-Siocontrol/blob/main/extras/SideBarExample.PNG)

With the Serial IO Control and an inexpensive Micro controller you can add Serial IO to any OctoPrint instance. Use a serial connection to a micro controller like the Arduino Mega, Nano, Esp8266/ESP32 over a direct wired serial connection. Use the micro controllers Digital IO from Octoprint. An alternitive to using GPIO/local IO on a Raspberry Pi like device. Specificly targed at users of Octoprint that have chosen to not use a Raspberry Pi. 

The number of IO and use case is configurable in the firmware of the micro controller. The serial protocal used is simple and can be ported to just about any micro controller with ease. There are several examples of firmware that can be used as is or adjusted to your needs. There are also several off the shelf IO board kits that can be purchased if you do not want to design and build one yourself.

- [Arduino shield](https://www.amazon.com/dp/B00DDEIW1Y): with 6 relay outputs and 6 digital inputs. Also requires an [Arduino UNO](https://www.amazon.com/Arduino-A000066-ARDUINO-UNO-R3/dp/B008GRTSV6). Example firmware:[Mega2560-SerialIO_PKA05IOShield](https://github.com/jcassel/Mega2560-SerialIO_PKA05IOShield)
- [CANADUINO PLC MEGA328](https://www.amazon.com/dp/B085F3YRK4) with 6 relay outputs and 4 digital inputs. Example firmware: [CanaduinoPLCSerialIO](https://github.com/jcassel/CanaduinoPLCSerialIO)
- [SerialIO Control board](https://www.tindie.com/products/jcsgotthis/iot-project-board-octoprint-siocontrol-board/) with 2 relay outputs, 6 digital configurable(in/out)puts. Example firmware:[D1SerialIO](https://github.com/jcassel/D1SerialIO)


## Setup

Install via the bundled [Plugin Manager](https://docs.octoprint.org/en/master/bundledplugins/pluginmanager.html)
or manually using this URL:

    https://github.com/jcassel/OctoPrint-Siocontrol/archive/master.zip

## Getting Started
Follow the [instructions on setting up the IO board of choice](#) first. Ensure you know what IO numbers are setup as Inputs and Outputs. Once ready continue on.


Before you plug in your IO device, you should ensure that you can connect to your printer. Make note of the port that your printer is on and set the Octoprint connection parameters for the port to the known port for your printer. Select the check box to "Save connection settings". This will ensure that Octorprint tries to connect to your printer directly based on the ports you set and not do an auto connect sequence which can often mistake the IO for the printer. Once you have that set, connect your IO device and follow the steps below to conigure. 

## Configuration
Configure the Serial Port Details. 
- Port Path(Linux) or Port Name(Windows)
- Baudrate (default firmeare is 115200)  
- Sensing/reporting interval (default is 3000ms (3 seconds))

![Connection and integrations](https://github.com/jcassel/OctoPrint-Siocontrol/blob/main/extras/SettingsExampleConnAndIntegratons.PNG)

Save these settings check in the lower left navigation pain. It should now say "Connected". If not you may not have put in the correct connection details. You can now reopen the SIO setting and assign the rest of the details as needed. 

Simple selections for integrations (Optional)
- Enable and select IO point for PSU Control Sub Plugin.
- Enable and select IO point for physical EStop.
- Enable and select IO point for Filament runout sensor.

![IO Configuration](https://github.com/jcassel/OctoPrint-Siocontrol/blob/main/extras/SettingsExampleIOConfig.PNG)


As you add SIO configurations they will apear on the side bar for interaction and monitoring:
- select icon using icon picker (or typing manually) for easy identification
- Type in a short name for the device connected to the IO Pin
- Type or select the pin number for your IO point. Note that the avalible numbers are based on the communication to the IO device. If you have 10 points, you should have 10 pins to select from.
- select if device an Input or an Output and what is its active state.
  - Out_HIGH means that this Pin is an output and its resting state is LOW. When turned on, it will go HIGH (To V+).
  - Out_LOW means that this Pin is an input and its resting state is HiGH. When it is turned on it will go LOW(To ground).
- select if device should be on or off by default after/on startup.(Only applies to Outputs)
  - Off would mean that no command will be sent to the IO after start up. 
  - On would cause a command to set the Pin to its active level after start up of OctoPrint.


### Note:
Configuration of a Pin makes it accessable in the sideNav. It is ok if the pin is used by the other integrations like PSUCorol. Inputs and outputs not configured at the device level from within OctoPrint. Misconfiguring a Pin in the interface will not change the pins type in the controller. To set the pins IO type see the directions for that device. The official example firmware repositories all have some general instructions on how to set IO point types either in the device code or as part of the readme. 

IO Point numbers and configurations must match the IO device firmware setup. In the [D1SerialIO firmware](https://github.com/jcassel/D1SerialIO) there are a total of 8 IO points. The [nanoSerialIO Firmware](https://github.com/jcassel/nanoSerialIO) has 20 digital points. All can configure each as either an input or an output. The OctoPrint-Serial IO Board I offer on Tindie has 2 relays and 6 other IO points that can be setup as either inputs or outputs. 




Thank you to the developers of [GpoiControl(@catgiggle)](https://github.com/catgiggle/OctoPrint-GpioControl) and [PSUControl(kantlivelong)](https://github.com/kantlivelong/OctoPrint-PSUControl) for giving me a lot of insparation on how this looks and works. A lot of the initial code for this was directly pulled from GPIO Control as a starting point. 

