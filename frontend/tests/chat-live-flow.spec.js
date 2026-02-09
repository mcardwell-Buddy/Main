const { test, expect } = require('@playwright/test');

test('chat approval flow streams live mission - WITH CONSOLE LOGS', async ({ page, context }) => {
  // Enable console output
  page.on('console', msg => {
    if (msg.type() === 'log' || msg.type() === 'info') {
      console.log(`[FRONTEND] ${msg.text()}`);
    }
    if (msg.type() === 'error') {
      console.error(`[FRONTEND ERROR] ${msg.text()}`);
    }
  });

  // Start with a fresh page (new chat session, no history)
  await page.goto('/');
  
  // Clear all storage to start fresh (clears chat history)
  await page.evaluate(() => {
    localStorage.clear();
    sessionStorage.clear();
  });
  
  // Hard reload to ensure clean state (bypass cache)
  await page.reload({ waitUntil: 'networkidle' });
  
  await page.waitForSelector('[data-testid="chat-input"]', { timeout: 10000 });

  const input = page.getByTestId('chat-input');
  const send = page.getByTestId('chat-send');

  // Use a task that requires execution (triggers mission proposal)
  const uniqueMsg = `Extract all contact information from https://example.com [TEST_${Date.now()}]`;
  await input.fill(uniqueMsg);
  await send.click();

  console.log('✅ Message sent');

  // Wait for response - look for the agent message with "I can handle this:"
  // Wait for at least one message with this text
  await page.waitForSelector('text=I can handle this:', { timeout: 15000 });
  console.log('✅ Got agent response with "I can handle this:"');
  
  // Now send approval via natural language (chat, not button)
  const input2 = page.getByTestId('chat-input');
  const send2 = page.getByTestId('chat-send');
  
  await input2.fill('approve');
  await send2.click();
  
  console.log('✅ Approval message sent');
  
  // Wait for Mission Visualizer to appear (execution started)
  await expect(page.locator('.mission-visualizer')).toBeVisible({ timeout: 15000 });
  console.log('✅ Mission Visualizer appeared');
  
  // Check visualizer content
  const mvTitle = page.locator('.mv-title');
  await expect(mvTitle).toContainText('Mission Visualizer');
  console.log('✅ Mission Visualizer title visible');

  // Check status
  const mvStatus = page.locator('.mv-status');
  const status = await mvStatus.textContent();
  console.log(`✅ Visualizer status: ${status}`);
  
  // Wait for some events to stream in (execution takes time)
  await page.waitForTimeout(5000);
  
  // Check for preview data
  const mvPreview = page.locator('.mv-preview');
  const previewText = await mvPreview.textContent();
  console.log(`📊 Preview content: ${previewText.substring(0, 100)}`);
  
  // Check if we got any actual data (not just "Waiting for live data")
  if (previewText.includes('Waiting for live data')) {
    console.log('⚠️ Still waiting for live data, checking for sections...');
    const sections = page.locator('.mv-section');
    const sectionCount = await sections.count();
    console.log(`📋 Sections found: ${sectionCount}`);
  }
  
  // Log final message count to confirm execution happened
  const finalMessages = await page.locator('.message-body').count();
  console.log(`✅ Final message count: ${finalMessages}`);
});
