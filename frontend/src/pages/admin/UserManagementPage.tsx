import { useEffect, useState } from 'react';
import type { User, UserRole } from '@/types';
import { userService } from '@/services';
import { Card, DataTable, Button, Modal, Badge, Spinner, SearchBar } from '@/components/ui';
import { InviteUserForm } from '@/components/forms/InviteUserForm';

const roleBadgeVariant: Record<UserRole, 'default' | 'success' | 'warning' | 'danger' | 'info'> = {
  admin: 'danger',
  security: 'warning',
  it: 'info',
  hr: 'success',
  finance: 'default',
};

export function UserManagementPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [search, setSearch] = useState('');

  const getDisplayName = (user: User) => user.name ?? user.email;
  const getRoleVariant = (user: User) => user.role ? roleBadgeVariant[user.role] : 'default';

  useEffect(() => {
    userService.getAll().then(data => {
      setUsers(data);
      setIsLoading(false);
    });
  }, []);

  const handleInvite = async (data: { name: string; email: string; role: UserRole }) => {
    const newUser = await userService.create(data);
    setUsers(prev => [...prev, newUser]);
    setIsModalOpen(false);
  };

  const handleDelete = async (id: string) => {
    await userService.remove(id);
    setUsers(prev => prev.filter(u => u.id !== id));
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
        <Badge variant={getRoleVariant(u)}>
          {u.role ?? 'unassigned'}
        </Badge>
      ),
    },
    {
      key: 'created',
      header: 'Created',
      render: (u: User) => (
        <span className="text-gray-400">
          {u.createdAt ? new Date(u.createdAt).toLocaleDateString() : 'N/A'}
        </span>
      ),
    },
    { key: 'lastLogin', header: 'Last Login', render: (u: User) => <span className="text-gray-400">{u.lastLogin ? new Date(u.lastLogin).toLocaleDateString() : 'Never'}</span> },
    { key: 'actions', header: '', render: (u: User) => (
      <Button size="sm" variant="danger" onClick={() => handleDelete(u.id)}>Remove</Button>
    )},
  ];

  if (isLoading) return <Spinner className="mt-20" />;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <h1 className="text-2xl font-bold text-gray-100">User Management</h1>
        <Button onClick={() => setIsModalOpen(true)}>Invite User</Button>
      </div>

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
