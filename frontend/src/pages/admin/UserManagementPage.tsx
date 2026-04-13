import { useEffect, useState } from 'react';
import type { User, UserRole } from '@/types';
import { userService } from '@/services';
import { Card, DataTable, Button, Modal, Badge, Spinner, SearchBar } from '@/components/ui';
import { InviteUserForm } from '@/components/forms/InviteUserForm';

const roleBadgeVariant: Record<UserRole, 'default' | 'success' | 'warning' | 'danger' | 'info'> = {
  user: 'info',
  admin: 'danger',
  security: 'warning',
};

const roleOptions: UserRole[] = ['user', 'admin', 'security'];

export function UserManagementPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [search, setSearch] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [editingRoleUserId, setEditingRoleUserId] = useState<string | null>(null);
  const [updatingRoleUserId, setUpdatingRoleUserId] = useState<string | null>(null);
  const [removingUserId, setRemovingUserId] = useState<string | null>(null);

  const getDisplayName = (user: User) => user.fullName ?? user.name ?? user.email;
  const getRoleVariant = (user: User) => user.role ? roleBadgeVariant[user.role] : 'default';
  const formatTimestamp = (value?: string, fallback = 'N/A') => (
    value ? new Date(value).toLocaleString() : fallback
  );

  useEffect(() => {
    const loadUsers = async () => {
      try {
        setError(null);
        setUsers(await userService.getAll());
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load users.');
      } finally {
        setIsLoading(false);
      }
    };

    void loadUsers();
  }, []);

  const handleInvite = async (data: { name: string; email: string; role: UserRole }) => {
    try {
      setError(null);
      const newUser = await userService.create(data);
      setUsers(prev => [...prev, newUser]);
      setIsModalOpen(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to invite user.');
    }
  };

  const handleDelete = async (id: string) => {
    try {
      setError(null);
      setRemovingUserId(id);
      await userService.remove(id);
      setUsers(prev => prev.filter(u => u.id !== id));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to remove user.');
    } finally {
      setRemovingUserId(null);
    }
  };

  const handleRoleChange = async (id: string, role: UserRole) => {
    try {
      setError(null);
      setUpdatingRoleUserId(id);
      const updatedUser = await userService.updateRole(id, role);
      setUsers(prev => prev.map(user => (user.id === updatedUser.id ? updatedUser : user)));
      setEditingRoleUserId(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update user role.');
    } finally {
      setUpdatingRoleUserId(null);
    }
  };

  const filtered = users.filter(u => {
    const displayName = getDisplayName(u);
    const query = search.toLowerCase();
    return (
      displayName.toLowerCase().includes(query) ||
      u.email.toLowerCase().includes(query)
    );
  });

  const columns = [
    { key: 'name', header: 'Name', render: (u: User) => (
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-full bg-aegis-900 text-aegis-400 flex items-center justify-center text-sm font-medium">
          {getDisplayName(u).charAt(0).toUpperCase()}
        </div>
        <div>
          <p className="font-medium text-gray-200">{getDisplayName(u)}</p>
          <p className="text-xs text-gray-500">{u.email}</p>
        </div>
      </div>
    )},
    {
      key: 'role',
      header: 'Role',
      render: (u: User) => (
        editingRoleUserId === u.id ? (
          <select
            autoFocus
            value={u.role ?? 'user'}
            disabled={updatingRoleUserId === u.id}
            onBlur={() => {
              if (updatingRoleUserId !== u.id) {
                setEditingRoleUserId(current => (current === u.id ? null : current));
              }
            }}
            onChange={event => {
              const nextRole = event.target.value as UserRole;
              if (nextRole === u.role) {
                setEditingRoleUserId(null);
                return;
              }
              void handleRoleChange(u.id, nextRole);
            }}
            className="rounded-full border border-gray-600 bg-gray-800 px-3 py-1 text-xs font-medium text-gray-100 focus:border-aegis-500 focus:outline-none focus:ring-2 focus:ring-aegis-500"
          >
            {roleOptions.map(role => (
              <option key={role} value={role}>
                {role}
              </option>
            ))}
          </select>
        ) : (
          <button
            type="button"
            onClick={() => setEditingRoleUserId(u.id)}
            className="rounded-full focus:outline-none focus:ring-2 focus:ring-aegis-500 focus:ring-offset-2 focus:ring-offset-gray-900"
          >
            <Badge variant={getRoleVariant(u)}>
              {u.role ?? 'unassigned'}
            </Badge>
          </button>
        )
      ),
    },
    {
      key: 'created',
      header: 'Created',
      render: (u: User) => (
        <span className="text-gray-400">
          {formatTimestamp(u.createdAt)}
        </span>
      ),
    },
    {
      key: 'lastLogin',
      header: 'Last Login',
      render: (u: User) => <span className="text-gray-400">{formatTimestamp(u.lastLogin, 'Never')}</span>,
    },
    { key: 'actions', header: '', render: (u: User) => (
      <Button
        size="sm"
        variant="danger"
        isLoading={removingUserId === u.id}
        disabled={updatingRoleUserId === u.id}
        onClick={() => void handleDelete(u.id)}
      >
        Remove
      </Button>
    )},
  ];

  if (isLoading) return <Spinner className="mt-20" />;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <h1 className="text-2xl font-bold text-gray-100">User Management</h1>
        <Button onClick={() => setIsModalOpen(true)}>Invite User</Button>
      </div>

      {error && (
        <div className="rounded-lg border border-red-800 bg-red-950/40 px-4 py-3 text-sm text-red-200">
          {error}
        </div>
      )}

      <Card padding={false}>
        <div className="p-4 border-b border-gray-800">
          <SearchBar value={search} onChange={setSearch} placeholder="Search users..." />
        </div>
        <DataTable columns={columns} data={filtered} keyExtractor={u => u.id} emptyMessage="No users found" />
      </Card>

      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title="Invite User">
        <InviteUserForm onSubmit={handleInvite} onCancel={() => setIsModalOpen(false)} />
      </Modal>
    </div>
  );
}
