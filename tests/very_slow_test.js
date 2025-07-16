// Very slow test for clear priority demonstration
const { test, expect } = require('@playwright/test');

test('Very Slow Priority Test', async ({ page }) => {
  console.log('Very slow test started - 20 seconds');
  
  // Simulate a very long test execution
  await new Promise(resolve => setTimeout(resolve, 20000)); // 20 second delay
  
  console.log('Very slow test completed');
  expect(true).toBe(true);
}); 