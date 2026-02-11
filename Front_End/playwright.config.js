// @ts-check
const { defineConfig, devices } = require('@playwright/test');

/**
 * Playwright Configuration for Buddy Invariant Testing
 * 
 * Purpose: Enforce system invariants and detect integration breakages
 * NOT for UI coverage - for truth detection
 */
module.exports = defineConfig({
  testDir: './tests',
  
  // Timeout settings
  timeout: 30 * 1000,
  expect: {
    timeout: 5000
  },
  
  // Fail fast - stop on first failure to surface issues immediately
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: 0, // No retries - failures must be deterministic
  workers: 1, // Serial execution for predictable state
  
  // Reporter configuration
  reporter: [
    ['list'],
    ['html', { open: 'never' }]
  ],
  
  // Shared settings for all projects
  use: {
    // Base URL for navigation
    baseURL: 'http://localhost:3000',
    
    // Capture on failure for diagnosis
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    
    // Headed mode for debugging (set to false for CI)
    headless: false,
    
    // Viewport
    viewport: { width: 1280, height: 720 },
    
    // Ignore HTTPS errors for local dev
    ignoreHTTPSErrors: true,
    
    // Action timeout
    actionTimeout: 10 * 1000,
  },

  // Configure projects for major browsers (chromium only for now)
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  // Web server configuration - start frontend automatically
  // Backend must already be running on port 8000
  webServer: {
    command: 'npm start',
    url: 'http://localhost:3000',
    reuseExistingServer: true,
    timeout: 120 * 1000,
  },
});
