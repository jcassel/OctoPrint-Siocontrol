---
layout: plugin
id: siocontrol
title: SIO Control
description: Serial IO Control that adds a sidebar with on/off buttons for controling outputs and monitoring of Inputs. Is a Subplugin for integration with PSU control, incorperates EStop and simple Filament runout as physical inputs. Alteritive if you are not using a Raspberry Pie or other device that can take advantage of GPIO. Requires a Microcotroler as the IO. See details below. 

authors: jcassel
license: AGPLv3
date: 2023-02-11
homepage: https://github.com/jcassel/OctoPrint-Siocontrol
source: https://github.com/jcassel/OctoPrint-Siocontrol
archive: https://github.com/jcassel/OctoPrint-Siocontrol/archive/master.zip

tags:
- gpio
- pc
- linux
- gpiostatus
- pin
- pins
- atx
- control
- io
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
- 232
- led


screenshots:
- url: /assets/img/plugins/SIOControl/SettingsExampleConnAndIntegratons.PNG
  alt: Settings Example Connection and Integratons
  caption: Settings and Integration
- url: /assets/img/plugins/SIOControl/SettingsExampleIOConfig.PNG
  alt: Settings Example IO Configuration
  caption: Settings for ad-hoc IO
- url: /assets/img/plugins/SIOControl/SideBarExample.PNG
  alt: Side bar example
  caption: Side bar view


featuredimage: /assets/img/plugins/SIOControl/SettingsExampleConnAndIntegratons.PNG
python: ">=3,<4"

---
# Serial IO Control
Alternitive to GPIO if you want to add some electronic/improvements to your printer. Works on Linux and Windows. 

## Setup

Install via the bundled [Plugin Manager](https://docs.octoprint.org/en/master/bundledplugins/pluginmanager.html)
or manually using this URL:

    https://github.com/jcassel/OctoPrint-Siocontrol/archive/master.zip

Used the power of an Arduino compatible micro controler to do the IO Part. 
The esp8266(Examples avalible) is used in the tutorial as the IO controller. This is a serial connection not wifi. Firmeare is easly adapted to run on many standard Arduino comparible devices. See [D1SerialIO firmware](https://github.com/jcassel/D1SerialIO) and information on how to make or buy a compatible IO Board. 

## Configuration
Configure the Serial comport details. 
- Port path(name)
- Baudrate  
- Sensing/reporting interval

Simple selections for integrations
- Enable and select IO point for PSU Control Sub Plugin.
- Enable and select IO point for physical EStop.
- Enable and select IO point for Filament runout sensor.

The number of IO Points is reported by the IO device firmware. In the [D1SerialIO firmware](https://github.com/jcassel/D1SerialIO) there are a total of 8 IO points.
You can configure each as either an input or an output. The OctoPrint-Serial IO Board has 2 relays and 6 other IO points that can be setup as either inputs or outputs. 

Just add correct GPIO configuration:
- select icon using icon picker (or typing manually) for better identification
- type name for your device connected to GPIO
- type pin number according to BCM numeration - for more details please [visit this page](https://pinout.xyz/)
- select if device is driven for low or high state of GPIO
    - _active high_ means that device is **on for high state** of GPIO and **off for low state**
    - _active low_ means that device is **on for low state** of GPIO and **off for high state**
- select if device should be on or off by default eg. after startup

