import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { UserManagementPage } from '@/pages/admin/UserManagementPage';
import { userService } from '@/services';
import type { User } from '@/types';

vi.mock('@/services', () => ({
  userService: {
    getAll: vi.fn(),
    create: vi.fn(),
    updateRole: vi.fn(),
    remove: vi.fn(),
  },
}));

function buildUser(overrides?: Partial<User>): User {
  return {
    id: 'user-1',
    email: 'alex@example.com',
    name: 'Alex Admin',
    fullName: 'Alex Admin',
    role: 'admin',
    createdAt: '2026-04-10T12:00:00Z',
    lastLogin: '2026-04-11T09:15:00Z',
    ...overrides,
  };
}

describe('UserManagementPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders live users from the service and filters by search text', async () => {
    vi.mocked(userService.getAll).mockResolvedValue([
      buildUser(),
      buildUser({
        id: 'user-2',
        email: 'casey@example.com',
        name: 'Casey Member',
        fullName: 'Casey Member',
        role: 'user',
      }),
    ]);

    render(<UserManagementPage />);

    expect(await screen.findByText('Alex Admin')).toBeInTheDocument();
    expect(screen.getByText('Casey Member')).toBeInTheDocument();

    const user = userEvent.setup();
    await user.type(screen.getByPlaceholderText('Search users...'), 'casey@example.com');

    await waitFor(() => {
      expect(screen.queryByText('Alex Admin')).not.toBeInTheDocument();
      expect(screen.getByText('Casey Member')).toBeInTheDocument();
    });
  });

  it('updates roles inline and removes rows through the live service layer', async () => {
    vi.mocked(userService.getAll).mockResolvedValue([
      buildUser(),
      buildUser({
        id: 'user-2',
        email: 'casey@example.com',
        name: 'Casey Member',
        fullName: 'Casey Member',
        role: 'user',
      }),
    ]);
    vi.mocked(userService.updateRole).mockResolvedValue(
      buildUser({
        role: 'security',
      }),
    );
    vi.mocked(userService.remove).mockResolvedValue(undefined);

    render(<UserManagementPage />);
    expect(await screen.findByText('Alex Admin')).toBeInTheDocument();

    const user = userEvent.setup();
    await user.click(screen.getByRole('button', { name: 'admin' }));
    await user.selectOptions(screen.getByRole('combobox'), 'security');

    await waitFor(() => {
      expect(userService.updateRole).toHaveBeenCalledWith('user-1', 'security');
    });
    expect(await screen.findByRole('button', { name: 'security' })).toBeInTheDocument();

    await user.click(screen.getAllByRole('button', { name: 'Remove' })[0]);

    await waitFor(() => {
      expect(userService.remove).toHaveBeenCalledWith('user-1');
    });
    expect(screen.queryByText('Alex Admin')).not.toBeInTheDocument();
  });
});
