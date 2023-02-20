---
layout: plugin
id: siocontrol
title: SIO Control
description: Serial IO Control, Adds a sidebar with on/off buttons for controling of Outputs and monitoring of Inputs. Is also a Subplugin for integration with PSU control, incorperates EStop and simple Filament runout as physical inputs. Mainly serves as an alteritive if you are not using a Raspberry Pie or other device that can take advantage local IO. Requires a Microcotroler as the IO. See details below. 

authors: jcassel
license: AGPLv3
date: 2023-02-11
homepage: https://github.com/jcassel/OctoPrint-Siocontrol
source: https://github.com/jcassel/OctoPrint-Siocontrol
archive: https://github.com/jcassel/OctoPrint-Siocontrol/archive/master.zip

tags:
- sio
- serial io
- serial
- io
- gpio
- rpio
- pc
- linux
- gpiostatus
- pin
- pins
- atx
- control
- power
- estop
- psu
- psucontrol
- psucontrol subplugin
- gpiocontrol
- relay
- enclosure
- button
- filament
- usb
- serial
- rs232
- led


screenshots:
- url: /assets/img/plugins/siocontrol/SettingsExampleConnAndIntegratons.PNG
  alt: Settings Example Connection and Integratons
  caption: Settings and Integration
- url: /assets/img/plugins/siocontrol/SettingsExampleIOConfig.PNG
  alt: Settings Example IO Configuration
  caption: Settings for ad-hoc IO
- url: /assets/img/plugins/siocontrol/SideBarExample.PNG
  alt: Side bar example
  caption: Side bar view


featuredimage: /assets/img/plugins/siocontrol/SettingsExampleConnAndIntegratons.PNG
python: ">=3,<4"

---
# Serial IO Control
Method for adding IO to any OctoPrint instance. Uses a serial connection to a micro controller like the Arduino Mega, Nano, Esp8266/ESP32 over a direct wired serial connection. A basic alternitive to using GPIO/local IO on a Raspberry Pi like device. Could also be used with GPIO or RPIO on these devices. The number of IO and use case is programable at the firmware of the Micro controller. The serial protocal is simple and can be ported to just about any micro controller with ease. There are a several examples of firmware that can be used as is or adjusted to your needs. See [GitHub repository](https://github.com/jcassel/OctoPrint-Siocontrol) for a list and links to details. Additionally one could purchase and use several "off the shelf" control boards also listed at this plugin's home page.

## Setup

Install via the bundled [Plugin Manager](https://docs.octoprint.org/en/master/bundledplugins/pluginmanager.html)
or manually using this URL:

    https://github.com/jcassel/OctoPrint-Siocontrol/archive/master.zip


## Configuration
Configure the Serial comport details. 
- Port path(Linux) name:(Windows)
- Baudrate  
- Sensing/reporting interval

Simple selections for integrations
- Enable and select IO point for PSU Control Sub Plugin.
- Enable and select IO point for physical EStop.
- Enable and select IO point for Filament runout sensor.

The number of IO Points is reported by the IO device firmware. In the [D1SerialIO firmware](https://github.com/jcassel/D1SerialIO) there are a total of 8 IO points. The [nanoSerialIO Firmware](https://github.com/jcassel/nanoSerialIO) has 20 digital points. All can configure each as either an input or an output. The OctoPrint-Serial IO Board I offer on Tindie has 2 relays and 6 other IO points that can be setup as either inputs or outputs. 

Add SIO configurations and they will apear on the side bar for interaction and monitoring:
- select icon using icon picker (or typing manually) for easy identification
- Type in a short name for the device connected to the IO Pin
- Type or select the pin number for your IO point. Note that the avalible numbers are based on the communication to the IO device. If you have 10 points, you should have 10 pins to select from.
- select if device an Input or an Output and what is its active state.
  - Out_HIGH means that this Pin is an output and its resting state is LOW. When turned on, it will go HIGH (To V+).
  - Out_LOW means that this Pin is an input and its resting state is HiGH. When it is turned on it will go LOW(To ground).
- select if device should be on or off by default after/on startup.(Only applies to Outputs)
  - Off would mean that no command will be sent to the IO after start up. 
  - On would cause a command to set the Pin to its active level after start up of OctoPrint.
-Note that Configuration of a Pin makes it accessable in the sideNav. It is ok if the pin is used by the other integrations like PSUCorol. Inputs and outputs not configured at the device level from within OctoPrint. Misconfiguring a Pin in the interface will not change the pins type in the controller. To set the pins IO type see the directions for that device. The official example firmware repositories all have some general instructions on how to set IO point types either in the device code or as part of the readme. 





Thank you to the developers of [GpoiControl(@catgiggle)](https://github.com/catgiggle/OctoPrint-GpioControl) and [PSUControl(kantlivelong)](https://github.com/kantlivelong/OctoPrint-PSUControl) for giving me a lot of insparation on how this looks and works. A lot of the initial code for this was directly pulled from GPIO Control as a starting point. 

