import fnmatch
import glob
import os
import re
import sys
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
        # self.ports = []

        self.readThread = None
        self.readThreadStop = False
        self._connected = False
        self.serialConn = None
        self.gCodeExtrusion = 0
        self.boxExtrusion = 0
        self.boxExtrusionOffset = 0
        # self.connect()

    def disconnect(self):

        while self.serialConn.is_open:
            self.serialConn.close()
            time.sleep(1)

        return

    def connect(self):
        self._logger.info("Connecting...")
        # self.ports = self.serialList()  # dont really need now.
        try:
            # self.serialConn = serial.Serial("COM3", 115200, timeout=0.5)

            self.serialConn = serial.Serial(
                self._settings.get(["IOPort"]),
                int(self._settings.get(["IOBaudRate"])),
                timeout=0.5,
            )
            if self.serialConn.is_open:
                self._connected = True
                self._logger.info("Starting read thread...")
                self.startReadThread()

        except serial.SerialException as err:
            self._logger.info("Connection failed!")
            self._logger.exception(f"Serial Exception: {err=}, {type(err)=}")
        except Exception as err:
            self._logger.exception(f"Unexpected {err=}, {type(err)=}")

    def Update_IOSI(self, value):
        self.send("SI " + value)

    def checkActionIO(self):
        self.checkEStop()
        self.checkFilamentRunOut()

    def checkFilamentRunOut(self):
        if not self._settings.get(["EnableFRSIOPoint"]):
            return

        if self._settings.get(["InvertFRSIOPoint"]):
            filamentOut = (
                self.plugin.IOCurrent[int(self._settings.get(["FRSIOPoint"]))] == "0"
            )
        else:
            filamentOut = (
                self.plugin.IOCurrent[int(self._settings.get(["FRSIOPoint"]))] == "1"
            )

        if filamentOut:
            if self._printer.is_printing():
                self._logger.info("Detected Filament RunOut")
                self._printer.toggle_pause_print()

    def checkEStop(self):
        estopPushed = None
        if not self._settings.get(["EnableESTIOPoint"]):
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
        self._logger.info("Sending: %s" % data)
        # data = data + "\n"
        self.serialConn.write(data.encode())

    def read_thread(self, serialConnection):
        self._logger.info("Read Thread: Starting thread")
        while self.readThreadStop is False:
            try:
                line = serialConnection.readline()
                if line:
                    try:
                        line = line.strip().decode()
                    except Exception:
                        pass

                    if line[:2] == "IO":
                        self._logger.info(f"IO Reported State as:{line=}")
                        self.plugin.IOCurrent = line[3:][:9]  # just digital
                        self.checkActionIO()

                    if line[:2] == "OK":
                        self._logger.info(f"IO Responded with:{line=}")

                    if line[:2] != "OK" and line[:2] != "IO":
                        self._logger.info(f"IO sent:{line=}")  # error?

            except serial.SerialException:
                self._connected = False
                self._logger.error("error reading from USB")
                # self.update_ui_control("disconnected")
                self.stopReadThread()

        self._logger.info("Read Thread: Thread stopped.")

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
                self._logger.exception(f"Unexpected {err=}, {type(err)=}")
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
                self._logger.exception(
                    "Error while retrieving additional "
                    "serial port names from hook {}".format(name)
                )

        # blacklisted ports
        blacklistedPorts = settings().get(["serial", "blacklistedPorts"])
        if blacklistedPorts:
            for pattern in settings().get(["serial", "blacklistedPorts"]):
                candidates = list(
                    filter(lambda x: not fnmatch.fnmatch(x, pattern), candidates)
                )

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
        self._logger.info("Trying port: %s" % selected_port)
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

    def startReadThread(self):
        if self.readThread is None:
            self.readThreadStop = False
            self.readThread = threading.Thread(
                target=self.read_thread, args=(self.serialConn,)
            )
            self.readThread.daemon = True
            self.readThread.start()

    def stopReadThread(self):
        self.readThreadStop = True
        if self.readThread and threading.current_thread() != self.readThread:
            self.readThread.join()
        self.readThread = None

    def is_connected(self):
        return self._connected
