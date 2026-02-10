import { useState, type FormEvent } from 'react';
import { Button, Input, TextArea } from '@/components/ui';
import type { UserRole } from '@/types';

interface UploadDocumentFormProps {
  onSubmit: (data: {
    title: string;
    description: string;
    fileName: string;
    allowedRoles: UserRole[];
  }) => Promise<void>;
  onCancel: () => void;
}

const allRoles: { value: UserRole; label: string }[] = [
  { value: 'admin', label: 'Admin' },
  { value: 'security', label: 'Security' },
  { value: 'it', label: 'IT' },
  { value: 'hr', label: 'HR' },
  { value: 'finance', label: 'Finance' },
];

export function UploadDocumentForm({ onSubmit, onCancel }: UploadDocumentFormProps) {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [fileName, setFileName] = useState('');
  const [selectedRoles, setSelectedRoles] = useState<UserRole[]>(['admin']);
  const [isLoading, setIsLoading] = useState(false);

  const toggleRole = (role: UserRole) => {
    setSelectedRoles(prev =>
      prev.includes(role) ? prev.filter(r => r !== role) : [...prev, role],
    );
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      await onSubmit({ title, description, fileName, allowedRoles: selectedRoles });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <Input label="Document Title" value={title} onChange={e => setTitle(e.target.value)} required />
      <TextArea label="Description" value={description} onChange={e => setDescription(e.target.value)} required />
      <Input label="File Name" value={fileName} onChange={e => setFileName(e.target.value)} placeholder="document.pdf" required />
      <div className="space-y-1">
        <label className="block text-sm font-medium text-gray-300">Allowed Roles</label>
        <div className="flex flex-wrap gap-2">
          {allRoles.map(r => (
            <button
              key={r.value}
              type="button"
              onClick={() => toggleRole(r.value)}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                selectedRoles.includes(r.value)
                  ? 'bg-aegis-600 text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              {r.label}
            </button>
          ))}
        </div>
      </div>
      <div className="flex justify-end gap-2 pt-2">
        <Button variant="secondary" type="button" onClick={onCancel}>Cancel</Button>
        <Button type="submit" isLoading={isLoading}>Upload</Button>
      </div>
    </form>
  );
}
