import { useEffect, useState } from 'react';
import type { Document } from '@/types';
import { documentService } from '@/services';
import { Card, DataTable, Badge, Spinner, SearchBar } from '@/components/ui';

export function SecurityDocumentsPage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [search, setSearch] = useState('');

  useEffect(() => {
    documentService.getAll().then(data => {
      setDocuments(data);
      setIsLoading(false);
    });
  }, []);

  const filtered = documents.filter(d =>
    d.title.toLowerCase().includes(search.toLowerCase()) ||
    d.allowedRoles.some(r => r.includes(search.toLowerCase())),
  );

  const columns = [
    { key: 'title', header: 'Document', render: (d: Document) => (
      <div>
        <p className="font-medium text-gray-200">{d.title}</p>
        <p className="text-xs text-gray-500">{d.description}</p>
      </div>
    ), className: 'px-4 py-3 text-sm max-w-sm' },
    { key: 'roles', header: 'Allowed Roles', render: (d: Document) => (
      <div className="flex flex-wrap gap-1">
        {d.allowedRoles.map(r => <Badge key={r} variant="info">{r}</Badge>)}
      </div>
    )},
    { key: 'status', header: 'Status', render: (d: Document) => (
      <Badge variant={d.status === 'active' ? 'success' : d.status === 'processing' ? 'warning' : 'default'}>
        {d.status}
      </Badge>
    )},
    { key: 'uploaded', header: 'Uploaded', render: (d: Document) => <span className="text-gray-400">{new Date(d.uploadedAt).toLocaleDateString()}</span> },
    { key: 'updated', header: 'Last Updated', render: (d: Document) => <span className="text-gray-400">{new Date(d.updatedAt).toLocaleDateString()}</span> },
  ];

  if (isLoading) return <Spinner className="mt-20" />;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-100">Document Access Control</h1>
      <p className="text-gray-400">Read-only view of all documents and their role-based access mappings.</p>

      <Card padding={false}>
        <div className="p-4 border-b border-gray-800">
          <SearchBar value={search} onChange={setSearch} placeholder="Search by document or role..." />
        </div>
        <DataTable columns={columns} data={filtered} keyExtractor={d => d.id} emptyMessage="No documents found" />
      </Card>
    </div>
  );
}
