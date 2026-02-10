import type { Document, UserRole } from '@/types';
import { mockDocuments } from '@/mock';

const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

let documents = mockDocuments.map(d => ({ ...d }));

export const documentService = {
  async getAll(): Promise<Document[]> {
    await delay(400);
    return documents.map(d => ({ ...d }));
  },

  async getByRole(role: UserRole): Promise<Document[]> {
    await delay(400);
    return documents
      .filter(d => d.allowedRoles.includes(role))
      .map(d => ({ ...d }));
  },

  async create(doc: Omit<Document, 'id' | 'uploadedAt' | 'updatedAt'>): Promise<Document> {
    await delay(600);
    const newDoc: Document = {
      ...doc,
      id: `d${Date.now()}`,
      uploadedAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    documents.push(newDoc);
    return { ...newDoc };
  },

  async update(id: string, updates: Partial<Document>): Promise<Document> {
    await delay(500);
    const index = documents.findIndex(d => d.id === id);
    if (index === -1) throw new Error('Document not found');
    documents[index] = { ...documents[index], ...updates, updatedAt: new Date().toISOString() };
    return { ...documents[index] };
  },

  async remove(id: string): Promise<void> {
    await delay(400);
    documents = documents.filter(d => d.id !== id);
  },
};
