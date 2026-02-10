import { useState, type FormEvent } from 'react';
import { Button, Input, Select } from '@/components/ui';
import type { UserRole } from '@/types';

interface InviteUserFormProps {
  onSubmit: (data: { name: string; email: string; role: UserRole }) => Promise<void>;
  onCancel: () => void;
}

const roleOptions = [
  { value: 'it', label: 'IT Staff' },
  { value: 'hr', label: 'Human Resources' },
  { value: 'finance', label: 'Finance' },
  { value: 'security', label: 'Security Analyst' },
  { value: 'admin', label: 'Administrator' },
];

export function InviteUserForm({ onSubmit, onCancel }: InviteUserFormProps) {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [role, setRole] = useState<UserRole>('it');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      await onSubmit({ name, email, role });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <Input label="Full Name" value={name} onChange={e => setName(e.target.value)} required />
      <Input label="Email" type="email" value={email} onChange={e => setEmail(e.target.value)} required />
      <Select label="Role" options={roleOptions} value={role} onChange={e => setRole(e.target.value as UserRole)} />
      <div className="flex justify-end gap-2 pt-2">
        <Button variant="secondary" type="button" onClick={onCancel}>Cancel</Button>
        <Button type="submit" isLoading={isLoading}>Invite User</Button>
      </div>
    </form>
  );
}
