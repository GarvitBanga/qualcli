import { test, expect } from "appwright";

test("Wikipedia Search Test", async ({ device }) => {
  // Wait for app to load and dismiss any initial screens
  try {
    await device.getByText("Skip").tap();
  } catch (e) {
    // Skip button might not be present, that's ok
  }

  // Find and tap search box
  const searchBox = device.getByText("Search Wikipedia", { exact: true });
  await searchBox.tap();

  // Type search query
  await searchBox.fill("Automation Testing");

  // Wait for and verify search results
  const results = await device.getByRole("listitem").all();
  expect(results.length).toBeGreaterThan(0);

  // Tap first result
  await results[0].tap();

  // Verify article content loaded
  const articleContent = await device.getByRole("article");
  await expect(articleContent).toBeVisible();

  // Verify article contains expected text
  const articleText = await articleContent.textContent();
  expect(articleText.toLowerCase()).toContain("automation");
}); 