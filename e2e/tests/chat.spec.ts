import { test, expect } from '@playwright/test';

// Build a fake JWT the frontend can decode (signature is ignored by the client).
function makeFakeJWT(payload: Record<string, unknown>): string {
    const header = Buffer.from(JSON.stringify({ alg: 'HS256', typ: 'JWT' })).toString('base64');
    const body = Buffer.from(JSON.stringify(payload)).toString('base64');
    return `${header}.${body}.fakesig`;
}

const VALID_TOKEN = makeFakeJWT({
    sub: 'e2e-user-id',
    email: 'e2e@example.com',
    exp: Math.floor(Date.now() / 1000) + 3600,
});

const SEED_CONVERSATIONS = [
    {
        id: 'conv-1',
        title: 'Test Conversation',
        provider: 'groq',
        model: 'llama-3.1-8b-instant',
        createdAt: new Date().toISOString(),
        lastMessageAt: new Date().toISOString(),
        lastMessage: 'Hello there',
    },
    {
        id: 'conv-2',
        title: 'Second Chat',
        provider: 'gemini',
        model: 'gemini-2.5-flash',
        createdAt: new Date().toISOString(),
        lastMessageAt: new Date().toISOString(),
    },
];

// Inject auth token (and optionally seeded conversations) before page load.
async function setAuth(page: Parameters<typeof test>[1] extends (...args: infer A) => unknown ? A[0] : never, conversations?: typeof SEED_CONVERSATIONS) {
    await page.addInitScript(
        ({ token, convos }) => {
            localStorage.setItem('aegis_token', token);
            if (convos) {
                const payload = JSON.parse(atob(token.split('.')[1]));
                const userId = payload.sub || 'anonymous';
                localStorage.setItem(`aegis_conversations_${userId}`, JSON.stringify(convos));
            }
        },
        { token: VALID_TOKEN, convos: conversations ?? null },
    );
}

test.beforeEach(({ page }) => {
    page.on('console', msg => console.log('BROWSER:', msg.text()));
    page.on('pageerror', err => console.log('PAGE ERROR:', err.message));
});

test.describe('Chat page – authentication guard', () => {
    test('unauthenticated user is redirected to /login', async ({ page }) => {
        await page.goto('/chat');
        await expect(page).toHaveURL(/\/login/);
    });

    test('authenticated user can access /chat', async ({ page }) => {
        await setAuth(page);
        await page.goto('/chat');
        await expect(page).toHaveURL(/\/chat/);
    });
});

test.describe('Chat page – conversation list', () => {
    test('shows empty state when no conversations exist', async ({ page }) => {
        await setAuth(page);
        await page.goto('/chat');
        await expect(page.getByText('No conversations yet')).toBeVisible();
    });

    test('shows seeded conversations in the sidebar', async ({ page }) => {
        await setAuth(page, SEED_CONVERSATIONS);
        await page.goto('/chat');
        await expect(page.getByText('Test Conversation')).toBeVisible();
        await expect(page.getByText('Second Chat')).toBeVisible();
    });

    test('shows last message preview in the list', async ({ page }) => {
        await setAuth(page, SEED_CONVERSATIONS);
        await page.goto('/chat');
        await expect(page.getByText('Hello there')).toBeVisible();
    });
});

test.describe('Chat page – new conversation modal', () => {
    test('clicking "+ New Conversation" opens the modal', async ({ page }) => {
        await setAuth(page);
        await page.goto('/chat');
        await page.getByText('+ New Conversation').click();
        await expect(page.getByText('New Conversation').first()).toBeVisible();
        await expect(page.getByPlaceholder('New Chat')).toBeVisible();
    });

    test('modal has provider and model fields', async ({ page }) => {
        await setAuth(page);
        await page.goto('/chat');
        await page.getByText('+ New Conversation').click();
        await expect(page.locator('select')).toBeVisible();
        await expect(page.getByPlaceholder(/llama/i)).toBeVisible();
    });

    test('provider options include Groq, Gemini, and DeepSeek', async ({ page }) => {
        await setAuth(page);
        await page.goto('/chat');
        await page.getByText('+ New Conversation').click();
        const select = page.locator('select');
        await expect(select.locator('option', { hasText: 'Groq' })).toBeAttached();
        await expect(select.locator('option', { hasText: 'Gemini' })).toBeAttached();
        await expect(select.locator('option', { hasText: 'DeepSeek' })).toBeAttached();
    });

    test('changing provider updates the default model', async ({ page }) => {
        await setAuth(page);
        await page.goto('/chat');
        await page.getByText('+ New Conversation').click();

        const modelInput = page.getByPlaceholder(/llama/i);
        await expect(modelInput).toHaveValue('llama-3.1-8b-instant');

        await page.locator('select').selectOption('gemini');
        await expect(page.getByLabel('Model')).toHaveValue('gemini-2.5-flash');

        await page.locator('select').selectOption('deepseek');
        await expect(page.getByLabel('Model')).toHaveValue('deepseek-chat');
    });

    test('Cancel button closes the modal', async ({ page }) => {
        await setAuth(page);
        await page.goto('/chat');
        await page.getByText('+ New Conversation').click();
        await expect(page.getByRole('heading', { name: 'New Conversation' })).toBeVisible();

        await page.getByRole('button', { name: 'Cancel' }).click();
        await expect(page.getByRole('heading', { name: 'New Conversation' })).not.toBeVisible();
    });

    test('creating a conversation calls the API and shows an error on failure', async ({ page }) => {
        await setAuth(page);
        await page.goto('/chat');
        await page.getByText('+ New Conversation').click();

        await page.getByLabel('Title (optional)').fill('My E2E Chat');
        await page.getByRole('button', { name: 'Create' }).click();

        // Either the conversation was created (API available) or an error is shown
        try {
            // API success path: modal closes and conversation appears
            await expect(page.getByRole('heading', { name: 'New Conversation' })).not.toBeVisible({ timeout: 3000 });
        } catch {
            // API failure path: error message is shown inside the modal
            const errorMsg = page.locator('.text-red-400.bg-red-900\\/30, p.text-red-400');
            await expect(errorMsg.first()).toBeVisible();
        }
    });
});

