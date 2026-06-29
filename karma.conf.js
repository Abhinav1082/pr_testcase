module.exports = function (config) {
    "use strict";

    config.set({
        frameworks: ["qunit", "ui5"],
        ui5: {
            type: "application",
            url: "https://sdk.openui5.org",
            testpage: "webapp/test/testsuite.qunit.html"
        },
        browsers: [process.env.CHROME_BIN ? "ChromeHeadlessNoSandbox" : "ChromeHeadless"],
        customLaunchers: {
            ChromeHeadlessNoSandbox: {
                base: "ChromeHeadless",
                flags: ["--no-sandbox", "--disable-gpu"]
            }
        },
        singleRun: true,
        reporters: ["progress"],
        logLevel: config.LOG_INFO,
        browserNoActivityTimeout: 60000,
        browserDisconnectTimeout: 10000
    });
};
