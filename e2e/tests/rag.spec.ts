import { expect, test, type APIRequestContext, type Page } from '@playwright/test';
import { randomUUID } from 'crypto';
import { mkdirSync, writeFileSync } from 'fs';
import { dirname } from 'path';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';
const PASSWORD = 'password123';
const PDF_FILENAME = 'aegis-rag-reference.pdf';
const PDF_SECRET = 'AEGIS-2026-SECURE';
const PDF_TEXT = `Aegis handbook: The office Wi-Fi password is ${PDF_SECRET}.`;
const QUESTION = 'According to the uploaded document, reply with only the exact office Wi-Fi password.';

const PROVIDER_LABELS = {
    groq: 'Groq',
    gemini: 'Gemini',
    deepseek: 'DeepSeek',
} as const;

const DEFAULT_MODELS = {
    groq: 'llama-3.1-8b-instant',
    gemini: 'gemini-2.5-flash',
    deepseek: 'deepseek-chat',
} as const;

type ProviderName = keyof typeof PROVIDER_LABELS;

function providerHasKey(provider: ProviderName): boolean {
    const envByProvider = {
        groq: process.env.GROQ_API_KEY,
        gemini: process.env.GEMINI_API_KEY,
        deepseek: process.env.DEEPSEEK_API_KEY,
    } as const;

    return !!envByProvider[provider];
}

function getProviderConfig():
    | { id: ProviderName; label: string; model: string }
    | null {
    const requestedProvider = process.env.E2E_PROVIDER?.trim().toLowerCase() as ProviderName | undefined;
    const requestedModel = process.env.E2E_MODEL?.trim();

    if (requestedProvider) {
        if (!(requestedProvider in PROVIDER_LABELS)) {
            throw new Error(`Unsupported E2E_PROVIDER "${requestedProvider}".`);
        }
        if (!providerHasKey(requestedProvider)) {
            throw new Error(`E2E_PROVIDER="${requestedProvider}" requires its matching API key env var.`);
        }

        return {
            id: requestedProvider,
            label: PROVIDER_LABELS[requestedProvider],
            model: requestedModel || DEFAULT_MODELS[requestedProvider],
        };
    }

    for (const provider of Object.keys(PROVIDER_LABELS) as ProviderName[]) {
        if (!providerHasKey(provider)) continue;
        return {
            id: provider,
            label: PROVIDER_LABELS[provider],
            model: DEFAULT_MODELS[provider],
        };
    }

    return null;
}

function escapePdfText(text: string): string {
    return text.replace(/\\/g, '\\\\').replace(/\(/g, '\\(').replace(/\)/g, '\\)');
}

function buildPdfBuffer(text: string): Buffer {
    const stream = `BT\n/F1 18 Tf\n72 120 Td\n(${escapePdfText(text)}) Tj\nET\n`;
    const objects = [
        '1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n',
        '2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n',
        '3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>\nendobj\n',
        `4 0 obj\n<< /Length ${Buffer.byteLength(stream, 'latin1')} >>\nstream\n${stream}endstream\nendobj\n`,
        '5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n',
    ];

    let pdf = '%PDF-1.4\n';
    const offsets: number[] = [0];
    for (const object of objects) {
        offsets.push(Buffer.byteLength(pdf, 'latin1'));
        pdf += object;
    }

    const xrefStart = Buffer.byteLength(pdf, 'latin1');
    pdf += `xref\n0 ${objects.length + 1}\n`;
    pdf += '0000000000 65535 f \n';
    for (const offset of offsets.slice(1)) {
        pdf += `${offset.toString().padStart(10, '0')} 00000 n \n`;
    }
    pdf += `trailer\n<< /Size ${objects.length + 1} /Root 1 0 R >>\nstartxref\n${xrefStart}\n%%EOF\n`;

    return Buffer.from(pdf, 'latin1');
}

