# coding=utf-8
from __future__ import absolute_import, print_function

import flask

import octoprint.plugin
from octoprint.access.permissions import Permissions
from octoprint.util import fqfn

from . import Connection

#import sys
#import threading
#import time
#import traceback
# from time import sleep, time


class SiocontrolPlugin(
    octoprint.plugin.SettingsPlugin,
    octoprint.plugin.AssetPlugin,
    octoprint.plugin.TemplatePlugin,
    octoprint.plugin.StartupPlugin,
    octoprint.plugin.SimpleApiPlugin,
    octoprint.plugin.RestartNeedingPlugin,
):
    def __init__(self):
        self.config = dict()
        self._sub_plugins = dict()
        self.DeviceCompatibleVersion = "SIOPlugin 0.1.1"
        self.IOCurrent = None
        self._lastIOCurent = None
        self.IOStatus = "Ready"
        self.IOSWarnings = ""
        self.conn = None  # Connection.Connection(self)
        return

    def get_template_vars(self):
        avalIOSI = [
            "500",
            "1000",
            "1500",
            "2000",
            "3000",
            "4000",
            "5000",
            "6000",
            "7000",
            "8000",
            "9000",
            "10000",
        ]
        # self._settings.set(["IOPorts"], self.conn.serialList())
        avalPorts = self.get_AvaliblePorts()
        self._settings.set(["IOPorts"], avalPorts)
        self._settings.set(["IOCounts"], self.getCounts())

        self.has_SIOC = False
        available_plugins = []
        for k in list(self._sub_plugins.keys()):
            available_plugins.append(dict(pluginIdentifier=k, displayName=self._plugin_manager.plugins[k].name))
            if k == "":  # I think this should be != but leaving for now. also maybe the bool has_SIOC should be has_SubPlugIn
                self.has_SIOC = True
        return {
            "availablePlugins": available_plugins,
            "hasSIOC": self.has_SIOC,
            "PSUIOPoint": self._settings.get(["PSUIOPoint"]),
            "ESTIOPoint": self._settings.get(["ESTIOPoint"]),
            "EnableESTIOPoint": self._settings.get(["EnableESTIOPoint"]),
            "EnablePSUIOPoint": self._settings.get(["EnablePSUIOPoint"]),
            "IOSI": self._settings.get(["IOSI"]),
            "IOPort": self._settings.get(["IOPort"]),
            "IOPorts": self._settings.get(["IOPorts"]),
            "IOBaudRate": self._settings.get(["IOBaudRate"]),
            "IOBaudRates": self._settings.get(["IOBaudRates"]),
            "IOSIs": avalIOSI,
            "FRSIOPoint": self._settings.get(["FRSIOPoint"]),
            "EnableFRSIOPoint": self._settings.get(["EnableFRSIOPoint"]),
            "IOCounts": self._settings.get(["IOCounts"]),
            "sio_configurations": self._settings.get(["sio_configurations"]),
            "IOStatusMessage": self.IOStatus,
            "IOSWarnings": self.IOSWarnings,
        }

    def get_template_configs(self):
        return [
            dict(
                type="settings",
                custom_bindings=True,
                template="siocontrol_settings.jinja2",
            ),
            dict(
                type="sidebar",
                custom_bindings=True,
                template="siocontrol_sidebar.jinja2",
                icon="map-signs",
            ),
        ]

    def get_settings_defaults(self):
        return dict(
            sio_configurations=[],
            PSUIOPoint="0",
            EnablePSUIOPoint=False,
            InvertPSUIOPoint=False,
            ESTIOPoint="0",
            EnableESTIOPoint=False,
            InvertESTIOPoint=False,
            FRSIOPoint="0",
            InvertFRSIOPoint=False,
            EnableFRSIOPoint=False,
            IOSI=3000,
            IOPort="",
            IOBaudRate="115200",
            IOBaudRates=["74880", "115200", "230400", "38400", "19200", "9600"],
            IOPorts=[],
            IOCounts=[],
            IOStatusMessage="Unknown Status",
            IOSWarnings="",
        )

    def on_settings_initialized(self):
        self.reload_settings()
        self.clean_Settings()
        return super().on_settings_initialized()

    def clean_Settings(self):
        # do what is needed to make sure old settings will stay working on an update.
        upDatedConfigs = []
        # add Nav Attribute to IO configs

        for configuration in self._settings.get(["sio_configurations"]):
            try:
                #needsnav  = 'on_nav' in configuration

                if 'on_side' not in configuration:
                    configuration['on_side'] = True  # defalt to show all on the side

                if 'on_nav' not in configuration:
                    configuration['on_nav'] = False

                #"active_mode": configuration["active_mode"],
                #"default_state": configuration["default_state"],
                #"icon": configuration["icon"],
                #"name": configuration["name"],
                #"on_nav": False,
                #"on_side": True,
                #"pin": configuration["pin"],
                upDatedConfigs.append(configuration)
            except Exception:
                self._logger.exception(
                    "Error Configuration update. Item {} caused an error while checking. You settins maybe lost or you may have to resave them to use new features.".format(
                        configuration['name']
                    ))
                pass
        # update the settings to have the new values into the future.
        self._settings.set(["sio_configurations"], upDatedConfigs)

    def reload_settings(self):
        for k, v in self.get_settings_defaults().items():
            if type(v) is str:
                v = self._settings.get([k])
            elif type(v) is int:
                v = self._settings.get_int([k])
            elif type(v) is float:
                v = self._settings.get_float([k])
            elif type(v) is bool:
                v = self._settings.get_boolean([k])

    def setStartUpIO(self):
        # Need to workout Non blocking thread with delay or other way to
        #  handle the comms to the MC better at startup.
        # Right now this will just not work for some Microcontrollers.
        # Due to the fact that the act of connecting causes it to reset.
        # So it is rebooting while these instructions are sent.
        # 2023-5-19 I this is is mostly worked out now. With the way the resend of VC works.

        self._logger.info("Setting initial State for Outputs")

        for configuration in self._settings.get(["sio_configurations"]):

            pin = int(configuration["pin"])

            if pin != -1:

                if configuration["active_mode"] == "active_out_low":
                    if configuration["default_state"] == "default_on":
                        self.conn.send(f"IO {pin} 0")
                    elif configuration["default_state"] == "default_off":
                        self.conn.send(f"IO {pin} 1")
                elif configuration["active_mode"] == "active_out_high":
                    if configuration["default_state"] == "default_on":
                        self.conn.send(f"IO {pin} 1")
                    elif configuration["default_state"] == "default_off":
                        self.conn.send(f"IO {pin} 0")

            self._logger.info(
                "Configured SIO{}: {},{} ({}),{},{}".format(
                    configuration["pin"],
                    configuration["active_mode"],
                    configuration["default_state"],
                    configuration["name"],
                    configuration["on_nav"],
                    configuration["on_side"],
                )
            )

        return

    def on_after_startup(self, *args, **kwargs):

        # connect to IO
        self.conn = Connection.Connection(self)
        self.conn.connect()

        if self.conn.is_connected():
            self._logger.info("Connected to Serial IO")
            self.IOStatus = "Connected"
            self.IOSWarnings = " "
            self.conn.send("SI " + self._settings.get(["IOSI"]))
            self.setStartUpIO()
        else:
            self.IOStatus = "Could not connect SIO"
            self._logger.error("Could not connect SIO")
            self._logger.info("IOSI:" + str(self._settings.get(["IOSI"])))
            self._logger.info("IOPort:" + str(self._settings.get(["IOPort"])))
            self._logger.info("IOPorts:" + str(self._settings.get(["IOPorts"])))
            self._logger.info("IOBaudRate:" + str(self._settings.get(["IOBaudRate"])))
            self._logger.info("IOBaudRates" + str(self._settings.get(["IOBaudRates"])))

        psucontrol_helpers = self._plugin_manager.get_helpers("psucontrol")
        if not psucontrol_helpers:
            self._logger.warning("PSUControl Plugin not found.")
            return

        elif "register_plugin" not in psucontrol_helpers.keys():
            self._logger.warning(
                "The version of PSUControl that is installed does not support plugin registration."
            )

            if self._settings.get(["EnablePSUIOPoint"]):
                self.IOSWarnings = "PSUControl version mismatch"
            return
        else:
            psucontrol_helpers["register_plugin"](self)
            self._logger.info("Regester as Sub Plugin to PSUControl")

    def get_AvaliblePorts(self):
        avalPorts = self.conn.serialList()
        try:
            if str(self._settings.get(["IOPort"])) != "None":
                commPort = str(self._settings.get(["IOPort"]))
                if avalPorts.index(commPort) < 0:
                    avalPorts.append(str(self._settings.get(["IOPort"])))
        except Exception:
            self._logger.warning(
                "Looks like No Comm port was selected yet. List of avalible ports may need to be refreshed."
            )

        return avalPorts

    def get_api_commands(self):
        return dict(
            turnSioOn=["id"],
            turnSioOff=["id"],
            toggelSio=["pin"],
            getSioState=["id"],
            getPorts="",
            getIOCounts="",
            getStatusMessage="",
            connectIO=["port", "baudRate", "si"],
        )

    def on_api_command(self, command, data):

        if command == "connectIO":
            self._settings.set(["IOSI"], data["si"])
            self._settings.set(["IOBaudRate"], data["baudRate"])
            self._settings.set(["IOPort"], data["port"])

            if self.conn.is_connected():
                self.conn.stopCommThreads()
                self.conn.disconnect()

            self.conn.connect()
            if self.conn.is_connected():
                self._logger.info("Connected")
                self.conn.send("SI " + self._settings.get(["IOSI"]))
            else:
                self._logger.error("Could not connect to SIO.")

            return flask.jsonify(self.IOStatus)

        if command == "getStatusMessage":
            return flask.jsonify(self.IOStatus, self.IOSWarnings)

        if command == "getPorts":
            avalPorts = self.get_AvaliblePorts()
            self._settings.set(["IOPorts"], avalPorts)
            return flask.jsonify(avalPorts)

        if command == "getIOCounts":
            return flask.jsonify(self.getCounts())

        if command == "toggelSio":
            pin = int(data["pin"])

            if pin >= len(self.IOCurrent) or pin < 0:
                self._logger.info(
                    "Toggle command ignored, Pin assignment out of range: {}".format(pin)
                )
                return

            if Permissions.CONTROL.can() and pin >= 0:
                if self.conn.is_connected():
                    self._logger.debug("Toggle SIO{}".format(pin))
                    newState = "0" if self.IOCurrent[pin] == "1" else "1"
                    self.conn.send(f"IO {pin} {newState}")
                    return flask.jsonify(f"{pin}: {newState}")

                else:
                    self._logger.info(
                        "Not connected ignored IO command on Pin{}".format(pin)
                    )

        else:
            configuration = self._settings.get(["sio_configurations"])[int(data["id"])]
            pin = int(configuration["pin"])

            if pin < len(self.IOCurrent):
                if command == "getSioState":
                    if pin <= 0:
                        return flask.jsonify("")
                    elif configuration["active_mode"] == "active_out_low":
                        rtnJ = flask.jsonify(
                            "on" if self.IOCurrent[pin] == "1" else "off"
                        )
                        return rtnJ
                    elif configuration["active_mode"] == "active_out_high":
                        rtnJ = flask.jsonify(
                            "off" if self.IOCurrent[pin] == "1" else "on"
                        )
                        return rtnJ

                elif command == "turnSioOn":
                    if Permissions.CONTROL.can() and pin >= 0:
                        if self.conn.is_connected():
                            self._logger.debug(
                                "Turned on SIO{}".format(configuration["pin"])
                            )

                            if configuration["active_mode"] == "active_out_low":
                                self.conn.send(f"IO {pin} 0")

                                if self.IOCurrent[pin] == "0":
                                    return flask.jsonify(f"{pin}: on")
                                else:
                                    return flask.jsonify(f"{pin}: off")

                            elif configuration["active_mode"] == "active_out_high":
                                self.conn.send(f"IO {pin} 1")

                                if self.IOCurrent[pin] == "1":
                                    return flask.jsonify(f"{pin}: on")
                                else:
                                    return flask.jsonify(f"{pin}: off")

                        else:
                            self._logger.info(
                                "Not connected ignored IO command on Pin{}".format(pin)
                            )

                elif command == "turnSioOff":
                    if Permissions.CONTROL.can() and pin >= 0:
                        if self.conn.is_connected():
                            self._logger.debug(
                                "Turned off SIO{}".format(configuration["pin"])
                            )
                            if configuration["active_mode"] == "active_out_low":
                                self.conn.send(f"IO {pin} 1")
                                if self.IOCurrent[pin] == "1":
                                    return flask.jsonify(f"{pin}: off")
                                else:
                                    return flask.jsonify(f"{pin}: on")

                            elif configuration["active_mode"] == "active_out_high":
                                self.conn.send(f"IO {pin} 0")
                                if self.IOCurrent[pin] == "0":
                                    return flask.jsonify(f"{pin}: off")
                                else:
                                    return flask.jsonify(f"{pin}: on")

                        else:
                            self._logger.info(
                                "Not connected ignored IO command on Pin{}".format(pin)
                            )
            else:
                self.IOSWarnings = "Pin [{}] out of range.".format(pin)
                self._logger.info("Pin [{}] outof range.".format(pin))
                self._logger.info(
                    "Max Pin assignment is [{}]".format(len(self.IOCurrent) - 1)
                )

    def on_api_get(self, request):
        return flask.jsonify(self.get_sio_Configuration_status())

    def getCounts(self):
        if self.conn.IOCount != 0:
            counts = [str(k) for k in range(0, self.conn.IOCount)]
        else:
            counts = [str(k) for k in range(0, 99)]
        return counts

    def on_settings_save(self, data):

        octoprint.plugin.SettingsPlugin.on_settings_save(self, data)

        # should do direct IO configuration sends here.

        comChanged = True
        if "IOPort" in data:
            self._settings.set(["IOPort"], data["IOPort"])
            comChanged = True

        if "IOBaudRate" in data:
            self._settings.set(["IOBaudRate"], data["IOBaudRate"])
            comChanged = True

        if comChanged:
            if self.conn.is_connected():
                self.conn.stopCommThreads()
                self.conn.disconnect()

            self.conn.connect()
            if self.conn.is_connected():
                self._logger.info("Connected")
            else:
                self._logger.error("Could not connect to SIO.")

        if "IOSI" in data:
            self._settings.set(["IOSI"], data["IOSI"])

        if "PSUIOPoint" in data:
            self._settings.set(["PSUIOPoint"], data["PSUIOPoint"])

        if self.conn.is_connected():
            self.conn.Update_IOSI(self._settings.get(["IOSI"]))

        self.reload_settings()

        return

    def SetDIOPoint(self,pin,action):
        #actions ["on","off"]
        if pin != -1:
            for configuration in self._settings.get(["sio_configurations"]):
                cpin = int(configuration["pin"])
                if pin == cpin:
                    if configuration["active_mode"] == "active_out_low":
                        if action == "on":
                            self.conn.send(f"IO {pin} 0")
                        elif action == "off":
                            self.conn.send(f"IO {pin} 1")
                        else:
                            self._logger.info("Can't set Digital IO pin {} State to {}. Action is invalid".format(configuration["pin"],action))

                    elif configuration["active_mode"] == "active_out_high":
                        if action == "on":
                            self.conn.send(f"IO {pin} 1")
                        elif action == "off":
                            self.conn.send(f"IO {pin} 0")
                        else:
                            self._logger.info("Can't set Digital IO pin {} State to {}. Action is invalid".format(configuration["pin"],action))
        else:
            self._logger.info("Can't set Digital IO pin {} State to {}. Pin number is out of range".format(configuration["pin"],action,))
        return

    def turn_psu_on(self):
        if self._settings.get(["EnablePSUIOPoint"]):
            psupoint = self._settings.get(["PSUIOPoint"])
            if self._settings.get(["InvertPSUIOPoint"]):
                self.conn.send(f"IO {psupoint} 0")
            else:
                self.conn.send(f"IO {psupoint} 1")
            self._logger.debug("******Switching PSU On: sending command to IO******")
        else:
            self._logger.debug(
                "******Turn On PSU requested: PSU Integration is not Endabled.******"
            )

    def turn_psu_off(self):
        if self._settings.get(["EnablePSUIOPoint"]):
            psupoint = self._settings.get(["PSUIOPoint"])
            if self._settings.get(["InvertPSUIOPoint"]):
                self.conn.send(f"IO {psupoint} 1")
            else:
                self.conn.send(f"IO {psupoint} 0")
            self._logger.debug("******Switching PSU Off: sending command to IO******")
        else:
            self._logger.debug(
                "******Turn Off PSU requested: PSU Integration is not Endabled.******"
            )

    def get_psu_state(self):
        rtn = None

        if self.IOCurrent is None:
            return False
        if len(self.IOCurrent) >= int(self._settings.get(["PSUIOPoint"])):

            psuRelayState = self.IOCurrent[int(self._settings.get(["PSUIOPoint"]))]
            self._logger.debug("******Reporting PSU Current State:" + psuRelayState)

            if self._settings.get(["InvertPSUIOPoint"]):
                rtn = self.IOCurrent[int(self._settings.get(["PSUIOPoint"]))] == "0"
            else:
                rtn = self.IOCurrent[int(self._settings.get(["PSUIOPoint"]))] == "1"

            return rtn
        else:
            self._logger.debug(
                "Cant get PSU State due to lack of reporting from SIO Control"
            )

    ##~~ AssetPlugin mixin

    def get_assets(self):
        self._logger.debug("SIOC Running get_assets")
        return dict(
            css=["css/SIOControl.css", "css/fontawesome-iconpicker.min.css"],
            js=["js/siocontrol.js", "js/fontawesome-iconpicker.min.js"],
        )

    ##~~ Sub Plugin Hooks
    def _get_plugin_key(self, implementation):
        for k, v in self._plugin_manager.plugin_implementations.items():
            if v == implementation:
                return k

    def register_plugin(self, implementation):
        k = self._get_plugin_key(implementation)

        self._logger.debug("Registering plugin - {} as SIO Control Sub plugin".format(k))

        if k not in self._sub_plugins:
            self._logger.info("Registered plugin - {} as SIO Control Sub plugin".format(k))
            self._sub_plugins[k] = implementation

    # Send serial data recieved for use in subPlugins.
    def serialRecievequeue(self,line):
        for k, v in self._sub_plugins.items():
            if hasattr(v,'hook_sio_serial_stream'):
                callback = self._sub_plugins[k].hook_sio_serial_stream
                try:
                    callback(line)
                except Exception:
                    self._logger.exception("Error while executing sub Plugin callback method {}".format(callback),extra={"callback":fqfn(callback)},)

        return line

    # Can be used to send arbatrary command to the SIO Control module. Commands are entered into the send Queue.
    def send_sio_command(self,command):
        self.conn.send(command)

    def broadCastStateToSubPlugins(self):
        #update all sub plugins with state array for digital IO points when the state changes.
        if self.IOCurrent == self._lastIOCurent:
            return

        self._lastIOCurrent = self.IOCurrent
        for k, v in self._sub_plugins.items():
            if hasattr(v,'sioStateChanged'):
                callback = self._sub_plugins[k].sioStateChanged
                try:
                    IOStatus = self.get_sio_digital_status()
                    callback(self.IOCurrent,IOStatus)
                except Exception:
                    self._logger.exception("Error while executing sub Plugin callback method {}".format(callback),extra={"callback":fqfn(callback)},)
                    #return  dont drop out.. this might be just one of many sub plugins looking for info.

    def set_sio_digital_state(self,point,action):
        #actions ["on,off"]
        self.SetDIOPoint(point,action)
        return self.IOCurrent

    def get_sio_digital_state(self):
        return self.IOCurrent

    def get_sio_digital_status(self):
        conStatus = self.get_sio_Configuration_status()
        status = []

        for _idx, _x in enumerate(self.IOCurrent):
            status.append("na")
        try:

            for idx,configuration in enumerate(self._settings.get(["sio_configurations"])):
                pin = int(configuration["pin"])
                status[pin] = conStatus[idx]
                self._logger.debug("Pin#{} set to \"{}\"".format(idx,status[pin]))

        except Exception:
            self._logger.exception("Error while getting digital status ConStatus{} IOCurrent{}".format(conStatus,self.IOCurrent))

        return status

    # Important to note that this is indexed in the order of the Configurations for the UI. Not in the pin IO Order.
    # It will also only return items that corospond to the sio_configurations. So if you only configured 2 points, you will
    # only get 2 items in the array.
    # to get the status for the configured pins, use get_sio_digital_status
    def get_sio_Configuration_status(self):
        status = []
        for configuration in self._settings.get(["sio_configurations"]):
            if configuration["pin"] is not None:
                pin = int(configuration["pin"])

                if self.IOCurrent is not None and pin < len(self.IOCurrent):
                    if pin < 0:
                        status.append("")
                    elif configuration["active_mode"] == "active_in_low":
                        pstatus = "off" if self.IOCurrent[pin] == "1" else "on"
                        status.append(pstatus)
                    elif configuration["active_mode"] == "active_in_high":
                        pstatus = "on" if self.IOCurrent[pin] == "1" else "off"
                        status.append(pstatus)
                    elif configuration["active_mode"] == "active_out_low":
                        pstatus = "off" if self.IOCurrent[pin] == "1" else "on"
                        status.append(pstatus)
                    elif configuration["active_mode"] == "active_out_high":
                        pstatus = "on" if self.IOCurrent[pin] == "1" else "off"
                        status.append(pstatus)
                else:
                    if self.conn is not None and self.conn.is_connected() is True:
                        self._logger.debug("Pin number assigned to IO control {} maybe out of range.".format(pin))

                    status.append("off")
            else:
                status.append("off")

        return status
    ##~~ Softwareupdate hook

    def get_update_information(self):
        # Define the configuration for your plugin to use with the Software Update
        # Plugin here. See https://docs.octoprint.org/en/master/bundledplugins/softwareupdate.html
        # for details.
        return {
            "siocontrol": {
                "displayName": "SIO Control",
                "displayVersion": self._plugin_version,
                # version check: github repository
                "type": "github_release",
                "user": "jcassel",
                "repo": "OctoPrint-Siocontrol",
                "current": self._plugin_version,
                # update method: pip
                "pip": "https://github.com/jcassel/OctoPrint-Siocontrol/archive/{target_version}.zip",
            }
        }


# If you want your plugin to be registered within OctoPrint under a different
# name than what you defined in setup.py
# ("OctoPrint-PluginSkeleton"), you may define that here. Same goes for the
# other metadata derived from setup.py that can be overwritten
# via __plugin_xyz__ control properties. See the documentation for that.
__plugin_name__ = "SIO Control"


# Set the Python version your plugin is compatible with below. Recommended
# is Python 3 only for all new plugins.
# OctoPrint 1.4.0 - 1.7.x run under both Python 3 and the end-of-life Python 2.
# OctoPrint 1.8.0 onwards only supports Python 3.
__plugin_pythoncompat__ = ">=3,<4"  # Only Python 3


def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = SiocontrolPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
    }

    global __plugin_helpers__
    __plugin_helpers__ = dict(
        set_sio_digital_state=__plugin_implementation__.set_sio_digital_state,
        get_sio_digital_state=__plugin_implementation__.get_sio_digital_state,
        send_sio_command=__plugin_implementation__.send_sio_command,
        register_plugin=__plugin_implementation__.register_plugin,

    )
