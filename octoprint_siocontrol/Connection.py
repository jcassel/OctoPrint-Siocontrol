# import fnmatch
import glob
import os
import re

# import sys
import threading
import time

import serial
import serial.tools.list_ports

import octoprint.plugin

# from octoprint.filemanager import valid_file_type
# from octoprint.filemanager.destinations import FileDestinations
from octoprint.settings import settings

try:
    import winreg
except ImportError:
    try:
        import _winreg as winreg  # type: ignore
    except ImportError:
        pass

regex_serial_devices = re.compile(r"^(?:ttyUSB|ttyACM|tty\.usb|cu\.|cuaU|ttyS|rfcomm).*")
"""Regex used to filter out valid tty devices"""


class Connection:
    def __init__(self, plugin):
        self._logger = plugin._logger
        self._printer = plugin._printer
        self._printer_profile_manager = plugin._printer_profile_manager
        self._plugin_manager = plugin._plugin_manager
        self._identifier = plugin._identifier
        self._settings = plugin._settings
        self.plugin = plugin
        self.readThread = None
        self.pauseReadThread = False
        self.readThreadStop = False
        self.writeThread = None
        self.pauseWriteThread = False
        self.writeThreadStop = False
        self._connected = False
        self.serialConn = None
        self.gCodeExtrusion = 0
        self.boxExtrusion = 0
        self.boxExtrusionOffset = 0
        self.IOCount = 0
        self.commandQueue = []
        self.enableCommandQueue = False
        self.deviceIsCompatible = False

        # this value should eventually be exposed.
        # It could be different depending on the controler
        self.iReadTimeoutCounterMax = 15

    def getVersionCompatibilty(self):
        self.send("VC")

    def IODeviceInitialize(self):
        self.serialConn.reset_input_buffer()
        self.serialConn.reset_output_buffer()
        self.serialConn.write("VC\n".encode())  # request version and compatibility info
        checkingCompatibility = True
        iReadTimeoutCounter = 0
        while checkingCompatibility is True:
            line = self.serialConn.readline()

            if line:
                try:
                    line = line.strip().decode()
                except Exception:
                    pass
                if line[:2] == "VI":
                    self._logger.debug("IO Reported Version as:{}".format(line[3:]))

                elif line[:2] == "CP":
                    self._logger.debug("IO Reported Compatibility as:{}".format(line))
                    self.plugin.ReportedCompatibleVersion = line[3:]
                    if self.plugin.ReportedCompatibleVersion not in self.plugin.DeviceCompatibleVersions:
                        self._logger.info("IO Reported Compatibility as:{}".format(line))
                        self._logger.info("Required Compatibility is:{}".format(self.plugin.DeviceCompatibleVersions))
                        self.disconnect()
                        self._connected = False
                        self._logger.error("IO Not compatible with this version of SIOPlugin")
                        self._logger.error("Stopping communications to SIO")
                        self.stopCommThreads()
                        self.plugin.IOSWarnings = ("Conneced to encompatible device. Check Comm port setting")
                        self.deviceIsCompatible = False
                    else:  # all good
                        self.deviceIsCompatible = True
                        self.send("IC")  # que up request for IO Count
                        self.plugin.IOSWarnings = ""
                    # no matter what the result is we are done here.
                    checkingCompatibility = False
                elif line[:2] == "OK":
                    self._logger.debug("IO Responded with Ack:{}".format(line))
                elif (line[:2] == "IO" or line[:2] == "RR" or line[:2] == "IT"):
                    # ignore
                    self._logger.debug("Unexpected(valid) Comm during compatibility check:{}".format(line))
                    # Attempt to reset comm and resend VC request
                    # this can be needed for controllers that reset on connect.
                    self._logger.debug("resetting comms resending VC request")
                    self.serialConn.reset_input_buffer()
                    self.serialConn.reset_output_buffer()
                    self.serialConn.write("VC\n".encode())
                elif line[:2] == "DG":
                    # truly ignore
                    self._logger.debug("Unexpected(valid) debug Comm during compatibility check:{}".format(line))
                else:
                    self._logger.debug("Unexpected Comm during compatibility check:{}".format(line))
                    iReadTimeoutCounter = iReadTimeoutCounter + 1
                    self._logger.error("IO readtimeout Count:{}".format(iReadTimeoutCounter))
                    if iReadTimeoutCounter == (self.iReadTimeoutCounterMax / 2):  # Attempt to reset comm and resend VC request
                        self._logger.debug("resetting comms resending VC request")
                        self.serialConn.reset_input_buffer()
                        self.serialConn.reset_output_buffer()
                        self.serialConn.write("VC\n".encode())  # request version and compatibility info

                    if iReadTimeoutCounter > self.iReadTimeoutCounterMax:
                        self.disconnect()
                        self._connected = False
                        self.stopCommThreads()
                        self.plugin.IOSWarnings = ("Conneced to encompatible device. Check Comm port setting")
                        self.deviceIsCompatible = False  # Seems that the device is not responding.
                        checkingCompatibility = False
            else:
                iReadTimeoutCounter = iReadTimeoutCounter + 1
                self._logger.error("IO readtimeout Count:{}".format(iReadTimeoutCounter))

                if iReadTimeoutCounter > self.iReadTimeoutCounterMax:
                    self.deviceIsCompatible = False
                    # Seems that the device is not responding.
                    checkingCompatibility = False

    def disconnect(self):
        self.commandQueue = []  # empty command queue
        self._logger.info("cleared Command queue")
        while self.serialConn.is_open:
            self.serialConn.close()
            time.sleep(1)

        self.IOCount = 0
        self._connected = False
        self.plugin.IOStatus = "Disconnected"
        return

    def connect(self):
        try:
            if (str(self._settings.get(["IOPort"])) != "None" and str(self._settings.get(["IOBaudRate"])) != "None"):
                self._logger.info("Connecting...")
                self._logger.info("Port:" + self._settings.get(["IOPort"]))
                self._logger.info("IOBaudRate:" + self._settings.get(["IOBaudRate"]))

                self.serialConn = serial.Serial(
                    self._settings.get(["IOPort"]),
                    int(self._settings.get(["IOBaudRate"])),
                    timeout=1,
                )

                if self.serialConn.is_open:
                    self.commandQueue = []
                    self._logger.debug("cleared Command queue")
                    self._connected = True
                    self.IODeviceInitialize()
                    if self.deviceIsCompatible is True:
                        self.plugin.IOStatus = "Connected"
                        self.plugin.IOWarnings = " "
                        self._logger.debug("Starting read thread...")
                        self.startCommThreads()
                    else:
                        self.plugin.IOStatus = "SIO device incompatible"
                        self._logger.info("SIO device incompatible")
                        self._connected = False
                else:
                    self.plugin.IOStatus = "Could not open port"
                    self._logger.info("Could not open port")
                    self._connected = False
            else:
                self._logger.info("Connection Information not set. Conneciton to SIO not attempted.")
                self.plugin.IOStatus = "Conn settings error"
                self._connected = False

        except serial.SerialException as err:
            self.commandQueue = []
            self._logger.debug("cleared Command queue")
            self._logger.debug("Connection failed!")
            self._logger.exception("Serial Exception: {}, {}".format(err, type(err)))

        except Exception as err:
            self._logger.exception("Unexpected {}, {}".format(err, type(err)))

    def Update_IOSI(self, value):
        self.send("SI " + value)

    def checkActionIO(self):
        self.checkEStop()
        self.checkFilamentRunOut()

    def checkFilamentRunOut(self):
        if not self._settings.get(["EnableFRSIOPoint"]):
            return

        if (
            int(self._settings.get(["FRSIOPoint"])) >= len(self.plugin.IOCurrent) or int(self._settings.get(["FRSIOPoint"])) < 0
        ):
            self._logger.info("Filament RunOut IO point is out of range.")
            return

        if self._settings.get(["InvertFRSIOPoint"]):
            filamentOut = (self.plugin.IOCurrent[int(self._settings.get(["FRSIOPoint"]))] == "0")
        else:
            filamentOut = (self.plugin.IOCurrent[int(self._settings.get(["FRSIOPoint"]))] == "1")

        if filamentOut:
            if self._printer.is_printing():
                self._logger.info("Detected Filament RunOut")
                self._printer.toggle_pause_print()

    def checkEStop(self):
        estopPushed = None
        if not self._settings.get(["EnableESTIOPoint"]):
            return

        if (
            int(self._settings.get(["ESTIOPoint"])) >= len(self.plugin.IOCurrent) or int(self._settings.get(["ESTIOPoint"])) < 0
        ):
            self._logger.info("E-Stop IO point is out of range.")
            return

        if self._settings.get(["InvertESTIOPoint"]):
            estopPushed = (
                self.plugin.IOCurrent[int(self._settings.get(["ESTIOPoint"]))] == "0"
            )
        else:
            estopPushed = (
                self.plugin.IOCurrent[int(self._settings.get(["ESTIOPoint"]))] == "1"
            )

        if estopPushed:  # estop
            self._printer.commands(["M112"])

    def send(self, data):
        self.commandQueue.append("{}\n".format(data).encode())  # f"{data}\n".encode()
        self._logger.debug("Queueing Command: %s" % data)

    def write_thread(self, serialConnection):
        pauseWasSent = False
        while self.is_connected and self.readThreadStop is False:
            try:
                time.sleep(0.125)
                if self.enableCommandQueue is True and len(self.commandQueue) > 0:
                    self.pauseReadThread = True
                    if len(self.commandQueue) > 1 and pauseWasSent is False:
                        serialConnection.reset_input_buffer()
                        serialConnection.write("EIO\n".encode())
                        command = "EIO-NoPop"
                        pauseWasSent = True
                    else:
                        command = self.commandQueue[0]
                        serialConnection.write(command)
                        self._logger.debug("SOI Sent:{}".format(command))

                    time.sleep(0.1)
                    line = serialConnection.readline()
                    if line:
                        try:
                            line = line.strip().decode()
                        except Exception:
                            pass
                        self._logger.debug(">IO Responded with:{}".format(line))
                        if line[:2] == "OK" and command != "EIO-NoPop":
                            pcommand = self.commandQueue.pop(0)
                            self._logger.debug("Poped Command: %s" % pcommand)
                            # errorCount = 0

                else:
                    if pauseWasSent is True:
                        pauseWasSent = False
                        serialConnection.write("BIO\n".encode())
                        self._logger.debug("SOI Sent:BIO")

                    self.pauseReadThread = False

            except serial.SerialException:
                self.disconnect()
                self._connected = False
                self._logger.error("error reading from USB")
                self.stopCommThreads()

        self._logger.debug("Write Thread: Thread stopped.")

    def read_thread(self, serialConnection):
        # need a short delay here for devices that reboot on connect like the nanno
        time.sleep(1)  # time for write thread to do work.
        errorCount = 0
        self._logger.debug("Read Thread: Starting thread")
        self.enableCommandQueue = False
        while self.readThreadStop is False:
            try:
                if (
                    len(self.commandQueue) == 0 or self.enableCommandQueue is False
                ) and self.pauseReadThread is False:
                    line = serialConnection.readline()
                    if line:
                        try:
                            line = line.strip().decode()
                        except Exception:
                            pass
                        # send line to down streem sub plugins before it is processed here. Note that sub PlugIns alter the line.
                        # this is important because a subplugins must get the line for review. If adding something to the firmware / sub plugin,
                        # that will respond to a subplugin, it should have a prefix with an "XT" as the lead 2 characters. If it does not have
                        # a known prefix, it will cause the error recieved count to raise and might casue a disconnect.
                        self.plugin.serialRecievequeue(line)
                        if line[:2] == "VI":
                            self._logger.debug("IO Reported Version as: {}".format(line))
                            errorCount = 0

                        elif line[:2] == "CP":
                            self._logger.debug("IO Reported Compatibility as: {}".format(line))
                            self.plugin.ReportedCompatibleVersion = line[3:]
                            if self.plugin.ReportedCompatibleVersion not in self.plugin.DeviceCompatibleVersions:
                                self._logger.info("IO Reported Compatibility as: {}".format(line))
                                self._logger.info("Required Compatibility is: {}".format(self.plugin.DeviceCompatibleVersion))
                                self.disconnect()
                                self._connected = False
                                self._logger.error("IO Not compatible with this version of SIOPlugin")
                                self._logger.error("Stopping communications to SIO")
                                self.stopCommThreads()
                            errorCount = 0

                        elif line[:2] == "IO":
                            self._logger.debug("IO Reported State as: {}".format(line))
                            if (self.plugin.IOCurrent != line[3:]):  # only react to changes. Maybe future have a timeout somewhere for no reports
                                self._logger.info("IO Reported State change as:{}".format(line))
                                self.plugin.IOCurrent = line[3:]
                                self.IOCount = len(self.plugin.IOCurrent)
                                self.checkActionIO()
                                self.plugin.broadCastStateToSubPlugins()  # calls methods in Sub plugins for changed IO state.

                            errorCount = 0

                        elif line[:2] == "OK":
                            self._logger.debug("IO Responded with Ack: {}".format(line))
                            errorCount = 0

                        elif line[:2] == "IC":  # explicit report IO count.
                            self.IOCount = int(line[3:])
                            errorCount = 0

                        elif line[:2] == "RR":  # IO ready for commands
                            self._logger.debug("IO claimed ready for commands: {}".format(line))
                            self.enableCommandQueue = True
                            errorCount = 0

                        elif line[:2] == "IT":  # IO type List
                            self._logger.debug("IO Type list recieved: {}".format(line))
                            errorCount = 0

                        elif line[:2] == "DG":  # Debug Message
                            self._logger.debug("IO sent debug message: {}".format(line))
                            errorCount = 0
                        elif line[:2] == "FS":  # 4MB with spiffs(1.2MB APP/1.5 SPIFFS) This is expected firmware format
                            self._logger.debug("IO Responded with Firmware information: {}".format(line))
                            errorCount = 0
                        elif line[:2] == "XT":  # this is an extended message set. Liklely from a custom change in the firmware or maybe to support a sub PlugIn
                            self.plugin.routeXTMessage(line)
                            self._logger.debug("IO Responded with Extened message response: {}".format(line))
                            errorCount = 0
                        elif line[:2] == "TC":  # IO type descriptors
                            self._logger.debug("IO Responded with IO Desciptors information: {}".format(line))
                            errorCount = 0
                        else:
                            self._logger.debug("IO reported an unexpected data line: {}".format(line))  # error?
                            errorCount = errorCount + 1
                            if errorCount > self.iReadTimeoutCounterMax:
                                self.plugin.IOCurrent = ""
                                self.IOCount = 0
                                self.disconnect()
                                self._connected = False
                                self._logger.error("Too many Comm Errors disconnecting IO")
                                self.stopCommThreads()
                                self.plugin.IOStatus = "COMM ERROR"
                else:
                    time.sleep(0.25)  # time for write thread to do work.
            except serial.SerialException:
                self.disconnect()
                self._connected = False
                self._logger.error("Error reading from USB Comm threads stop called.")
                self.stopCommThreads()

        self._logger.debug("Read Thread: Thread stopped.")

    # serialList was copied from util/comm.py in the core of OctoPrint (that unreachabe section is there too. Not sure what its deal is maybe a false pos)
    def serialList(self):
        if os.name == "nt":
            candidates = []
            try:
                key = winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE, "HARDWARE\\DEVICEMAP\\SERIALCOMM"
                )
                i = 0
                while True:
                    portName = winreg.EnumValue(key, i)[1]
                    if not self.isPrinterPort(portName):
                        candidates += [portName]
                    i += 1

            except Exception as err:
                # [22] happens on windows machines. This is normal.
                if err.errno == 22:
                    self._logger.debug("Unexpected(windows OK) {}, {}".format(err, type(err)))
                else:
                    self._logger.exception("Unexpected {}, {}".format(err, type(err)))

                pass
        else:
            candidates = []
            try:
                with os.scandir("/dev") as it:
                    for entry in it:
                        if regex_serial_devices.match(entry.name):
                            if not self.isPrinterPort(entry.path):
                                candidates.append(entry.path)
            except Exception:
                self._logger.exception(
                    "Could not scan /dev for serial ports on the system"
                )

        # additional ports
        additionalPorts = settings().get(["serial", "additionalPorts"])
        if additionalPorts:
            for additional in additionalPorts:
                if not additional == "VIRTUAL":
                    candidates += glob.glob(additional)

        hooks = octoprint.plugin.plugin_manager().get_hooks(
            "octoprint.comm.transport.serial.additional_port_names"
        )
        for name, hook in hooks.items():
            try:
                if not hook(candidates)[0] == "VIRTUAL":
                    candidates += hook(candidates)

            except Exception:
                self._logger.info(
                    "Error while retrieving additional "
                    "serial port names from hook {}".format(name)
                )

        # blacklisted ports
        # blacklistedPorts = settings().get(["serial", "blacklistedPorts"])
        # if blacklistedPorts:
        #    for pattern in settings().get(["serial", "blacklistedPorts"]):
        #        candidates = list(
        #            filter(lambda x: not fnmatch.fnmatch(x, pattern), candidates)
        #        )

        # last used port = first to try, move to start
        prev = settings().get(["serial", "port"])
        if prev in candidates:
            candidates.remove(prev)
            candidates.insert(0, prev)

        return candidates

    def getRealPaths(self, ports):
        self._logger.info("Paths: %s" % ports)
        for index, port in enumerate(ports):
            port = os.path.realpath(port)
            ports[index] = port
        return ports

    def isPrinterPort(self, selected_port):
        if os.name != "nt":
            selected_port = os.path.realpath(selected_port)

        printer_port = self._printer.get_current_connection()[1]
        self._logger.info(
            "Checking is this port: %s the printers connected port?" % selected_port
        )
        self._logger.info("Printer port: %s" % printer_port)
        # because ports usually have a second available one (.tty or .cu)
        printer_port_alt = ""
        if printer_port is None:
            return False
        else:
            if "tty." in printer_port:
                printer_port_alt = printer_port.replace("tty.", "cu.", 1)
            elif "cu." in printer_port:
                printer_port_alt = printer_port.replace("cu.", "tty.", 1)
            self._logger.info("Printer port alt: %s" % printer_port_alt)
            if selected_port == printer_port or selected_port == printer_port_alt:
                return True
            else:
                return False

    def startCommThreads(self):
        if self.readThread is None:
            self.readThreadStop = False
            self.readThread = threading.Thread(
                target=self.read_thread, args=(self.serialConn,)
            )
            self.readThread.daemon = True
            self.readThread.start()

        if self.writeThread is None:
            self.writeThreadStop = False
            self.writeThread = threading.Thread(
                target=self.write_thread, args=(self.serialConn,)
            )
            self.writeThread.daemon = True
            self.writeThread.start()

    def stopCommThreads(self):
        self.readThreadStop = True
        if self.readThread and threading.current_thread() != self.readThread:
            try:
                self.readThread.join()
            except Exception:
                pass

        self.readThread = None

        self.writeThreadStop = True
        if self.writeThread and threading.current_thread() != self.writeThread:
            try:
                self.writeThread.join()
            except Exception:
                pass

        self.writeThread = None

    def is_connected(self):
        return self._connected
