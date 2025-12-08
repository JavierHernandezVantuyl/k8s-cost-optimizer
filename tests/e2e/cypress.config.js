const { defineConfig } = require('cypress')

module.exports = defineConfig({
  e2e: {
    baseUrl: 'http://localhost:3000',
    supportFile: 'tests/e2e/cypress/support/e2e.js',
    specPattern: 'tests/e2e/cypress/integration/**/*.spec.js',
    fixturesFolder: 'tests/e2e/cypress/fixtures',
    screenshotsFolder: 'tests/e2e/cypress/screenshots',
    videosFolder: 'tests/e2e/cypress/videos',
    downloadsFolder: 'tests/e2e/cypress/downloads',

    setupNodeEvents(on, config) {
      // implement node event listeners here
    },

    viewportWidth: 1280,
    viewportHeight: 720,

    video: true,
    videoCompression: 32,

    screenshotOnRunFailure: true,

    retries: {
      runMode: 2,
      openMode: 0
    },

    defaultCommandTimeout: 10000,
    requestTimeout: 15000,
    responseTimeout: 15000,

    env: {
      apiUrl: 'http://localhost:8000',
      coverage: false
    }
  }
})
