/*
 * View model for OctoPrint-SioControl
 *
 * Author: JCsGotThis
 * License: AGPLv3
 */
$(function () {
    function SioControlViewModel(parameters) {
        var self = this;
        self.settingsViewModel = parameters[0];
        self.controlViewModel = parameters[1];
        self.loginStateViewModel = parameters[2];
        self.accessViewModel = parameters[3];

        self.sioButtons = ko.observableArray();
        self.sioConfigurations = ko.observableArray();
        self.SIO_IOCounts = ko.observableArray();
        self.SIO_BaudRate = "";
        self.SIO_BaudRates = [];
        self.SIO_Port = ko.observable('');
        self.SIO_Ports = ko.observableArray();
        self.IOStatusMessage = ko.observable('Ready');
        self.IOSWarnings = ko.observable('');

        self.SIO_SI = 3001;

        SIO_EnablePSUIOPoint = 0;
        SIO_PSUIOPoint = "-1";
        SIO_InvertPSUIOPoint = "";

        SIO_EnableESTIOPoint = 0;
        SIO_ESTIOPoint = "-1"
        SIO_InvertESTIOPoint = "";

        SIO_EnableFRSIOPoint = 0;
        SIO_FRSIOPoint = "-1";
        SIO_InvertFRSIOPoint = "";

        SioButtonStatusUpdateInterval = 1000;
        btnStates = [];


        var SioBtnInterval = -1; //setup for later access to clearInterval(SioBtnInterval);



        self.onBeforeBinding = function () {
            self.sioConfigurations(self.settingsViewModel.settings.plugins.siocontrol.sio_configurations.slice(0));
                

            if (self.SIO_Port != null) {
                if (self.SIO_IOCounts().length == 0) {
                    self.getIOCounts();
                    console.log(self.SIO_IOCounts().length);
                }

                SioBtnInterval = setInterval(function () {
                    self.updateSioButtons();
                }, self.SIO_SI);
            }


            self.IOStatusMessage(self.settingsViewModel.settings.plugins.siocontrol.IOStatusMessage());
            self.IOSWarnings(self.settingsViewModel.settings.plugins.siocontrol.IOSWarnings());

            self.SIO_Port(self.settingsViewModel.settings.plugins.siocontrol.IOPort());
            self.SIO_Ports(self.settingsViewModel.settings.plugins.siocontrol.IOPorts());
            self.SIO_BaudRate = self.settingsViewModel.settings.plugins.siocontrol.IOBaudRate();
            self.SIO_BaudRates = self.settingsViewModel.settings.plugins.siocontrol.IOBaudRates();
            self.SIO_SI = self.settingsViewModel.settings.plugins.siocontrol.IOSI();
            self.SIO_EnablePSUIOPoint = self.settingsViewModel.settings.plugins.siocontrol.EnablePSUIOPoint();
            self.SIO_PSUIOPoint = self.settingsViewModel.settings.plugins.siocontrol.PSUIOPoint();
            self.SIO_InvertPSUIOPoint = self.settingsViewModel.settings.plugins.siocontrol.InvertPSUIOPoint();
            self.SIO_EnableESTIOPoint = self.settingsViewModel.settings.plugins.siocontrol.EnableESTIOPoint();
            self.SIO_ESTIOPoint = self.settingsViewModel.settings.plugins.siocontrol.ESTIOPoint();
            self.SIO_InvertESTIOPoint = self.settingsViewModel.settings.plugins.siocontrol.InvertESTIOPoint();
            self.SIO_EnableFRSIOPoint = self.settingsViewModel.settings.plugins.siocontrol.EnableFRSIOPoint();
            self.SIO_FRSIOPoint = self.settingsViewModel.settings.plugins.siocontrol.FRSIOPoint();
            self.SIO_InvertFRSIOPoint = self.settingsViewModel.settings.plugins.siocontrol.InvertFRSIOPoint();

            console.log(self.SIO_Port()); //here for debuging. Easy to get to binding packed js

            setInterval(function () {
                self.getStatusMessage();
            }, 5000);

            console.log(self.SIO_SI);

        };


        self.hasControlPermission = function () {
            return self.loginStateViewModel.hasPermission(self.accessViewModel.permissions.CONTROL);
        };


        self.onSettingsBeforeSave = function () {
            self.settingsViewModel.settings.plugins.siocontrol.sio_configurations(self.sioConfigurations.slice(0));
            self.settingsViewModel.settings.plugins.siocontrol.IOPort(self.SIO_Port());
            self.settingsViewModel.settings.plugins.siocontrol.IOBaudRate(self.SIO_BaudRate);
            if (self.SIO_SI != self.settingsViewModel.settings.plugins.siocontrol.IOSI()) {
                clearInterval(SioBtnInterval); //stop existing polling.
                SioBtnInterval = setInterval(function () { //start the updated one.
                    self.updateSioButtons();
                }, self.SIO_SI);
            }
            self.settingsViewModel.settings.plugins.siocontrol.IOSI(self.SIO_SI); //alwasy update
            self.settingsViewModel.settings.plugins.siocontrol.EnablePSUIOPoint(self.SIO_EnablePSUIOPoint);
            self.settingsViewModel.settings.plugins.siocontrol.PSUIOPoint(self.SIO_PSUIOPoint);
            self.settingsViewModel.settings.plugins.siocontrol.InvertPSUIOPoint(self.SIO_InvertPSUIOPoint);
            self.settingsViewModel.settings.plugins.siocontrol.EnableESTIOPoint(self.SIO_EnableESTIOPoint);
            self.settingsViewModel.settings.plugins.siocontrol.ESTIOPoint(self.SIO_ESTIOPoint);
            self.settingsViewModel.settings.plugins.siocontrol.InvertESTIOPoint(self.SIO_InvertESTIOPoint);
            self.settingsViewModel.settings.plugins.siocontrol.EnableFRSIOPoint(self.SIO_EnableFRSIOPoint);
            self.settingsViewModel.settings.plugins.siocontrol.FRSIOPoint(self.SIO_FRSIOPoint);
            self.settingsViewModel.settings.plugins.siocontrol.InvertFRSIOPoint(self.SIO_InvertFRSIOPoint);
            self.updateSioButtons();
            self.getIOCounts();
        };

        self.onSettingsShown = function () {
            self.sioConfigurations(self.settingsViewModel.settings.plugins.siocontrol.sio_configurations.slice(0));
            self.updateIconPicker();
        };

        self.onSettingsHidden = function () {
            self.sioConfigurations(self.settingsViewModel.settings.plugins.siocontrol.sio_configurations.slice(0));
        };

        self.addSioConfiguration = function () {
            self.sioConfigurations.push({ pin: 0, icon: "fas fa-plug", name: "", active_mode: "active_out_high", default_state: "default_off", on_nav: 0,on_side:0 });
            self.updateIconPicker();
        };



        self.removeSioConfiguration = function (configuration) {
            self.sioConfigurations.remove(configuration);
        };


        self.updateSioButtons = function () {
            if (self.SIO_IOCounts().length == 0) {
                self.requestIOCounts();
            }

            OctoPrint.simpleApiGet("siocontrol").then(function (states) {
                updateBtns = false;

                if (self.btnStates === undefined) {
                    self.btnStates = states;
                    updateBtns = true; //first time through
                }

                for (i = 0; i < states.length; i++) {
                    if (states[i] != self.btnStates[i]) {
                        self.btnStates = states;
                        updateBtns = true;
                        continue;
                    }
                }

                //if (updateBtns) {

                self.sioButtons(ko.toJS(self.sioConfigurations).map(function (item) {
                    return {
                        icon: item.icon,
                        name: item.name,
                        current_state: "unknown",
                        active_mode: item.active_mode,
                        pin: item.pin,
                        on_nav: item.on_nav,
                        on_side: item.on_side,
                    }
                }));

                self.sioButtons().forEach(function (item, index) {
                    self.sioButtons.replace(item, {
                        icon: item.icon,
                        name: item.name,
                        current_state: states[index],
                        active_mode: item.active_mode,
                        pin: item.pin,
                        on_nav: item.on_nav,
                        on_side: item.on_side,
                    });

                    //removeClass("off").addClass("on");    
                });
                //}

            });
        };


        self.addSioScriptAlignment = function () {
            self.sioScriptAlignments.push({ name: "", pin: -1, trigger_type: "" });
        };

        self.removeSioScriptAlignment = function (alignments) {
            self.sioScriptAlignments.remove(alignments);
        };

        self.getStatusMessage = function () {
            OctoPrint.simpleApiCommand("siocontrol", "getStatusMessage", {}).then(function (status) {
                self.IOStatusMessage(status[0]);
                self.IOSWarnings(status[1]);
            });


        };

        self.connectIO = function () {
            OctoPrint.simpleApiCommand("siocontrol", "connectIO", { port: self.SIO_Port(), baudRate: self.SIO_BaudRate, si: self.SIO_SI }).then(function (connected) {
                //no need to do anything the status will update. 
            });
        };

        self.getIOCounts = function () {
            //self.requestIOCounts();

            setTimeout(function () {
                self.requestIOCounts();
            }, self.SIO_SI * 2); //when you change ports.. you got to give it enough time to connect and calculate the count.
        }

        self.requestIOCounts = function () {
            OctoPrint.simpleApiCommand("siocontrol", "getIOCounts", {}).then(function (counts) {
                self.SIO_IOCounts(counts);
            });
        }


        self.getPorts = function () {
            OctoPrint.simpleApiCommand("siocontrol", "getPorts", {}).then(function (ports) {
                self.SIO_Ports(ports);
            });
        }

        self.toggleSioByIONumber = function (sioPin) {
            OctoPrint.simpleApiCommand("siocontrol", "toggelSio", { pin: sioPin }).then(function (state) {
                //self.sioButtons.indexOf(this)["current_state"] = state;
            });
            self.updateSioButtons();
        }

        self.turnSioOnByIONumber = function (sioId) {
            OctoPrint.simpleApiCommand("siocontrol", "turnSioOn", { id: sioId }).then(function (state) {
                //self.sioButtons.indexOf(this)["current_state"] = state;
            });
            self.updateSioButtons();
        }

        self.turnSioOffByIONumber = function (sioId) {
            OctoPrint.simpleApiCommand("siocontrol", "turnSioOff", { id: sioId }).then(function (state) {
                //self.sioButtons.indexOf(this)["current_state"] = state; 
            });
            self.updateSioButtons();
        }

        self.turnSioOn = function () {
            self.turnSioOnByIONumber(self.sioButtons.indexOf(this));
        }

        self.turnSioOff = function () {
            self.turnSioOffByIONumber(self.sioButtons.indexOf(this));
        }

        self.getBtnCls = function () {
            pin = self.sioButtons.indexOf(this);
            mode = self.sioConfigurations(pin)["active_mode"];
            console.log(mode);
            return "btn";

        }





        self.updateIconPicker = function () {
            $('.iconpicker').each(function (index, item) {
                $(item).iconpicker({
                    placement: "bottomLeft",
                    hideOnSelect: true,
                });
            });
        };




    }

    OCTOPRINT_VIEWMODELS.push({
        construct: SioControlViewModel,
        dependencies: ["settingsViewModel", "controlViewModel", "loginStateViewModel", "accessViewModel"],
        elements: ["#settings_plugin_siocontrol", "#sidebar_plugin_siocontrol", "#navbar_plugin_siocontrol"]
    });
});
