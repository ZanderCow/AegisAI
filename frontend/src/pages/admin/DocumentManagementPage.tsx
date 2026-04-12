import { useEffect, useState } from 'react';
import type { Document, UserRole } from '@/types';
import { documentService } from '@/services';
import { Card, DataTable, Button, Modal, Badge, Spinner, SearchBar } from '@/components/ui';
import { UploadDocumentForm } from '@/components/forms/UploadDocumentForm';

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

export function DocumentManagementPage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [search, setSearch] = useState('');
  const [error, setError] = useState('');

  const load = async () => {
    try {
      const data = await documentService.getAll();
      setDocuments(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load documents');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleUpload = async (data: {
    file: File;
    title: string;
    description: string;
    allowedRoles: UserRole[];
  }) => {
    const newDoc = await documentService.upload(data.file, data.title, data.description, data.allowedRoles);
    setDocuments(prev => [...prev, newDoc]);
    setIsModalOpen(false);
  };

  const handleDelete = async (id: string) => {
    await documentService.remove(id);
    setDocuments(prev => prev.filter(d => d.id !== id));
  };

  const filtered = documents.filter(d =>
    d.title.toLowerCase().includes(search.toLowerCase()) ||
    d.fileName.toLowerCase().includes(search.toLowerCase()),
  );

  const statusVariant: Record<string, 'success' | 'warning' | 'default'> = {
    active: 'success',
    processing: 'warning',
    archived: 'default',
  };

  const columns = [
    { key: 'title', header: 'Title', render: (d: Document) => (
      <div>
        <p className="font-medium text-gray-200">{d.title}</p>
        <p className="text-xs text-gray-500">{d.fileName}</p>
      </div>
    )},
    { key: 'size', header: 'Size', render: (d: Document) => <span className="text-gray-400">{formatFileSize(d.fileSize)}</span> },
    { key: 'roles', header: 'Allowed Roles', render: (d: Document) => (
      <div className="flex flex-wrap gap-1">
        {d.allowedRoles.map(r => <Badge key={r} variant="info">{r}</Badge>)}
      </div>
    )},
    { key: 'status', header: 'Status', render: (d: Document) => <Badge variant={statusVariant[d.status]}>{d.status}</Badge> },
    { key: 'updated', header: 'Updated', render: (d: Document) => <span className="text-gray-400">{new Date(d.updatedAt).toLocaleDateString()}</span> },
    { key: 'actions', header: '', render: (d: Document) => (
      <Button size="sm" variant="danger" onClick={() => handleDelete(d.id)}>Delete</Button>
    )},
  ];

  if (isLoading) return <Spinner className="mt-20" />;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <h1 className="text-2xl font-bold text-gray-100">Document Management</h1>
        <Button onClick={() => setIsModalOpen(true)}>Upload Document</Button>
      </div>

      {error && (
        <div className="px-4 py-3 rounded-lg bg-red-900/30 border border-red-800 text-red-300 text-sm">{error}</div>
      )}

      <Card padding={false}>
        <div className="p-4 border-b border-gray-800">
          <SearchBar value={search} onChange={setSearch} placeholder="Search documents..." />
        </div>
        <DataTable columns={columns} data={filtered} keyExtractor={d => d.id} emptyMessage="No documents found" />
      </Card>

      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title="Upload Document">
        <UploadDocumentForm onSubmit={handleUpload} onCancel={() => setIsModalOpen(false)} />
      </Modal>
    </div>
  );
}
