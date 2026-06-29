sap.ui.define([
    "com/demo/fioriapp/model/formatter"
], function (formatter) {
    "use strict";

    QUnit.module("Formatter - formatItemCount");

    QUnit.test("Should return 'No items' for count 0", function (assert) {
        assert.strictEqual(formatter.formatItemCount(0), "No items");
    });

    QUnit.test("Should return formatted string for positive count", function (assert) {
        assert.strictEqual(formatter.formatItemCount(3), "3 item(s)");
    });

    QUnit.test("Should return empty string for null", function (assert) {
        assert.strictEqual(formatter.formatItemCount(null), "");
    });

    QUnit.module("Formatter - formatStatus");

    QUnit.test("Should return Success for active status", function (assert) {
        assert.strictEqual(formatter.formatStatus("active"), "Success");
    });

    QUnit.test("Should return Warning for inactive status", function (assert) {
        assert.strictEqual(formatter.formatStatus("inactive"), "Warning");
    });

    QUnit.test("Should return None for unknown status", function (assert) {
        assert.strictEqual(formatter.formatStatus("unknown"), "None");
    });
});
