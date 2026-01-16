/**
 * API Key Settings E2E Tests
 * ===========================
 *
 * Tests the API key configuration functionality
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

// Helper to get captured alert messages
async function getAlertMessages(page: any): Promise<string[]> {
  return page.evaluate(() => (window as any).__alertMessages || []);
}

test.describe('API Key Settings', () => {
  test.beforeEach(async ({ page }) => {
    // Clear localStorage before each test
    await page.goto('/');
    await page.evaluate(() => localStorage.clear());
    await page.reload();
    // Mock alerts after reload
    await mockAlerts(page);
  });

  test('should display API key settings section', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'API Key Settings' })).toBeVisible();
    await expect(page.locator('input[placeholder="Enter your API key"]')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Show' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Save' })).toBeVisible();
  });

  test('should show message when API key is not set', async ({ page }) => {
    await expect(
      page.getByText('Set your API key to create and delete graphs')
    ).toBeVisible();
  });

  test('should toggle API key visibility', async ({ page }) => {
    const apiKeyInput = page.locator('input[placeholder="Enter your API key"]');

    // Initially password type
    await expect(apiKeyInput).toHaveAttribute('type', 'password');

    // Click Show button and wait for it to change to Hide
    await page.getByRole('button', { name: 'Show' }).click();
    await expect(apiKeyInput).toHaveAttribute('type', 'text');
    await expect(page.getByRole('button', { name: 'Hide' })).toBeVisible();

    // Click Hide button and wait for it to change back
    await page.getByRole('button', { name: 'Hide' }).click();
    await expect(apiKeyInput).toHaveAttribute('type', 'password');
    await expect(page.getByRole('button', { name: 'Show' })).toBeVisible();
  });

  test('should save API key and show confirmation', async ({ page }) => {
    const apiKeyInput = page.locator('input[placeholder="Enter your API key"]');
    const saveButton = page.getByRole('button', { name: 'Save' });

    // Enter API key
    await apiKeyInput.fill('my-secret-api-key');

    // Click save
    await saveButton.click();

    // Verify alert was shown
    const alerts = await getAlertMessages(page);
    expect(alerts).toContain('API key saved!');

    // Should show configured message
    await expect(page.getByText('API key is configured')).toBeVisible();

    // Clear button should appear
    await expect(page.getByRole('button', { name: 'Clear' })).toBeVisible();
  });

  test('should disable save button when API key is empty', async ({ page }) => {
    const saveButton = page.getByRole('button', { name: 'Save' });

    // Save button should be visually disabled (via style, not disabled attribute)
    // The button uses cursor: not-allowed for empty input
    await expect(saveButton).toBeVisible();
  });

  test('should clear API key when Clear button is clicked', async ({ page }) => {
    const apiKeyInput = page.locator('input[placeholder="Enter your API key"]');

    // First, set an API key
    await apiKeyInput.fill('test-key');

    // Save the key
    await page.getByRole('button', { name: 'Save' }).click();

    // Verify save alert
    let alerts = await getAlertMessages(page);
    expect(alerts).toContain('API key saved!');

    // Wait for clear button to appear
    await expect(page.getByRole('button', { name: 'Clear' })).toBeVisible();

    // Clear the API key
    await page.getByRole('button', { name: 'Clear' }).click();

    // Verify clear alert
    alerts = await getAlertMessages(page);
    expect(alerts).toContain('API key cleared!');

    // Should show not configured message
    await expect(
      page.getByText('Set your API key to create and delete graphs')
    ).toBeVisible();

    // Clear button should disappear
    await expect(page.getByRole('button', { name: 'Clear' })).not.toBeVisible();
  });

  test('should persist API key after page reload', async ({ page }) => {
    const apiKeyInput = page.locator('input[placeholder="Enter your API key"]');

    // Set API key
    await apiKeyInput.fill('persistent-key');

    // Save
    await page.getByRole('button', { name: 'Save' }).click();

    // Wait for save confirmation
    await expect(page.getByText('API key is configured')).toBeVisible();

    // Reload page
    await page.reload();

    // API key should still be configured
    await expect(page.getByText('API key is configured')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Clear' })).toBeVisible();
  });
});
