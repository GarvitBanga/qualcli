// Demo test for normal priority
const { test, expect } = require('@playwright/test');

test('Normal Priority Demo Test', async ({ page }) => {
  // Simple test that always passes
  expect(true).toBe(true);
  console.log('Normal priority test executed successfully!');
}); 