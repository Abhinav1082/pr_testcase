sap.ui.define([
    "sap/ui/test/opaQunit",
    "com/demo/fioriapp/test/integration/pages/Main"
], function (opaTest) {
    "use strict";

    QUnit.module("Main View Integration Tests");

    opaTest("Should show confirmation dialog when deleting an item", function (Given, When, Then) {
        // Arrangements
        Given.iStartMyApp();

        // Actions
        When.onTheMainPage.iPressDeleteOnAnItem();

        // Assertions
        Then.onTheMainPage.iShouldSeeTheConfirmationDialog();

        // Cleanup
        Then.iTeardownMyApp();
    });

    opaTest("Should update item count after deletion", function (Given, When, Then) {
        // Arrangements
        Given.iStartMyApp();

        // Actions
        When.onTheMainPage.iConfirmDeletion();

        // Assertions
        Then.onTheMainPage.iShouldSeeUpdatedItemCount();

        // Cleanup
        Then.iTeardownMyApp();
    });
});