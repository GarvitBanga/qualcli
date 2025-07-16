// Demo test for high priority
const { test, expect } = require('@playwright/test');

test('High Priority Demo Test', async ({ page }) => {
  // Simple test that always passes
  expect(true).toBe(true);
  console.log('High priority test executed successfully!');
}); 