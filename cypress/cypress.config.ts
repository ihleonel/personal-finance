import { defineConfig } from 'cypress';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  e2e: {
    baseUrl: 'http://localhost:36130',
    specPattern: path.join(__dirname, 'e2e/**/*.cy.{ts,js}'),
    supportFile: path.join(__dirname, 'support/e2e.ts'),
    fixturesFolder: path.join(__dirname, 'fixtures'),
    videosFolder: path.join(__dirname, 'videos'),
    screenshotsFolder: path.join(__dirname, 'screenshots'),
    downloadsFolder: path.join(__dirname, 'downloads'),
    defaultCommandTimeout: 15000,
    retries: { runMode: 2, openMode: 0 },
  },
  viewportWidth: 1280,
  viewportHeight: 720,
  video: true,
  screenshotOnRunFailure: true,
});