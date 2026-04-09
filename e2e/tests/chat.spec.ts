/**
 * Covers the core chat workspace flows for authenticated users.
 *
 * These scenarios focus on conversation lifecycle behavior in the UI rather
 * than provider-specific response quality, which is handled elsewhere.
 */
import { test, expect } from '@playwright/test';
import { attachPageDebugLogging, createAndLoginUser } from './helpers/auth';
import {
  conversationListItem,
  conversationDeleteButton,
  createConversation,
  hoverConversation,
  openConversationFromList,
  openNewConversationModal,
  sendMessageWithButton,
  waitForPreviewText,
} from './helpers/chat';

test.beforeEach(({ page }) => {
  // Bubble browser errors into test logs to make flaky chat failures diagnosable.
  attachPageDebugLogging(page);
});

test.describe('Chat page – authentication guard', () => {
  test('unauthenticated user is redirected to /login', async ({ page }) => {
    await page.goto('/chat');
    await expect(page).toHaveURL(/\/login$/);
  });

  test('authenticated user can access /chat', async ({ page, request }) => {
    await createAndLoginUser(page, request, 'chat-auth');
    await page.goto('/chat');
    await expect(page).toHaveURL(/\/chat$/);
  });
});

test.describe('Chat page – conversation list', () => {
  test('shows empty state when no conversations exist', async ({ page, request }) => {
    await createAndLoginUser(page, request, 'chat-empty');
    await page.goto('/chat');
    await expect(page.getByText('No conversations yet')).toBeVisible();
  });

  test('shows created conversations in the sidebar', async ({ page, request }) => {
    await createAndLoginUser(page, request, 'chat-sidebar');
    await createConversation(page, 'Test Conversation');
    await createConversation(page, 'Second Chat', 'gemini');

    await page.goto('/chat');
    await expect(page.getByText('Test Conversation')).toBeVisible();
    await expect(page.getByText('Second Chat')).toBeVisible();
  });

  test('shows last message preview in the list', async ({ page, request }) => {
    test.slow();
    await createAndLoginUser(page, request, 'chat-preview');
    await createConversation(page, 'Preview Conversation');
    await sendMessageWithButton(page, 'Summarize this chat for me.');

    const preview = await waitForPreviewText(page, 'Preview Conversation');
    expect(preview.length).toBeGreaterThan(0);
  });
});

test.describe('Chat page – new conversation modal', () => {
  test('clicking "+ New Conversation" opens the modal', async ({ page, request }) => {
    await createAndLoginUser(page, request, 'chat-modal-open');
    await openNewConversationModal(page);
    await expect(page.getByPlaceholder('New Chat')).toBeVisible();
  });

  test('modal has provider and model fields', async ({ page, request }) => {
    await createAndLoginUser(page, request, 'chat-modal-fields');
    await openNewConversationModal(page);
    await expect(page.locator('select')).toBeVisible();
    await expect(page.getByLabel('Model')).toBeVisible();
  });

  test('provider options include Groq, Gemini, and DeepSeek', async ({ page, request }) => {
    await createAndLoginUser(page, request, 'chat-provider-options');
    await openNewConversationModal(page);

    const select = page.locator('select');
    await expect(select.locator('option', { hasText: 'Groq' })).toBeAttached();
    await expect(select.locator('option', { hasText: 'Gemini' })).toBeAttached();
    await expect(select.locator('option', { hasText: 'DeepSeek' })).toBeAttached();
  });

  test('changing provider updates the default model', async ({ page, request }) => {
    await createAndLoginUser(page, request, 'chat-provider-model');
    await openNewConversationModal(page);

    await expect(page.getByLabel('Model')).toHaveValue('llama-3.1-8b-instant');
    await page.locator('select').selectOption('gemini');
    await expect(page.getByLabel('Model')).toHaveValue('gemini-2.5-flash');
    await page.locator('select').selectOption('deepseek');
    await expect(page.getByLabel('Model')).toHaveValue('deepseek-chat');
  });

  test('Cancel button closes the modal', async ({ page, request }) => {
    await createAndLoginUser(page, request, 'chat-modal-cancel');
    await openNewConversationModal(page);

    await page.getByRole('button', { name: 'Cancel' }).click();
    await expect(page.getByRole('heading', { name: 'New Conversation' })).not.toBeVisible();
  });

  test('creating a conversation persists it in the UI', async ({ page, request }) => {
    await createAndLoginUser(page, request, 'chat-modal-create');
    await createConversation(page, 'My E2E Chat');

    await expect(page.getByRole('heading', { name: 'My E2E Chat' })).toBeVisible();
    await expect(conversationListItem(page, 'My E2E Chat')).toBeVisible();
  });
});

