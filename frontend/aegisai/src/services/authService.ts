import type { User } from '@/types';
import { apiClient } from './apiClient';
import { mockUsers } from '@/mock'; // Keeping fallback mock data for user profile since /users/me is not implemented in backend yet

const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

export const authService = {
  async login(email: string, password: string): Promise<User> {
    // Call backend API
    const response = await apiClient<{ access_token: string }>('/auth/login/access-token', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });

    localStorage.setItem('access_token', response.access_token);

    // Backend doesn't fully implement /users/me yet, so fallback to mock user or construct one
    const user = mockUsers.find(u => u.email === email) || {
      id: 'backend-user-123',
      email,
      name: email.split('@')[0],
      role: 'security' as const,
      createdAt: new Date().toISOString(),
    };

    return { ...user, lastLogin: new Date().toISOString() };
  },

  async getCurrentUser(userId: string): Promise<User | null> {
    await delay(300);
    // TODO: hit backend /users/me when implemented
    const user = mockUsers.find(u => u.id === userId);
    return user ? { ...user } : null;
  },
};
