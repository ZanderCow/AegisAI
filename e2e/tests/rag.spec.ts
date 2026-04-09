/**
 * End-to-end coverage for document indexing and grounded chat retrieval.
 *
 * The suite creates a tiny PDF fixture on the fly, uploads it through the RAG
 * UI, and then verifies that a chat conversation can retrieve the known secret
 * from the indexed document.
 */
import { expect, test, type APIRequestContext, type Page } from '@playwright/test';
import { mkdirSync, writeFileSync } from 'fs';
import { dirname } from 'path';
import { attachPageDebugLogging, createAndLoginUser } from './helpers/auth';

const PDF_FILENAME = 'aegis-rag-reference.pdf';
const PDF_SECRET = 'AEGIS-2026-SECURE';
const PDF_TEXT = `Aegis handbook: The office Wi-Fi password is ${PDF_SECRET}.`;
const QUESTION = 'According to the uploaded document, reply with only the exact office Wi-Fi password.';

/** Maps provider ids to their user-facing labels in the new-conversation modal. */
const PROVIDER_LABELS = {
    groq: 'Groq',
    gemini: 'Gemini',
    deepseek: 'DeepSeek',
} as const;

/** Mirrors the frontend defaults so the test can assert provider-driven model changes. */
const DEFAULT_MODELS = {
    groq: 'llama-3.1-8b-instant',
    gemini: 'gemini-2.5-flash',
    deepseek: 'deepseek-chat',
} as const;

type ProviderName = keyof typeof PROVIDER_LABELS;

/**
 * Reports whether the selected provider has the API key needed for a live RAG run.
 *
 * @param provider - Provider id requested by the test configuration.
 * @returns True when the matching provider API key is present in the environment.
 */
function providerHasKey(provider: ProviderName): boolean {
    const envByProvider = {
        groq: process.env.GROQ_API_KEY,
        gemini: process.env.GEMINI_API_KEY,
        deepseek: process.env.DEEPSEEK_API_KEY,
    } as const;

    return !!envByProvider[provider];
}

/**
 * Resolves the provider and model used for the RAG E2E scenario.
 *
 * The test honors explicit `E2E_PROVIDER` and `E2E_MODEL` overrides first.
 * When no override is provided, it selects the first provider that has a
 * configured API key so local and CI environments can share the same suite.
 *
 * @returns The provider configuration to use, or `null` when no live provider is configured.
 * @throws Error When `E2E_PROVIDER` names an unsupported provider or lacks its required API key.
 */
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

/**
 * Escapes PDF content stream characters that would otherwise break the fixture.
 *
 * @param text - Plain text injected into the generated PDF.
 * @returns Text escaped for use inside a literal PDF string.
 */
function escapePdfText(text: string): string {
    return text.replace(/\\/g, '\\\\').replace(/\(/g, '\\(').replace(/\)/g, '\\)');
}

/**
 * Builds a minimal single-page PDF that contains the provided text.
 *
 * The fixture is intentionally tiny so the test controls the indexed content
 * without depending on checked-in binary assets.
 *
 * @param text - Text content rendered onto the single PDF page.
 * @returns A PDF buffer ready to upload through the documents page.
 */
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

/**
 * Writes the generated PDF fixture to the current test's output directory.
 *
 * @param path - Absolute file path where the PDF should be created.
 */
function createPdfFixture(path: string): void {
    mkdirSync(dirname(path), { recursive: true });
    writeFileSync(path, buildPdfBuffer(PDF_TEXT));
}

test.beforeEach(({ page }) => {
    // Mirror browser console output in the terminal for easier CI debugging.
    attachPageDebugLogging(page);
});

test.describe('RAG document upload and chat retrieval', () => {
    test('uploads a PDF and answers from the indexed document in chat', async ({ page, request }, testInfo) => {
        test.setTimeout(180_000);
        const provider = getProviderConfig();
        if (!provider) {
            test.skip(true, 'RAG E2E requires GROQ_API_KEY, GEMINI_API_KEY, or DEEPSEEK_API_KEY.');
            return;
        }

        const pdfPath = testInfo.outputPath(PDF_FILENAME);
        createPdfFixture(pdfPath);

        await createAndLoginUser(page, request, 'rag');

        // Use a separate chat tab so we verify retrieval from a fresh conversation
        // while the original page stays focused on document upload progress.
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

        await expect(
            chatPage.locator('.text-sm.whitespace-pre-wrap.leading-relaxed').filter({ hasText: PDF_SECRET }),
        ).toBeVisible({ timeout: 90_000 });
    });
});
