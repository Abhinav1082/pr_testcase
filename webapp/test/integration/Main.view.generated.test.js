sap.ui.define([
    "sap/ui/test/opaQunit",
    "com/demo/fioriapp/test/integration/pages/Main"
], function (opaTest) {
    "use strict";

    QUnit.module("Main View Integration Tests");

    opaTest("Should display confirmation dialog on delete", function (Given, When, Then) {
        // Arrangements
        Given.iStartMyApp();

        // Actions
        When.onTheMainPage.iPressDeleteOnAnItem();

        // Assertions
        Then.onTheMainPage.iShouldSeeTheConfirmationDialog();

        // Cleanup
        Then.iTeardownMyApp();
    });

    opaTest("Should show toast message on item addition", function (Given, When, Then) {
        // Arrangements
        Given.iStartMyApp();

        // Actions
        When.onTheMainPage.iPressAddItem();

        // Assertions
        Then.onTheMainPage.iShouldSeeTheItemAddedToast();

        // Cleanup
        Then.iTeardownMyApp();
    });
});