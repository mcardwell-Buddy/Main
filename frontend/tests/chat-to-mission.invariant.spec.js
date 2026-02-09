/**
 * INVARIANT TEST: Chat Intent → Mission Creation → Whiteboard Display
 * 
 * Purpose: Enforce end-to-end flow from user intent to visible mission
 * This is NOT a UI coverage test - it's a truth detection test for the complete pipeline
 * 
 * Invariant Being Tested:
 * If a user enters an actionable intent via chat, it MUST surface as a mission/goal
 * visible in the Whiteboard UI within a reasonable time window.
 * 
 * Why This Matters:
 * - Validates the complete chat → backend → mission → whiteboard pipeline
 * - Detects breakages in intent classification
 * - Catches mission persistence failures
 * - Validates dashboard aggregation logic
 * - Ensures UI rendering of backend state
 * 
 * Test Strategy:
 * 1. Load chat interface
 * 2. Send actionable intent that should create a mission
 * 3. Wait for backend processing
 * 4. Navigate to whiteboard
 * 5. Assert mission/goal is visible in whiteboard UI
 * 
 * Failure Modes This Detects:
 * - Chat handler not processing messages
 * - Intent classification failing
 * - Mission not being created in backend
 * - Mission not persisted to storage
 * - Dashboard API not returning missions
 * - Whiteboard UI not rendering missions
 * - Signal emission failures
 * - Race conditions in async processing
 * 
 * DO NOT MOCK:
 * - Backend APIs (testing real integration)
 * - Message processing (testing real flow)
 * - Mission creation (testing real persistence)
 * - Dashboard aggregation (testing real queries)
 */

import { test, expect } from '@playwright/test';

// Pre-condition: Backend must be running on port 8000, Frontend on port 3000
// Start servers manually before running this test:
//   Terminal 1: cd C:\Users\micha\Buddy && python backend/main.py
//   Terminal 2: cd C:\Users\micha\Buddy\frontend && npm start

test.describe('Chat to Mission Invariant', () => {
  
  test('User intent creates visible mission in Whiteboard', async ({ page }) => {
    // STEP 1: Load chat interface
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Verify chat is loaded
    const chatInput = page.locator('[data-testid="chat-input"]');
    const chatSend = page.locator('[data-testid="chat-send"]');
    await expect(chatInput).toBeVisible({ timeout: 5000 });
    await expect(chatSend).toBeVisible();
    
    // STEP 2: Send actionable intent that should create a mission
    // Using a clear, unambiguous request that should trigger mission creation
    const testIntent = 'Extract pricing information from competitor websites and analyze market positioning';
    
    await chatInput.fill(testIntent);
    await chatSend.click();
    
    // STEP 3: Wait for backend processing
    // The backend needs time to:
    // - Receive message via /chat/integrated
    // - Classify intent
    // - Route to appropriate handler
    // - Create mission proposal
    // - Emit signals
    // - Update whiteboard state
    await page.waitForTimeout(3000); // Allow backend processing time
    
    // Additional verification: Look for agent response
    // This confirms the message was processed
    await page.waitForSelector('.message.agent', { timeout: 10000 });
    
    // STEP 4: Navigate to whiteboard
    const whiteboardButton = page.locator('[data-testid="open-whiteboard"]');
    await expect(whiteboardButton).toBeVisible();
    await whiteboardButton.click();
    
    await page.waitForURL('/whiteboard', { timeout: 5000 });
    await page.waitForLoadState('networkidle');
    
    // Wait for whiteboard to load and fetch data
    const whiteboardRoot = page.locator('[data-testid="whiteboard-root"]');
    await expect(whiteboardRoot).toBeVisible({ timeout: 5000 });
    
    // STEP 5: INVARIANT CHECK - Mission MUST be visible
    // Check for active goals count > 0
    const goalsCount = page.locator('[data-testid="active-goals-count"]');
    await expect(goalsCount).toBeVisible({ timeout: 5000 });
    
    // Get the actual count
    const countText = await goalsCount.textContent();
    const count = parseInt(countText || '0', 10);
    
    // CRITICAL ASSERTION: At least one goal should exist
    expect(count).toBeGreaterThan(0);
    
    // Verify the goals list is visible (rendered)
    const goalsList = page.locator('[data-testid="goals-list"]');
    await expect(goalsList).toBeVisible({ timeout: 5000 });
    
    // Verify at least one goal item exists
    const goalItems = goalsList.locator('.goal-item');
    const goalCount = await goalItems.count();
    expect(goalCount).toBeGreaterThan(0);
    
    // Verify goal has content (not empty)
    const firstGoal = goalItems.first();
    const goalTitle = firstGoal.locator('.goal-title');
    await expect(goalTitle).toBeVisible();
    const titleText = await goalTitle.textContent();
    expect(titleText).toBeTruthy();
    expect(titleText.length).toBeGreaterThan(0);
  });
  
  test.describe('Failure Diagnosis Helpers', () => {
    // These tests help diagnose WHERE in the pipeline the invariant fails
    
    test('Chat message API is reachable', async ({ request }) => {
      // Test that the chat endpoint exists
      const response = await request.post('http://127.0.0.1:8000/chat/integrated', {
        data: {
          user_id: 'test_user',
          session_id: 'test_session',
          message: 'Hello',
          source: 'web_ui'
        }
      });
      
      // Should return 200 or similar success code
      expect(response.status()).toBeLessThan(500);
    });
    
    test('Dashboard operations endpoint returns goals', async ({ request }) => {
      // Test that the dashboard API can return goal data in correct format
      const response = await request.get('http://127.0.0.1:8000/dashboards/operations');
      expect(response.ok()).toBeTruthy();
      
      const data = await response.json();
      expect(data).toHaveProperty('active_goals');
      expect(data).toHaveProperty('active_goals_count');
      
      // Validate schema: active_goals MUST be array
      expect(Array.isArray(data.active_goals)).toBeTruthy();
      
      // Validate schema: active_goals_count MUST be number
      expect(typeof data.active_goals_count).toBe('number');
    });
    
    test('Whiteboard fetches dashboard data on load', async ({ page }) => {
      // Monitor network requests to verify dashboard API is called
      const dashboardRequests = [];
      page.on('request', request => {
        if (request.url().includes('/dashboards/operations')) {
          dashboardRequests.push(request);
        }
      });
      
      await page.goto('/whiteboard');
      await page.waitForLoadState('networkidle');
      
      // Verify at least one dashboard request was made
      expect(dashboardRequests.length).toBeGreaterThan(0);
    });
    
    test('Chat form is functional', async ({ page }) => {
      await page.goto('/');
      await page.waitForLoadState('networkidle');
      
      const chatInput = page.locator('[data-testid="chat-input"]');
      const chatSend = page.locator('[data-testid="chat-send"]');
      
      // Verify form elements are interactive
      await chatInput.fill('Test message');
      await expect(chatSend).not.toBeDisabled();
      
      const inputValue = await chatInput.inputValue();
      expect(inputValue).toBe('Test message');
    });
  });
});
