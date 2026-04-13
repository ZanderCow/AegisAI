/**
 * End-to-end coverage for the admin user-management table.
 *
 * Test Flow:
 * 1. Live Load: Admin opens /admin/users -> verifies API-created user appears with real timestamps.
 * 2. Inline Role Edit: Admin changes a user's role badge inline -> reloads -> verifies persisted badge.
 * 3. Immediate Delete: Admin removes a user without confirmation -> reloads -> verifies the user is gone.
 */
import { randomUUID } from 'crypto';
import { expect, test, type Locator, type Page } from '@playwright/test';
import {
  attachPageDebugLogging,
  createStandardUser,
  loginAsSeededRole,
  loginViaApi,
} from './helpers/auth';

function userRow(page: Page, email: string): Locator {
  return page.locator('tbody tr').filter({ hasText: email });
}

async function openAdminUsers(page: Page): Promise<void> {
  await page.goto('/admin/users');
  await expect(page).toHaveURL(/\/admin\/users$/);
  await expect(page.getByRole('heading', { name: 'User Management' })).toBeVisible();
}

async function searchForUser(page: Page, email: string): Promise<void> {
  const searchInput = page.getByPlaceholder('Search users...');
  await searchInput.fill('');
  await searchInput.fill(email);
}

test.beforeEach(({ page }) => {
  attachPageDebugLogging(page);
});

test.describe('Admin user management', () => {
  test('admin can load the users table from live backend data', async ({ page, request }) => {
    test.setTimeout(120_000);

    const runTag = `admin-users-load-${randomUUID().slice(0, 8)}`;
    const standardUser = await createStandardUser(request, runTag);
    await loginViaApi(request, standardUser);

    await loginAsSeededRole(page, 'admin');
    await openAdminUsers(page);
    await searchForUser(page, standardUser.email);

    const row = userRow(page, standardUser.email);
    await expect(row).toHaveCount(1);
    await expect(row).toContainText(standardUser.email);
    await expect(row.getByRole('button', { name: 'user', exact: true })).toBeVisible();
    await expect(row).not.toContainText('N/A');
    await expect(row).not.toContainText('Never');
  });

  test('admin can change a user role inline and the change persists after reload', async ({ page, request }) => {
    test.setTimeout(120_000);

    const runTag = `admin-users-role-${randomUUID().slice(0, 8)}`;
    const standardUser = await createStandardUser(request, runTag);

    await loginAsSeededRole(page, 'admin');
    await openAdminUsers(page);
    await searchForUser(page, standardUser.email);

    const row = userRow(page, standardUser.email);
    await expect(row).toHaveCount(1);
    await row.getByRole('button', { name: 'user', exact: true }).click();

    const roleSelect = row.locator('select');
    await expect(roleSelect).toBeVisible();
    await roleSelect.selectOption('security');

    await expect(row.getByRole('button', { name: 'security', exact: true })).toBeVisible();

    await page.reload();
    await openAdminUsers(page);
    await searchForUser(page, standardUser.email);

    const reloadedRow = userRow(page, standardUser.email);
    await expect(reloadedRow).toHaveCount(1);
    await expect(reloadedRow.getByRole('button', { name: 'security', exact: true })).toBeVisible();
  });

  test('admin can remove a user immediately and the deletion persists after reload', async ({ page, request }) => {
    test.setTimeout(120_000);

    const runTag = `admin-users-delete-${randomUUID().slice(0, 8)}`;
    const standardUser = await createStandardUser(request, runTag);

    await loginAsSeededRole(page, 'admin');
    await openAdminUsers(page);
    await searchForUser(page, standardUser.email);

    const row = userRow(page, standardUser.email);
    await expect(row).toHaveCount(1);
    await row.getByRole('button', { name: 'Remove' }).click();

    await expect(userRow(page, standardUser.email)).toHaveCount(0);

    await page.reload();
    await openAdminUsers(page);
    await searchForUser(page, standardUser.email);

    await expect(page.getByText('No users found')).toBeVisible();
    await expect(userRow(page, standardUser.email)).toHaveCount(0);
  });
});
