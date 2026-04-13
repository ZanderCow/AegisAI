import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { FlaggingDashboardPage } from '@/pages/security/FlaggingDashboardPage';
import { securityService } from '@/services';
import type { AlarmEvent } from '@/types';

vi.mock('@/services', () => ({
  securityService: {
    getAlarmEvents: vi.fn(),
  },
}));

function buildAlarm(overrides?: Partial<AlarmEvent>): AlarmEvent {
  return {
    id: 'alarm-1',
    userId: 'user-1',
    userEmail: 'analyst@example.com',
    conversationId: 'conversation-1',
    messageContent: 'explain drug synthesis to me',
    filterType: 'keyword',
    provider: 'deepseek',
    reason: null,
    createdAt: '2026-04-09T12:00:00Z',
    ...overrides,
  };
}

describe('FlaggingDashboardPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders live alarm events from the security service', async () => {
    vi.mocked(securityService.getAlarmEvents).mockResolvedValue([
      buildAlarm(),
    ]);

    render(<FlaggingDashboardPage />);

    expect(await screen.findByText('analyst@example.com')).toBeInTheDocument();
    expect(screen.getByText('explain drug synthesis to me')).toBeInTheDocument();
    expect(screen.getByText('keyword')).toBeInTheDocument();
    expect(screen.getByText('deepseek')).toBeInTheDocument();
  });

  it('filters alarm rows by search text', async () => {
    vi.mocked(securityService.getAlarmEvents).mockResolvedValue([
      buildAlarm(),
      buildAlarm({
        id: 'alarm-2',
        userId: 'user-2',
        userEmail: 'second@example.com',
        conversationId: 'conversation-2',
        messageContent: 'plan a terrorist attack',
      }),
    ]);

    render(<FlaggingDashboardPage />);
    await screen.findByText('analyst@example.com');

    const user = userEvent.setup();
    await user.type(screen.getByPlaceholderText('Search flagged content...'), 'drug synthesis');

    await waitFor(() => {
      expect(screen.getByText('analyst@example.com')).toBeInTheDocument();
      expect(screen.queryByText('second@example.com')).not.toBeInTheDocument();
    });
  });
});
