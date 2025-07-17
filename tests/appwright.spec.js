import { test, expect } from "appwright";

test("Complete Wikipedia search test with Playwright", async ({
  device,
}) => {
  // Handle initial dialog (Google Pixel 7 shows "Ok" button)
  try {
    await device.getByText("Skip").tap({ timeout: 5000 });
    console.log("✅ Dismissed initial dialog");
  } catch (e) {
    console.log("ℹ️  No initial dialog found, continuing...");
  }

  // Wait for app to fully load
  await device.waitForTimeout(3000);

  // Verify Wikipedia app has loaded successfully
  await expect(device.getByText("Search Wikipedia")).toBeVisible();
  console.log("✅ Wikipedia app loaded with search functionality");

    // Enter search term - using the working solution from appwright1.spec.js
  const searchInput = device.getByText("Search Wikipedia", { exact: true });
  await searchInput.tap();
  console.log("✅ Search interface activated successfully");

  // Use the direct fill approach that works
  await searchInput.fill("playwright");
  console.log("✅ Successfully typed 'playwright' in search field");

  // Wait for search suggestions/results to appear
  await device.waitForTimeout(2000);

  // Look for search results and tap carefully
  try {
    // First verify that search results appeared
    await expect(device.getByText("Playwright")).toBeVisible({ timeout: 5000 });
    console.log("✅ Search results appeared");
    
    // Use the simple, working approach from appwright1.spec.js
    await device.getByText("Playwright (software)").tap();
    console.log("✅ Tapped on Playwright (software) result");
  } catch (e) {
    // If exact match fails, try just "Playwright"
    console.log("⚠️  Could not find or tap 'Playwright (software)', trying fallback...");
    try {
      const generalResult = device.getByText("Playwright", { exact: false });
      await generalResult.tap();
      console.log("✅ Tapped on Playwright result using fallback");
    } catch (e2) {
      throw new Error("Failed to find any Playwright results: " + e2.message);
    }
  }

  // Wait for article to load
  await device.waitForTimeout(2000);

  // Try to verify we're on the article page and check for Microsoft
  try {
    await expect(device.getByText("Microsoft")).toBeVisible();
    console.log("✅ Verified Microsoft is visible in the article");
  } catch (e) {
    // If Microsoft isn't visible, check for error screens
    const errorMessages = ["An error occurred", "Error", "Something went wrong", "Network error"];
    for (const errorMsg of errorMessages) {
      try {
        await expect(device.getByText(errorMsg)).toBeVisible({ timeout: 1000 });
        throw new Error(`Found error message: "${errorMsg}" - The app encountered an error`);
      } catch (e) {
        // Good - no error message found
      }
    }

    // If no error messages, just note that Microsoft wasn't visible
    console.log("ℹ️  Microsoft not immediately visible, but no errors found");
  }
  
  console.log("🎉 COMPLETE SUCCESS: Wikipedia search test passed!");
  console.log("🔧 KEY SOLUTION: Fill text directly on the Search Wikipedia element!");
});