import { useState, type FormEvent } from 'react';
import { Button, Input, TextArea } from '@/components/ui';

interface CreateRoleFormProps {
  onSubmit: (data: { label: string; description: string; permissions: string[] }) => Promise<void>;
  onCancel: () => void;
}

export function CreateRoleForm({ onSubmit, onCancel }: CreateRoleFormProps) {
  const [label, setLabel] = useState('');
  const [description, setDescription] = useState('');
  const [permissions, setPermissions] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      await onSubmit({
        label,
        description,
        permissions: permissions.split(',').map(p => p.trim()).filter(Boolean),
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <Input label="Role Label" value={label} onChange={e => setLabel(e.target.value)} required />
      <TextArea label="Description" value={description} onChange={e => setDescription(e.target.value)} required />
      <Input label="Permissions (comma-separated)" value={permissions} onChange={e => setPermissions(e.target.value)} placeholder="chat, admin.dashboard" />
      <div className="flex justify-end gap-2 pt-2">
        <Button variant="secondary" type="button" onClick={onCancel}>Cancel</Button>
        <Button type="submit" isLoading={isLoading}>Save</Button>
      </div>
    </form>
  );
}
