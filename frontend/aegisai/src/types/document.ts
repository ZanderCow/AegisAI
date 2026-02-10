import type { UserRole } from './user';

export type DocumentStatus = 'active' | 'archived' | 'processing';

export interface Document {
  id: string;
  title: string;
  description: string;
  fileName: string;
  fileSize: number;
  allowedRoles: UserRole[];
  status: DocumentStatus;
  uploadedBy: string;
  uploadedAt: string;
  updatedAt: string;
}
