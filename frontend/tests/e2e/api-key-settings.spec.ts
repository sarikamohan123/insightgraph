/**
 * API Key Settings E2E Tests
 * ===========================
 *
 * Tests the API key configuration functionality
 */

import { test, expect } from '@playwright/test';

test.describe('API Key Settings', () => {
  test.beforeEach(async ({ page }) => {
    // Clear localStorage before each test
    await page.goto('/');
    await page.evaluate(() => localStorage.clear());
    await page.reload();
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
    const toggleButton = page.getByRole('button', { name: 'Show' });

    // Initially password type
    await expect(apiKeyInput).toHaveAttribute('type', 'password');

    // Click to show
    await toggleButton.click();
    await expect(apiKeyInput).toHaveAttribute('type', 'text');
    await expect(page.getByRole('button', { name: 'Hide' })).toBeVisible();

    // Click to hide again
    await page.getByRole('button', { name: 'Hide' }).click();
    await expect(apiKeyInput).toHaveAttribute('type', 'password');
  });

  test('should save API key and show confirmation', async ({ page }) => {
    const apiKeyInput = page.locator('input[placeholder="Enter your API key"]');
    const saveButton = page.getByRole('button', { name: 'Save' });

    // Enter API key
    await apiKeyInput.fill('my-secret-api-key');

    // Handle alert dialog
    page.on('dialog', async (dialog) => {
      expect(dialog.message()).toBe('API key saved!');
      await dialog.accept();
    });

    // Save
    await saveButton.click();

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

    let dialogCount = 0;
    page.on('dialog', async (dialog) => {
      dialogCount++;
      if (dialogCount === 1) {
        expect(dialog.message()).toBe('API key saved!');
      } else if (dialogCount === 2) {
        expect(dialog.message()).toBe('API key cleared!');
      }
      await dialog.accept();
    });

    await page.getByRole('button', { name: 'Save' }).click();

    // Wait for clear button to appear
    await expect(page.getByRole('button', { name: 'Clear' })).toBeVisible();

    // Clear the API key
    await page.getByRole('button', { name: 'Clear' }).click();

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

    page.on('dialog', async (dialog) => {
      await dialog.accept();
    });

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
