sap.ui.require([
    "sap/ui/test/opaQunit",
    "com/demo/fioriapp/test/integration/pages/Main"
], function (opaTest) {
    "use strict";

    QUnit.module("Main View Integration Tests");

    opaTest("Should see the main page with search field", function (Given, When, Then) {
        Given.iStartMyApp();
        Then.onTheMainPage.iShouldSeeTheSearchField();
        Then.iTeardownMyApp();
    });

    opaTest("Should see the item list", function (Given, When, Then) {
        Given.iStartMyApp();
        Then.onTheMainPage.iShouldSeeTheItemList();
        Then.iTeardownMyApp();
    });

    QUnit.start();
});
