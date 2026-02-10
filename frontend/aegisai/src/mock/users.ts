import type { User } from '@/types';

export const mockUsers: User[] = [
  {
    id: 'u1',
    email: 'admin@aegisai.com',
    name: 'Alex Admin',
    role: 'admin',
    createdAt: '2025-01-15T09:00:00Z',
    lastLogin: '2025-06-10T08:30:00Z',
  },
  {
    id: 'u2',
    email: 'sarah@aegisai.com',
    name: 'Sarah Security',
    role: 'security',
    createdAt: '2025-02-01T10:00:00Z',
    lastLogin: '2025-06-10T07:45:00Z',
  },
  {
    id: 'u3',
    email: 'ivan@aegisai.com',
    name: 'Ivan IT',
    role: 'it',
    createdAt: '2025-02-15T11:00:00Z',
    lastLogin: '2025-06-09T16:20:00Z',
  },
  {
    id: 'u4',
    email: 'hannah@aegisai.com',
    name: 'Hannah HR',
    role: 'hr',
    createdAt: '2025-03-01T09:30:00Z',
    lastLogin: '2025-06-10T09:00:00Z',
  },
  {
    id: 'u5',
    email: 'frank@aegisai.com',
    name: 'Frank Finance',
    role: 'finance',
    createdAt: '2025-03-10T14:00:00Z',
    lastLogin: '2025-06-08T11:30:00Z',
  },
  {
    id: 'u6',
    email: 'tina@aegisai.com',
    name: 'Tina IT',
    role: 'it',
    createdAt: '2025-04-01T08:00:00Z',
    lastLogin: '2025-06-10T10:15:00Z',
  },
];

export const mockPasswords: Record<string, string> = {
  'admin@aegisai.com': 'admin123',
  'sarah@aegisai.com': 'security123',
  'ivan@aegisai.com': 'it123',
  'hannah@aegisai.com': 'hr123',
  'frank@aegisai.com': 'finance123',
  'tina@aegisai.com': 'it123',
};
