import type { User } from '@/types';
import { mockUsers } from '@/mock';

const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

let users = mockUsers.map(u => ({ ...u }));

export const userService = {
  async getAll(): Promise<User[]> {
    await delay(400);
    return users.map(u => ({ ...u }));
  },

  async create(user: Omit<User, 'id' | 'createdAt'>): Promise<User> {
    await delay(600);
    const newUser: User = {
      ...user,
      id: `u${Date.now()}`,
      createdAt: new Date().toISOString(),
    };
    users.push(newUser);
    return { ...newUser };
  },

  async update(id: string, updates: Partial<User>): Promise<User> {
    await delay(500);
    const index = users.findIndex(u => u.id === id);
    if (index === -1) throw new Error('User not found');
    users[index] = { ...users[index], ...updates };
    return { ...users[index] };
  },

  async remove(id: string): Promise<void> {
    await delay(400);
    users = users.filter(u => u.id !== id);
  },
};
