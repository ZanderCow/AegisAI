import type { Role } from '@/types';

export const mockRoles: Role[] = [
  {
    id: 'r1',
    name: 'admin',
    label: 'Administrator',
    description: 'Full system access including user management and security monitoring',
    permissions: ['chat', 'admin.dashboard', 'admin.users', 'admin.roles', 'admin.documents', 'admin.security'],
    userCount: 1,
  },
  {
    id: 'r2',
    name: 'security',
    label: 'Security Analyst',
    description: 'Access to security dashboard and document-role audit views',
    permissions: ['security.dashboard', 'security.documents'],
    userCount: 1,
  },
  {
    id: 'r3',
    name: 'it',
    label: 'IT Staff',
    description: 'Access to IT-related documents via chat interface',
    permissions: ['chat'],
    userCount: 2,
  },
  {
    id: 'r4',
    name: 'hr',
    label: 'Human Resources',
    description: 'Access to HR policies and documents via chat interface',
    permissions: ['chat'],
    userCount: 1,
  },
  {
    id: 'r5',
    name: 'finance',
    label: 'Finance',
    description: 'Access to financial documents via chat interface',
    permissions: ['chat'],
    userCount: 1,
  },
];
