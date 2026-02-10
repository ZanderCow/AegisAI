import type { User } from '@/types';
import { mockUsers, mockPasswords } from '@/mock';

const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

export const authService = {
  async login(email: string, password: string): Promise<User> {
    await delay(800);
    const user = mockUsers.find(u => u.email === email);
    if (!user || mockPasswords[email] !== password) {
      throw new Error('Invalid email or password');
    }
    return { ...user, lastLogin: new Date().toISOString() };
  },

  async getCurrentUser(userId: string): Promise<User | null> {
    await delay(300);
    const user = mockUsers.find(u => u.id === userId);
    return user ? { ...user } : null;
  },
};
