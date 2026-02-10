import { useEffect, useState } from 'react';
import type { Role } from '@/types';
import { roleService } from '@/services';
import { Card, DataTable, Button, Modal, Badge, Spinner, SearchBar } from '@/components/ui';
import { CreateRoleForm } from '@/components/forms/CreateRoleForm';

export function RoleManagementPage() {
  const [roles, setRoles] = useState<Role[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [search, setSearch] = useState('');
  const [editingRole, setEditingRole] = useState<Role | null>(null);

  useEffect(() => {
    roleService.getAll().then(data => {
      setRoles(data);
      setIsLoading(false);
    });
  }, []);

  const handleSave = async (data: { label: string; description: string; permissions: string[] }) => {
    if (editingRole) {
      const updated = await roleService.update(editingRole.id, data);
      setRoles(prev => prev.map(r => (r.id === updated.id ? updated : r)));
    }
    setIsModalOpen(false);
    setEditingRole(null);
  };

  const filtered = roles.filter(r =>
    r.label.toLowerCase().includes(search.toLowerCase()) ||
    r.name.toLowerCase().includes(search.toLowerCase()),
  );

  const columns = [
    { key: 'name', header: 'Role', render: (r: Role) => <span className="font-medium text-gray-200">{r.label}</span> },
    { key: 'description', header: 'Description', render: (r: Role) => <span className="text-gray-400">{r.description}</span>, className: 'px-4 py-3 text-sm text-gray-400 max-w-xs truncate' },
    {
      key: 'permissions',
      header: 'Permissions',
      render: (r: Role) => (
        <div className="flex flex-wrap gap-1">
          {r.permissions.map(p => <Badge key={p} variant="info">{p}</Badge>)}
        </div>
      ),
    },
    { key: 'users', header: 'Users', render: (r: Role) => <span className="text-gray-300">{r.userCount}</span> },
    {
      key: 'actions',
      header: '',
      render: (r: Role) => (
        <Button size="sm" variant="ghost" onClick={() => { setEditingRole(r); setIsModalOpen(true); }}>
          Edit
        </Button>
      ),
    },
  ];

  if (isLoading) return <Spinner className="mt-20" />;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <h1 className="text-2xl font-bold text-gray-100">Role Management</h1>
      </div>

      <Card padding={false}>
        <div className="p-4 border-b border-gray-800">
          <SearchBar value={search} onChange={setSearch} placeholder="Search roles..." />
        </div>
        <DataTable columns={columns} data={filtered} keyExtractor={r => r.id} emptyMessage="No roles found" />
      </Card>

      <Modal isOpen={isModalOpen} onClose={() => { setIsModalOpen(false); setEditingRole(null); }} title={editingRole ? 'Edit Role' : 'Create Role'}>
        <CreateRoleForm onSubmit={handleSave} onCancel={() => { setIsModalOpen(false); setEditingRole(null); }} />
      </Modal>
    </div>
  );
}
