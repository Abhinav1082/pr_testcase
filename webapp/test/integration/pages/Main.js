sap.ui.define([
    "sap/ui/test/Opa5",
    "sap/ui/test/actions/Press",
    "sap/ui/test/matchers/PropertyStrictEquals"
], function (Opa5, Press, PropertyStrictEquals) {
    "use strict";

    Opa5.createPageObjects({
        onTheMainPage: {
            arrangements: {
                iStartMyApp: function () {
                    return this.iStartMyUIComponent({
                        componentConfig: {
                            name: "com.demo.fioriapp"
                        }
                    });
                }
            },
            assertions: {
                iShouldSeeTheSearchField: function () {
                    return this.waitFor({
                        id: "searchField",
                        viewName: "com.demo.fioriapp.view.Main",
                        success: function () {
                            Opa5.assert.ok(true, "The search field is visible");
                        },
                        errorMessage: "Search field not found"
                    });
                },

                iShouldSeeTheItemList: function () {
                    return this.waitFor({
                        id: "itemList",
                        viewName: "com.demo.fioriapp.view.Main",
                        success: function () {
                            Opa5.assert.ok(true, "The item list is visible");
                        },
                        errorMessage: "Item list not found"
                    });
                }
            }
        }
    });
});
