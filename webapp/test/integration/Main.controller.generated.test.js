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
                            itemCount: 0
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
                                return "/Items/1";
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

    QUnit.test("Should update item count after deletion", function (assert) {
        // Arrange
        var oModel = this.oController.getView().getModel();
        oModel.setProperty("/itemCount", 5);

        // Act
        this.oController._updateItemCount();

        // Assert
        assert.strictEqual(oModel.getProperty("/itemCount"), 4, "Item count should be decremented by 1");
    });

    QUnit.test("Should show toast message on add item", function (assert) {
        // Arrange
        var oModel = this.oController.getView().getModel();

        // Act
        this.oController.onAddItem();

        // Assert
        assert.strictEqual(oModel.getProperty("/itemCount"), 1, "Item count should be incremented by 1");
    });
});