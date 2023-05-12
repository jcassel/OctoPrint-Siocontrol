# coding=utf-8
from __future__ import absolute_import, print_function

import flask

import octoprint.plugin
from octoprint.access.permissions import Permissions

from . import Connection

# from time import sleep, time


### (Don't forget to remove me)
# This is a basic skeleton for your plugin's __init__.py. You probably want to adjust the class name of your plugin
# as well as the plugin mixins it's subclassing from. This is really just a basic skeleton to get you started,
# defining your plugin as a template plugin, settings and asset plugin. Feel free to add or remove mixins
# as necessary.
#
# Take a look at the documentation on what other plugin mixins are available.


class SiocontrolPlugin(
    octoprint.plugin.SettingsPlugin,
    octoprint.plugin.AssetPlugin,
    octoprint.plugin.TemplatePlugin,
    octoprint.plugin.StartupPlugin,
    octoprint.plugin.SimpleApiPlugin,
    octoprint.plugin.RestartNeedingPlugin,
):
    def __init__(self):
        # self.config = dict()
        self.DeviceCompatibleVersion = "SIOPlugin 0.1.1"
        self.IOCurrent = None
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
        self._settings.set(["IOPorts"], self.conn.serialList())
        self._settings.set(["IOCounts"], self.getCounts())

        return {
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
        return super().on_settings_initialized()

    def reload_settings(self):
        for k, v in self.get_settings_defaults().items():
            if type(v) == str:
                v = self._settings.get([k])
            elif type(v) == int:
                v = self._settings.get_int([k])
            elif type(v) == float:
                v = self._settings.get_float([k])
            elif type(v) == bool:
                v = self._settings.get_boolean([k])

    def setStartUpIO(self):
        # Need to workout Non blocking thread with delay or other way to handle the comms to the MC better at startup.
        # Right now this will just not work for some Microcontrollers.
        # Due to the fact that the act of connecting causes it to reset.
        # So it is rebooting while these instructions are sent.

        self._logger.info("Setting initial State for Outputs")
        for configuration in self._settings.get(["sio_configurations"]):
            self._logger.info(
                "Configured SIO{}: {},{} ({})".format(
                    configuration["pin"],
                    configuration["active_mode"],
                    configuration["default_state"],
                    configuration["name"],
                )
            )

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
            self.IOStatus = "Could not connect Serial IO"
            self._logger.error("Could not connect Serial IO")
            self._logger.info("IOSI:" + str(self._settings.get(["IOSI"])))
            self._logger.info("IOPort:" + str(self._settings.get(["IOPort"])))
            self._logger.info("IOPorts:" + str(self._settings.get(["IOPorts"])))
            self._logger.info("IOBaudRate:" + str(self._settings.get(["IOBaudRate"])))
            self._logger.info("IOBaudRates" + str(self._settings.get(["IOBaudRates"])))

        psucontrol_helpers = self._plugin_manager.get_helpers("psucontrol")
        if not psucontrol_helpers or "register_plugin" not in psucontrol_helpers.keys():
            self._logger.warning(
                "The version of PSUControl that is installed does not support plugin registration."
            )
            self.IOSWarnings = "PSUControl version mistmatch"
            return
        else:
            psucontrol_helpers["register_plugin"](self)
            self._logger.info("Regester as Sub Plugin to PSUControl")

    def get_api_commands(self):
        return dict(
            turnSioOn=["id"],
            turnSioOff=["id"],
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
            avalPorts = self.conn.serialList()
            self._settings.set(["IOPorts"], avalPorts)
            return flask.jsonify(avalPorts)

        if command == "getIOCounts":
            return flask.jsonify(self.getCounts())

        configuration = self._settings.get(["sio_configurations"])[int(data["id"])]
        pin = int(configuration["pin"])
        if pin < len(self.IOCurrent):
            if command == "getSioState":
                if pin <= 0:
                    return flask.jsonify("")
                elif configuration["active_mode"] == "active_out_low":
                    rtnJ = flask.jsonify("on" if self.IOCurrent[pin] == "1" else "off")
                    return rtnJ
                elif configuration["active_mode"] == "active_out_high":
                    rtnJ = flask.jsonify("off" if self.IOCurrent[pin] == "1" else "on")
                    return rtnJ

            elif command == "turnSioOn":
                if Permissions.CONTROL.can() and pin >= 0:
                    if self.conn.is_connected():
                        self._logger.info("Turned on SIO{}".format(configuration["pin"]))

                        if configuration["active_mode"] == "active_out_low":
                            self.conn.send(f"IO {pin} 0")

                            if self.IOCurrent[pin] == "0":
                                return flask.jsonify("state: on")
                            else:
                                return flask.jsonify("state: off")

                        elif configuration["active_mode"] == "active_out_high":
                            self.conn.send(f"IO {pin} 1")

                            if self.IOCurrent[pin] == "1":
                                return flask.jsonify("state: on")
                            else:
                                return flask.jsonify("state: off")

                    else:
                        self._logger.info(
                            "Not connected ignored IO command on Pin{}".format(pin)
                        )

            elif command == "turnSioOff":
                if Permissions.CONTROL.can() and pin >= 0:
                    if self.conn.is_connected():
                        self._logger.info("Turned off SIO{}".format(configuration["pin"]))
                        if configuration["active_mode"] == "active_out_low":
                            self.conn.send(f"IO {pin} 1")
                            if self.IOCurrent[pin] == "1":
                                return flask.jsonify("state: off")
                            else:
                                return flask.jsonify("state: on")

                        elif configuration["active_mode"] == "active_out_high":
                            self.conn.send(f"IO {pin} 0")
                            if self.IOCurrent[pin] == "0":
                                return flask.jsonify("state: off")
                            else:
                                return flask.jsonify("state: on")

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
        states = []
        for configuration in self._settings.get(["sio_configurations"]):
            if configuration["pin"] is not None:
                pin = int(configuration["pin"])

                if self.IOCurrent is not None and pin < len(self.IOCurrent):
                    if pin < 0:
                        states.append("")
                    elif configuration["active_mode"] == "active_in_low":
                        pstate = "off" if self.IOCurrent[pin] == "1" else "on"
                        states.append(pstate)
                    elif configuration["active_mode"] == "active_in_high":
                        pstate = "on" if self.IOCurrent[pin] == "1" else "off"
                        states.append(pstate)
                    elif configuration["active_mode"] == "active_out_low":
                        pstate = "off" if self.IOCurrent[pin] == "1" else "on"
                        states.append(pstate)
                    elif configuration["active_mode"] == "active_out_high":
                        pstate = "on" if self.IOCurrent[pin] == "1" else "off"
                        states.append(pstate)
                else:
                    if self.conn is not None and self.conn.is_connected() is True:
                        self._logger.info(
                            f"Pin number assigned to IO control{pin=} maybe out of range."
                        )

                    states.append("off")
            else:
                states.append("off")

        return flask.jsonify(states)

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

    def turn_psu_on(self):
        if self._settings.get(["EnablePSUIOPoint"]):
            psupoint = self._settings.get(["PSUIOPoint"])
            if self._settings.get(["InvertPSUIOPoint"]):
                self.conn.send(f"IO {psupoint} 0")
            else:
                self.conn.send(f"IO {psupoint} 1")

        self._logger.info("******Switching PSU On: sending command to IO******")

    def turn_psu_off(self):
        if self._settings.get(["EnablePSUIOPoint"]):
            psupoint = self._settings.get(["PSUIOPoint"])
            if self._settings.get(["InvertPSUIOPoint"]):
                self.conn.send(f"IO {psupoint} 1")
            else:
                self.conn.send(f"IO {psupoint} 0")

        self._logger.info("******Switching PSU Off: sending command to IO******")

    def get_psu_state(self):
        rtn = None

        if self.IOCurrent is None:
            return False

        psuRelayState = self.IOCurrent[int(self._settings.get(["PSUIOPoint"]))]
        self._logger.info("******Reporting PSU Current State:" + psuRelayState)

        if self._settings.get(["InvertPSUIOPoint"]):
            rtn = self.IOCurrent[int(self._settings.get(["PSUIOPoint"]))] == "0"
        else:
            rtn = self.IOCurrent[int(self._settings.get(["PSUIOPoint"]))] == "1"

        return rtn

    ##~~ AssetPlugin mixin

    def get_assets(self):
        # Define your plugin's asset files to automatically include in the
        # core UI here.
        # "less": ["less/PSUControlSerial.less"],
        return dict(
            js=["js/siocontrol.js", "js/fontawesome-iconpicker.min.js"],
            css=["css/siocontrol.css", "css/fontawesome-iconpicker.min.css"],
        )

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
