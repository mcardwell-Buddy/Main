process.chdir("C:\\Users\\micha\\Buddy\\frontend");
const { chromium } = require("playwright");

(async () => {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();
  const consoleErrors = [];
  
  page.on("console", msg => {
    if (msg.type() === "error") consoleErrors.push(msg.text());
    console.log("[console]", msg.type(), msg.text());
  });
  
  page.on("pageerror", err => {
    consoleErrors.push(err.message);
    console.log("[pageerror]", err.message);
  });
  
  try {
    console.log("Opening Buddy UI...");
    await page.goto("http://localhost:3000", { waitUntil: "domcontentloaded" });
    
    console.log("Waiting for chat input...");
    await page.waitForSelector("[data-testid=\"chat-input\"]", { timeout: 20000 });
    
    const sendMessage = async (text) => {
      console.log(`Sending message: ${text}`);
      await page.fill("[data-testid=\"chat-input\"]", text);
      await page.click("[data-testid=\"chat-send\"]");
      await page.waitForTimeout(2000);
    };
    
    // Test 1: Navigate
    await sendMessage("Navigate to https://www.cardwellassociates.com");
    
    // Wait for mission ready or error
    try {
      await page.waitForSelector("text=Mission ready", { timeout: 60000 });
      console.log("✓ Mission ready detected");
      
      // Approve
      await sendMessage("yes");
      
      // Wait for execution
      await page.waitForSelector("text=Approved and executed", { timeout: 120000 });
      console.log("✓ Navigation executed");
    } catch (e) {
      console.log("⚠ Navigation did not complete as expected:", e.message);
    }
    
    // Test 2: Extract
    await page.waitForTimeout(2000);
    await sendMessage("Extract the company phone number from https://www.cardwellassociates.com");
    await page.waitForTimeout(15000);
    
    // Check results
    const lastMessages = await page.locator(".message-text").allTextContents();
    console.log("\n=== LAST 6 MESSAGES ===");
    lastMessages.slice(-6).forEach((msg, i) => console.log(`${i + 1}. ${msg.substring(0, 200)}`));
    
    console.log("\n=== CONSOLE ERRORS ===");
    if (consoleErrors.length > 0) {
      consoleErrors.forEach(err => console.log(`❌ ${err}`));
    } else {
      console.log("✅ No console errors detected");
    }
    
    await page.waitForTimeout(5000);
    await browser.close();
    
  } catch (err) {
    console.error("❌ Test failed:", err.message);
    await browser.close();
    process.exit(1);
  }
})();
