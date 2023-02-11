/*
 * View model for OctoPrint-SioControl
 *
 * Author: JCsGotThis
 * License: AGPLv3
 */
$(function () {
    function SioControlViewModel(parameters) {
        var self = this;
        self.settings = parameters[0];
        self.sioButtons = ko.observableArray();
        self.sioConfigurations = ko.observableArray();
        self.SIO_Port = "";
        self.SIO_BaudRate = "";
        self.SIO_SI = "";

        SIO_EnablePSUIOPoint = "";
        SIO_PSUIOPoint = "";
        SIO_InvertPSUIOPoint = "";

        SIO_EnableESTIOPoint = "";
        SIO_ESTIOPoint = "";
        SIO_InvertESTIOPoint = "";

        SIO_EnableFRSIOPoint = "";
        SOI_FRSIOPoint = "";
        SIO_InvertFRSIOPoint = "";

        SioButtonStatusUpdateInterval = 1000;
        btnStates = [];

        var SioBtnInterval = -1; //setup for later access to clearInterval(SioBtnInterval);



        self.onBeforeBinding = function () {
            self.sioConfigurations(self.settings.settings.plugins.siocontrol.sio_configurations.slice(0));
            self.SIO_Port = self.settings.settings.plugins.siocontrol.IOPort();
            self.SIO_BaudRate = self.settings.settings.plugins.siocontrol.IOBaudRate();
            self.SIO_SI = self.settings.settings.plugins.siocontrol.IOSI();
            self.SIO_EnablePSUIOPoint = self.settings.settings.plugins.siocontrol.EnablePSUIOPoint();
            self.SIO_PSUIOPoint = self.settings.settings.plugins.siocontrol.PSUIOPoint();
            self.SIO_InvertPSUIOPoint = self.settings.settings.plugins.siocontrol.InvertPSUIOPoint();
            self.SIO_EnableESTIOPoint = self.settings.settings.plugins.siocontrol.EnableESTIOPoint();
            self.SIO_ESTIOPoint = self.settings.settings.plugins.siocontrol.ESTIOPoint();
            self.SIO_InvertESTIOPoint = self.settings.settings.plugins.siocontrol.InvertESTIOPoint();
            self.SIO_EnableFRSIOPoint = self.settings.settings.plugins.siocontrol.EnableFRSIOPoint();
            self.SIO_FRSIOPoint = self.settings.settings.plugins.siocontrol.FRSIOPoint();
            self.SIO_InvertFRSIOPoint = self.settings.settings.plugins.siocontrol.InvertFRSIOPoint();
            console.log(self.SIO_Port); //here for debuging. Easy to get to binding packed js
            self.updateSioButtons();

            intervalIds = setInterval(function () {
                self.updateSioButtons();
            }, self.SIO_SI);

            console.log(self.SIO_SI);

        };

        self.onSettingsBeforeSave = function () {
            self.settings.settings.plugins.siocontrol.sio_configurations(self.sioConfigurations.slice(0));
            self.settings.settings.plugins.siocontrol.IOPort(self.SIO_Port);
            self.settings.settings.plugins.siocontrol.IOBaudRate(self.SIO_BaudRate);
            self.settings.settings.plugins.siocontrol.IOSI(self.SIO_SI);
            self.settings.settings.plugins.siocontrol.EnablePSUIOPoint(self.SIO_EnablePSUIOPoint);
            self.settings.settings.plugins.siocontrol.PSUIOPoint(self.SIO_PSUIOPoint);
            self.settings.settings.plugins.siocontrol.InvertPSUIOPoint(self.SIO_InvertPSUIOPoint);
            self.settings.settings.plugins.siocontrol.EnableESTIOPoint(self.SIO_EnableESTIOPoint);
            self.settings.settings.plugins.siocontrol.ESTIOPoint(self.SIO_ESTIOPoint);
            self.settings.settings.plugins.siocontrol.InvertESTIOPoint(self.SIO_InvertESTIOPoint);
            self.settings.settings.plugins.siocontrol.EnableFRSIOPoint(self.SIO_EnableFRSIOPoint);
            self.settings.settings.plugins.siocontrol.FRSIOPoint(self.SIO_InvertFRSIOPoint);
            self.settings.settings.plugins.siocontrol.InvertFRSIOPoint(self.SIO_InvertFRSIOPoint);
        };

        self.onSettingsShown = function () {
            self.sioConfigurations(self.settings.settings.plugins.siocontrol.sio_configurations.slice(0));
            self.updateIconPicker();
        };

        self.onSettingsHidden = function () {
            self.sioConfigurations(self.settings.settings.plugins.siocontrol.sio_configurations.slice(0));
            //self.updateSioButtons();
        };

        self.addSioConfiguration = function () {
            self.sioConfigurations.push({ pin: 0, icon: "fas fa-plug", name: "", active_mode: "active_out_high", default_state: "default_off" });
            self.updateIconPicker();
        };

        self.removeSioConfiguration = function (configuration) {
            self.sioConfigurations.remove(configuration);
        };

        self.updateSioButtons = function () {
            if (self.btnStates === undefined) {
                self.sioButtons(ko.toJS(self.sioConfigurations).map(function (item) {
                    return {
                        icon: item.icon,
                        name: item.name,
                        current_state: "unknown",
                    }
                }));
            }

            OctoPrint.simpleApiGet("siocontrol").then(function (states) {
                updateBtns = false;
                if (self.btnStates === undefined)
                    self.btnStates = states;
                updateBtns = true; //first time through

                for (i = 0; i < states.length; i++) {
                    if (states[i] != self.btnStates[i]) {
                        btnStates = states;
                        updateBtns = true;
                        continue;
                    }
                }

                if (updateBtns) {
                    self.sioButtons().forEach(function (item, index) {
                        self.sioButtons.replace(item, {
                            icon: item.icon,
                            name: item.name,
                            current_state: states[index],
                        });
                    });
                }

            });
        };


        self.turnSioOn = function () {
            OctoPrint.simpleApiCommand("siocontrol", "turnSioOn", { id: self.sioButtons.indexOf(this) });
        }

        self.turnSioOff = function () {
            OctoPrint.simpleApiCommand("siocontrol", "turnSioOff", { id: self.sioButtons.indexOf(this) });
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
        dependencies: ["settingsViewModel"],
        elements: ["#settings_plugin_siocontrol", "#sidebar_plugin_siocontrol"]
    });
});
