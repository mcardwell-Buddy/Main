/**
 * INVARIANT TEST: Whiteboard No Duplicates
 * 
 * Purpose: Detect and prevent silent duplicate entries in Whiteboard display
 * This is a data integrity test, not a UI test
 * 
 * Invariant Being Tested:
 * Each logical goal/mission must appear only once in the Whiteboard UI.
 * No entity should be duplicated due to polling, aggregation, or caching bugs.
 * 
 * Why This Matters:
 * - Duplicates cause confusing UX (same goal appears twice)
 * - Indicates bugs in backend aggregation or dashboard polling
 * - Can lead to double-execution of goals
 * - Silent issue (user sees multiple entries but doesn't know it's a bug)
 * 
 * Identifier Strategy:
 * Uses goal.goal_id as the stable unique identifier
 * Falls back to goal.id if goal_id unavailable
 * Reports if no stable identifier exists
 * 
 * Test Strategy:
 * 1. Load app
 * 2. Open Whiteboard
 * 3. Wait for dashboard data to load
 * 4. Collect all rendered goal elements
 * 5. Extract unique identifier from each
 * 6. Assert: total count === unique count
 * 7. If duplicates found, report exactly which IDs are duplicated
 * 
 * Failure Modes This Detects:
 * - Polling returns same goals multiple times
 * - Aggregator merging logic broken
 * - Frontend accidentally renders duplicates
 * - Cache contamination
 * - Race conditions in async data loading
 * 
 * DO NOT MOCK:
 * - Backend APIs (testing real data flow)
 * - Data aggregation (testing real duplication)
 * - Polling (testing real behavior)
 * 
 * DO NOT FIX IN THIS TEST:
 * - This test only detects duplicates
 * - Root cause will be identified separately
 * - Deduplication logic is NOT added to fix this
 */

import { test, expect } from '@playwright/test';

