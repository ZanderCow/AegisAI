/**
 * Covers the seeded-role login flows used throughout the E2E suite.
 *
 * Test Flow:
 * 1. Role Login: Submit credentials (Admin/Security) -> Verify specific dashboard redirects.
 * 2. Auth Failure: Submit invalid password -> Verify error visibility and page retention.
 */
import { test, expect } from '@playwright/test';
import {
  attachPageDebugLogging,
  getSeededCredentials,
  loginAsSeededRole,
  submitLoginForm,
} from './helpers/auth';

test.beforeEach(({ page }) => {
  // Surface browser-side errors in CI output when a login redirect fails.
  attachPageDebugLogging(page);
});

test.describe('Login flow', () => {
  test('admin can log in and is redirected to the admin dashboard', async ({ page }) => {
    const credentials = await loginAsSeededRole(page, 'admin');

    await expect(page).toHaveURL(/\/admin\/dashboard$/);
    await expect(page.getByRole('complementary')).toContainText(credentials.email);
    await expect(page.getByRole('button', { name: 'Logout' })).toBeVisible();
  });

  test('security can log in and is redirected to the security dashboard', async ({ page }) => {
    const credentials = await loginAsSeededRole(page, 'security');

    await expect(page).toHaveURL(/\/security\/dashboard$/);
    await expect(page.getByRole('complementary')).toContainText(credentials.email);
    await expect(page.getByRole('button', { name: 'Logout' })).toBeVisible();
  });

  test('invalid credentials show an error', async ({ page }) => {
    const credentials = getSeededCredentials('admin');

    await submitLoginForm(page, credentials.email, `${credentials.password}-wrong`);

    await expect(page.locator('p.text-red-400.bg-red-900\\/30')).toBeVisible();
    await expect(page).toHaveURL(/\/login$/);
  });
});
