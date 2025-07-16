const { devices } = require('@playwright/test');

/** @type {import('@playwright/test').PlaywrightTestConfig} */
const config = {
  testDir: './tests',
  timeout: 30000,
  expect: {
    timeout: 5000
  },
  projects: [
    {
      name: 'android',
      use: {
        // Base configuration for Android
        browserName: 'chromium',
        channel: 'chrome',
        viewport: { width: 360, height: 800 },
        deviceScaleFactor: 2,
        isMobile: true,
        hasTouch: true,
        defaultBrowserType: 'chromium',
        launchOptions: {
          args: ['--no-sandbox']
        },
        contextOptions: {
          reducedMotion: 'reduce',
          strictSelectors: true
        },
        // Android app configuration
        app: {
          package: 'org.wikipedia',
          activity: 'org.wikipedia.main.MainActivity'
        }
      },
    }
  ],
  reporter: 'list',
};

module.exports = config; 