// Slow test to demonstrate priority scheduling
const { test, expect } = require('@playwright/test');

test('Slow Priority Test', async ({ page }) => {
  console.log('Slow test started - this will take 15 seconds');
  
  // Simulate a longer test execution
  await new Promise(resolve => setTimeout(resolve, 15000)); // 15 second delay
  
  console.log('Slow test completed');
  expect(true).toBe(true);
}); 