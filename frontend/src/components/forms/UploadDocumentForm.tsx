import { useRef, useState, type FormEvent } from 'react';
import { Button, Input, TextArea } from '@/components/ui';
import type { UserRole } from '@/types';

interface UploadDocumentFormProps {
  onSubmit: (data: {
    file: File;
    title: string;
    description: string;
    allowedRoles: UserRole[];
  }) => Promise<void>;
  onCancel: () => void;
}

const allRoles: { value: UserRole; label: string }[] = [
  { value: 'user', label: 'User' },
  { value: 'admin', label: 'Admin' },
  { value: 'security', label: 'Security' },
];

export function UploadDocumentForm({ onSubmit, onCancel }: UploadDocumentFormProps) {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [selectedRoles, setSelectedRoles] = useState<UserRole[]>(['admin']);
  const [file, setFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const toggleRole = (role: UserRole) => {
    setSelectedRoles(prev =>
      prev.includes(role) ? prev.filter(r => r !== role) : [...prev, role],
    );
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const picked = e.target.files?.[0] ?? null;
    setFile(picked);
    if (picked && !title) setTitle(picked.name.replace(/\.pdf$/i, ''));
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!file) return;
    setIsLoading(true);
    try {
      await onSubmit({ file, title, description, allowedRoles: selectedRoles });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* PDF file picker */}
      <div className="space-y-1">
        <label className="block text-sm font-medium text-gray-300">PDF File</label>
        <div
          className="flex items-center gap-3 px-3 py-2 rounded-lg border border-gray-700 bg-gray-800 cursor-pointer hover:border-aegis-600 transition-colors"
          onClick={() => fileInputRef.current?.click()}
        >
          <svg className="w-5 h-5 text-gray-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
          </svg>
          <span className={`text-sm truncate ${file ? 'text-gray-200' : 'text-gray-500'}`}>
            {file ? file.name : 'Choose a PDF file…'}
          </span>
        </div>
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf"
          className="hidden"
          onChange={handleFileChange}
          required
        />
      </div>

      <Input label="Document Title" value={title} onChange={e => setTitle(e.target.value)} required />
      <TextArea label="Description" value={description} onChange={e => setDescription(e.target.value)} required />

      <div className="space-y-1">
        <label className="block text-sm font-medium text-gray-300">Allowed Roles</label>
        <div className="flex flex-wrap gap-2">
          {allRoles.map(r => (
            <button
              key={r.value}
              type="button"
              aria-pressed={selectedRoles.includes(r.value)}
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
        <Button type="submit" isLoading={isLoading} disabled={!file}>Upload</Button>
      </div>
    </form>
  );
}
