const { test, expect } = require('@playwright/test');

test('Wikipedia Language Switch Test', async ({ device }) => {
  // Wait for app to load
  await device.waitForSelector('~Settings');
  
  // Open settings
  await device.tap('~Settings');
  
  // Wait for and tap on Wikipedia languages
  await device.waitForSelector('~Wikipedia languages');
  await device.tap('~Wikipedia languages');
  
  // Add a new language
  await device.waitForSelector('~Add language');
  await device.tap('~Add language');
  
  // Search for Spanish
  await device.waitForSelector('~Search languages');
  await device.tap('~Search languages');
  await device.fill('~Search languages', 'Spanish');
  
  // Select Spanish (Español)
  await device.waitForSelector('~Español');
  await device.tap('~Español');
  
  // Go back to main screen
  await device.tap('~Navigate up');
  await device.tap('~Navigate up');
  
  // Verify Spanish is now in language list
  await device.waitForSelector('~Español');
  const spanishLanguage = await device.$('~Español');
  expect(spanishLanguage).toBeTruthy();
}); 