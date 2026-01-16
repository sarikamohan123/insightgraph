/**
 * Graph Extraction E2E Tests
 * ===========================
 *
 * Tests the main graph extraction flow from text input to visualization
 */

import { test, expect } from '@playwright/test';

// Helper to mock window.alert (required for Firefox compatibility)
async function mockAlerts(page: any) {
  await page.evaluate(() => {
    (window as any).__alertMessages = [];
    window.alert = (msg: string) => {
      (window as any).__alertMessages.push(msg);
    };
  });
}

// Helper to set up API key with mocked alerts (works in all browsers including Firefox)
async function setupApiKey(page: any, apiKey: string) {
  await mockAlerts(page);

  const apiKeyInput = page.locator('input[placeholder="Enter your API key"]');
  await apiKeyInput.fill(apiKey);
  await page.getByRole('button', { name: 'Save' }).click();

  // Wait for the key to be saved
  await expect(page.getByText('API key is configured')).toBeVisible();
}

test.describe('Graph Extraction Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should display the main page correctly', async ({ page }) => {
    // Check header
    await expect(page.locator('h1')).toContainText('InsightGraph');
    await expect(page.locator('header p')).toContainText('Transform text into interactive knowledge graphs');

    // Check form elements exist
    await expect(page.locator('#title')).toBeVisible();
    await expect(page.locator('#text')).toBeVisible();
    await expect(page.locator('#description')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Create Graph' })).toBeVisible();

    // Check sections exist
    await expect(page.getByRole('heading', { name: 'Create New Graph' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Saved Graphs' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Graph Visualization' })).toBeVisible();
  });

  test('should show character count for text input', async ({ page }) => {
    const textarea = page.locator('#text');

    // Initially shows 0 characters
    await expect(page.getByText('0 / 10,000 characters')).toBeVisible();

    // Type some text
    await textarea.fill('Hello World');
    await expect(page.getByText('11 / 10,000 characters')).toBeVisible();
  });

  test('should disable submit button when text is empty', async ({ page }) => {
    const submitButton = page.getByRole('button', { name: 'Create Graph' });

    // Button should be disabled when text is empty
    await expect(submitButton).toBeDisabled();

    // Button should be enabled after entering text
    await page.locator('#text').fill('Python is a programming language');
    await expect(submitButton).toBeEnabled();
  });

  test('should show validation error for empty text submission', async ({ page }) => {
    // Try to submit with only whitespace
    await page.locator('#text').fill('   ');

    // Button should still be disabled
    await expect(page.getByRole('button', { name: 'Create Graph' })).toBeDisabled();
  });

  test('should fill form and create a graph successfully', async ({ page }) => {
    // Set API key first (required for creating graphs)
    await setupApiKey(page, 'test-api-key');

    // Fill the form
    await page.locator('#title').fill('Python Knowledge Graph');
    await page.locator('#text').fill('Python is a programming language used for data science and machine learning. NumPy and Pandas are popular Python libraries.');
    await page.locator('#description').fill('A test graph about Python');

    // Submit the form
    await page.getByRole('button', { name: 'Create Graph' }).click();

    // Button should show loading state
    await expect(page.getByRole('button', { name: 'Creating Graph...' })).toBeVisible();

    // Wait for the graph to be created (with timeout for API response)
    // Look for the heading in the visualization section (right column)
    await expect(page.locator('.sticky h2').filter({ hasText: 'Python Knowledge Graph' })).toBeVisible({ timeout: 30000 });

    // Visualization should show node/edge counts
    await expect(page.locator('strong:has-text("Nodes:")')).toBeVisible();
    await expect(page.locator('strong:has-text("Edges:")')).toBeVisible();
  });

  test('should clear form after successful submission', async ({ page }) => {
    // Set API key
    await setupApiKey(page, 'test-api-key');

    // Fill and submit form
    await page.locator('#title').fill('Test Graph');
    await page.locator('#text').fill('React is a JavaScript library for building user interfaces');
    await page.locator('#description').fill('Test description');

    await page.getByRole('button', { name: 'Create Graph' }).click();

    // Wait for creation to complete
    await expect(page.getByRole('button', { name: 'Create Graph' })).toBeVisible({ timeout: 30000 });

    // Form should be cleared
    await expect(page.locator('#title')).toHaveValue('');
    await expect(page.locator('#text')).toHaveValue('');
    await expect(page.locator('#description')).toHaveValue('');
  });
});

test.describe('Graph Visualization', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should show placeholder when no graph is selected', async ({ page }) => {
    // The visualization section should show default heading
    await expect(page.getByRole('heading', { name: 'Graph Visualization' })).toBeVisible();
  });

  test('should display graph metadata when a graph is created', async ({ page }) => {
    // Set API key
    await setupApiKey(page, 'test-api-key');

    // Create a graph
    await page.locator('#text').fill('JavaScript and TypeScript are programming languages');
    await page.getByRole('button', { name: 'Create Graph' }).click();

    // Wait for creation and check metadata
    await expect(page.locator('strong:has-text("Nodes:")')).toBeVisible({ timeout: 30000 });
    await expect(page.locator('strong:has-text("Edges:")')).toBeVisible();
    await expect(page.locator('strong:has-text("Created:")')).toBeVisible();
  });
});
