sap.ui.define([
    "sap/ui/core/mvc/Controller",
    "sap/ui/model/json/JSONModel",
    "sap/m/MessageBox",
    "sap/m/MessageToast",
    "com/demo/fioriapp/model/formatter"
], function (Controller, JSONModel, MessageBox, MessageToast, formatter) {
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
            MessageToast.show("Item added successfully");
        },

        onDeleteItem: function (oEvent) {
            var oItem = oEvent.getParameter("listItem");
            var sPath = oItem.getBindingContext().getPath();
            var oModel = this.getView().getModel();
            var that = this;

            MessageBox.confirm("Are you sure you want to delete this item?", {
                title: "Confirm Deletion",
                onClose: function (sAction) {
                    if (sAction === MessageBox.Action.OK) {
                        oModel.remove(sPath, {
                            success: function () {
                                MessageToast.show("Item deleted successfully");
                                that._updateItemCount();
                            },
                            error: function () {
                                MessageBox.error("Failed to delete item. Please try again.");
                            }
                        });
                    }
                }
            });
        },

        _updateItemCount: function () {
            var oModel = this.getView().getModel("view");
            var iCount = oModel.getProperty("/itemCount");
            if (iCount > 0) {
                oModel.setProperty("/itemCount", iCount - 1);
            }
        },

        formatItemCount: function (iCount) {
            return iCount === 0 ? "No items" : iCount + " item(s)";
        }
    });
});
