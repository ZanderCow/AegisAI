import { test, expect, type Page } from '@playwright/test';

// Build a fake JWT the frontend can decode (signature is ignored by the client).
function makeFakeJWT(payload: Record<string, unknown>): string {
    const header = Buffer.from(JSON.stringify({ alg: 'HS256', typ: 'JWT' })).toString('base64');
    const body = Buffer.from(JSON.stringify(payload)).toString('base64');
    return `${header}.${body}.fakesig`;
}

function tokenFor(role: string): string {
    return makeFakeJWT({
        sub: `e2e-${role}-id`,
        email: `${role}@example.com`,
        role,
        exp: Math.floor(Date.now() / 1000) + 3600,
    });
}

async function setAuth(page: Page, role: string) {
    const token = tokenFor(role);
    await page.addInitScript(
        ({ t }) => { localStorage.setItem('aegis_token', t); },
        { t: token },
    );
}

test.beforeEach(({ page }) => {
    page.on('console', msg => console.log('BROWSER:', msg.text()));
    page.on('pageerror', err => console.log('PAGE ERROR:', err.message));
});

// ---------------------------------------------------------------------------
// user role
// ---------------------------------------------------------------------------

test.describe('Role: user', () => {
    test('can access /chat', async ({ page }) => {
        await setAuth(page, 'user');
        await page.goto('/chat');
        await expect(page).toHaveURL(/\/chat/);
    });

    test('can access /documents', async ({ page }) => {
        await setAuth(page, 'user');
        await page.goto('/documents');
        await expect(page).toHaveURL(/\/documents/);
    });

    test('is redirected to /forbidden when accessing /admin/dashboard', async ({ page }) => {
        await setAuth(page, 'user');
        await page.goto('/admin/dashboard');
        await expect(page).toHaveURL(/\/forbidden/);
    });

    test('is redirected to /forbidden when accessing /security/dashboard', async ({ page }) => {
        await setAuth(page, 'user');
        await page.goto('/security/dashboard');
        await expect(page).toHaveURL(/\/forbidden/);
    });

    test('sidebar shows Chat and RAG Documents', async ({ page }) => {
        await setAuth(page, 'user');
        await page.goto('/chat');
        await expect(page.getByRole('link', { name: 'Chat' })).toBeVisible();
        await expect(page.getByRole('link', { name: 'RAG Documents' })).toBeVisible();
    });

    test('sidebar does not show admin or security items', async ({ page }) => {
        await setAuth(page, 'user');
        await page.goto('/chat');
        await expect(page.getByRole('link', { name: 'Dashboard' })).not.toBeVisible();
        await expect(page.getByRole('link', { name: 'Security Logs' })).not.toBeVisible();
        await expect(page.getByRole('link', { name: 'Security Dashboard' })).not.toBeVisible();
        await expect(page.getByRole('link', { name: 'Document Access' })).not.toBeVisible();
    });
});

// ---------------------------------------------------------------------------
// admin role
// ---------------------------------------------------------------------------

test.describe('Role: admin', () => {
    test('can access /chat', async ({ page }) => {
        await setAuth(page, 'admin');
        await page.goto('/chat');
        await expect(page).toHaveURL(/\/chat/);
    });

    test('can access /documents', async ({ page }) => {
        await setAuth(page, 'admin');
        await page.goto('/documents');
        await expect(page).toHaveURL(/\/documents/);
    });

    test('can access /admin/dashboard', async ({ page }) => {
        await setAuth(page, 'admin');
        await page.goto('/admin/dashboard');
        await expect(page).toHaveURL(/\/admin\/dashboard/);
    });

    test('can access /admin/roles', async ({ page }) => {
        await setAuth(page, 'admin');
        await page.goto('/admin/roles');
        await expect(page).toHaveURL(/\/admin\/roles/);
    });

    test('can access /admin/users', async ({ page }) => {
        await setAuth(page, 'admin');
        await page.goto('/admin/users');
        await expect(page).toHaveURL(/\/admin\/users/);
    });

    test('can access /security/dashboard', async ({ page }) => {
        await setAuth(page, 'admin');
        await page.goto('/security/dashboard');
        await expect(page).toHaveURL(/\/security\/dashboard/);
    });

    test('can access /security/documents', async ({ page }) => {
        await setAuth(page, 'admin');
        await page.goto('/security/documents');
        await expect(page).toHaveURL(/\/security\/documents/);
    });

    test('sidebar shows all navigation items', async ({ page }) => {
        await setAuth(page, 'admin');
        await page.goto('/chat');
        await expect(page.getByRole('link', { name: 'Chat' })).toBeVisible();
        await expect(page.getByRole('link', { name: 'RAG Documents' })).toBeVisible();
        await expect(page.getByRole('link', { name: 'Dashboard' })).toBeVisible();
        await expect(page.getByRole('link', { name: 'Roles' })).toBeVisible();
        await expect(page.getByRole('link', { name: 'Users' })).toBeVisible();
        await expect(page.getByRole('link', { name: 'Security Logs' })).toBeVisible();
        await expect(page.getByRole('link', { name: 'Security Dashboard' })).toBeVisible();
        await expect(page.getByRole('link', { name: 'Document Access' })).toBeVisible();
    });
});

// ---------------------------------------------------------------------------
// security role
// ---------------------------------------------------------------------------

test.describe('Role: security', () => {
    test('can access /security/dashboard', async ({ page }) => {
        await setAuth(page, 'security');
        await page.goto('/security/dashboard');
        await expect(page).toHaveURL(/\/security\/dashboard/);
    });

    test('can access /security/documents', async ({ page }) => {
        await setAuth(page, 'security');
        await page.goto('/security/documents');
        await expect(page).toHaveURL(/\/security\/documents/);
    });

    test('can access /documents', async ({ page }) => {
        await setAuth(page, 'security');
        await page.goto('/documents');
        await expect(page).toHaveURL(/\/documents/);
    });

    test('cannot access /chat and is redirected to /forbidden', async ({ page }) => {
        await setAuth(page, 'security');
        await page.goto('/chat');
        await expect(page).toHaveURL(/\/forbidden/);
    });

    test('is redirected to /forbidden when accessing /admin/dashboard', async ({ page }) => {
        await setAuth(page, 'security');
        await page.goto('/admin/dashboard');
        await expect(page).toHaveURL(/\/forbidden/);
    });

    test('sidebar shows security items', async ({ page }) => {
        await setAuth(page, 'security');
        await page.goto('/security/dashboard');
        await expect(page.getByRole('link', { name: 'Security Logs' })).toBeVisible();
        await expect(page.getByRole('link', { name: 'Security Dashboard' })).toBeVisible();
        await expect(page.getByRole('link', { name: 'Document Access' })).toBeVisible();
    });

    test('sidebar does not show chat or admin-only items', async ({ page }) => {
        await setAuth(page, 'security');
        await page.goto('/security/dashboard');
        await expect(page.getByRole('link', { name: 'Chat' })).not.toBeVisible();
        await expect(page.getByRole('link', { name: 'RAG Documents' })).not.toBeVisible();
        await expect(page.getByRole('link', { name: 'Dashboard' })).not.toBeVisible();
        await expect(page.getByRole('link', { name: 'Roles' })).not.toBeVisible();
        await expect(page.getByRole('link', { name: 'Users' })).not.toBeVisible();
    });
});
