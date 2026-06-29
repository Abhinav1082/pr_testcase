sap.ui.define([
    "sap/ui/core/UIComponent",
    "com/demo/fioriapp/model/models"
], function (UIComponent, models) {
    "use strict";

    return UIComponent.extend("com.demo.fioriapp.Component", {
        metadata: {
            manifest: "json"
        },

        init: function () {
            UIComponent.prototype.init.apply(this, arguments);
            this.setModel(models.createDeviceModel(), "device");
            this.getRouter().initialize();
        }
    });
});
