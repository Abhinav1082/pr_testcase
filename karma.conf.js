module.exports = function (config) {
    "use strict";

    config.set({
        frameworks: ["qunit", "ui5"],
        ui5: {
            type: "application",
            url: "https://sdk.openui5.org",
            testpage: "webapp/test/testsuite.qunit.html"
        },
        browsers: ["ChromeHeadless"],
        singleRun: true,
        reporters: ["progress", "coverage"],
        coverageReporter: {
            dir: "coverage",
            reporters: [
                { type: "html", subdir: "html" },
                { type: "text-summary" }
            ]
        },
        logLevel: config.LOG_INFO
    });
};
