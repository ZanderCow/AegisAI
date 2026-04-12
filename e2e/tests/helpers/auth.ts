/**
 * Shared authentication helpers for Playwright E2E tests.
 *
 * The helpers centralize seeded-account lookup, API-based test-user creation,
 * and the common login assertions used across auth, role, chat, and RAG suites.
 */
import { expect, type APIRequestContext, type Page } from '@playwright/test';
import { randomUUID } from 'crypto';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

/** Roles that are pre-seeded by the local development and E2E Docker setup. */
export type SeededRole = 'admin' | 'security';

/** Roles that can appear in E2E login helpers, including runtime-created users. */
export type AuthenticatedRole = 'user' | SeededRole;

/** Credentials returned by the auth helpers for login and route assertions. */
export interface TestCredentials {
  /** Email address submitted through the login form or signup endpoint. */
  email: string;

  /** Plaintext password used only in the isolated local and E2E environments. */
  password: string;

  /** Role that determines the expected post-login landing route. */
  role: AuthenticatedRole;
}

/** Default password for standard users created dynamically during E2E runs. */
export const TEST_USER_PASSWORD = 'AegisUser!2026';

/**
 * Reads a required E2E environment variable and fails fast when it is missing.
 *
 * @param name - Environment variable name to resolve.
 * @returns The trimmed variable value.
 * @throws Error When the variable is unset or blank.
 */
function requiredEnv(name: string): string {
  const value = process.env[name]?.trim();
  if (!value) {
    throw new Error(`Missing required E2E environment variable: ${name}`);
  }
  return value;
}

/**
 * Escapes route strings before embedding them in regex-based URL assertions.
 *
 * @param value - Raw route fragment.
 * @returns A regex-safe version of the provided string.
 */
function escapeRegex(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

/**
 * Maps a role to the route users should land on immediately after login.
 *
 * @param role - Authenticated role returned by the helper.
 * @returns The role-specific application home route.
 */
function homeRoute(role: AuthenticatedRole): string {
  if (role === 'admin') return '/admin/dashboard';
  if (role === 'security') return '/security/dashboard';
  return '/chat';
}

/** Seeded accounts supplied by the local Docker environment for deterministic E2E logins. */
const SEEDED_CREDENTIALS: Record<SeededRole, TestCredentials> = {
  admin: {
    email: requiredEnv('admin_user_username'),
    password: requiredEnv('admin_user_password'),
    role: 'admin',
  },
  security: {
    email: requiredEnv('security_username'),
    password: requiredEnv('security_password'),
    role: 'security',
  },
};

/**
 * Mirrors browser console and page errors into the test runner output.
 *
 * @param page - Playwright page whose client-side logs should be attached.
 */
export function attachPageDebugLogging(page: Page): void {
  page.on('console', msg => console.log('BROWSER:', msg.text()));
  page.on('pageerror', err => console.log('PAGE ERROR:', err.message));
}

/**
 * Returns the seeded credentials for a privileged role.
 *
 * @param role - Seeded role to look up.
 * @returns Credentials supplied by the E2E environment.
 */
export function getSeededCredentials(role: SeededRole): TestCredentials {
  return SEEDED_CREDENTIALS[role];
}

/**
 * Navigates to the login page and submits the provided credentials.
 *
 * @param page - Playwright page used for browser interaction.
 * @param email - Email address to submit.
 * @param password - Plaintext password to submit.
 * @returns A promise that resolves after the sign-in button is clicked.
 */
export async function submitLoginForm(page: Page, email: string, password: string): Promise<void> {
  await page.goto('/login');
  await page.getByLabel('Email').fill(email);
  await page.getByLabel('Password').fill(password);
  const submitButton = page.getByRole('button', { name: 'Sign In' });
  await expect(submitButton).toBeEnabled();
  await submitButton.click();
}

/**
 * Logs in with the provided credentials and verifies the expected landing route.
 *
 * @param page - Playwright page used for browser interaction.
 * @param credentials - Credentials and role metadata for the login attempt.
 * @returns A promise that resolves once the auth token is present in local storage.
 */
export async function loginWithCredentials(page: Page, credentials: TestCredentials): Promise<void> {
  await submitLoginForm(page, credentials.email, credentials.password);
  await expect(page).toHaveURL(new RegExp(`${escapeRegex(homeRoute(credentials.role))}$`));

  const token = await page.evaluate(() => localStorage.getItem('aegis_token'));
  expect(token).toBeTruthy();
}

/**
 * Logs in using one of the deterministic seeded privileged accounts.
 *
 * @param page - Playwright page used for browser interaction.
 * @param role - Seeded role to authenticate as.
 * @returns The credentials that were used for the login.
 */
export async function loginAsSeededRole(page: Page, role: SeededRole): Promise<TestCredentials> {
  const credentials = getSeededCredentials(role);
  await loginWithCredentials(page, credentials);
  return credentials;
}

/**
 * Authenticates through the backend API and returns the issued bearer token.
 *
 * @param request - Playwright API client scoped to the current test.
 * @param credentials - Credentials used for the login request.
 * @returns The backend-issued JWT access token.
 */
export async function loginViaApi(
  request: APIRequestContext,
  credentials: TestCredentials,
): Promise<string> {
  const response = await request.post(`${BACKEND_URL}/api/v1/auth/login`, {
    data: {
      email: credentials.email,
      password: credentials.password,
    },
  });

  expect(response.ok()).toBeTruthy();
  const data = await response.json();
  if (data.mfa_required) {
    throw new Error('E2E API login does not support MFA flows.');
  }

  return data.access_token as string;
}

/**
 * Creates a standard user through the backend signup API.
 *
 * Using the API keeps role-matrix tests fast and avoids repeating the UI signup
 * flow when the test only needs an authenticated baseline user.
 *
 * @param request - Playwright API client scoped to the current test.
 * @param prefix - Prefix added to the generated email address for easier debugging.
 * @returns Credentials for the newly created standard user.
 */
export async function createStandardUser(
  request: APIRequestContext,
  prefix = 'user',
): Promise<TestCredentials> {
  const credentials: TestCredentials = {
    email: `${prefix}_${randomUUID().slice(0, 8)}@example.com`,
    password: TEST_USER_PASSWORD,
    role: 'user',
  };

  const response = await request.post(`${BACKEND_URL}/api/v1/auth/signup`, {
    data: {
      email: credentials.email,
      password: credentials.password,
      role: credentials.role,
    },
  });

  expect(response.ok()).toBeTruthy();
  return credentials;
}

/**
 * Creates a standard user and completes the browser login flow for that user.
 *
 * @param page - Playwright page used for browser interaction.
 * @param request - Playwright API client scoped to the current test.
 * @param prefix - Prefix added to the generated email address for easier debugging.
 * @returns Credentials for the created and logged-in user.
 */
export async function createAndLoginUser(
  page: Page,
  request: APIRequestContext,
  prefix = 'user',
): Promise<TestCredentials> {
  const credentials = await createStandardUser(request, prefix);
  await loginWithCredentials(page, credentials);
  return credentials;
}

/**
 * Logs the current user out through the shared topbar control.
 *
 * @param page - Playwright page used for browser interaction.
 * @returns A promise that resolves once the login screen is visible again.
 */
export async function logoutFromApp(page: Page): Promise<void> {
  await page.getByRole('button', { name: 'Logout' }).click();
  await expect(page).toHaveURL(/\/login$/);
  const token = await page.evaluate(() => localStorage.getItem('aegis_token'));
  expect(token).toBeNull();
}
