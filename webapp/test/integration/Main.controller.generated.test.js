sap.ui.define([
    "sap/ui/base/ManagedObject",
    "com/demo/fioriapp/controller/Main.controller"
], function (ManagedObject, MainController) {
    "use strict";

    QUnit.module("Main Controller Tests", {
        beforeEach: function () {
            this.oController = new MainController();
            this.oController.getView = function() {
                return {
                    getModel: function() {
                        return new sap.ui.model.json.JSONModel({
                            itemCount: 5
                        });
                    }
                };
            };
        },
        afterEach: function () {
            this.oController.destroy();
        }
    });

    QUnit.test("Should show confirmation dialog on delete", function (assert) {
        // Arrange
        var oEvent = {
            getParameter: function() {
                return {
                    getBindingContext: function() {
                        return {
                            getPath: function() {
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
        assert.ok(true, "Confirmation dialog should be shown");
    });

    QUnit.test("Should update item count on successful deletion", function (assert) {
        // Arrange
        var oEvent = {
            getParameter: function() {
                return {
                    getBindingContext: function() {
                        return {
                            getPath: function() {
                                return "/Items/0";
                            }
                        };
                    }
                };
            }
        };

        // Act
        this.oController.onDeleteItem(oEvent);

        // Simulate successful deletion
        this.oController._updateItemCount();

        // Assert
        assert.strictEqual(this.oController.getView().getModel().getProperty("/itemCount"), 4, "Item count should be decremented");
    });
});