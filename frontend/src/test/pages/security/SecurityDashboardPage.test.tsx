import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { SecurityDashboardPage } from '@/pages/security/SecurityDashboardPage';
import { securityService } from '@/services';
import type { HistoricChatDashboard } from '@/types';

vi.mock('@/services', () => ({
  securityService: {
    getHistoricChatDashboard: vi.fn(),
  },
}));

function buildDashboard(overrides?: Partial<HistoricChatDashboard>): HistoricChatDashboard {
  return {
    items: [
      {
        conversationId: 'conversation-1',
        title: 'Incident Review',
        userId: 'user-1',
        userEmail: 'analyst@example.com',
        provider: 'groq',
        model: 'llama-3.1-8b-instant',
        createdAt: '2026-04-08T10:00:00Z',
        lastActivityAt: '2026-04-08T11:00:00Z',
        messageCount: 2,
        messages: [
          {
            id: 'message-1',
            role: 'user',
            content: 'How many incidents were reported yesterday?',
            createdAt: '2026-04-08T10:30:00Z',
          },
          {
            id: 'message-2',
            role: 'assistant',
            content: 'Three incidents were reported yesterday.',
            createdAt: '2026-04-08T11:00:00Z',
          },
        ],
      },
    ],
    total: 1,
    limit: 10,
    offset: 0,
    summary: {
      totalHistories: 1,
      totalMessages: 2,
      recentActivity: 2,
      uniqueUsers: 1,
    },
    ...overrides,
  };
}

describe('SecurityDashboardPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders live historic chat data from the security service', async () => {
    vi.mocked(securityService.getHistoricChatDashboard).mockResolvedValue(buildDashboard());

    render(<SecurityDashboardPage />);

    expect(await screen.findByText('analyst@example.com')).toBeInTheDocument();
    expect(screen.getByText('Incident Review')).toBeInTheDocument();
    expect(screen.getByText('How many incidents were reported yesterday?')).toBeInTheDocument();
    expect(screen.getByText('Three incidents were reported yesterday.')).toBeInTheDocument();
    expect(screen.getByText('Total Histories')).toBeInTheDocument();
    expect(screen.getByText('Showing 1-1 of 1 histories')).toBeInTheDocument();
    expect(securityService.getHistoricChatDashboard).toHaveBeenCalledWith(10, 0);
  });

  it('requests the next page when pagination advances', async () => {
    vi.mocked(securityService.getHistoricChatDashboard)
      .mockResolvedValueOnce(buildDashboard({ total: 11 }))
      .mockResolvedValueOnce(
        buildDashboard({
          items: [
            {
              conversationId: 'conversation-2',
              title: 'Follow-up Review',
              userId: 'user-2',
              userEmail: 'responder@example.com',
              provider: 'deepseek',
              model: 'deepseek-chat',
              createdAt: '2026-04-09T09:00:00Z',
              lastActivityAt: '2026-04-09T09:10:00Z',
              messageCount: 1,
              messages: [
                {
                  id: 'message-3',
                  role: 'user',
                  content: 'Show the final summary.',
                  createdAt: '2026-04-09T09:10:00Z',
                },
              ],
            },
          ],
          total: 11,
          offset: 10,
        }),
      );

    render(<SecurityDashboardPage />);

    await screen.findByText('Incident Review');

    const user = userEvent.setup();
    await user.click(screen.getByRole('button', { name: 'Next' }));

    await waitFor(() => {
      expect(securityService.getHistoricChatDashboard).toHaveBeenNthCalledWith(2, 10, 10);
    });
    expect(await screen.findByText('Follow-up Review')).toBeInTheDocument();
    expect(screen.getByText('responder@example.com')).toBeInTheDocument();
  });
});
