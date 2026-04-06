import { useEffect, useState } from 'react';
import type { Document } from '@/types';
import { documentService } from '@/services';
import { Card, Badge, Spinner } from '@/components/ui';

export function RagDocumentsPage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    documentService.getAll()
      .then(data => setDocuments(data))
      .catch(() => {})
      .finally(() => setIsLoading(false));
  }, []);

  if (isLoading) return <Spinner className="mt-20" />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-100">RAG Documents</h1>
        <p className="text-sm text-gray-400 mt-1">
          Documents available to your role. The AI will use these as context in your chats.
        </p>
      </div>

      <Card padding={false}>
        {documents.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
            <div className="w-14 h-14 rounded-full bg-gray-800 flex items-center justify-center mb-4">
              <svg className="w-7 h-7 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <p className="text-gray-400 font-medium">No documents available</p>
            <p className="text-gray-500 text-sm mt-1">No documents have been assigned to your role yet.</p>
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-800">
                <th className="text-left px-6 py-3 text-xs font-medium text-gray-400 uppercase tracking-wider">Document</th>
                <th className="text-left px-6 py-3 text-xs font-medium text-gray-400 uppercase tracking-wider">Roles</th>
                <th className="text-left px-6 py-3 text-xs font-medium text-gray-400 uppercase tracking-wider">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {documents.map(doc => (
                <tr key={doc.id} className="hover:bg-gray-800/40 transition-colors">
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-lg bg-aegis-900/50 border border-aegis-800 flex items-center justify-center flex-shrink-0">
                        <svg className="w-4 h-4 text-aegis-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                        </svg>
                      </div>
                      <div>
                        <p className="text-gray-200 font-medium">{doc.title}</p>
                        <p className="text-xs text-gray-500">{doc.fileName}</p>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex flex-wrap gap-1">
                      {doc.allowedRoles.map(r => <Badge key={r} variant="info">{r}</Badge>)}
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <Badge variant={doc.status === 'active' ? 'success' : doc.status === 'processing' ? 'warning' : 'default'}>
                      {doc.status}
                    </Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>

      {documents.length > 0 && (
        <p className="text-xs text-gray-500 text-center">
          {documents.length} document{documents.length !== 1 ? 's' : ''} available — the AI will automatically use these as context in your chats.
        </p>
      )}
    </div>
  );
}
