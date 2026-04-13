/**
 * End-to-end coverage for admin-managed RAG document ingestion and retrieval.
 *
 * Test Flow:
 * 1. Admin Ingestion: Login as admin -> Upload PDFs -> Assert successful upload.
 * 2. User Visibility: Login as standard user -> Verify PDF titles appear in /documents.
 * 3. Grounded Retrieval: Start chat -> Ask factual questions -> Assert response contains PDF data.
 */
import { expect, test, type Page } from '@playwright/test';
import path from 'path';
import {
  attachPageDebugLogging,
  createStandardUser,
  loginAsSeededRole,
  loginWithCredentials,
  logoutFromApp,
  type TestCredentials,
} from './helpers/auth';
import {
  createConversation,
  latestAssistantMessageContent,
  sendMessageWithButton,
  type ProviderName,
} from './helpers/chat';

interface ProviderConfig {
  id: ProviderName;
  model: string;
}

interface RagAsset {
  filePath: string;
  title: string;
  description: string;
  prompt: string;
  assertions: RegExp[];
}

const FILES_DIR = path.resolve(__dirname, 'files');

const DEFAULT_MODELS: Record<ProviderName, string> = {
  groq: 'llama-3.1-8b-instant',
  gemini: 'gemini-2.5-flash',
  deepseek: 'deepseek-chat',
};

const RAG_ASSETS: RagAsset[] = [
  {
    filePath: path.join(FILES_DIR, 'employee_handbook.pdf'),
    title: 'Employee Handbook',
    description: 'RAG E2E asset: employee handbook',
    prompt: 'According to the uploaded employee handbook, what is the maximum PTO carryover per calendar year? Reply with just the number of hours.',
    assertions: [/40/i, /hour/i],
  },
  {
    filePath: path.join(FILES_DIR, 'incident-num-2031.pdf'),
    title: 'Incident 2031',
    description: 'RAG E2E asset: incident report',
    prompt: 'According to incident #2031, which endpoint exposed the DB connection string? Reply with just the endpoint path.',
    assertions: [/\/debug\/vars/i],
  },
  {
    filePath: path.join(FILES_DIR, 'payroll.pdf'),
    title: 'Payroll Register',
    description: 'RAG E2E asset: payroll register',
    prompt: 'According to the uploaded payroll register, what was the total gross pay for the pay period? Reply with just the dollar amount.',
    assertions: [/\$?38,?080(?:\.00)?/i],
  },
];

function providerHasKey(provider: ProviderName): boolean {
  const envByProvider = {
    groq: process.env.GROQ_API_KEY,
    gemini: process.env.GEMINI_API_KEY,
    deepseek: process.env.DEEPSEEK_API_KEY,
  } as const;

  return !!envByProvider[provider];
}

function getProviderConfig(): ProviderConfig {
  const requestedProvider = process.env.E2E_PROVIDER?.trim().toLowerCase() as ProviderName | undefined;
  const requestedModel = process.env.E2E_MODEL?.trim();

  if (requestedProvider) {
    if (!(requestedProvider in DEFAULT_MODELS)) {
      throw new Error(`Unsupported E2E_PROVIDER "${requestedProvider}". Expected one of: ${Object.keys(DEFAULT_MODELS).join(', ')}.`);
    }
    if (!providerHasKey(requestedProvider)) {
      throw new Error(`E2E_PROVIDER="${requestedProvider}" requires its matching API key environment variable.`);
    }

    return {
      id: requestedProvider,
      model: requestedModel || DEFAULT_MODELS[requestedProvider],
    };
  }

  for (const provider of Object.keys(DEFAULT_MODELS) as ProviderName[]) {
    if (!providerHasKey(provider)) {
      continue;
    }

    return {
      id: provider,
      model: requestedModel || DEFAULT_MODELS[provider],
    };
  }

  throw new Error(
    'RAG E2E requires a live provider. Set E2E_PROVIDER plus its API key, or provide one of GROQ_API_KEY, GEMINI_API_KEY, or DEEPSEEK_API_KEY.',
  );
}

async function uploadDocumentFromAdmin(page: Page, asset: RagAsset): Promise<void> {
  await page.getByRole('button', { name: 'Upload Document' }).click();
  await expect(page.getByRole('heading', { name: 'Upload Document' })).toBeVisible();
  const uploadForm = page.locator('form').filter({ has: page.getByLabel('Document Title') });

  const uploadResponsePromise = page.waitForResponse(
    response =>
      response.url().includes('/api/v1/documents')
      && response.request().method() === 'POST',
  );

  await uploadForm.locator('input[type="file"]').setInputFiles(asset.filePath);
  await uploadForm.getByLabel('Document Title').fill(asset.title);
  await uploadForm.getByLabel('Description').fill(asset.description);
  await uploadForm.getByRole('button', { name: 'User', exact: true }).click();
  await uploadForm.getByRole('button', { name: 'Upload', exact: true }).click();

  const uploadResponse = await uploadResponsePromise;
  expect(uploadResponse.ok()).toBeTruthy();

  await expect(page.getByRole('heading', { name: 'Upload Document' })).not.toBeVisible();
  await expect(page.getByText(asset.title, { exact: true })).toBeVisible({ timeout: 120_000 });
}

async function verifyGroundedReply(page: Page, asset: RagAsset, provider: ProviderConfig): Promise<void> {
  const conversationTitle = `RAG ${asset.title}`;

  await createConversation(page, conversationTitle, provider.id, provider.model);
  await sendMessageWithButton(page, asset.prompt, 120_000);

  const assistantReply = latestAssistantMessageContent(page);
  await expect(assistantReply).toBeVisible({ timeout: 120_000 });
  for (const assertion of asset.assertions) {
    await expect(assistantReply).toContainText(assertion, { timeout: 120_000 });
  }
}

test.beforeEach(({ page }) => {
  attachPageDebugLogging(page);
});

test.describe('RAG document upload and chat retrieval', () => {
  test('uploads real PDFs through admin UI and retrieves grounded answers in chat', async ({ page, request }) => {
    test.setTimeout(300_000);

    const provider = getProviderConfig();
    const standardUser: TestCredentials = await createStandardUser(request, 'rag');

    await loginAsSeededRole(page, 'admin');
    await page.goto('/admin/documents');
    await expect(page.getByRole('heading', { name: 'Document Management' })).toBeVisible();

    for (const asset of RAG_ASSETS) {
      await uploadDocumentFromAdmin(page, asset);
    }

    await logoutFromApp(page);
    await loginWithCredentials(page, standardUser);

    await page.goto('/documents');
    await expect(page.getByRole('heading', { name: 'RAG Documents' })).toBeVisible();
    for (const asset of RAG_ASSETS) {
      await expect(page.getByText(asset.title, { exact: true })).toBeVisible({ timeout: 120_000 });
    }

    await page.goto('/chat');
    await expect(page).toHaveURL(/\/chat$/);

    for (const asset of RAG_ASSETS) {
      await verifyGroundedReply(page, asset, provider);
    }
  });
});
