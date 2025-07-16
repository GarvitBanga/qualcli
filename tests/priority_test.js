// Long-running test to demonstrate priority scheduling
const { test, expect } = require('@playwright/test');

test('Priority Test - Takes 30 seconds', async ({ page }) => {
  const startTime = new Date().toISOString();
  console.log(`Test started at: ${startTime}`);
  
  // Simulate a long test that takes 30 seconds
  await new Promise(resolve => setTimeout(resolve, 30000));
  
  const endTime = new Date().toISOString();
  console.log(`Test completed at: ${endTime}`);
  
  expect(true).toBe(true);
}); 