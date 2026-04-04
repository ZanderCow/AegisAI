import { API_URL } from '@/config/api';

function getToken(): string {
  return localStorage.getItem('aegis_token') || '';
}

function authHeaders(): Record<string, string> {
  return { Authorization: `Bearer ${getToken()}` };
}

export interface RagDocument {
  doc_id: string;
  filename: string;
  chunk_count: number;
}

export interface UploadResponse {
  doc_id: string;
  filename: string;
  chunk_count: number;
  message: string;
}

export const ragService = {
  async listDocuments(): Promise<RagDocument[]> {
    const res = await fetch(`${API_URL}/api/v1/rag/documents`, {
      headers: authHeaders(),
    });
    if (!res.ok) throw new Error('Failed to fetch documents');
    return res.json();
  },

  async uploadDocument(file: File): Promise<UploadResponse> {
    const form = new FormData();
    form.append('file', file);
    const res = await fetch(`${API_URL}/api/v1/rag/documents`, {
      method: 'POST',
      headers: authHeaders(),
      body: form,
    });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data.detail || 'Upload failed');
    }
    return res.json();
  },

  async deleteDocument(docId: string): Promise<void> {
    const res = await fetch(`${API_URL}/api/v1/rag/documents/${docId}`, {
      method: 'DELETE',
      headers: authHeaders(),
    });
    if (!res.ok) throw new Error('Failed to delete document');
  },
};
