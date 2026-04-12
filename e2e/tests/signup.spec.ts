/**
 * Exercises the public signup flow for newly created end users.
 *
 * Test Flow:
 * 1. Successful Signup: Navigate to /signup -> Generate unique user -> Submit -> Verify /chat redirect + JWT.
 * 2. Duplicate Validation: Submit existing admin email -> Verify "Email already registered" error.
 */
import { test, expect } from '@playwright/test';
import { randomUUID } from 'crypto';
import {
  TEST_USER_PASSWORD,
  attachPageDebugLogging,
  getSeededCredentials,
} from './helpers/auth';

test.beforeEach(({ page }) => {
  // Surface browser-side errors in CI output when signup assertions fail.
  attachPageDebugLogging(page);
});

test.describe('Signup flow', () => {
  test('successful signup', async ({ page }) => {
    await page.goto('/signup');

    // Each run creates a unique address because successful signups persist.
    const uniqueEmail = `user_${randomUUID().substring(0, 8)}@example.com`;

    await page.getByLabel('Email').fill(uniqueEmail);
    await page.getByLabel('Password', { exact: true }).fill(TEST_USER_PASSWORD);
    await page.getByLabel('Confirm Password').fill(TEST_USER_PASSWORD);

    await page.getByRole('button', { name: 'Sign Up' }).click();

    await expect(page).toHaveURL(/\/chat$/);
    const token = await page.evaluate(() => localStorage.getItem('aegis_token'));
    expect(token).toBeTruthy();
  });

  test('duplicate email signup shows a validation error for a seeded admin user', async ({ page }) => {
    const admin = getSeededCredentials('admin');

    await page.goto('/signup');
    await page.getByLabel('Email').fill(admin.email);
    await page.getByLabel('Password', { exact: true }).fill(TEST_USER_PASSWORD);
    await page.getByLabel('Confirm Password').fill(TEST_USER_PASSWORD);

    await page.getByRole('button', { name: 'Sign Up' }).click();

    await expect(page.locator('p.text-red-400.bg-red-900\\/30')).toContainText('Email already registered');
    await expect(page).toHaveURL(/\/signup$/);
  });
});
