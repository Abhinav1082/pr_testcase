sap.ui.define([
    "sap/ui/core/mvc/Controller",
    "sap/ui/model/json/JSONModel",
    "com/demo/fioriapp/model/formatter"
], function (Controller, JSONModel, formatter) {
    "use strict";

    return Controller.extend("com.demo.fioriapp.controller.Main", {
        formatter: formatter,

        onInit: function () {
            var oViewModel = new JSONModel({
                busy: false,
                itemCount: 0,
                searchQuery: ""
            });
            this.getView().setModel(oViewModel, "view");
            this._loadItems();
        },

        _loadItems: function () {
            var oModel = this.getView().getModel("view");
            oModel.setProperty("/busy", true);

            // Simulate loading items
            setTimeout(function () {
                oModel.setProperty("/busy", false);
                oModel.setProperty("/itemCount", 5);
            }, 100);
        },

        onSearch: function (oEvent) {
            var sQuery = oEvent.getParameter("newValue") || "";
            var oModel = this.getView().getModel("view");
            oModel.setProperty("/searchQuery", sQuery);

            var oList = this.byId("itemList");
            var oBinding = oList.getBinding("items");

            if (sQuery) {
                var oFilter = new sap.ui.model.Filter(
                    "Name",
                    sap.ui.model.FilterOperator.Contains,
                    sQuery
                );
                oBinding.filter([oFilter]);
            } else {
                oBinding.filter([]);
            }
        },

        onItemPress: function (oEvent) {
            var oItem = oEvent.getSource();
            var sPath = oItem.getBindingContext().getPath();
            var sId = sPath.split("/").pop();

            this.getOwnerComponent().getRouter().navTo("detail", {
                id: sId
            });
        },

        onAddItem: function () {
            var oModel = this.getView().getModel("view");
            var iCount = oModel.getProperty("/itemCount");
            oModel.setProperty("/itemCount", iCount + 1);
        },

        formatItemCount: function (iCount) {
            return iCount === 0 ? "No items" : iCount + " item(s)";
        }
    });
});