function createPdfFixture(path: string): void {
    mkdirSync(dirname(path), { recursive: true });
    writeFileSync(path, buildPdfBuffer(PDF_TEXT));
}

async function createUser(email: string, request: APIRequestContext) {
    const response = await request.post(`${BACKEND_URL}/api/v1/auth/signup`, {
        data: { email, password: PASSWORD },
    });
    expect(response.ok()).toBeTruthy();
}

async function login(page: Page, email: string) {
    await page.goto('/login');
    await page.getByLabel('Email').fill(email);
    await page.getByLabel('Password').fill(PASSWORD);
    await page.getByRole('button', { name: 'Sign In' }).click();
    await expect(page).toHaveURL(/\/chat/);
}

test.beforeEach(({ page }) => {
    page.on('console', msg => console.log('BROWSER:', msg.text()));
    page.on('pageerror', err => console.log('PAGE ERROR:', err.message));
});

test.describe('RAG document upload and chat retrieval', () => {
    test('uploads a PDF and answers from the indexed document in chat', async ({ page, request }, testInfo) => {
        test.setTimeout(180_000);
        const provider = getProviderConfig();
        if (!provider) {
            test.skip(true, 'RAG E2E requires GROQ_API_KEY, GEMINI_API_KEY, or DEEPSEEK_API_KEY.');
            return;
        }

        const email = `rag_${randomUUID().slice(0, 8)}@example.com`;
        const pdfPath = testInfo.outputPath(PDF_FILENAME);
        createPdfFixture(pdfPath);

        await createUser(email, request);
        await login(page, email);

        const chatPage = await page.context().newPage();
        chatPage.on('console', msg => console.log('CHAT TAB:', msg.text()));
        chatPage.on('pageerror', err => console.log('CHAT TAB ERROR:', err.message));
        await chatPage.goto('/chat');
        await expect(chatPage).toHaveURL(/\/chat/);

        await page.goto('/documents');
        await expect(page.getByRole('heading', { name: 'RAG Documents' })).toBeVisible();

        const uploadResponsePromise = page.waitForResponse(
            response =>
                response.url().includes('/api/v1/rag/documents')
                && response.request().method() === 'POST',
        );
        await page.locator('input[type="file"]').setInputFiles(pdfPath);
        const uploadResponse = await uploadResponsePromise;
        expect(uploadResponse.ok()).toBeTruthy();

        await expect(page.getByText(new RegExp(`"${PDF_FILENAME}" indexed successfully`, 'i'))).toBeVisible({
            timeout: 120_000,
        });
        await expect(page.getByText(PDF_FILENAME, { exact: true })).toBeVisible();

        await chatPage.bringToFront();
        await chatPage.getByRole('button', { name: '+ New Conversation' }).click();
        if (provider.id !== 'groq') {
            await chatPage.locator('select').selectOption(provider.id);
        }
        await expect(chatPage.getByLabel('Model')).toHaveValue(DEFAULT_MODELS[provider.id]);
        if (provider.model !== DEFAULT_MODELS[provider.id]) {
            await chatPage.getByLabel('Model').fill(provider.model);
        }
        await chatPage.getByLabel('Title (optional)').fill('RAG E2E Conversation');
        await chatPage.getByRole('button', { name: 'Create' }).click();

        await expect(chatPage.getByRole('heading', { name: 'RAG E2E Conversation' })).toBeVisible();

        const sendResponsePromise = chatPage.waitForResponse(
            response =>
                response.url().includes('/messages/send')
                && response.request().method() === 'POST',
        );
        await chatPage.getByPlaceholder(/Type your message/i).fill(QUESTION);
        await chatPage.locator('form').getByRole('button').click();
        const sendResponse = await sendResponsePromise;
        expect(sendResponse.ok()).toBeTruthy();

        await expect(chatPage.getByText(PDF_SECRET)).toBeVisible({ timeout: 90_000 });
    });
});
