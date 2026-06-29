sap.ui.define([
    "sap/ui/base/ManagedObject",
    "com/demo/fioriapp/controller/Main.controller"
], function (ManagedObject, MainController) {
    "use strict";

    QUnit.module("Main Controller Tests", {
        beforeEach: function () {
            this.oController = new MainController();
        },
        afterEach: function () {
            this.oController.destroy();
        }
    });

    QUnit.test("Should add item and show MessageToast", function (assert) {
        // Arrange
        var oModel = new sap.ui.model.json.JSONModel({ itemCount: 0 });
        this.oController.getView().setModel(oModel, "view");

        // Act
        this.oController.onAddItem();

        // Assert
        assert.strictEqual(oModel.getProperty("/itemCount"), 1, "Item count should be incremented");
        assert.ok(sap.m.MessageToast.show.calledWith("Item added successfully"), "MessageToast should be shown");
    });

    QUnit.test("Should delete item with confirmation dialog", function (assert) {
        // Arrange
        var oModel = new sap.ui.model.json.JSONModel({ itemCount: 1 });
        this.oController.getView().setModel(oModel, "view");
        var oEvent = {
            getParameter: function () {
                return {
                    getBindingContext: function () {
                        return {
                            getPath: function () {
                                return "/Items/0";
                            }
                        };
                    }
                };
            }
        };

        // Act
        this.oController.onDeleteItem(oEvent);

        // Assert
        assert.ok(sap.m.MessageBox.confirm.calledOnce, "Confirmation dialog should be shown");
        assert.ok(sap.m.MessageToast.show.calledWith("Item deleted successfully"), "MessageToast should be shown after deletion");
    });
});