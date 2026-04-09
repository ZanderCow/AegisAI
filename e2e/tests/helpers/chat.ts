/**
 * Shared Playwright helpers for chat and conversation management flows.
 *
 * These helpers keep the chat specs focused on behavior by centralizing the
 * selectors and request waits needed for conversation CRUD interactions.
 */
import { expect, type Locator, type Page } from '@playwright/test';

/** Providers supported by the new-conversation modal in E2E tests. */
type ProviderName = 'groq' | 'gemini' | 'deepseek';

/** Default model values expected after a provider selection changes. */
const DEFAULT_MODELS: Record<ProviderName, string> = {
  groq: 'llama-3.1-8b-instant',
  gemini: 'gemini-2.5-flash',
  deepseek: 'deepseek-chat',
};

/**
 * Locates a conversation list row by its title.
 *
 * @param page - Playwright page used for browser interaction.
 * @param title - Visible conversation title.
 * @returns The first matching list item locator.
 */
export function conversationListItem(page: Page, title: string): Locator {
  return page.locator('li').filter({ hasText: title }).first();
}

/**
 * Opens the new-conversation modal and waits for it to become visible.
 *
 * @param page - Playwright page used for browser interaction.
 * @returns A promise that resolves once the modal heading is visible.
 */
export async function openNewConversationModal(page: Page): Promise<void> {
  await page.getByRole('button', { name: '+ New Conversation' }).click();
  await expect(page.getByRole('heading', { name: 'New Conversation' })).toBeVisible();
}

/**
 * Creates a conversation through the modal using the requested provider and model.
 *
 * @param page - Playwright page used for browser interaction.
 * @param title - Conversation title shown in the sidebar and header.
 * @param provider - Provider selected in the modal.
 * @param model - Model value typed into the modal after provider selection.
 * @returns A promise that resolves once the new conversation is active in the UI.
 */
export async function createConversation(
  page: Page,
  title: string,
  provider: ProviderName = 'groq',
  model = DEFAULT_MODELS[provider],
): Promise<void> {
  await openNewConversationModal(page);
  await page.getByLabel('Title (optional)').fill(title);

  if (provider !== 'groq') {
    await page.locator('select').selectOption(provider);
  }
  await expect(page.getByLabel('Model')).toHaveValue(DEFAULT_MODELS[provider]);

  if (model !== DEFAULT_MODELS[provider]) {
    await page.getByLabel('Model').fill(model);
  }

  await page.getByRole('button', { name: 'Create' }).click();
  await expect(page.getByRole('heading', { name: 'New Conversation' })).not.toBeVisible();
  await expect(page.getByRole('heading', { name: title })).toBeVisible();
}

/**
 * Opens an existing conversation from the sidebar.
 *
 * @param page - Playwright page used for browser interaction.
 * @param title - Conversation title displayed in the sidebar.
 * @returns A promise that resolves once the conversation header is visible.
 */
export async function openConversationFromList(page: Page, title: string): Promise<void> {
  await conversationListItem(page, title).click();
  await expect(page.getByRole('heading', { name: title })).toBeVisible();
}

/**
 * Sends a message through the chat form and waits for the send request to complete.
 *
 * @param page - Playwright page used for browser interaction.
 * @param content - Message content entered into the chat textarea.
 * @param completionTimeoutMs - Maximum time to wait for the textarea to re-enable.
 * @returns A promise that resolves after the echoed user message is visible.
 */
export async function sendMessageWithButton(
  page: Page,
  content: string,
  completionTimeoutMs = 60_000,
): Promise<void> {
  const textarea = page.getByPlaceholder(/Type your message/i);
  const responsePromise = page.waitForResponse(
    response =>
      response.url().includes('/messages/send')
      && response.request().method() === 'POST',
  );

  await textarea.fill(content);
  await page.locator('form').getByRole('button').click();

  const response = await responsePromise;
  expect(response.ok()).toBeTruthy();
  await expect(page.getByText(content, { exact: true })).toBeVisible();
  await expect(textarea).toBeEnabled({ timeout: completionTimeoutMs });
}

/**
 * Polls the sidebar until a conversation preview contains non-empty text.
 *
 * @param page - Playwright page used for browser interaction.
 * @param title - Conversation title whose preview should be inspected.
 * @returns The trimmed preview text once the backend response has updated it.
 */
export async function waitForPreviewText(page: Page, title: string): Promise<string> {
  const item = conversationListItem(page, title);
  await expect(item).toBeVisible();

  await expect
    .poll(async () => {
      const preview = item.locator('p.text-xs.text-gray-500').first();
      if ((await preview.count()) === 0) {
        return '';
      }
      return (await preview.textContent())?.trim() ?? '';
    }, { timeout: 30_000 })
    .not.toBe('');

  const preview = item.locator('p.text-xs.text-gray-500').first();
  return ((await preview.textContent()) ?? '').trim();
}

/**
 * Hovers a sidebar conversation row so hover-only controls become visible.
 *
 * @param page - Playwright page used for browser interaction.
 * @param title - Conversation title displayed in the sidebar.
 * @returns A promise that resolves after the hover interaction completes.
 */
export async function hoverConversation(page: Page, title: string): Promise<void> {
  await conversationListItem(page, title).hover();
}

/**
 * Locates the delete button rendered inside a conversation row.
 *
 * @param page - Playwright page used for browser interaction.
 * @param title - Conversation title displayed in the sidebar.
 * @returns The delete button locator scoped to the conversation row.
 */
export function conversationDeleteButton(page: Page, title: string): Locator {
  return conversationListItem(page, title).locator('button');
}
