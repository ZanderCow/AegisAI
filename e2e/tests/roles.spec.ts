/**
 * Verifies route guards and sidebar visibility for each supported role.
 *
 * The matrix intentionally mixes direct URL navigation and sidebar checks so
 * we cover both authorization middleware and role-aware navigation chrome.
 */
import { test, expect } from '@playwright/test';
import {
  attachPageDebugLogging,
  createAndLoginUser,
  loginAsSeededRole,
} from './helpers/auth';

test.beforeEach(({ page }) => {
  // Keep browser logs attached because authorization failures are often client-side.
  attachPageDebugLogging(page);
});

/** Covers the default end-user experience after signup or standard login. */

test.describe('Role: user', () => {
  test('can access /chat', async ({ page, request }) => {
    await createAndLoginUser(page, request, 'roles-user-chat');
    await page.goto('/chat');
    await expect(page).toHaveURL(/\/chat$/);
  });

  test('can access /documents', async ({ page, request }) => {
    await createAndLoginUser(page, request, 'roles-user-docs');
    await page.goto('/documents');
    await expect(page).toHaveURL(/\/documents$/);
  });

  test('is redirected to /forbidden when accessing /admin/dashboard', async ({ page, request }) => {
    await createAndLoginUser(page, request, 'roles-user-admin');
    await page.goto('/admin/dashboard');
    await expect(page).toHaveURL(/\/forbidden$/);
  });

  test('is redirected to /forbidden when accessing /security/dashboard', async ({ page, request }) => {
    await createAndLoginUser(page, request, 'roles-user-security');
    await page.goto('/security/dashboard');
    await expect(page).toHaveURL(/\/forbidden$/);
  });

  test('sidebar shows Chat and RAG Documents', async ({ page, request }) => {
    await createAndLoginUser(page, request, 'roles-user-sidebar');
    await page.goto('/chat');
    await expect(page.getByRole('link', { name: 'Chat' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'RAG Documents' })).toBeVisible();
  });

  test('sidebar does not show admin or security items', async ({ page, request }) => {
    await createAndLoginUser(page, request, 'roles-user-nav');
    await page.goto('/chat');
    await expect(page.getByRole('link', { name: 'Dashboard', exact: true })).not.toBeVisible();
    await expect(page.getByRole('link', { name: 'Security Logs' })).not.toBeVisible();
    await expect(page.getByRole('link', { name: 'Security Dashboard' })).not.toBeVisible();
    await expect(page.getByRole('link', { name: 'Document Access' })).not.toBeVisible();
  });
});

/** Covers privileged navigation and route access expected for admins. */

test.describe('Role: admin', () => {
  test('can access /chat', async ({ page }) => {
    await loginAsSeededRole(page, 'admin');
    await page.goto('/chat');
    await expect(page).toHaveURL(/\/chat$/);
  });

  test('can access /documents', async ({ page }) => {
    await loginAsSeededRole(page, 'admin');
    await page.goto('/documents');
    await expect(page).toHaveURL(/\/documents$/);
  });

  test('can access /admin/dashboard', async ({ page }) => {
    await loginAsSeededRole(page, 'admin');
    await page.goto('/admin/dashboard');
    await expect(page).toHaveURL(/\/admin\/dashboard$/);
  });

  test('can access /admin/roles', async ({ page }) => {
    await loginAsSeededRole(page, 'admin');
    await page.goto('/admin/roles');
    await expect(page).toHaveURL(/\/admin\/roles$/);
  });

  test('can access /admin/users', async ({ page }) => {
    await loginAsSeededRole(page, 'admin');
    await page.goto('/admin/users');
    await expect(page).toHaveURL(/\/admin\/users$/);
  });

  test('is redirected to /forbidden when accessing /security/dashboard', async ({ page }) => {
    await loginAsSeededRole(page, 'admin');
    await page.goto('/security/dashboard');
    await expect(page).toHaveURL(/\/forbidden$/);
  });

  test('can access /security/documents', async ({ page }) => {
    await loginAsSeededRole(page, 'admin');
    await page.getByRole('link', { name: 'Document Access' }).click();
    await expect(page).toHaveURL(/\/security\/documents$/);
  });

  test('sidebar shows all navigation items', async ({ page }) => {
    await loginAsSeededRole(page, 'admin');
    await page.goto('/chat');
    await expect(page.getByRole('link', { name: 'Chat' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'RAG Documents' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Dashboard', exact: true })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Roles' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Users' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Security Logs' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Security Dashboard' })).not.toBeVisible();
    await expect(page.getByRole('link', { name: 'Document Access' })).toBeVisible();
  });
});

/** Covers the restricted security-only workspace and its forbidden paths. */

test.describe('Role: security', () => {
  test('can access /security/dashboard', async ({ page }) => {
    await loginAsSeededRole(page, 'security');
    await page.goto('/security/dashboard');
    await expect(page).toHaveURL(/\/security\/dashboard$/);
  });

  test('can access /security/documents', async ({ page }) => {
    await loginAsSeededRole(page, 'security');
    await page.goto('/security/documents');
    await expect(page).toHaveURL(/\/security\/documents$/);
  });

  test('can access /documents', async ({ page }) => {
    await loginAsSeededRole(page, 'security');
    await page.goto('/documents');
    await expect(page).toHaveURL(/\/documents$/);
  });

  test('cannot access /chat and is redirected to /forbidden', async ({ page }) => {
    await loginAsSeededRole(page, 'security');
    await page.goto('/chat');
    await expect(page).toHaveURL(/\/forbidden$/);
  });

  test('is redirected to /forbidden when accessing /admin/dashboard', async ({ page }) => {
    await loginAsSeededRole(page, 'security');
    await page.goto('/admin/dashboard');
    await expect(page).toHaveURL(/\/forbidden$/);
  });

  test('sidebar shows security items', async ({ page }) => {
    await loginAsSeededRole(page, 'security');
    await page.goto('/security/dashboard');
    await expect(page.getByRole('link', { name: 'Security Logs' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Security Dashboard' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Document Access' })).toBeVisible();
  });

  test('sidebar does not show chat or admin-only items', async ({ page }) => {
    await loginAsSeededRole(page, 'security');
    await page.goto('/security/dashboard');
    await expect(page.getByRole('link', { name: 'Chat' })).not.toBeVisible();
    await expect(page.getByRole('link', { name: 'Dashboard', exact: true })).not.toBeVisible();
    await expect(page.getByRole('link', { name: 'Roles' })).not.toBeVisible();
    await expect(page.getByRole('link', { name: 'Users' })).not.toBeVisible();
  });
});
