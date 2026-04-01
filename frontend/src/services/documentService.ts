/**
 * Provides mock document CRUD operations for the frontend.
 *
 * The service simulates API latency with in-memory data so the UI can be built
 * and tested before the backend integration is complete.
 */
import type { Document, UserRole } from '@/types';
import { mockDocuments } from '@/mock';

/**
 * Input required to create a new document record.
 *
 * The service generates the identifier and timestamp fields automatically.
 */
export type DocumentCreateInput = Omit<Document, 'id' | 'uploadedAt' | 'updatedAt'>;

/**
 * Contract for the mock document service consumed by document management views.
 */
export interface DocumentService {
  /**
   * Returns every document currently stored in memory.
   *
   * @returns A cloned list of all documents.
   */
  getAll(): Promise<Document[]>;

  /**
   * Returns the documents accessible to the provided user role.
   *
   * @param role - The role used to filter document access.
   * @returns A cloned list of documents the role is allowed to view.
   */
  getByRole(role: UserRole): Promise<Document[]>;

  /**
   * Creates a new document record in the in-memory store.
   *
   * @param doc - The document fields supplied by the caller.
   * @returns The newly created document with generated metadata.
   */
  create(doc: DocumentCreateInput): Promise<Document>;

  /**
   * Updates an existing document and refreshes its timestamp.
   *
   * @param id - The unique document identifier.
   * @param updates - The partial document fields to merge into the stored record.
   * @returns The updated document.
   * @throws Error When the requested document cannot be found.
   */
  update(id: string, updates: Partial<Document>): Promise<Document>;

  /**
   * Removes a document from the in-memory store.
   *
   * @param id - The unique document identifier.
   * @returns A promise that resolves after the document is removed.
   */
  remove(id: string): Promise<void>;
}

/**
 * Waits for the supplied duration to emulate API latency.
 *
 * @param ms - The number of milliseconds to pause before resolving.
 * @returns A promise that resolves after the delay elapses.
 */
function delay(ms: number): Promise<void> {
  return new Promise(resolve => {
    setTimeout(resolve, ms);
  });
}

/**
 * Creates a defensive copy of a document record.
 *
 * @param document - The document to clone.
 * @returns A shallow clone of the provided document.
 */
function cloneDocument(document: Document): Document {
  return { ...document };
}

/**
 * Creates defensive copies of a list of document records.
 *
 * @param source - The documents to clone.
 * @returns A cloned list that is safe to return to callers.
 */
function cloneDocuments(source: Document[]): Document[] {
  return source.map(cloneDocument);
}

/**
 * Generates an ISO-8601 timestamp for new or updated records.
 *
 * @returns The current timestamp in ISO string format.
 */
function nowIsoString(): string {
  return new Date().toISOString();
}

let documents: Document[] = cloneDocuments(mockDocuments);

export const documentService: DocumentService = {
  async getAll(): Promise<Document[]> {
    await delay(400);
    return cloneDocuments(documents);
  },

  async getByRole(role: UserRole): Promise<Document[]> {
    await delay(400);
    return cloneDocuments(documents.filter(document => document.allowedRoles.includes(role)));
  },

  async create(doc: DocumentCreateInput): Promise<Document> {
    await delay(600);
    const newDoc: Document = {
      ...doc,
      id: `d${Date.now()}`,
      uploadedAt: nowIsoString(),
      updatedAt: nowIsoString(),
    };
    documents.push(newDoc);
    return cloneDocument(newDoc);
  },

  async update(id: string, updates: Partial<Document>): Promise<Document> {
    await delay(500);
    const index = documents.findIndex(document => document.id === id);
    if (index === -1) throw new Error('Document not found');
    documents[index] = { ...documents[index], ...updates, updatedAt: nowIsoString() };
    return cloneDocument(documents[index]);
  },

  async remove(id: string): Promise<void> {
    await delay(400);
    documents = documents.filter(document => document.id !== id);
  },
};
