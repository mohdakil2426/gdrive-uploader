const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();

  // Listen for console messages
  page.on('console', msg => console.log('BROWSER:', msg.text()));

  // Navigate to local web UI
  await page.goto('http://localhost:8080');
  console.log('Page loaded');

  // Wait for page to be ready
  await page.waitForTimeout(1000);

  // Enter the Pinggy URL
  const serverUrl = 'https://gccaf-136-119-80-128.a.free.pinggy.link';
  await page.fill('#server-url', serverUrl);
  console.log('Entered server URL:', serverUrl);

  // Click connect button
  await page.click('#connect-btn');
  console.log('Clicked Connect');

  // Wait and check for result
  await page.waitForTimeout(3000);

  // Check connection status
  const statusText = await page.textContent('#status-text');
  console.log('Status:', statusText);

  // Check for any error messages
  const toasts = await page.locator('.toast, [class*="error"], [class*="alert"]').allTextContents();
  if (toasts.length > 0) {
    console.log('Messages:', toasts);
  }

  // Keep browser open for inspection
  console.log('Browser open - check for errors. Press Ctrl+C to close.');
  await page.waitForTimeout(60000);

  await browser.close();
})();
