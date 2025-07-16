// Priority Demo Test - simulates a 10 second test
const { test, expect } = require('@playwright/test');

test('Priority Demo Test', async ({ page }) => {
  // Simulate a longer test execution to see priority effects
  console.log('Priority demo test started');
  
  // Simulate test work
  await new Promise(resolve => setTimeout(resolve, 10000)); // 10 second delay
  
  console.log('Priority demo test completed');
  expect(true).toBe(true);
}); 