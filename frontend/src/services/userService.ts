import { API_URL } from '@/config/api';
import type { User, UserRole } from '@/types';

type AdminUserResponse = {
  id: string;
  full_name: string | null;
  email: string;
  role: UserRole;
  created_at: string;
  last_login: string | null;
};

function getToken(): string {
  return localStorage.getItem('aegis_token') || '';
}

function getAuthHeaders(includeJson = false): HeadersInit {
  return {
    ...(includeJson ? { 'Content-Type': 'application/json' } : {}),
    Authorization: `Bearer ${getToken()}`,
  };
}

async function parseError(res: Response): Promise<string> {
  try {
    const data = await res.json();
    return data.detail || 'An error occurred';
  } catch {
    return 'An error occurred';
  }
}

function mapAdminUser(user: AdminUserResponse): User {
  return {
    id: user.id,
    email: user.email,
    name: user.full_name ?? user.email,
    fullName: user.full_name ?? undefined,
    role: user.role,
    createdAt: user.created_at,
    lastLogin: user.last_login ?? undefined,
  };
}

export const userService = {
  async getAll(): Promise<User[]> {
    const res = await fetch(`${API_URL}/api/v1/admin/users`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error(await parseError(res));
    const users: AdminUserResponse[] = await res.json();
    return users.map(mapAdminUser);
  },

  async create(_user: Omit<User, 'id' | 'createdAt'>): Promise<User> {
    throw new Error('Invite flow is not available yet.');
  },

  async updateRole(id: string, role: UserRole): Promise<User> {
    const res = await fetch(`${API_URL}/api/v1/admin/users/${id}/role`, {
      method: 'PATCH',
      headers: getAuthHeaders(true),
      body: JSON.stringify({ role }),
    });
    if (!res.ok) throw new Error(await parseError(res));
    const user: AdminUserResponse = await res.json();
    return mapAdminUser(user);
  },

  async remove(id: string): Promise<void> {
    const res = await fetch(`${API_URL}/api/v1/admin/users/${id}`, {
      method: 'DELETE',
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error(await parseError(res));
  },
};
