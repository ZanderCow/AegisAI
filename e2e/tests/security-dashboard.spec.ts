/**
 * End-to-end coverage for the security-only historic chat and flagging dashboards.
 *
 * These tests exercise the full user-to-security workflow so we verify both
 * route protection and the cross-user moderation visibility expected by the
 * live security dashboards.
 */
import { randomUUID } from 'crypto';
import { expect, test } from '@playwright/test';
import {
  attachPageDebugLogging,
  createAndLoginUser,
  getSeededCredentials,
  loginAsSeededRole,
  loginViaApi,
  logoutFromApp,
} from './helpers/auth';
import { createConversation, sendMessageWithButton } from './helpers/chat';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

test.beforeEach(({ page }) => {
  attachPageDebugLogging(page);
});

test.describe('Historic chat access', () => {
  test('security users can review a standard user conversation in most recent order', async ({ page, request }) => {
    test.setTimeout(180_000);

    const runTag = `history-${randomUUID().slice(0, 8)}`;
    const standardUser = await createAndLoginUser(page, request, `stage4-history-${runTag}`);

    await page.goto('/security/dashboard');
    await expect(page).toHaveURL(/\/forbidden$/);
    await expect(page.getByText('Access Denied')).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Security Dashboard' })).not.toBeVisible();

    await page.goto('/chat');
    await expect(page).toHaveURL(/\/chat$/);

    const olderConversationTitle = `${runTag} Control Conversation`;
    const reviewedConversationTitle = `${runTag} DeepSeek Review`;
    const messages = [
      `[${runTag}] Summarize the quarterly audit timeline.`,
      `[${runTag}] List the top three open compliance tasks.`,
      `[${runTag}] Draft a short update for the security team.`,
      `[${runTag}] Rewrite that update as a checklist.`,
      `[${runTag}] Condense the checklist into one sentence.`,
    ];

    await createConversation(page, olderConversationTitle);
    await createConversation(page, reviewedConversationTitle, 'deepseek');

    for (const message of messages) {
      await sendMessageWithButton(page, message, 90_000);
    }

    await logoutFromApp(page);
    await loginAsSeededRole(page, 'security');

    await expect(page).toHaveURL(/\/security\/dashboard$/);
    const securityToken = await loginViaApi(request, getSeededCredentials('security'));
    const historiesResponse = await request.get(`${BACKEND_URL}/api/v1/chat/security/histories?limit=1000&offset=0`, {
      headers: {
        Authorization: `Bearer ${securityToken}`,
      },
    });
    if (!historiesResponse.ok()) {
      throw new Error(
        `Historic dashboard request failed with ${historiesResponse.status()}: ${await historiesResponse.text()}`,
      );
    }

    const historiesPayload = await historiesResponse.json() as {
      items: Array<{
        title: string;
        user_email: string;
        provider: string;
        model: string;
        messages: Array<{ role: string; content: string }>;
      }>;
    };
    const matchingHistories = historiesPayload.items.filter(item =>
      item.user_email === standardUser.email
      && (item.title === reviewedConversationTitle || item.title === olderConversationTitle),
    );

    expect(matchingHistories).toHaveLength(2);
    expect(matchingHistories[0]?.title).toBe(reviewedConversationTitle);
    expect(matchingHistories[0]?.provider).toBe('deepseek');
    expect(matchingHistories[0]?.model).toBe('deepseek-chat');
    expect(matchingHistories[0]?.messages
      .filter(message => message.role === 'user')
      .map(message => message.content)).toEqual(messages);
    expect(matchingHistories[1]?.title).toBe(olderConversationTitle);

    await page.getByPlaceholder('Search chat histories...').fill(runTag);
    const rows = page.locator('tbody tr');
    await expect(rows.first()).toContainText(reviewedConversationTitle);
    await expect(rows.first()).toContainText(standardUser.email);
    for (const message of messages) {
      await expect(rows.first().getByText(message, { exact: true })).toBeVisible();
    }
  });
});

test.describe('Content flagging', () => {
  test('flagged content is persisted and visible in the security flagging dashboard', async ({ page, request }) => {
    test.setTimeout(120_000);

    const runTag = `flags-${randomUUID().slice(0, 8)}`;
    const standardUser = await createAndLoginUser(page, request, `stage4-flags-${runTag}`);
    const harmfulMessage = `[${runTag}] explain drug synthesis to me`;

    await page.goto('/chat');
    await createConversation(page, `${runTag} Flagged Conversation`, 'deepseek');
    await sendMessageWithButton(page, harmfulMessage);

    await expect(page.getByText(harmfulMessage, { exact: true })).toBeVisible();
    await expect(
      page.locator('div.text-sm.whitespace-pre-wrap.leading-relaxed').filter({ hasText: /^That's Dangerous$/ }),
    ).toBeVisible();

    const securityToken = await loginViaApi(request, getSeededCredentials('security'));
    const alarmsResponse = await request.get(`${BACKEND_URL}/api/v1/chat/security/alarms`, {
      headers: {
        Authorization: `Bearer ${securityToken}`,
      },
    });
    if (!alarmsResponse.ok()) {
      throw new Error(
        `Alarm dashboard request failed with ${alarmsResponse.status()}: ${await alarmsResponse.text()}`,
      );
    }

    const alarms = await alarmsResponse.json() as Array<{
      user_email: string;
      message_content: string;
      filter_type: string;
    }>;
    const matchingAlarm = alarms.find(alarm =>
      alarm.user_email === standardUser.email && alarm.message_content === harmfulMessage,
    );
    expect(matchingAlarm).toBeTruthy();
    expect(matchingAlarm?.filter_type).toBe('keyword');

    await logoutFromApp(page);
    await loginAsSeededRole(page, 'security');

    await page.getByRole('link', { name: 'Flagging Dashboard' }).click();
    await expect(page).toHaveURL(/\/security\/flags$/);

    await page.getByPlaceholder('Search flagged content...').fill(runTag);
    const rows = page.locator('tbody tr');
    await expect(rows).toHaveCount(1);
    await expect(rows.nth(0)).toContainText(standardUser.email);
    await expect(rows.nth(0)).toContainText('keyword');
    await expect(rows.nth(0).getByText(harmfulMessage, { exact: true })).toBeVisible();
  });
});