test.describe('Chat page – selecting a conversation', () => {
  test('shows empty state when no conversation is selected', async ({ page, request }) => {
    await createAndLoginUser(page, request, 'chat-empty-selected');
    await createConversation(page, 'Selection Test Conversation');

    await page.goto('/chat');
    await expect(page.getByText('No conversation selected')).toBeVisible();
  });

  test('clicking a conversation opens the chat window', async ({ page, request }) => {
    await createAndLoginUser(page, request, 'chat-open-conversation');
    await createConversation(page, 'Test Conversation');

    await page.goto('/chat');
    await openConversationFromList(page, 'Test Conversation');
    await expect(page.getByText(/groq/i)).toBeVisible();
  });

  test('selected conversation shows the chat input textarea', async ({ page, request }) => {
    await createAndLoginUser(page, request, 'chat-input-visible');
    await createConversation(page, 'Input Test Conversation');

    await page.goto('/chat');
    await openConversationFromList(page, 'Input Test Conversation');
    await expect(page.getByPlaceholder(/Type your message/i)).toBeVisible();
  });
});

test.describe('Chat page – chat input', () => {
  test('send button is disabled when textarea is empty', async ({ page, request }) => {
    await createAndLoginUser(page, request, 'chat-send-disabled');
    await createConversation(page, 'Disabled Send Conversation');

    const sendButton = page.locator('form').getByRole('button');
    await expect(sendButton).toBeDisabled();
  });

  test('send button becomes enabled after typing a message', async ({ page, request }) => {
    await createAndLoginUser(page, request, 'chat-send-enabled');
    await createConversation(page, 'Enabled Send Conversation');

    await page.getByPlaceholder(/Type your message/i).fill('Hello, AI!');
    const sendButton = page.locator('form').getByRole('button');
    await expect(sendButton).toBeEnabled();
  });

  test('pressing Enter sends the message', async ({ page, request }) => {
    test.slow();
    await createAndLoginUser(page, request, 'chat-enter-send');
    await createConversation(page, 'Enter Send Conversation');

    const responsePromise = page.waitForResponse(
      response =>
        response.url().includes('/messages/send')
        && response.request().method() === 'POST',
    );

    const textarea = page.getByPlaceholder(/Type your message/i);
    await textarea.fill('Hello, AI!');
    await textarea.press('Enter');

    const response = await responsePromise;
    expect(response.ok()).toBeTruthy();
    await expect(page.getByText('Hello, AI!', { exact: true })).toBeVisible();
  });

  test('Shift+Enter adds a newline instead of sending', async ({ page, request }) => {
    await createAndLoginUser(page, request, 'chat-shift-enter');
    await createConversation(page, 'Shift Enter Conversation');

    const textarea = page.getByPlaceholder(/Type your message/i);
    await textarea.fill('line one');
    await textarea.press('Shift+Enter');
    await textarea.type('line two');

    await expect(textarea).toHaveValue('line one\nline two');
  });
});

test.describe('Chat page – deleting a conversation', () => {
  test('hovering a conversation reveals the delete button', async ({ page, request }) => {
    await createAndLoginUser(page, request, 'chat-delete-hover');
    await createConversation(page, 'Delete Hover Conversation');

    await hoverConversation(page, 'Delete Hover Conversation');
    await expect(conversationDeleteButton(page, 'Delete Hover Conversation')).toBeVisible();
  });

  test('clicking delete removes the conversation from the list', async ({ page, request }) => {
    await createAndLoginUser(page, request, 'chat-delete-remove');
    await createConversation(page, 'Delete Me Conversation');

    await expect(conversationListItem(page, 'Delete Me Conversation')).toBeVisible();
    await hoverConversation(page, 'Delete Me Conversation');
    await conversationDeleteButton(page, 'Delete Me Conversation').click();

    await expect(conversationListItem(page, 'Delete Me Conversation')).not.toBeVisible();
  });
});
