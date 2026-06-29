sap.ui.define([
    "sap/ui/test/opaQunit",
    "com/demo/fioriapp/test/integration/pages/Main"
], function (opaTest) {
    "use strict";

    QUnit.module("Main View Integration Tests");

    opaTest("Should display confirmation dialog on item delete", function (Given, When, Then) {
        // Arrangements
        Given.iStartMyApp();

        // Actions
        When.onTheMainPage.iDeleteAnItem();

        // Assertions
        Then.onTheMainPage.iShouldSeeTheConfirmationDialog();

        // Cleanup
        Then.iTeardownMyApp();
    });

    opaTest("Should update item count after deletion", function (Given, When, Then) {
        // Arrangements
        Given.iStartMyApp();

        // Actions
        When.onTheMainPage.iDeleteAnItem();
        When.onTheConfirmationDialog.iConfirmDeletion();

        // Assertions
        Then.onTheMainPage.iShouldSeeUpdatedItemCount();

        // Cleanup
        Then.iTeardownMyApp();
    });
});