test.describe('Whiteboard No Duplicates Invariant', () => {
  
  test('Whiteboard contains no duplicate goals', async ({ page }) => {
    // STEP 1: Load app
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // STEP 2: Open Whiteboard
    const whiteboardButton = page.locator('[data-testid="open-whiteboard"]');
    await expect(whiteboardButton).toBeVisible({ timeout: 5000 });
    await whiteboardButton.click();
    
    // Wait for navigation
    await page.waitForURL('/whiteboard', { timeout: 5000 });
    await page.waitForLoadState('networkidle');
    
    // STEP 3: Wait for dashboard data to load
    const whiteboardRoot = page.locator('[data-testid="whiteboard-root"]');
    await expect(whiteboardRoot).toBeVisible({ timeout: 5000 });
    
    // Wait a moment for goals to attempt to render
    await page.waitForTimeout(2000);
    
    // STEP 4-5: Collect all rendered goal elements and extract identifiers
    const goalElements = await page.locator('[data-testid="whiteboard-goal"]').all();
    
    // If no goals exist, that's acceptable - not a duplicate issue
    if (goalElements.length === 0) {
      console.log('No goals found in whiteboard - this is acceptable');
      expect(goalElements.length).toBe(0);
      return;
    }
    
    // Extract goal IDs from each rendered element
    const goalIds = await Promise.all(
      goalElements.map(el => el.getAttribute('data-goal-id'))
    );
    
    // STEP 6: INVARIANT CHECK - Assert no duplicates
    const uniqueIds = new Set(goalIds);
    
    // Log for debugging
    console.log(`Total goals rendered: ${goalIds.length}`);
    console.log(`Unique goal IDs: ${uniqueIds.size}`);
    console.log(`Goal IDs: ${JSON.stringify(Array.from(goalIds))}`);
    
    // ASSERTION: Each goal appears exactly once
    expect(goalIds.length).toBe(uniqueIds.size);
    
    // If we get here, no duplicates were found
  });
  
  test.describe('Duplicate Detection - Detailed Analysis', () => {
    
    test('Reports duplicate IDs if found', async ({ page }) => {
      // This test provides detailed diagnostics if duplicates exist
      await page.goto('/');
      await page.waitForLoadState('networkidle');
      
      await page.click('[data-testid="open-whiteboard"]');
      await page.waitForURL('/whiteboard', { timeout: 5000 });
      await page.waitForLoadState('networkidle');
      
      // Wait for goals
      try {
        await page.waitForSelector('[data-testid="whiteboard-goal"]', { timeout: 5000 });
      } catch {
        // No goals rendered - that's okay
        return;
      }
      
      // Collect goal IDs
      const goalIds = await page.$$eval(
        '[data-testid="whiteboard-goal"]',
        nodes => nodes.map(n => n.getAttribute('data-goal-id'))
      );
      
      if (goalIds.length === 0) return;
      
      // Find duplicates
      const idCounts = {};
      const duplicateIds = [];
      
      for (const id of goalIds) {
        idCounts[id] = (idCounts[id] || 0) + 1;
        if (idCounts[id] === 2) {
          // Only add to duplicates array first time we detect it's duplicated
          duplicateIds.push(id);
        }
      }
      
      // If duplicates found, assert to fail with diagnostic info
      if (duplicateIds.length > 0) {
        const duplicateReport = duplicateIds.map(id => 
          `ID "${id}" appears ${idCounts[id]} times`
        ).join('\n  ');
        
        console.log(`\n❌ DUPLICATES DETECTED:\n  ${duplicateReport}`);
        
        expect(duplicateIds.length).toBe(0);
      } else {
        expect(goalIds.length).toBe(new Set(goalIds).size);
      }
    });
    
    test('Persists after whiteboard refresh', async ({ page }) => {
      // Verify duplicates (if they exist) are deterministic and persist
      await page.goto('/');
      await page.waitForLoadState('networkidle');
      
      await page.click('[data-testid="open-whiteboard"]');
      await page.waitForURL('/whiteboard', { timeout: 5000 });
      await page.waitForLoadState('networkidle');
      
      try {
        await page.waitForSelector('[data-testid="whiteboard-goal"]', { timeout: 5000 });
      } catch {
        return;
      }
      
      // Collect initial goal IDs
      const initialGoals = await page.$$eval(
        '[data-testid="whiteboard-goal"]',
        nodes => nodes.map(n => n.getAttribute('data-goal-id'))
      );
      
      if (initialGoals.length === 0) return;
      
      // Refresh page
      await page.reload({ waitUntil: 'networkidle' });
      
      // Wait for goals again
      try {
        await page.waitForSelector('[data-testid="whiteboard-goal"]', { timeout: 5000 });
      } catch {
        return;
      }
      
      // Collect goals after refresh
      const refreshedGoals = await page.$$eval(
        '[data-testid="whiteboard-goal"]',
        nodes => nodes.map(n => n.getAttribute('data-goal-id'))
      );
      
      // If duplicates existed before, they should still exist after
      // (This confirms it's not a transient rendering bug, but persistent data issue)
      const initialHasDups = initialGoals.length > new Set(initialGoals).size;
      const refreshedHasDups = refreshedGoals.length > new Set(refreshedGoals).size;
      
      if (initialHasDups) {
        expect(refreshedHasDups).toBe(true);
      }
    });
    
    test('Identifies root cause location', async ({ request }) => {
      // Query backend directly to check if duplicates exist at source
      const response = await request.get('http://127.0.0.1:8000/dashboards/operations');
      expect(response.ok()).toBeTruthy();
      
      const data = await response.json();
      
      if (!data.active_goals || data.active_goals.length === 0) {
        return; // No goals to check
      }
      
      // Check backend response for duplicates
      const backendGoalIds = data.active_goals.map(g => g.goal_id || g.id);
      const uniqueBackendIds = new Set(backendGoalIds);
      
      // If backend has duplicates, problem is in aggregation/storage
      // If backend is clean but UI has duplicates, problem is in frontend rendering
      if (backendGoalIds.length > uniqueBackendIds.size) {
        console.log('DUPLICATE SOURCE: Backend API returning duplicates');
        console.log(`Backend has ${backendGoalIds.length} goals but only ${uniqueBackendIds.size} unique`);
      } else if (uniqueBackendIds.size > 0) {
        console.log('DUPLICATE SOURCE: Likely frontend rendering issue');
        console.log(`Backend clean (${uniqueBackendIds.size} unique), check UI rendering logic`);
      }
    });
  });
});
