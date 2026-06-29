sap.ui.define([
    "sap/ui/test/opaQunit",
    "com/demo/fioriapp/test/integration/pages/Main"
], function (opaTest) {
    "use strict";

    QUnit.module("Main View Integration Tests");

    opaTest("Should show delete confirmation dialog when deleting an item", function (Given, When, Then) {
        // Arrangements
        Given.iStartMyApp();

        // Actions
        When.onTheMainPage.iDeleteAnItem();

        // Assertions
        Then.onTheMainPage.iShouldSeeTheDeleteConfirmationDialog();

        // Cleanup
        Then.iTeardownMyApp();
    });

    opaTest("Should update item count after deletion", function (Given, When, Then) {
        // Arrangements
        Given.iStartMyApp();

        // Actions
        When.onTheMainPage.iDeleteAnItem();
        When.onTheMainPage.iConfirmDeletion();

        // Assertions
        Then.onTheMainPage.iShouldSeeUpdatedItemCount();

        // Cleanup
        Then.iTeardownMyApp();
    });

    opaTest("Should show toast message on adding an item", function (Given, When, Then) {
        // Arrangements
        Given.iStartMyApp();

        // Actions
        When.onTheMainPage.iAddAnItem();

        // Assertions
        Then.onTheMainPage.iShouldSeeAddItemToastMessage();

        // Cleanup
        Then.iTeardownMyApp();
    });
});