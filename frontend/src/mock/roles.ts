import type { Role } from '@/types';

export const mockRoles: Role[] = [
  {
    id: 'r1',
    name: 'user',
    label: 'User',
    description: 'Standard end-user access for chat and role-scoped RAG documents',
    permissions: ['chat', 'documents'],
    userCount: 3,
  },
  {
    id: 'r2',
    name: 'admin',
    label: 'Administrator',
    description: 'Full system access including user management and security monitoring',
    permissions: ['chat', 'admin.dashboard', 'admin.users', 'admin.roles', 'admin.documents', 'admin.security'],
    userCount: 1,
  },
  {
    id: 'r3',
    name: 'security',
    label: 'Security Analyst',
    description: 'Access to security dashboard and document-role audit views',
    permissions: ['security.dashboard', 'security.documents'],
    userCount: 1,
  },
];
