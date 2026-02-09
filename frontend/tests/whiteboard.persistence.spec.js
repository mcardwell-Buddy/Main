/**
 * INVARIANT TEST: Whiteboard Persistence
 * 
 * Purpose: Enforce that the Whiteboard state persists across browser refreshes
 * This is NOT a UI coverage test - it's a truth detection test for system architecture
 * 
 * Invariant Being Tested:
 * If a user navigates to the Whiteboard, it MUST remain visible after a browser refresh.
 * This validates that routing state and localStorage persistence work correctly.
 * 
 * Why This Matters:
 * - Detects routing configuration breakages
 * - Validates localStorage persistence architecture
 * - Catches navigation regressions immediately
 * - Ensures user experience continuity
 * 
 * Test Strategy:
 * 1. Load app (default route: chat)
 * 2. Navigate to whiteboard via UI interaction (click Buddy avatar)
 * 3. Assert whiteboard is visible
 * 4. Perform hard browser refresh
 * 5. Assert whiteboard is STILL visible (invariant holds)
 * 
 * Failure Modes This Detects:
 * - Routing not configured correctly
 * - localStorage not persisting UI state
 * - Navigation state lost on refresh
 * - React Router configuration broken
 * 
 * DO NOT MOCK:
 * - Backend APIs (real servers must be running)
 * - localStorage (testing real browser behavior)
 * - Navigation (testing real routing)
 */

import { test, expect } from '@playwright/test';

// Pre-condition: Backend must be running on port 8000, Frontend on port 3000
// Start servers manually before running this test:
//   Terminal 1: cd C:\Users\micha\Buddy && python backend/main.py
//   Terminal 2: cd C:\Users\micha\Buddy\frontend && npm start

test.describe('Whiteboard Persistence Invariant', () => {
  
  test('Whiteboard persists across browser refresh', async ({ page }) => {
    // STEP 1: Start at root (chat interface)
    await page.goto('/');
    
    // Wait for page to be fully loaded
    await page.waitForLoadState('networkidle');
    
    // Verify we're on the chat page initially (Buddy avatar should be visible)
    const buddyAvatar = page.locator('[data-testid="open-whiteboard"]');
    await expect(buddyAvatar).toBeVisible({ timeout: 5000 });
    
    // STEP 2: Navigate to whiteboard via UI interaction (click Buddy avatar)
    await buddyAvatar.click();
    
    // Wait for navigation to complete
    await page.waitForURL('/whiteboard', { timeout: 5000 });
    
    // STEP 3: Assert whiteboard is visible
    const whiteboardRoot = page.locator('[data-testid="whiteboard-root"]');
    await expect(whiteboardRoot).toBeVisible({ timeout: 5000 });
    
    // Verify URL is correct
    expect(page.url()).toContain('/whiteboard');
    
    // STEP 4: Perform hard browser refresh
    await page.reload({ waitUntil: 'networkidle' });
    
    // STEP 5: INVARIANT CHECK - Whiteboard MUST still be visible
    await expect(whiteboardRoot).toBeVisible({ timeout: 5000 });
    
    // Verify URL is STILL /whiteboard (routing persisted)
    expect(page.url()).toContain('/whiteboard');
    
    // Additional verification: Check that whiteboard container has loaded content
    // This ensures it's not just an empty div but actually rendered the component
    const containerClass = await whiteboardRoot.getAttribute('class');
    expect(containerClass).toContain('whiteboard-container');
  });
  
  test.describe('Failure Diagnosis Helpers', () => {
    // These tests help diagnose WHY the invariant might fail
    
    test('Backend is reachable', async ({ request }) => {
      const response = await request.get('http://127.0.0.1:8000/dashboards/operations');
      expect(response.ok()).toBeTruthy();
    });
    
    test('Frontend serves static assets', async ({ page }) => {
      await page.goto('/');
      await page.waitForLoadState('domcontentloaded');
      
      // Verify React app loaded
      const appElement = page.locator('.App');
      await expect(appElement).toBeAttached();
    });
    
    test('React Router is configured', async ({ page }) => {
      // Test that both routes exist
      await page.goto('/');
      await expect(page.locator('.App')).toBeAttached();
      
      await page.goto('/whiteboard');
      await expect(page.locator('.App')).toBeAttached();
    });
  });
});
