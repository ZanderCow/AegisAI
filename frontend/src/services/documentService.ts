/**
 * Real API client for the /api/v1/documents endpoints.
 *
 * Replaces the previous in-memory mock. All operations hit the backend and
 * are subject to role-based access control enforced server-side.
 */
import type { Document, UserRole } from '@/types';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function getToken(): string {
  return localStorage.getItem('aegis_token') || '';
}

function authHeaders(): Record<string, string> {
  return { Authorization: `Bearer ${getToken()}` };
}

async function parseError(res: Response): Promise<string> {
  try {
    const data = await res.json();
    return data.detail || 'An error occurred';
  } catch {
    return 'An error occurred';
  }
}

/** Shape returned by GET /api/v1/documents */
interface ApiDocument {
  id: string;
  title: string;
  description: string;
  filename: string;
  file_size: number;
  status: string;
  uploaded_by: string;
  allowed_roles: string[];
  chroma_doc_id: string | null;
  created_at: string;
  updated_at: string;
}

function mapDoc(d: ApiDocument): Document {
  return {
    id: d.id,
    title: d.title,
    description: d.description,
    fileName: d.filename,
    fileSize: d.file_size,
    status: d.status as Document['status'],
    uploadedBy: d.uploaded_by,
    allowedRoles: d.allowed_roles as Document['allowedRoles'],
    uploadedAt: d.created_at,
    updatedAt: d.updated_at,
  };
}

export const documentService = {
  /** List documents accessible to the current user's role. */
  async getAll(): Promise<Document[]> {
    const res = await fetch(`${API_URL}/api/v1/documents`, {
      headers: authHeaders(),
    });
    if (!res.ok) throw new Error(await parseError(res));
    const data: ApiDocument[] = await res.json();
    return data.map(mapDoc);
  },

  /**
   * Upload a PDF and assign roles. Admin only.
   * @param file - The PDF file to upload.
   * @param title - Display title.
   * @param description - Optional description.
   * @param allowedRoles - Roles that may access this document.
   */
  async upload(
    file: File,
    title: string,
    description: string,
    allowedRoles: UserRole[],
  ): Promise<Document> {
    const form = new FormData();
    form.append('file', file);
    form.append('title', title);
    form.append('description', description);
    form.append('allowed_roles', allowedRoles.join(','));

    const res = await fetch(`${API_URL}/api/v1/documents`, {
      method: 'POST',
      headers: authHeaders(),
      body: form,
    });
    if (!res.ok) throw new Error(await parseError(res));
    return mapDoc(await res.json());
  },

  /** Update document metadata or role assignments. Admin only. */
  async update(
    id: string,
    updates: { title?: string; description?: string; allowedRoles?: UserRole[]; status?: string },
  ): Promise<Document> {
    const body: Record<string, unknown> = {};
    if (updates.title !== undefined) body.title = updates.title;
    if (updates.description !== undefined) body.description = updates.description;
    if (updates.allowedRoles !== undefined) body.allowed_roles = updates.allowedRoles;
    if (updates.status !== undefined) body.status = updates.status;

    const res = await fetch(`${API_URL}/api/v1/documents/${id}`, {
      method: 'PUT',
      headers: { ...authHeaders(), 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error(await parseError(res));
    return mapDoc(await res.json());
  },

  /** Delete a document and its vector chunks. Admin only. */
  async remove(id: string): Promise<void> {
    const res = await fetch(`${API_URL}/api/v1/documents/${id}`, {
      method: 'DELETE',
      headers: authHeaders(),
    });
    if (!res.ok) throw new Error(await parseError(res));
  },
};
