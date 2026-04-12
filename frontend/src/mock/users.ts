/**
 * Mock user records used by admin and role-management views in local UI flows.
 */
import type { User } from '@/types';

/** Stable user fixtures that drive mock-only tables and navigation states. */
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
    email: 'uma@aegisai.com',
    name: 'Uma User',
    role: 'user',
    createdAt: '2025-02-15T11:00:00Z',
    lastLogin: '2025-06-09T16:20:00Z',
  },
  {
    id: 'u4',
    email: 'ulysses@aegisai.com',
    name: 'Ulysses User',
    role: 'user',
    createdAt: '2025-03-01T09:30:00Z',
    lastLogin: '2025-06-10T09:00:00Z',
  },
  {
    id: 'u5',
    email: 'ursula@aegisai.com',
    name: 'Ursula User',
    role: 'user',
    createdAt: '2025-03-10T14:00:00Z',
    lastLogin: '2025-06-08T11:30:00Z',
  },
];