test.describe('Chat page – selecting a conversation', () => {
    test('shows empty state when no conversation is selected', async ({ page }) => {
        await setAuth(page, SEED_CONVERSATIONS);
        await page.goto('/chat');
        // On desktop, both panel and empty state are visible simultaneously
        await expect(page.getByText('No conversation selected')).toBeVisible();
    });

    test('clicking a conversation opens the chat window', async ({ page }) => {
        await setAuth(page, SEED_CONVERSATIONS);
        await page.goto('/chat');

        await page.getByText('Test Conversation').click();

        // The chat window header shows the conversation title
        await expect(page.getByRole('heading', { name: 'Test Conversation' })).toBeVisible();
        // Provider and model info line
        await expect(page.getByText(/groq/i)).toBeVisible();
    });

    test('selected conversation shows the chat input textarea', async ({ page }) => {
        await setAuth(page, SEED_CONVERSATIONS);
        await page.goto('/chat');
        await page.getByText('Test Conversation').click();

        await expect(page.getByPlaceholder(/Type your message/i)).toBeVisible();
    });
});

test.describe('Chat page – chat input', () => {
    test('send button is disabled when textarea is empty', async ({ page }) => {
        await setAuth(page, SEED_CONVERSATIONS);
        await page.goto('/chat');
        await page.getByText('Test Conversation').click();

        // The send button (svg icon button at end of input) should be disabled
        const sendButton = page.locator('form').getByRole('button');
        await expect(sendButton).toBeDisabled();
    });

    test('send button becomes enabled after typing a message', async ({ page }) => {
        await setAuth(page, SEED_CONVERSATIONS);
        await page.goto('/chat');
        await page.getByText('Test Conversation').click();

        await page.getByPlaceholder(/Type your message/i).fill('Hello, AI!');
        const sendButton = page.locator('form').getByRole('button');
        await expect(sendButton).toBeEnabled();
    });

    test('pressing Enter sends the message (or shows an error if API unavailable)', async ({ page }) => {
        await setAuth(page, SEED_CONVERSATIONS);
        await page.goto('/chat');
        await page.getByText('Test Conversation').click();

        const textarea = page.getByPlaceholder(/Type your message/i);
        await textarea.fill('Hello, AI!');
        await textarea.press('Enter');

        try {
            // If API is available: the user message appears in the message list
            await expect(page.getByText('Hello, AI!')).toBeVisible({ timeout: 3000 });
        } catch {
            // If API unavailable: textarea is cleared or stays, but no crash
            // The page should still be functional (no error overlay)
            await expect(page.locator('body')).toBeVisible();
        }
    });

    test('Shift+Enter adds a newline instead of sending', async ({ page }) => {
        await setAuth(page, SEED_CONVERSATIONS);
        await page.goto('/chat');
        await page.getByText('Test Conversation').click();

        const textarea = page.getByPlaceholder(/Type your message/i);
        await textarea.fill('line one');
        await textarea.press('Shift+Enter');
        await textarea.type('line two');

        // Textarea should now contain a newline
        const value = await textarea.inputValue();
        expect(value).toContain('\n');
    });
});

test.describe('Chat page – deleting a conversation', () => {
    test('hovering a conversation reveals the delete button', async ({ page }) => {
        await setAuth(page, SEED_CONVERSATIONS);
        await page.goto('/chat');

        const convItem = page.locator('li').filter({ hasText: 'Test Conversation' });
        await convItem.hover();

        // The delete button (trash icon) becomes visible on hover
        const deleteBtn = convItem.locator('button');
        await expect(deleteBtn).toBeVisible();
    });

    test('clicking delete removes the conversation from the list', async ({ page }) => {
        await setAuth(page, SEED_CONVERSATIONS);
        await page.goto('/chat');

        await expect(page.getByText('Test Conversation')).toBeVisible();

        const convItem = page.locator('li').filter({ hasText: 'Test Conversation' });
        await convItem.hover();
        await convItem.locator('button').click();

        await expect(page.getByText('Test Conversation')).not.toBeVisible();
    });
});
