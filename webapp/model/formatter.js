sap.ui.define([], function () {
    "use strict";

    return {
        /**
         * Format item count for display.
         * @param {number} iCount - Number of items
         * @returns {string} Formatted count string
         */
        formatItemCount: function (iCount) {
            if (iCount === null || iCount === undefined) {
                return "";
            }
            if (iCount === 0) {
                return "No items";
            }
            return iCount + " item(s)";
        },

        /**
         * Format status to corresponding state.
         * @param {string} sStatus - Status value
         * @returns {string} ValueState
         */
        formatStatus: function (sStatus) {
            switch (sStatus) {
                case "active":
                    return "Success";
                case "inactive":
                    return "Warning";
                case "error":
                    return "Error";
                default:
                    return "None";
            }
        },

        /**
         * Format date for display.
         * @param {string} sDate - Date string
         * @returns {string} Formatted date
         */
        formatDate: function (sDate) {
            if (!sDate) {
                return "";
            }
            var oDate = new Date(sDate);
            return oDate.toLocaleDateString();
        }
    };
});
